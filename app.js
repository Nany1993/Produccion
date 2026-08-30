
// ============================================================
// UTILIDADES
// ============================================================

const Toast = {
  container: null,

  init() {
    if (!this.container) {
      this.container = document.getElementById('toast-container');
    }
  },

  show(message, type = 'info', duration = 3000) {
    this.init();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || icons.info}</span>
      <span class="toast-message">${message}</span>
      <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    this.container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('toast-visible'));
    setTimeout(() => {
      toast.classList.remove('toast-visible');
      toast.classList.add('toast-hiding');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  success(msg) { this.show(msg, 'success'); },
  error(msg) { this.show(msg, 'error', 5000); },
  warning(msg) { this.show(msg, 'warning', 4000); },
  info(msg) { this.show(msg, 'info'); }
};

const Modal = {
  overlay: null,

  confirm(title, message) {
    return new Promise((resolve) => {
      this.overlay = document.getElementById('modal-overlay');
      const titleEl = document.getElementById('modal-title');
      const msgEl = document.getElementById('modal-message');
      const confirmBtn = document.getElementById('modal-confirm');
      const cancelBtn = document.getElementById('modal-cancel');

      titleEl.textContent = title;
      msgEl.textContent = message;
      this.overlay.classList.add('modal-visible');

      const cleanup = () => {
        this.overlay.classList.remove('modal-visible');
        confirmBtn.onclick = null;
        cancelBtn.onclick = null;
      };

      confirmBtn.onclick = () => { cleanup(); resolve(true); };
      cancelBtn.onclick = () => { cleanup(); resolve(false); };
    });
  }
};

async function api(url, options = {}) {
  const btn = options._btn;
  if (btn) {
    btn.disabled = true;
    btn.dataset.originalText = btn.textContent;
    btn.textContent = 'Procesando...';
  }

  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    });
    const data = await res.json();

    if (!res.ok) {
      Toast.error(data.error || 'Error en la operación');
      return null;
    }
    return data;
  } catch (e) {
    Toast.error('Error de conexión con el servidor');
    return null;
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = btn.dataset.originalText;
    }
  }
}

function formatTime(seconds) {
  if (!seconds && seconds !== 0) return 'N/A';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function validateField(inputId, rules = {}) {
  const input = document.getElementById(inputId);
  const value = input.value.trim();
  let error = '';

  if (rules.required && !value) {
    error = 'Campo requerido';
  } else if (rules.minLength && value.length < rules.minLength) {
    error = `Mínimo ${rules.minLength} caracteres`;
  } else if (rules.positive && (isNaN(value) || Number(value) <= 0)) {
    error = 'Debe ser un número positivo';
  } else if (rules.number && isNaN(value)) {
    error = 'Debe ser un número';
  }

  showFieldError(inputId, error);
  return !error;
}

function showFieldError(inputId, message) {
  const input = document.getElementById(inputId);
  let errorEl = document.getElementById(`${inputId}-error`);

  if (!errorEl) {
    errorEl = document.createElement('span');
    errorEl.id = `${inputId}-error`;
    errorEl.className = 'field-error';
    input.parentElement.appendChild(errorEl);
  }

  errorEl.textContent = message;
  input.classList.toggle('input-error', !!message);
}

function clearFieldErrors(...ids) {
  ids.forEach(id => showFieldError(id, ''));
}

function togglePanel(containerId, btnId, showText, hideText) {
  const container = document.getElementById(containerId);
  const btn = document.getElementById(btnId);
  const isHidden = container.style.display === 'none' || !container.style.display;
  container.style.display = isHidden ? 'block' : 'none';
  if (btn) btn.textContent = isHidden ? hideText : showText;
}

function resetButton(btnId, text, color) {
  const btn = document.getElementById(btnId);
  if (btn) {
    btn.textContent = text;
    if (color) btn.style.background = color;
  }
}

// ============================================================
// SELECT CON BUSCADOR INTELIGENTE
// ============================================================

function hacerSelectBuscable(idSelect) {
  const select = document.getElementById(idSelect);
  if (!select || select.dataset.buscable) return;
  select.dataset.buscable = '1';

  // Contenedor nuevo que envuelve input + select
  const wrapper = document.createElement('div');
  wrapper.className = 'select-buscable';
  select.parentNode.insertBefore(wrapper, select);

  const input = document.createElement('input');
  input.type = 'text';
  input.className = 'select-buscable-input';
  input.placeholder = '🔎 Buscar...';
  input.autocomplete = 'off';
  wrapper.appendChild(input);
  wrapper.appendChild(select);

  const vacio = document.createElement('div');
  vacio.className = 'select-buscable-vacio';
  vacio.style.display = 'none';
  vacio.textContent = 'Sin resultados';
  wrapper.appendChild(vacio);

  function filtrar() {
    const q = input.value.toLowerCase().trim();
    let visibles = 0;
    Array.from(select.options).forEach(o => {
      const match = !q || o.text.toLowerCase().includes(q);
      o.hidden = !match;
      if (match) visibles++;
    });
    vacio.style.display = visibles === 0 ? 'block' : 'none';
    // Si solo hay una visible y hay query, seleccionarla
    if (visibles === 1 && q) {
      const opt = Array.from(select.options).find(o => !o.hidden);
      if (opt && opt.value !== select.value) select.value = opt.value;
    }
  }

  input.addEventListener('input', filtrar);
  select.addEventListener('change', () => { input.value = ''; filtrar(); });
  // El usuario puede resetear manualmente
  input.addEventListener('focus', () => {
    if (!input.value) { Array.from(select.options).forEach(o => o.hidden = false); vacio.style.display = 'none'; }
  });
}

const SELECTS_BUSCABLES = [
  'op-maquina', 'op-seccion',
  'prog-referencia',
  'input-usuario-empleado',
  'input-emp-maquina',
  'ctrl-maquina', 'ctrl-referencia',
  'input-orden-ref',
  'sim-referencia',
  'eff-referencia', 'eff-orden',
  'input-maquina-modulo'
];

function conectarBuscadores() {
  SELECTS_BUSCABLES.forEach(id => hacerSelectBuscable(id));
}

// ============================================================
// SESIÓN Y LOGIN
// ============================================================

let sesionActual = null;
let moduloActual = 'mod-maquinaria';

// Módulos permitidos por rol. Admin lo ve todo.
// Supervisor/Operador: solo registro + reportes (sin configuración ni datos maestros).
const MODULOS_BASICOS = ['mod-control-hora', 'mod-eficiencia', 'mod-progreso'];

function aplicarPermisosMenu() {
  const esAdmin = sesionActual && sesionActual.rol === 'Admin';
  const esBasico = !esAdmin; // supervisores y operadores → solo lo básico

  // Sección CONFIGURACIÓN completa: solo Admin
  const navConfig = document.getElementById('nav-config');
  if (navConfig) navConfig.style.display = esAdmin ? '' : 'none';

  if (esBasico) {
    // En OPERACIONES: ocultar todo menos Registro de Producción
    ['link-operaciones', 'link-ordenes', 'link-ingenieria', 'link-programacion'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.display = 'none';
    });
    // En ANÁLISIS: ocultar Simulador Balanceo (dejar Tablero y Progreso)
    const linkSim = document.getElementById('link-simulador');
    if (linkSim) linkSim.style.display = 'none';
    // Si el módulo actual no le corresponde al rol (p.ej. quedó Maquinaria
    // como activo), mostrar el Registro de Producción por defecto.
    if (!MODULOS_BASICOS.includes(moduloActual)) {
      showModule('mod-control-hora');
    }
  } else {
    // Admin: restaurar todo
    ['link-operaciones', 'link-ordenes', 'link-ingenieria', 'link-programacion'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.style.display = '';
    });
    const linkSim2 = document.getElementById('link-simulador');
    if (linkSim2) linkSim2.style.display = '';
  }
}

function guardarSesion(usuario) {
  sesionActual = usuario;
  localStorage.setItem('sesion', JSON.stringify(usuario));
  document.getElementById('login-overlay').classList.add('hidden');
  const bar = document.getElementById('session-bar');
  bar.style.display = 'flex';
  document.getElementById('session-info').innerText = `${usuario.nombre_empleado || usuario.nombre_usuario} · ${usuario.rol}`;
  // Control de modalidad global: visible solo para Admin
  const ctrlAdmin = document.getElementById('admin-modalidad');
  if (ctrlAdmin) {
    ctrlAdmin.style.display = (usuario.rol === 'Admin') ? 'inline-flex' : 'none';
  }
  aplicarPermisosMenu();
  Toast.success(`Bienvenido, ${usuario.nombre_usuario}`);
  initControlHora();
  cargarControlesHoy();
}

async function cambiarModalidadRegistro() {
  const sel = document.getElementById('select-modalidad');
  if (sesionActual && sesionActual.rol !== 'Admin') { Toast.error('Solo el administrador puede cambiar la modalidad'); return; }
  const data = await api('/api/configuracion', {
    method: 'PUT',
    body: JSON.stringify({ modalidad_registro: sel.value }),
    _btn: sel
  });
  if (data) {
    window.modalidadRegistro = data.modalidad_registro || sel.value;
    aplicarModalidadRegistro();
    Toast.success(`Modalidad de registro: ${window.modalidadRegistro}`);
  } else if (sel) {
    sel.value = window.modalidadRegistro || 'Diario';
  }
}

function cerrarSesion() {
  sesionActual = null;
  localStorage.removeItem('sesion');
  document.getElementById('login-overlay').classList.remove('hidden');
  document.getElementById('session-bar').style.display = 'none';
}

async function iniciarSesion() {
  const nombre = document.getElementById('login-usuario').value.trim();
  const password = document.getElementById('login-password').value;
  const errEl = document.getElementById('login-error');

  if (!nombre || !password) {
    errEl.textContent = 'Ingrese usuario y contraseña';
    errEl.style.display = 'block';
    return;
  }

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre_usuario: nombre, password })
    });
    const data = await res.json();
    if (!res.ok) {
      errEl.textContent = data.error || 'Credenciales inválidas';
      errEl.style.display = 'block';
      return;
    }
    errEl.style.display = 'none';
    guardarSesion(data);
  } catch (e) {
    errEl.textContent = 'Error de conexión';
    errEl.style.display = 'block';
  }
}

function ocultarSesionInicial() {
  const guardada = localStorage.getItem('sesion');
  if (guardada) {
    try {
      sesionActual = JSON.parse(guardada);
      document.getElementById('login-overlay').classList.add('hidden');
      document.getElementById('session-bar').style.display = 'flex';
      document.getElementById('session-info').innerText = `${sesionActual.nombre_empleado || sesionActual.nombre_usuario} · ${sesionActual.rol}`;
      const ctrlAdmin2 = document.getElementById('admin-modalidad');
      if (ctrlAdmin2) ctrlAdmin2.style.display = (sesionActual.rol === 'Admin') ? 'inline-flex' : 'none';
      aplicarPermisosMenu();
      return true;
    } catch (e) { localStorage.removeItem('sesion'); }
  }
  return false;
}

function toggleFormColapsable(formId, btnId, textoCrear) {
  const form = document.getElementById(formId);
  const btn = document.getElementById(btnId);
  if (!form || !btn) return;
  if (form.style.display === 'none') {
    form.style.display = 'block';
    btn.textContent = '− Cerrar';
  } else {
    form.style.display = 'none';
    btn.textContent = textoCrear;
  }
}

function abrirFormColapsable(formId, btnId) {
  const form = document.getElementById(formId);
  if (!form) return;
  if (form.style.display !== 'block') {
    form.style.display = 'block';
    const btn = document.getElementById(btnId);
    if (btn) btn.textContent = '− Cerrar';
  }
}

// ============================================================
// NAVEGACIÓN
// ============================================================

function toggleNavSection(sectionId) {
  const section = document.getElementById(sectionId);
  section.classList.toggle('expanded');
}

function expandParentSection(linkId) {
  const link = document.getElementById(linkId);
  if (!link) return;
  const navSection = link.closest('.nav-section');
  if (navSection && !navSection.classList.contains('expanded')) {
    navSection.classList.add('expanded');
  }
}

function showModule(moduleId) {
  moduloActual = moduleId;
  document.querySelectorAll('.module-section').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));

  document.getElementById(moduleId).classList.add('active');
  const linkId = moduleId.replace('mod-', 'link-');
  const link = document.getElementById(linkId);
  if (link) link.classList.add('active');

  expandParentSection(linkId);

  if (moduleId === 'mod-programacion') {
    cargarDatosProgramacion();
    cargarAsignaciones();
  }
  if (moduleId === 'mod-ordenes') {
    cargarOrdenes();
    cargarSelectOrdenesRef();
  }
  if (moduleId === 'mod-materiales') cargarMateriales();
  if (moduleId === 'mod-usuarios') {
    cargarUsuarios();
    cargarSelectUsuarioEmpleado();
    cargarUsuarioModulosSupervisor();
  }
  if (moduleId === 'mod-causas') cargarCausas();
  if (moduleId === 'mod-control-hora') initControlHora();
  if (moduleId === 'mod-progreso') cargarOrdenesReporte();
  if (moduleId === 'mod-eficiencia') {
    const hoy = new Date();
    const fi = document.getElementById('eff-fecha-inicio');
    const ff = document.getElementById('eff-fecha-fin');
    if (!fi.value || !ff.value) {
      const mes = hoy.getMonth();
      const anio = hoy.getFullYear();
      const primero = new Date(anio, mes, 1);
      const ultimo = new Date(anio, mes + 1, 0);
      const iso = d => d.toISOString().split('T')[0];
      if (!fi.value) fi.value = iso(primero);
      if (!ff.value) ff.value = iso(ultimo);
      consultarEficiencia();
    }
    cargarFiltrosEficiencia();
  }
}

// ============================================================
// CATÁLOGOS
// ============================================================

async function cargarSelectMaquinaModulo() {
  const mods = await api('/api/modulos');
  if (!mods) return;
  const select = document.getElementById('input-maquina-modulo');
  const val = select.value;
  select.innerHTML = '<option value="">Seleccione línea...</option>';
  mods.forEach(m => select.innerHTML += `<option value="${m.id}">${m.nombre}</option>`);
  if (val) select.value = val;
}

async function cargarMaquinaria() {
  const datos = await api('/api/maquinaria');
  if (!datos) return;

  const tbody = document.getElementById('lista-maquinaria');
  const select = document.getElementById('op-maquina');
  const empty = document.getElementById('empty-maquinaria');

  tbody.innerHTML = '';
  const valActual = select.value;
  select.innerHTML = '<option value="">Seleccione una máquina...</option>';

  if (datos.length === 0) {
    empty.style.display = 'block';
  } else {
    empty.style.display = 'none';
    datos.forEach(m => {
      const estadoClass = m.estado === 'Activa' ? 'badge-module' : (m.estado === 'Mantenimiento' ? 'badge-hour' : 'badge-machine');
      tbody.innerHTML += `
        <tr>
          <td><strong>${m.nombre}</strong></td>
          <td>${m.descripcion || '-'}</td>
          <td>${m.nombre_modulo ? `<span class="badge badge-module">${m.nombre_modulo}</span>` : '<span style="color:var(--text-muted);">Sin línea</span>'}</td>
          <td>${m.velocidad_tipica ? m.velocidad_tipica + ' uds/h' : '-'}</td>
          <td><span class="badge ${estadoClass}">${m.estado}</span></td>
        </tr>
      `;
      select.innerHTML += `<option value="${m.id}">${m.nombre}</option>`;
    });
  }
  if (valActual) select.value = valActual;
}

async function guardarMaquina() {
  const nombre = document.getElementById('input-maquina').value.trim();
  const descripcion = document.getElementById('input-maquina-desc').value.trim();
  const idModulo = document.getElementById('input-maquina-modulo').value;
  const velocidad = document.getElementById('input-maquina-vel').value;
  const estado = document.getElementById('input-maquina-estado').value;

  if (!nombre) { showFieldError('input-maquina', 'Ingrese un nombre'); return; }
  clearFieldErrors('input-maquina');
  if (!idModulo) { showFieldError('input-maquina-modulo', 'Seleccione la línea'); return; }
  clearFieldErrors('input-maquina-modulo');

  const data = await api('/api/maquinaria', {
    method: 'POST',
    body: JSON.stringify({
      nombre,
      descripcion: descripcion || null,
      id_modulo: parseInt(idModulo),
      velocidad_tipica: velocidad ? parseInt(velocidad) : null,
      estado
    }),
    _btn: event.target
  });

  if (data) {
    document.getElementById('input-maquina').value = '';
    document.getElementById('input-maquina-desc').value = '';
    document.getElementById('input-maquina-modulo').value = '';
    document.getElementById('input-maquina-vel').value = '';
    document.getElementById('input-maquina-estado').value = 'Activa';
    Toast.success(data.mensaje || 'Máquina guardada');
    cargarMaquinaria();
  }
}

async function cargarSecciones() {
  const datos = await api('/api/secciones');
  if (!datos) return;

  const tbody = document.getElementById('lista-secciones');
  const select = document.getElementById('op-seccion');
  const empty = document.getElementById('empty-secciones');

  tbody.innerHTML = '';
  const valActual = select.value;
  select.innerHTML = '<option value="">Seleccione una sección...</option>';

  if (datos.length === 0) {
    empty.style.display = 'block';
  } else {
    empty.style.display = 'none';
    datos.forEach(s => {
      tbody.innerHTML += `
        <tr>
          <td>${s.orden_proceso || '-'}</td>
          <td><strong>${s.nombre}</strong></td>
          <td>${s.descripcion || '-'}</td>
        </tr>
      `;
      select.innerHTML += `<option value="${s.id}">${s.nombre}</option>`;
    });
  }
  if (valActual) select.value = valActual;
}

async function guardarSeccion() {
  const nombre = document.getElementById('input-seccion').value.trim();
  const descripcion = document.getElementById('input-seccion-desc').value.trim();
  const orden = document.getElementById('input-seccion-orden').value;

  if (!nombre) { showFieldError('input-seccion', 'Ingrese un nombre'); return; }
  clearFieldErrors('input-seccion');

  const data = await api('/api/secciones', {
    method: 'POST',
    body: JSON.stringify({
      nombre,
      descripcion: descripcion || null,
      orden_proceso: orden ? parseInt(orden) : null
    }),
    _btn: event.target
  });

  if (data) {
    document.getElementById('input-seccion').value = '';
    document.getElementById('input-seccion-desc').value = '';
    document.getElementById('input-seccion-orden').value = '';
    Toast.success(data.mensaje || 'Sección guardada');
    cargarSecciones();
  }
}

async function cargarModulos() {
  const datos = await api('/api/modulos');
  if (!datos) return;

  const tbody = document.getElementById('lista-modulos');
  const empty = document.getElementById('empty-modulos');

  tbody.innerHTML = '';
  if (datos.length === 0) {
    empty.style.display = 'block';
  } else {
    empty.style.display = 'none';
    datos.forEach(m => {
      const estadoClass = m.estado === 'Activo' ? 'badge-module' : 'badge-machine';
      let capCell = '<td>-</td>';
      if (m.capacidad_maxima) {
        const actual = m.operadores_actuales || 0;
        const cap = m.capacidad_maxima;
        const pct = actual / cap;
        const color = pct >= 1 ? '#dc3545' : (pct >= 0.8 ? '#e6a23c' : '#2ea367');
        capCell = `<td><span style="color:${color};font-weight:600;">${actual}</span>/<span style="font-weight:600;">${cap}</span> op.</td>`;
      }
      tbody.innerHTML += `
        <tr>
          <td>${m.id}</td>
          <td><strong>${m.nombre}</strong></td>
          ${capCell}
          <td>${m.ubicacion || '-'}</td>
          <td><span class="badge ${estadoClass}">${m.estado}</span></td>
        </tr>
      `;
    });
  }
}

async function guardarModulo() {
  const nombre = document.getElementById('input-modulo').value.trim();
  const capacidad = document.getElementById('input-modulo-cap').value;
  const ubicacion = document.getElementById('input-modulo-ubic').value.trim();
  const estado = document.getElementById('input-modulo-estado').value;

  if (!nombre) { showFieldError('input-modulo', 'Ingrese un nombre'); return; }
  clearFieldErrors('input-modulo');

  const data = await api('/api/modulos', {
    method: 'POST',
    body: JSON.stringify({
      nombre,
      capacidad_maxima: capacidad ? parseInt(capacidad) : null,
      ubicacion: ubicacion || null,
      estado
    }),
    _btn: event.target
  });

  if (data) {
    document.getElementById('input-modulo').value = '';
    document.getElementById('input-modulo-cap').value = '';
    document.getElementById('input-modulo-ubic').value = '';
    document.getElementById('input-modulo-estado').value = 'Activo';
    Toast.success(data.mensaje || 'Módulo guardado');
    cargarModulos();
  }
}

async function cargarHoras() {
  const datos = await api('/api/horas');
  if (!datos) return;

  const tbody = document.getElementById('lista-horas');
  const empty = document.getElementById('empty-horas');

  tbody.innerHTML = '';
  if (datos.length === 0) {
    empty.style.display = 'block';
  } else {
    empty.style.display = 'none';
    datos.forEach(h => {
      tbody.innerHTML += `
        <tr>
          <td>${h.id}</td>
          <td><strong>${h.nombre}</strong></td>
          <td>${h.hora_inicio || '-'}</td>
          <td>${h.hora_fin || '-'}</td>
        </tr>
      `;
    });
  }
}

async function guardarHora() {
  const nombre = document.getElementById('input-hora').value.trim();
  const horaInicio = document.getElementById('input-hora-inicio').value;
  const horaFin = document.getElementById('input-hora-fin').value;

  if (!nombre) { showFieldError('input-hora', 'Ingrese un nombre'); return; }
  clearFieldErrors('input-hora');

  const data = await api('/api/horas', {
    method: 'POST',
    body: JSON.stringify({
      nombre,
      hora_inicio: horaInicio || null,
      hora_fin: horaFin || null
    }),
    _btn: event.target
  });

  if (data) {
    document.getElementById('input-hora').value = '';
    document.getElementById('input-hora-inicio').value = '';
    document.getElementById('input-hora-fin').value = '';
    Toast.success(data.mensaje || 'Hora guardada');
    cargarHoras();
  }
}

async function cargarParadas() {
  const datos = await api('/api/paradas');
  if (!datos) return;

  const tbody = document.getElementById('lista-paradas');
  const empty = document.getElementById('empty-paradas');

  tbody.innerHTML = '';
  if (datos.length === 0) {
    empty.style.display = 'block';
  } else {
    empty.style.display = 'none';
    datos.forEach(p => {
      const tipoClass = p.tipo === 'Obligatoria' ? 'badge-module' : 'badge-machine';
      tbody.innerHTML += `
        <tr>
          <td>${p.id}</td>
          <td><strong>${p.nombre}</strong></td>
          <td>${formatTime(p.tiempo)}</td>
          <td><span class="badge ${tipoClass}">${p.tipo}</span></td>
          <td>${p.frecuencia}</td>
        </tr>
      `;
    });
  }
}

async function guardarParada() {
  const nombre = document.getElementById('input-parada-nombre').value.trim();
  const tiempo = document.getElementById('input-parada-tiempo').value;
  const tipo = document.getElementById('input-parada-tipo').value;
  const frecuencia = document.getElementById('input-parada-frec').value;

  let valid = true;
  if (!nombre) { showFieldError('input-parada-nombre', 'Ingrese un nombre'); valid = false; }
  else { clearFieldErrors('input-parada-nombre'); }

  if (!tiempo || isNaN(tiempo)) { showFieldError('input-parada-tiempo', 'Ingrese un tiempo válido'); valid = false; }
  else { clearFieldErrors('input-parada-tiempo'); }

  if (!valid) return;

  const data = await api('/api/paradas', {
    method: 'POST',
    body: JSON.stringify({
      nombre,
      tiempo: parseInt(tiempo),
      tipo,
      frecuencia
    }),
    _btn: event.target
  });

  if (data) {
    document.getElementById('input-parada-nombre').value = '';
    document.getElementById('input-parada-tiempo').value = '';
    document.getElementById('input-parada-tipo').value = 'Opcional';
    document.getElementById('input-parada-frec').value = 'Diaria';
    Toast.success(data.mensaje || 'Parada guardada');
    cargarParadas();
  }
}

// ============================================================
// EMPLEADOS
// ============================================================

let idEmpleadoEnEdicion = null;

async function cargarEmpleados() {
  const datos = await api('/api/empleados');
  if (!datos) return;

  const tbody = document.getElementById('lista-empleados');
  const empty = document.getElementById('empty-empleados');

  tbody.innerHTML = '';
  if (datos.length === 0) {
    empty.style.display = 'block';
  } else {
    empty.style.display = 'none';
    datos.forEach(e => {
      const objStr = JSON.stringify(e).replace(/'/g, "\\'").replace(/"/g, '&quot;');
      const estadoClass = e.estado === 'Activo' ? 'badge-module' : (e.estado === 'Vacaciones' || e.estado === 'Incapacidad' ? 'badge-hour' : 'badge-machine');
      const rolClass = e.rol === 'Supervisor' ? 'badge-hour' : 'badge-machine';
      tbody.innerHTML += `
        <tr>
          <td>${e.numero_documento}</td>
          <td><strong>${e.nombre}</strong></td>
          <td><span class="badge ${rolClass}">${e.rol || 'Operador'}</span></td>
          <td>${e.cargo}</td>
          <td>${e.nombre_maquina ? `<span class="badge badge-machine">${e.nombre_maquina}</span>` : (e.rol === 'Supervisor' ? '<span style="color:var(--text-muted);">Supervisa</span>' : '-')}</td>
          <td><span class="badge ${estadoClass}">${e.estado}</span></td>
          <td class="action-buttons">
            <button class="btn-icon btn-edit" onclick="iniciarEdicionEmpleado(${objStr})">Editar</button>
            <button class="btn-icon btn-delete" onclick="eliminarEmpleado(${e.id})">Eliminar</button>
          </td>
        </tr>
      `;
    });
  }
}

async function cargarSelectMaquinaEmpleado() {
  const maq = await api('/api/maquinaria');
  if (!maq) return;
  const select = document.getElementById('input-emp-maquina');
  const val = select.value;
  select.innerHTML = '<option value="">Seleccione máquina...</option>';
  maq.forEach(m => select.innerHTML += `<option value="${m.id}">${m.nombre} (${m.nombre_modulo || 'sin línea'})</option>`);
  if (val) select.value = val;
}

function toggleRolEmpleado() {
  const rol = document.getElementById('input-emp-rol').value;
  const esSup = rol === 'Supervisor';
  document.getElementById('form-emp-maquina').style.display = esSup ? 'none' : 'block';
}

function limpiarFormEmpleado() {
  idEmpleadoEnEdicion = null;
  document.getElementById('empleado-id-edicion').value = '';
  document.getElementById('input-emp-nombre').value = '';
  document.getElementById('input-emp-doc').value = '';
  document.getElementById('input-emp-cargo').value = '';
  document.getElementById('input-emp-rol').value = 'Operador';
  document.getElementById('input-emp-maquina').value = '';
  document.getElementById('input-emp-fecha').value = '';
  document.getElementById('input-emp-estado').value = 'Activo';
  document.getElementById('input-emp-tel').value = '';
  document.getElementById('input-emp-email').value = '';
  toggleRolEmpleado();
  const btn = document.getElementById('btn-empleado');
  btn.textContent = 'Guardar Empleado';
  btn.style.background = '';
}

async function procesarEmpleado() {
  const nombre = document.getElementById('input-emp-nombre').value.trim();
  const numero_documento = document.getElementById('input-emp-doc').value.trim();
  const cargo = document.getElementById('input-emp-cargo').value.trim();
  const rol = document.getElementById('input-emp-rol').value;
  const fecha_ingreso = document.getElementById('input-emp-fecha').value;
  const estado = document.getElementById('input-emp-estado').value;
  const telefono = document.getElementById('input-emp-tel').value.trim();
  const email = document.getElementById('input-emp-email').value.trim();
  const id_maquina = document.getElementById('input-emp-maquina').value;

  let valid = true;
  if (!nombre) { showFieldError('input-emp-nombre', 'Campo requerido'); valid = false; }
  else { clearFieldErrors('input-emp-nombre'); }

  if (!numero_documento) { showFieldError('input-emp-doc', 'Campo requerido'); valid = false; }
  else { clearFieldErrors('input-emp-doc'); }

  if (!cargo) { showFieldError('input-emp-cargo', 'Ingrese un cargo'); valid = false; }
  else { clearFieldErrors('input-emp-cargo'); }

  if (rol === 'Operador' && !id_maquina) {
    showFieldError('input-emp-maquina', 'Un operador debe tener máquina'); valid = false;
  } else { clearFieldErrors('input-emp-maquina'); }

  if (!valid) return;

  const payload = {
    nombre,
    numero_documento,
    cargo,
    rol,
    fecha_ingreso: fecha_ingreso || null,
    estado,
    telefono: telefono || null,
    email: email || null,
    id_maquina: rol === 'Operador' && id_maquina ? parseInt(id_maquina) : null
  };

  let url = '/api/empleados';
  let method = 'POST';
  if (idEmpleadoEnEdicion) {
    url = `/api/empleados/${idEmpleadoEnEdicion}`;
    method = 'PUT';
  }

  const data = await api(url, {
    method,
    body: JSON.stringify(payload),
    _btn: event.target
  });

  if (data) {
    Toast.success(data.mensaje || 'Empleado guardado');
    limpiarFormEmpleado();
    cargarEmpleados();
    cargarUsuarios();
    cargarSelectUsuarioEmpleado();
  }
}

function iniciarEdicionEmpleado(e) {
  idEmpleadoEnEdicion = e.id;
  abrirFormColapsable('form-nuevo-empleado', 'btn-nuevo-empleado');
  document.getElementById('empleado-id-edicion').value = e.id;
  document.getElementById('input-emp-nombre').value = e.nombre;
  document.getElementById('input-emp-doc').value = e.numero_documento;
  document.getElementById('input-emp-cargo').value = e.cargo;
  document.getElementById('input-emp-rol').value = (e.rol || 'Operador') === 'Supervisor' ? 'Supervisor' : 'Operador';
  document.getElementById('input-emp-maquina').value = e.id_maquina || '';
  document.getElementById('input-emp-fecha').value = e.fecha_ingreso || '';
  document.getElementById('input-emp-estado').value = e.estado || 'Activo';
  document.getElementById('input-emp-tel').value = e.telefono || '';
  document.getElementById('input-emp-email').value = e.email || '';

  toggleRolEmpleado();

  const btn = document.getElementById('btn-empleado');
  btn.textContent = 'Actualizar Empleado';
  btn.style.background = 'var(--accent-blue)';

  document.getElementById('mod-empleados').scrollIntoView({ behavior: 'smooth' });
}

async function eliminarEmpleado(id) {
  const ok = await Modal.confirm('Eliminar Empleado', '¿Estás seguro de eliminar este empleado? Esta acción no se puede deshacer.');
  if (!ok) return;

  const data = await api(`/api/empleados/${id}`, { method: 'DELETE' });
  if (data) {
    Toast.success('Empleado eliminado');
    cargarEmpleados();
  }
}

// ============================================================
// USUARIOS Y ACCESOS
// ============================================================

let idUsuarioEnEdicion = null;

function toggleFormNuevoUsuario() {
  const form = document.getElementById('form-nuevo-usuario');
  const btn = document.getElementById('btn-nuevo-usuario');
  if (form.style.display === 'none') {
    form.style.display = 'block';
    btn.textContent = '− Cerrar';
  } else {
    form.style.display = 'none';
    btn.textContent = '+ Nuevo Usuario';
    limpiarFormUsuario();
  }
}

async function cargarSelectUsuarioEmpleado() {
  const emp = await api('/api/empleados');
  if (!emp) return;
  const select = document.getElementById('input-usuario-empleado');
  select.innerHTML = '<option value="">Seleccione empleado...</option>';
  emp.forEach(e => {
    select.innerHTML += `<option value="${e.id}">${e.nombre} (${e.numero_documento})</option>`;
  });
}

async function cargarUsuarios() {
  const data = await api('/api/usuarios');
  if (!data) return;

  const tbody = document.getElementById('lista-usuarios');
  const empty = document.getElementById('empty-usuarios');
  tbody.innerHTML = '';
  if (data.length === 0) {
    empty.style.display = 'block';
  } else {
    empty.style.display = 'none';
    data.forEach(u => {
      const objStr = JSON.stringify(u).replace(/'/g, "\\'").replace(/"/g, '&quot;');
      const rolClass = u.rol === 'Administrador' ? 'badge-module' : (u.rol === 'Supervisor' ? 'badge-hour' : 'badge-machine');
      tbody.innerHTML += `
        <tr>
          <td><strong>${u.nombre_usuario}</strong></td>
          <td><span class="badge ${rolClass}">${u.rol}</span></td>
          <td>${u.nombre_empleado || '-'}</td>
          <td class="action-buttons">
            <button class="btn-icon btn-edit" onclick="iniciarEdicionUsuario(${objStr})">Editar</button>
            <button class="btn-icon btn-delete" onclick="eliminarUsuarioData(${u.id})">Eliminar</button>
          </td>
        </tr>
      `;
    });
  }
}

function limpiarFormUsuario() {
  idUsuarioEnEdicion = null;
  document.getElementById('usuario-id-edicion').value = '';
  document.getElementById('input-usuario-nombre').value = '';
  document.getElementById('input-usuario-pass').value = '';
  document.getElementById('input-usuario-rol').value = 'Supervisor';
  document.getElementById('input-usuario-empleado').value = '';
  const chkList = document.getElementById('usuario-modulos-supervisor');
  if (chkList) chkList.querySelectorAll('input').forEach(i => i.checked = false);
  toggleRolUsuario();
  const btn = document.getElementById('btn-usuario');
  if (btn) { btn.textContent = 'Crear Usuario'; btn.style.background = ''; }
}

async function cargarUsuarioModulosSupervisor() {
  const mods = await api('/api/modulos');
  if (!mods) return;
  const cont = document.getElementById('usuario-modulos-supervisor');
  if (!cont) return;
  cont.innerHTML = '';
  mods.forEach(m => {
    cont.innerHTML += `
      <label class="linea-check">
        <input type="checkbox" value="${m.id}"> ${m.nombre}
      </label>`;
  });
}

function leerModulosUsuario() {
  return Array.from(document.querySelectorAll('#usuario-modulos-supervisor input:checked')).map(i => parseInt(i.value));
}

function toggleRolUsuario() {
  const rol = document.getElementById('input-usuario-rol').value;
  const cont = document.getElementById('form-usuario-modulos-sup');
  if (cont) cont.style.display = (rol === 'Supervisor') ? 'block' : 'none';
  if (rol !== 'Supervisor') {
    const chkList = document.getElementById('usuario-modulos-supervisor');
    if (chkList) chkList.querySelectorAll('input').forEach(i => i.checked = false);
  }
}

async function sincronizarLineasUsuario(idUsuario, rol) {
  // Las líneas se gestionan acá (en el módulo Usuarios), según el rol de la cuenta:
  //   - Supervisor → las líneas que marcó (AsignacionUsuarioLinea)
  //   - Operador/Admin → no se escriben; el operador deduce su línea de la máquina
  //     del empleado (fallback en el backend) y el admin ve toda la planta.
  if (rol !== 'Supervisor') return;
  const modulos = leerModulosUsuario();
  if (modulos.length === 0) return;
  await api(`/api/usuarios/${idUsuario}/lineas`, {
    method: 'POST',
    body: JSON.stringify({ id_modulos: modulos })
  });
}

async function procesarUsuario() {
  const nombre = document.getElementById('input-usuario-nombre').value.trim();
  const password = document.getElementById('input-usuario-pass').value;
  const rol = document.getElementById('input-usuario-rol').value;
  const idEmpleado = document.getElementById('input-usuario-empleado').value;

  let valid = true;
  if (!nombre) { showFieldError('input-usuario-nombre', 'Requerido'); valid = false; }
  else clearFieldErrors('input-usuario-nombre');
  if (!password) { showFieldError('input-usuario-pass', 'Requerido'); valid = false; }
  else clearFieldErrors('input-usuario-pass');
  if (!idEmpleado) { showFieldError('input-usuario-empleado', 'Seleccione empleado'); valid = false; }
  else clearFieldErrors('input-usuario-empleado');
  if (rol === 'Supervisor' && leerModulosUsuario().length === 0) {
    Toast.warning('Un supervisor debe marcar al menos una línea a supervisar');
    valid = false;
  }
  if (!valid) return;

  const payload = { nombre_usuario: nombre, password, rol, id_empleado: parseInt(idEmpleado) };

  let url = '/api/usuarios';
  let method = 'POST';
  if (idUsuarioEnEdicion) {
    url = `/api/usuarios/${idUsuarioEnEdicion}`;
    method = 'PUT';
  }

  const data = await api(url, { method, body: JSON.stringify(payload), _btn: event.target });
  if (data) {
    const nuevoId = data.id || idUsuarioEnEdicion;
    if (nuevoId) await sincronizarLineasUsuario(nuevoId, rol);
    Toast.success(data.mensaje || 'Usuario guardado');
    limpiarFormUsuario();
    cargarUsuarios();
  }
}

async function iniciarEdicionUsuario(u) {
  idUsuarioEnEdicion = u.id;
  // Abrir el formulario si está cerrado para que la edición sea visible
  const form = document.getElementById('form-nuevo-usuario');
  if (form && form.style.display !== 'block') {
    form.style.display = 'block';
    const btnNuevo = document.getElementById('btn-nuevo-usuario');
    if (btnNuevo) btnNuevo.textContent = '− Cerrar';
  }
  document.getElementById('usuario-id-edicion').value = u.id;
  document.getElementById('input-usuario-nombre').value = u.nombre_usuario;
  document.getElementById('input-usuario-pass').value = 'cambiar';
  document.getElementById('input-usuario-rol').value = u.rol;
  document.getElementById('input-usuario-empleado').value = u.id_empleado || '';
  toggleRolUsuario();

  // Precargar líneas del supervisor desde su asignación
  const acc = document.getElementById('form-usuario-modulos-sup');
  if (acc) acc.style.display = (u.rol === 'Supervisor') ? 'block' : 'none';
  if (u.rol === 'Supervisor') {
    // Si el contenedor de líneas quedó vacío (falló la carga inicial al abrir
    // la página), recargarlo antes de marcar los checks de este supervisor.
    const chkList = document.getElementById('usuario-modulos-supervisor');
    if (chkList && chkList.querySelectorAll('input').length === 0) {
      await cargarUsuarioModulosSupervisor();
    }
    const lineas = await api(`/api/usuarios/${u.id}/lineas`);
    if (chkList) chkList.querySelectorAll('input').forEach(i => {
      i.checked = Array.isArray(lineas) && lineas.includes(parseInt(i.value));
    });
  }

  const btn = document.getElementById('btn-usuario');
  btn.textContent = 'Actualizar Usuario';
  btn.style.background = 'var(--accent-blue)';
}

async function eliminarUsuarioData(id) {
  const ok = await Modal.confirm('Eliminar Usuario', '¿Eliminar este usuario?');
  if (!ok) return;
  const data = await api(`/api/usuarios/${id}`, { method: 'DELETE' });
  if (data) {
    Toast.success('Usuario eliminado');
    cargarUsuarios();
  }
}

async function cargarCausas() {
  const data = await api('/api/causas-parada');
  if (!data) return;
  const tbody = document.getElementById('lista-causas');
  tbody.innerHTML = '';
  data.forEach(c => {
    tbody.innerHTML += `
      <tr>
        <td>${c.id}</td>
        <td>${c.nombre}</td>
        <td><button class="btn-icon btn-delete" onclick="eliminarCausaData(${c.id})">✕</button></td>
      </tr>`;
  });
}

async function guardarCausa() {
  const input = document.getElementById('input-causa-nombre');
  const nombre = input.value.trim();
  if (!nombre) { Toast.warning('Ingrese una causa'); return; }
  const data = await api('/api/causas-parada', {
    method: 'POST',
    body: JSON.stringify({ nombre })
  });
  if (data) {
    input.value = '';
    Toast.success('Causa guardada');
    cargarCausas();
  }
}

async function eliminarCausaData(id) {
  const ok = await Modal.confirm('Eliminar Causa', '¿Eliminar esta causa?');
  if (!ok) return;
  const data = await api(`/api/causas-parada/${id}`, { method: 'DELETE' });
  if (data) {
    Toast.success('Causa eliminada');
    cargarCausas();
  }
}

// ============================================================
// OPERACIONES
// ============================================================

let idOperacionEnEdicion = null;

async function cargarOperaciones() {
  const datos = await api('/api/operaciones');
  if (!datos) return;

  const tbody = document.getElementById('lista-operaciones');
  const empty = document.getElementById('empty-operaciones');

  tbody.innerHTML = '';
  if (datos.length === 0) {
    empty.style.display = 'block';
  } else {
    empty.style.display = 'none';
    datos.forEach(o => {
      const objStr = JSON.stringify(o).replace(/'/g, "\\'").replace(/"/g, '&quot;');
      tbody.innerHTML += `
        <tr>
          <td>${o.nombre}</td>
          <td><span class="badge badge-machine">${o.maquina}</span></td>
          <td>${o.seccion}</td>
          <td class="text-accent">${formatTime(o.tiempo)}</td>
          <td class="action-buttons">
            <button class="btn-icon btn-edit" onclick="iniciarEdicionOperacion(${objStr})">Editar</button>
            <button class="btn-icon btn-delete" onclick="eliminarOperacion(${o.id})">Eliminar</button>
          </td>
        </tr>
      `;
    });
  }
}

function iniciarEdicionOperacion(operacion) {
  idOperacionEnEdicion = operacion.id;
  abrirFormColapsable('form-nueva-operacion', 'btn-nueva-operacion');
  document.getElementById('op-nombre').value = operacion.nombre;
  document.getElementById('op-tiempo').value = operacion.tiempo;
  document.getElementById('op-maquina').value = operacion.id_maquina;
  document.getElementById('op-seccion').value = operacion.id_seccion;

  const btn = document.getElementById('btn-operacion');
  btn.textContent = 'Actualizar Operación';
  btn.style.background = 'var(--accent-blue)';

  const mod = document.getElementById('mod-operaciones');
  if (mod) mod.scrollIntoView({ behavior: 'smooth' });
}

async function procesarOperacion() {
  const nombre = document.getElementById('op-nombre').value.trim();
  const tiempo = document.getElementById('op-tiempo').value;
  const id_maquina = document.getElementById('op-maquina').value;
  const id_seccion = document.getElementById('op-seccion').value;

  let valid = true;
  if (!nombre) { showFieldError('op-nombre', 'Campo requerido'); valid = false; }
  else { clearFieldErrors('op-nombre'); }

  if (!tiempo || isNaN(tiempo) || Number(tiempo) <= 0) { showFieldError('op-tiempo', 'Ingrese un tiempo válido'); valid = false; }
  else { clearFieldErrors('op-tiempo'); }

  if (!id_maquina) { showFieldError('op-maquina', 'Seleccione una máquina'); valid = false; }
  else { clearFieldErrors('op-maquina'); }

  if (!id_seccion) { showFieldError('op-seccion', 'Seleccione una sección'); valid = false; }
  else { clearFieldErrors('op-seccion'); }

  if (!valid) return;

  const payload = { nombre, tiempo: parseInt(tiempo), id_maquina: parseInt(id_maquina), id_seccion: parseInt(id_seccion) };

  let url = '/api/operaciones';
  let method = 'POST';
  if (idOperacionEnEdicion) {
    url = `/api/operaciones/${idOperacionEnEdicion}`;
    method = 'PUT';
  }

  const data = await api(url, {
    method,
    body: JSON.stringify(payload),
    _btn: event.target
  });

  if (data) {
    document.getElementById('op-nombre').value = '';
    document.getElementById('op-tiempo').value = '';
    document.getElementById('op-maquina').value = '';
    document.getElementById('op-seccion').value = '';

    idOperacionEnEdicion = null;
    const btn = document.getElementById('btn-operacion');
    btn.textContent = 'Guardar Operación';
    btn.style.background = 'var(--accent-success)';

    Toast.success(data.mensaje || 'Operación guardada');
    cargarOperaciones();
  }
}

async function eliminarOperacion(id) {
  const ok = await Modal.confirm('Eliminar Operación', '¿Estás seguro de eliminar esta operación? Esta acción no se puede deshacer.');
  if (!ok) return;

  const data = await api(`/api/operaciones/${id}`, { method: 'DELETE' });
  if (data) {
    Toast.success('Operación eliminada');
    cargarOperaciones();
  }
}

function toggleListaOperaciones() {
  togglePanel('container-lista-ops', 'btn-toggle-ops', 'Ver listado de operaciones', 'Ocultar listado de operaciones');
}

function toggleCatalogo(containerId, btnId) {
  togglePanel(containerId, btnId, 'Ver Listado', 'Ocultar Listado');
}

// ============================================================
// INGENIERÍA (REFERENCIAS)
// ============================================================

let referenciaActivaId = null;
let idReferenciaEnEdicion = null;
let secuenciaActualLength = 0;
let referenciasCache = [];

function renderListaReferencias(data) {
  const container = document.getElementById('lista-referencias');
  container.innerHTML = '';

  const filtro = (document.getElementById('input-buscar-ref').value || '').toLowerCase().trim();
  const filtradas = filtro ? data.filter(ref => ref.nombre.toLowerCase().includes(filtro)) : data;

  const emptyFilter = document.getElementById('empty-referencias-filtro');
  if (emptyFilter) emptyFilter.style.display = (filtro && filtradas.length === 0) ? 'block' : 'none';

  filtradas.forEach(ref => {
    const item = document.createElement('div');
    item.className = 'reference-item';

    const badges = [];
    if (ref.foto) badges.push('<span class="badge badge-module" title="Tiene foto">📷</span>');
    if (ref.especificaciones) badges.push('<span class="badge badge-hour" title="Tiene especificaciones">📝</span>');
    item.innerHTML = `
      <div style="display:flex; flex-direction:column; flex:1; min-width:0;">
        <span style="font-weight:600;">${ref.nombre}</span>
        <span style="display:flex; gap:4px; margin-top:4px;">${badges.join('') || ''}</span>
      </div>
      <div style="display:flex; gap:5px; align-items:center; flex-wrap:wrap; justify-content:flex-end;">
        <button class="btn-action-ref" title="Ver detalle y editar diagrama/materiales" onclick="verDetalleReferencia(${ref.id}, '${ref.nombre.replace(/'/g, "\\\\'")}')">👁 Ver detalle</button>
        <button class="btn-action-ref btn-action-edit" onclick="abrirModalEditarReferencia(${ref.id})">✎ Editar</button>
        <button class="btn-action-ref btn-action-delete" onclick="eliminarReferencia(${ref.id})">✕ Eliminar</button>
      </div>
    `;
    container.appendChild(item);
  });
}

function filtrarReferencias() {
  renderListaReferencias(referenciasCache);
}

async function cargarReferencias() {
  const data = await api('/api/referencias');
  if (!data) return;

  referenciasCache = data;
  renderListaReferencias(data);

  const selectSim = document.getElementById('sim-referencia');
  const currentSim = selectSim.value;
  selectSim.innerHTML = '<option value="">Seleccione...</option>';
  data.forEach(ref => {
    selectSim.innerHTML += `<option value="${ref.id}">${ref.nombre}</option>`;
  });
  if (currentSim) selectSim.value = currentSim;
}

async function crearReferencia() {
  const nombre = document.getElementById('cm-ref-nombre').value.trim();
  const especificaciones = document.getElementById('cm-ref-espec').value.trim();

  if (!nombre) { showFieldError('cm-ref-nombre', 'Ingrese un nombre'); return; }
  clearFieldErrors('cm-ref-nombre');

  let url = '/api/referencias';
  let method = 'POST';
  let idRef = null;

  if (idReferenciaEnEdicion) {
    url = `/api/referencias/${idReferenciaEnEdicion}`;
    method = 'PUT';
    idRef = idReferenciaEnEdicion;
  }

  const payload = { nombre, especificaciones: especificaciones || null };

  const data = await api(url, {
    method,
    body: JSON.stringify(payload),
    _btn: document.getElementById('cm-ref-guardar')
  });

  if (data) {
    if (data.id) idRef = data.id;

    // Subir la foto si eligió archivo
    const inputFoto = document.getElementById('cm-ref-foto');
    if (inputFoto && inputFoto.files && inputFoto.files[0] && idRef) {
      await subirFotoReferencia(idRef, inputFoto.files[0]);
    }

    ContentModal.cerrar();
    Toast.success(data.mensaje || 'Referencia guardada');
    cargarReferencias();
    cargarSelectOrdenesRef();
  }
}

function abrirModalNuevaReferencia() {
  idReferenciaEnEdicion = null;
  const body = `
    <div class="form-group">
      <label>Nombre de Referencia *</label>
      <input type="text" id="cm-ref-nombre" placeholder="Ej: Gorra Snapback">
    </div>
    <div class="form-group">
      <label>Especificaciones Técnicas</label>
      <textarea id="cm-ref-espec" rows="3" placeholder="Descripción técnica, materiales, tallas..."></textarea>
    </div>
    <div class="form-group">
      <label>Foto del Prototipo</label>
      <div class="foto-upload">
        <input type="file" id="cm-ref-foto" accept="image/*" onchange="previewFotoNueva(this)">
        <img id="cm-ref-preview" style="display:none;" alt="Vista previa">
      </div>
    </div>
    <div class="content-modal-actions">
      <button class="btn-secondary" onclick="ContentModal.cerrar()">Cancelar</button>
      <button class="btn-primary" id="cm-ref-guardar" onclick="crearReferencia()">Crear Referencia</button>
    </div>
  `;
  ContentModal.abrir({ title: 'Nueva Referencia', body });
}

async function abrirModalEditarReferencia(id) {
  const data = await api('/api/referencias');
  if (!data) return;
  const ref = data.find(r => r.id === id);
  if (!ref) return;

  idReferenciaEnEdicion = ref.id;
  const body = `
    <div class="form-group">
      <label>Nombre de Referencia *</label>
      <input type="text" id="cm-ref-nombre" value="${(ref.nombre || '').replace(/"/g, '&quot;')}">
    </div>
    <div class="form-group">
      <label>Especificaciones Técnicas</label>
      <textarea id="cm-ref-espec" rows="3">${(ref.especificaciones || '').replace(/</g, '&lt;')}</textarea>
    </div>
    <div class="form-group">
      <label>Foto del Prototipo</label>
      <div class="foto-upload">
        <input type="file" id="cm-ref-foto" accept="image/*" onchange="previewFotoNueva(this)">
        <img id="cm-ref-preview" src="${ref.foto || ''}" style="${ref.foto ? 'display:block;' : 'display:none;'}" alt="Vista previa">
        ${ref.foto ? '<span style="font-size:0.85rem; color:var(--text-muted); margin-top:6px; display:block;">Foto actual subida. Elegí un archivo solo si querés cambiarla.</span>' : ''}
      </div>
    </div>
    <div class="content-modal-actions">
      <button class="btn-secondary" onclick="ContentModal.cerrar()">Cancelar</button>
      <button class="btn-primary" id="cm-ref-guardar" onclick="crearReferencia()">Actualizar Referencia</button>
    </div>
  `;
  ContentModal.abrir({ title: 'Editar Referencia', body });
}

async function subirFotoReferencia(idRef, archivo) {
  const formData = new FormData();
  formData.append('foto', archivo);
  try {
    const res = await fetch(`/api/referencias/${idRef}/foto`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (res.ok) {
      Toast.success('Foto del prototipo subida');
      cargarReferencias();
    }
  } catch (e) {
    Toast.error('Error al subir la foto');
  }
}
async function eliminarReferencia(id) {
  const ok = await Modal.confirm('Eliminar Referencia', '¿Eliminar esta referencia y toda su secuencia de operaciones?\n\nNota: no podrás eliminarla si tiene órdenes de producción asociadas.');
  if (!ok) return;

  const data = await api(`/api/referencias/${id}`, { method: 'DELETE' });
  if (data) {
    if (referenciaActivaId === id) {
      ContentModal.cerrar();
    }
    Toast.success('Referencia eliminada');
    cargarReferencias();
  }
}

const ContentModal = {
  overlay: null,
  activo: false,

  abrir({ title, body }) {
    this.overlay = document.getElementById('content-modal-overlay');
    if (!this.overlay) return;
    const titulo = document.getElementById('content-modal-title');
    const status = document.getElementById('content-modal-body');
    if (titulo) titulo.textContent = title || '';
    if (status) status.innerHTML = body || '';
    this.overlay.classList.add('content-modal-visible');
    this.activo = true;

    const close = this.overlay.querySelector('#content-modal-close');
    if (close) close.onclick = () => this.cerrar();
  },

  cerrar() {
    if (!this.overlay) this.overlay = document.getElementById('content-modal-overlay');
    if (this.overlay) this.overlay.classList.remove('content-modal-visible');
    this.activo = false;
    referenciaActivaId = null;
  }
};

function previewFotoNueva(input) {
  const preview = document.getElementById('cm-ref-preview');
  if (!preview) return;
  if (input.files && input.files[0]) {
    preview.src = URL.createObjectURL(input.files[0]);
    preview.style.display = 'block';
  } else {
    preview.style.display = 'none';
    preview.src = '';
  }
}

async function verDetalleReferencia(id, nombre) {
  const data = await api('/api/referencias');
  if (!data) return;
  const ref = data.find(r => r.id === id);
  if (!ref) return;

  referenciaActivaId = id;

  const fotoHtml = ref.foto
    ? `<img src="${ref.foto}" alt="Foto prototipo">`
    : `<span style="color:var(--text-muted); font-size:0.85rem;">Sin foto</span>`;

  const body = `
    <div class="content-modal-ficha">
      <div class="content-modal-ficha-foto">${fotoHtml}</div>
      <div class="content-modal-ficha-info">
        <div class="content-modal-ficha-titulo">Especificaciones Técnicas</div>
        <div class="content-modal-ficha-texto">${(ref.especificaciones || 'Sin especificaciones.').replace(/</g, '&lt;')}</div>
      </div>
    </div>

    <div class="content-modal-tabs">
      <button class="content-modal-tab active" id="cm-tab-secuencia" onclick="cambiarTabDetalle('secuencia')">🛠 Diagrama de Actividades</button>
      <button class="content-modal-tab" id="cm-tab-bom" onclick="cambiarTabDetalle('bom')">🧵 Materiales</button>
    </div>

    <div id="cm-panel-secuencia">
      <div class="form-group" style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 12px; align-items: end;">
        <div>
          <label>Operación</label>
          <select id="cm-seq-operacion"></select>
        </div>
        <div>
          <label>Letra</label>
          <input type="text" id="cm-seq-letra" placeholder="A, B...">
        </div>
        <div>
          <label>Predec.</label>
          <input type="text" id="cm-seq-pred" placeholder="N/A o A,C">
        </div>
        <div>
          <button class="btn-primary" onclick="agregarDetalle()">Agregar</button>
        </div>
      </div>
      <div class="data-table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Orden</th>
              <th>Letra</th>
              <th>Operación</th>
              <th>Máquina</th>
              <th>Tiempo</th>
              <th>Pred.</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody id="cm-lista-secuencia"></tbody>
        </table>
        <div id="cm-empty-secuencia" class="empty-state" style="display: none;">Esta referencia no tiene operaciones asignadas.</div>
      </div>
    </div>

    <div id="cm-panel-bom" style="display: none;">
      <div class="form-group" style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 8px; align-items: end;">
        <div>
          <label>Material</label>
          <select id="cm-bom-material"></select>
        </div>
        <div>
          <label>Cant./unidad</label>
          <input type="number" id="cm-bom-cantidad" placeholder="0.35" step="0.01">
        </div>
        <div>
          <label>Merma %</label>
          <input type="number" id="cm-bom-merma" placeholder="5" step="0.01">
        </div>
        <div>
          <button class="btn-primary" onclick="agregarMaterialReferencia()">Agregar</button>
        </div>
      </div>
      <div class="data-table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Material</th>
              <th>Unidad</th>
              <th>Cant./unidad</th>
              <th>Merma</th>
              <th>Nota</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody id="cm-lista-bom"></tbody>
        </table>
        <div id="cm-empty-bom" class="empty-state" style="display: none;">Esta referencia no tiene materiales asociados.</div>
      </div>
    </div>
  `;

  ContentModal.abrir({ title: `Detalle: ${nombre}`, body });
  cargarOperacionesSelectModal();
  await cargarDetallesReferencia(id);
  cargarMaterialesSelectModal();
  cargarMaterialesReferencia(id);
}

function cambiarTabDetalle(tab) {
  const esBom = tab === 'bom';
  const tabSec = document.getElementById('cm-tab-secuencia');
  const tabBom = document.getElementById('cm-tab-bom');
  const panelSec = document.getElementById('cm-panel-secuencia');
  const panelBom = document.getElementById('cm-panel-bom');
  if (!tabSec || !tabBom) return;
  tabSec.classList.toggle('active', !esBom);
  tabBom.classList.toggle('active', esBom);
  if (panelSec) panelSec.style.display = esBom ? 'none' : 'block';
  if (panelBom) panelBom.style.display = esBom ? 'block' : 'none';
  if (esBom) cargarMaterialesReferencia(referenciaActivaId);
}

async function cargarDetallesReferencia(idRef) {
  const data = await api(`/api/referencias/${idRef}/detalles`);
  if (!data) return;

  const tbody = document.getElementById('cm-lista-secuencia');
  if (!tbody) return;
  tbody.innerHTML = '';
  secuenciaActualLength = data.length;

  const empty = document.getElementById('cm-empty-secuencia');
  if (empty) empty.style.display = data.length === 0 ? 'block' : 'none';

  const nextChar = String.fromCharCode(65 + secuenciaActualLength);
  const letraInput = document.getElementById('cm-seq-letra');
  const predInput = document.getElementById('cm-seq-pred');
  if (letraInput) letraInput.value = nextChar;
  if (predInput) predInput.value = secuenciaActualLength > 0 ? data[data.length - 1].letra : 'N/A';

  data.forEach((d, index) => {
    tbody.innerHTML += `
      <tr>
        <td style="color:var(--text-muted);">${index + 1}</td>
        <td><span class="sequence-badge">${d.letra}</span></td>
        <td>${d.nombre_operacion}</td>
        <td><span class="badge badge-machine">${d.maquina}</span></td>
        <td>${formatTime(d.tiempo)}</td>
        <td>${d.predecesoras}</td>
        <td><button class="btn-icon btn-delete" onclick="eliminarDetalle(${d.id})">✕</button></td>
      </tr>
    `;
  });
}

async function cargarOperacionesSelectModal() {
  const data = await api('/api/operaciones');
  if (!data) return;

  const select = document.getElementById('cm-seq-operacion');
  if (!select) return;
  select.innerHTML = '';
  data.forEach(o => {
    select.innerHTML += `<option value="${o.id}">${o.nombre} (${formatTime(o.tiempo)})</option>`;
  });
}

async function agregarDetalle() {
  if (!referenciaActivaId) return;

  const id_operacion = document.getElementById('cm-seq-operacion').value;
  const letra = document.getElementById('cm-seq-letra').value.toUpperCase();
  const predecesoras = document.getElementById('cm-seq-pred').value.toUpperCase();

  if (!letra) { Toast.warning('Falta la letra de secuencia'); return; }

  const data = await api(`/api/referencias/${referenciaActivaId}/detalles`, {
    method: 'POST',
    body: JSON.stringify({
      id_operacion: parseInt(id_operacion),
      letra,
      predecesoras,
      orden: secuenciaActualLength + 1
    }),
    _btn: document.getElementById('cm-panel-secuencia') ? event.target : null
  });

  if (data) {
    Toast.success('Operación agregada a la secuencia');
    cargarDetallesReferencia(referenciaActivaId);
  }
}

async function eliminarDetalle(id) {
  const ok = await Modal.confirm('Quitar Operación', '¿Quitar esta operación de la secuencia?');
  if (!ok) return;

  const data = await api(`/api/detalles/${id}`, { method: 'DELETE' });
  if (data) {
    Toast.success('Operación quitada');
    cargarDetallesReferencia(referenciaActivaId);
  }
}

async function cargarMaterialesSelectModal() {
  const data = await api('/api/materiales');
  if (!data) return;

  const select = document.getElementById('cm-bom-material');
  if (!select) return;
  select.innerHTML = '<option value="">Seleccione material...</option>';
  data.forEach(m => {
    select.innerHTML += `<option value="${m.id}">${m.nombre}</option>`;
  });
}

async function cargarMaterialesReferencia(idRef) {
  const data = await api(`/api/referencias/${idRef}/materiales`);
  if (!data) return;

  const tbody = document.getElementById('cm-lista-bom');
  if (!tbody) return;
  tbody.innerHTML = '';
  const empty = document.getElementById('cm-empty-bom');
  if (empty) empty.style.display = data.length === 0 ? 'block' : 'none';

  data.forEach(b => {
    tbody.innerHTML += `
      <tr>
        <td><strong>${b.nombre}</strong></td>
        <td>${b.unidad || '-'}</td>
        <td class="text-accent">${b.cantidad_por_unidad}</td>
        <td>${b.merma_porcentaje}%</td>
        <td>${b.nota || '-'}</td>
        <td><button class="btn-icon btn-delete" onclick="eliminarMaterialReferencia(${b.id})">✕</button></td>
      </tr>
    `;
  });
}

async function agregarMaterialReferencia() {
  if (!referenciaActivaId) return;

  const id_material = document.getElementById('cm-bom-material').value;
  const cantidad = document.getElementById('cm-bom-cantidad').value;
  const merma = document.getElementById('cm-bom-merma').value;

  if (!id_material) { Toast.warning('Seleccione un material'); return; }
  if (!cantidad || isNaN(cantidad) || Number(cantidad) <= 0) { Toast.warning('Cantidad inválida'); return; }

  const data = await api(`/api/referencias/${referenciaActivaId}/materiales`, {
    method: 'POST',
    body: JSON.stringify({
      id_material: parseInt(id_material),
      cantidad_por_unidad: parseFloat(cantidad),
      merma_porcentaje: merma ? parseFloat(merma) : 0
    })
  });

  if (data) {
    Toast.success('Material asociado a la referencia');
    document.getElementById('cm-bom-cantidad').value = '';
    document.getElementById('cm-bom-merma').value = '';
    cargarMaterialesReferencia(referenciaActivaId);
  }
}

async function eliminarMaterialReferencia(id) {
  const ok = await Modal.confirm('Quitar Material', '¿Quitar este material de la referencia?');
  if (!ok) return;
  const data = await api(`/api/materiales-referencia/${id}`, { method: 'DELETE' });
  if (data) {
    Toast.success('Material removido');
    cargarMaterialesReferencia(referenciaActivaId);
  }
}

// ============================================================
// ÓRDENES DE PRODUCCIÓN (LOTES)
// ============================================================

let idOrdenEnEdicion = null;

async function cargarSelectOrdenesRef() {
  const data = await api('/api/referencias');
  if (!data) return;
  const select = document.getElementById('input-orden-ref');
  if (!select) return;
  const val = select.value;
  select.innerHTML = '<option value="">Seleccione referencia...</option>';
  data.forEach(r => {
    select.innerHTML += `<option value="${r.id}">${r.nombre}</option>`;
  });
  if (val) select.value = val;
}

async function cargarOrdenes() {
  const data = await api('/api/ordenes');
  if (!data) return;

  const tbody = document.getElementById('lista-ordenes');
  const empty = document.getElementById('empty-ordenes');
  tbody.innerHTML = '';
  if (data.length === 0) {
    empty.style.display = 'block';
  } else {
    empty.style.display = 'none';
    data.forEach(o => {
      const objStr = JSON.stringify(o).replace(/'/g, "\\'").replace(/"/g, '&quot;');
      const estadoClass = o.estado === 'Abierta' ? 'badge-module' : 'badge-machine';
      const completas = o.gorras_completas || 0;
      const pct = Math.min(100, o.porcentaje_cumplimiento || 0);
      const pctColor = pct >= 100 ? 'var(--eff-super)' : pct >= 80 ? 'var(--accent-success)' : pct >= 50 ? 'var(--eff-warn)' : 'var(--accent-danger)';
      tbody.innerHTML += `
        <tr>
          <td><strong>${o.nombre_orden}</strong></td>
          <td>${o.referencia}</td>
          <td class="text-accent">${o.cantidad_lote}</td>
          <td style="min-width:140px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <div class="progress-bar-container" style="width:90px; margin:0; height:7px;">
                <div class="progress-bar" style="width:${pct}%; background:${pctColor};"></div>
              </div>
              <span style="font-size:0.8rem; font-weight:700; color:${pctColor};">${o.porcentaje_cumplimiento || 0}%</span>
            </div>
            <div style="font-size:0.7rem; color:var(--text-muted);">${completas} completas / ${o.cantidad_lote}</div>
          </td>
          <td><span class="badge ${estadoClass}">${o.estado}</span></td>
          <td class="action-buttons">
            <button class="btn-icon btn-edit" style="background:var(--accent-green);" onclick="verMaterialesOrden(${o.id})" title="Ver materiales calculados">📦</button>
            <button class="btn-icon btn-edit" onclick="iniciarEdicionOrden(${objStr})" title="Editar">✎</button>
            <button class="btn-icon btn-edit" onclick="cambiarEstadoOrden(${o.id}, '${o.estado}')" title="Cambiar estado">⇄</button>
            <button class="btn-icon btn-delete" onclick="eliminarOrden(${o.id})" title="Eliminar">✕</button>
          </td>
        </tr>
      `;
    });
  }
}

function limpiarFormOrden() {
  idOrdenEnEdicion = null;
  document.getElementById('orden-id-edicion').value = '';
  document.getElementById('input-orden-nombre').value = '';
  document.getElementById('input-orden-cantidad').value = '';
  document.getElementById('input-orden-ref').value = '';
  const btn = document.getElementById('btn-orden');
  if (btn) { btn.textContent = 'Crear Orden'; btn.style.background = ''; }
}

async function procesarOrden() {
  const idReferencia = document.getElementById('input-orden-ref').value;
  const nombreOrden = document.getElementById('input-orden-nombre').value.trim();
  const cantidad = document.getElementById('input-orden-cantidad').value;

  let valid = true;
  if (!idReferencia) { showFieldError('input-orden-ref', 'Seleccione referencia'); valid = false; }
  else { clearFieldErrors('input-orden-ref'); }
  if (!nombreOrden) { showFieldError('input-orden-nombre', 'Ingrese nombre'); valid = false; }
  else { clearFieldErrors('input-orden-nombre'); }
  if (!cantidad || isNaN(cantidad) || Number(cantidad) <= 0) { showFieldError('input-orden-cantidad', 'Cantidad inválida'); valid = false; }
  else { clearFieldErrors('input-orden-cantidad'); }
  if (!valid) return;

  let url = '/api/ordenes';
  let method = 'POST';
  if (idOrdenEnEdicion) {
    url = `/api/ordenes/${idOrdenEnEdicion}`;
    method = 'PUT';
  }

  const payload = idOrdenEnEdicion
    ? { cantidad_lote: parseInt(cantidad) }
    : { id_referencia: parseInt(idReferencia), nombre_orden: nombreOrden, cantidad_lote: parseInt(cantidad) };

  const data = await api(url, {
    method,
    body: JSON.stringify(payload),
    _btn: event.target
  });

  if (data) {
    Toast.success(data.mensaje || 'Orden guardada');
    limpiarFormOrden();
    cargarOrdenes();
    cargarDatosProgramacion();
  }
}

function iniciarEdicionOrden(o) {
  idOrdenEnEdicion = o.id;
  abrirFormColapsable('form-nueva-orden', 'btn-nueva-orden');
  document.getElementById('orden-id-edicion').value = o.id;
  document.getElementById('input-orden-nombre').value = o.nombre_orden;
  document.getElementById('input-orden-ref').value = o.id_referencia;
  document.getElementById('input-orden-cantidad').value = o.cantidad_lote;
  const btn = document.getElementById('btn-orden');
  if (btn) { btn.textContent = 'Actualizar Cantidad'; btn.style.background = 'var(--accent-blue)'; }
}

async function cambiarEstadoOrden(id, estadoActual) {
  const nuevo = estadoActual === 'Abierta' ? 'Cerrada' : 'Abierta';
  const ok = await Modal.confirm('Cambiar Estado', `¿Cambiar la orden a estado "${nuevo}"?`);
  if (!ok) return;

  const data = await api(`/api/ordenes/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ estado: nuevo })
  });
  if (data) {
    Toast.success(`Orden ${nuevo.toLowerCase()}`);
    cargarOrdenes();
    cargarDatosProgramacion();
  }
}

async function eliminarOrden(id) {
  const ok = await Modal.confirm('Eliminar Orden', '¿Eliminar esta orden de producción? Esta acción no se puede deshacer.');
  if (!ok) return;

  const data = await api(`/api/ordenes/${id}`, { method: 'DELETE' });
  if (data) {
    Toast.success('Orden eliminada');
    cargarOrdenes();
    cargarDatosProgramacion();
  }
}

// ============================================================
// MATERIALES (BOM)
// ============================================================

let idMaterialEnEdicion = null;

async function cargarMateriales() {
  const data = await api('/api/materiales');
  if (!data) return;

  const tbody = document.getElementById('lista-materiales');
  const empty = document.getElementById('empty-materiales');

  tbody.innerHTML = '';

  if (data.length === 0) {
    empty.style.display = 'block';
  } else {
    empty.style.display = 'none';
    data.forEach(m => {
      const objStr = JSON.stringify(m).replace(/'/g, "\\'").replace(/"/g, '&quot;');
      tbody.innerHTML += `
        <tr>
          <td><strong>${m.nombre}</strong></td>
          <td>${m.unidad || '-'}</td>
          <td>${m.costo_unitario ? '$' + m.costo_unitario.toLocaleString() : '-'}</td>
          <td>${m.proveedor || '-'}</td>
          <td class="action-buttons">
            <button class="btn-icon btn-edit" onclick="iniciarEdicionMaterial(${objStr})">Editar</button>
            <button class="btn-icon btn-delete" onclick="eliminarMaterial(${m.id})">Eliminar</button>
          </td>
        </tr>
      `;
    });
  }
}

function limpiarFormMaterial() {
  idMaterialEnEdicion = null;
  document.getElementById('material-id-edicion').value = '';
  document.getElementById('input-mat-nombre').value = '';
  document.getElementById('input-mat-unidad').value = '';
  document.getElementById('input-mat-costo').value = '';
  document.getElementById('input-mat-proveedor').value = '';
  document.getElementById('input-mat-desc').value = '';
  const btn = document.getElementById('btn-material');
  if (btn) { btn.textContent = 'Guardar Material'; btn.style.background = ''; }
}

async function procesarMaterial() {
  const nombre = document.getElementById('input-mat-nombre').value.trim();
  if (!nombre) { showFieldError('input-mat-nombre', 'Campo requerido'); return; }
  clearFieldErrors('input-mat-nombre');

  const payload = {
    nombre,
    unidad: document.getElementById('input-mat-unidad').value.trim() || null,
    costo_unitario: document.getElementById('input-mat-costo').value ? parseFloat(document.getElementById('input-mat-costo').value) : null,
    proveedor: document.getElementById('input-mat-proveedor').value.trim() || null,
    descripcion: document.getElementById('input-mat-desc').value.trim() || null
  };

  let url = '/api/materiales';
  let method = 'POST';
  if (idMaterialEnEdicion) {
    url = `/api/materiales/${idMaterialEnEdicion}`;
    method = 'PUT';
  }

  const data = await api(url, { method, body: JSON.stringify(payload), _btn: event.target });
  if (data) {
    Toast.success(data.mensaje || 'Material guardado');
    limpiarFormMaterial();
    cargarMateriales();
  }
}

function iniciarEdicionMaterial(m) {
  idMaterialEnEdicion = m.id;
  abrirFormColapsable('form-nuevo-material', 'btn-nuevo-material');
  document.getElementById('material-id-edicion').value = m.id;
  document.getElementById('input-mat-nombre').value = m.nombre;
  document.getElementById('input-mat-unidad').value = m.unidad || '';
  document.getElementById('input-mat-costo').value = m.costo_unitario || '';
  document.getElementById('input-mat-proveedor').value = m.proveedor || '';
  document.getElementById('input-mat-desc').value = m.descripcion || '';
  const btn = document.getElementById('btn-material');
  if (btn) { btn.textContent = 'Actualizar Material'; btn.style.background = 'var(--accent-blue)'; }
}

async function eliminarMaterial(id) {
  const ok = await Modal.confirm('Eliminar Material', '¿Eliminar este material del catálogo?');
  if (!ok) return;
  const data = await api(`/api/materiales/${id}`, { method: 'DELETE' });
  if (data) {
    Toast.success('Material eliminado');
    cargarMateriales();
  }
}

function cerrarMaterialesOrden() {
  const panel = document.getElementById('orden-materiales-panel');
  if (panel) panel.style.display = 'none';
}

async function verMaterialesOrden(idOrden) {
  const data = await api(`/api/ordenes/${idOrden}/materiales`);
  if (!data) return;

  const panel = document.getElementById('orden-materiales-panel');
  panel.style.display = 'block';
  document.getElementById('orden-materiales-titulo').innerText = `Materiales para ${data.nombre_orden} (lote: ${data.cantidad_lote})`;

  const tbody = document.getElementById('lista-orden-materiales');
  tbody.innerHTML = '';
  data.materiales.forEach(m => {
    tbody.innerHTML += `
      <tr>
        <td><strong>${m.nombre}</strong></td>
        <td>${m.unidad || '-'}</td>
        <td>${m.cantidad_por_unidad}</td>
        <td>${m.merma_porcentaje}%</td>
        <td class="text-accent">${m.cantidad_requerida}</td>
        <td>${m.costo_estimado ? '$' + m.costo_estimado.toLocaleString() : '-'}</td>
      </tr>
    `;
  });

  const total = document.getElementById('orden-materiales-total');
  total.innerText = data.materiales.length
    ? `Costo estimado total: $${data.total_costo_estimado.toLocaleString()}`
    : 'Esta referencia no tiene materiales asociados en su BOM.';

  panel.scrollIntoView({ behavior: 'smooth' });
}

// ============================================================
// PROGRAMACIÓN (ASIGNACIONES)
// ============================================================

let idAsignacionEnEdicion = null;

function toggleFormNuevaAsignacion() {
  const form = document.getElementById('form-nueva-asignacion');
  const btn = document.getElementById('btn-nueva-asignacion');
  if (form.style.display === 'none') {
    form.style.display = 'block';
    btn.textContent = '− Cerrar';
    cargarDatosProgramacion();
  } else {
    form.style.display = 'none';
    btn.textContent = '+ Nueva Asignación';
    cancelarEdicionAsignacion();
  }
}

async function cargarDatosProgramacion() {
  const dataRef = await api('/api/ordenes-disponibles');
  if (!dataRef) return;

  const selRef = document.getElementById('prog-referencia');
  const valActual = selRef.value;
  selRef.innerHTML = '<option value="">Seleccione Orden...</option>';
  dataRef.forEach(o => {
    selRef.innerHTML += `<option value="${o.id}">${o.nombre_orden} (${o.referencia})</option>`;
  });

  const dataMod = await api('/api/modulos');
  if (!dataMod) return;

  // Reconstruir siempre la lista: refleja líneas nuevas/módulos creados posteriormente
  const cont = document.getElementById('prog-lineas-checks');
  if (cont) {
    cont.innerHTML = '';
    dataMod.forEach(m => {
      cont.innerHTML += `
        <div class="prog-linea-fila">
          <input type="checkbox" class="prog-linea-marca" value="${m.id}" onchange="this.closest('.prog-linea-fila').classList.toggle('sel', this.checked)">
          <span class="prog-linea-nombre">${m.nombre}</span>
          <input type="number" class="prog-linea-cantidad" placeholder="Cantidad" min="0">
        </div>`;
    });
  }

  if (valActual) selRef.value = valActual;
  if (selRef.onchange) verificarDisponibilidad();
}

function leerLineasAsignacion() {
  // Devuelve [{id_modulo, cantidad}] solo de líneas marcadas con cantidad > 0
  const res = [];
  document.querySelectorAll('#prog-lineas-checks .prog-linea-fila').forEach(fila => {
    const marca = fila.querySelector('.prog-linea-marca');
    const cant = fila.querySelector('.prog-linea-cantidad');
    if (marca && marca.checked && cant && parseInt(cant.value) > 0) {
      res.push({ id_modulo: parseInt(marca.value), cantidad: parseInt(cant.value) });
    }
  });
  return res;
}

async function verificarDisponibilidad() {
  const idOrden = document.getElementById('prog-referencia').value;
  const label = document.getElementById('prog-disponibilidad');

  if (!idOrden || idOrden === '-1') {
    if (idOrden === '-1') return;
    label.innerText = 'Disponible: - / Total: -';
    return;
  }

  const data = await api(`/api/ordenes/${idOrden}/disponibilidad`);
  if (data) {
    label.innerText = `Disponible: ${data.disponible} / Total: ${data.total}`;
    if (data.disponible <= 0) {
      label.style.color = 'var(--accent-danger)';
    } else {
      label.style.color = 'var(--text-secondary)';
    }
  }
}

async function guardarAsignacion() {
  const idOrden = document.getElementById('prog-referencia').value;
  const lineas = leerLineasAsignacion();

  let valid = true;
  if (!idOrden) { showFieldError('prog-referencia', 'Seleccione una orden'); valid = false; }
  else { clearFieldErrors('prog-referencia'); }

  if (lineas.length === 0) {
    showFieldError('prog-lineas-checks', 'Marque al menos una línea y ponga su cantidad');
    valid = false;
  } else {
    clearFieldErrors('prog-lineas-checks');
  }

  if (!valid) return;

  if (idAsignacionEnEdicion) {
    const data = await api(`/api/asignaciones/${idAsignacionEnEdicion}`, {
      method: 'PUT',
      body: JSON.stringify({ cantidad: lineas[0].cantidad }),
      _btn: event.target
    });
    if (data) {
      Toast.success('Asignación actualizada');
      cancelarEdicionAsignacion();
      verificarDisponibilidad();
      cargarAsignaciones();
      cargarDatosProgramacion();
    }
    return;
  }

  let errores = [];
  let totalAsignado = 0;

  for (const l of lineas) {
    const data = await api('/api/asignaciones', {
      method: 'POST',
      body: JSON.stringify({
        id_orden: parseInt(idOrden),
        id_modulo: l.id_modulo,
        cantidad: l.cantidad
      })
    });
    if (data) {
      totalAsignado += l.cantidad;
    } else {
      errores.push(`Línea ${l.id_modulo}`);
    }
  }

  // Limpiar filas marcadas
  document.querySelectorAll('#prog-lineas-checks .prog-linea-fila').forEach(f => {
    const marca = f.querySelector('.prog-linea-marca');
    const cant = f.querySelector('.prog-linea-cantidad');
    if (marca) marca.checked = false;
    if (cant) cant.value = '';
    f.classList.remove('sel');
  });

  if (errores.length === 0) {
    Toast.success(`Asignado ${totalAsignado} unidades en ${lineas.length} líneas`);
    // Cerrar el formulario para ver las asignaciones a pantalla completa
    const form = document.getElementById('form-nueva-asignacion');
    const btn = document.getElementById('btn-nueva-asignacion');
    if (form) form.style.display = 'none';
    if (btn) btn.textContent = '+ Nueva Asignación';
  } else {
    Toast.error(`Hubo líneas sin asignar: ${errores.join(', ')}`);
  }
  verificarDisponibilidad();
  cargarAsignaciones();
  cargarDatosProgramacion();
}

async function cargarAsignaciones() {
  const data = await api('/api/asignaciones');
  if (!data) return;

  const tbody = document.getElementById('lista-asignaciones');
  const empty = document.getElementById('empty-asignaciones');

  tbody.innerHTML = '';
  if (data.length === 0) {
    empty.style.display = 'block';
  } else {
    empty.style.display = 'none';
    data.forEach(a => {
      const refSafe = a.referencia.replace(/'/g, "\\'").replace(/"/g, '&quot;');
      const ordenSafe = (a.orden || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
      const modSafe = a.modulo.replace(/'/g, "\\'").replace(/"/g, '&quot;');
      tbody.innerHTML += `
        <tr>
          <td><span class="badge badge-hour">${a.orden}</span></td>
          <td>${a.referencia}</td>
          <td><span class="badge badge-module">${a.modulo}</span></td>
          <td class="text-accent">${a.cantidad}</td>
          <td class="action-buttons">
            <button class="btn-icon btn-edit" onclick="iniciarEdicionAsignacion(${a.id}, ${a.cantidad}, ${a.id_orden}, '${ordenSafe}', '${modSafe}')">✎</button>
            <button class="btn-icon btn-delete" onclick="eliminarAsignacion(${a.id})">✕</button>
          </td>
        </tr>
      `;
    });
  }
}

async function eliminarAsignacion(id) {
  const ok = await Modal.confirm('Eliminar Asignación', '¿Eliminar esta asignación de módulo?');
  if (!ok) return;

  const data = await api(`/api/asignaciones/${id}`, { method: 'DELETE' });
  if (data) {
    Toast.success('Asignación eliminada');
    cargarAsignaciones();
    verificarDisponibilidad();
    cargarDatosProgramacion();
    if (idAsignacionEnEdicion === id) cancelarEdicionAsignacion();
  }
}

function iniciarEdicionAsignacion(id, cantidad, idOrden, nombreOrden, nombreMod) {
  idAsignacionEnEdicion = id;
  abrirFormColapsable('form-nueva-asignacion', 'btn-nueva-asignacion');

  const btn = document.getElementById('btn-guardar-asignacion') || document.querySelector('#mod-programacion .btn-primary');
  btn.textContent = 'Actualizar Asignación';
  btn.style.backgroundColor = 'var(--accent-blue)';

  const selRef = document.getElementById('prog-referencia');
  selRef.disabled = true;

  // Habilitar filas y limpiar
  document.querySelectorAll('#prog-lineas-checks .prog-linea-fila').forEach(f => {
    const marca = f.querySelector('.prog-linea-marca');
    const cant = f.querySelector('.prog-linea-cantidad');
    if (marca) marca.disabled = false;
    if (cant) cant.disabled = false;
    f.classList.remove('sel');
  });

  // Marcar la fila del módulo y poner su cantidad
  document.querySelectorAll('#prog-lineas-checks .prog-linea-fila').forEach(f => {
    const nombre = f.querySelector('.prog-linea-nombre').textContent.trim();
    if (nombre === nombreMod) {
      const marca = f.querySelector('.prog-linea-marca');
      const cant = f.querySelector('.prog-linea-cantidad');
      if (marca) { marca.checked = true; f.classList.add('sel'); }
      if (cant) cant.value = cantidad;
    }
  });

  // Seleccionar la orden por id (puede ser un placeholder -1 si ya no está disponible)
  let foundRef = false;
  for (let op of selRef.options) {
    if (op.value === String(idOrden)) { selRef.value = op.value; foundRef = true; break; }
  }
  if (!foundRef) {
    const opt = document.createElement('option');
    opt.text = nombreOrden + ' (Actual)';
    opt.value = '-1';
    opt.selected = true;
    selRef.add(opt);
  }

  if (!document.getElementById('btn-cancel-assign')) {
    const cancelBtn = document.createElement('button');
    cancelBtn.id = 'btn-cancel-assign';
    cancelBtn.textContent = 'Cancelar';
    cancelBtn.className = 'btn-secondary';
    cancelBtn.style.marginTop = '10px';
    cancelBtn.onclick = cancelarEdicionAsignacion;
    btn.parentElement.appendChild(cancelBtn);
  }
}

function cancelarEdicionAsignacion() {
  idAsignacionEnEdicion = null;
  document.getElementById('prog-referencia').disabled = false;
  document.querySelectorAll('#prog-lineas-checks .prog-linea-fila').forEach(f => {
    const marca = f.querySelector('.prog-linea-marca');
    const cant = f.querySelector('.prog-linea-cantidad');
    if (marca) marca.disabled = false;
    if (cant) { cant.disabled = false; cant.value = ''; }
    f.classList.remove('sel');
  });

  const btn = document.getElementById('btn-guardar-asignacion') || document.querySelector('#mod-programacion .btn-primary');
  btn.textContent = 'Asignar';
  btn.style.backgroundColor = '';

  const cancelBtn = document.getElementById('btn-cancel-assign');
  if (cancelBtn) cancelBtn.remove();

  cargarDatosProgramacion();
  document.getElementById('prog-disponibilidad').innerText = 'Disponible: - / Total: -';
}

// ============================================================
// CONTROL HORA A HORA
// ============================================================

let catalogoParadasCache = [
  { id: 1, nombre: 'Desayuno', tiempo: 900 },
  { id: 2, nombre: 'Almuerzo', tiempo: 1800 },
  { id: 3, nombre: 'Ninguna', tiempo: 0 }
];

let causasParadaCache = [];

function aplicarModalidadRegistro() {
  const porHora = (window.modalidadRegistro || 'Diario') === 'Por Hora';
  const grupo = document.getElementById('grupo-ctrl-hora');
  const selHora = document.getElementById('ctrl-hora');
  if (grupo) grupo.style.display = porHora ? '' : 'none';
  if (selHora) selHora.disabled = !porHora;
}

function abrirModalRegistroProduccion() {
  const fechaSel = document.getElementById('ctrl-fecha');
  if (fechaSel && !fechaSel.value) fechaSel.valueAsDate = new Date();
  cancelarEdicionControl();
  const overlay = document.getElementById('reg-modal-overlay');
  if (overlay) overlay.classList.add('reg-modal-visible');
}
  const overlay = document.getElementById('reg-modal-overlay');
  if (overlay) overlay.classList.add('reg-modal-visible');
}

function cerrarModalRegistroProduccion() {
  const overlay = document.getElementById('reg-modal-overlay');
  if (overlay) overlay.classList.remove('reg-modal-visible');
}

async function initControlHora() {
  // Máquinas: si el usuario tiene líneas asignadas, solo las de esas líneas; si no, todas
  const maquinas = await api('/api/maquinaria');
  if (!maquinas) return;

  // Modalidad de registro global de la plataforma (Diario | Por Hora)
  const cfg = await api('/api/configuracion');
  window.modalidadRegistro = (cfg && cfg.modalidad_registro) || 'Diario';
  const selModalidad = document.getElementById('select-modalidad');
  if (selModalidad) selModalidad.value = window.modalidadRegistro;
  aplicarModalidadRegistro();

  // Select de horas (para modalidad Por Hora)
  const horas = await api('/api/horas');
  const selHora = document.getElementById('ctrl-hora');
  selHora.innerHTML = '<option value="">Seleccione hora...</option>';
  (horas || []).forEach(h => {
    const etiqueta = h.nombre;
    selHora.innerHTML += `<option value="${h.id}">${etiqueta}</option>`;
  });

  const lineasUsuario = sesionActual && sesionActual.lineas && sesionActual.lineas.length > 0
    ? sesionActual.lineas.map(l => l.id)
    : null;

  const filtradas = lineasUsuario
    ? maquinas.filter(m => m.id_modulo && lineasUsuario.includes(m.id_modulo))
    : maquinas;

  const selMaq = document.getElementById('ctrl-maquina');
  selMaq.innerHTML = '<option value="">Seleccione Máquina...</option>';
  filtradas.forEach(m => {
    const etiqueta = m.nombre_modulo ? `${m.nombre} (${m.nombre_modulo})` : m.nombre;
    selMaq.innerHTML += `<option value="${m.id}" data-modulo="${m.id_modulo || ''}" data-modulo-nombre="${m.nombre_modulo || ''}">${etiqueta}</option>`;
  });

  document.getElementById('ctrl-fecha').valueAsDate = new Date();

  const paradas = catalogoParadasCache;
  actualizarSelectParadas(paradas);

  const causas = await api('/api/causas-parada');
  causasParadaCache = causas || [];
  document.querySelectorAll('.parada-np-causa').forEach(sel => llenarSelectCausas(sel));

  cargarControlesHoy();
}

function llenarSelectCausas(select) {
  const val = select.value;
  select.innerHTML = '<option value="">Seleccione causa...</option>';
  causasParadaCache.forEach(c => {
    select.innerHTML += `<option value="${c.id}">${c.nombre}</option>`;
  });
  if (val) select.value = val;
}

function toggleDescripcionParada(select) {
  const fila = select.closest('.parada-np-row');
  const desc = fila ? fila.querySelector('.parada-np-desc') : null;
  if (!desc) return;
  const esOtro = select.options[select.selectedIndex] ? select.options[select.selectedIndex].text === 'Otro' : false;
  desc.style.display = esOtro ? 'block' : 'none';
}

function actualizarSelectParadas(paradas) {
  const selParada = document.getElementById('ctrl-parada-p');
  selParada.innerHTML = '';
  paradas.forEach(p => {
    selParada.innerHTML += `<option value="${p.id}" data-tiempo="${p.tiempo}">${p.nombre}</option>`;
  });
  actualizarTiempoParadaP();
}

function actualizarTiempoParadaP() {
  const sel = document.getElementById('ctrl-parada-p');
  const opt = sel.options[sel.selectedIndex];
  document.getElementById('ctrl-tiempo-p').value = opt ? opt.dataset.tiempo || 0 : 0;
}

function agregarFilaParadaNP() {
  const cont = document.getElementById('lista-paradas-np');
  const fila = document.createElement('div');
  fila.className = 'parada-np-row';
  fila.innerHTML = `
    <select class="parada-np-causa" onchange="toggleDescripcionParada(this)"></select>
    <input type="number" class="parada-np-tiempo" placeholder="Segundos" min="0">
    <input type="text" class="parada-np-desc" placeholder="¿Qué pasó?" style="display:none;">
    <button class="btn-icon btn-delete" onclick="this.parentElement.remove()">✕</button>
  `;
  cont.appendChild(fila);
  llenarSelectCausas(fila.querySelector('.parada-np-causa'));
}

async function cargarReferenciasPorModulo() {
  const selMaq = document.getElementById('ctrl-maquina');
  const selRef = document.getElementById('ctrl-referencia');
  const optMaq = selMaq.options[selMaq.selectedIndex];

  const idModulo = optMaq ? parseInt(optMaq.getAttribute('data-modulo') || 0) : 0;
  const nombreModulo = optMaq ? optMaq.getAttribute('data-modulo-nombre') || '' : '';

  // Mostrar módulo deducido de la máquina
  const infoModulo = document.getElementById('ctrl-modulo-info');
  const hiddenModulo = document.getElementById('ctrl-modulo');
  if (infoModulo) {
    infoModulo.value = idModulo ? nombreModulo : '';
  }
  if (hiddenModulo) hiddenModulo.value = idModulo || '';

  // Limpiar dependientes
  if (!idModulo) {
    selRef.innerHTML = '<option value="">Seleccione Máquina primero...</option>';
    selRef.disabled = true;
    document.getElementById('ctrl-actividad').innerHTML = '<option value="">Seleccione la orden primero...</option>';
    document.getElementById('ctrl-actividad').disabled = true;
    actualizarTiempoCiclo();
    return;
  }

  const refs = await api(`/api/modulos/${idModulo}/referencias-asignadas`);
  if (!refs) return;

  selRef.innerHTML = '<option value="">Seleccione Asignación...</option>';
  refs.forEach(r => {
    const etiqueta = r.nombre_orden ? `${r.nombre_orden} - ${r.nombre}` : r.nombre;
    selRef.innerHTML += `<option value="${r.id}" data-ref-id="${r.id_referencia}" data-orden-id="${r.id_orden}">${etiqueta}</option>`;
  });
  selRef.disabled = false;

  document.getElementById('ctrl-actividad').innerHTML = '<option value="">Seleccione la orden primero...</option>';
  document.getElementById('ctrl-actividad').disabled = true;
  cargarOpcionesActividad();
}

async function cargarOpcionesActividad() {
  const selRef = document.getElementById('ctrl-referencia');
  const selAct = document.getElementById('ctrl-actividad');
  const selMaq = document.getElementById('ctrl-maquina');
  const optRef = selRef.options[selRef.selectedIndex];
  const idReferencia = optRef ? optRef.getAttribute('data-ref-id') : null;
  const idMaquina = parseInt(selMaq.value) || 0;

  if (!idReferencia) {
    selAct.innerHTML = '<option value="">Seleccione la orden primero...</option>';
    selAct.disabled = true;
    return;
  }

  const detalles = await api(`/api/referencias/${idReferencia}/detalles`);
  if (!detalles) { selAct.disabled = true; return; }

  // Mostrar SOLO las actividades que se ejecutan en la MÁQUINA seleccionada.
  // (Si la operación no tiene máquina definida, se muestra por si acaso.)
  const disponibles = detalles.filter(d => !d.id_maquina || d.id_maquina === idMaquina);

  selAct.innerHTML = '<option value="">Seleccione actividad...</option>';
  disponibles.forEach(d => {
    selAct.innerHTML += `<option value="${d.id_operacion}" data-letra="${d.letra}" data-tc="${d.tiempo || 0}">${d.letra} - ${d.nombre_operacion}</option>`;
  });
  if (disponibles.length === 0) {
    selAct.innerHTML = '<option value="">Esta máquina no ejecuta ninguna actividad de esta referencia...</option>';
  }
  selAct.disabled = false;
  actualizarTiempoCiclo();
}

function actualizarTiempoCiclo() {
  // Muestra el TIEMPO de la actividad seleccionada en el campo ctrl-ciclo (antes manejado por actualizarOpcionesCiclo, que no existía)
  const selAct = document.getElementById('ctrl-actividad');
  const ctrlCiclo = document.getElementById('ctrl-ciclo');
  if (!ctrlCiclo) return;
  const opt = selAct.options[selAct.selectedIndex];
  const tc = opt ? (parseInt(opt.getAttribute('data-tc')) || 0) : 0;
  if (tc > 0) {
    const mm = Math.floor(tc / 60);
    const ss = tc % 60;
    ctrlCiclo.innerHTML = `<option value="${tc}" selected>${tc}s (${mm}min ${String(ss).padStart(2, '0')}s)</option>`;
  } else {
    ctrlCiclo.innerHTML = '<option value="" selected>-</option>';
  }
}

async function guardarControlHora(btn = null) {
  const fecha = document.getElementById('ctrl-fecha').value;
  const idMaquina = document.getElementById('ctrl-maquina').value;
  const idMod = document.getElementById('ctrl-modulo').value;
  const selRef = document.getElementById('ctrl-referencia');
  const optRef = selRef.options[selRef.selectedIndex];
  const idOrden = optRef ? optRef.getAttribute('data-orden-id') : null;
  const idOperacion = document.getElementById('ctrl-actividad').value;
  const cantidad = document.getElementById('ctrl-cantidad').value;
  const defectuosas = document.getElementById('ctrl-defectuosas').value;
  const porHora = (window.modalidadRegistro || 'Diario') === 'Por Hora';
  const idHora = porHora ? document.getElementById('ctrl-hora').value : '';

  let valid = true;
  if (!fecha) { showFieldError('ctrl-fecha', 'Requerido'); valid = false; } else clearFieldErrors('ctrl-fecha');
  if (!idMaquina) { showFieldError('ctrl-maquina', 'Seleccione la máquina'); valid = false; } else clearFieldErrors('ctrl-maquina');
  if (!idOrden) { showFieldError('ctrl-referencia', 'Seleccione una orden'); valid = false; } else clearFieldErrors('ctrl-referencia');
  if (!idOperacion) { showFieldError('ctrl-actividad', 'Seleccione la actividad'); valid = false; } else clearFieldErrors('ctrl-actividad');
  if (porHora && !idHora) { showFieldError('ctrl-hora', 'Seleccione la hora'); valid = false; } else if (porHora) clearFieldErrors('ctrl-hora');
  if (!cantidad || isNaN(cantidad) || Number(cantidad) <= 0) { showFieldError('ctrl-cantidad', 'Ingrese cantidad'); valid = false; } else clearFieldErrors('ctrl-cantidad');
  if (!sesionActual) { Toast.error('Debe iniciar sesión para registrar'); return; }
  if (!valid) return;

  const paradasNP = [];
  document.querySelectorAll('.parada-np-row').forEach(fila => {
    const causa = fila.querySelector('.parada-np-causa').value;
    const tiempo = fila.querySelector('.parada-np-tiempo').value;
    const causaTexto = fila.querySelector('.parada-np-causa').options[fila.querySelector('.parada-np-causa').selectedIndex];
    const esOtro = causaTexto && causaTexto.text === 'Otro';
    const descripcion = fila.querySelector('.parada-np-desc').value.trim();
    if (causa && tiempo) {
      paradasNP.push({
        id_causa: parseInt(causa),
        tiempo_segundos: parseInt(tiempo),
        descripcion: esOtro ? (descripcion || '') : null
      });
    }
  });

  const idParadaP = document.getElementById('ctrl-parada-p').value;
  const tiempoP = document.getElementById('ctrl-tiempo-p').value;
  const paradas = [];
  if (idParadaP && parseInt(tiempoP) > 0) {
    paradas.push({ id_parada_programada: parseInt(idParadaP), tiempo_segundos: parseInt(tiempoP) });
  }
  paradasNP.forEach(p => paradas.push(p));

  // VALIDACIÓN: aviso si ya hay registro de esta actividad hoy (módulo, y hora si es por hora)
  const horaQ = porHora ? `&id_hora=${idHora}` : '';
  const resumen = await api(`/api/produccion/resumen?fecha=${fecha}&id_modulo=${idMod}&id_operacion=${idOperacion}${horaQ}`);
  let continuar = true;
  if (resumen && resumen.hora > 0) {
    const sufijo = porHora ? ` en esta hora` : ' hoy en este módulo';
    continuar = await Modal.confirm(
      'Ya hay registro',
      `Ya registraste ${resumen.hora} unidades de esta actividad${sufijo}.\nEn el día llevas ${resumen.dia} unidades registradas.\n¿Deseas continuar?`
    );
  }
  if (!continuar) return;

  const payload = {
    fecha,
    id_modulo: parseInt(idMod),
    id_orden: parseInt(idOrden),
    id_operacion: parseInt(idOperacion),
    id_maquina: parseInt(idMaquina),
    id_hora: porHora ? parseInt(idHora) : null,
    porcion_tiempo: 1.0,
    cantidad_operarios: parseInt(document.getElementById('ctrl-operarios').value || 0),
    cantidad_producida: parseInt(cantidad),
    cantidad_defectuosa: defectuosas ? parseInt(defectuosas) : 0,
    observaciones: document.getElementById('ctrl-obs').value.trim(),
    id_usuario: sesionActual.id,
    paradas
  };

  const data = await api('/api/produccion', {
    method: 'POST',
    body: JSON.stringify(payload),
    _btn: btn
  });

  if (data) {
    Toast.success(data.mensaje || 'Registro guardado');
    cancelarEdicionControl();
    cargarControlesHoy();
  }
}

async function cargarControlesHoy() {
  const fecha = document.getElementById('ctrl-fecha').value || new Date().toISOString().split('T')[0];
  const usr = sesionActual ? `&id_usuario=${sesionActual.id}` : '';
  const data = await api(`/api/produccion/dia?fecha=${fecha}${usr}`);
  if (!data) return;

  const tbody = document.getElementById('lista-controles');
  tbody.innerHTML = '';
  document.getElementById('empty-controles').style.display = data.length === 0 ? 'block' : 'none';

  data.forEach(c => {
    // Paradas resumen
    const paradasTexto = (c.paradas || []).map(p => {
      const n = p.parada_programada || p.causa;
      let txt = n ? `${n} (${formatTime(p.tiempo)})` : null;
      if (p.descripcion) txt += ` → ${p.descripcion}`;
      return txt;
    }).filter(Boolean).join(', ') || 'Sin paradas';

    const defectClass = c.cantidad_defectuosa > 0 ? 'badge-machine' : 'badge-module';
    const actividad = c.letra ? `<span class="badge badge-hour">${c.letra}</span> ${c.nombre_operacion || ''}` : '-';
    const maquinaCell = c.maquina ? `<span title="${c.maquina}" style="font-size:0.72rem;color:var(--text-muted);">🔧 ${c.maquina}</span>` : '-';
    // Marca de tiempo real: si hay created_at muestro su hora, si no la fecha.
    // Si el registro es POR HORA, muestro la hora del catálogo (ej: Hora 3) + marca.
    let marca = c.hora_nombre || c.timestamp || c.fecha;
    if (marca && !c.hora_nombre && marca.includes(' ')) marca = marca.split(' ')[1].substring(0, 5);
    const badgeHora = c.hora_nombre ? 'badge-machine' : 'badge-hour';
    tbody.innerHTML += `
      <tr>
        <td><span class="badge ${badgeHora}">${marca}</span></td>
        <td>${c.modulo}<br>${maquinaCell}</td>
        <td>${c.orden}</td>
        <td>${actividad}</td>
        <td class="text-accent">${c.cantidad_producida}</td>
        <td><span class="badge ${defectClass}">${c.cantidad_defectuosa || 0}</span></td>
        <td>${c.usuario}</td>
        <td title="${paradasTexto}" style="max-width:140px;">${paradasTexto}</td>
        <td class="action-buttons">
          <button class="btn-icon btn-delete" onclick="eliminarControlHora(${c.id})">✕</button>
        </td>
      </tr>
    `;
  });
}

async function eliminarControlHora(id) {
  const ok = await Modal.confirm('Eliminar Registro', '¿Eliminar este registro de producción?');
  if (!ok) return;

  const data = await api(`/api/produccion/${id}`, { method: 'DELETE' });
  if (data) {
    Toast.success('Registro eliminado');
    cargarControlesHoy();
  }
}

function cancelarEdicionControl() {
  document.getElementById('ctrl-cantidad').value = '';
  document.getElementById('ctrl-defectuosas').value = '0';
  document.getElementById('ctrl-obs').value = '';
  document.getElementById('ctrl-maquina').value = '';
  document.getElementById('ctrl-modulo').value = '';
  const infoModulo = document.getElementById('ctrl-modulo-info');
  if (infoModulo) infoModulo.value = '';
  document.getElementById('ctrl-operarios').value = '';
  document.getElementById('ctrl-parada-p').value = '1';
  actualizarTiempoParadaP();
  document.querySelectorAll('.parada-np-row:not(:first-child)').forEach(r => r.remove());
  const fila1 = document.querySelector('.parada-np-row');
  if (fila1) {
    fila1.querySelector('.parada-np-causa').value = '';
    fila1.querySelector('.parada-np-tiempo').value = '';
    fila1.querySelector('.parada-np-desc').value = '';
    fila1.querySelector('.parada-np-desc').style.display = 'none';
  }

  const selRef = document.getElementById('ctrl-referencia');
  selRef.value = '';
  selRef.innerHTML = '<option value="">Seleccione Máquina primero...</option>';
  selRef.disabled = true;
}

// ============================================================
// TABLERO DE EFICIENCIAS
// ============================================================

async function consultarEficiencia() {
  const startDate = document.getElementById('eff-fecha-inicio').value;
  const endDate = document.getElementById('eff-fecha-fin').value;
  const idRef = document.getElementById('eff-referencia').value;
  const idOrden = document.getElementById('eff-orden').value;
  const container = document.getElementById('eff-reporte-container');

  if (!startDate || !endDate) { Toast.warning('Seleccione el rango de fechas'); return; }

  container.innerHTML = '<div class="empty-state" style="text-align:center; padding: 40px;">Procesando datos...</div>';

  try {
    let url = `/api/reportes/eficiencia?fecha_inicio=${startDate}&fecha_fin=${endDate}`;
    if (idRef) url += `&id_referencia=${idRef}`;
    if (idOrden) url += `&id_orden=${idOrden}`;

    const data = await api(url);
    if (!data) return;

    if (data.reporte.length === 0) {
      container.innerHTML = '<div class="empty-state" style="text-align:center; padding: 40px;">No hay registros para este periodo con los filtros seleccionados.</div>';
      return;
    }

    renderizarTablaEficiencia(data);
  } catch (e) {
    container.innerHTML = '<div class="empty-state" style="text-align:center; padding: 40px; color:var(--accent-danger);">Error de conexión.</div>';
  }
}

async function cargarFiltrosEficiencia() {
  const refs = await api('/api/referencias');
  if (!refs) return;
  const selRef = document.getElementById('eff-referencia');
  const val = selRef.value;
  selRef.innerHTML = '<option value="">Todas</option>';
  refs.forEach(r => selRef.innerHTML += `<option value="${r.id}">${r.nombre}</option>`);
  if (val) selRef.value = val;
  cargarOrdenesFiltro();
}

async function cargarOrdenesFiltro() {
  const ordenes = await api('/api/ordenes');
  if (!ordenes) return;
  const idRef = document.getElementById('eff-referencia').value;
  const sel = document.getElementById('eff-orden');
  const val = sel.value;
  sel.innerHTML = '<option value="">Todos</option>';
  ordenes.forEach(o => {
    if (!idRef || o.id_referencia === parseInt(idRef)) {
      sel.innerHTML += `<option value="${o.id}">${o.nombre_orden}</option>`;
    }
  });
  if (val) sel.value = val;
}

function renderizarTablaEficiencia(data) {
  const container = document.getElementById('eff-reporte-container');
  const modulos = data.modulos;
  const reporte = data.reporte;

  // ---- Resumen por módulo (todo el período) + detalle por hora ----
  window.effDetalleModulos = {};
  const resumenMod = {};
  modulos.forEach(m => {
    resumenMod[m] = { cant: 0, meta: 0, defectos: 0 };
    window.effDetalleModulos[m] = [];
  });

  reporte.forEach(row => {
    modulos.forEach(m => {
      const d = row.datos_modulos[m] || {};
      resumenMod[m].cant += d.cantidad || 0;
      resumenMod[m].meta += d.meta || 0;
      resumenMod[m].defectos += d.defectos || 0;
      window.effDetalleModulos[m].push({
        dia: row.fecha,
        cant: d.cantidad || 0,
        meta: d.meta || 0,
        eff: d.eficiencia || 0,
        calidad: d.calidad || 0
      });
    });
  });

  let html = '';

  // Tarjetas por línea (clicables)
  html += `<div class="eff-tarjetas">`;
  modulos.forEach(m => {
    const r = resumenMod[m];
    const eff = r.meta > 0 ? Math.round(r.cant / r.meta * 100) : 0;
    const cal = r.cant > 0 ? Math.round((r.cant - r.defectos) / r.cant * 100) : 0;
    const colorName = eff >= 100 ? 'var(--eff-super)' : (eff >= 90 ? 'var(--eff-good)' : (eff >= 80 ? 'var(--eff-warn)' : 'var(--eff-critical)'));
    const nombreId = m.replace(/[^a-zA-Z0-9]/g, '_');
    html += `
      <div class="eff-tarjeta" onclick="mostrarDetalleModulo('${nombreId}')" title="Clic para ver detalle por día">
        <div class="eff-tarjeta-nombre">${m}</div>
        <div class="eff-tarjeta-num" style="color:${colorName};">${eff}%</div>
        <div class="eff-tarjeta-label">Eficiencia</div>
        <div class="progress-bar-container" style="height:7px; margin:8px 0;">
          <div class="progress-bar" style="width:${Math.min(100,eff)}%; ${claseBarraEficiencia(eff)}"></div>
        </div>
        <div class="eff-tarjeta-footer">
          <span>${r.cant} uds</span>
          <span>Calidad ${cal}%</span>
        </div>
        <div class="eff-tarjeta-ver">Ver detalle por día →</div>
      </div>`;
    window['effTarjeta_' + nombreId] = m;
  });
  html += '</div>';

  // Tabla consolidada por día (solo totales, ligera)
  html += `<div class="report-table-container" style="margin-top:20px;"><table class="report-table"><thead>
    <tr><th class="header-hora">FECHA</th><th>CANT</th><th>META</th><th>EFF</th><th>CALID</th></tr>
  </thead><tbody>`;

  reporte.forEach(row => {
    const t = row.total_planta;
    const tCalidClass = t.calidad >= 95 ? 'bg-eff-good' : (t.calidad >= 90 ? 'bg-eff-warn' : 'bg-eff-critical');
    html += `<tr>
      <td class="header-hora">${row.fecha}</td>
      <td>${t.cantidad}</td>
      <td>${t.meta}</td>
      <td class="cell-eff ${obtenerClaseEficiencia(t.eficiencia)}">${t.eficiencia}%</td>
      <td class="cell-eff ${tCalidClass}">${t.calidad}%</td>
    </tr>`;
  });

  // Fila de total del periodo
  const totCant = Object.values(resumenMod).reduce((s, r) => s + r.cant, 0);
  const totMeta = Object.values(resumenMod).reduce((s, r) => s + r.meta, 0);
  const totEff = totMeta > 0 ? Math.round(totCant / totMeta * 100) : 0;
  const totDef = Object.values(resumenMod).reduce((s, r) => s + r.defectos, 0);
  const totCal = totCant > 0 ? Math.round((totCant - totDef) / totCant * 100) : 0;
  html += `<tr>
    <td class="header-hora">TOTAL</td>
    <td><strong>${totCant}</strong></td>
    <td><strong>${totMeta}</strong></td>
    <td class="cell-eff ${obtenerClaseEficiencia(totEff)}"><strong>${totEff}%</strong></td>
    <td class="cell-eff ${totCal >= 95 ? 'bg-eff-good' : totCal >= 90 ? 'bg-eff-warn' : 'bg-eff-critical'}"><strong>${totCal}%</strong></td>
  </tr>`;

  html += '</tbody></table></div>';

  container.innerHTML = html;
}

function mostrarDetalleModulo(nombreId) {
  const modulo = window['effTarjeta_' + nombreId];
  if (!modulo || !window.effDetalleModulos || !window.effDetalleModulos[modulo]) return;

  const detalle = window.effDetalleModulos[modulo];
  let html = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
      <div style="font-weight:700; font-size:1.1rem; color:var(--text-primary);">${modulo} — detalle por día</div>
      <button class="btn-secondary" onclick="cerrarDetalleModulo()" style="width:auto; padding:6px 14px;">✕ Cerrar</button>
    </div>
    <div class="report-table-container"><table class="report-table"><thead>
      <tr><th class="header-hora">FECHA</th><th>CANT</th><th>META</th><th>EFF</th><th>CALID</th></tr>
    </thead><tbody>`;

  detalle.forEach(h => {
    const cClass = h.calidad >= 95 ? 'bg-eff-good' : (h.calidad >= 90 ? 'bg-eff-warn' : 'bg-eff-critical');
    html += `<tr>
      <td class="header-hora">${h.dia}</td>
      <td>${h.cant}</td>
      <td>${h.meta}</td>
      <td class="cell-eff ${obtenerClaseEficiencia(h.eff)}">${h.eff}%</td>
      <td class="cell-eff ${cClass}">${h.calidad}%</td>
    </tr>`;
  });
  html += '</tbody></table></div>';

  // Insertar el detalle debajo de las tarjetas
  let detalleEl = document.getElementById('eff-detalle-modulo');
  if (!detalleEl) {
    detalleEl = document.createElement('div');
    detalleEl.id = 'eff-detalle-modulo';
    const tarjetas = document.querySelector('.eff-tarjetas');
    if (tarjetas) tarjetas.parentNode.insertBefore(detalleEl, tarjetas.nextSibling);
  }
  detalleEl.innerHTML = `<div style="margin-top:16px; padding:16px; background:var(--bg-secondary); border:1px solid var(--card-border); border-radius:12px;">${html}</div>`;
  detalleEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function cerrarDetalleModulo() {
  const el = document.getElementById('eff-detalle-modulo');
  if (el) el.innerHTML = '';
}

function claseBarraEficiencia(eff) {
  if (eff >= 100) return 'background:var(--eff-super);';
  if (eff >= 90) return 'background:var(--eff-good);';
  if (eff >= 80) return 'background:var(--eff-warn);';
  return 'background:var(--eff-critical);';
}

function obtenerClaseEficiencia(v) {
  if (v >= 100) return 'bg-eff-super';
  if (v >= 90) return 'bg-eff-good';
  if (v >= 80) return 'bg-eff-warn';
  return 'bg-eff-critical';
}

// ============================================================
// PROGRESO DE PRODUCCIÓN
// ============================================================

async function cargarOrdenesReporte() {
  const data = await api('/api/ordenes');
  if (!data) return;
  const select = document.getElementById('prog-reporte-orden');
  select.innerHTML = '<option value="">Seleccione el lote...</option>';
  data.forEach(o => {
    select.innerHTML += `<option value="${o.id}">${o.nombre_orden} — ${o.referencia}</option>`;
  });
}

async function consultarProgreso() {
  const idOrden = document.getElementById('prog-reporte-orden').value;
  if (!idOrden) { Toast.warning('Seleccione una orden'); return; }

  const data = await api(`/api/progreso/${idOrden}`);
  if (!data) return;
  renderizarProgreso(data);
}

function renderizarProgreso(data) {
  document.getElementById('progreso-resumen').style.display = 'block';
  document.getElementById('progreso-ref').innerText = data.referencia;
  document.getElementById('progreso-orden').innerText = `${data.nombre_orden} · Lote objetivo: ${data.cantidad_lote} gorras · Estado: ${data.estado}`;
  document.getElementById('progreso-total-pct').innerText = data.porcentaje_total + '%';
  document.getElementById('progreso-total-bar').style.width = Math.min(100, data.porcentaje_total) + '%';
  document.getElementById('progreso-hechas').innerText = `${data.unidades_completas} completas`;
  document.getElementById('progreso-objetivo').innerText = `Objetivo: ${data.unidades_objetivo} gorras`;

  const container = document.getElementById('progreso-container');
  if (data.actividades.length === 0) {
    container.innerHTML = '<div class="empty-state" style="text-align:center; padding:40px;">Esta referencia no tiene actividades definidas.</div>';
    return;
  }

  // Ordenar actividades por avance ASC (las más atrasadas primero = prioridad)
  const ordenadas = [...data.actividades].sort((a, b) => a.avance - b.avance);
  const cuello = data.actividades.filter(a => a.producido === data.unidades_completas && data.unidades_completas > 0);
  const actividadesCriticas = ordenadas.filter(a => a.avance < data.porcentaje_total && a.avance < 100);
  const pendientes = ordenadas.filter(a => a.avance < 100);
  const completas = ordenadas.filter(a => a.avance >= 100);

  let html = '';

  // KPIs rápidos
  html += `
    <div class="progreso-kpi-grid">
      <div class="progreso-kpi">
        <div class="progreso-kpi-num">${data.unidades_completas}</div>
        <div class="progreso-kpi-label">Gorras completas</div>
      </div>
      <div class="progreso-kpi">
        <div class="progreso-kpi-num">${data.actividades.length - completas.length}</div>
        <div class="progreso-kpi-label">Actividades pendientes</div>
      </div>
      <div class="progreso-kpi">
        <div class="progreso-kpi-num">${completas.length}</div>
        <div class="progreso-kpi-label">Actividades al 100%</div>
      </div>
    </div>`;

  // Alertas de prioridad
  if (cuello.length > 0 && data.porcentaje_total < 100) {
    html += `
      <div style="margin:16px 0; padding:14px 16px; border:1px solid var(--accent-danger); border-radius:10px; background:rgba(239,68,68,0.08);">
        <strong style="color:var(--accent-danger);">⛔ Está frenando la producción:</strong>
        <span style="color:var(--text-secondary);"> ${cuello.map(a => `${a.letra} — ${a.nombre}`).join(' · ')}</span>
        <div style="color:var(--text-muted); font-size:0.8rem; margin-top:6px;">Solo ${cuello[0].producido} de ${data.cantidad_lote} pasaron por esta actividad. Mientras no avance, ninguna gorra puede completarse.</div>
      </div>`;
  } else if (data.porcentaje_total >= 100) {
    html += `<div style="margin:16px 0; padding:14px 16px; border:1px solid var(--accent-success); border-radius:10px; background:rgba(74,222,128,0.08);">
      <strong style="color:var(--accent-success);">✅ Lote completo</strong></div>`;
  }

  // Tabla de actividades: las críticas resaltadas primero
  html += `<div class="report-table-container"><table class="report-table"><thead>
    <tr><th>ACT.</th><th>OPERACIÓN</th><th>PRODUCIDO</th><th>OBJETIVO</th><th style="min-width:200px;">AVANCE</th><th>%</th><th>ESTADO</th></tr>
  </thead><tbody>`;

  ordenadas.forEach(a => {
    const pct = Math.min(100, a.avance);
    let color = 'var(--accent-success)';
    let estado = '<span class="badge badge-module">OK</span>';
    if (a.avance >= 100) { color = 'var(--eff-super)'; estado = '<span class="badge badge-module" style="background:rgba(6,182,212,.15); color:var(--eff-super);">100%</span>'; }
    else if (a.avance < data.porcentaje_total) { color = 'var(--accent-danger)'; estado = '<span class="badge badge-machine">CRÍTICA</span>'; }
    else if (a.avance < 80) { color = 'var(--eff-warn)'; estado = '<span class="badge badge-hour">ATRASADA</span>'; }
    const esCuello = cuello.some(c => c.id_operacion === a.id_operacion) && data.porcentaje_total < 100;
    html += `
      <tr ${esCuello ? 'style="background:rgba(239,68,68,0.06);"' : ''}>
        <td><span class="progreso-activity-letra" style="width:26px;height:26px;">${a.letra}</span></td>
        <td>${a.nombre}</td>
        <td class="${a.avance < data.porcentaje_total ? 'text-accent' : ''}">${a.producido}</td>
        <td>${a.necesario}</td>
        <td><div class="progress-bar-container" style="margin:0;"><div class="progress-bar" style="width:${pct}%; background:${color};"></div></div></td>
        <td class="cell-eff" style="color:${color}; font-weight:700;">${a.avance}%</td>
        <td>${estado}${esCuello ? ' <span class="badge badge-machine">CU</span>' : ''}</td>
      </tr>`;
  });

  html += `</tbody></table></div>`;

  container.innerHTML = html;
}

// ============================================================
// SIMULADOR DE BALANCEO
// ============================================================

let resultadoSimulacionGlobal = null;

async function mostrarMinimoOperarios() {
  const idRef = document.getElementById('sim-referencia').value;
  const hint = document.getElementById('sim-min-hint');
  if (!idRef) { hint.innerText = ''; return; }

  const detalles = await api(`/api/referencias/${idRef}/detalles`);
  if (!detalles || detalles.length === 0) { hint.innerText = ''; return; }

  const maquinas = new Set(detalles.map(d => d.maquina));
  const minimo = maquinas.size;
  hint.innerText = `Requiere al menos ${minimo} operarios (${minimo} tipos de máquina: ${Array.from(maquinas).join(', ')})`;
  const input = document.getElementById('sim-operarios');
  if (parseInt(input.value) < minimo) input.value = minimo;
}

async function ejecutarSimulacion() {
  const idRef = document.getElementById('sim-referencia').value;
  const numOps = document.getElementById('sim-operarios').value;

  if (!idRef) { Toast.warning('Seleccione una referencia'); return; }
  if (!numOps || numOps < 1) { Toast.warning('Ingrese número de operarios'); return; }

  const data = await api('/api/balanceo/calcular', {
    method: 'POST',
    body: JSON.stringify({ id_referencia: parseInt(idRef), num_operarios: parseInt(numOps) }),
    _btn: event.target
  });

  if (!data) return;

  if (data.error) {
    Toast.error(data.error);
    return;
  }

  resultadoSimulacionGlobal = data;
  document.getElementById('sim-scenario-controls').style.display = 'flex';
  cambiarEscenario('secuencial');
}

function cambiarEscenario(tipo) {
  if (!resultadoSimulacionGlobal) return;

  document.getElementById('btn-scen-sec').classList.toggle('active', tipo === 'secuencial');
  document.getElementById('btn-scen-eff').classList.toggle('active', tipo === 'eficiencia');

  renderizarResultados(resultadoSimulacionGlobal[tipo]);
}

function renderizarResultados(data) {
  document.getElementById('sim-resultados').style.display = 'block';

  const kpis = data.kpis;
  const ef = document.getElementById('kpi-eficiencia');
  ef.innerText = kpis.eficiencia + '%';
  ef.style.color = kpis.eficiencia > 85 ? 'var(--accent-success)' : (kpis.eficiencia < 60 ? 'var(--accent-danger)' : 'var(--text-primary)');

  document.getElementById('kpi-produccion').innerText = kpis.produccion_hora;
  document.getElementById('kpi-ciclo').innerText = formatTime(kpis.tiempo_ciclo);

  const numOps = parseInt(document.getElementById('sim-operarios').value || 1);
  const totalCycle = kpis.tiempo_ciclo * numOps;
  document.getElementById('kpi-ciclo-total').innerText = formatTime(totalCycle);

  const grid = document.getElementById('grid-operarios');
  grid.innerHTML = '';

  data.operarios.forEach(op => {
    let tareasHtml = '';
    op.tareas.forEach(t => {
      tareasHtml += `
        <div class="task-item-mini">
          <span><strong style="color:var(--accent-blue)">${t.letra}</strong> ${t.nombre}</span>
          <span style="color:var(--text-muted)">${formatTime(t.tiempo)}</span>
        </div>
      `;
    });

    let barColor = 'var(--accent-success)';
    if (op.porcentaje_carga < 80) barColor = '#facc15';
    if (op.porcentaje_carga > 105) barColor = '#f87171';

    grid.innerHTML += `
      <div class="operator-card">
        <div class="operator-header">
          <span style="font-weight:700; font-size:1.1rem;">${op.nombre}</span>
          <span class="op-machine-badge">${op.maquina_asignada || 'N/A'}</span>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-top:4px;">
          <span>Carga: ${formatTime(op.tiempo_acumulado)}</span>
          <span>${Math.round(op.porcentaje_carga)}%</span>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar" style="width: ${op.porcentaje_carga}%; background-color: ${barColor}"></div>
        </div>
        <div class="task-list-mini">
          ${tareasHtml || '<div style="font-style:italic; padding:8px;">Sin tareas asignadas</div>'}
        </div>
      </div>
    `;
  });
}

// ============================================================
// INICIALIZACIÓN
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  const sesionOk = ocultarSesionInicial();

  cargarMaquinaria();
  cargarSelectMaquinaModulo();
  cargarSecciones();
  cargarModulos();
  cargarEmpleados();
  cargarSelectMaquinaEmpleado();
  cargarUsuarioModulosSupervisor();
  cargarMateriales();
  cargarHoras();
  cargarParadas();
  cargarOperaciones();
  cargarReferencias();
  cargarOrdenes();
  cargarSelectOrdenesRef();
  cargarDatosProgramacion();
  cargarAsignaciones();
  cargarUsuarios();
  cargarSelectUsuarioEmpleado();
  cargarCausas();
  conectarBuscadores();

  if (sesionOk) {
    initControlHora();
    cargarControlesHoy();
  }

  // Enter en el login
  document.getElementById('login-password').addEventListener('keydown', e => {
    if (e.key === 'Enter') iniciarSesion();
  });
  document.getElementById('login-usuario').addEventListener('keydown', e => {
    if (e.key === 'Enter') iniciarSesion();
  });
});
