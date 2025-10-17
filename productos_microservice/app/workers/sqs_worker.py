"""
Worker para procesar mensajes de SQS de importación de productos
"""
import os
import sys
import time
import signal
import logging
import json
from typing import Optional
from datetime import datetime

# Añadir el directorio raíz al path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from app.extensions import db
from app.models.import_job import ImportJob
from app.services.sqs_service import SQSService
from app.services.s3_service import S3Service
from app.services.csv_service import CSVProductoService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variable global para manejo de shutdown graceful
shutdown_requested = False


def signal_handler(signum, frame):
    """Maneja señales de terminación (SIGTERM, SIGINT)"""
    global shutdown_requested
    logger.info(f"Señal {signum} recibida. Iniciando shutdown graceful...")
    shutdown_requested = True


def procesar_mensaje(app, mensaje: dict, sqs_service: SQSService, s3_service: S3Service) -> bool:
    """
    Procesa un mensaje de la cola SQS
    
    Args:
        app: Flask app instance
        mensaje: Mensaje de SQS
        sqs_service: Servicio de SQS
        s3_service: Servicio de S3
        
    Returns:
        bool: True si se procesó exitosamente, False en caso contrario
    """
    receipt_handle = mensaje['ReceiptHandle']
    message_id = mensaje['MessageId']
    
    try:
        # Parsear el body del mensaje
        body = json.loads(mensaje['Body'])
        job_id = body.get('job_id')
        s3_key = body.get('s3_key')
        usuario_registro = body.get('usuario_registro', 'sistema')
        
        logger.info(f"📥 Procesando mensaje {message_id} - Job {job_id}")
        
        if not job_id or not s3_key:
            logger.error(f"❌ Mensaje inválido: falta job_id o s3_key")
            # Eliminar mensaje inválido
            sqs_service.eliminar_mensaje(receipt_handle)
            return False
        
        # Trabajar dentro del contexto de la aplicación
        with app.app_context():
            # 1. Obtener el Job de la base de datos
            job = db.session.query(ImportJob).filter_by(id=job_id).first()
            
            if not job:
                logger.error(f"❌ Job {job_id} no encontrado en la base de datos")
                sqs_service.eliminar_mensaje(receipt_handle)
                return False
            
            # 2. Marcar el job como PROCESANDO
            job.marcar_como_procesando()
            db.session.commit()
            logger.info(f"🔄 Job {job_id} marcado como PROCESANDO")
            
            # 3. Descargar el CSV desde S3
            logger.info(f"📥 Descargando CSV desde S3: {s3_key}")
            contenido_csv = s3_service.descargar_csv(s3_key)
            
            if not contenido_csv:
                error_msg = f"No se pudo descargar el archivo CSV desde S3: {s3_key}"
                logger.error(f"❌ {error_msg}")
                job.marcar_como_fallido(error_msg)
                db.session.commit()
                sqs_service.eliminar_mensaje(receipt_handle)
                return False
            
            # 4. Callback para actualizar progreso
            def actualizar_progreso(fila_actual: int, total_filas: int, exitosos: int, fallidos: int):
                """Actualiza el progreso del job en la base de datos"""
                try:
                    progreso = (fila_actual / total_filas * 100) if total_filas > 0 else 0
                    job.progreso = round(progreso, 2)
                    job.exitosos = exitosos
                    job.fallidos = fallidos
                    db.session.commit()
                    
                    # Log cada 10% de progreso
                    if fila_actual % max(1, total_filas // 10) == 0:
                        logger.info(f"📊 Job {job_id}: {progreso:.1f}% - {exitosos} exitosos, {fallidos} fallidos")
                        
                    # Extender visibilidad del mensaje si lleva mucho tiempo
                    # Esto evita que el mensaje vuelva a la cola mientras se procesa
                    if fila_actual % max(1, total_filas // 4) == 0:  # Cada 25%
                        logger.info(f"⏱️  Extendiendo visibilidad del mensaje...")
                        sqs_service.cambiar_visibilidad_mensaje(receipt_handle, 300)  # 5 minutos más
                        
                except Exception as e:
                    logger.error(f"❌ Error actualizando progreso: {str(e)}")
            
            # 5. Procesar el CSV
            logger.info(f"🚀 Iniciando procesamiento del CSV...")
            csv_service = CSVProductoService()
            
            resultado = csv_service.procesar_csv_desde_contenido(
                contenido_csv=contenido_csv,
                usuario_registro=usuario_registro,
                callback_progreso=actualizar_progreso
            )
            
            # 6. Actualizar el job con los resultados finales
            if resultado['estado'] == 'completado':
                job.marcar_como_completado(
                    exitosos=resultado['exitosos'],
                    fallidos=resultado['fallidos'],
                    errores=resultado['detalles_errores']
                )
                logger.info(f"✅ Job {job_id} COMPLETADO: {resultado['exitosos']} exitosos, {resultado['fallidos']} fallidos")
            else:
                error_msg = resultado.get('error', 'Error desconocido durante el procesamiento')
                job.marcar_como_fallido(error_msg)
                logger.error(f"❌ Job {job_id} FALLIDO: {error_msg}")
            
            db.session.commit()
            
            # 7. Eliminar el mensaje de la cola (procesamiento exitoso)
            sqs_service.eliminar_mensaje(receipt_handle)
            logger.info(f"🗑️  Mensaje {message_id} eliminado de la cola")
            
            # 8. Opcionalmente, eliminar el archivo de S3 después de procesarlo
            # Comentado por si quieres mantener los archivos como backup
            # logger.info(f"🗑️  Eliminando CSV de S3: {s3_key}")
            # s3_service.eliminar_csv(s3_key)
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje {message_id}: {str(e)}", exc_info=True)
        
        # Intentar marcar el job como fallido
        try:
            with app.app_context():
                body = json.loads(mensaje['Body'])
                job_id = body.get('job_id')
                if job_id:
                    job = db.session.query(ImportJob).filter_by(id=job_id).first()
                    if job:
                        job.marcar_como_fallido(f"Error en worker: {str(e)}")
                        db.session.commit()
        except Exception as inner_e:
            logger.error(f"❌ Error marcando job como fallido: {str(inner_e)}")
        
        # NO eliminar el mensaje - dejarlo para reintento o DLQ
        return False


def run_worker():
    """
    Worker principal que escucha la cola SQS y procesa mensajes
    """
    logger.info("=" * 80)
    logger.info("🚀 Iniciando SQS Worker para importación de productos")
    logger.info("=" * 80)
    
    # Registrar manejadores de señales
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Crear la aplicación Flask
    app = create_app()
    
    # Verificar configuración
    with app.app_context():
        from app.config.aws_config import AWSConfig
        
        if not AWSConfig.verificar_configuracion():
            logger.error("❌ AWS no está configurado correctamente")
            logger.error("   Configure las variables de entorno AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            logger.error("   AWS_REGION, AWS_SQS_QUEUE_URL y AWS_S3_BUCKET_NAME")
            sys.exit(1)
        
        logger.info(f"✅ AWS configurado correctamente")
        logger.info(f"   Region: {os.getenv('AWS_REGION', 'us-east-1')}")
        logger.info(f"   Queue: {os.getenv('AWS_SQS_QUEUE_URL', 'N/A')}")
        logger.info(f"   Bucket: {os.getenv('AWS_S3_BUCKET_NAME', 'N/A')}")
    
    # Inicializar servicios
    sqs_service = SQSService()
    s3_service = S3Service()
    
    # Contadores
    mensajes_procesados = 0
    mensajes_exitosos = 0
    mensajes_fallidos = 0
    ciclos_sin_mensajes = 0
    
    logger.info("👂 Escuchando cola SQS...")
    logger.info("   Presione Ctrl+C para detener el worker")
    logger.info("-" * 80)
    
    # Loop principal
    while not shutdown_requested:
        try:
            # Recibir mensajes de la cola (long polling de 20 segundos)
            mensajes = sqs_service.recibir_mensajes(
                max_messages=1,  # Procesar de uno en uno para mejor control
                wait_time_seconds=20,
                visibility_timeout=300  # 5 minutos para procesar
            )
            
            if not mensajes:
                ciclos_sin_mensajes += 1
                if ciclos_sin_mensajes % 3 == 0:  # Cada ~60 segundos
                    logger.info(f"⏳ Esperando mensajes... ({ciclos_sin_mensajes * 20}s)")
                continue
            
            ciclos_sin_mensajes = 0
            
            # Procesar cada mensaje
            for mensaje in mensajes:
                if shutdown_requested:
                    logger.info("🛑 Shutdown solicitado, no se procesarán más mensajes")
                    break
                
                mensajes_procesados += 1
                
                # Procesar el mensaje
                exito = procesar_mensaje(app, mensaje, sqs_service, s3_service)
                
                if exito:
                    mensajes_exitosos += 1
                else:
                    mensajes_fallidos += 1
                
                logger.info(f"📈 Stats: {mensajes_exitosos} exitosos, {mensajes_fallidos} fallidos de {mensajes_procesados} totales")
                logger.info("-" * 80)
        
        except KeyboardInterrupt:
            logger.info("⌨️  Keyboard interrupt recibido")
            break
        
        except Exception as e:
            logger.error(f"❌ Error en el loop principal: {str(e)}", exc_info=True)
            logger.info("😴 Esperando 10 segundos antes de reintentar...")
            time.sleep(10)
    
    # Shutdown
    logger.info("=" * 80)
    logger.info("🛑 Worker detenido")
    logger.info(f"📊 Estadísticas finales:")
    logger.info(f"   - Mensajes procesados: {mensajes_procesados}")
    logger.info(f"   - Exitosos: {mensajes_exitosos}")
    logger.info(f"   - Fallidos: {mensajes_fallidos}")
    logger.info("=" * 80)


if __name__ == '__main__':
    run_worker()
