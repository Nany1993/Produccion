# Sistema de Balanceo de Producción

Sistema web para gestión y balanceo de líneas de producción en plantas de confección de gorras.

---

## Stack

| Capa | Tecnología |
|------|------------|
| Backend | Python 3.8+ / Flask |
| Base de datos | SQLite |
| Frontend | HTML5 + CSS3 + JavaScript vanilla |
| Puerto | 8000 |

## Estructura

```
├── main.py            # Servidor Flask + rutas API REST
├── database.py        # Capa de acceso a datos (toda la SQL vive aquí)
├── engine.py          # Algoritmo de balanceo de línea
├── seed_data.py       # Generador de datos de ejemplo
├── index.html         # Interfaz de usuario
├── style.css          # Estilos
├── app.js             # Lógica del frontend
├── schema.dbml        # Modelo de datos para dbdiagram.io
└── DOCUMENTACION.md   # Documentación de la API
```

## Instalación

```bash
git clone https://github.com/Nany1993/Produccion.git
cd Produccion
pip install flask
python seed_data.py      # datos de ejemplo (opcional)
python main.py           # http://localhost:8000
```

Credenciales por defecto: `admin` / `1234` (Admin).

---

## Arquitectura de datos

Base de datos SQLite con **19 tablas** y foreign keys habilitadas en todas las conexiones de runtime.

El modelo se divide en 5 dominios:

1. **Fábrica** — módulos, máquinas, secciones, horas, paradas
2. **Personas** — empleados, usuarios, asignaciones de línea
3. **Ingeniería** — referencias (productos), operaciones, materiales, BOM
4. **Producción** — órdenes, asignaciones, registro real, paradas
5. **Control** — control por hora, configuración del sistema

---

### Dominio: Fábrica

Define la planta física: dónde se produce, con qué máquinas, en qué secciones, durante cuánto tiempo.

---

#### `ModuloConfeccion`

Línea de producción. Un módulo tiene un conjunto de máquinas, operarios y opera como una unidad independiente.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `nombre` | TEXT | NOT NULL | Nombre de la línea (ej: "Línea A") |
| `capacidad_maxima` | INTEGER | | Máximo de operarios que puede albergar |
| `ubicacion` | TEXT | | Ubicación física en la planta |
| `estado` | TEXT | | "activo" / "inactivo" |

**Relaciones:**
- Una máquina (`Maquinas.id_modulo`) apunta a un módulo.
- Un empleado se asigna a una máquina; el módulo se deduce de la máquina (cadena: Empleado → Máquina → Módulo).
- Una orden se asigna a un módulo vía `AsignacionModulo`.

---

#### `Maquinas`

Máquina disponible en la planta. Puede ser fija a un módulo o compartida.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `nombre` | INTEGER | NOT NULL | Nombre del tipo de máquina |
| `descripcion` | TEXT | | Descripción técnica |
| `velocidad_tipica` | INTEGER | | Velocidad estándar (unidades/minuto) |
| `estado` | TEXT | | "activa" / "inactiva" |
| `id_modulo` | INTEGER | FK → ModuloConfeccion | Módulo al que pertenece (nullable) |
| `marca` | TEXT | | Marca del fabricante |
| `modelo` | TEXT | | Modelo específico |
| `serial` | TEXT | | Número de serie |
| `codigo_inventario` | TEXT | | Código de inventario interno |
| `ubicacion` | TEXT | | Ubicación física en la planta |

**Relaciones:**
- Una máquina pertenece a **un solo módulo** (FK único, no many-to-many).
- Una operación puede requerir una máquina específica (`Operacion.id_maquina`).
- Un empleado puede estar asignado a una máquina (`Empleados.id_maquina`).

---

#### `SeccionPrenda`

Secciones de la gorra (ala, corona, cierre, bordado, etc.). Determinan el orden de proceso de las operaciones.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `nombre` | TEXT | NOT NULL | Nombre de la sección |
| `descripcion` | TEXT | | Detalle de la sección |
| `orden_proceso` | INTEGER | | Orden en el flujo de producción |

**Relaciones:**
- Una operación pertenece a una sección (`Operacion.id_seccion`).

---

#### `HorasProduccion`

Franjas horarias del turno de producción. Cada registro representa una hora del día laboral.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `nombre` | TEXT | NOT NULL | Nombre de la hora (ej: "Hora 1") |
| `hora_inicio` | TEXT | | Inicio de la franja (ej: "06:00") |
| `hora_fin` | TEXT | | Fin de la franja (ej: "07:00") |

**Relaciones:**
- El control por hora (`ControlHoraHora.id_hora`) apunta a una hora.

---

#### `ParadasProgramadas`

Paradas oficiales de la jornada: refrigerios, almuerzo, limpieza, etc.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `nombre` | TEXT | NOT NULL | Nombre de la parada (ej: "Refrigerio") |
| `tiempo_segundos` | INTEGER | NOT NULL | Duración en segundos |
| `tipo` | TEXT | | "programada" / "extraordinaria" |
| `frecuencia` | TEXT | | "diaria", "semanal", etc. |

**Relaciones:**
- El control por hora (`ControlHoraHora.id_parada_programada`) registra cuál parada se aplicó.
- `ParadaRegistro` también apunta aquí si la parada fue programada.

---

### Dominio: Personas

El personal de la planta: quiénes trabajan, qué rol tienen, y en qué línea están asignados.

---

#### `Empleados`

Personal de la planta. Un empleado puede tener un rol (operador, supervisor, etc.) y estar asignado a un módulo y/o máquina.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `nombre` | TEXT | NOT NULL | Nombre completo |
| `numero_documento` | TEXT | NOT NULL | Cédula o DNI |
| `cargo` | TEXT | NOT NULL | Cargo del empleado |
| `rol` | TEXT | | Rol funcional: "operador", "supervisor" |
| `fecha_ingreso` | TEXT | | Fecha de ingreso |
| `estado` | TEXT | | "activo" / "inactivo" |
| `telefono` | TEXT | | Teléfono de contacto |
| `email` | TEXT | | Correo electrónico |
| `modulo_asignado` | INTEGER | FK → ModuloConfeccion | Módulo donde trabaja (calculado desde la máquina) |
| `id_maquina` | INTEGER | FK → Maquinas | Máquina que opera |

**Relaciones:**
- Un empleado se asigna a una **máquina** (`id_maquina`).
- El **módulo** se deduce automáticamente de la máquina (`modulo_asignado` = `Maquinas.id_modulo`).
- La cadena es: **Empleado → Máquina → Módulo**.
- Solo los **operadores** pueden tener máquina asignada. Los **supervisores** no tienen máquina.
- Un empleado tiene un usuario (`Usuario.id_empleado`).
- Un empleado puede tener registros de producción (`RegistroProduccion.id_operador`).

**Restricción FK:** No se puede eliminar un empleado que tenga usuario o producción registrada.

---

#### `Usuario`

Credenciales de acceso al sistema. Cada usuario pertenece a un empleado y tiene un rol con permisos.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `nombre_usuario` | TEXT | NOT NULL | Nombre de usuario para login |
| `password` | TEXT | NOT NULL | Contraseña (actualmente en texto plano) |
| `rol` | TEXT | | "admin", "supervisor", "operador" |
| `id_empleado` | INTEGER | NOT NULL, FK → Empleados | Empleado asociado |
| `activo` | INTEGER | | 1 = activo, 0 = inactivo |

**Relaciones:**
- Solo usuarios con rol **supervisor** tienen asignaciones de línea (`AsignacionUsuarioLinea`).
- Los supervisores **no** tienen máquina asignada; solo los operadores.
- Un usuario registra producción (`RegistroProduccion.id_usuario`).
- Al crear un usuario, solo aparecen empleados con rol **supervisor** en el selector.

**Restricción FK:** No se puede eliminar un usuario que tenga registros de producción.

---

#### `AsignacionUsuarioLinea`

Acceso de supervisores a módulos. Solo los usuarios con rol **supervisor** tienen asignaciones. Determina los permisos de menú del frontend.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `id_usuario` | INTEGER | NOT NULL, FK → Usuario | Usuario asignado |
| `id_modulo` | INTEGER | NOT NULL, FK → ModuloConfeccion | Módulo al que tiene acceso |

**Relaciones:**
- Se elimina automáticamente en cascada si se borra el usuario padre.

---

### Dominio: Ingeniería

Define los productos (referencias), cómo se fabrican (operaciones, secuencia) y con qué materiales (BOM).

---

#### `ReferenciaProducto`

Modelo de gorra. Es el "plano" del producto: especificaciones técnicas, foto del prototipo, secuencia de operaciones, lista de materiales y documentación PDF.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `nombre_referencia` | TEXT | NOT NULL | Nombre del modelo (ej: "Gorra Trucker") |
| `especificaciones` | TEXT | | Detalles técnicos |
| `foto` | TEXT | | URL de la foto del prototipo |
| `fecha_creacion` | TIMESTAMP | | Fecha de creación |
| `pdf_path` | TEXT | | Ruta del PDF con información adicional (máx 10MB) |

**Relaciones:**
- Tiene una secuencia de operaciones (`ReferenciaDetalle`).
- Tiene una lista de materiales / BOM (`ReferenciaMaterial`).
- Puede tener un PDF con documentación adicional.
- Se usa para crear órdenes de producción (`OrdenProduccion.id_referencia`).

---

#### `Operacion`

Operación de confección con su tiempo estándar. Ej: "Coser ala", "Bordar frente", "Poner cierre".

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `nombre_operacion` | TEXT | NOT NULL | Nombre de la operación |
| `tiempo_segundos` | INTEGER | NOT NULL | Tiempo estándar en segundos por unidad |
| `id_maquina` | INTEGER | FK → Maquinas | Máquina requerida (nullable) |
| `id_seccion` | INTEGER | FK → SeccionPrenda | Sección de la prenda |

**Relaciones:**
- Aparece en la secuencia de una referencia (`ReferenciaDetalle.id_operacion`).
- Se registra en producción real (`RegistroProduccion.id_operacion`).

**Restricción FK:** No se puede eliminar una operación que esté en una secuencia de referencia o tenga producción registrada.

---

#### `ReferenciaDetalle`

Secuencia de operaciones de una referencia. Cada fila es una letra (A, B, C...) que representa un paso del proceso de confección.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `id_referencia` | INTEGER | NOT NULL, FK → ReferenciaProducto | Referencia padre |
| `id_operacion` | INTEGER | NOT NULL, FK → Operacion | Operación de este paso |
| `letra_secuencia` | TEXT | NOT NULL | Letra del paso (A, B, C...) |
| `predecesoras` | TEXT | | Letras de pasos que deben completarse antes (ej: "A,B") |
| `orden_fila` | INTEGER | | Orden visual en la grilla |

---

#### `Materiales`

Catálogo de insumos: telas, hebillas, etiquetas, hilos, etc.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `nombre` | TEXT | NOT NULL | Nombre del material |
| `unidad` | TEXT | | Unidad de medida: "metros", "unidades", "kg" |
| `costo_unitario` | REAL | | Costo por unidad de medida |
| `proveedor` | TEXT | | Proveedor |
| `descripcion` | TEXT | | Descripción del material |

**Relaciones:**
- Se usa en BOM (`ReferenciaMaterial.id_material`).

**Restricción FK:** No se puede eliminar un material que esté en una o más referencias (BOM).

---

#### `ReferenciaMaterial`

Lista de materiales (BOM) de una referencia. Cuánto material se necesita por unidad de producto.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `id_referencia` | INTEGER | NOT NULL, FK → ReferenciaProducto | Referencia padre |
| `id_material` | INTEGER | NOT NULL, FK → Materiales | Material |
| `cantidad_por_unidad` | REAL | NOT NULL | Cantidad necesaria por gorra |
| `merma_porcentaje` | REAL | | Porcentaje de merma estimado |
| `nota` | TEXT | | Observaciones |

**Relaciones:**
- Al borrar una referencia, se eliminan automáticamente sus materiales (CASCADE).

---

### Dominio: Producción

El ciclo de vida real de fabricación: crear una orden, asignarla a una línea, y registrar lo que realmente produce cada operario.

---

#### `OrdenProduccion`

Lote de producción. Define cuántas gorras de un modelo se van a fabricar.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `id_referencia` | INTEGER | NOT NULL, FK → ReferenciaProducto | Modelo a fabricar |
| `nombre_orden` | TEXT | NOT NULL | Nombre/identificador de la orden |
| `cantidad_lote` | INTEGER | NOT NULL | Cantidad de unidades a producir |
| `estado` | TEXT | | "pendiente", "en_progreso", "completada" |
| `fecha_creacion` | TIMESTAMP | | Fecha de creación |

**Relaciones:**
- Se asigna a módulos vía `AsignacionModulo`.
- Se registra producción contra esta orden (`RegistroProduccion.id_orden`).

**Restricción FK:** No se puede eliminar una orden que tenga producción registrada o líneas asignadas.

---

#### `AsignacionModulo`

Vínculo entre una orden y un módulo. Define cuántas unidades de la orden se producen en esa línea.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `id_orden` | INTEGER | NOT NULL, FK → OrdenProduccion | Orden asignada |
| `id_modulo` | INTEGER | NOT NULL, FK → ModuloConfeccion | Módulo destino |
| `cantidad_asignada` | INTEGER | NOT NULL | Unidades a producir en este módulo |

**Relaciones:**
- El control por hora (`ControlHoraHora`) usa la orden de producción directamente.

---

#### `RegistroProduccion`

Registro diario de producción. El supervisor registra para cada operario: cantidad producida, defectuosas y paradas. **Tabla simplificada — el módulo y máquina se deducen.**

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `fecha` | TEXT | NOT NULL | Fecha del registro (YYYY-MM-DD) |
| `id_orden` | INTEGER | NOT NULL, FK → OrdenProduccion | Contra qué orden se produce |
| `id_operacion` | INTEGER | FK → Operacion | Actividad realizada (necesaria: una máquina puede hacer varias operaciones) |
| `id_operador` | INTEGER | NOT NULL, FK → Empleados | Empleado que produjo |
| `cantidad_producida` | INTEGER | NOT NULL | Unidades buenas producidas |
| `cantidad_defectuosa` | INTEGER | DEFAULT 0 | Unidades defectuosas |
| `observaciones` | TEXT | | Notas del operario (opcional) |
| `id_usuario` | INTEGER | NOT NULL, FK → Usuario | Supervisor que registró |
| `created_at` | TIMESTAMP | | Timestamp del registro |

**Relaciones:**
- El **módulo** se deduce del supervisor (`AsignacionUsuarioLinea`).
- La **máquina** se deduce del empleado (`Empleados.id_maquina`).
- La **actividad** (`id_operacion`) se registra porque una máquina puede hacer varias operaciones.
- Puede tener paradas registradas (`ParadaRegistro.id_registro`).

**Flujo del supervisor:**
1. Ingresa → el sistema sabe qué módulo supervisa.
2. Ve el personal activo de su línea con cargo y máquina.
3. Para cada empleado: cantidad producida, defectuosa, paradas.

---

#### `ParadaRegistro`

Parada real ocurrida durante la producción. Puede ser programada (refrigerio) o no programada (falla de máquina).

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `id_registro` | INTEGER | NOT NULL, FK → RegistroProduccion | Registro de producción asociado |
| `id_parada_programada` | INTEGER | FK → ParadasProgramadas | Parada programada (si aplica) |
| `id_causa` | INTEGER | FK → CausaParada | Causa de la parada |
| `tiempo_segundos` | INTEGER | NOT NULL | Duración de la parada |
| `descripcion` | TEXT | | Descripción de lo que pasó |

**Relaciones:**
- Si el registro de producción se borra, sus paradas se eliminan automáticamente (CASCADE).

---

#### `CausaParada`

Catálogo de causas de parada no programada: falla mecánica, falta de material, corte de luz, etc.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `nombre` | TEXT | NOT NULL | Nombre de la causa |

**Restricción FK:** No se puede eliminar una causa que esté usada en paradas de producción registradas.

---

### Dominio: Control

Monitoreo granular y configuración del sistema.

---

#### `ControlHoraHora`

Control por hora de producción. Registra lo que cada empleado produjo en una hora específica. Mismo patrón que `RegistroProduccion` pero desglosado por hora.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `fecha` | TEXT | NOT NULL | Fecha del control |
| `id_hora` | INTEGER | NOT NULL, FK → HorasProduccion | Franja horaria del turno |
| `id_orden` | INTEGER | NOT NULL, FK → OrdenProduccion | Orden de producción |
| `id_operador` | INTEGER | NOT NULL, FK → Empleados | Empleado que operó |
| `cantidad_producida` | INTEGER | NOT NULL | Unidades buenas producidas |
| `cantidad_defectuosa` | INTEGER | DEFAULT 0 | Unidades defectuosas |
| `observaciones` | TEXT | | Notas libres |
| `id_usuario` | INTEGER | NOT NULL, FK → Usuario | Supervisor que registró |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Marca de registro |

**Flujo del supervisor:**
1. Selecciona la hora del turno
2. Ve el personal activo de su línea (traído del backend)
3. Para cada empleado: cantidad producida, defectuosa, y paradas si las hubo

**Paradas**: se registran en tabla separada `ParadaControlHora` (una fila por cada parada del registro).

---

#### `ParadaControlHora`

Paradas asociadas a un registro de control por hora. Puede tener cero o varias paradas por registro.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PK | Identificador único |
| `id_control` | INTEGER | NOT NULL, FK → ControlHoraHora | Registro de control |
| `id_parada_programada` | INTEGER | FK → ParadasProgramadas | Parada programada |
| `id_causa` | INTEGER | FK → CausaParada | Causa de la parada |
| `tiempo_segundos` | INTEGER | NOT NULL | Duración de la parada (seg) |
| `descripcion` | TEXT | | Descripción de la parada |

---

#### `Configuracion`

Pares clave-valor para configuración del sistema.

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `clave` | TEXT | PK | Nombre de la configuración |
| `valor` | TEXT | | Valor |

---

## Diagrama de relaciones

```
ModuloConfeccion ◄── Maquinas (id_modulo)
Maquinas ◄── Empleados (id_maquina)  →  Empleado trabaja en módulo vía máquina
ModuloConfeccion ◄── AsignacionUsuarioLinea (id_modulo)
ModuloConfeccion ◄── AsignacionModulo (id_modulo)

Maquinas ◄── Operacion (id_maquina)

SeccionPrenda ◄── Operacion (id_seccion)

Empleados ◄── Usuario (id_empleado)
Usuario ◄── AsignacionUsuarioLinea (id_usuario)
Usuario ◄── RegistroProduccion (id_usuario)

ReferenciaProducto ◄── OrdenProduccion (id_referencia)
ReferenciaProducto ◄── ReferenciaDetalle (id_referencia)
ReferenciaProducto ◄── ReferenciaMaterial (id_referencia)

Operacion ◄── ReferenciaDetalle (id_operacion)
Operacion ◄── RegistroProduccion (id_operacion)

Materiales ◄── ReferenciaMaterial (id_material)

OrdenProduccion ◄── AsignacionModulo (id_orden)
OrdenProduccion ◄── RegistroProduccion (id_orden)

Empleados ◄── RegistroProduccion (id_operador)  [operario que produjo]

OrdenProduccion ◄── ControlHoraHora (id_orden)
HorasProduccion ◄── ControlHoraHora (id_hora)
Empleados ◄── ControlHoraHora (id_operador)

ParadasProgramadas ◄── ParadaRegistro (id_parada_programada)
ParadasProgramadas ◄── ParadaControlHora (id_parada_programada)

CausaParada ◄── ParadaRegistro (id_causa)
CausaParada ◄── ParadaControlHora (id_causa)

RegistroProduccion ◄── ParadaRegistro (id_registro)  [ON DELETE CASCADE]
ControlHoraHora ◄── ParadaControlHora (id_control)  [ON DELETE CASCADE]
```

## Modelo de datos en dbdiagram.io

Abrí `schema.dbml` en [dbdiagram.io](https://dbdiagram.io/d) para ver el diagrama ER interactivo.

---

## API

| Recurso | GET (lista) | GET (uno) | POST | PUT | DELETE |
|---------|-------------|-----------|------|-----|--------|
| Módulos | `/api/modulos` | `/api/modulos/{id}` | `/api/modulos` | `/api/modulos/{id}` | `/api/modulos/{id}` |
| Maquinaria | `/api/maquinaria` | `/api/maquinaria/{id}` | `/api/maquinaria` | `/api/maquinaria/{id}` | `/api/maquinaria/{id}` |
| Secciones | `/api/secciones` | `/api/secciones/{id}` | `/api/secciones` | `/api/secciones/{id}` | `/api/secciones/{id}` |
| Empleados | `/api/empleados` | `/api/empleados/{id}` | `/api/empleados` | `/api/empleados/{id}` | `/api/empleados/{id}` |
| Usuarios | `/api/usuarios` | `/api/usuarios/{id}` | `/api/usuarios` | `/api/usuarios/{id}` | `/api/usuarios/{id}` |
| Horas | `/api/horas` | `/api/horas/{id}` | `/api/horas` | `/api/horas/{id}` | `/api/horas/{id}` |
| Paradas | `/api/paradas` | `/api/paradas/{id}` | `/api/paradas` | `/api/paradas/{id}` | `/api/paradas/{id}` |
| Operaciones | `/api/operaciones` | `/api/operaciones/{id}` | `/api/operaciones` | `/api/operaciones/{id}` | `/api/operaciones/{id}` |
| Referencias | `/api/referencias` | `/api/referencias/{id}` | `/api/referencias` | `/api/referencias/{id}` | `/api/referencias/{id}` |
| PDF Ref | `/api/referencias/{id}/pdf` (GET) | | `/api/referencias/{id}/pdf` (POST) | | `/api/referencias/{id}/pdf` (DELETE) |
| Detalles | `/api/referencias/{id}/detalles` | | `/api/detalles` | `/api/detalles/{id}` | `/api/detalles/{id}` |
| Materiales | `/api/materiales` | `/api/materiales/{id}` | `/api/materiales` | `/api/materiales/{id}` | `/api/materiales/{id}` |
| BOM | `/api/referencias/{id}/materiales` | | `/api/materiales-referencia` | `/api/materiales-referencia/{id}` | `/api/materiales-referencia/{id}` |
| Órdenes | `/api/ordenes` | `/api/ordenes/{id}` | `/api/ordenes` | `/api/ordenes/{id}` | `/api/ordenes/{id}` |
| Asignaciones | `/api/asignaciones` | `/api/asignaciones/{id}` | `/api/asignaciones` | `/api/asignaciones/{id}` | `/api/asignaciones/{id}` |
| Producción | `/api/produccion` | `/api/produccion/{id}` | `/api/produccion` | `/api/produccion/{id}` | `/api/produccion/{id}` |
| Control Hora | `/api/control-hora` | | `/api/control-hora` | | `/api/control-hora/{id}` |
| Eficiencia | `/api/reportes/eficiencia` | | | | |
| Balanceo | `/api/balanceo/calcular` | | | | |
| Login | | | `/api/login` | | |

## Licencia

Proyecto privado.
