import sys
import cv2
import numpy as np

# 1. Inicialización segura inyectando atributos dinámicos para evitar bugs de Windows/Python 3.12
MEDIAPIPE_AVAILABLE = False

try:
    import mediapipe as mp
    
    # Si la instalación oculta .solutions, creamos el puente de forma segura
    if not hasattr(mp, 'solutions'):
        sys.modules['mediapipe.solutions'] = mp
            
    # Extracción segura con getattr para que no arroje AttributeError con NumPy 2
    mp_face_mesh = getattr(mp, 'solutions', mp).face_mesh if hasattr(getattr(mp, 'solutions', mp), 'face_mesh') else None
    mp_pose = getattr(mp, 'solutions', mp).pose if hasattr(getattr(mp, 'solutions', mp), 'pose') else None
    mp_drawing = getattr(mp, 'solutions', mp).drawing_utils if hasattr(getattr(mp, 'solutions', mp), 'drawing_utils') else None
    mp_drawing_styles = getattr(mp, 'solutions', mp).drawing_styles if hasattr(getattr(mp, 'solutions', mp), 'drawing_styles') else None
    
    if mp_face_mesh and mp_pose:
        MEDIAPIPE_AVAILABLE = True
        
except Exception:
    mp_face_mesh = None
    mp_pose = None
    mp_drawing = None
    mp_drawing_styles = None
    MEDIAPIPE_AVAILABLE = False


# 2. La Clase Solicitada por el Sistema (VideoDetector)
class VideoDetector:
    def __init__(self, use_face_mesh=True, use_pose=True):
        self.use_face_mesh = use_face_mesh
        self.use_pose = use_pose
        
        # Guardamos referencias de utilidades si MediaPipe cargó
        self.mp_drawing = mp_drawing
        self.mp_drawing_styles = mp_drawing_styles
        
        if self.use_face_mesh and MEDIAPIPE_AVAILABLE:
            self.mp_face_mesh = mp_face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        else:
            self.face_mesh = None
            
        if self.use_pose and MEDIAPIPE_AVAILABLE:
            self.mp_pose = mp_pose
            self.pose = self.mp_pose.Pose(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        else:
            self.pose = None

    def procesar_frame(self, frame):
        """
        Procesa un frame de OpenCV y extrae los landmarks faciales y corporales.
        """
        h, w, c = frame.shape
        landmarks_datos = {
            "face_landmarks": None,
            "pose_landmarks": None,
            "dimensiones": (w, h)
        }
        
        if not MEDIAPIPE_AVAILABLE:
            # Tolerancia a fallos: Si MediaPipe no inició, retorna el frame limpio y el motor
            # cognitivo del backend simulará las métricas para que el sistema siga corriendo.
            return frame, landmarks_datos

        # Convertir BGR a RGB para MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Procesar Face Mesh
        if self.face_mesh:
            resultados_cara = self.face_mesh.process(frame_rgb)
            if resultados_cara.multi_face_landmarks:
                cara_landmarks = resultados_cara.multi_face_landmarks[0]
                landmarks_datos["face_landmarks"] = []
                for lm in cara_landmarks.landmark:
                    landmarks_datos["face_landmarks"].append((lm.x, lm.y, lm.z))
                
                if self.mp_drawing and self.mp_drawing_styles:
                    self.mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=cara_landmarks,
                        connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
                    )
                
        # Procesar Pose
        if self.pose:
            resultados_pose = self.pose.process(frame_rgb)
            if resultados_pose.pose_landmarks:
                pose_landmarks = resultados_pose.pose_landmarks
                landmarks_datos["pose_landmarks"] = []
                for lm in pose_landmarks.landmark:
                    landmarks_datos["pose_landmarks"].append((lm.x, lm.y, lm.z, lm.visibility))
                
                if self.mp_drawing and self.mp_drawing_styles:
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