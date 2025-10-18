"""
Tests unitarios para el worker de procesamiento SQS
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
from io import BytesIO

from app import create_app
from app.extensions import db
from app.models.import_job import ImportJob
from app.workers.sqs_worker import procesar_mensaje


@pytest.fixture
def app_worker():
    """Crear aplicación de prueba para el worker"""
    app = create_app()
    app.config.from_object('app.config.TestingConfig')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def mock_sqs_message():
    """Fixture para simular un mensaje SQS"""
    return {
        'MessageId': 'test-message-id-123',
        'ReceiptHandle': 'test-receipt-handle',
        'Body': json.dumps({
            'job_id': 'test-job-id-456',
            's3_key': 'imports/test_user/20251017_abc123_test.csv',
            'usuario_registro': 'test_user@example.com',
            'timestamp': '20251017_120000'
        })
    }


@pytest.fixture
def mock_csv_content():
    """Fixture para simular contenido CSV"""
    return """sku,nombre,descripcion,precio,categoria,proveedor_id,codigo_tipo_producto,fecha_vencimiento,lote,requiere_receta,es_generico,temperatura_almacenamiento,indicaciones,contraindicaciones,efectos_secundarios,dosis_recomendada
SKU-TEST-001,Producto Test 1,Descripción test 1,10.50,Analgésicos,1,MEDICAMENTO,31/12/2025,LOTE-001,false,true,25,Indicaciones test,Contraindicaciones test,Efectos test,1 tableta
SKU-TEST-002,Producto Test 2,Descripción test 2,20.00,Antibióticos,1,MEDICAMENTO,31/12/2025,LOTE-002,true,false,4,Indicaciones test,Contraindicaciones test,Efectos test,2 tabletas
SKU-TEST-003,Producto Test 3,Descripción test 3,15.75,Vitaminas,1,SUPLEMENTO,31/12/2025,LOTE-003,false,false,25,Indicaciones test,Contraindicaciones test,Efectos test,1 cápsula
"""


class TestWorkerProcesarMensaje:
    """Tests para la función procesar_mensaje del worker"""
    
    def test_procesar_mensaje_exitoso(self, app_worker, mock_sqs_message, mock_csv_content):
        """Test: Procesar mensaje SQS exitosamente"""
        with app_worker.app_context():
            # Crear ImportJob en la base de datos
            job = ImportJob(
                id='test-job-id-456',
                nombre_archivo='test.csv',
                s3_key='imports/test_user/20251017_abc123_test.csv',
                total_filas=3,
                usuario_registro='test_user@example.com',
                sqs_message_id='test-message-id-123',
                estado='EN_COLA'  # Estado inicial para procesamiento
            )
            db.session.add(job)
            db.session.commit()
            
            # Mock de servicios
            mock_sqs_service = Mock()
            mock_sqs_service.eliminar_mensaje.return_value = True
            mock_sqs_service.cambiar_visibilidad_mensaje.return_value = True
            
            mock_s3_service = Mock()
            mock_s3_service.descargar_csv.return_value = mock_csv_content
            
            # Mock de CSVProductoService
            with patch('app.workers.sqs_worker.CSVProductoService') as MockCSV:
                mock_csv_instance = MockCSV.return_value
                mock_csv_instance.procesar_csv_desde_contenido.return_value = {
                    'exitosos': 3,
                    'fallidos': 0,
                    'detalles_errores': []
                }
                
                # Ejecutar procesamiento
                resultado = procesar_mensaje(
                    app_worker,
                    mock_sqs_message,
                    mock_sqs_service,
                    mock_s3_service
                )
                
                # Verificaciones
                assert resultado is True
                
                # Verificar que se llamaron los métodos correctos
                mock_s3_service.descargar_csv.assert_called_once_with(
                    'imports/test_user/20251017_abc123_test.csv'
                )
                mock_sqs_service.eliminar_mensaje.assert_called_once()
                
                # Verificar estado del job
                db.session.refresh(job)
                assert job.estado == 'COMPLETADO'
                assert job.exitosos == 3
                assert job.fallidos == 0
    
    def test_procesar_mensaje_con_errores_validacion(self, app_worker, mock_sqs_message, mock_csv_content):
        """Test: Procesar mensaje con errores de validación"""
        with app_worker.app_context():
            # Crear ImportJob
            job = ImportJob(
                id='test-job-id-456',
                nombre_archivo='test.csv',
                s3_key='imports/test_user/20251017_abc123_test.csv',
                total_filas=5,
                usuario_registro='test_user@example.com',
                estado='EN_COLA'
            )
            db.session.add(job)
            db.session.commit()
            
            # Mock de servicios
            mock_sqs_service = Mock()
            mock_sqs_service.eliminar_mensaje.return_value = True
            mock_sqs_service.cambiar_visibilidad_mensaje.return_value = True
            
            mock_s3_service = Mock()
            mock_s3_service.descargar_csv.return_value = mock_csv_content
            
            # Mock de CSVProductoService con errores
            with patch('app.workers.sqs_worker.CSVProductoService') as MockCSV:
                mock_csv_instance = MockCSV.return_value
                mock_csv_instance.procesar_csv_desde_contenido.return_value = {
                    'exitosos': 3,
                    'fallidos': 2,
                    'detalles_errores': [
                        {
                            'fila': 2,
                            'sku': 'SKU-DUP-001',
                            'error': 'SKU duplicado',
                            'codigo': 'SKU_DUPLICADO'
                        },
                        {
                            'fila': 4,
                            'sku': 'SKU-INV-001',
                            'error': 'Precio inválido',
                            'codigo': 'PRECIO_INVALIDO'
                        }
                    ]
                }
                
                # Ejecutar procesamiento
                resultado = procesar_mensaje(
                    app_worker,
                    mock_sqs_message,
                    mock_sqs_service,
                    mock_s3_service
                )
                
                # Verificaciones
                assert resultado is True
                
                # Verificar estado del job
                db.session.refresh(job)
                assert job.estado == 'COMPLETADO'
                assert job.exitosos == 3
                assert job.fallidos == 2
                
                # Verificar que se guardaron los errores
                assert job.detalles_errores is not None
                assert 'errores' in job.detalles_errores
                assert len(job.detalles_errores['errores']) == 2
    
    def test_procesar_mensaje_job_no_existe(self, app_worker, mock_sqs_message):
        """Test: Intentar procesar mensaje cuando el job no existe en BD"""
        with app_worker.app_context():
            # Mock de servicios
            mock_sqs_service = Mock()
            mock_sqs_service.eliminar_mensaje.return_value = True
            
            mock_s3_service = Mock()
            
            # Ejecutar procesamiento (job no existe)
            resultado = procesar_mensaje(
                app_worker,
                mock_sqs_message,
                mock_sqs_service,
                mock_s3_service
            )
            
            # Debe retornar False porque el job no existe
            assert resultado is False
            
            # Debe eliminar el mensaje inválido
            mock_sqs_service.eliminar_mensaje.assert_called_once()
    
    def test_procesar_mensaje_error_descarga_s3(self, app_worker, mock_sqs_message):
        """Test: Error al descargar archivo de S3"""
        with app_worker.app_context():
            # Crear ImportJob
            job = ImportJob(
                id='test-job-id-456',
                nombre_archivo='test.csv',
                s3_key='imports/test_user/20251017_abc123_test.csv',
                total_filas=3,
                usuario_registro='test_user@example.com',
                estado='EN_COLA'
            )
            db.session.add(job)
            db.session.commit()
            
            # Mock de servicios
            mock_sqs_service = Mock()
            mock_sqs_service.eliminar_mensaje.return_value = True
            
            mock_s3_service = Mock()
            mock_s3_service.descargar_csv.return_value = None  # Simular error
            
            # Ejecutar procesamiento
            resultado = procesar_mensaje(
                app_worker,
                mock_sqs_message,
                mock_sqs_service,
                mock_s3_service
            )
            
            # Debe retornar False por el error
            assert resultado is False
            
            # Verificar que el job se marcó como fallido
            db.session.refresh(job)
            assert job.estado == 'FALLIDO'
            
            # Debe eliminar el mensaje
            mock_sqs_service.eliminar_mensaje.assert_called_once()
    
    def test_procesar_mensaje_json_invalido(self, app_worker):
        """Test: Mensaje SQS con JSON inválido"""
        with app_worker.app_context():
            mensaje_invalido = {
                'MessageId': 'test-message-id',
                'ReceiptHandle': 'test-receipt',
                'Body': 'esto no es JSON válido {'
            }
            
            # Mock de servicios
            mock_sqs_service = Mock()
            mock_sqs_service.eliminar_mensaje.return_value = True
            
            mock_s3_service = Mock()
            
            # Ejecutar procesamiento
            resultado = procesar_mensaje(
                app_worker,
                mensaje_invalido,
                mock_sqs_service,
                mock_s3_service
            )
            
            # Debe retornar False
            assert resultado is False
    
    def test_procesar_mensaje_campos_faltantes(self, app_worker):
        """Test: Mensaje SQS sin campos requeridos"""
        with app_worker.app_context():
            mensaje_incompleto = {
                'MessageId': 'test-message-id',
                'ReceiptHandle': 'test-receipt',
                'Body': json.dumps({
                    'job_id': 'test-job-id-456'
                    # Falta s3_key y usuario_registro
                })
            }
            
            # Mock de servicios
            mock_sqs_service = Mock()
            mock_sqs_service.eliminar_mensaje.return_value = True
            
            mock_s3_service = Mock()
            
            # Ejecutar procesamiento
            resultado = procesar_mensaje(
                app_worker,
                mensaje_incompleto,
                mock_sqs_service,
                mock_s3_service
            )
            
            # Debe retornar False
            assert resultado is False
            
            # Debe eliminar el mensaje inválido
            mock_sqs_service.eliminar_mensaje.assert_called_once()


class TestWorkerErrorHandling:
    """Tests para manejo de errores del worker"""
    
    def test_worker_maneja_excepcion_inesperada(self, app_worker, mock_sqs_message):
        """Test: Worker maneja excepciones inesperadas correctamente"""
        with app_worker.app_context():
            # Crear ImportJob
            job = ImportJob(
                id='test-job-id-456',
                nombre_archivo='test.csv',
                s3_key='imports/test_user/test.csv',
                total_filas=3,
                usuario_registro='test_user@example.com',
                estado='EN_COLA'
            )
            db.session.add(job)
            db.session.commit()
            
            # Mock de servicios
            mock_sqs_service = Mock()
            
            mock_s3_service = Mock()
            mock_s3_service.descargar_csv.side_effect = RuntimeError("Error inesperado")
            
            # Ejecutar procesamiento
            resultado = procesar_mensaje(
                app_worker,
                mock_sqs_message,
                mock_sqs_service,
                mock_s3_service
            )
            
            # Debe retornar False
            assert resultado is False
            
            # Verificar que el job se marcó como fallido
            db.session.refresh(job)
            assert job.estado == 'FALLIDO'
    
    def test_worker_limita_cantidad_errores_guardados(self, app_worker, mock_sqs_message, mock_csv_content):
        """Test: Worker limita la cantidad de errores guardados"""
        with app_worker.app_context():
            # Crear ImportJob
            job = ImportJob(
                id='test-job-id-456',
                nombre_archivo='test.csv',
                s3_key='imports/test_user/test.csv',
                total_filas=200,
                usuario_registro='test_user@example.com',
                estado='EN_COLA'
            )
            db.session.add(job)
            db.session.commit()
            
            # Crear muchos errores (más de 100)
            errores = [
                {
                    'fila': i,
                    'sku': f'SKU-{i}',
                    'error': 'Error de validación',
                    'codigo': 'VALIDACION'
                }
                for i in range(150)
            ]
            
            # Mock de servicios
            mock_sqs_service = Mock()
            mock_sqs_service.eliminar_mensaje.return_value = True
            mock_sqs_service.cambiar_visibilidad_mensaje.return_value = True
            
            mock_s3_service = Mock()
            mock_s3_service.descargar_csv.return_value = mock_csv_content
            
            # Mock de CSVProductoService con muchos errores
            with patch('app.workers.sqs_worker.CSVProductoService') as MockCSV:
                mock_csv_instance = MockCSV.return_value
                mock_csv_instance.procesar_csv_desde_contenido.return_value = {
                    'exitosos': 50,
                    'fallidos': 150,
                    'detalles_errores': errores
                }
                
                # Ejecutar procesamiento
                procesar_mensaje(
                    app_worker,
                    mock_sqs_message,
                    mock_sqs_service,
                    mock_s3_service
                )
                
                # Verificar que se limitaron los errores a 100
                db.session.refresh(job)
                assert job.detalles_errores is not None
                assert 'errores' in job.detalles_errores
                assert len(job.detalles_errores['errores']) == 100
                assert job.detalles_errores['total_errores'] == 150
                assert job.detalles_errores['errores_capturados'] == 100


class TestWorkerEstadosJob:
    """Tests para transiciones de estado del ImportJob"""
    
    def test_job_transicion_en_cola_a_procesando(self, app_worker, mock_sqs_message, mock_csv_content):
        """Test: Job transiciona de EN_COLA a PROCESANDO"""
        with app_worker.app_context():
            # Crear ImportJob
            job = ImportJob(
                id='test-job-id-456',
                nombre_archivo='test.csv',
                s3_key='imports/test_user/test.csv',
                total_filas=3,
                usuario_registro='test_user@example.com',
                estado='EN_COLA'
            )
            db.session.add(job)
            db.session.commit()
            
            assert job.estado == 'EN_COLA'
            
            # Mock de servicios
            mock_sqs_service = Mock()
            mock_sqs_service.eliminar_mensaje.return_value = True
            mock_sqs_service.cambiar_visibilidad_mensaje.return_value = True
            
            mock_s3_service = Mock()
            mock_s3_service.descargar_csv.return_value = mock_csv_content
            
            # Mock de CSVProductoService
            with patch('app.workers.sqs_worker.CSVProductoService') as MockCSV:
                mock_csv_instance = MockCSV.return_value
                mock_csv_instance.procesar_csv_desde_contenido.return_value = {
                    'exitosos': 3,
                    'fallidos': 0,
                    'detalles_errores': []
                }
                
                # Ejecutar procesamiento
                procesar_mensaje(
                    app_worker,
                    mock_sqs_message,
                    mock_sqs_service,
                    mock_s3_service
                )
                
                # Verificar transición de estado
                db.session.refresh(job)
                assert job.estado == 'COMPLETADO'
                assert job.fecha_inicio_proceso is not None
                assert job.fecha_finalizacion is not None
    
    def test_job_transicion_a_fallido_en_error(self, app_worker, mock_sqs_message):
        """Test: Job transiciona a FALLIDO cuando hay error"""
        with app_worker.app_context():
            # Crear ImportJob
            job = ImportJob(
                id='test-job-id-456',
                nombre_archivo='test.csv',
                s3_key='imports/test_user/test.csv',
                total_filas=3,
                usuario_registro='test_user@example.com',
                estado='EN_COLA'
            )
            db.session.add(job)
            db.session.commit()
            
            # Mock de servicios
            mock_sqs_service = Mock()
            
            mock_s3_service = Mock()
            mock_s3_service.descargar_csv.return_value = None  # Simular error
            
            # Ejecutar procesamiento
            procesar_mensaje(
                app_worker,
                mock_sqs_message,
                mock_sqs_service,
                mock_s3_service
            )
            
            # Verificar transición a FALLIDO
            db.session.refresh(job)
            assert job.estado == 'FALLIDO'
            assert job.mensaje_error is not None
