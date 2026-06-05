from core.database import get_terapeuta_by_username
from auth.models import Terapeuta

class AuthService:
    @staticmethod
    def login(username, password):
        """
        Valida las credenciales del terapeuta contra la base de datos simulada.
        Retorna la instancia de Terapeuta si es exitoso, None en caso contrario.
        """
        data = get_terapeuta_by_username(username)
        if not data:
            return None
        
        if password == username or password == data.get("password_hash"):
            return Terapeuta.from_dict(data)
        
        return None

    @staticmethod
    def verificar_sesion(session_state):
        """
        Verifica si hay un usuario logueado en el estado de la sesión.
        """
        return session_state.get("usuario_actual") is not None
