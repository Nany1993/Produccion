# Sistema de Gestión de Balanceo de Producción

## Descripción General

Sistema web para gestión y balanceo de líneas de producción en plantas de confección. Permite administrar operaciones, referencias de producto, asignación de lotes a módulos, control de producción hora a hora y análisis de eficiencia.

**Stack Tecnológico:**
- Backend: Python + Flask
- Base de Datos: SQLite
- Frontend: HTML5 + CSS3 + JavaScript (vanilla)
- Puerto: 8000

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Browser)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ index.html  │  │  style.css  │  │     app.js      │ │
│  │ (UI/HTML)   │  │ (Estilos)   │  │ (Lógica/AJAX)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/JSON
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Backend (Flask)                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │                   main.py                        │    │
│  │  • Rutas API REST                                │    │
│  │  • Servidor estático                             │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────┐  ┌─────────────────────────────┐   │
│  │   database.py   │  │        engine.py            │   │
│  │  • Conexión DB  │  │  • Algoritmo de balanceo    │   │
│  │  • CRUD ops     │  │  • Asignación de operarios  │   │
│  └─────────────────┘  └─────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              SQLite (balanceo_produccion.db)             │
└─────────────────────────────────────────────────────────┘
```

---

## Módulos Funcionales

### 1. Catálogos
Gestión de datos maestros del sistema.

| Catálogo | Descripción |
|----------|-------------|
| **Maquinaria** | Tipos de máquina disponibles (Plana, Fileteadora, etc.) |
| **Secciones** | Partes de la prenda (Delantero, Posterior, Ensamble) |
| **Módulos** | Líneas de producción físicas (Módulo 1, 2, etc.) |
| **Horas** | Horas operativas del día (Hora 1 a Hora 8/9/Extra) |
| **Paradas** | Paradas programadas con duración (Desayuno, Almuerzo, etc.) |

### 2. Operaciones
Registro de operaciones estándar de confección.

Cada operación define:
- Nombre descriptivo
- Tiempo estándar en segundos
- Máquina requerida
- Sección de la prenda

### 3. Ingeniería de Producto
Creación de referencias (modelos de producto) con su secuencia de operaciones.

**Conceptos clave:**
- **Referencia**: Un modelo específico de producto (ej: "Pantalón Ref. 30220")
- **Secuencia**: Orden de operaciones con letras (A, B, C...)
- **Predecesoras**: Operaciones que deben completarse antes (ej: "A,B")
- **Lote**: Cantidad planificada a producir

### 4. Programación
Asignación de lotes de referencias a módulos de producción.

**Reglas de negocio:**
- No se puede asignar más de lo disponible (lote - ya asignado)
- Una referencia puede asignarse a múltiples módulos
- Un módulo puede tener múltiples referencias asignadas

### 5. Control Hora a Hora
Registro de producción real por hora operativa.

**Datos registrados:**
- Fecha y hora
- Módulo y referencia
- Cantidad producida
- Cantidad de operarios
- Paradas programadas y no programadas
- Porción de tiempo (0.1 a 1.0 = 10% a 100% de la hora)

**Validaciones:**
- Suma de porciones de tiempo por módulo/hora ≤ 1.0
- Producción acumulada no puede exceder la asignación

### 6. Tablero de Eficiencias
Reporte de eficiencia por módulo y hora.

**Fórmula de meta:**
```
TD = (Num_Operarios × 3600 × Porción) - (Parada_Prog × Num_Op) - Parada_NoProg
Meta = TD / Tiempo_Ciclo_Referencia
Eficiencia = (Producción_Real / Meta) × 100%
```

**Heatmap de eficiencia:**
- ≥100%: Cian (Super)
- 90-99%: Verde (Bueno)
- 80-89%: Amarillo (Alerta)
- <80%: Rojo (Crítico)

### 7. Simulador de Balanceo
Calcula la asignación óptima de operaciones a operarios.

**Dos escenarios:**
1. **Secuencial**: Respeta predecesoras (flujo real de producción)
2. **Eficiencia Máxima**: Ignora secuencia para maximizar balance

**Algoritmo:**
- Agrupa operaciones por tipo de máquina
- Asigna roles (cada operario se especializa en un tipo de máquina)
- Distribuye operaciones usando heurística LPT (Longest Processing Time first)
- Calcula KPIs: eficiencia, producción/hora, tiempo ciclo

---

## Modelo Entidad-Relación

### Diagrama

```
┌──────────────────┐       ┌──────────────────┐
│  TipoMaquinaria  │       │   SeccionPrenda  │
├──────────────────┤       ├──────────────────┤
│ id (PK)          │       │ id (PK)          │
│ nombre           │       │ nombre           │
└────────┬─────────┘       └────────┬─────────┘
         │                          │
         │ FK                       │ FK
         ▼                          ▼
┌──────────────────────────────────────────────┐
│                  Operacion                   │
├──────────────────────────────────────────────┤
│ id (PK)                                      │
│ nombre_operacion                             │
│ tiempo_segundos                              │
│ id_maquina (FK → TipoMaquinaria)             │
│ id_seccion (FK → SeccionPrenda)              │
└──────────────────────┬───────────────────────┘
                       │
                       │ FK
                       ▼
┌──────────────────┐   ┌──────────────────────────────────┐
│ReferenciaProducto│   │       ReferenciaDetalle          │
├──────────────────┤   ├──────────────────────────────────┤
│ id (PK)          │◄──│ id_referencia (FK)               │
│ nombre_referencia│   │ id_operacion (FK → Operacion)    │
│ fecha_creacion   │   │ letra_secuencia                  │
│ cantidad_lote    │   │ predecesoras                     │
└────────┬─────────┘   │ orden_fila                       │
         │             └──────────────────────────────────┘
         │
         │ FK
         ▼
┌──────────────────────────────────────────────────┐
│              AsignacionModulo                     │
├──────────────────────────────────────────────────┤
│ id (PK)                                          │
│ id_referencia (FK → ReferenciaProducto)          │
│ id_modulo (FK → ModuloConfeccion)                │
│ cantidad_asignada                                │
└──────────────────────┬───────────────────────────┘
                       │
                       │ FK
         ┌─────────────┼─────────────────┐
         ▼             ▼                 ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│ModuloConfecc.│ │HorasProducc. │ │ParadasProgramadas│
├──────────────┤ ├──────────────┤ ├──────────────────┤
│ id (PK)      │ │ id (PK)      │ │ id (PK)          │
│ nombre       │ │ nombre       │ │ nombre           │
│ capacidad_   │ │ hora_inicio  │ │ tiempo_segundos  │
│   maxima     │ │ hora_fin     │ │ tipo             │
│ ubicacion    │ │ turno        │ │ frecuencia       │
│ supervisor   │ └──────────────┘ └──────────────────┘
│ estado       │
└──────┬───────┘
       │
       │ FK (modulo_asignado)
       ▼
┌──────────────────┐
│    Empleados     │
├──────────────────┤
│ id (PK)          │
│ nombre           │
│ numero_documento │
│ cargo            │
│ especialidad     │
│ turno            │
│ fecha_ingreso    │
│ estado           │
│ telefono         │
│ email            │
│ modulo_asignado  │
│   (FK)           │
└──────────────────┘
         │             │                 │
         │ FK          │ FK              │ FK
         ▼             ▼                 ▼
┌──────────────────────────────────────────────────────┐
│                   ControlHoraHora                     │
├──────────────────────────────────────────────────────┤
│ id (PK)                                              │
│ fecha                                                │
│ id_modulo (FK → ModuloConfeccion)                    │
│ id_asignacion (FK → AsignacionModulo)                │
│ id_hora (FK → HorasProduccion)                       │
│ porcion_tiempo                                       │
│ cantidad_operarios                                   │
│ cantidad_producida                                   │
│ id_parada_programada (FK → ParadasProgramadas)       │
│ descripcion_parada_no_programada                     │
│ tiempo_parada_no_programada                          │
│ created_at                                           │
│ updated_at                                           │
└──────────────────────────────────────────────────────┘
```

### Tablas y Relaciones

#### TipoMaquinaria
Catálogo de tipos de máquina disponibles.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| nombre | TEXT | Nombre del tipo de máquina |

#### SeccionPrenda
Partes o secciones de la prenda.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| nombre | TEXT | Nombre de la sección |

#### Operacion
Operaciones estándar de confección.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| nombre_operacion | TEXT | Descripción de la operación |
| tiempo_segundos | INTEGER | Tiempo estándar en segundos |
| id_maquina | INTEGER FK | Máquina requerida |
| id_seccion | INTEGER FK | Sección de la prenda |

#### ReferenciaProducto
Modelos de producto (referencias).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| nombre_referencia | TEXT | Nombre/código de la referencia |
| fecha_creacion | TIMESTAMP | Fecha de creación |
| cantidad_lote | INTEGER | Cantidad planificada del lote |

#### ReferenciaDetalle
Secuencia de operaciones de cada referencia.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| id_referencia | INTEGER FK | Referencia padre |
| id_operacion | INTEGER FK | Operación del catálogo |
| letra_secuencia | TEXT | Letra identificadora (A, B, C...) |
| predecesoras | TEXT | Letras de operaciones previas requeridas |
| orden_fila | INTEGER | Orden de visualización |

#### ModuloConfeccion
Líneas de producción físicas.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| nombre | TEXT | Nombre del módulo |
| capacidad_maxima | INTEGER | Número máximo de operarios |
| ubicacion | TEXT | Ubicación física |
| supervisor | TEXT | Responsable de la línea |
| estado | TEXT | Activo o Inactivo |

#### Empleados
Personal de la planta (operarios, supervisores, auxiliares).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| nombre | TEXT | Nombre completo |
| numero_documento | TEXT UNIQUE | Número de documento (único) |
| cargo | TEXT | Cargo (Operario, Supervisor, etc.) |
| especialidad | TEXT | Tipo de máquina que maneja |
| turno | TEXT | Mañana, Tarde, Noche, Mixto |
| fecha_ingreso | TEXT | Fecha de ingreso |
| estado | TEXT | Activo, Inactivo, Vacaciones, Incapacidad |
| telefono | TEXT | Número de contacto |
| email | TEXT | Correo electrónico |
| modulo_asignado | INTEGER FK | Módulo de producción asignado |

#### HorasProduccion
Horas operativas del día.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| nombre | TEXT | Nombre de la hora (Hora 1, Hora 2...) |

#### ParadasProgramadas
Paradas planificadas con duración.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| nombre | TEXT | Descripción de la parada |
| tiempo_segundos | INTEGER | Duración en segundos |

#### AsignacionModulo
Asignación de referencias a módulos.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| id_referencia | INTEGER FK | Referencia asignada |
| id_modulo | INTEGER FK | Módulo destino |
| cantidad_asignada | INTEGER | Unidades asignadas |

#### ControlHoraHora
Registro de producción hora a hora.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| fecha | TEXT | Fecha del registro (YYYY-MM-DD) |
| id_modulo | INTEGER FK | Módulo de producción |
| id_asignacion | INTEGER FK | Asignación (ref+módulo) |
| id_hora | INTEGER FK | Hora operativa |
| porcion_tiempo | REAL | Fracción de hora (0.1 a 1.0) |
| cantidad_operarios | REAL | Número de operarios |
| cantidad_producida | INTEGER | Unidades producidas |
| id_parada_programada | INTEGER FK | Tipo de parada programada |
| descripcion_parada_no_programada | TEXT | Causa de parada no planificada |
| tiempo_parada_no_programada | INTEGER | Duración parada no programada |
| created_at | TIMESTAMP | Fecha de creación del registro |
| updated_at | TIMESTAMP | Fecha de última modificación |

---

## API Endpoints

### Catálogos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/maquinaria` | Listar máquinas |
| POST | `/api/maquinaria` | Crear máquina |
| GET | `/api/secciones` | Listar secciones |
| POST | `/api/secciones` | Crear sección |
| GET | `/api/modulos` | Listar módulos |
| POST | `/api/modulos` | Crear módulo |
| GET | `/api/horas` | Listar horas |
| POST | `/api/horas` | Crear hora |
| GET | `/api/paradas` | Listar paradas |
| POST | `/api/paradas` | Crear parada |
| GET | `/api/empleados` | Listar empleados |
| GET | `/api/empleados/{id}` | Obtener empleado |
| POST | `/api/empleados` | Crear empleado |
| PUT | `/api/empleados/{id}` | Actualizar empleado |
| DELETE | `/api/empleados/{id}` | Eliminar empleado |

### Operaciones

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/operaciones` | Listar operaciones |
| POST | `/api/operaciones` | Crear operación |
| PUT | `/api/operaciones/{id}` | Actualizar operación |
| DELETE | `/api/operaciones/{id}` | Eliminar operación |

### Referencias

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/referencias` | Listar referencias |
| POST | `/api/referencias` | Crear referencia |
| PUT | `/api/referencias/{id}` | Actualizar referencia |
| DELETE | `/api/referencias/{id}` | Eliminar referencia |
| POST | `/api/referencias/{id}/duplicar` | Duplicar referencia |
| GET | `/api/referencias/{id}/detalles` | Listar detalles de secuencia |
| POST | `/api/referencias/{id}/detalles` | Agregar operación a secuencia |
| DELETE | `/api/detalles/{id}` | Quitar operación de secuencia |
| GET | `/api/referencias-disponibles` | Referencias con stock disponible |
| GET | `/api/referencias/{id}/disponibilidad` | Stock disponible de referencia |

### Programación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/asignaciones` | Listar asignaciones |
| POST | `/api/asignaciones` | Crear asignación |
| PUT | `/api/asignaciones/{id}` | Actualizar cantidad |
| DELETE | `/api/asignaciones/{id}` | Eliminar asignación |
| GET | `/api/modulos/{id}/referencias-asignadas` | Referencias en un módulo |

### Control Hora a Hora

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/control-hora` | Crear registro |
| GET | `/api/control-hora/hoy?fecha=YYYY-MM-DD` | Registros del día |
| PUT | `/api/control-hora/{id}` | Actualizar registro |
| DELETE | `/api/control-hora/{id}` | Eliminar registro |

### Reportes y Simulación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/reportes/eficiencia?fecha_inicio=&fecha_fin=` | Tablero de eficiencias |
| POST | `/api/balanceo/calcular` | Calcular balanceo de línea |

---

## Reglas de Negocio

### Asignación de Lotes
1. No se puede asignar más unidades que las disponibles (lote - ya asignado)
2. Al editar una asignación, se valida contra el máximo posible
3. Una referencia puede estar en múltiples módulos simultáneamente

### Control de Producción
1. La suma de porciones de tiempo por módulo/hora/fecha no puede exceder 1.0
2. La producción acumulada por asignación no puede exceder la cantidad asignada
3. Cada registro está vinculado a una asignación específica (referencia + módulo)

### Balanceo de Línea
1. Se requiere al menos 1 operario por tipo de máquina presente
2. El algoritmo asigna roles fijos por tipo de máquina
3. Se generan dos escenarios: secuencial (respeta predecesoras) y eficiencia máxima

---

## Estructura de Archivos

```
proyecto-balanceo/
├── main.py                 # Servidor Flask + rutas API
├── database.py             # Capa de acceso a datos (SQLite)
├── engine.py               # Algoritmo de balanceo
├── index.html              # Interfaz de usuario
├── style.css               # Estilos
├── app.js                  # Lógica del frontend
├── balanceo_produccion.db  # Base de datos SQLite
└── DOCUMENTACION.md        # Este archivo
```

---

## Historial de Cambios

### v0.2 - Refactor UX (Actual)
- Extracción de JS a archivo separado (app.js)
- Sistema de toasts en lugar de `alert()`
- Modal de confirmación en lugar de `confirm()`
- Validación inline de formularios
- Formato de tiempos en minutos/segundos
- Badges visuales para máquinas, módulos y horas
- Eliminación de código duplicado y archivos obsoletos

### v0.1 - Prototipo Inicial
- Implementación base del sistema
- 7 módulos funcionales
- Base de datos SQLite

---

## Datos de Producción de Gorras

### Guía de Campos por Catálogo

#### 1. Maquinaria (TipoMaquinaria)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| **id** | INTEGER | Auto | Identificador único generado automáticamente |
| **nombre** | TEXT | ✓ | Nombre del tipo de máquina (ej: PLANA, FILETEADORA) |
| **descripcion** | TEXT | No | Función o propósito de la máquina (ej: "Costura recta general") |
| **velocidad_tipica** | INTEGER | No | Velocidad promedio de producción en unidades por hora |
| **estado** | TEXT | No | Estado actual: `Activa`, `Inactiva` o `Mantenimiento` |

**Uso:** Define los tipos de máquina disponibles en la planta. Cada operación de confección requiere un tipo específico de máquina.

---

#### 2. Secciones (SeccionPrenda)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| **id** | INTEGER | Auto | Identificador único |
| **nombre** | TEXT | ✓ | Nombre de la sección (ej: CORONA, VISERA, BANDA INTERIOR) |
| **descripcion** | TEXT | No | Descripción de la parte de la gorra (ej: "Paneles que forman la copa") |
| **orden_proceso** | INTEGER | No | Orden secuencial en el proceso de fabricación (1, 2, 3...) |

**Uso:** Representa las partes o secciones de la gorra. Ayuda a organizar las operaciones por área de trabajo.

---

#### 3. Módulos (ModuloConfeccion)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| **id** | INTEGER | Auto | Identificador único |
| **nombre** | TEXT | ✓ | Nombre de la línea de producción (ej: Línea 1, Línea 2) |
| **capacidad_maxima** | INTEGER | No | Número máximo de operarios que puede tener el módulo |
| **ubicacion** | TEXT | No | Ubicación física (ej: "Nave A - Piso 1") |
| **supervisor** | TEXT | No | Nombre del supervisor responsable de la línea |
| **estado** | TEXT | No | Estado actual: `Activo` o `Inactivo` |

**Uso:** Representa las líneas de producción físicas donde se asignan las referencias y se registra la producción hora a hora.

---

#### 4. Horas (HorasProduccion)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| **id** | INTEGER | Auto | Identificador único |
| **nombre** | TEXT | ✓ | Nombre de la hora operativa (ej: Hora 1, Hora 2, Hora Extra) |
| **hora_inicio** | TEXT | No | Hora de inicio en formato HH:MM (ej: "07:00") |
| **hora_fin** | TEXT | No | Hora de fin en formato HH:MM (ej: "08:00") |
| **turno** | TEXT | No | Turno al que pertenece: `Mañana`, `Tarde`, `Noche` o `Extra` |

**Uso:** Define las horas operativas del día para el registro de producción hora a hora.

---

#### 5. Paradas Programadas (ParadasProgramadas)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| **id** | INTEGER | Auto | Identificador único |
| **nombre** | TEXT | ✓ | Descripción de la parada (ej: Desayuno, Almuerzo, Pausa Activa) |
| **tiempo_segundos** | INTEGER | ✓ | Duración de la parada en segundos (ej: 900 = 15 min) |
| **tipo** | TEXT | No | Tipo de parada: `Obligatoria` u `Opcional` |
| **frecuencia** | TEXT | No | Frecuencia de ocurrencia: `Diaria`, `Por cambio de ref` o `Semanal` |

**Uso:** Define las paradas planificadas que afectan el tiempo disponible de producción. Se usan en el control hora a hora y en el cálculo de eficiencia.

---

#### 6. Empleados (Empleados)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| **id** | INTEGER | Auto | Identificador único |
| **nombre** | TEXT | ✓ | Nombre completo del empleado |
| **numero_documento** | TEXT | ✓ | Número de identificación (único) |
| **cargo** | TEXT | ✓ | Cargo del empleado: `Operario`, `Supervisor`, `Auxiliar`, `Mecánico` |
| **especialidad** | TEXT | No | Tipo de máquina que maneja (ej: PLANA, FILETEADORA) |
| **turno** | TEXT | No | Turno de trabajo: `Mañana`, `Tarde`, `Noche` |
| **fecha_ingreso** | TEXT | No | Fecha de ingreso a la empresa (YYYY-MM-DD) |
| **estado** | TEXT | No | Estado actual: `Activo` o `Inactivo` |
| **telefono** | TEXT | No | Número de teléfono de contacto |
| **email** | TEXT | No | Correo electrónico del empleado |
| **modulo_asignado** | INTEGER | No | ID del módulo donde trabaja actualmente (FK → ModuloConfeccion) |

**Uso:** Gestiona el personal de la planta. Permite asignar operarios a módulos específicos y llevar control de sus especialidades y turnos.

---

### Catálogos

**Máquinas (8 tipos):**
| ID | Máquina | Uso |
|----|---------|-----|
| 1 | PLANA | Costura recta general |
| 2 | FILETEADORA | Acabado de bordes |
| 3 | BORDADORA | Logos y diseños |
| 4 | OJETERA | Ojetes de ventilación |
| 5 | BOTONERA | Botones y broches |
| 6 | RIBETADORA | Ribete de visera |
| 7 | PRENSA TERMICA | Moldeo y planchado |
| 8 | CORTADORA | Corte de telas |

**Secciones de la gorra (6):**
| ID | Sección | Descripción |
|----|---------|-------------|
| 1 | CORONA (PANELES) | Paneles que forman la copa |
| 2 | VISERA | Parte frontal rígida |
| 3 | BANDA INTERIOR | Sweatband y unión corona-visera |
| 4 | CIERRE/AJUSTE | Snapback, velcro, hebilla |
| 5 | ACABADOS | Botón, ojetes, control, empaque |
| 6 | BORDADO/LOGO | Bordados decorativos |

**Módulos de producción (8 líneas):**
Línea 1 a Línea 8

**Horas operativas (10):**
Hora 1 a Hora 9 + Hora Extra

**Paradas programadas (6):**
| Parada | Duración |
|--------|----------|
| Desayuno | 15 min |
| Almuerzo | 30 min |
| Pausa Activa | 5 min |
| Cambio de Referencia | 10 min |
| Mantenimiento | 20 min |
| Ninguna | 0 |

### Operaciones de Gorras (20)

| # | Operación | Tiempo | Máquina | Sección |
|---|-----------|--------|---------|---------|
| 1 | Cortar paneles de corona | 35s | CORTADORA | CORONA |
| 2 | Filetear bordes de paneles | 25s | FILETEADORA | CORONA |
| 3 | Unir paneles de corona (6 piezas) | 45s | PLANA | CORONA |
| 4 | Pegar entretela a visera | 30s | PLANA | VISERA |
| 5 | Cortar visera | 20s | CORTADORA | VISERA |
| 6 | Ribetear visera | 40s | RIBETADORA | VISERA |
| 7 | Unir visera a corona | 50s | PLANA | BANDA INTERIOR |
| 8 | Colocar banda interior (sweatband) | 55s | PLANA | BANDA INTERIOR |
| 9 | Filetear unión corona-visera | 30s | FILETEADORA | BANDA INTERIOR |
| 10 | Colocar cierre trasero (snapback) | 35s | BOTONERA | CIERRE/AJUSTE |
| 11 | Colocar ajuste velcro | 30s | PLANA | CIERRE/AJUSTE |
| 12 | Colocar ajuste hebilla metálica | 40s | PLANA | CIERRE/AJUSTE |
| 13 | Bordar logo frontal | 60s | BORDADORA | BORDADO/LOGO |
| 14 | Bordar logo lateral | 45s | BORDADORA | BORDADO/LOGO |
| 15 | Colocar botón superior | 15s | BOTONERA | ACABADOS |
| 16 | Colocar ojetes de ventilación | 25s | OJETERA | ACABADOS |
| 17 | Prensar y dar forma final | 35s | PRENSA TERMICA | ACABADOS |
| 18 | Control de calidad visual | 20s | PLANA | ACABADOS |
| 19 | Colocar etiqueta interior | 15s | PLANA | ACABADOS |
| 20 | Empacar unidad | 10s | PLANA | ACABADOS |

### Referencias (8 modelos de gorra)

| Referencia | Lote | Operaciones | Tiempo Ciclo |
|------------|------|-------------|--------------|
| Gorra Snapback Clásica | 30,000 | 17 ops | ~605s |
| Gorra Trucker Malla | 25,000 | 16 ops | ~545s |
| Gorra Dad Hat Curvada | 20,000 | 17 ops | ~605s |
| Gorra 5 Panel Camp | 18,000 | 15 ops | ~515s |
| Gorra Deportiva Dry-Fit | 35,000 | 17 ops | ~610s |
| Gorra Military Flat | 15,000 | 15 ops | ~515s |
| Gorra Bucket Hat | 28,000 | 11 ops | ~345s |
| Gorra Snapback Premium Bordada | 12,000 | 18 ops | ~650s |

### Resumen de datos

| Tabla | Registros |
|-------|-----------|
| Maquinaria | 8 |
| Secciones | 6 |
| Módulos | 8 |
| Horas | 10 |
| Paradas | 6 |
| Empleados | 20 |
| Operaciones | 20 |
| Referencias | 8 |
| Detalles de secuencia | 126 |
| Asignaciones | 26 |
| Control hora a hora | 1200 |
| **TOTAL** | **1,438** |

---

## Próximas Mejoras Planificadas

1. **Normalización de datos**
   - Eliminar redundancia de `tiempo_parada_programada` en ControlHoraHora
   - Tabla separada para paradas no programadas recurrentes

2. **Predecesoras relacionales**
   - Migrar campo texto a tabla de relaciones para mejor integridad

3. **Autenticación y roles**
   - Sistema de usuarios
   - Permisos por rol (operador, supervisor, administrador)

4. **Auditoría completa**
   - Timestamps en todas las tablas
   - Log de cambios

5. **Escalabilidad**
   - Migrar de SQLite a PostgreSQL para producción
   - Implementar conexión pool
   - Caché de consultas frecuentes
