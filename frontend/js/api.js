/* =====================================================================
   ADHD-VISION API WRAPPER (Fetch API Client)
   ===================================================================== */

const API_BASE = ''; // Same origin serving

const API = {
  /**
   * Evaluator Login Authentication
   */
  async login(username, password) {
    const response = await fetch(`${API_BASE}/api/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Error de autenticación');
    }
    return data; // Expected { status, user: { id, nombre, usuario, rol } }
  },

  /**
   * Get Patients for Evaluator
   */
  async getPacientes(idEvaluador) {
    const response = await fetch(`${API_BASE}/api/pacientes?id_evaluador=${idEvaluador}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Error al obtener pacientes');
    }
    return data; // Array of patients
  },

  /**
   * Get sessions list and full details for a patient
   */
  async getSesiones(idPaciente) {
    const response = await fetch(`${API_BASE}/api/sesiones?id_paciente=${idPaciente}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Error al obtener expediente');
    }
    return data; // Expected { paciente, sesiones }
  },

  /**
   * Trigger stochastic AI simulation for clinical demo
   */
  async simularAnalisis(params) {
    const response = await fetch(`${API_BASE}/api/analisis/simular`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(params)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Error en la simulación');
    }
    return data;
  },

  /**
   * Upload video file and run actual OpenCV + MediaPipe analysis
   */
  async subirVideo(pacienteId, file) {
    const formData = new FormData();
    formData.append('paciente_id', pacienteId);
    formData.append('video', file);

    const response = await fetch(`${API_BASE}/api/analisis/video`, {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Error al procesar el video');
    }
    return data;
  }
};
