"""
Configuración de servicios AWS
"""
import boto3
import os
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


class AWSConfig:
    """Configuración centralizada de servicios AWS"""
    
    # SQS Configuration
    SQS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    SQS_QUEUE_URL = os.getenv('AWS_SQS_QUEUE_URL')
    SQS_QUEUE_NAME = os.getenv('SQS_QUEUE_NAME', 'productos-importacion-queue.fifo')
    SQS_DLQ_NAME = os.getenv('SQS_DLQ_NAME', 'productos-importacion-dlq')
    
    # S3 Configuration
    S3_BUCKET_CSV = os.getenv('AWS_S3_BUCKET_NAME', os.getenv('S3_BUCKET_CSV', 'medisupply-csv-imports'))
    S3_REGION = os.getenv('AWS_REGION', os.getenv('S3_REGION', 'us-east-1'))
    
    # AWS Credentials (mejor usar IAM roles en producción)
    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    # Feature flags
    USE_AWS = os.getenv('USE_AWS', 'false').lower() == 'true'
    
    @staticmethod
    def get_sqs_client():
        """
        Obtiene cliente de SQS configurado
        
        Returns:
            boto3.client: Cliente de SQS
        """
        try:
            if AWSConfig.AWS_ACCESS_KEY and AWSConfig.AWS_SECRET_KEY:
                return boto3.client(
                    'sqs',
                    region_name=AWSConfig.SQS_REGION,
                    aws_access_key_id=AWSConfig.AWS_ACCESS_KEY,
                    aws_secret_access_key=AWSConfig.AWS_SECRET_KEY
                )
            else:
                # Usar credenciales por defecto (IAM roles, profile, etc)
                return boto3.client('sqs', region_name=AWSConfig.SQS_REGION)
        except Exception as e:
            logger.error(f"Error creando cliente SQS: {e}")
            raise
    
    @staticmethod
    def get_s3_client():
        """
        Obtiene cliente de S3 configurado
        
        Returns:
            boto3.client: Cliente de S3
        """
        try:
            if AWSConfig.AWS_ACCESS_KEY and AWSConfig.AWS_SECRET_KEY:
                return boto3.client(
                    's3',
                    region_name=AWSConfig.S3_REGION,
                    aws_access_key_id=AWSConfig.AWS_ACCESS_KEY,
                    aws_secret_access_key=AWSConfig.AWS_SECRET_KEY
                )
            else:
                # Usar credenciales por defecto
                return boto3.client('s3', region_name=AWSConfig.S3_REGION)
        except Exception as e:
            logger.error(f"Error creando cliente S3: {e}")
            raise
    
    @staticmethod
    def get_queue_url(queue_name=None):
        """
        Obtiene URL de la cola SQS
        
        Args:
            queue_name: Nombre de la cola (opcional, usa default si no se proporciona)
            
        Returns:
            str: URL de la cola SQS
        """
        if not queue_name:
            queue_name = AWSConfig.SQS_QUEUE_NAME
            
        try:
            sqs = AWSConfig.get_sqs_client()
            response = sqs.get_queue_url(QueueName=queue_name)
            return response['QueueUrl']
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AWS.SimpleQueueService.NonExistentQueue':
                logger.error(f"Cola SQS no existe: {queue_name}")
            else:
                logger.error(f"Error obteniendo URL de cola: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado obteniendo URL: {e}")
            return None
    
    @staticmethod
    def verificar_configuracion():
        """
        Verifica que la configuración de AWS sea válida
        
        Returns:
            dict: Estado de la configuración
        """
        estado = {
            'aws_configurado': False,
            'sqs_disponible': False,
            's3_disponible': False,
            'errores': []
        }
        
        if not AWSConfig.USE_AWS:
            estado['errores'].append('AWS deshabilitado (USE_AWS=false)')
            return estado
        
        # Verificar credenciales
        if not AWSConfig.AWS_ACCESS_KEY or not AWSConfig.AWS_SECRET_KEY:
            estado['errores'].append('Credenciales AWS no configuradas')
            return estado
        
        estado['aws_configurado'] = True
        
        # Verificar SQS
        try:
            queue_url = AWSConfig.get_queue_url()
            if queue_url:
                estado['sqs_disponible'] = True
            else:
                estado['errores'].append('Cola SQS no encontrada')
        except Exception as e:
            estado['errores'].append(f'Error SQS: {str(e)}')
        
        # Verificar S3
        try:
            s3 = AWSConfig.get_s3_client()
            s3.head_bucket(Bucket=AWSConfig.S3_BUCKET_CSV)
            estado['s3_disponible'] = True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                estado['errores'].append('Bucket S3 no existe')
            elif error_code == '403':
                estado['errores'].append('Sin permisos para acceder al bucket S3')
            else:
                estado['errores'].append(f'Error S3: {str(e)}')
        except Exception as e:
            estado['errores'].append(f'Error verificando S3: {str(e)}')
        
        return estado
