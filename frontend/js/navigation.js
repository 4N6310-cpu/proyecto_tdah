/* =====================================================================
   ADHD-VISION SINGLE PAGE APPLICATION (SPA) ROUTER & DOM CONTROLLER
   ===================================================================== */

// Global navigation state
let currentView = null;
let currentPatient = null;
let patientsData = [];
let selectedPhotoBase64 = null;
let selectedPhotoFile = null;

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
      const response = await fetch('login.html?t=' + Date.now());
      const html = await response.text();
      container.innerHTML = html;
      bindLoginEvents();
    } else if (viewName === 'dashboard') {
      const response = await fetch('dashboard.html?t=' + Date.now());
      const html = await response.text();
      container.innerHTML = html;

      const evalData = Auth.getEvaluador();
      document.getElementById('user-display').innerText = `${evalData.nombre} (${evalData.especialidad || evalData.rol || 'Especialista'})`;

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

  // Patient photo file input change listener
  const photoInput = document.getElementById('modal-patient-photo');
  if (photoInput) {
    photoInput.addEventListener('change', (e) => {
      console.log("File input changed. Files selected:", e.target.files ? e.target.files.length : 0);
      if (e.target.files && e.target.files.length > 0) {
        const file = e.target.files[0];
        selectedPhotoFile = file; // Store raw file object
        console.log("Processing file:", file.name, "size:", file.size, "type:", file.type);
        const reader = new FileReader();
        reader.onload = function(event) {
          const rawBase64 = event.target.result;
          console.log("FileReader completed. Raw Base64 string length:", rawBase64.length);
          
          // Helper to update UI preview
          const updatePreview = (base64Data) => {
            const previewEl = document.getElementById('modal-photo-preview');
            const placeholderEl = document.getElementById('modal-photo-placeholder');
            if (previewEl && placeholderEl) {
              previewEl.src = base64Data;
              previewEl.style.display = 'block';
              placeholderEl.style.display = 'none';
              console.log("Preview image updated successfully.");
            } else {
              console.error("Preview elements not found in DOM.");
            }
          };

          // Try canvas resizing
          try {
            const img = new Image();
            img.onload = function() {
              try {
                console.log("Image loaded in memory. Original size:", img.width, "x", img.height);
                const maxDim = 300;
                let width = img.width;
                let height = img.height;
                
                if (width > maxDim || height > maxDim) {
                  if (width > height) {
                    height = Math.round((height * maxDim) / width);
                    width = maxDim;
                  } else {
                    width = Math.round((width * maxDim) / height);
                    height = maxDim;
                  }
                }
                
                console.log("Calculated dimensions for resize:", width, "x", height);
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                
                const resizedBase64 = canvas.toDataURL('image/jpeg', 0.85);
                console.log("Canvas resize complete. New Base64 length:", resizedBase64.length);
                selectedPhotoBase64 = resizedBase64;
                updatePreview(resizedBase64);
              } catch (canvasErr) {
                console.error("Canvas resizing logic crashed. Falling back to raw image:", canvasErr);
                selectedPhotoBase64 = rawBase64;
                updatePreview(rawBase64);
              }
            };
            img.onerror = function(loadErr) {
              console.error("Failed to load image element. Falling back to raw Base64:", loadErr);
              selectedPhotoBase64 = rawBase64;
              updatePreview(rawBase64);
            };
            img.src = rawBase64;
          } catch (imgErr) {
            console.error("Image loading initialization failed. Using raw Base64:", imgErr);
            selectedPhotoBase64 = rawBase64;
            updatePreview(rawBase64);
          }
        };
        reader.onerror = function(readErr) {
          console.error("FileReader failed to read the file:", readErr);
        };
        reader.readAsDataURL(file);
      }
    });
  } else {
    console.error("modal-patient-photo element was not found in DOM.");
  }
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

  grid.innerHTML = list.map(pac => {
    const avatarHtml = pac.foto_perfil 
      ? `<img src="${pac.foto_perfil}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`
      : `👦`;
    return `
      <div class="patient-card" onclick="openPatientDossier(${pac.id})">
        <div class="patient-avatar">${avatarHtml}</div>
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
    `;
  }).join('');
}

/* =====================================================================
   PATIENT CRUD MODAL ACTIONS
   ===================================================================== */
function openAddPatientModal() {
  document.getElementById('modal-title').innerText = 'Agregar Nuevo Paciente';
  document.getElementById('modal-patient-id').value = '';
  document.getElementById('modal-patient-name').value = '';
  document.getElementById('modal-patient-birthdate').value = '';
  document.getElementById('modal-patient-gender').value = 'No especificado';
  document.getElementById('modal-patient-tutor').value = '';
  document.getElementById('modal-patient-tutor-phone').value = '';
  document.getElementById('modal-patient-history').value = '';
  
  // Reset photo upload elements
  selectedPhotoBase64 = null;
  selectedPhotoFile = null;
  document.getElementById('modal-patient-photo').value = '';
  document.getElementById('modal-photo-preview').src = '';
  document.getElementById('modal-photo-preview').style.display = 'none';
  document.getElementById('modal-photo-placeholder').style.display = 'block';
  
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
  document.getElementById('modal-patient-gender').value = patient.genero || 'No especificado';
  document.getElementById('modal-patient-tutor').value = patient.tutor_nombre || '';
  document.getElementById('modal-patient-tutor-phone').value = (patient.tutor_celular && patient.tutor_celular !== "No tiene") ? patient.tutor_celular : '';
  document.getElementById('modal-patient-history').value = patient.notas || '';
  
  // Load profile photo if it exists
  document.getElementById('modal-patient-photo').value = '';
  selectedPhotoFile = null;
  if (patient.foto_perfil) {
    selectedPhotoBase64 = patient.foto_perfil;
    document.getElementById('modal-photo-preview').src = patient.foto_perfil;
    document.getElementById('modal-photo-preview').style.display = 'block';
    document.getElementById('modal-photo-placeholder').style.display = 'none';
  } else {
    selectedPhotoBase64 = null;
    document.getElementById('modal-photo-preview').src = '';
    document.getElementById('modal-photo-preview').style.display = 'none';
    document.getElementById('modal-photo-placeholder').style.display = 'block';
  }
  
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
  const genero = document.getElementById('modal-patient-gender').value;
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
      await API.updatePaciente(id, nombre, fechaNacimiento, historialClinico, tutor, numeroDeTutor, selectedPhotoFile, genero);
    } else {
      await API.addPaciente(nombre, fechaNacimiento, historialClinico, evalData.id, tutor, numeroDeTutor, selectedPhotoFile, genero);
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

/**
 * Custom promise-based patient deletion confirmation modal
 */
function confirmPatientDeletion(patientName) {
  return new Promise((resolve) => {
    const modal = document.getElementById('delete-patient-confirm-modal');
    const nameEl = document.getElementById('confirm-patient-name');
    const acceptBtn = document.getElementById('confirm-accept-btn');
    const cancelBtn = document.getElementById('confirm-cancel-btn');
    
    if (!modal || !acceptBtn || !cancelBtn) {
      // Fallback to native confirm if modal elements are missing
      resolve(confirm(`¿Estás seguro de que deseas eliminar permanentemente a ${patientName}? Esta acción no se puede deshacer y borrará también todas sus sesiones asociadas.`));
      return;
    }
    
    // Set patient name
    if (nameEl) {
      nameEl.innerText = patientName;
    }
    
    // Show modal
    modal.classList.remove('hidden');
    
    // Focus accept button for accessibility
    acceptBtn.focus();
    
    const handleOutsideClick = (e) => {
      if (e.target === modal) {
        handleCancel();
      }
    };
    
    const handleKeyPress = (e) => {
      if (e.key === 'Escape') {
        handleCancel();
      }
    };
    
    const handleAccept = () => {
      cleanup();
      resolve(true);
    };
    
    const handleCancel = () => {
      cleanup();
      resolve(false);
    };
    
    const cleanup = () => {
      modal.classList.add('hidden');
      acceptBtn.removeEventListener('click', handleAccept);
      cancelBtn.removeEventListener('click', handleCancel);
      modal.removeEventListener('click', handleOutsideClick);
      document.removeEventListener('keydown', handleKeyPress);
    };
    
    acceptBtn.addEventListener('click', handleAccept);
    cancelBtn.addEventListener('click', handleCancel);
    modal.addEventListener('click', handleOutsideClick);
    document.addEventListener('keydown', handleKeyPress);
  });
}

async function deletePatientAction(event, patientId) {
  if (event) event.stopPropagation(); // Evitar abrir el expediente del paciente
  
  const patient = patientsData.find(p => p.id === patientId);
  const name = patient ? patient.nombre : 'este paciente';
  
  const confirmDelete = await confirmPatientDeletion(name);
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
  const bannerAvatarHtml = paciente.foto_perfil
    ? `<img src="${paciente.foto_perfil}" style="width: 100%; height: 100%; object-fit: cover;">`
    : `<span style="font-size: 45px;">👦</span>`;
    
  banner.innerHTML = `
    <div class="patient-banner-avatar" style="width: 80px; height: 80px; border-radius: 50%; overflow: hidden; border: 3px solid rgba(255,255,255,0.4); display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.1); flex-shrink: 0;">
      ${bannerAvatarHtml}
    </div>
    <div>
      <span style="font-size: 13px; text-transform: uppercase; font-weight: 600; opacity: 0.8; display: block; margin-bottom: 4px;">Ficha de Expediente Clínico</span>
      <h1 class="patient-header-title" style="color: white !important; margin: 0 0 4px 0; line-height: 1.2;">${escapeHTML(paciente.nombre)}</h1>
      <p class="patient-header-desc" style="margin: 0;">
        Edad: ${paciente.edad} años | Género: ${escapeHTML(paciente.genero)} | Tutor: ${escapeHTML(paciente.tutor)} | Teléfono: ${escapeHTML(paciente.celular)}
      </p>
    </div>
  `;

  // 2. Clear upload elements
  document.getElementById('video-input').value = '';
  document.getElementById('video-filename').innerText = '';
  document.getElementById('run-analysis-btn').disabled = true;
  document.getElementById('analysis-alert').classList.add('hidden');
  document.getElementById('analysis-progress-container').classList.add('hidden');

  // 3. Populate Medical Notes
  document.getElementById('patient-notes-field').value = paciente.notas || '';

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

        <div class="session-notes-section" style="margin-top: 15px; margin-bottom: 15px; text-align: left;">
          <label for="session-notes-${ses.id}" style="font-weight: 600; font-size: 13px; display: block; margin-bottom: 5px; color: var(--text-dark);">Notas y Observaciones de la Sesión:</label>
          <textarea id="session-notes-${ses.id}" class="form-control" placeholder="Escribe observaciones clínicas sobre esta sesión..." style="min-height: 80px; resize: vertical; margin-bottom: 8px;">${escapeHTML(ses.notas || '')}</textarea>
          <div style="display: flex; align-items: center; gap: 10px;">
            <button class="btn btn-secondary" style="width: auto; padding: 6px 14px; font-size: 13px;" onclick="saveSessionNotes(${ses.id})">Guardar Notas de Sesión</button>
            <span id="session-notes-status-${ses.id}" style="font-size: 12px; font-weight: 600;"></span>
          </div>
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

async function savePatientNotes() {
  if (!currentPatient) return;
  const notesField = document.getElementById('patient-notes-field');
  const newNotes = notesField.value.trim();
  const statusSpan = document.getElementById('patient-notes-status');
  const saveBtn = document.getElementById('save-patient-notes-btn');

  saveBtn.disabled = true;
  statusSpan.innerText = 'Guardando...';
  statusSpan.style.color = 'var(--text-muted)';

  try {
    const tutorPhone = (currentPatient.celular === 'no tiene' || !currentPatient.celular) ? '' : currentPatient.celular;
    
    await API.updatePaciente(
      currentPatient.id,
      currentPatient.nombre,
      currentPatient.fecha_nacimiento,
      newNotes,
      currentPatient.tutor,
      tutorPhone,
      null,
      currentPatient.genero
    );

    currentPatient.notas = newNotes;
    statusSpan.innerText = '✓ Guardado correctamente';
    statusSpan.style.color = 'var(--success)';
  } catch (err) {
    statusSpan.innerText = '✗ Error: ' + err.message;
    statusSpan.style.color = 'var(--danger)';
  } finally {
    saveBtn.disabled = false;
    setTimeout(() => {
      if (statusSpan.innerText.includes('Guardado') || statusSpan.innerText.includes('Error')) {
        statusSpan.innerText = '';
      }
    }, 3000);
  }
}

async function saveSessionNotes(sessionId) {
  const notesField = document.getElementById(`session-notes-${sessionId}`);
  if (!notesField) return;
  const newNotes = notesField.value.trim();
  const statusSpan = document.getElementById(`session-notes-status-${sessionId}`);
  const container = document.getElementById(`accordion-s-${sessionId}`);
  const saveBtn = container ? container.querySelector('.session-notes-section button') : null;

  if (saveBtn) saveBtn.disabled = true;
  statusSpan.innerText = 'Guardando...';
  statusSpan.style.color = 'var(--text-muted)';

  try {
    await API.updateSessionNotes(sessionId, newNotes);

    if (currentPatient && currentPatient.historial_analisis) {
      const session = currentPatient.historial_analisis.find(s => s.id === sessionId);
      if (session) {
        session.notas = newNotes;
      }
    }

    statusSpan.innerText = '✓ Guardado';
    statusSpan.style.color = 'var(--success)';
  } catch (err) {
    statusSpan.innerText = '✗ Error: ' + err.message;
    statusSpan.style.color = 'var(--danger)';
  } finally {
    if (saveBtn) saveBtn.disabled = false;
    setTimeout(() => {
      statusSpan.innerText = '';
    }, 3000);
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
