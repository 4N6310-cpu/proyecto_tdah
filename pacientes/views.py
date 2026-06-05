from core.database import get_pacientes_by_terapeuta

class PacientesController:
    @staticmethod
    def obtener_pacientes_terapeuta(terapeuta_id):
        """
        Retorna la lista de pacientes asignados al terapeuta.
        """
        return get_pacientes_by_terapeuta(terapeuta_id)
