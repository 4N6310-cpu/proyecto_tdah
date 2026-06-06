import mysql.connector
from mysql.connector import Error
import datetime

# CONFIGURACIÓN DE TU INSTANCIA DE MYSQL WORKBENCH
DB_CONFIG = {
    "host": "localhost",       # Cambiar si tu Workbench está en la nube o en otro servidor
    "user": "root",            # Tu usuario de MySQL
    "password": "angelo2oo4", # Reemplaza con tu contraseña de MySQL Workbench
    "database": "feria"        # Nombre exacto de tu base de datos
}

def conectar_db():
    """Establece y retorna la conexión activa con MySQL Workbench."""
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"Error crítico al conectar a MySQL Workbench: {e}")
        return None

# =====================================================================
# FUNCIONES DE CONSULTA Y ESCRITURA REALES (SQL DIRECTO)
# =====================================================================

def get_usuario_by_username(username):
    """Busca en la tabla usuarios por la columna 'usuario' (Login)."""
    conexion = conectar_db()
    if not conexion: return None
    
    cursor = conexion.cursor(dictionary=True) # Retorna filas como diccionarios
    query = "SELECT id, nombre, usuario, password, rol FROM usuarios WHERE usuario = %s"
    
    try:
        cursor.execute(query, (username,))
        usuario = cursor.fetchone()
        return usuario
    except Error as e:
        print(f"Error en login query: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()

def get_pacientes_by_evaluador(id_evaluador):
    """Filtra los pacientes asignados al evaluador logueado."""
    conexion = conectar_db()
    if not conexion: return []
    
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT id, nombre, fecha_nacimiento, genero, id_evaluador, tutor, numero_de_tutor, historial_clinico, foto_perfil FROM pacientes WHERE id_evaluador = %s"
    
    try:
        cursor.execute(query, (id_evaluador,))
        pacientes = cursor.fetchall()
        
        for pac in pacientes:
            tutor_real = pac.get('tutor')
            telefono_real = pac.get('numero_de_tutor')

            # 1. Guardamos el nombre del tutor
            pac["tutor_nombre"] = tutor_real if tutor_real else "No asignado"

            # 2. Guardamos el celular de forma independiente
            if telefono_real and str(telefono_real).strip() != "":
                pac["tutor_celular"] = telefono_real
            else:
                pac["tutor_celular"] = "No tiene"
            
            # 3. Procesamiento seguro de la Edad
            fecha_nac = pac["fecha_nacimiento"]
            if fecha_nac:
                # Si la base de datos devuelve la fecha como string, la convertimos a objeto date
                if isinstance(fecha_nac, str):
                    fecha_nac = datetime.datetime.strptime(fecha_nac, "%Y-%m-%d").date()
                
                hoy = datetime.date.today()
                pac["edad"] = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
                pac["fecha_nacimiento"] = fecha_nac.strftime("%Y-%m-%d")
            else:
                pac["edad"] = 0 
            
            # 4. Mantenemos 'contacto' por si alguna otra vista vieja lo sigue usando
            pac["nombre_tutor"] = f"{pac['tutor_nombre']}"
            pac["contacto"] = f"{pac['tutor_celular']}"
            
            # 5. Notas reales/predeterminadas
            pac["notas"] = pac.get("historial_clinico") if pac.get("historial_clinico") else "Paciente en seguimiento de comportamiento." 

        return pacientes
    except Error as e:
        print(f"Error al obtener pacientes: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()    
def generar_timeline_sintetico(duracion, atencion_pct, fidgeting_val):
    import random
    timeline = []
    # Usar una semilla pseudo-aleatoria basada en la duración y atención para consistencia
    random.seed(int(duracion) + int(atencion_pct))
    for s in range(0, int(duracion) + 1):
        att = 1 if random.random() * 100 < atencion_pct else 0
        fid = max(0.0, min(10.0, fidgeting_val + random.uniform(-1.0, 1.0)))
        timeline.append({
            "segundo": s,
            "atencion": att,
            "fidgeting_score": round(fid, 2)
        })
    return timeline

def get_sesiones_by_paciente(id_paciente):
    """Obtiene el histórico de análisis de la tabla sesiones de un niño."""
    conexion = conectar_db()
    if not conexion: return []
    
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT id, id_paciente, fecha_hora, duracion, indice_atencion, hiperactividad, distraccion, notas FROM sesiones WHERE id_paciente = %s ORDER BY fecha_hora DESC"
    
    try:
        cursor.execute(query, (id_paciente,))
        rows = cursor.fetchall()
        sesiones_formateadas = []
        for r in rows:
            duracion = r["duracion"] if r["duracion"] else 120
            
            # Parsear porcentaje de atención
            indice = r["indice_atencion"]
            atencion_pct = 60.0
            if indice:
                if "%" in str(indice):
                    try:
                        atencion_pct = float(str(indice).replace("%", ""))
                    except ValueError:
                        pass
                elif str(indice).upper() == "ALTO":
                    atencion_pct = 85.0
                elif str(indice).upper() == "MEDIO":
                    atencion_pct = 60.0
                elif str(indice).upper() == "BAJO":
                    atencion_pct = 35.0
                else:
                    try:
                        atencion_pct = float(indice)
                    except ValueError:
                        pass
            
            fidgeting_score = round(r["hiperactividad"] * 10.0, 1) if r["hiperactividad"] is not None else 5.0
            distraccion_ratio = r["distraccion"] if r["distraccion"] is not None else 0.3
            
            eventos_dist = max(1, int(distraccion_ratio * 8))
            tiempo_dist = int(duracion * distraccion_ratio)
            
            if atencion_pct >= 70.0 and fidgeting_score < 4.0:
                diag = f"El paciente muestra un nivel de atención sostenida adecuado ({atencion_pct:.1f}%) con escaso registro de hiperactividad motora ({fidgeting_score:.1f}/10). Patrón dentro de la media."
            elif atencion_pct < 65.0 and fidgeting_score >= 5.5:
                diag = f"Foco visual inestable con múltiples desviaciones de mirada ({atencion_pct:.1f}% de atención) y nivel de fidgeting elevado ({fidgeting_score:.1f}/10). Conducta compatible con déficit atencional e inquietud motora severa."
            else:
                diag = f"Desempeño general moderado. Foco atencional fluctuante ({atencion_pct:.1f}%) con presencia de movimientos corporales compensatorios y fidgeting leve ({fidgeting_score:.1f}/10)."
            
            fecha_str = r["fecha_hora"].strftime("%Y-%m-%d %H:%M") if r["fecha_hora"] else datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            
            timeline = generar_timeline_sintetico(duracion, atencion_pct, fidgeting_score)
            
            sesiones_formateadas.append({
                "id": r["id"],
                "id_paciente": r["id_paciente"],
                "fecha": fecha_str,
                "duracion_total_seg": duracion,
                "atencion_porcentaje": atencion_pct,
                "fidgeting_score": fidgeting_score,
                "distraccion": distraccion_ratio,
                "eventos_distraccion": eventos_dist,
                "tiempo_distraccion_seg": tiempo_dist,
                "diagnostico_auto": diag,
                "video_origen": f"sesion_video_{r['id']}.mp4",
                "timeline": timeline,
                "intervalos_distraccion": [],
                "notas": r["notas"]
            })
        return sesiones_formateadas
    except Error as e:
        print(f"Error al obtener sesiones: {e}")
        return []
    finally:
        cursor.close()
        conexion.close()

def get_paciente_by_id(paciente_id):
    """Busca un paciente por ID y enriquece la estructura con datos esperados por el frontend y reportes."""
    conexion = conectar_db()
    if not conexion: return None
    
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT id, nombre, fecha_nacimiento, genero, id_evaluador, tutor, numero_de_tutor, historial_clinico, foto_perfil FROM pacientes WHERE id = %s"
    
    try:
        cursor.execute(query, (paciente_id,))
        paciente = cursor.fetchone()
        if paciente:
            fecha_nac = paciente["fecha_nacimiento"]
            if fecha_nac:
                if isinstance(fecha_nac, str):
                    fecha_nac = datetime.datetime.strptime(fecha_nac, "%Y-%m-%d").date()
                hoy = datetime.date.today()
                paciente["edad"] = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
                paciente["fecha_nacimiento"] = fecha_nac.strftime("%Y-%m-%d")
            else:
                paciente["edad"] = 0
            
            paciente["tutor"] = paciente['tutor'] if paciente['tutor'] else "No asignado"
            numero = paciente.get('numero_de_tutor')
            paciente["celular"] = str(numero) if numero is not None else "no tiene"
            paciente["notas"] = paciente.get("historial_clinico") if paciente.get("historial_clinico") else "Paciente en seguimiento de comportamiento. Se observa inquietud motora en entornos de concentración estructurada."
            paciente["historial_analisis"] = get_sesiones_by_paciente(paciente_id)
            
        return paciente
    except Error as e:
        print(f"Error al obtener paciente: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()

def get_terapeuta_by_username(username):
    """Adaptador que busca un usuario por su nombre de usuario y lo formatea para el AuthService."""
    user_data = get_usuario_by_username(username)
    if not user_data:
        return None
    return {
        "id": user_data["id"],
        "username": user_data["usuario"],
        "nombre": user_data["nombre"],
        "especialidad": user_data["rol"],
        "email": f"{user_data['usuario']}@clinica.com",
        "password_hash": user_data["password"]
    }

def add_analisis_to_paciente(paciente_id, analisis):
    """Inserta una sesión de análisis en la tabla sesiones."""
    conexion = conectar_db()
    if not conexion: return False
    cursor = conexion.cursor()
    
    duracion = analisis.get("duracion_total_seg", 120)
    atencion_pct = analisis.get("atencion_porcentaje", 70.0)
    fidgeting = analisis.get("fidgeting_score", 5.0)
    distraccion = 0.0
    if duracion > 0:
        distraccion = analisis.get("tiempo_distraccion_seg", 0) / duracion
        
    indice_atencion = f"{atencion_pct:.1f}%"
    hiperactividad = fidgeting / 10.0
    
    query = """
        INSERT INTO sesiones (id_paciente, fecha_hora, duracion, indice_atencion, hiperactividad, distraccion)
        VALUES (%s, NOW(), %s, %s, %s, %s)
    """
    try:
        cursor.execute(query, (paciente_id, duracion, indice_atencion, hiperactividad, distraccion))
        conexion.commit()
        return True
    except Error as e:
        print(f"Error al guardar sesión: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

# Aliases de compatibilidad
get_pacientes_by_terapeuta = get_pacientes_by_evaluador

def get_sesion_by_id(session_id):
    """Busca una sesión por su ID y la formatea."""
    conexion = conectar_db()
    if not conexion: return None
    
    cursor = conexion.cursor(dictionary=True)
    query = "SELECT id, id_paciente, fecha_hora, duracion, indice_atencion, hiperactividad, distraccion, notas FROM sesiones WHERE id = %s"
    
    try:
        cursor.execute(query, (session_id,))
        r = cursor.fetchone()
        if r:
            duracion = r["duracion"] if r["duracion"] else 120
            
            # Parsear porcentaje de atención
            indice = r["indice_atencion"]
            atencion_pct = 60.0
            if indice:
                if "%" in str(indice):
                    try:
                        atencion_pct = float(str(indice).replace("%", ""))
                    except ValueError:
                        pass
                elif str(indice).upper() == "ALTO":
                    atencion_pct = 85.0
                elif str(indice).upper() == "MEDIO":
                    atencion_pct = 60.0
                elif str(indice).upper() == "BAJO":
                    atencion_pct = 35.0
                else:
                    try:
                        atencion_pct = float(indice)
                    except ValueError:
                        pass
            
            fidgeting_score = round(r["hiperactividad"] * 10.0, 1) if r["hiperactividad"] is not None else 5.0
            distraccion_ratio = r["distraccion"] if r["distraccion"] is not None else 0.3
            
            eventos_dist = max(1, int(distraccion_ratio * 8))
            tiempo_dist = int(duracion * distraccion_ratio)
            
            if atencion_pct >= 70.0 and fidgeting_score < 4.0:
                diag = f"El paciente muestra un nivel de atención sostenida adecuado ({atencion_pct:.1f}%) con escaso registro de hiperactividad motora ({fidgeting_score:.1f}/10). Patrón dentro de la media."
            elif atencion_pct < 65.0 and fidgeting_score >= 5.5:
                diag = f"Foco visual inestable con múltiples desviaciones de mirada ({atencion_pct:.1f}% de atención) y nivel de fidgeting elevado ({fidgeting_score:.1f}/10). Conducta compatible con déficit atencional e inquietud motora severa."
            else:
                diag = f"Desempeño general moderado. Foco atencional fluctuante ({atencion_pct:.1f}%) con presencia de movimientos corporales compensatorios y fidgeting leve ({fidgeting_score:.1f}/10)."
            
            fecha_str = r["fecha_hora"].strftime("%Y-%m-%d %H:%M") if r["fecha_hora"] else datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            
            timeline = generar_timeline_sintetico(duracion, atencion_pct, fidgeting_score)
            
            return {
                "id": r["id"],
                "id_paciente": r["id_paciente"],
                "fecha": fecha_str,
                "duracion_total_seg": duracion,
                "atencion_porcentaje": atencion_pct,
                "fidgeting_score": fidgeting_score,
                "distraccion": distraccion_ratio,
                "eventos_distraccion": eventos_dist,
                "tiempo_distraccion_seg": tiempo_dist,
                "diagnostico_auto": diag,
                "video_origen": f"sesion_video_{r['id']}.mp4",
                "timeline": timeline,
                "intervalos_distraccion": [],
                "notas": r["notas"]
            }
        return None
    except Error as e:
        print(f"Error al obtener sesión por ID: {e}")
        return None
    finally:
        cursor.close()
        conexion.close()

def add_paciente(nombre, fecha_nacimiento, historial_clinico, id_evaluador, tutor, numero_de_tutor, foto_perfil=None, genero='No especificado'):
    """Inserta un nuevo paciente en la base de datos."""
    conexion = conectar_db()
    if not conexion: return False
    cursor = conexion.cursor()
    
    # Obtener el siguiente ID disponible
    try:
        cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM pacientes")
        nuevo_id = cursor.fetchone()[0]
    except Error as e:
        print(f"Error al calcular el nuevo ID de paciente: {e}")
        cursor.close()
        conexion.close()
        return False
    
    # Sanitizar número de tutor
    try:
        num_tutor = int(numero_de_tutor)
    except (ValueError, TypeError):
        num_tutor = 0
    
    query = """
        INSERT INTO pacientes (id, nombre, fecha_nacimiento, genero, id_evaluador, tutor, numero_de_tutor, historial_clinico, foto_perfil)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(query, (nuevo_id, nombre, fecha_nacimiento, genero, id_evaluador, tutor, num_tutor, historial_clinico, foto_perfil))
        conexion.commit()
        return True
    except Error as e:
        print(f"Error al añadir paciente: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

def update_paciente(paciente_id, nombre, fecha_nacimiento, historial_clinico, tutor, numero_de_tutor, foto_perfil=None, genero='No especificado'):
    """Actualiza los datos de un paciente."""
    conexion = conectar_db()
    if not conexion: return False
    cursor = conexion.cursor()
    
    # Sanitizar número de tutor
    try:
        num_tutor = int(numero_de_tutor)
    except (ValueError, TypeError):
        num_tutor = 0
    
    query = """
        UPDATE pacientes 
        SET nombre = %s, fecha_nacimiento = %s, historial_clinico = %s, tutor = %s, numero_de_tutor = %s, foto_perfil = %s, genero = %s
        WHERE id = %s
    """
    try:
        cursor.execute(query, (nombre, fecha_nacimiento, historial_clinico, tutor, num_tutor, foto_perfil, genero, paciente_id))
        conexion.commit()
        return True
    except Error as e:
        print(f"Error al actualizar paciente: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

def delete_paciente(paciente_id):
    """Elimina un paciente y por ON DELETE CASCADE sus sesiones asociadas."""
    conexion = conectar_db()
    if not conexion: return False
    cursor = conexion.cursor()
    
    query = "DELETE FROM pacientes WHERE id = %s"
    try:
        cursor.execute(query, (paciente_id,))
        conexion.commit()
        return True
    except Error as e:
        print(f"Error al eliminar paciente: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()

def update_session_notas(session_id, notas):
    """Actualiza las notas de una sesión de evaluación."""
    conexion = conectar_db()
    if not conexion: return False
    cursor = conexion.cursor()
    query = "UPDATE sesiones SET notas = %s WHERE id = %s"
    try:
        cursor.execute(query, (notas, session_id))
        conexion.commit()
        return True
    except Error as e:
        print(f"Error al actualizar notas de sesión: {e}")
        return False
    finally:
        cursor.close()
        conexion.close()