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

### 5. Registro de Producción
Registro de producción real por día y actividad, vinculado al puesto de trabajo (máquina).

**Datos registrados:**
- Fecha y marca de tiempo real (created_at)
- Máquina / puesto de trabajo y módulo
- Orden de producción y actividad (operación)
- Cantidad producida y defectuosa
- Cantidad de operarios
- Porción de tiempo trabajada (0.1 a 1.0)
- Paradas (programadas y no programadas) en ParadaRegistro

**Modalidad global:** configurada por el Admin (`Diario` | `Por Hora`) desde la barra superior.

**Validaciones:**
- La suma de porciones de tiempo por módulo/fecha ≤ 1.0
- La producción acumulada no puede exceder lo asignado a la orden

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
┌──────────────────────┐   ┌──────────────────────────────────┐
│ReferenciaMaterial(BOM)│  │       ReferenciaDetalle          │
├──────────────────────┤   ├──────────────────────────────────┤
│ id (PK)              │   │ id_referencia (FK)               │
│ id_referencia (FK)   │   │ id_operacion (FK → Operacion)    │
│ id_material (FK)     │   │ letra_secuencia                  │
│ cantidad_por_unidad  │   │ predecesoras                     │
│ merma_porcentaje     │   │ orden_fila                       │
│ nota                 │   └──────────────────────────────────┘
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌────────────────────┐  ┌──────────────────┐
│     Materiales     │  │ReferenciaProducto│
├────────────────────┤  ├──────────────────┤
│ id (PK)            │  │ id (PK)          │
│ nombre             │  │ nombre_referencia│
│ unidad             │  │ especificaciones │
│ costo_unitario     │  │ foto             │
│ proveedor          │  └────────┬─────────┘
│ descripcion        │           │
└────────────────────┘           │
                                 │ FK (id_referencia)
                                 ▼
┌─────────────────────────────────────────┐
│         OrdenProduccion (LOTE)          │
├─────────────────────────────────────────┤
│ id (PK)                                 │
│ id_referencia (FK → ReferenciaProducto) │
│ nombre_orden                            │
│ cantidad_lote                           │
│ estado (Abierta/Cerrada)                │
│ fecha_creacion                          │
└────────────────────┬────────────────────┘
                     │
                     │ FK (id_orden)
                     ▼
┌──────────────────────────────────────────────────┐
│              AsignacionModulo                     │
├──────────────────────────────────────────────────┤
│ id (PK)                                          │
│ id_orden (FK → OrdenProduccion)                  │
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
│ ubicacion    │ └──────────────┘ │ frecuencia       │
│ supervisor   │                  └──────────────────┘
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
│ rol              │
│ fecha_ingreso    │
│ estado           │
│ telefono         │
│ email            │
│ modulo_asignado  │
│ id_maquina (FK)  │
└──────────────────┘
         │             │                 │
         │ FK          │ FK              │ FK
         ▼             ▼                 ▼
┌──────────────────────────────────────────────────────┐
│                  RegistroProduccion                   │
├──────────────────────────────────────────────────────┤
│ id (PK)                                              │
│ fecha                                                │
│ id_modulo (FK → ModuloConfeccion)                    │
│ id_hora (FK → HorasProduccion, nullable)             │
│ id_orden (FK → OrdenProduccion)                      │
│ id_operacion (FK → Operacion)                        │
│ porcion_tiempo                                       │
│ cantidad_operarios                                   │
│ cantidad_producida                                   │
│ cantidad_defectuosa                                  │
│ observaciones                                        │
│ id_usuario (FK → Usuario)                            │
│ created_at                                           │
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
Catálogo de modelos de producto (referencias).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| nombre_referencia | TEXT | Nombre/código de la referencia |
| especificaciones | TEXT | Especificaciones técnicas detalladas del modelo |
| foto | TEXT | Ruta de la foto del prototipo (uploads/) |
| fecha_creacion | TIMESTAMP | Fecha de creación |

> Nota: La referencia es el MODELO. El lote/cantidad vive en OrdenProduccion para permitir reutilizar un modelo en múltiples órdenes.

#### Materiales
Catálogo de insumos/fabricantes reutilizable.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| nombre | TEXT | Nombre del material |
| unidad | TEXT | Unidad (metros, unidades, kg, conos...) — texto libre |
| costo_unitario | REAL | Costo por unidad (opcional) |
| proveedor | TEXT | Proveedor (opcional) |
| descripcion | TEXT | Descripción (opcional) |

#### ReferenciaMaterial (BOM)
Lista de materiales que consume cada referencia (por unidad de producto).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| id_referencia | INTEGER FK | Referencia padre |
| id_material | INTEGER FK | Material del catálogo |
| cantidad_por_unidad | REAL | Cantidad que consume UNA unidad de producto |
| merma_porcentaje | REAL | % de desperdicio (corte, etc.) |
| nota | TEXT | Nota opcional (color, talla) |

**Cálculo de requerimiento para un lote:**
```
Requerimiento = cantidad_por_unidad × cantidad_lote × (1 + merma/100)
Costo estimado = Requerimiento × costo_unitario
```
Endpoint: `GET /api/ordenes/{id}/materiales`

#### OrdenProduccion
Órdenes de producción (lotes). Una referencia puede tener muchas órdenes.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| id_referencia | INTEGER FK | Referencia (modelo) |
| nombre_orden | TEXT | Nombre de la orden (ej: LOTE-001-1) |
| cantidad_lote | INTEGER | Cantidad del lote |
| estado | TEXT | Abierta o Cerrada |
| fecha_creacion | TIMESTAMP | Fecha de creación |

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
| rol | TEXT | Rol de acceso a la plataforma: Operador, Supervisor, Admin |
| fecha_ingreso | TEXT | Fecha de ingreso |
| estado | TEXT | Activo, Inactivo, Vacaciones, Incapacidad |
| telefono | TEXT | Número de contacto |
| email | TEXT | Correo electrónico |
| modulo_asignado | INTEGER FK | Módulo de producción asignado |
| id_maquina | INTEGER FK | Máquina (puesto de trabajo) que opera |

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
Asignación de órdenes (lotes) a módulos.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| id_orden | INTEGER FK | Orden de producción asignada |
| id_modulo | INTEGER FK | Módulo destino |
| cantidad_asignada | INTEGER | Unidades asignadas |

#### RegistroProduccion
Registro de producción real (diario o por actividad).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | INTEGER PK | Identificador único |
| fecha | TEXT | Fecha del registro (YYYY-MM-DD) |
| id_modulo | INTEGER FK | Módulo de producción |
| id_hora | INTEGER FK | Hora operativa (nullable; el timestamp real va en created_at) |
| id_orden | INTEGER FK | Orden de producción |
| id_operacion | INTEGER FK | Actividad/operación registrada |
| porcion_tiempo | REAL | Fracción de tiempo trabajado (0.1 a 1.0) |
| cantidad_operarios | INTEGER | Número de operarios |
| cantidad_producida | INTEGER | Unidades producidas |
| cantidad_defectuosa | INTEGER | Unidades defectuosas |
| observaciones | TEXT | Notas del registro |
| id_usuario | INTEGER FK | Usuario que registró |
| created_at | TIMESTAMP | Marca de tiempo real del registro |

> Las paradas del registro viven en la tabla **ParadaRegistro** (varias por registro).

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
| GET | `/api/ordenes` | Listar órdenes de producción |
| POST | `/api/ordenes` | Crear orden (lote) |
| PUT | `/api/ordenes/{id}` | Actualizar cantidad/estado de orden |
| DELETE | `/api/ordenes/{id}` | Eliminar orden |
| GET | `/api/ordenes-disponibles` | Órdenes abiertas con stock disponible |
| GET | `/api/ordenes/{id}/disponibilidad` | Stock disponible de una orden |
| GET | `/api/materiales` | Listar catálogo de materiales |
| POST | `/api/materiales` | Crear material |
| PUT | `/api/materiales/{id}` | Actualizar material |
| DELETE | `/api/materiales/{id}` | Eliminar material |
| GET | `/api/referencias/{id}/materiales` | BOM de una referencia |
| POST | `/api/referencias/{id}/materiales` | Asociar material a referencia |
| DELETE | `/api/materiales-referencia/{id}` | Quitar material de referencia |
| GET | `/api/ordenes/{id}/materiales` | Cálculo de materiales requeridos para un lote |

### Programación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/asignaciones` | Listar asignaciones |
| POST | `/api/asignaciones` | Crear asignación |
| PUT | `/api/asignaciones/{id}` | Actualizar cantidad |
| DELETE | `/api/asignaciones/{id}` | Eliminar asignación |
| GET | `/api/modulos/{id}/referencias-asignadas` | Referencias en un módulo |

### Registro de Producción

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/produccion` | Crear registro de producción |
| GET | `/api/produccion/dia?fecha=YYYY-MM-DD` | Registros del día |
| GET | `/api/produccion/resumen?fecha=&id_modulo=&id_hora=&id_operacion=` | Resumen por módulo/hora/operación |
| DELETE | `/api/produccion/{id}` | Eliminar registro |
| GET | `/api/progreso/{id_orden}` | Progreso y cumplimiento de una orden |

### Reportes y Simulación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/reportes/eficiencia?fecha_inicio=&fecha_fin=` | Tablero de eficiencias |
| POST | `/api/balanceo/calcular` | Calcular balanceo de línea |

---

## Reglas de Negocio

### Ciclo de Vida de una Referencia (Diseño → Producción)
1. Una referencia (modelo de gorra) se crea en estado **Diseño**
2. Mientras está en Diseño, se define su **secuencia de operaciones** (diagrama de actividades)
3. Solo cuando el diseño está aprobado, la referencia pasa a estado **Activo**
4. En estado Activo, se pueden crear **órdenes de producción** (lotes) sobre ese modelo
5. Se mantiene el estado **Obsoleto** para modelos que ya no se producen

> **Por qué esta separación resuelve el problema de diseño vs producción:** la referencia define QUÉ se debe hacer (operaciones aprobadas) y la orden define CUÁNTO y CUÁNDO se produce. Una referencia no aprobada no puede generar lotes de producción.

### Asignación de Lotes
1. No se puede asignar más unidades que las disponibles (cantidad_lote de la orden - ya asignado)
2. Una orden debe estar `Abierta` para poder asignarse
3. Una referencia (modelo) puede generar múltiples órdenes de producción
4. Al editar una asignación, se valida contra el máximo posible

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

### v0.3 - Sistema de Producción (Actual)
- Registro de producción por máquina (puesto de trabajo) y actividad, con timestamp real
- Ingeniería de Producto rediseñada: lista al ancho con Ver detalle / Editar / Eliminar en modales
- Gestión de materiales (BOM), órdenes de producción y cálculo de materiales por lote
- Cumplimiento de órdenes por gorras completas (mínimo entre actividades)
- Modalidad global de registro (Diario | Por Hora) controlada por el Admin
- Jornada dinámica desde el catálogo de horas; sin campo `turno`
- Sistema de usuarios con roles y permisos de menú; líneas de supervisión por usuario
- Validaciones de negocio: eficiencia por actividad, capacidad de módulos, stock por orden

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

**Uso:** Define las horas operativas del día que alimentan la jornada disponible (ya no se registra producción por hora; el registro usa marca de tiempo real).

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
| **rol** | TEXT | No | Rol de acceso a la plataforma: `Operador`, `Supervisor`, `Admin` |
| **fecha_ingreso** | TEXT | No | Fecha de ingreso a la empresa (YYYY-MM-DD) |
| **estado** | TEXT | No | Estado actual: `Activo` o `Inactivo` |
| **telefono** | TEXT | No | Número de teléfono de contacto |
| **email** | TEXT | No | Correo electrónico del empleado |
| **modulo_asignado** | INTEGER | No | ID del módulo donde trabaja actualmente (FK → ModuloConfeccion) |
| **id_maquina** | INTEGER | No | ID de la máquina (puesto de trabajo) que opera (FK → TipoMaquinaria) |

**Uso:** Gestiona el personal de la planta y su vínculo con los puestos de trabajo (máquina) y líneas. El acceso a la plataforma (usuario/rol) se gestiona desde el módulo **Usuarios**.

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
| Materiales | 15 |
| Operaciones | 20 |
| Referencias | 8 |
| BOM (materiales x referencia) | 73 |
| Detalles de secuencia | 126 |
| Órdenes de producción | 18 |
| Asignaciones | 18 |
| Control hora a hora | 1200 |
| **TOTAL** | **1,540** |

---

## Próximas Mejoras Planificadas

1. **Normalización de datos**
   - Tabla separada para paradas no programadas recurrentes (por tipo de causa)
   - Unificar criterio de `porcion_tiempo` con el tiempo disponible real de la jornada

2. **Predecesoras relacionales**
   - Migrar campo texto a tabla de relaciones para mejor integridad

3. **Autenticación y roles** ✅ (implementado)
   - Sistema de usuarios con roles (operador, supervisor, administrador)
   - Permisos de menú por rol y líneas de supervisión por usuario

4. **Auditoría completa**
   - Log de cambios y registro de usuario en todas las operaciones de catálogo

5. **Escalabilidad**
   - Migrar de SQLite a PostgreSQL para producción
   - Implementar conexión pool
   - Caché de consultas frecuentes
