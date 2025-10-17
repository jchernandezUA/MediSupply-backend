"""
Servicio para gestionar mensajes en AWS SQS
"""
import json
import boto3
from botocore.exceptions import ClientError
from app.config.aws_config import AWSConfig
from datetime import datetime
import logging
import hashlib

logger = logging.getLogger(__name__)


class SQSService:
    """Servicio para gestionar mensajes en cola SQS"""
    
    @staticmethod
    def enviar_job_a_cola(job_id, s3_key, nombre_archivo, usuario_registro, metadata=None):
        """
        Envía un job de importación a la cola SQS
        
        Args:
            job_id: ID del job
            s3_key: Ruta del archivo en S3
            nombre_archivo: Nombre original del archivo
            usuario_registro: Usuario que inició la importación
            metadata: Metadata adicional (opcional)
            
        Returns:
            dict: Respuesta de SQS con MessageId
            
        Raises:
            Exception: Si hay error enviando el mensaje
        """
        try:
            sqs = AWSConfig.get_sqs_client()
            queue_url = AWSConfig.get_queue_url()
            
            if not queue_url:
                raise Exception("No se pudo obtener URL de la cola SQS")
            
            # Preparar mensaje
            mensaje = {
                'job_id': job_id,
                's3_bucket': AWSConfig.S3_BUCKET_CSV,
                's3_key': s3_key,
                'nombre_archivo': nombre_archivo,
                'usuario_registro': usuario_registro,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            mensaje_json = json.dumps(mensaje)
            
            # Preparar atributos del mensaje
            message_attributes = {
                'JobId': {
                    'StringValue': job_id,
                    'DataType': 'String'
                },
                'TipoArchivo': {
                    'StringValue': 'CSV',
                    'DataType': 'String'
                },
                'Usuario': {
                    'StringValue': usuario_registro,
                    'DataType': 'String'
                }
            }
            
            # Parámetros base
            send_params = {
                'QueueUrl': queue_url,
                'MessageBody': mensaje_json,
                'MessageAttributes': message_attributes
            }
            
            # Si es cola FIFO, agregar parámetros adicionales
            if AWSConfig.SQS_QUEUE_NAME.endswith('.fifo'):
                send_params['MessageGroupId'] = 'productos-import'
                send_params['MessageDeduplicationId'] = job_id
            
            # Enviar mensaje a SQS
            response = sqs.send_message(**send_params)
            
            logger.info(f"Job {job_id} enviado a SQS. MessageId: {response.get('MessageId')}")
            
            return {
                'MessageId': response.get('MessageId'),
                'MD5OfMessageBody': response.get('MD5OfMessageBody'),
                'SequenceNumber': response.get('SequenceNumber')  # Solo para FIFO
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"Error ClientError enviando mensaje a SQS: {error_code} - {error_msg}")
            raise Exception(f"Error enviando mensaje a SQS: {error_msg}")
        except Exception as e:
            logger.error(f"Error inesperado enviando mensaje a SQS: {str(e)}")
            raise Exception(f"Error enviando mensaje: {str(e)}")
    
    @staticmethod
    def recibir_mensajes(max_mensajes=1, wait_time=20):
        """
        Recibe mensajes de la cola SQS (long polling)
        
        Args:
            max_mensajes: Número máximo de mensajes a recibir (1-10)
            wait_time: Tiempo de espera en segundos (0-20, long polling)
            
        Returns:
            list: Lista de mensajes recibidos
        """
        try:
            sqs = AWSConfig.get_sqs_client()
            queue_url = AWSConfig.get_queue_url()
            
            if not queue_url:
                logger.error("No se pudo obtener URL de la cola SQS")
                return []
            
            # Validar parámetros
            max_mensajes = min(max(1, max_mensajes), 10)
            wait_time = min(max(0, wait_time), 20)
            
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_mensajes,
                WaitTimeSeconds=wait_time,
                MessageAttributeNames=['All'],
                AttributeNames=['All'],
                VisibilityTimeout=300  # 5 minutos inicial
            )
            
            mensajes = response.get('Messages', [])
            
            if mensajes:
                logger.info(f"Recibidos {len(mensajes)} mensaje(s) de SQS")
            
            return mensajes
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"Error recibiendo mensajes de SQS: {error_code} - {error_msg}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado recibiendo mensajes: {str(e)}")
            return []
    
    @staticmethod
    def eliminar_mensaje(receipt_handle):
        """
        Elimina un mensaje de la cola después de procesarlo exitosamente
        
        Args:
            receipt_handle: Handle del mensaje a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente
            
        Raises:
            Exception: Si hay error eliminando el mensaje
        """
        try:
            sqs = AWSConfig.get_sqs_client()
            queue_url = AWSConfig.get_queue_url()
            
            if not queue_url:
                raise Exception("No se pudo obtener URL de la cola SQS")
            
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            
            logger.info("Mensaje eliminado de SQS exitosamente")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"Error eliminando mensaje de SQS: {error_code} - {error_msg}")
            raise Exception(f"Error eliminando mensaje: {error_msg}")
        except Exception as e:
            logger.error(f"Error inesperado eliminando mensaje: {str(e)}")
            raise Exception(f"Error eliminando mensaje: {str(e)}")
    
    @staticmethod
    def cambiar_visibilidad_mensaje(receipt_handle, timeout):
        """
        Cambia el timeout de visibilidad de un mensaje
        Útil para extender el tiempo de procesamiento
        
        Args:
            receipt_handle: Handle del mensaje
            timeout: Nuevo timeout en segundos (0-43200, 12 horas)
            
        Returns:
            bool: True si se cambió exitosamente
        """
        try:
            sqs = AWSConfig.get_sqs_client()
            queue_url = AWSConfig.get_queue_url()
            
            if not queue_url:
                raise Exception("No se pudo obtener URL de la cola SQS")
            
            # Validar timeout (max 12 horas)
            timeout = min(max(0, timeout), 43200)
            
            sqs.change_message_visibility(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=timeout
            )
            
            logger.info(f"Visibilidad del mensaje cambiada a {timeout} segundos")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"Error cambiando visibilidad: {error_code} - {error_msg}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado cambiando visibilidad: {str(e)}")
            return False
    
    @staticmethod
    def obtener_atributos_cola():
        """
        Obtiene atributos y estadísticas de la cola
        
        Returns:
            dict: Atributos de la cola
        """
        try:
            sqs = AWSConfig.get_sqs_client()
            queue_url = AWSConfig.get_queue_url()
            
            if not queue_url:
                return None
            
            response = sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['All']
            )
            
            attributes = response.get('Attributes', {})
            
            return {
                'mensajes_disponibles': int(attributes.get('ApproximateNumberOfMessages', 0)),
                'mensajes_en_vuelo': int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0)),
                'mensajes_retrasados': int(attributes.get('ApproximateNumberOfMessagesDelayed', 0)),
                'creado_timestamp': attributes.get('CreatedTimestamp'),
                'ultima_modificacion': attributes.get('LastModifiedTimestamp'),
                'visibility_timeout': int(attributes.get('VisibilityTimeout', 0)),
                'message_retention_period': int(attributes.get('MessageRetentionPeriod', 0)),
                'max_message_size': int(attributes.get('MaximumMessageSize', 0)),
                'es_fifo': attributes.get('FifoQueue') == 'true'
            }
            
        except ClientError as e:
            logger.error(f"Error obteniendo atributos de cola: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado obteniendo atributos: {str(e)}")
            return None
    
    @staticmethod
    def purgar_cola():
        """
        Elimina todos los mensajes de la cola
        ADVERTENCIA: Esta operación es irreversible
        
        Returns:
            bool: True si se purgó exitosamente
        """
        try:
            sqs = AWSConfig.get_sqs_client()
            queue_url = AWSConfig.get_queue_url()
            
            if not queue_url:
                raise Exception("No se pudo obtener URL de la cola SQS")
            
            sqs.purge_queue(QueueUrl=queue_url)
            
            logger.warning("Cola SQS purgada - todos los mensajes eliminados")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'PurgeQueueInProgress':
                logger.warning("Ya hay una operación de purga en progreso")
            else:
                logger.error(f"Error purgando cola: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado purgando cola: {str(e)}")
            return False
    
    @staticmethod
    def verificar_cola():
        """
        Verifica que la cola SQS exista y sea accesible
        
        Returns:
            bool: True si la cola es accesible
        """
        try:
            queue_url = AWSConfig.get_queue_url()
            if not queue_url:
                logger.error(f"Cola SQS no encontrada: {AWSConfig.SQS_QUEUE_NAME}")
                return False
            
            # Intentar obtener atributos para verificar acceso
            attributes = SQSService.obtener_atributos_cola()
            if attributes:
                logger.info(f"Cola SQS verificada: {AWSConfig.SQS_QUEUE_NAME}")
                logger.info(f"Mensajes disponibles: {attributes['mensajes_disponibles']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando cola SQS: {str(e)}")
            return False
