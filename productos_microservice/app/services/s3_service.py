"""
Servicio para gestionar archivos CSV en AWS S3
"""
import boto3
from botocore.exceptions import ClientError
from app.config.aws_config import AWSConfig
from werkzeug.datastructures import FileStorage
import logging
from datetime import datetime
import uuid
import io

logger = logging.getLogger(__name__)


class S3Service:
    """Servicio para gestionar archivos CSV en S3"""
    
    @staticmethod
    def subir_csv(archivo, usuario_registro):
        """
        Sube un archivo CSV a S3
        
        Args:
            archivo: FileStorage object o file-like object
            usuario_registro: Usuario que sube el archivo
            
        Returns:
            tuple: (s3_key, nombre_archivo)
            
        Raises:
            Exception: Si hay error subiendo el archivo
        """
        try:
            s3 = AWSConfig.get_s3_client()
            
            # Obtener nombre del archivo
            if isinstance(archivo, FileStorage):
                nombre_archivo = archivo.filename
                archivo_stream = archivo.stream
            else:
                nombre_archivo = getattr(archivo, 'name', 'unknown.csv')
                archivo_stream = archivo
            
            # Generar nombre único para el archivo en S3
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            nombre_seguro = nombre_archivo.replace(' ', '_').replace('/', '_')
            s3_key = f"imports/{usuario_registro}/{timestamp}_{unique_id}_{nombre_seguro}"
            
            # Reiniciar el stream si es posible
            if hasattr(archivo_stream, 'seek'):
                archivo_stream.seek(0)
            
            # Subir archivo a S3
            s3.upload_fileobj(
                archivo_stream,
                AWSConfig.S3_BUCKET_CSV,
                s3_key,
                ExtraArgs={
                    'ContentType': 'text/csv',
                    'ServerSideEncryption': 'AES256',
                    'Metadata': {
                        'usuario': usuario_registro,
                        'fecha_subida': datetime.utcnow().isoformat(),
                        'nombre_original': nombre_archivo
                    }
                }
            )
            
            logger.info(f"Archivo subido exitosamente a S3: {s3_key}")
            
            return s3_key, nombre_archivo
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"Error ClientError subiendo archivo a S3: {error_code} - {error_msg}")
            raise Exception(f"Error subiendo archivo a S3: {error_msg}")
        except Exception as e:
            logger.error(f"Error inesperado subiendo archivo a S3: {str(e)}")
            raise Exception(f"Error subiendo archivo: {str(e)}")
    
    @staticmethod
    def descargar_csv(s3_key):
        """
        Descarga un archivo CSV desde S3
        
        Args:
            s3_key: Ruta del archivo en S3
            
        Returns:
            str: Contenido del archivo CSV
            
        Raises:
            Exception: Si hay error descargando el archivo
        """
        try:
            s3 = AWSConfig.get_s3_client()
            
            logger.info(f"Descargando archivo de S3: {s3_key}")
            
            response = s3.get_object(
                Bucket=AWSConfig.S3_BUCKET_CSV,
                Key=s3_key
            )
            
            # Leer contenido del archivo
            contenido = response['Body'].read().decode('utf-8')
            
            logger.info(f"Archivo descargado exitosamente: {len(contenido)} caracteres")
            
            return contenido
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.error(f"Archivo no encontrado en S3: {s3_key}")
                raise Exception(f"Archivo no encontrado: {s3_key}")
            elif error_code == 'NoSuchBucket':
                logger.error(f"Bucket no existe: {AWSConfig.S3_BUCKET_CSV}")
                raise Exception(f"Bucket no existe: {AWSConfig.S3_BUCKET_CSV}")
            else:
                error_msg = e.response['Error']['Message']
                logger.error(f"Error descargando archivo de S3: {error_code} - {error_msg}")
                raise Exception(f"Error descargando archivo: {error_msg}")
        except Exception as e:
            logger.error(f"Error inesperado descargando archivo: {str(e)}")
            raise Exception(f"Error descargando archivo: {str(e)}")
    
    @staticmethod
    def eliminar_csv(s3_key):
        """
        Elimina un archivo CSV de S3
        
        Args:
            s3_key: Ruta del archivo en S3
            
        Returns:
            bool: True si se eliminó exitosamente
            
        Raises:
            Exception: Si hay error eliminando el archivo
        """
        try:
            s3 = AWSConfig.get_s3_client()
            
            logger.info(f"Eliminando archivo de S3: {s3_key}")
            
            s3.delete_object(
                Bucket=AWSConfig.S3_BUCKET_CSV,
                Key=s3_key
            )
            
            logger.info(f"Archivo eliminado exitosamente de S3: {s3_key}")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"Error eliminando archivo de S3: {error_code} - {error_msg}")
            raise Exception(f"Error eliminando archivo: {error_msg}")
        except Exception as e:
            logger.error(f"Error inesperado eliminando archivo: {str(e)}")
            raise Exception(f"Error eliminando archivo: {str(e)}")
    
    @staticmethod
    def obtener_metadata(s3_key):
        """
        Obtiene metadata de un archivo en S3
        
        Args:
            s3_key: Ruta del archivo en S3
            
        Returns:
            dict: Metadata del archivo
        """
        try:
            s3 = AWSConfig.get_s3_client()
            
            response = s3.head_object(
                Bucket=AWSConfig.S3_BUCKET_CSV,
                Key=s3_key
            )
            
            return {
                'tamaño': response.get('ContentLength', 0),
                'content_type': response.get('ContentType'),
                'ultima_modificacion': response.get('LastModified'),
                'metadata': response.get('Metadata', {}),
                'etag': response.get('ETag')
            }
            
        except ClientError as e:
            logger.error(f"Error obteniendo metadata: {str(e)}")
            return None
    
    @staticmethod
    def listar_archivos(usuario=None, limite=100):
        """
        Lista archivos CSV en S3
        
        Args:
            usuario: Filtrar por usuario (opcional)
            limite: Máximo de archivos a retornar
            
        Returns:
            list: Lista de archivos
        """
        try:
            s3 = AWSConfig.get_s3_client()
            
            prefix = f"imports/{usuario}/" if usuario else "imports/"
            
            response = s3.list_objects_v2(
                Bucket=AWSConfig.S3_BUCKET_CSV,
                Prefix=prefix,
                MaxKeys=limite
            )
            
            archivos = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    archivos.append({
                        'key': obj['Key'],
                        'tamaño': obj['Size'],
                        'ultima_modificacion': obj['LastModified'].isoformat(),
                        'etag': obj['ETag']
                    })
            
            return archivos
            
        except ClientError as e:
            logger.error(f"Error listando archivos: {str(e)}")
            return []
    
    @staticmethod
    def verificar_bucket():
        """
        Verifica que el bucket S3 exista y sea accesible
        
        Returns:
            bool: True si el bucket es accesible
        """
        try:
            s3 = AWSConfig.get_s3_client()
            s3.head_bucket(Bucket=AWSConfig.S3_BUCKET_CSV)
            logger.info(f"Bucket S3 verificado: {AWSConfig.S3_BUCKET_CSV}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"Bucket no existe: {AWSConfig.S3_BUCKET_CSV}")
            elif error_code == '403':
                logger.error(f"Sin permisos para acceder al bucket: {AWSConfig.S3_BUCKET_CSV}")
            else:
                logger.error(f"Error verificando bucket: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado verificando bucket: {str(e)}")
            return False
