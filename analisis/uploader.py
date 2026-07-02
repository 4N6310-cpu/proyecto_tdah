import cv2
import os
import tempfile
from analisis.detector import VideoDetector
from analisis.behavioral_engine import BehavioralEngine
from core.database import add_analisis_to_paciente
import datetime

# Variables globales para auditoría y persistencia de estado de la última sesión procesada
promedio_atencional = 0.0
contador_frames = 0
fidgeting_acumulado = 0.0

def limpiar_sesion_ia():
    """
    Establece en 0 o None todas las variables globales de cálculo de métricas de la sesión.
    """
    global promedio_atencional, contador_frames, fidgeting_acumulado
    promedio_atencional = 0.0
    contador_frames = 0
    fidgeting_acumulado = 0.0
    print('DEBUG: Variables IA reseteadas a cero')

class VideoAnalysisUploader:
    @staticmethod
    def procesar_archivo_video(path_video, paciente_id, callback_progreso=None):
        """
        Abre un archivo de video, lo procesa cuadro a cuadro a través del VideoDetector,
        analiza su comportamiento con el BehavioralEngine y guarda el resultado en la BD.
        
        - callback_progreso: función que acepta un float (0.0 a 1.0) para actualizar la barra de progreso en el Frontend.
        """
        # Reseteo obligatorio de métricas globales al iniciar el análisis de video
        limpiar_sesion_ia()

        cap = None
        detector = None
        try:
            cap = cv2.VideoCapture(path_video)
            if not cap.isOpened():
                raise ValueError(f"No se pudo abrir el archivo de video: {path_video}")
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30.0 # Valor por defecto
                
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Inicializar detector y motor de comportamiento
            detector = VideoDetector(use_face_mesh=True, use_pose=True)
            engine = BehavioralEngine(fps=fps)
            
            frame_actual = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Procesar landmarks con MediaPipe
                frame_anotado, landmarks_datos = detector.procesar_frame(frame)
                
                # Evaluar comportamiento
                engine.procesar_frame_analisis(landmarks_datos)
                
                frame_actual += 1
                if callback_progreso and total_frames > 0:
                    progreso = min(1.0, frame_actual / total_frames)
                    callback_progreso(progreso)
                    
        finally:
            if cap is not None:
                cap.release()
            if detector is not None:
                detector.liberar()
            
        # Obtener resultados finales
        resultados = engine.obtener_resultados_sesion()
        
        # Guardar en base de datos
        identificador = f"A-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
        res_db = {
            "id": identificador,
            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "video_origen": os.path.basename(path_video),
            "atencion_porcentaje": resultados["atencion_porcentaje"],
            "eventos_distraccion": resultados["eventos_distraccion"],
            "tiempo_distraccion_seg": resultados["tiempo_distraccion_seg"],
            "fidgeting_score": resultados["fidgeting_score"],
            "duracion_total_seg": resultados["duracion_total_seg"],
            "diagnostico_auto": resultados["diagnostico_auto"],
            "estado_pdf": "pendiente",
            # Guardamos la timeline y los intervalos en la estructura de base de datos
            "timeline": resultados["timeline"],
            "intervalos_distraccion": resultados["intervalos_distraccion"]
        }
        
        add_analisis_to_paciente(paciente_id, res_db)
        
        # Actualización de variables globales al terminar
        global promedio_atencional, contador_frames, fidgeting_acumulado
        contador_frames = frame_actual
        promedio_atencional = resultados["atencion_porcentaje"]
        fidgeting_acumulado = resultados["fidgeting_score"]
        print("[DEBUG BACKEND] [UPDATE] Variables globales de métricas actualizadas con nuevos datos:")
        print(f"  - promedio_atencional: {promedio_atencional}%")
        print(f"  - contador_frames: {contador_frames}")
        print(f"  - fidgeting_acumulado: {fidgeting_acumulado}")
        
        return res_db