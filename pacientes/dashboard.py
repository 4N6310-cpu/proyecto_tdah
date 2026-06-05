from core.database import get_paciente_by_id

class PacienteDashboardController:
    @staticmethod
    def obtener_detalle_paciente(paciente_id):
        """
        Retorna la información completa de un paciente por su ID.
        """
        return get_paciente_by_id(paciente_id)
    
    @staticmethod
    def calcular_tendencia_atencion(paciente):
        """
        Calcula la evolución de la atención del paciente a lo largo de las sesiones.
        Retorna una lista de tuplas (fecha, porcentaje).
        """
        historial = paciente.get("historial_analisis", [])
        if not historial:
            return []
        
        # El historial se almacena del más nuevo al más viejo, lo invertimos para graficar cronológicamente
        tendencia = []
        for sesion in reversed(historial):
            tendencia.append({
                "fecha": sesion["fecha"].split(" ")[0],
                "atencion": sesion["atencion_porcentaje"],
                "fidgeting": sesion["fidgeting_score"]
            })
        return tendencia
