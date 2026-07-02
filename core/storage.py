import os
import traceback
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class StorageStrategy(ABC):
    @abstractmethod
    def upload_file(self, file, default_filename=None) -> str:
        """
        Sube o guarda el archivo y retorna la URL pública o la ruta relativa.
        """
        pass

class CloudinaryStorageStrategy(StorageStrategy):
    def upload_file(self, file, default_filename=None) -> str:
        import cloudinary.uploader
        print("[STORAGE DEBUG] Subiendo a Cloudinary...")
        try:
            upload_result = cloudinary.uploader.upload(
                file,
                folder="proyecto_tdah/pacientes"
            )
            secure_url = upload_result.get("secure_url")
            print(f"[STORAGE DEBUG] Subida exitosa a Cloudinary. URL: '{secure_url}'")
            return secure_url
        except Exception as e:
            print(f"[STORAGE DEBUG] Error al guardar en Cloudinary: {str(e)}")
            traceback.print_exc()
            raise e

class LocalStorageStrategy(StorageStrategy):
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        os.makedirs(self.upload_folder, exist_ok=True)

    def upload_file(self, file, default_filename=None) -> str:
        from werkzeug.utils import secure_filename
        import time
        print("[STORAGE DEBUG] Guardando en local...")
        try:
            filename = getattr(file, 'filename', '')
            if not filename or filename == '':
                filename = default_filename if default_filename else f"archivo_{int(time.time())}"
            
            safe_filename = secure_filename(f"{int(time.time())}_{filename}")
            filepath = os.path.join(self.upload_folder, safe_filename)
            file.save(filepath)
            
            # Devolvemos la ruta que interpretará el frontend mediante el servidor estático
            rel_path = f"/static/uploads/{safe_filename}"
            print(f"[STORAGE DEBUG] Guardado local exitoso en: '{rel_path}'")
            return rel_path
        except Exception as e:
            print(f"[STORAGE DEBUG] Error al guardar en local: {str(e)}")
            raise e

class StorageContext:
    def __init__(self):
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        api_key = os.getenv("CLOUDINARY_API_KEY")
        api_secret = os.getenv("CLOUDINARY_API_SECRET")
        
        # Validar si las credenciales de la nube están presentes
        if cloud_name and api_key and api_secret:
            print("[STORAGE DEBUG] Arquitectura Híbrida: Credenciales en la nube detectadas. Usando Cloudinary.")
            self._strategy = CloudinaryStorageStrategy()
        else:
            print("[STORAGE DEBUG] Arquitectura Híbrida: Credenciales no detectadas. Usando almacenamiento Local.")
            # Definir carpeta local frontend/static/uploads
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            upload_path = os.path.join(base_dir, 'frontend', 'static', 'uploads')
            self._strategy = LocalStorageStrategy(upload_path)

    def set_strategy(self, strategy: StorageStrategy):
        self._strategy = strategy

    def save(self, file, default_filename=None) -> str:
        print("[STORAGE DEBUG] Recibiendo archivo...")
        if not file:
            print("[STORAGE DEBUG] Error al guardar: El archivo recibido es nulo.")
            return None
        return self._strategy.upload_file(file, default_filename)
