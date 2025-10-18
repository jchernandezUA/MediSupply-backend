#!/usr/bin/env python3
"""
Script de prueba para el worker de procesamiento SQS
Simula el envío de un mensaje a la cola y verifica que el worker lo procese
"""
import os
import sys
import json
import time
from datetime import datetime

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.import_job import ImportJob
from app.services.sqs_service import SQSService
from app.services.s3_service import S3Service


def crear_csv_ejemplo():
    """Crea un CSV de ejemplo para pruebas"""
    csv_content = """sku,nombre,descripcion,precio,categoria,proveedor_id,codigo_tipo_producto,fecha_vencimiento,lote,requiere_receta,es_generico,temperatura_almacenamiento,indicaciones,contraindicaciones,efectos_secundarios,dosis_recomendada,url_certificacion_sanitaria,url_ficha_tecnica
SKU-TEST-001,Producto Test 1,Descripción test 1,10.50,Analgésicos,1,MEDICAMENTO,2025-12-31,LOTE-001,false,true,25,Indicaciones test,Contraindicaciones test,Efectos test,1 tableta,https://example.com/cert1.pdf,https://example.com/ficha1.pdf
SKU-TEST-002,Producto Test 2,Descripción test 2,20.00,Antibióticos,1,MEDICAMENTO,2025-12-31,LOTE-002,true,false,4,Indicaciones test,Contraindicaciones test,Efectos test,2 tabletas,https://example.com/cert2.pdf,https://example.com/ficha2.pdf
SKU-TEST-003,Producto Test 3,Descripción test 3,15.75,Vitaminas,1,SUPLEMENTO,2025-12-31,LOTE-003,false,false,25,Indicaciones test,Contraindicaciones test,Efectos test,1 cápsula,,
"""
    return csv_content


def test_worker_flow():
    """
    Prueba el flujo completo del worker:
    1. Crear un CSV
    2. Subirlo a S3
    3. Crear un ImportJob
    4. Enviar mensaje a SQS
    5. Verificar que el worker lo procese
    """
    print("=" * 80)
    print("🧪 Prueba del Worker de Procesamiento SQS")
    print("=" * 80)
    
    # Crear la aplicación Flask
    app = create_app()
    
    with app.app_context():
        # Verificar configuración de AWS
        from app.config.aws_config import AWSConfig
        
        if not AWSConfig.verificar_configuracion():
            print("❌ Error: AWS no está configurado correctamente")
            print("   Configure las variables de entorno necesarias:")
            print("   - AWS_ACCESS_KEY_ID")
            print("   - AWS_SECRET_ACCESS_KEY")
            print("   - AWS_REGION")
            print("   - AWS_SQS_QUEUE_URL")
            print("   - AWS_S3_BUCKET_NAME")
            return False
        
        print("✅ AWS configurado correctamente")
        
        # Inicializar servicios
        sqs_service = SQSService()
        s3_service = S3Service()
        
        # 1. Crear CSV de ejemplo
        print("\n📝 Paso 1: Crear CSV de ejemplo...")
        csv_content = crear_csv_ejemplo()
        print(f"   CSV creado con {len(csv_content.split(chr(10))) - 1} líneas de datos")
        
        # 2. Subir CSV a S3
        print("\n☁️  Paso 2: Subir CSV a S3...")
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"test_worker_{timestamp}.csv"
        
        s3_key = s3_service.subir_csv(
            contenido=csv_content,
            nombre_archivo=filename,
            metadata={
                'test': 'true',
                'timestamp': timestamp,
                'total_filas': '3'
            }
        )
        
        if not s3_key:
            print("   ❌ Error subiendo CSV a S3")
            return False
        
        print(f"   ✅ CSV subido a S3: {s3_key}")
        
        # 3. Crear ImportJob
        print("\n💾 Paso 3: Crear ImportJob en la base de datos...")
        job = ImportJob(
            nombre_archivo=filename,
            s3_key=s3_key,
            total_filas=3,
            usuario_registro='test'
        )
        db.session.add(job)
        db.session.commit()
        
        job_id = str(job.id)
        print(f"   ✅ ImportJob creado: {job_id}")
        print(f"   Estado inicial: {job.estado}")
        
        # 4. Enviar mensaje a SQS
        print("\n📨 Paso 4: Enviar mensaje a SQS...")
        mensaje = {
            'job_id': job_id,
            's3_key': s3_key,
            'usuario_registro': 'test',
            'timestamp': timestamp
        }
        
        message_id = sqs_service.enviar_job_a_cola(mensaje)
        
        if not message_id:
            print("   ❌ Error enviando mensaje a SQS")
            # Limpiar
            s3_service.eliminar_csv(s3_key)
            db.session.delete(job)
            db.session.commit()
            return False
        
        print(f"   ✅ Mensaje enviado a SQS: {message_id}")
        
        # Actualizar job con message_id
        job.sqs_message_id = message_id
        job.marcar_en_cola()
        db.session.commit()
        
        print(f"   Estado actualizado: {job.estado}")
        
        # 5. Mostrar instrucciones para el usuario
        print("\n" + "=" * 80)
        print("✅ Configuración completada exitosamente!")
        print("=" * 80)
        print("\n📋 Información del Job:")
        print(f"   Job ID: {job_id}")
        print(f"   Archivo: {filename}")
        print(f"   S3 Key: {s3_key}")
        print(f"   Message ID: {message_id}")
        print(f"   Estado: {job.estado}")
        
        print("\n🚀 Próximos pasos:")
        print("   1. Iniciar el worker en otra terminal:")
        print("      python worker.py")
        print()
        print("   2. El worker procesará el mensaje automáticamente")
        print()
        print("   3. Consultar el estado del job:")
        print(f"      curl http://localhost:5008/api/productos/importar-csv/status/{job_id}")
        print()
        print("   4. Ver detalles con errores:")
        print(f"      curl http://localhost:5008/api/productos/importar-csv/status/{job_id}?include_errors=true")
        
        # 6. Esperar y monitorear (opcional)
        print("\n⏳ Monitoreando el estado del job (presione Ctrl+C para salir)...")
        print("   El script consultará el estado cada 3 segundos")
        print()
        
        try:
            estado_anterior = job.estado
            while True:
                time.sleep(3)
                
                # Refrescar el job
                db.session.refresh(job)
                
                if job.estado != estado_anterior:
                    print(f"   📊 Estado cambió: {estado_anterior} → {job.estado}")
                    estado_anterior = job.estado
                    
                    if job.estado in ['COMPLETADO', 'FALLIDO']:
                        print(f"\n✅ Procesamiento finalizado!")
                        print(f"   Estado: {job.estado}")
                        print(f"   Exitosos: {job.exitosos}")
                        print(f"   Fallidos: {job.fallidos}")
                        print(f"   Progreso: {job.progreso}%")
                        
                        if job.errores_detalle:
                            print(f"\n   Errores encontrados: {len(job.errores_detalle)}")
                        
                        break
                else:
                    # Mostrar progreso si está procesando
                    if job.estado == 'PROCESANDO':
                        print(f"   ⏳ Procesando: {job.progreso:.1f}% - {job.exitosos} exitosos, {job.fallidos} fallidos")
        
        except KeyboardInterrupt:
            print("\n\n⌨️  Monitoreo interrumpido por el usuario")
            print(f"   El job {job_id} seguirá procesándose en background")
            print(f"   Puedes consultar el estado con el endpoint /status/{job_id}")
        
        print("\n" + "=" * 80)
        print("🎉 Prueba completada!")
        print("=" * 80)
        
        return True


if __name__ == '__main__':
    try:
        exito = test_worker_flow()
        sys.exit(0 if exito else 1)
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
