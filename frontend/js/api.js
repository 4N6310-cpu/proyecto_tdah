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
  },

  /**
   * Add a new patient
   */
  async addPaciente(nombre, fechaNacimiento, historialClinico, idEvaluador, tutor, numeroDeTutor) {
    const response = await fetch(`${API_BASE}/api/pacientes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        nombre, 
        fecha_nacimiento: fechaNacimiento, 
        historial_clinico: historialClinico, 
        id_evaluador: idEvaluador,
        tutor: tutor,
        numero_de_tutor: numeroDeTutor
      })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Error al registrar paciente');
    }
    return data;
  },

  /**
   * Update an existing patient
   */
  async updatePaciente(id, nombre, fechaNacimiento, historialClinico, tutor, numeroDeTutor) {
    const response = await fetch(`${API_BASE}/api/pacientes/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        nombre, 
        fecha_nacimiento: fechaNacimiento, 
        historial_clinico: historialClinico,
        tutor: tutor,
        numero_de_tutor: numeroDeTutor
      })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Error al actualizar paciente');
    }
    return data;
  },

  /**
   * Delete a patient
   */
  async deletePaciente(id) {
    const response = await fetch(`${API_BASE}/api/pacientes/${id}`, {
      method: 'DELETE'
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'Error al eliminar paciente');
    }
    return data;
  }
};
