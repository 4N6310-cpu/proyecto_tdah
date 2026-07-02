import cv2
import numpy as np
import math

class BehavioralEngine:
    def __init__(self, fps=30.0, umbral_yaw=18.0, umbral_pitch=15.0, umbral_fidgeting=0.03):
        self.fps = fps
        self.umbral_yaw = umbral_yaw
        self.umbral_pitch = umbral_pitch
        self.umbral_fidgeting = umbral_fidgeting  # Umbral de movimiento de landmarks por frame
        
        # Puntos 3D genéricos del modelo de cara para SolvePnP (alineando la dirección de los ejes con la imagen 2D)
        self.model_points = np.array([
            (0.0, 0.0, 0.0),             # Punta de la nariz (Landmark 1)
            (0.0, 330.0, -65.0),         # Mentón (Landmark 152) (hacia abajo, positivo)
            (-225.0, -170.0, -135.0),    # Esquina externa ojo izquierdo (Landmark 33) (hacia arriba, negativo)
            (225.0, -170.0, -135.0),     # Esquina externa ojo derecho (Landmark 263) (hacia arriba, negativo)
            (-150.0, 150.0, -125.0),     # Esquina externa boca izquierda (Landmark 61) (hacia abajo, positivo)
            (150.0, 150.0, -125.0)       # Esquina externa boca derecha (Landmark 291) (hacia abajo, positivo)
        ], dtype=np.float64)

        # Estado del análisis de la sesión
        self.reset_session()

    def reset_session(self):
        """Reinicia todos los contadores de la sesión actual."""
        self.frames_totales = 0
        self.frames_atencion = 0
        self.frames_distraccion = 0
        
        # Tracking de eventos de distracción
        self.eventos_distraccion = 0
        self.frames_distraccion_consecutivos = 0
        self.segundos_para_evento_distraccion = 1.5  # X segundos para registrar evento
        self.frames_para_evento = int(self.segundos_para_evento_distraccion * self.fps)
        
        # Historial para la línea de tiempo (segundo a segundo)
        self.timeline_data = [] # Lista de dicts con: segundo, atencion (0 o 1), fidgeting_score (0-10)
        
        # Historial de landmarks anteriores para calcular fidgeting (movimiento)
        self.prev_pose_landmarks = None
        self.fidgeting_acumulado = 0.0
        self.valores_fidgeting_frame = []
        
        # Registro de intervalos de distracción
        self.intervalos_distraccion = []
        self.distraccion_inicio_seg = None

    def estimar_pose_cabeza(self, landmarks_cara, w, h):
        """
        Calcula los ángulos de rotación de la cabeza (Yaw, Pitch, Roll) usando SolvePnP.
        """
        # Índices de landmarks de MediaPipe Face Mesh correspondientes al modelo 3D genérico
        indices_cara = [1, 152, 33, 263, 61, 291]
        
        image_points = []
        for idx in indices_cara:
            lm = landmarks_cara[idx]
            image_points.append([lm[0] * w, lm[1] * h])
            
        image_points = np.array(image_points, dtype=np.float64)
        
        # Matriz de la cámara (aproximada basada en el tamaño del frame)
        focal_length = w
        center = (w / 2, h / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float64)
        
        dist_coeffs = np.zeros((4, 1)) # Asumimos sin distorsión de lente
        
        success, rotation_vector, translation_vector = cv2.solvePnP(
            self.model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        if not success:
            return 0.0, 0.0, 0.0
            
        # Obtener matriz de rotación
        rmat, _ = cv2.Rodrigues(rotation_vector)
        
        # Extraer ángulos de Euler (Yaw, Pitch, Roll) en grados
        # rmat[2, 0] = -sin(pitch)
        # rmat[2, 1] = cos(pitch)*sin(roll)
        # rmat[2, 2] = cos(pitch)*cos(roll)
        # rmat[1, 0] = sin(yaw)*cos(pitch) ... aproximado
        
        # Proyección estándar
        sy = math.sqrt(rmat[0,0] * rmat[0,0] +  rmat[1,0] * rmat[1,0])
        singular = sy < 1e-6

        if not singular:
            x = math.atan2(rmat[2,1] , rmat[2,2])
            y = math.atan2(-rmat[2,0], sy)
            z = math.atan2(rmat[1,0], rmat[0,0])
        else:
            x = math.atan2(-rmat[1,2], rmat[1,1])
            y = math.atan2(-rmat[2,0], sy)
            z = 0

        # Convertir a grados
        pitch = x * (180.0 / math.pi)
        yaw = y * (180.0 / math.pi)
        roll = z * (180.0 / math.pi)
        
        return yaw, pitch, roll

    def calcular_desvio_mirada(self, landmarks_cara, w, h):
        """
        Calcula si el paciente está desviando la mirada (gaze deviation) comparando la posición
        de la pupila (iris) con los extremos de cada ojo en coordenadas reales.
        """
        # Verificar que el face mesh de MediaPipe cuente con los puntos del iris (mínimo 478 landmarks)
        if len(landmarks_cara) < 478:
            return False
            
        try:
            # Ojo izquierdo: extremo externo=33, extremo interno=133, centro del iris=468
            izq_ext = np.array([landmarks_cara[33][0] * w, landmarks_cara[33][1] * h])
            izq_int = np.array([landmarks_cara[133][0] * w, landmarks_cara[133][1] * h])
            izq_iris = np.array([landmarks_cara[468][0] * w, landmarks_cara[468][1] * h])
            
            # Ojo derecho: extremo externo=362, extremo interno=263, centro del iris=473
            der_ext = np.array([landmarks_cara[362][0] * w, landmarks_cara[362][1] * h])
            der_int = np.array([landmarks_cara[263][0] * w, landmarks_cara[263][1] * h])
            der_iris = np.array([landmarks_cara[473][0] * w, landmarks_cara[473][1] * h])
            
            # Medir anchos de los ojos
            ancho_izq = np.linalg.norm(izq_ext - izq_int)
            ancho_der = np.linalg.norm(der_ext - der_int)
            
            if ancho_izq < 1.0 or ancho_der < 1.0:
                return False
                
            # Calcular la posición horizontal relativa del iris (0.0 = externo, 1.0 = interno)
            dist_ext_izq = np.linalg.norm(izq_ext - izq_iris)
            ratio_izq = dist_ext_izq / ancho_izq
            
            dist_ext_der = np.linalg.norm(der_ext - der_iris)
            ratio_der = dist_ext_der / ancho_der
            
            # Si el iris se desplaza lateralmente (fuera de la franja central 0.34 a 0.66)
            desvio_izq = abs(ratio_izq - 0.5) > 0.16
            desvio_der = abs(ratio_der - 0.5) > 0.16
            
            # Considerar desvío si al menos un ojo desvía la mirada de forma evidente
            return desvio_izq or desvio_der
            
        except Exception:
            return False

    def calcular_fidgeting_frame(self, pose_landmarks):
        """
        Calcula la cantidad de movimiento (fidgeting) entre el frame actual y el anterior.
        Utiliza las muñecas (15, 16) y hombros (11, 12).
        """
        if self.prev_pose_landmarks is None or pose_landmarks is None:
            self.prev_pose_landmarks = pose_landmarks
            return 0.0
            
        # Landmarks a seguir: hombros y muñecas
        indices_fidgeting = [11, 12, 15, 16]
        movimientos = []
        
        for idx in indices_fidgeting:
            if idx < len(pose_landmarks) and idx < len(self.prev_pose_landmarks):
                curr_lm = pose_landmarks[idx]
                prev_lm = self.prev_pose_landmarks[idx]
                
                # Distancia euclidiana en coordenadas 2D (x, y)
                dist = math.sqrt((curr_lm[0] - prev_lm[0])**2 + (curr_lm[1] - prev_lm[1])**2)
                movimientos.append(dist)
                
        self.prev_pose_landmarks = pose_landmarks
        
        if not movimientos:
            return 0.0
            
        # Retorna el promedio de desplazamiento de los puntos clave analizados
        return float(np.mean(movimientos))

    def procesar_frame_analisis(self, landmarks_datos):
        """
        Procesa los landmarks extraídos en el frame actual y actualiza las métricas.
        """
        self.frames_totales += 1
        w, h = landmarks_datos["dimensiones"]
        
        yaw, pitch, roll = 0.0, 0.0, 0.0
        cara_detectada = landmarks_datos["face_landmarks"] is not None
        pose_detectada = landmarks_datos["pose_landmarks"] is not None
        
        # 1. Analizar Atención por Rotación Cefálica y Desvío de Ojos (Gaze Tracking)
        esta_distraido = False
        if cara_detectada:
            yaw, pitch, roll = self.estimar_pose_cabeza(landmarks_datos["face_landmarks"], w, h)
            # Si supera los umbrales de rotación cefálica, se considera distraído
            if abs(yaw) > self.umbral_yaw or abs(pitch) > self.umbral_pitch:
                esta_distraido = True
            # Si la cabeza está de frente, evaluar el desvío ocular lateral (Iris tracking)
            elif self.calcular_desvio_mirada(landmarks_datos["face_landmarks"], w, h):
                esta_distraido = True
        else:
            # Si no se detecta el rostro del niño, se asume que está fuera de encuadre (distracción)
            esta_distraido = True

        # Control del estado de atención
        if esta_distraido:
            self.frames_distraccion += 1
            self.frames_distraccion_consecutivos += 1
            
            # Si cruza el umbral de segundos consecutivos, se registra el evento
            if self.frames_distraccion_consecutivos == self.frames_para_evento:
                self.eventos_distraccion += 1
                
            # Guardar inicio del intervalo de distracción
            segundo_actual = self.frames_totales / self.fps
            if self.distraccion_inicio_seg is None:
                self.distraccion_inicio_seg = segundo_actual
        else:
            self.frames_atencion += 1
            # Si veníamos de una distracción prolongada, cerrar el intervalo
            if self.distraccion_inicio_seg is not None:
                segundo_actual = self.frames_totales / self.fps
                duracion = segundo_actual - self.distraccion_inicio_seg
                if duracion >= self.segundos_para_evento_distraccion:
                    self.intervalos_distraccion.append({
                        "inicio": round(self.distraccion_inicio_seg, 1),
                        "fin": round(segundo_actual, 1),
                        "duracion": round(duracion, 1)
                    })
                self.distraccion_inicio_seg = None
            
            self.frames_distraccion_consecutivos = 0

        # 2. Analizar Fidgeting/Hiperactividad
        fidgeting_val = 0.0
        if pose_detectada:
            fidgeting_val = self.calcular_fidgeting_frame(landmarks_datos["pose_landmarks"])
            self.valores_fidgeting_frame.append(fidgeting_val)
        else:
            self.valores_fidgeting_frame.append(0.0)

        # 3. Guardar datos en la línea de tiempo cada 1 segundo
        if self.frames_totales % int(self.fps) == 0:
            segundo = int(self.frames_totales / self.fps)
            
            # Calcular fidgeting score promedio en el último segundo (escala de 0 a 10)
            ultimos_fidgeting = self.valores_fidgeting_frame[-int(self.fps):]
            fidgeting_promedio = float(np.mean(ultimos_fidgeting)) if ultimos_fidgeting else 0.0
            
            # Normalizar fidgeting en escala 0 a 10 (con clipping)
            # Asumimos que un valor promedio de 0.05 de movimiento en normalizado de landmarks representa hiperactividad alta (10)
            fidgeting_score = min(10.0, (fidgeting_promedio / self.umbral_fidgeting) * 5.0)
            fidgeting_score = round(fidgeting_score, 1)
            
            # Atención en el último segundo (1 si estuvo más atento que distraído, 0 si no)
            estado_atencion = 0 if esta_distraido else 1
            
            self.timeline_data.append({
                "segundo": segundo,
                "atencion": estado_atencion,
                "fidgeting_score": fidgeting_score,
                "yaw": round(yaw, 1),
                "pitch": round(pitch, 1)
            })



    def obtener_resultados_sesion(self):
        """
        Retorna las estadísticas consolidadas del análisis de comportamiento en la sesión.
        """
        if self.frames_totales == 0:
            return {
                "atencion_porcentaje": 0.0,
                "eventos_distraccion": 0,
                "tiempo_distraccion_seg": 0,
                "fidgeting_score": 0.0,
                "duracion_total_seg": 0,
                "timeline": [],
                "intervalos_distraccion": []
            }
            
        duracion_total = self.frames_totales / self.fps
        atencion_porcentaje = (self.frames_atencion / self.frames_totales) * 100.0
        tiempo_distraccion = self.frames_distraccion / self.fps
        
        # Calcular Fidgeting general de la sesión (promedio de los scores por segundo)
        fidgeting_scores = [d["fidgeting_score"] for d in self.timeline_data]
        fidgeting_general = float(np.mean(fidgeting_scores)) if fidgeting_scores else 0.0
        
        # Conclusiones automatizadas diagnósticas predefinidas
        conclusiones = ""
        if atencion_porcentaje >= 75:
            conclusiones += "Nivel de atención óptimo para el rango etario. "
        elif atencion_porcentaje >= 55:
            conclusiones += "Atención fluctuante moderada. Muestra fatiga atencional típica. "
        else:
            conclusiones += "Déficit atencional severo detectado. Frecuente desconexión visual y desvío del eje corporal de la tarea. "
            
        if fidgeting_general >= 6.5:
            conclusiones += "Indicadores de alta actividad motora periférica (fidgeting excesivo en extremidades). Consistente con hiperactividad física."
        elif fidgeting_general >= 4.0:
            conclusiones += "Actividad motora levemente aumentada. Cambios posturales recurrentes."
        else:
            conclusiones += "Estabilidad motora conservada. Mantiene la postura durante el foco de concentración."

        return {
            "atencion_porcentaje": round(atencion_porcentaje, 1),
            "eventos_distraccion": self.eventos_distraccion,
            "tiempo_distraccion_seg": round(tiempo_distraccion, 1),
            "fidgeting_score": round(fidgeting_general, 1),
            "duracion_total_seg": round(duracion_total, 1),
            "diagnostico_auto": conclusiones,
            "timeline": self.timeline_data,
            "intervalos_distraccion": self.intervalos_distraccion
        }