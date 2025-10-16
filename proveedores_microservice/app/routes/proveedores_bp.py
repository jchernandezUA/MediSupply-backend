from flask import Blueprint, request, jsonify
from app.extensions import ma
from app.services.proveedor_service import ProveedorService, ConflictError
from app.models.proveedor import Proveedor, Certificacion

proveedores_bp = Blueprint("proveedores", __name__)

# --- Esquemas para serialización ---
class CertificacionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Certificacion
        load_instance = True
        exclude = ['ruta_archivo']  # No exponer la ruta completa por seguridad

class ProveedorSchema(ma.SQLAlchemyAutoSchema):
    certificaciones = ma.Nested(CertificacionSchema, many=True)
    
    class Meta:
        model = Proveedor
        load_instance = True

proveedor_schema = ProveedorSchema()
proveedores_schema = ProveedorSchema(many=True)

# =============================================================================
# ENDPOINTS DE CONSULTA (HU KAN-92)
# =============================================================================

@proveedores_bp.route("/", methods=["GET"])
def listar_proveedores():
    """
    Endpoint para listar proveedores con búsqueda y filtros según HU KAN-92
    
    Query Parameters:
    - nombre: str (opcional) - Búsqueda parcial por nombre del proveedor
    - pais: str (opcional) - Filtro por país exacto
    - estado: str (opcional) - Filtro por estado 'Activo' o 'Inactivo'
    - estado_certificacion: str (opcional) - Filtro por estado de certificaciones:
        * 'vigente': Proveedores con certificaciones activas
        * 'sin_certificaciones': Proveedores sin certificaciones
        * 'vencida': Proveedores con certificaciones vencidas (futuro)
        * 'en_revision': Proveedores con certificaciones en revisión (futuro)
    - pagina: int (opcional, default=1) - Número de página para paginación
    - por_pagina: int (opcional, default=20, max=100) - Items por página
    
    Returns:
        200: Lista de proveedores con paginación
        {
            "mensaje": "Proveedores obtenidos exitosamente",
            "data": [...],
            "paginacion": {
                "total": int,
                "pagina": int,
                "por_pagina": int,
                "total_paginas": int
            }
        }
        400: Parámetros inválidos
        500: Error interno del servidor
    
    Criterios de aceptación (HU KAN-92):
    ✓ Lista con nombre, país, estado certificaciones, datos de contacto
    ✓ Búsqueda por nombre (parcial, case-insensitive)
    ✓ Filtro por país
    ✓ Filtro por estado de certificación
    ✓ Paginación para rendimiento
    ✓ Respuesta en ≤ 2 segundos
    """
    try:
        # Obtener parámetros de query
        filtros = {
            'nombre': request.args.get('nombre'),
            'pais': request.args.get('pais'),
            'estado': request.args.get('estado'),
            'estado_certificacion': request.args.get('estado_certificacion')
        }
        
        # Remover filtros None (no aplicados)
        filtros = {k: v for k, v in filtros.items() if v is not None}
        
        # Parámetros de paginación con validación
        try:
            pagina = int(request.args.get('pagina', 1))
            por_pagina = int(request.args.get('por_pagina', 20))
            
            # Validar rangos
            if pagina < 1:
                pagina = 1
            if por_pagina < 1 or por_pagina > 100:
                por_pagina = 20
                
        except ValueError:
            return jsonify({
                "error": "Los parámetros 'pagina' y 'por_pagina' deben ser números enteros válidos",
                "codigo": "PARAMETROS_INVALIDOS"
            }), 400
        
        # Llamar al servicio de listado
        resultado = ProveedorService.listar_proveedores(
            filtros=filtros,
            pagina=pagina,
            por_pagina=por_pagina
        )
        
        return jsonify({
            "mensaje": "Proveedores obtenidos exitosamente",
            "data": resultado['proveedores'],
            "paginacion": {
                "total": resultado['total'],
                "pagina": resultado['pagina'],
                "por_pagina": resultado['por_pagina'],
                "total_paginas": resultado['total_paginas']
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Error al obtener proveedores: {str(e)}",
            "codigo": "ERROR_INTERNO"
        }), 500


@proveedores_bp.route("/<int:proveedor_id>", methods=["GET"])
def obtener_detalle_proveedor(proveedor_id):
    """
    Endpoint para obtener el detalle completo de un proveedor según HU KAN-92
    
    Path Parameters:
    - proveedor_id: int - ID del proveedor a consultar
    
    Returns:
        200: Información completa del proveedor
        {
            "mensaje": "Proveedor obtenido exitosamente",
            "data": {
                "id": int,
                "nombre": str,
                "estado": str,
                "fecha_registro": str,
                "informacion_fiscal": {
                    "nit": str,
                    "pais": str,
                    "regimen": str
                },
                "contacto": {
                    "nombre_contacto": str,
                    "email": str,
                    "telefono": str,
                    "direccion": str
                },
                "estado_certificacion": str,
                "certificaciones": [...],
                "historial_compras": {...}
            }
        }
        404: Proveedor no encontrado
        500: Error interno del servidor
    
    Criterios de aceptación (HU KAN-92):
    ✓ Información fiscal validada (NIT, régimen, país)
    ✓ Datos de contacto completos
    ✓ Certificaciones adjuntas con fechas de vencimiento
    ✓ Historial de compras asociadas al proveedor
    ✓ Respuesta en ≤ 1 segundo
    """
    try:
        proveedor = ProveedorService.obtener_proveedor_por_id(proveedor_id)
        
        return jsonify({
            "mensaje": "Proveedor obtenido exitosamente",
            "data": proveedor
        }), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Proveedor no encontrado",
            "codigo": "PROVEEDOR_NO_ENCONTRADO"
        }), 404
    except Exception as e:
        return jsonify({
            "error": f"Error al obtener proveedor: {str(e)}",
            "codigo": "ERROR_INTERNO"
        }), 500


# =============================================================================
# ENDPOINTS DE GESTIÓN
# =============================================================================

# --- Ruta principal ---
@proveedores_bp.route("/", methods=["POST"])
def registrar_proveedor():
    """Endpoint para registrar un nuevo proveedor con certificaciones"""
    try:
        # Obtener datos del formulario
        data = request.form.to_dict()
        
        # Obtener archivos de certificación
        archivos = []
        if 'certificaciones' in request.files:
            archivos = request.files.getlist('certificaciones')
        
        # Crear proveedor usando el servicio
        nuevo_proveedor = ProveedorService.crear_proveedor(data, archivos)
        
        return jsonify({
            "mensaje": "Proveedor registrado exitosamente",
            "data": proveedor_schema.dump(nuevo_proveedor),
        }), 201
        
    except ConflictError as e:
        return jsonify({
            "error": "Proveedor con el mismo NIT o correo ya existe.",
            "codigo": "PROVEEDOR_DUPLICADO"
        }), 400  # 400 Bad Request para duplicados
    except ValueError as e:
        return jsonify({
            "error": str(e.args[0]),
            "codigo": "VALOR_INVALIDO"
        
        }), 400  # 400 Bad Request para validaciones
    except Exception as e:
        # Capturar específicamente errores de tamaño de archivo
        error_msg = str(e)
        if "413" in error_msg or "Request Entity Too Large" in error_msg:
            return jsonify({
                "error": "El archivo excede el tamaño máximo permitido de 5MB",
                "codigo": "ARCHIVO_MUY_GRANDE"
            }), 400
        
        return jsonify({"error": f"Error interno del servidor: {error_msg}"}), 500


# --- Endpoint de salud (útil para monitoreo) ---
@proveedores_bp.route("/health", methods=["GET"])
def health_check():
    """Endpoint de verificación de salud del microservicio"""
    return jsonify({
        "servicio": "Proveedores Microservice",
        "estado": "activo",
        "version": "1.0.0"
    }), 200


# --- Endpoint para cambiar estado del proveedor (opcional) ---
@proveedores_bp.route("/<int:proveedor_id>/estado", methods=["PATCH"])
def cambiar_estado_proveedor(proveedor_id):
    """Endpoint para activar/desactivar un proveedor"""
    try:
        from app.extensions import db
        
        proveedor = db.session.get(Proveedor, proveedor_id)
        if not proveedor:
            return jsonify({"error": "Proveedor no encontrado"}), 404
        
        data = request.get_json()
        nuevo_estado = data.get('estado')
        
        if nuevo_estado not in ['Activo', 'Inactivo']:
            return jsonify({"error": "Estado debe ser 'Activo' o 'Inactivo'"}), 400
        
        proveedor.estado = nuevo_estado
        db.session.commit()
        
        return jsonify({
            "mensaje": f"Proveedor {nuevo_estado.lower()}",
            "data": proveedor_schema.dump(proveedor)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Error al cambiar estado: {str(e)}"}), 500
