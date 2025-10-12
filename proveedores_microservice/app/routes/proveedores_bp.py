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
