
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
  if (moduleId === 'mod-control-hora') initControlHora();
  if (moduleId === 'mod-eficiencia') {
    const hoy = new Date().toISOString().split('T')[0];
    const fi = document.getElementById('eff-fecha-inicio');
    const ff = document.getElementById('eff-fecha-fin');
    if (!fi.value) fi.value = hoy;
    if (!ff.value) ff.value = hoy;
  }
}

// ============================================================
// CATÁLOGOS
// ============================================================

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
          <td>${m.id}</td>
          <td><strong>${m.nombre}</strong></td>
          <td>${m.descripcion || '-'}</td>
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
  const velocidad = document.getElementById('input-maquina-vel').value;
  const estado = document.getElementById('input-maquina-estado').value;

  if (!nombre) { showFieldError('input-maquina', 'Ingrese un nombre'); return; }
  clearFieldErrors('input-maquina');

  const data = await api('/api/maquinaria', {
    method: 'POST',
    body: JSON.stringify({
      nombre,
      descripcion: descripcion || null,
      velocidad_tipica: velocidad ? parseInt(velocidad) : null,
      estado
    }),
    _btn: event.target
  });

  if (data) {
    document.getElementById('input-maquina').value = '';
    document.getElementById('input-maquina-desc').value = '';
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
      tbody.innerHTML += `
        <tr>
          <td>${m.id}</td>
          <td><strong>${m.nombre}</strong></td>
          <td>${m.capacidad_maxima ? m.capacidad_maxima + ' op.' : '-'}</td>
          <td>${m.ubicacion || '-'}</td>
          <td>${m.supervisor || '-'}</td>
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
  const supervisor = document.getElementById('input-modulo-sup').value.trim();
  const estado = document.getElementById('input-modulo-estado').value;

  if (!nombre) { showFieldError('input-modulo', 'Ingrese un nombre'); return; }
  clearFieldErrors('input-modulo');

  const data = await api('/api/modulos', {
    method: 'POST',
    body: JSON.stringify({
      nombre,
      capacidad_maxima: capacidad ? parseInt(capacidad) : null,
      ubicacion: ubicacion || null,
      supervisor: supervisor || null,
      estado
    }),
    _btn: event.target
  });

  if (data) {
    document.getElementById('input-modulo').value = '';
    document.getElementById('input-modulo-cap').value = '';
    document.getElementById('input-modulo-ubic').value = '';
    document.getElementById('input-modulo-sup').value = '';
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
          <td>${h.turno ? `<span class="badge badge-hour">${h.turno}</span>` : '-'}</td>
        </tr>
      `;
    });
  }
}

async function guardarHora() {
  const nombre = document.getElementById('input-hora').value.trim();
  const horaInicio = document.getElementById('input-hora-inicio').value;
  const horaFin = document.getElementById('input-hora-fin').value;
  const turno = document.getElementById('input-hora-turno').value;

  if (!nombre) { showFieldError('input-hora', 'Ingrese un nombre'); return; }
  clearFieldErrors('input-hora');

  const data = await api('/api/horas', {
    method: 'POST',
    body: JSON.stringify({
      nombre,
      hora_inicio: horaInicio || null,
      hora_fin: horaFin || null,
      turno: turno || null
    }),
    _btn: event.target
  });

  if (data) {
    document.getElementById('input-hora').value = '';
    document.getElementById('input-hora-inicio').value = '';
    document.getElementById('input-hora-fin').value = '';
    document.getElementById('input-hora-turno').value = '';
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
      tbody.innerHTML += `
        <tr>
          <td>${e.numero_documento}</td>
          <td><strong>${e.nombre}</strong></td>
          <td>${e.cargo}</td>
          <td>${e.especialidad || '-'}</td>
          <td>${e.turno || '-'}</td>
          <td>${e.nombre_modulo ? `<span class="badge badge-module">${e.nombre_modulo}</span>` : 'Sin asignar'}</td>
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

async function cargarSelectModulos() {
  const datos = await api('/api/modulos');
  if (!datos) return;

  const select = document.getElementById('input-emp-modulo');
  const valActual = select.value;
  select.innerHTML = '<option value="">Sin asignar</option>';
  datos.forEach(m => {
    select.innerHTML += `<option value="${m.id}">${m.nombre}</option>`;
  });
  if (valActual) select.value = valActual;
}

function limpiarFormEmpleado() {
  idEmpleadoEnEdicion = null;
  document.getElementById('empleado-id-edicion').value = '';
  document.getElementById('input-emp-nombre').value = '';
  document.getElementById('input-emp-doc').value = '';
  document.getElementById('input-emp-cargo').value = '';
  document.getElementById('input-emp-especialidad').value = '';
  document.getElementById('input-emp-turno').value = '';
  document.getElementById('input-emp-fecha').value = '';
  document.getElementById('input-emp-estado').value = 'Activo';
  document.getElementById('input-emp-tel').value = '';
  document.getElementById('input-emp-email').value = '';
  document.getElementById('input-emp-modulo').value = '';
  const btn = document.getElementById('btn-empleado');
  btn.textContent = 'Guardar Empleado';
  btn.style.background = '';
}

async function procesarEmpleado() {
  const nombre = document.getElementById('input-emp-nombre').value.trim();
  const numero_documento = document.getElementById('input-emp-doc').value.trim();
  const cargo = document.getElementById('input-emp-cargo').value;
  const especialidad = document.getElementById('input-emp-especialidad').value;
  const turno = document.getElementById('input-emp-turno').value;
  const fecha_ingreso = document.getElementById('input-emp-fecha').value;
  const estado = document.getElementById('input-emp-estado').value;
  const telefono = document.getElementById('input-emp-tel').value.trim();
  const email = document.getElementById('input-emp-email').value.trim();
  const modulo_asignado = document.getElementById('input-emp-modulo').value;

  let valid = true;
  if (!nombre) { showFieldError('input-emp-nombre', 'Campo requerido'); valid = false; }
  else { clearFieldErrors('input-emp-nombre'); }

  if (!numero_documento) { showFieldError('input-emp-doc', 'Campo requerido'); valid = false; }
  else { clearFieldErrors('input-emp-doc'); }

  if (!cargo) { showFieldError('input-emp-cargo', 'Seleccione un cargo'); valid = false; }
  else { clearFieldErrors('input-emp-cargo'); }

  if (!valid) return;

  const payload = {
    nombre,
    numero_documento,
    cargo,
    especialidad: especialidad || null,
    turno: turno || null,
    fecha_ingreso: fecha_ingreso || null,
    estado,
    telefono: telefono || null,
    email: email || null,
    modulo_asignado: modulo_asignado ? parseInt(modulo_asignado) : null
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
  }
}

function iniciarEdicionEmpleado(e) {
  idEmpleadoEnEdicion = e.id;
  document.getElementById('empleado-id-edicion').value = e.id;
  document.getElementById('input-emp-nombre').value = e.nombre;
  document.getElementById('input-emp-doc').value = e.numero_documento;
  document.getElementById('input-emp-cargo').value = e.cargo;
  document.getElementById('input-emp-especialidad').value = e.especialidad || '';
  document.getElementById('input-emp-turno').value = e.turno || '';
  document.getElementById('input-emp-fecha').value = e.fecha_ingreso || '';
  document.getElementById('input-emp-estado').value = e.estado || 'Activo';
  document.getElementById('input-emp-tel').value = e.telefono || '';
  document.getElementById('input-emp-email').value = e.email || '';
  document.getElementById('input-emp-modulo').value = e.modulo_asignado || '';

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
  document.getElementById('op-nombre').value = operacion.nombre;
  document.getElementById('op-tiempo').value = operacion.tiempo;
  document.getElementById('op-maquina').value = operacion.id_maquina;
  document.getElementById('op-seccion').value = operacion.id_seccion;

  const btn = document.getElementById('btn-operacion');
  btn.textContent = 'Actualizar Operación';
  btn.style.background = 'var(--accent-blue)';

  document.querySelector('#mod-operaciones .section-title-container').scrollIntoView({ behavior: 'smooth' });
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
    item.className = `reference-item ${referenciaActivaId === ref.id ? 'active' : ''}`;
    item.onclick = (e) => {
      if (!e.target.closest('button')) seleccionarReferencia(ref.id, ref.nombre);
    };

    const objStr = JSON.stringify(ref).replace(/'/g, "\\'").replace(/"/g, '&quot;');
    const badges = [];
    if (ref.foto) badges.push('<span class="badge badge-module" title="Tiene foto">📷</span>');
    if (ref.especificaciones) badges.push('<span class="badge badge-hour" title="Tiene especificaciones">📝</span>');
    item.innerHTML = `
      <div style="display:flex; flex-direction:column; flex:1; min-width:0;">
        <span style="font-weight:600;">${ref.nombre}</span>
        <span style="display:flex; gap:4px; margin-top:4px;">${badges.join('') || ''}</span>
        <span class="reference-view-hint ${referenciaActivaId === ref.id ? 'visible' : ''}">Ver diagrama de actividades →</span>
      </div>
      <div style="display:flex; gap: 5px; align-items:center;">
        <button class="btn-icon btn-edit" style="padding:4px 8px;" onclick="iniciarEdicionReferencia(${objStr})" title="Editar">✎</button>
        <button class="btn-icon btn-edit" style="padding:4px 8px;" onclick="duplicarReferencia(${ref.id}, '${ref.nombre}')" title="Duplicar">⧉</button>
        <button class="btn-icon btn-delete" style="padding:4px 8px;" onclick="eliminarReferencia(${ref.id})" title="Eliminar">✕</button>
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
  const nombre = document.getElementById('input-ref-nombre').value.trim();
  const especificaciones = document.getElementById('input-ref-espec').value.trim();

  if (!nombre) { showFieldError('input-ref-nombre', 'Ingrese un nombre'); return; }
  clearFieldErrors('input-ref-nombre');

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
    _btn: event.target
  });

  if (data) {
    if (data.id) idRef = data.id;

    // Subir la foto si eligió archivo
    const inputFoto = document.getElementById('input-ref-foto');
    if (inputFoto && inputFoto.files && inputFoto.files[0] && idRef) {
      await subirFotoReferencia(idRef, inputFoto.files[0]);
    }

    limpiarFormularioReferencia();
    Toast.success(data.mensaje || 'Referencia guardada');
    cargarReferencias();
    cargarSelectOrdenesRef();
  }
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

function iniciarEdicionReferencia(ref) {
  idReferenciaEnEdicion = ref.id;
  document.getElementById('input-ref-nombre').value = ref.nombre;
  document.getElementById('input-ref-espec').value = ref.especificaciones || '';
  document.getElementById('input-ref-foto').value = '';

  const btn = document.querySelector('#input-ref-nombre').parentElement.querySelector('button');
  if (btn) btn.innerText = 'Actualizar Referencia';
}

function limpiarFormularioReferencia() {
  idReferenciaEnEdicion = null;
  document.getElementById('input-ref-nombre').value = '';
  document.getElementById('input-ref-espec').value = '';
  document.getElementById('input-ref-foto').value = '';
  const preview = document.getElementById('preview-ref-foto');
  if (preview) { preview.style.display = 'none'; preview.src = ''; }
  const btn = document.querySelector('#input-ref-nombre').parentElement.querySelector('button');
  if (btn) btn.innerText = 'Crear Referencia';
}

async function eliminarReferencia(id) {
  const ok = await Modal.confirm('Eliminar Referencia', '¿Eliminar esta referencia y toda su secuencia de operaciones?');
  if (!ok) return;

  const data = await api(`/api/referencias/${id}`, { method: 'DELETE' });
  if (data) {
    if (referenciaActivaId === id) {
      resetPanelSecuencia();
    }
    Toast.success('Referencia eliminada');
    cargarReferencias();
  }
}

function resetPanelSecuencia() {
  referenciaActivaId = null;
  document.getElementById('titulo-ref-activa').style.display = 'none';
  document.getElementById('empty-secuencia-placeholder').style.display = 'flex';
  document.getElementById('secuencia-content').style.display = 'none';
  document.getElementById('lista-secuencia').innerHTML = '';
  const ficha = document.getElementById('ficha-tecnica-container');
  if (ficha) ficha.style.display = 'none';
}

async function duplicarReferencia(id, nombreActual) {
  const nuevoNombre = prompt('Nombre para la nueva referencia:', 'Copia de ' + nombreActual);
  if (!nuevoNombre) return;

  const data = await api(`/api/referencias/${id}/duplicar`, {
    method: 'POST',
    body: JSON.stringify({ nombre: nuevoNombre })
  });

  if (data) {
    Toast.success('Referencia duplicada');
    cargarReferencias();
  }
}

function cambiarTabReferencia(tab) {
  const esBom = tab === 'bom';
  document.getElementById('tab-secuencia').classList.toggle('active', !esBom);
  document.getElementById('tab-bom').classList.toggle('active', esBom);
  document.getElementById('detail-secuencia').style.display = esBom ? 'none' : 'block';
  document.getElementById('detail-bom').style.display = esBom ? 'block' : 'none';
  if (esBom) cargarMaterialesReferencia(referenciaActivaId);
}

function toggleFormNuevaReferencia() {
  const form = document.getElementById('form-nueva-ref');
  const btn = document.getElementById('btn-nueva-ref');
  if (form.style.display === 'none') {
    form.style.display = 'block';
    btn.textContent = '− Cerrar';
  } else {
    form.style.display = 'none';
    btn.textContent = '+ Nueva Referencia';
    limpiarFormularioReferencia();
  }
}

function previewFotoNueva(input) {
  const preview = document.getElementById('preview-ref-foto');
  if (input.files && input.files[0]) {
    preview.src = URL.createObjectURL(input.files[0]);
    preview.style.display = 'block';
  } else {
    preview.style.display = 'none';
    preview.src = '';
  }
}

async function cambiarFotoPrototipo(input) {
  if (!referenciaActivaId) return;
  if (!input.files || !input.files[0]) return;

  const formData = new FormData();
  formData.append('foto', input.files[0]);
  try {
    const res = await fetch(`/api/referencias/${referenciaActivaId}/foto`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (res.ok) {
      Toast.success('Foto del prototipo actualizada');
      input.value = '';
      cargarFichaTecnica(referenciaActivaId);
      cargarReferencias();
    } else {
      Toast.error(data.error || 'Error al subir la foto');
    }
  } catch (e) {
    Toast.error('Error al subir la foto');
  }
}

async function seleccionarReferencia(id, nombre) {
  referenciaActivaId = id;
  document.getElementById('titulo-ref-activa').innerText = `Diagrama de Actividades: ${nombre}`;
  document.getElementById('titulo-ref-activa').style.display = 'block';
  document.getElementById('empty-secuencia-placeholder').style.display = 'none';
  document.getElementById('secuencia-content').style.display = 'block';
  cargarReferencias();
  await cargarDetallesReferencia(id);
  cargarOperacionesSelect();
  cargarFichaTecnica(id);
  cargarMaterialesReferencia(id);
  cargarMateriales();
}

async function cargarFichaTecnica(idRef) {
  const data = await api('/api/referencias');
  if (!data) return;
  const ref = data.find(r => r.id === idRef);
  if (!ref) return;

  const container = document.getElementById('ficha-tecnica-container');
  container.style.display = 'flex';

  const img = document.getElementById('ficha-foto-img');
  const empty = document.getElementById('ficha-foto-empty');
  if (ref.foto) {
    img.src = ref.foto;
    img.style.display = 'block';
    empty.style.display = 'none';
  } else {
    img.style.display = 'none';
    empty.style.display = 'block';
  }

  document.getElementById('ficha-especificaciones').textContent = ref.especificaciones || 'Sin especificaciones.';
}

async function cargarDetallesReferencia(idRef) {
  const data = await api(`/api/referencias/${idRef}/detalles`);
  if (!data) return;

  const tbody = document.getElementById('lista-secuencia');
  tbody.innerHTML = '';
  secuenciaActualLength = data.length;

  document.getElementById('empty-secuencia').style.display = data.length === 0 ? 'block' : 'none';

  const nextChar = String.fromCharCode(65 + secuenciaActualLength);
  document.getElementById('seq-letra').value = nextChar;
  document.getElementById('seq-pred').value = secuenciaActualLength > 0 ? data[data.length - 1].letra : 'N/A';

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

async function cargarOperacionesSelect() {
  const data = await api('/api/operaciones');
  if (!data) return;

  const select = document.getElementById('seq-operacion');
  select.innerHTML = '';
  data.forEach(o => {
    select.innerHTML += `<option value="${o.id}">${o.nombre} (${formatTime(o.tiempo)})</option>`;
  });
}

async function agregarDetalle() {
  if (!referenciaActivaId) return;

  const id_operacion = document.getElementById('seq-operacion').value;
  const letra = document.getElementById('seq-letra').value.toUpperCase();
  const predecesoras = document.getElementById('seq-pred').value.toUpperCase();

  if (!letra) { Toast.warning('Falta la letra de secuencia'); return; }

  const data = await api(`/api/referencias/${referenciaActivaId}/detalles`, {
    method: 'POST',
    body: JSON.stringify({
      id_operacion: parseInt(id_operacion),
      letra,
      predecesoras,
      orden: secuenciaActualLength + 1
    }),
    _btn: event.target
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

function finalizarReferencia() {
  resetPanelSecuencia();
  Toast.success('Referencia guardada correctamente');
  cargarReferencias();
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
      const estadoClass = o.estado === 'Abierta' ? 'badge-module' : (o.estado === 'Cerrada' ? 'badge-machine' : 'badge-hour');
      tbody.innerHTML += `
        <tr>
          <td><strong>${o.nombre_orden}</strong></td>
          <td>${o.referencia}</td>
          <td class="text-accent">${o.cantidad_lote}</td>
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
  const select = document.getElementById('bom-material');

  tbody.innerHTML = '';
  let valSelect = null;
  if (select) valSelect = select.value;
  if (select) select.innerHTML = '<option value="">Seleccione material...</option>';

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
      if (select) {
        select.innerHTML += `<option value="${m.id}">${m.nombre}</option>`;
      }
    });
  }
  if (select && valSelect) select.value = valSelect;
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

async function cargarMaterialesReferencia(idRef) {
  const data = await api(`/api/referencias/${idRef}/materiales`);
  if (!data) return;

  const tbody = document.getElementById('lista-bom');
  const empty = document.getElementById('empty-bom');
  tbody.innerHTML = '';
  if (data.length === 0) {
    empty.style.display = 'block';
  } else {
    empty.style.display = 'none';
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
}

async function agregarMaterialReferencia() {
  if (!referenciaActivaId) return;

  const idMaterial = document.getElementById('bom-material').value;
  const cantidad = document.getElementById('bom-cantidad').value;
  const merma = document.getElementById('bom-merma').value;

  if (!idMaterial) { Toast.warning('Seleccione un material'); return; }
  if (!cantidad || isNaN(cantidad) || Number(cantidad) <= 0) { Toast.warning('Ingrese cantidad por unidad'); return; }

  const data = await api(`/api/referencias/${referenciaActivaId}/materiales`, {
    method: 'POST',
    body: JSON.stringify({
      id_material: parseInt(idMaterial),
      cantidad_por_unidad: parseFloat(cantidad),
      merma_porcentaje: parseFloat(merma) || 0
    }),
    _btn: event.target
  });

  if (data) {
    Toast.success('Material asociado a la referencia');
    document.getElementById('bom-cantidad').value = '';
    document.getElementById('bom-merma').value = '';
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

  const selMod = document.getElementById('prog-modulo');
  const modActual = selMod.value;
  selMod.innerHTML = '<option value="">Seleccione Módulo...</option>';
  dataMod.forEach(m => {
    selMod.innerHTML += `<option value="${m.id}">${m.nombre}</option>`;
  });

  if (valActual) selRef.value = valActual;
  if (modActual) selMod.value = modActual;
}

async function verificarDisponibilidad() {
  const idOrden = document.getElementById('prog-referencia').value;
  const label = document.getElementById('prog-disponibilidad');
  const hint = document.getElementById('prog-cantidad-hint');

  if (!idOrden || idOrden === '-1') {
    if (idOrden === '-1') return;
    label.innerText = 'Disponible: - / Total: -';
    if (hint) hint.innerText = '';
    return;
  }

  const data = await api(`/api/ordenes/${idOrden}/disponibilidad`);
  if (data) {
    label.innerText = `Disponible: ${data.disponible} / Total: ${data.total}`;
    if (hint) {
      hint.innerText = `(Disp: ${data.disponible})`;
      if (data.disponible <= 0) {
        hint.style.color = 'var(--accent-danger)';
        label.style.color = 'var(--accent-danger)';
      } else {
        hint.style.color = 'var(--accent-success)';
        label.style.color = 'var(--text-secondary)';
      }
    }
  }
}

async function guardarAsignacion() {
  const idOrden = document.getElementById('prog-referencia').value;
  const idMod = document.getElementById('prog-modulo').value;
  const cant = document.getElementById('prog-cantidad').value;

  let valid = true;
  if (!idOrden) { showFieldError('prog-referencia', 'Seleccione una orden'); valid = false; }
  else { clearFieldErrors('prog-referencia'); }

  if (!idMod) { showFieldError('prog-modulo', 'Seleccione módulo'); valid = false; }
  else { clearFieldErrors('prog-modulo'); }

  if (!cant || isNaN(cant) || Number(cant) <= 0) { showFieldError('prog-cantidad', 'Cantidad inválida'); valid = false; }
  else { clearFieldErrors('prog-cantidad'); }

  if (!valid) return;

  if (idAsignacionEnEdicion) {
    const data = await api(`/api/asignaciones/${idAsignacionEnEdicion}`, {
      method: 'PUT',
      body: JSON.stringify({ cantidad: parseInt(cant) }),
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

  const data = await api('/api/asignaciones', {
    method: 'POST',
    body: JSON.stringify({
      id_orden: parseInt(idOrden),
      id_modulo: parseInt(idMod),
      cantidad: parseInt(cant)
    }),
    _btn: event.target
  });

  if (data) {
    document.getElementById('prog-cantidad').value = '';
    Toast.success(data.mensaje || 'Asignación guardada');
    verificarDisponibilidad();
    cargarAsignaciones();
    cargarDatosProgramacion();
  }
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

  const btn = document.querySelector('#mod-programacion .btn-primary');
  btn.textContent = 'Actualizar Asignación';
  btn.style.backgroundColor = 'var(--accent-blue)';

  document.getElementById('prog-cantidad').value = cantidad;

  const selRef = document.getElementById('prog-referencia');
  const selMod = document.getElementById('prog-modulo');
  selRef.disabled = true;
  selMod.disabled = true;

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

  let foundMod = false;
  for (let op of selMod.options) {
    if (op.text === nombreMod) { selMod.value = op.value; foundMod = true; break; }
  }
  if (!foundMod) {
    const opt = document.createElement('option');
    opt.text = nombreMod;
    opt.value = '-1';
    opt.selected = true;
    selMod.add(opt);
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
  document.getElementById('prog-cantidad').value = '';
  document.getElementById('prog-referencia').disabled = false;
  document.getElementById('prog-modulo').disabled = false;

  const btn = document.querySelector('#mod-programacion .btn-primary');
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

async function initControlHora() {
  const mods = await api('/api/modulos');
  if (!mods) return;

  const selMod = document.getElementById('ctrl-modulo');
  selMod.innerHTML = '<option value="">Seleccione Módulo...</option>';
  mods.forEach(m => selMod.innerHTML += `<option value="${m.id}">${m.nombre}</option>`);

  document.getElementById('ctrl-fecha').valueAsDate = new Date();

  const selHora = document.getElementById('ctrl-hora');
  selHora.innerHTML = '';
  ['Hora 1', 'Hora 2', 'Hora 3', 'Hora 4', 'Hora 5', 'Hora 6', 'Hora 7', 'Hora 8', 'Hora 9', 'Hora Extra'].forEach((h, i) => {
    selHora.innerHTML += `<option value="${i + 1}">${h}</option>`;
  });

  const selParada = document.getElementById('ctrl-parada-p');
  selParada.innerHTML = '';
  catalogoParadasCache.forEach(p => {
    selParada.innerHTML += `<option value="${p.id}">${p.nombre}</option>`;
  });
  actualizarTiempoParadaP();

  cargarControlesHoy();
}

async function cargarReferenciasPorModulo() {
  const idMod = document.getElementById('ctrl-modulo').value;
  const selRef = document.getElementById('ctrl-referencia');

  if (!idMod) {
    selRef.innerHTML = '<option value="">Seleccione Módulo primero...</option>';
    selRef.disabled = true;
    return;
  }

  const refs = await api(`/api/modulos/${idMod}/referencias-asignadas`);
  if (!refs) return;

  selRef.innerHTML = '<option value="">Seleccione Asignación...</option>';
  refs.forEach(r => {
    const etiqueta = r.nombre_orden ? `${r.nombre_orden} - ${r.nombre}` : r.nombre;
    selRef.innerHTML += `<option value="${r.id}" data-ref-id="${r.id_referencia}">${etiqueta}</option>`;
  });
  selRef.disabled = false;

  const prevVal = selRef.getAttribute('data-prev-val');
  if (prevVal) {
    selRef.value = prevVal;
    selRef.removeAttribute('data-prev-val');
    actualizarOpcionesCiclo();
  }
}

function actualizarTiempoParadaP() {
  const idParada = parseInt(document.getElementById('ctrl-parada-p').value);
  const parada = catalogoParadasCache.find(p => p.id === idParada);
  document.getElementById('ctrl-tiempo-p').value = parada ? parada.tiempo : 0;
}

async function guardarControlHora() {
  const fecha = document.getElementById('ctrl-fecha').value;
  const idMod = document.getElementById('ctrl-modulo').value;
  const operarios = document.getElementById('ctrl-operarios').value;
  const idAsignacion = document.getElementById('ctrl-referencia').value;
  const idHora = document.getElementById('ctrl-hora').value;
  const porcion = document.getElementById('ctrl-porcion').value;
  const cantidad = document.getElementById('ctrl-cantidad').value;
  const idParadaP = document.getElementById('ctrl-parada-p').value;
  const tiempoP = document.getElementById('ctrl-tiempo-p').value;
  const descNP = document.getElementById('ctrl-parada-np').value;
  const tiempoNP = document.getElementById('ctrl-tiempo-np').value;

  let valid = true;
  if (!fecha) { showFieldError('ctrl-fecha', 'Requerido'); valid = false; } else { clearFieldErrors('ctrl-fecha'); }
  if (!idMod) { showFieldError('ctrl-modulo', 'Requerido'); valid = false; } else { clearFieldErrors('ctrl-modulo'); }
  if (!idAsignacion) { showFieldError('ctrl-referencia', 'Requerido'); valid = false; } else { clearFieldErrors('ctrl-referencia'); }
  if (!idHora) { showFieldError('ctrl-hora', 'Requerido'); valid = false; } else { clearFieldErrors('ctrl-hora'); }
  if (!cantidad || isNaN(cantidad)) { showFieldError('ctrl-cantidad', 'Ingrese cantidad'); valid = false; } else { clearFieldErrors('ctrl-cantidad'); }

  if (!valid) return;

  const payload = {
    fecha,
    id_modulo: parseInt(idMod),
    id_asignacion: parseInt(idAsignacion),
    id_hora: parseInt(idHora),
    porcion_tiempo: parseFloat(porcion),
    cantidad_producida: parseInt(cantidad),
    cantidad_operarios: operarios ? parseFloat(operarios) : 0,
    id_parada_programada: parseInt(idParadaP),
    tiempo_parada_programada: parseInt(tiempoP),
    descripcion_parada_no_programada: descNP,
    tiempo_parada_no_programada: tiempoNP ? parseInt(tiempoNP) : 0
  };

  let url = '/api/control-hora';
  let method = 'POST';
  const idEdicion = document.getElementById('ctrl-id-edicion').value;
  if (idEdicion) {
    url = `/api/control-hora/${idEdicion}`;
    method = 'PUT';
  }

  const data = await api(url, {
    method,
    body: JSON.stringify(payload),
    _btn: event.target
  });

  if (data) {
    Toast.success(data.mensaje || 'Registro guardado');
    cancelarEdicionControl();
    cargarControlesHoy();
  }
}

async function cargarControlesHoy() {
  const fecha = document.getElementById('ctrl-fecha').value || new Date().toISOString().split('T')[0];
  const data = await api(`/api/control-hora/hoy?fecha=${fecha}`);
  if (!data) return;

  const tbody = document.getElementById('lista-controles');
  tbody.innerHTML = '';
  document.getElementById('empty-controles').style.display = data.length === 0 ? 'block' : 'none';

  data.forEach(c => {
    tbody.innerHTML += `
      <tr>
        <td><span class="badge badge-hour">${c.hora}</span></td>
        <td>${c.modulo}</td>
        <td>${c.referencia}</td>
        <td class="text-accent">${formatTime(c.tc)}</td>
        <td>${c.cantidad}</td>
        <td title="${c.parada}">${formatTime(c.tiempo_p)}</td>
        <td title="${c.descripcion_parada_no_programada || 'Sin descripción'}">${formatTime(c.tiempo_np)}</td>
        <td class="action-buttons">
          <button class="btn-icon btn-edit" onclick='editarControlHora(${JSON.stringify(c)})'>✎</button>
          <button class="btn-icon btn-delete" onclick="eliminarControlHora(${c.id})">✕</button>
        </td>
      </tr>
    `;
  });
}

async function eliminarControlHora(id) {
  const ok = await Modal.confirm('Eliminar Registro', '¿Eliminar este registro de producción?');
  if (!ok) return;

  const data = await api(`/api/control-hora/${id}`, { method: 'DELETE' });
  if (data) {
    Toast.success('Registro eliminado');
    cargarControlesHoy();
  }
}

function cancelarEdicionControl() {
  document.getElementById('ctrl-id-edicion').value = '';
  document.getElementById('ctrl-operarios').value = '';
  document.getElementById('ctrl-cantidad').value = '';
  document.getElementById('ctrl-parada-np').value = '';
  document.getElementById('ctrl-tiempo-np').value = '';
  document.getElementById('ctrl-modulo').value = '';
  document.getElementById('ctrl-hora').value = '';
  document.getElementById('ctrl-porcion').value = '1.0';
  document.getElementById('ctrl-parada-p').value = '';
  document.getElementById('ctrl-tiempo-p').value = '';

  const selRef = document.getElementById('ctrl-referencia');
  selRef.value = '';
  selRef.innerHTML = '<option value="">Seleccione Módulo primero...</option>';
  selRef.disabled = true;

  const btn = document.querySelector('#mod-control-hora .btn-primary');
  if (btn) btn.textContent = 'Guardar Registro';
}

async function editarControlHora(c) {
  document.getElementById('ctrl-id-edicion').value = c.id;
  document.getElementById('ctrl-fecha').value = c.fecha;
  document.getElementById('ctrl-modulo').value = c.id_modulo;
  await cargarReferenciasPorModulo();
  document.getElementById('ctrl-referencia').value = c.id_asignacion;
  document.getElementById('ctrl-hora').value = c.id_hora;
  document.getElementById('ctrl-operarios').value = c.cantidad_operarios || '';
  document.getElementById('ctrl-porcion').value = c.porcion_tiempo;
  document.getElementById('ctrl-cantidad').value = c.cantidad_producida;
  document.getElementById('ctrl-parada-p').value = c.id_parada_programada;
  actualizarTiempoParadaP();
  document.getElementById('ctrl-parada-np').value = c.descripcion_parada_no_programada || '';
  document.getElementById('ctrl-tiempo-np').value = c.tiempo_parada_no_programada || '';

  const btn = document.querySelector('#mod-control-hora .btn-primary');
  if (btn) btn.textContent = 'Actualizar Registro';

  document.getElementById('mod-control-hora').scrollIntoView({ behavior: 'smooth' });
}

async function actualizarOpcionesCiclo() {
  const selRef = document.getElementById('ctrl-referencia');
  const numOps = document.getElementById('ctrl-operarios').value;
  const selCiclo = document.getElementById('ctrl-ciclo');

  const idRefOption = selRef.options[selRef.selectedIndex];
  const idReferenciaReal = idRefOption ? idRefOption.getAttribute('data-ref-id') : null;

  if (!idReferenciaReal || !numOps) {
    selCiclo.innerHTML = '<option value="">Faltan datos...</option>';
    return;
  }

  selCiclo.innerHTML = '<option value="">Calculando...</option>';

  try {
    const res = await fetch('/api/balanceo/calcular', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_referencia: parseInt(idReferenciaReal), num_operarios: parseInt(numOps) })
    });

    if (!res.ok) {
      selCiclo.innerHTML = '<option value="">Error en cálculo</option>';
      return;
    }

    const data = await res.json();
    const cicloSec = Math.round(data.secuencial.kpis.tiempo_ciclo * parseFloat(numOps));
    const cicloEff = Math.round(data.eficiencia.kpis.tiempo_ciclo * parseFloat(numOps));

    selCiclo.innerHTML = `
      <option value="${cicloSec}">${formatTime(cicloSec)} (Secuencial)</option>
      <option value="${cicloEff}">${formatTime(cicloEff)} (Eficiencia)</option>
    `;
  } catch (e) {
    selCiclo.innerHTML = '<option value="">Error de conexión</option>';
  }
}

// ============================================================
// TABLERO DE EFICIENCIAS
// ============================================================

async function consultarEficiencia() {
  const startDate = document.getElementById('eff-fecha-inicio').value;
  const endDate = document.getElementById('eff-fecha-fin').value;
  const container = document.getElementById('eff-reporte-container');

  if (!startDate || !endDate) { Toast.warning('Seleccione el rango de fechas'); return; }

  container.innerHTML = '<div class="empty-state" style="text-align:center; padding: 40px;">Procesando datos...</div>';

  try {
    const data = await api(`/api/reportes/eficiencia?fecha_inicio=${startDate}&fecha_fin=${endDate}`);
    if (!data) return;

    if (data.reporte.length === 0) {
      container.innerHTML = '<div class="empty-state" style="text-align:center; padding: 40px;">No hay registros para este periodo.</div>';
      return;
    }

    renderizarTablaEficiencia(data);
  } catch (e) {
    container.innerHTML = '<div class="empty-state" style="text-align:center; padding: 40px; color:var(--accent-danger);">Error de conexión.</div>';
  }
}

function renderizarTablaEficiencia(data) {
  const container = document.getElementById('eff-reporte-container');
  const modulos = data.modulos;
  const reporte = data.reporte;

  let html = `<table class="report-table"><thead><tr><th rowspan="2" class="header-hora">HORA</th>`;
  modulos.forEach(mod => { html += `<th colspan="3">${mod}</th>`; });
  html += `<th colspan="3" class="col-total">TOTAL PLANTA</th></tr><tr>`;
  modulos.forEach(() => { html += `<th>CANT</th><th>META</th><th>EFF</th>`; });
  html += `<th class="col-total">CANT</th><th class="col-total">META</th><th class="col-total">EFF</th></tr></thead><tbody>`;

  reporte.forEach(row => {
    html += `<tr><td class="header-hora">${row.hora}</td>`;
    modulos.forEach(mod => {
      const d = row.datos_modulos[mod] || { cantidad: 0, meta: 0, eficiencia: 0 };
      html += `<td>${d.cantidad}</td><td>${d.meta}</td><td class="cell-eff ${obtenerClaseEficiencia(d.eficiencia)}">${d.eficiencia}%</td>`;
    });
    const t = row.total_planta;
    html += `<td class="col-total">${t.cantidad}</td><td class="col-total">${t.meta}</td><td class="col-total cell-eff ${obtenerClaseEficiencia(t.eficiencia)}">${t.eficiencia}%</td></tr>`;
  });

  html += '</tbody></table>';
  container.innerHTML = html;
}

function obtenerClaseEficiencia(v) {
  if (v >= 100) return 'bg-eff-super';
  if (v >= 90) return 'bg-eff-good';
  if (v >= 80) return 'bg-eff-warn';
  return 'bg-eff-critical';
}

// ============================================================
// SIMULADOR DE BALANCEO
// ============================================================

let resultadoSimulacionGlobal = null;

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
  cargarMaquinaria();
  cargarSecciones();
  cargarModulos();
  cargarEmpleados();
  cargarSelectModulos();
  cargarMateriales();
  cargarHoras();
  cargarParadas();
  cargarOperaciones();
  cargarReferencias();
  cargarOrdenes();
  cargarSelectOrdenesRef();
  cargarDatosProgramacion();
  cargarAsignaciones();
});
