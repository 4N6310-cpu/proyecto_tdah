import cv2
import numpy as np

# Intentar importar mediapipe de forma segura para permitir fallback simulado si no está instalado
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

class VideoDetector:
    def __init__(self, use_face_mesh=True, use_pose=True):
        self.use_face_mesh = use_face_mesh
        self.use_pose = use_pose
        
        if MEDIAPIPE_AVAILABLE:
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
            
            if self.use_face_mesh:
                self.mp_face_mesh = mp.solutions.face_mesh
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            else:
                self.face_mesh = None
                
            if self.use_pose:
                self.mp_pose = mp.solutions.pose
                self.pose = self.mp_pose.Pose(
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
            else:
                self.pose = None
        else:
            self.face_mesh = None
            self.pose = None
            print("[ADVERTENCIA] MediaPipe no está instalado en este sistema. El detector operará en modo Simulado.")

    def procesar_frame(self, frame):
        """
        Procesa un frame de OpenCV y extrae los landmarks faciales y corporales.
        Retorna:
            - frame_anotado: El frame con las visualizaciones dibujadas.
            - landmarks_datos: Un diccionario con los puntos clave normalizados.
        """
        h, w, c = frame.shape
        landmarks_datos = {
            "face_landmarks": None,
            "pose_landmarks": None,
            "dimensiones": (w, h)
        }
        
        if not MEDIAPIPE_AVAILABLE:
            # Simulación: Retornar el frame original y datos vacíos
            # (El behavioral_engine manejará la simulación de métricas si esto está vacío)
            return frame, landmarks_datos

        # Convertir BGR a RGB para MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 1. Procesar Face Mesh
        if self.face_mesh:
            resultados_cara = self.face_mesh.process(frame_rgb)
            if resultados_cara.multi_face_landmarks:
                # Tomamos la primera cara detectada
                cara_landmarks = resultados_cara.multi_face_landmarks[0]
                landmarks_datos["face_landmarks"] = []
                for lm in cara_landmarks.landmark:
                    landmarks_datos["face_landmarks"].append((lm.x, lm.y, lm.z))
                
                # Dibujar malla facial básica
                self.mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=cara_landmarks,
                    connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
                )
                
        # 2. Procesar Pose
        if self.pose:
            resultados_pose = self.pose.process(frame_rgb)
            if resultados_pose.pose_landmarks:
                pose_landmarks = resultados_pose.pose_landmarks
                landmarks_datos["pose_landmarks"] = []
                for lm in pose_landmarks.landmark:
                    landmarks_datos["pose_landmarks"].append((lm.x, lm.y, lm.z, lm.visibility))
                
                # Dibujar esqueleto de pose básico
                self.mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=pose_landmarks,
                    connections=self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                )
                
        return frame, landmarks_datos

    def liberar(self):
        """Libera los recursos de MediaPipe."""
        if self.face_mesh:
            self.face_mesh.close()
        if self.pose:
            self.pose.close()
