# Sistema de Balanceo de Producción

Sistema web para gestión y balanceo de líneas de producción en plantas de confección de gorras. Permite administrar catálogos, operaciones, referencias de producto, programación de módulos, registro de producción y análisis de eficiencia.

## Características

- **Catálogos**: Maquinaria, secciones, módulos (líneas), horas operativas y paradas programadas
- **Empleados**: Registro del personal con cargo, rol y puesto de trabajo (máquina) asignado
- **Materiales**: Catálogo de insumos con unidad (metros, unidades, kg) y costo
- **Operaciones**: Registro de operaciones de confección con tiempos estándar
- **Ingeniería de Producto**: Creación de referencias (modelos) con especificaciones técnicas, foto de prototipo, secuencia de operaciones y lista de materiales (BOM)
- **Órdenes de Producción**: Creación de lotes sobre una referencia con cálculo automático de materiales requeridos y costo estimado
- **Programación**: Asignación de órdenes/lotes a módulos de producción
- **Registro de Producción**: Registro real por máquina, orden y actividad, con paradas y modalidad Diario/Por Hora
- **Usuarios**: Acceso con roles (Operador, Supervisor, Admin) y permisos de menú por línea
- **Tablero de Eficiencias**: Reporte de cumplimiento de metas por módulo y hora
- **Simulador de Balanceo**: Cálculo de asignación óptima de operaciones a operarios (2 escenarios)

## Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Backend | Python + Flask |
| Base de datos | SQLite |
| Frontend | HTML5 + CSS3 + JavaScript (vanilla) |
| Puerto | 8000 |

## Estructura del Proyecto

```
proyecto-bu/
├── main.py            # Servidor Flask + rutas API REST
├── database.py        # Capa de acceso a datos (SQLite)
├── engine.py          # Algoritmo de balanceo de línea
├── seed_data.py       # Generador de datos de ejemplo
├── index.html         # Interfaz de usuario
├── style.css          # Estilos
├── app.js             # Lógica del frontend
└── DOCUMENTACION.md   # Documentación completa (modelo ER, API, guías)
```

## Requisitos

- Python 3.8+
- Flask 3.x

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/Nany1993/Produccion.git
cd Produccion

# 2. Instalar dependencias
pip install flask

# 3. (Opcional) Cargar datos de ejemplo
python seed_data.py

# 4. Iniciar el servidor
python main.py
```

El sistema queda disponible en **http://localhost:8000**

> **Nota**: La base de datos `balanceo_produccion.db` se crea automáticamente al iniciar el servidor. Si no aparece, ejecutá `python seed_data.py` para generarla con datos de ejemplo.

**Credenciales por defecto** (según el generador de datos): `admin` / `1234` (Admin), `carlos` / `1234` (Supervisor), `operario` / `1234` (Operador).

## Uso Rápido

1. **Configuración** → Empleados: registrar el personal, asignarlos a líneas
2. **Configuración** → Catálogos: definir máquinas, secciones, horas y paradas
3. **Operaciones** → Operaciones Estándar: registrar operaciones de confección
4. **Configuración** → Materiales: crear el catálogo de insumos
5. **Operaciones** → Ingeniería de Producto: crear referencias con especificaciones, foto del prototipo, secuencia de operaciones y materiales (BOM)
6. **Operaciones** → Órdenes de Producción: crear lotes y ver el cálculo de materiales requeridos
7. **Operaciones** → Programación de Líneas: asignar órdenes a módulos
8. **Operaciones** → Registro de Producción: registrar producción real por máquina y actividad
9. **Análisis** → Tablero Eficiencias: consultar cumplimiento de metas
10. **Análisis** → Simulador Balanceo: calcular distribución óptima de operarios

## API

El sistema expone una API REST. Todos los endpoints están documentados en `DOCUMENTACION.md`.

| Recurso | Endpoints |
|---------|-----------|
| Maquinaria | `/api/maquinaria` |
| Secciones | `/api/secciones` |
| Módulos | `/api/modulos` |
| Empleados | `/api/empleados` |
| Horas | `/api/horas` |
| Paradas | `/api/paradas` |
| Operaciones | `/api/operaciones` |
| Referencias | `/api/referencias` |
| Asignaciones | `/api/asignaciones` |
| Producción | `/api/produccion` |
| Usuarios | `/api/usuarios`, `/api/login` |
| Eficiencia | `/api/reportes/eficiencia` |
| Balanceo | `/api/balanceo/calcular` |

## Documentación

La documentación completa (modelo entidad-relación, guía de campos, reglas de negocio) está en [`DOCUMENTACION.md`](DOCUMENTACION.md).

## Licencia

Proyecto privado.