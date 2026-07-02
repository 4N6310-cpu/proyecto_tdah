import os
import tempfile
import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# Import database core functions
from core.database import (
    conectar_db,
    get_usuario_by_username,
    get_pacientes_by_evaluador,
    get_sesiones_by_paciente,
    get_paciente_by_id,
    get_terapeuta_by_username,
    add_analisis_to_paciente,
    get_sesion_by_id,
    add_paciente,
    update_paciente,
    delete_paciente,
    update_session_notas
)

# Import services and helpers
from auth.services import AuthService
from analisis.uploader import VideoAnalysisUploader
from reportes.pdf_generator import PDFReportGenerator

# Initialize Flask with frontend folder as static source
app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app) # Enable Cross-Origin Resource Sharing for easy API access

# Configure uploads directory inside frontend static folder
UPLOAD_FOLDER = os.path.join(app.root_path, 'frontend', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    """Serves the main entry HTML of the Single Page Application."""
    return app.send_static_file('index.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """Handles evaluator authentication."""
    data = request.json
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"status": "error", "message": "Datos de acceso incompletos."}), 400
    
    username = data['username']
    password = data['password']
    
    # Authenticate via AuthService (adapting DB keys internally)
    terapeuta = AuthService.login(username, password)
    if terapeuta:
        return jsonify({
            "status": "success",
            "user": {
                "id": terapeuta.id,
                "nombre": terapeuta.nombre,
                "usuario": terapeuta.username,
                "rol": terapeuta.especialidad,
                "especialidad": terapeuta.especialidad
            }
        })
    else:
        return jsonify({"status": "error", "message": "Credenciales incorrectas. Intenta de nuevo."}), 401

@app.route('/api/pacientes', methods=['GET'])
def api_pacientes():
    """Returns the patients list assigned to the logged-in evaluator."""
    id_evaluador = request.args.get('id_evaluador')
    if not id_evaluador:
        return jsonify({"status": "error", "message": "El parámetro id_evaluador es requerido."}), 400
    
    try:
        pacientes = get_pacientes_by_evaluador(int(id_evaluador))
        return jsonify(pacientes)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error del servidor: {str(e)}"}), 500

@app.route('/api/pacientes', methods=['POST'])
def api_add_paciente():
    """Registra un nuevo paciente."""
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form
    else:
        data = request.json or {}
        
    if not data or 'nombre' not in data or 'fecha_nacimiento' not in data or 'id_evaluador' not in data:
        return jsonify({"status": "error", "message": "Faltan parámetros requeridos (nombre, fecha_nacimiento, id_evaluador)."}), 400
        
    nombre = data['nombre']
    fecha_nacimiento = data['fecha_nacimiento']
    historial_clinico = data.get('historial_clinico', '')
    id_evaluador = int(data['id_evaluador'])
    tutor = data.get('tutor', 'No asignado')
    numero_de_tutor = data.get('numero_de_tutor', 0)
    genero = data.get('genero', 'No especificado')
    
    # Check for file upload
    foto_perfil = None
    if 'foto_perfil' in request.files:
        file = request.files['foto_perfil']
        if file and file.filename != '':
            from werkzeug.utils import secure_filename
            import time
            filename = secure_filename(f"new_{int(time.time())}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            foto_perfil = f"uploads/{filename}"
            
    try:
        success = add_paciente(nombre, fecha_nacimiento, historial_clinico, id_evaluador, tutor, numero_de_tutor, foto_perfil, genero)
        if success:
            return jsonify({"status": "success", "message": "Paciente registrado correctamente."}), 201
        else:
            return jsonify({"status": "error", "message": "No se pudo registrar el paciente."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/pacientes/<int:id>', methods=['PUT'])
def api_update_paciente(id):
    """Actualiza un paciente existente."""
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form
    else:
        data = request.json or {}
        
    if not data or 'nombre' not in data or 'fecha_nacimiento' not in data:
        return jsonify({"status": "error", "message": "Faltan parámetros requeridos (nombre, fecha_nacimiento)."}), 400
        
    nombre = data['nombre']
    fecha_nacimiento = data['fecha_nacimiento']
    historial_clinico = data.get('historial_clinico', '')
    tutor = data.get('tutor', 'No asignado')
    numero_de_tutor = data.get('numero_de_tutor', 0)
    genero = data.get('genero', 'No especificado')
    
    # Check for file upload
    foto_perfil = None
    if 'foto_perfil' in request.files:
        file = request.files['foto_perfil']
        if file and file.filename != '':
            from werkzeug.utils import secure_filename
            filename = secure_filename(f"paciente_{id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            foto_perfil = f"uploads/{filename}"
            
    # If no new photo uploaded, keep current photo path
    if not foto_perfil:
        current_pac = get_paciente_by_id(id)
        if current_pac:
            foto_perfil = current_pac.get('foto_perfil')
            
    try:
        success = update_paciente(id, nombre, fecha_nacimiento, historial_clinico, tutor, numero_de_tutor, foto_perfil, genero)
        if success:
            return jsonify({"status": "success", "message": "Paciente actualizado correctamente."}), 200
        else:
            return jsonify({"status": "error", "message": "No se pudo actualizar el paciente."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/pacientes/<int:id>', methods=['DELETE'])
def api_delete_paciente(id):
    """Elimina un paciente."""
    try:
        success = delete_paciente(id)
        if success:
            return jsonify({"status": "success", "message": "Paciente eliminado correctamente."}), 200
        else:
            return jsonify({"status": "error", "message": "No se pudo eliminar el paciente."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/sesiones', methods=['GET'])
def api_sesiones():
    """Returns the full clinical dossier and session logs for a specific patient."""
    id_paciente = request.args.get('id_paciente')
    if not id_paciente:
        return jsonify({"status": "error", "message": "El parámetro id_paciente es requerido."}), 400
    
    try:
        paciente = get_paciente_by_id(int(id_paciente))
        if not paciente:
            return jsonify({"status": "error", "message": "Paciente no encontrado en el sistema."}), 404
            
        # Extract sessions list from patient object to match frontend API contract
        sesiones = paciente.pop("historial_analisis", [])
        return jsonify({
            "paciente": paciente,
            "sesiones": sesiones
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error del servidor: {str(e)}"}), 500

@app.route('/api/sesiones/<int:id>/notas', methods=['PUT'])
def api_update_session_notes(id):
    """Actualiza las observaciones/notas de una sesión específica."""
    data = request.json
    if not data or 'notas' not in data:
        return jsonify({"status": "error", "message": "Parámetro 'notas' es requerido."}), 400
        
    notas = data['notas']
    try:
        success = update_session_notas(id, notas)
        if success:
            return jsonify({"status": "success", "message": "Notas de sesión actualizadas correctamente."}), 200
        else:
            return jsonify({"status": "error", "message": "No se pudo actualizar las notas de sesión."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route('/api/analisis/video', methods=['POST'])
def api_analisis_video():
    """Receives an uploaded video file, processes it frame-by-frame using computer vision, and registers metrics."""
    if 'video' not in request.files or 'paciente_id' not in request.form:
        return jsonify({"status": "error", "message": "Archivo de video y paciente_id son requeridos."}), 400
        
    video_file = request.files['video']
    paciente_id = int(request.form['paciente_id'])
    
    if video_file.filename == '':
        return jsonify({"status": "error", "message": "El archivo de video provisto está vacío."}), 400
        
    try:
        from werkzeug.utils import secure_filename
        import time
        
        # Guardar el archivo en la carpeta local de uploads
        filename = secure_filename(f"video_{paciente_id}_{int(time.time())}_{video_file.filename}")
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video_file.save(video_path)
        
        # Procesar usando MediaPipe y BehavioralEngine desde la carpeta uploads
        res = VideoAnalysisUploader.procesar_archivo_video(
            path_video=video_path,
            paciente_id=paciente_id,
            callback_progreso=None
        )
        return jsonify({"status": "success", "result": res})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error en procesamiento de video: {str(e)}"}), 500

@app.route('/api/reportes/pdf/<int:session_id>', methods=['GET'])
def api_reporte_pdf(session_id):
    """Generates a medical-grade report PDF containing charts and conclusions for a specific session."""
    try:
        # Retrieve session
        sesion = get_sesion_by_id(session_id)
        if not sesion:
            return "Sesión no encontrada en el sistema.", 404
            
        # Retrieve patient
        paciente = get_paciente_by_id(sesion["id_paciente"])
        if not paciente:
            return "Paciente no encontrado.", 404
            
        # Find evaluator name to inject in report
        conexion = conectar_db()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT nombre FROM usuarios WHERE id = %s", (paciente["id_evaluador"],))
        evaluador = cursor.fetchone()
        paciente["terapeuta_nombre"] = evaluador["nombre"] if evaluador else "Especialista Asignado"
        cursor.close()
        conexion.close()
        
        # Build path to generate PDF
        temp_dir = tempfile.gettempdir()
        pdf_filename = f"Reporte_TDAH_{paciente['nombre'].replace(' ', '_')}_{session_id}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)
        
        # Compile PDF with reportlab
        PDFReportGenerator.generar_pdf_clinico(paciente, sesion, pdf_path)
        
        # Serve PDF to download
        response = send_file(pdf_path, mimetype='application/pdf', as_attachment=True, download_name=pdf_filename)
        
        # Clean up temporary PDF upon request completion
        @response.call_on_close
        def remove_file():
            try:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
            except Exception as e:
                app.logger.error(f"Error removing temporary PDF: {e}")
                
        return response
    except Exception as e:
        return f"Error crítico al generar reporte PDF: {str(e)}", 500

if __name__ == '__main__':
    # Run local dev server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
