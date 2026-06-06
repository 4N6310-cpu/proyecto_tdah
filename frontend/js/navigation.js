/* =====================================================================
   ADHD-VISION SINGLE PAGE APPLICATION (SPA) ROUTER & DOM CONTROLLER
   ===================================================================== */

// Global navigation state
let currentView = null;
let currentPatient = null;
let patientsData = [];

// Initialize SPA on load
document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

function initApp() {
  if (Auth.isLoggedIn()) {
    navigateTo('dashboard');
  } else {
    navigateTo('login');
  }
}

/**
 * Main View Router
 */
async function navigateTo(viewName) {
  const container = document.getElementById('app-container');
  currentView = viewName;

  // Show base loader
  container.innerHTML = `
    <div class="loader-container">
      <div class="spinner"></div>
      <p>Cargando interfaz...</p>
    </div>
  `;

  try {
    if (viewName === 'login') {
      const response = await fetch('login.html');
      const html = await response.text();
      container.innerHTML = html;
      bindLoginEvents();
    } else if (viewName === 'dashboard') {
      const response = await fetch('dashboard.html');
      const html = await response.text();
      container.innerHTML = html;

      const evalData = Auth.getEvaluador();
      document.getElementById('user-display').innerText = `${evalData.nombre} (${evalData.especialidad})`;

      bindDashboardEvents();
      loadPatients();
    }
  } catch (error) {
    console.error('Error loading view:', error);
    container.innerHTML = `
      <div style="padding: 40px; text-align: center; color: var(--danger);">
        <h3>Error al cargar el portal</h3>
        <p>${error.message}</p>
        <button onclick="initApp()" class="btn" style="width: auto; margin-top: 15px;">Reintentar</button>
      </div>
    `;
  }
}

/* =====================================================================
   LOGIN LOGIC
   ===================================================================== */
function bindLoginEvents() {
  const form = document.getElementById('login-form');
  const alertEl = document.getElementById('login-alert');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    alertEl.classList.add('hidden');

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    // UI feedback
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerText;
    submitBtn.disabled = true;
    submitBtn.innerText = 'Autenticando...';

    try {
      // Direct demo logins for fast demonstration without DB if preferred:
      let sessionUser;
      if (username === 'doctor_perez' && password === 'doctor_perez') {
        // Mock fallback doctor
        sessionUser = { id: 1, nombre: 'Dr. Alejandro Pérez', usuario: 'doctor_perez', rol: 'Administrador' };
      } else {
        const res = await API.login(username, password);
        sessionUser = res.user;
      }

      Auth.login(sessionUser);
      navigateTo('dashboard');
    } catch (err) {
      alertEl.innerText = err.message || 'Error de conexión';
      alertEl.classList.remove('hidden');
      submitBtn.disabled = false;
      submitBtn.innerText = originalText;
    }
  });
}

/* =====================================================================
   DASHBOARD / PATIENTS LIST LOGIC
   ===================================================================== */
function bindDashboardEvents() {
  // Logout
  document.getElementById('logout-btn').addEventListener('click', () => {
    Auth.logout();
  });

  // Search filter
  const searchInput = document.getElementById('patient-search');
  searchInput.addEventListener('input', (e) => {
    filterPatients(e.target.value);
  });

  // Back button in Dossier
  document.getElementById('back-to-patients-btn').addEventListener('click', () => {
    document.getElementById('patient-detail-view').classList.add('hidden');
    document.getElementById('patients-list-view').classList.remove('hidden');
    currentPatient = null;
    loadPatients(); // Refresh patient listing metrics
  });

  // Video input change feedback
  const videoInput = document.getElementById('video-input');
  videoInput.addEventListener('change', (e) => {
    const runBtn = document.getElementById('run-analysis-btn');
    const filenameEl = document.getElementById('video-filename');
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      filenameEl.innerText = `Archivo seleccionado: ${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`;
      runBtn.disabled = false;
    } else {
      filenameEl.innerText = '';
      runBtn.disabled = true;
    }
  });

  // Video processing action
  document.getElementById('run-analysis-btn').addEventListener('click', executeVideoAnalysis);

  // Behavior simulation action
  document.getElementById('run-simulation-btn').addEventListener('click', executeSimulation);
}

/**
 * Fetch assigned patients and render cards
 */
async function loadPatients() {
  const grid = document.getElementById('patients-grid');
  const evalData = Auth.getEvaluador();

  try {
    const list = await API.getPacientes(evalData.id);
    patientsData = list;
    renderPatients(patientsData);
  } catch (err) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; padding: 20px; color: var(--danger); text-align: center;">
        <p>No se pudo conectar a la base de datos MySQL feria.</p>
        <p style="font-size: 13px; color: var(--text-muted); margin-top: 5px;">${err.message}</p>
        <p style="font-size: 12px; margin-top: 10px;">Comprueba que el servicio local MySQL esté activo en el puerto estándar.</p>
      </div>
    `;
  }
}

function renderPatients(list) {
  const grid = document.getElementById('patients-grid');
  if (list.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 40px 20px; background: rgba(255,255,255,0.6); border-radius: var(--radius-lg); border: 1px dashed var(--border-color); box-shadow: var(--shadow-sm);">
        <p style="color: var(--text-muted); margin-bottom: 20px; font-size: 15px;">No hay pacientes asignados que coincidan.</p>
        <button class="btn" style="width: auto; margin: 0 auto;" onclick="openAddPatientModal()">✨ Agregar Nuevo Paciente</button>
      </div>
    `;
    return;
  }

  grid.innerHTML = list.map(pac => `
    <div class="patient-card" onclick="openPatientDossier(${pac.id})">
      <div class="patient-avatar">👦</div>
      <div class="patient-info">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <h3 class="patient-name" style="margin: 0;">${escapeHTML(pac.nombre)}</h3>
          <div class="patient-card-actions" style="margin-top: 0;">
            <button class="btn-icon" title="Editar Paciente" onclick="openEditPatientModal(event, ${pac.id})">✏️</button>
            <button class="btn-icon btn-icon-danger" title="Eliminar Paciente" onclick="deletePatientAction(event, ${pac.id})">🗑️</button>
          </div>
        </div>
        <p class="patient-details" style="margin-top: 8px;">
          Edad: ${pac.edad} años | Género: ${escapeHTML(pac.genero)}<br>
          Nombre Tutor: ${escapeHTML(pac.nombre_tutor || 'No registrado')}<br>
          Contacto: ${escapeHTML(pac.contacto || 'No registrado')}
        </p>
        <span class="patient-stats">Ver expediente clínico ➡️</span>
      </div>
    </div>
  `).join('');
}

/* =====================================================================
   PATIENT CRUD MODAL ACTIONS
   ===================================================================== */
function openAddPatientModal() {
  document.getElementById('modal-title').innerText = 'Agregar Nuevo Paciente';
  document.getElementById('modal-patient-id').value = '';
  document.getElementById('modal-patient-name').value = '';
  document.getElementById('modal-patient-birthdate').value = '';
  document.getElementById('modal-patient-tutor').value = '';
  document.getElementById('modal-patient-tutor-phone').value = '';
  document.getElementById('modal-patient-history').value = '';
  document.getElementById('patient-modal').classList.remove('hidden');
}

function openEditPatientModal(event, patientId) {
  if (event) event.stopPropagation(); // Evitar abrir el expediente del paciente
  
  const patient = patientsData.find(p => p.id === patientId);
  if (!patient) return;
  
  document.getElementById('modal-title').innerText = 'Editar Datos del Paciente';
  document.getElementById('modal-patient-id').value = patient.id;
  document.getElementById('modal-patient-name').value = patient.nombre;
  document.getElementById('modal-patient-birthdate').value = patient.fecha_nacimiento || '';
  document.getElementById('modal-patient-tutor').value = patient.tutor_nombre || '';
  document.getElementById('modal-patient-tutor-phone').value = (patient.tutor_celular && patient.tutor_celular !== "No tiene") ? patient.tutor_celular : '';
  document.getElementById('modal-patient-history').value = patient.notas || '';
  
  document.getElementById('patient-modal').classList.remove('hidden');
}

function closePatientModal() {
  document.getElementById('patient-modal').classList.add('hidden');
}

async function savePatient(event) {
  event.preventDefault();
  
  const id = document.getElementById('modal-patient-id').value;
  const nombre = document.getElementById('modal-patient-name').value.trim();
  const fechaNacimiento = document.getElementById('modal-patient-birthdate').value;
  const tutor = document.getElementById('modal-patient-tutor').value.trim();
  const numeroDeTutor = document.getElementById('modal-patient-tutor-phone').value.trim();
  const historialClinico = document.getElementById('modal-patient-history').value.trim();
  const evalData = Auth.getEvaluador();
  
  const submitBtn = document.getElementById('modal-submit-btn');
  const originalText = submitBtn.innerText;
  submitBtn.disabled = true;
  submitBtn.innerText = 'Guardando...';
  
  try {
    if (id) {
      await API.updatePaciente(id, nombre, fechaNacimiento, historialClinico, tutor, numeroDeTutor);
    } else {
      await API.addPaciente(nombre, fechaNacimiento, historialClinico, evalData.id, tutor, numeroDeTutor);
    }
    
    closePatientModal();
    await loadPatients(); // Actualizar lista inmediatamente
  } catch (err) {
    alert('Error al guardar paciente: ' + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerText = originalText;
  }
}

async function deletePatientAction(event, patientId) {
  if (event) event.stopPropagation(); // Evitar abrir el expediente del paciente
  
  const patient = patientsData.find(p => p.id === patientId);
  const name = patient ? patient.nombre : 'este paciente';
  
  const confirmDelete = confirm(`¿Estás seguro de que deseas eliminar permanentemente a ${name}? Esta acción no se puede deshacer y borrará también todas sus sesiones asociadas.`);
  if (!confirmDelete) return;
  
  try {
    await API.deletePaciente(patientId);
    await loadPatients(); // Actualizar lista inmediatamente
  } catch (err) {
    alert('Error al eliminar paciente: ' + err.message);
  }
}

function filterPatients(query) {
  const filtered = patientsData.filter(pac =>
    pac.nombre.toLowerCase().includes(query.toLowerCase())
  );
  renderPatients(filtered);
}

/* =====================================================================
   CLINICAL EXPEDIENTE (DOSSIER) LOGIC
   ===================================================================== */
async function openPatientDossier(patientId) {
  // Show dossier view, hide patient list
  document.getElementById('patients-list-view').classList.add('hidden');
  const dossierView = document.getElementById('patient-detail-view');
  dossierView.classList.remove('hidden');

  // Load skeleton/loader inside card
  dossierView.querySelector('#patient-banner').innerHTML = `
    <h1 style="color: white; margin: 0;">Cargando expediente...</h1>
  `;

  try {
    const data = await API.getSesiones(patientId);
    currentPatient = data.paciente;
    currentPatient.historial_analisis = data.sesiones || [];

    renderDossier(currentPatient);
  } catch (err) {
    document.getElementById('patient-banner').innerHTML = `
      <h1 style="color: white; margin: 0;">Error al cargar expediente</h1>
      <p style="color: white; opacity: 0.8; margin-top: 5px;">${err.message}</p>
    `;
  }
}

function renderDossier(paciente) {
  // 1. Render Banner
  const banner = document.getElementById('patient-banner');
  banner.innerHTML = `
    <span style="font-size: 13px; text-transform: uppercase; font-weight: 600; opacity: 0.8;">Ficha de Expediente Clínico</span>
    <h1 class="patient-header-title" style="color: white !important;">${escapeHTML(paciente.nombre)}</h1>
    <p class="patient-header-desc">
      Edad: ${paciente.edad} años | Género: ${escapeHTML(paciente.genero)} | Tutor: ${escapeHTML(paciente.tutor)} | Teléfono: ${escapeHTML(paciente.celular)}    </p>
  `;

  // 2. Clear upload elements
  document.getElementById('video-input').value = '';
  document.getElementById('video-filename').innerText = '';
  document.getElementById('run-analysis-btn').disabled = true;
  document.getElementById('analysis-alert').classList.add('hidden');
  document.getElementById('analysis-progress-container').classList.add('hidden');

  // 3. Populate Medical Notes
  document.getElementById('patient-notes-field').value = paciente.notas || 'Sin notas registradas.';

  // 4. Calculate Average Metrics
  const sessions = paciente.historial_analisis || [];
  let avgAttention = 0;
  let avgDistraction = 0;
  let avgFidgeting = 0;

  if (sessions.length > 0) {
    const sumAtt = sessions.reduce((acc, s) => acc + s.atencion_porcentaje, 0);
    const sumFid = sessions.reduce((acc, s) => acc + s.fidgeting_score, 0);
    const sumDist = sessions.reduce((acc, s) => acc + s.distraccion, 0);

    avgAttention = Math.round(sumAtt / sessions.length);
    avgFidgeting = parseFloat((sumFid / sessions.length).toFixed(1));
    avgDistraction = Math.round((sumDist / sessions.length) * 100);
  }

  // Set Progress bar values
  document.getElementById('avg-attention-val').innerText = `${avgAttention}%`;
  document.getElementById('avg-attention-bar').style.width = `${avgAttention}%`;

  document.getElementById('avg-distraction-val').innerText = `${avgDistraction}%`;
  document.getElementById('avg-distraction-bar').style.width = `${avgDistraction}%`;

  document.getElementById('avg-fidgeting-val').innerText = `${avgFidgeting} / 10`;
  document.getElementById('avg-fidgeting-bar').style.width = `${avgFidgeting * 10}%`;

  // Update classes depending on average metrics
  const attBar = document.getElementById('avg-attention-bar');
  attBar.className = 'metric-progress-fill';
  if (avgAttention >= 70) attBar.classList.add('bg-success');
  else if (avgAttention >= 50) attBar.classList.add('bg-warning');
  else attBar.classList.add('bg-danger');

  const fidBar = document.getElementById('avg-fidgeting-bar');
  fidBar.className = 'metric-progress-fill';
  if (avgFidgeting < 4) fidBar.classList.add('bg-success');
  else if (avgFidgeting < 6.5) fidBar.classList.add('bg-warning');
  else fidBar.classList.add('bg-danger');

  // 5. Render Chart.js
  renderEvolutionChart(sessions);

  // 6. Render Sessions Accordion list
  renderSessionsList(sessions);
}

/**
 * Draw Interactive Line Chart with Chart.js
 */
function renderEvolutionChart(sessions) {
  const ctx = document.getElementById('evolution-chart').getContext('2d');

  // Clean old instance to prevent hover artifacts
  if (window.myEvolutionChart) {
    window.myEvolutionChart.destroy();
  }

  if (sessions.length === 0) {
    ctx.font = '14px Outfit';
    ctx.textAlign = 'center';
    ctx.fillText('Sin datos de sesiones anteriores para graficar.', ctx.canvas.width / 2, ctx.canvas.height / 2);
    return;
  }

  // Invert sessions to show them chronologically (from oldest to newest)
  const sortedSessions = [...sessions].reverse();
  const labels = sortedSessions.map(s => s.fecha.split(' ')[0]);
  const attentionData = sortedSessions.map(s => s.atencion_porcentaje);
  const fidgetingData = sortedSessions.map(s => s.fidgeting_score);

  window.myEvolutionChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: '% Atención',
          data: attentionData,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          yAxisID: 'y-attention',
          tension: 0.3,
          fill: true,
          borderWidth: 3
        },
        {
          label: 'Fidgeting (0-10)',
          data: fidgetingData,
          borderColor: '#ef4444',
          backgroundColor: 'transparent',
          yAxisID: 'y-fidgeting',
          tension: 0.3,
          borderWidth: 3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        'y-attention': {
          type: 'linear',
          position: 'left',
          min: 0,
          max: 100,
          title: {
            display: true,
            text: '% Atención Sostenida',
            font: { family: 'Outfit', weight: 'bold' }
          }
        },
        'y-fidgeting': {
          type: 'linear',
          position: 'right',
          min: 0,
          max: 10,
          grid: { drawOnChartArea: false }, // Avoid grid lines overlay
          title: {
            display: true,
            text: 'Score de Fidgeting / Hiperactividad',
            font: { family: 'Outfit', weight: 'bold' }
          }
        }
      },
      plugins: {
        legend: {
          labels: { font: { family: 'Outfit' } }
        }
      }
    }
  });
}

/**
 * Render Session Accordions
 */
function renderSessionsList(sessions) {
  const container = document.getElementById('sessions-accordion-container');
  if (sessions.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; color: var(--text-muted); padding: 20px;">
        Este paciente no registra ninguna sesión en la base de datos MySQL feria.
      </div>
    `;
    return;
  }

  container.innerHTML = sessions.map((ses, idx) => `
    <div class="session-accordion" id="accordion-s-${ses.id}">
      <div class="session-header" onclick="toggleAccordion('accordion-s-${ses.id}')">
        <span>📅 Sesión ${ses.fecha}</span>
        <div class="session-header-metrics">
          <span class="session-badge" style="color: var(--success);">Atención: ${ses.atencion_porcentaje}%</span>
          <span class="session-badge" style="color: var(--danger);">Fidgeting: ${ses.fidgeting_score}/10</span>
          <span>▼</span>
        </div>
      </div>
      <div class="session-content ${idx === 0 ? '' : 'hidden'}">
        <div class="session-detail-grid">
          <div class="session-detail-card">
            <span class="session-detail-label">ID de Sesión</span>
            <div class="session-detail-value">A-${ses.id}</div>
          </div>
          <div class="session-detail-card">
            <span class="session-detail-label">Duración Total</span>
            <div class="session-detail-value">${ses.duracion_total_seg} seg</div>
          </div>
          <div class="session-detail-card">
            <span class="session-detail-label">Eventos Distracción</span>
            <div class="session-detail-value">${ses.eventos_distraccion}</div>
          </div>
          <div class="session-detail-card">
            <span class="session-detail-label">Tiempo Distraído</span>
            <div class="session-detail-value">${ses.tiempo_distraccion_seg} seg</div>
          </div>
        </div>
        
        <div class="session-diagnosis">
          <strong>Impresión Clínica Automatizada:</strong><br>
          ${escapeHTML(ses.diagnostico_auto)}
        </div>
        
        <a href="/api/reportes/pdf/${ses.id}" class="btn btn-secondary" style="width: auto; padding: 8px 15px; font-size: 13px;" download>
          📥 Descargar Reporte PDF Clínico
        </a>
      </div>
    </div>
  `).join('');
}

function toggleAccordion(id) {
  const accordion = document.getElementById(id);
  const content = accordion.querySelector('.session-content');
  const arrow = accordion.querySelector('.session-header-metrics span:last-child');

  if (content.classList.contains('hidden')) {
    content.classList.remove('hidden');
    arrow.innerText = '▲';
  } else {
    content.classList.add('hidden');
    arrow.innerText = '▼';
  }
}

/* =====================================================================
   TABS MANAGEMENT (REAL VIDEO UPLOAD VS SIMULATOR)
   ===================================================================== */
function switchAnalysisTab(tab) {
  // Deactivate all
  document.getElementById('tab-btn-upload').classList.remove('active');
  document.getElementById('tab-btn-simulate').classList.remove('active');
  document.getElementById('tab-pane-upload').classList.remove('active');
  document.getElementById('tab-pane-simulate').classList.remove('active');

  // Activate selected
  if (tab === 'upload') {
    document.getElementById('tab-btn-upload').classList.add('active');
    document.getElementById('tab-pane-upload').classList.add('active');
  } else {
    document.getElementById('tab-btn-simulate').classList.add('active');
    document.getElementById('tab-pane-simulate').classList.add('active');
  }
}

/* =====================================================================
   VIDEO PROCESSING & BEHAVIOR SIMULATOR API EXECUTIONS
   ===================================================================== */
async function executeVideoAnalysis() {
  const videoInput = document.getElementById('video-input');
  const alertEl = document.getElementById('analysis-alert');
  const progressContainer = document.getElementById('analysis-progress-container');
  const progressBar = document.getElementById('analysis-progress-bar');
  const progressStatus = document.getElementById('progress-status');
  const progressPercentage = document.getElementById('progress-percentage');
  const runBtn = document.getElementById('run-analysis-btn');

  if (!videoInput.files || videoInput.files.length === 0) return;
  const file = videoInput.files[0];

  alertEl.classList.add('hidden');
  progressContainer.classList.remove('hidden');
  runBtn.disabled = true;

  // Simulate smooth OpenCV processing progress ticks since standard HTTP POST is monolithic
  let pct = 0;
  progressBar.style.width = '0%';
  progressPercentage.innerText = '0%';
  progressStatus.innerText = 'Subiendo video e iniciando OpenCV/MediaPipe...';

  const timer = setInterval(() => {
    if (pct < 92) {
      pct += Math.floor(Math.random() * 5) + 2;
      pct = Math.min(pct, 92);
      progressBar.style.width = `${pct}%`;
      progressPercentage.innerText = `${pct}%`;

      if (pct > 70) {
        progressStatus.innerText = 'Motor de comportamiento estimando postura de la cara y fidgeting...';
      } else if (pct > 35) {
        progressStatus.innerText = 'Detectando puntos faciales (landmarks) con redes neuronales...';
      } else {
        progressStatus.innerText = 'Procesando fotogramas de video...';
      }
    }
  }, 1000);

  try {
    const res = await API.subirVideo(currentPatient.id, file);

    clearInterval(timer);
    progressBar.style.width = '100%';
    progressPercentage.innerText = '100%';
    progressStatus.innerText = '¡Análisis de video completado! Guardando en MySQL feria...';

    setTimeout(async () => {
      // Reload patient dossier to reflect changes
      await openPatientDossier(currentPatient.id);
    }, 1500);
  } catch (err) {
    clearInterval(timer);
    progressContainer.classList.add('hidden');
    alertEl.innerText = err.message || 'Error al procesar el archivo.';
    alertEl.classList.remove('hidden');
    runBtn.disabled = false;
  }
}

async function executeSimulation() {
  const alertEl = document.getElementById('analysis-alert');
  const progressContainer = document.getElementById('analysis-progress-container');
  const progressBar = document.getElementById('analysis-progress-bar');
  const progressStatus = document.getElementById('progress-status');
  const progressPercentage = document.getElementById('progress-percentage');
  const runBtn = document.getElementById('run-simulation-btn');

  const videoName = document.getElementById('sim-name').value.trim();
  const atencion = parseFloat(document.getElementById('sim-attention').value);
  const hiperactividad = parseFloat(document.getElementById('sim-fidgeting').value);
  const duracion = parseInt(document.getElementById('sim-duration').value);

  alertEl.classList.add('hidden');
  progressContainer.classList.remove('hidden');
  runBtn.disabled = true;

  // Process simulation animation (fast 2 seconds sleep equivalent)
  progressBar.style.width = '0%';
  progressPercentage.innerText = '0%';
  progressStatus.innerText = 'Corriendo algoritmos clínicos estocásticos...';

  let pct = 0;
  const timer = setInterval(() => {
    if (pct < 90) {
      pct += 15;
      progressBar.style.width = `${pct}%`;
      progressPercentage.innerText = `${pct}%`;
    }
  }, 300);

  try {
    await API.simularAnalisis({
      paciente_id: currentPatient.id,
      video_name: videoName,
      atencion: atencion,
      hiperactividad: hiperactividad,
      duracion_seg: duracion
    });

    clearInterval(timer);
    progressBar.style.width = '100%';
    progressPercentage.innerText = '100%';
    progressStatus.innerText = 'Simulación completada y guardada en MySQL...';

    setTimeout(async () => {
      // Reload patient dossier
      await openPatientDossier(currentPatient.id);
      runBtn.disabled = false;
    }, 1200);
  } catch (err) {
    clearInterval(timer);
    progressContainer.classList.add('hidden');
    alertEl.innerText = err.message || 'Error durante la simulación.';
    alertEl.classList.remove('hidden');
    runBtn.disabled = false;
  }
}

/* =====================================================================
   HELPER UTILITIES
   ===================================================================== */
function escapeHTML(str) {
  if (!str) return '';
  return str.replace(/[&<>'"]/g,
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}
