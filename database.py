import sqlite3
import os

# Configuración del archivo de base de datos
DB_NAME = "balanceo_produccion.db"

def _conexion():
    """Abre una conexión con timeout y busy_timeout para evitar 'database is locked'
    cuando el servidor recibe requests concurrentes (login, carga de listas, etc.)."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000;")
    return conn

def inicializar_base_de_datos():
    """
    Crea las tablas necesarias para la aplicación 'Balanceo' si no existen.
    Garantiza la persistencia de datos al no usar comandos DROP TABLE.
    """
    try:
        # Conectar a la base de datos (se crea el archivo si no existe)
        conexion = _conexion()
        cursor = conexion.cursor()

        # Habilitar soporte para claves foráneas en SQLite
        cursor.execute("PRAGMA foreign_keys = ON;")

        print(f"Iniciando configuración de la base de datos: {DB_NAME}")

        # 1. Tabla TipoMaquinaria
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TipoMaquinaria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                velocidad_tipica INTEGER,
                estado TEXT DEFAULT 'Activa',
                id_modulo INTEGER,
                FOREIGN KEY (id_modulo) REFERENCES ModuloConfeccion(id)
            );
        """)
        print("- Tabla 'TipoMaquinaria' lista.")

        # 2. Tabla SeccionPrenda
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SeccionPrenda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                orden_proceso INTEGER
            );
        """)
        print("- Tabla 'SeccionPrenda' lista.")

        # 2b. Tabla ModuloConfeccion (NUEVA)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ModuloConfeccion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                capacidad_maxima INTEGER,
                ubicacion TEXT,
                supervisor TEXT,
                estado TEXT DEFAULT 'Activo'
            );
        """)
        print("- Tabla 'ModuloConfeccion' lista.")

        # 2d. Tabla ParadasProgramadas (NUEVA)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ParadasProgramadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                tiempo_segundos INTEGER NOT NULL,
                tipo TEXT DEFAULT 'Opcional',
                frecuencia TEXT DEFAULT 'Diaria'
            );
        """)
        # Seed Paradas Programadas
        cursor.execute("SELECT COUNT(*) FROM ParadasProgramadas")
        if cursor.fetchone()[0] == 0:
            paradas = [('Desayuno', 900), ('Almuerzo', 1800), ('Ninguna', 0)]
            cursor.executemany("INSERT INTO ParadasProgramadas (nombre, tiempo_segundos) VALUES (?, ?)", paradas)
        print("- Tabla 'ParadasProgramadas' lista.")

        # 2c. Tabla HorasProduccion (NUEVA)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS HorasProduccion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                hora_inicio TEXT,
                hora_fin TEXT
            );
        """)
        # Seed Horas Produccion
        cursor.execute("SELECT COUNT(*) FROM HorasProduccion")
        if cursor.fetchone()[0] == 0:
            horas = [
                ('Hora 1', '07:00', '08:00'),
                ('Hora 2', '08:00', '09:00'),
                ('Hora 3', '09:00', '10:00'),
                ('Hora 4', '10:00', '11:00'),
                ('Hora 5', '11:00', '12:00'),
                ('Hora 6', '13:00', '14:00'),
                ('Hora 7', '14:00', '15:00'),
                ('Hora 8', '15:00', '16:00'),
                ('Hora 9', '16:00', '17:00'),
                ('Hora Extra', '17:00', '18:00')
            ]
            cursor.executemany("INSERT INTO HorasProduccion (nombre, hora_inicio, hora_fin) VALUES (?, ?, ?)", horas)
        print("- Tabla 'HorasProduccion' lista.")

        # 2f. Tabla Empleados (NUEVA)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Empleados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                numero_documento TEXT UNIQUE NOT NULL,
                cargo TEXT NOT NULL,
                rol TEXT DEFAULT 'Operador',
                fecha_ingreso TEXT,
                estado TEXT DEFAULT 'Activo',
                telefono TEXT,
                email TEXT,
                modulo_asignado INTEGER,
                id_maquina INTEGER,
                FOREIGN KEY (modulo_asignado) REFERENCES ModuloConfeccion(id),
                FOREIGN KEY (id_maquina) REFERENCES TipoMaquinaria(id)
            );
        """)
        print("- Tabla 'Empleados' lista.")

        # 2fa. Tabla Usuario (NUEVA)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Usuario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_usuario TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                rol TEXT DEFAULT 'Operador',
                id_empleado INTEGER NOT NULL,
                activo INTEGER DEFAULT 1,
                FOREIGN KEY (id_empleado) REFERENCES Empleados(id)
            );
        """)
        print("- Tabla 'Usuario' lista.")

        # 2fb. Tabla AsignacionUsuarioLinea (NUEVA)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AsignacionUsuarioLinea (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario INTEGER NOT NULL,
                id_modulo INTEGER NOT NULL,
                FOREIGN KEY (id_usuario) REFERENCES Usuario(id) ON DELETE CASCADE,
                FOREIGN KEY (id_modulo) REFERENCES ModuloConfeccion(id)
            );
        """)
        print("- Tabla 'AsignacionUsuarioLinea' lista.")

        # 2fc. Tabla CausaParada (catálogo de causas no programadas)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS CausaParada (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            );
        """)
        cursor.execute("SELECT COUNT(*) FROM CausaParada")
        if cursor.fetchone()[0] == 0:
            causas = ["Falta de material", "Avería de máquina", "Cambio de operario",
                      "Problema de calidad", "Falta de energía", "Reunión/socialización",
                      "Espera de instrucciones", "Cambio de referencia", "Otro"]
            cursor.executemany("INSERT INTO CausaParada (nombre) VALUES (?)", [(c,) for c in causas])
        print("- Tabla 'CausaParada' lista.")

        # 2fd. Tabla RegistroProduccion (NUEVA - reemplaza ControlHoraHora)
        # id_hora quedó nullable: ya no se registra por hora operativa (marca real en created_at)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RegistroProduccion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                id_modulo INTEGER NOT NULL,
                id_hora INTEGER,
                id_orden INTEGER NOT NULL,
                id_operacion INTEGER,
                porcion_tiempo REAL,
                cantidad_operarios INTEGER,
                cantidad_producida INTEGER NOT NULL,
                cantidad_defectuosa INTEGER DEFAULT 0,
                observaciones TEXT,
                id_usuario INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_modulo) REFERENCES ModuloConfeccion(id),
                FOREIGN KEY (id_hora) REFERENCES HorasProduccion(id),
                FOREIGN KEY (id_orden) REFERENCES OrdenProduccion(id),
                FOREIGN KEY (id_operacion) REFERENCES Operacion(id),
                FOREIGN KEY (id_usuario) REFERENCES Usuario(id)
            );
        """)
        print("- Tabla 'RegistroProduccion' lista.")

        # 2fe. Tabla ParadaRegistro (una hora puede tener varias paradas)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ParadaRegistro (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_registro INTEGER NOT NULL,
                id_parada_programada INTEGER,
                id_causa INTEGER,
                tiempo_segundos INTEGER NOT NULL,
                descripcion TEXT,
                FOREIGN KEY (id_registro) REFERENCES RegistroProduccion(id) ON DELETE CASCADE,
                FOREIGN KEY (id_parada_programada) REFERENCES ParadasProgramadas(id),
                FOREIGN KEY (id_causa) REFERENCES CausaParada(id)
            );
        """)
        print("- Tabla 'ParadaRegistro' lista.")

        # 2g. Tabla AsignacionModulo (NUEVA)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AsignacionModulo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_orden INTEGER NOT NULL,
                id_modulo INTEGER NOT NULL,
                cantidad_asignada INTEGER NOT NULL,
                FOREIGN KEY (id_orden) REFERENCES OrdenProduccion(id),
                FOREIGN KEY (id_modulo) REFERENCES ModuloConfeccion(id)
            );
        """)
        print("- Tabla 'AsignacionModulo' lista.")

        # 3. Tabla Operacion
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Operacion (
                id INTEGER PRIMARY KEY,
                nombre_operacion TEXT NOT NULL,
                tiempo_segundos INTEGER NOT NULL,
                id_maquina INTEGER,
                id_seccion INTEGER,
                FOREIGN KEY (id_maquina) REFERENCES TipoMaquinaria(id),
                FOREIGN KEY (id_seccion) REFERENCES SeccionPrenda(id)
            );
        """)
        print("- Tabla 'Operacion' lista.")



        # 4. Tabla ReferenciaProducto (catálogo del modelo, SIN lote)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ReferenciaProducto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_referencia TEXT NOT NULL,
                especificaciones TEXT,
                foto TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("- Tabla 'ReferenciaProducto' lista.")

        # 4b. Tabla OrdenProduccion (el lote) [NUEVA]
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS OrdenProduccion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_referencia INTEGER NOT NULL,
                nombre_orden TEXT NOT NULL,
                cantidad_lote INTEGER NOT NULL,
                estado TEXT DEFAULT 'Abierta',
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_referencia) REFERENCES ReferenciaProducto(id)
            );
        """)
        print("- Tabla 'OrdenProduccion' lista.")

        # 5. Tabla ReferenciaDetalle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ReferenciaDetalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_referencia INTEGER NOT NULL,
                id_operacion INTEGER NOT NULL,
                letra_secuencia TEXT NOT NULL,
                predecesoras TEXT,
                orden_fila INTEGER,
                FOREIGN KEY (id_referencia) REFERENCES ReferenciaProducto(id) ON DELETE CASCADE,
                FOREIGN KEY (id_operacion) REFERENCES Operacion(id)
            );
        """)
        print("- Tabla 'ReferenciaDetalle' lista.")

        # 5b. Tabla Configuracion (parámetros globales de la plataforma)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Configuracion (
                clave TEXT PRIMARY KEY,
                valor TEXT
            );
        """)
        # Seed: modalidad de registro global (Diario | Por Hora)
        cursor.execute("SELECT COUNT(*) FROM Configuracion WHERE clave = 'modalidad_registro'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO Configuracion (clave, valor) VALUES ('modalidad_registro', 'Diario')")
        print("- Tabla 'Configuracion' lista.")

        # 2h. Tabla Materiales (catálogo de insumos) [NUEVA]
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Materiales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                unidad TEXT,
                costo_unitario REAL,
                proveedor TEXT,
                descripcion TEXT
            );
        """)
        print("- Tabla 'Materiales' lista.")

        # 2i. Tabla ReferenciaMaterial (BOM: materiales por referencia) [NUEVA]
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ReferenciaMaterial (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_referencia INTEGER NOT NULL,
                id_material INTEGER NOT NULL,
                cantidad_por_unidad REAL NOT NULL,
                merma_porcentaje REAL DEFAULT 0,
                nota TEXT,
                FOREIGN KEY (id_referencia) REFERENCES ReferenciaProducto(id) ON DELETE CASCADE,
                FOREIGN KEY (id_material) REFERENCES Materiales(id)
            );
        """)
        print("- Tabla 'ReferenciaMaterial' lista.")

        # MIGRACIÓN: Agregar columnas nuevas si no existen
        migraciones = [
            ("TipoMaquinaria", "descripcion", "TEXT"),
            ("TipoMaquinaria", "velocidad_tipica", "INTEGER"),
            ("TipoMaquinaria", "estado", "TEXT DEFAULT 'Activa'"),
            ("SeccionPrenda", "descripcion", "TEXT"),
            ("SeccionPrenda", "orden_proceso", "INTEGER"),
            ("ModuloConfeccion", "capacidad_maxima", "INTEGER"),
            ("ModuloConfeccion", "ubicacion", "TEXT"),
            ("ModuloConfeccion", "supervisor", "TEXT"),
            ("ModuloConfeccion", "estado", "TEXT DEFAULT 'Activo'"),
            ("HorasProduccion", "hora_inicio", "TEXT"),
            ("HorasProduccion", "hora_fin", "TEXT"),
            ("ParadasProgramadas", "tipo", "TEXT DEFAULT 'Opcional'"),
            ("ParadasProgramadas", "frecuencia", "TEXT DEFAULT 'Diaria'"),
            ("ReferenciaProducto", "especificaciones", "TEXT"),
            ("ReferenciaProducto", "foto", "TEXT"),
            ("ParadaRegistro", "descripcion", "TEXT"),
            ("RegistroProduccion", "id_operacion", "INTEGER"),
            ("TipoMaquinaria", "id_modulo", "INTEGER"),
            ("Empleados", "id_maquina", "INTEGER"),
            ("Empleados", "rol", "TEXT DEFAULT 'Operador'"),
            ("RegistroProduccion", "id_operador", "INTEGER"),
        ]
        
        for tabla, columna, tipo in migraciones:
            try:
                cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")
                print(f"- Migración: Columna '{columna}' agregada a {tabla}.")
            except sqlite3.OperationalError:
                pass  # La columna ya existe

        # MIGRACIÓN: Eliminar la columna 'turno' de Empleados (ya no se usa)
        try:
            cursor.execute("ALTER TABLE Empleados DROP COLUMN turno")
            print("- Migración: Columna 'turno' eliminada de Empleados.")
        except sqlite3.OperationalError:
            pass  # La columna ya no existe

        # Confirmar cambios
        conexion.commit()
        print("\nConfiguración finalizada con éxito. Todos los datos persistirán.")

    except sqlite3.Error as e:
        print(f"Error al configurar la base de datos: {e}")
    
    if conexion:
        conexion.close()

def obtener_maquinaria():
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT tm.id, tm.nombre, tm.descripcion, tm.velocidad_tipica, tm.estado,
               tm.id_modulo, m.nombre as nombre_modulo
        FROM TipoMaquinaria tm
        LEFT JOIN ModuloConfeccion m ON tm.id_modulo = m.id
        ORDER BY m.nombre, tm.nombre
    """)
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "descripcion": f[2], "velocidad_tipica": f[3],
             "estado": f[4] or 'Activa', "id_modulo": f[5], "nombre_modulo": f[6]} for f in filas]

def insertar_maquina(nombre, descripcion=None, velocidad_tipica=None, estado='Activa', id_modulo=None):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO TipoMaquinaria (nombre, descripcion, velocidad_tipica, estado, id_modulo) VALUES (?, ?, ?, ?, ?)", 
                   (nombre, descripcion, velocidad_tipica, estado, id_modulo))
    conexion.commit()
    conexion.close()

def obtener_secciones():
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, descripcion, orden_proceso FROM SeccionPrenda ORDER BY orden_proceso, id")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "descripcion": f[2], "orden_proceso": f[3]} for f in filas]

def insertar_seccion(nombre, descripcion=None, orden_proceso=None):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO SeccionPrenda (nombre, descripcion, orden_proceso) VALUES (?, ?, ?)",
                   (nombre, descripcion, orden_proceso))
    conexion.commit()
    conexion.close()

def obtener_operaciones_detalladas():
    conexion = _conexion()
    cursor = conexion.cursor()
    query = """
        SELECT 
            o.id, 
            o.nombre_operacion, 
            o.tiempo_segundos, 
            m.nombre as maquina, 
            s.nombre as seccion,
            o.id_maquina,
            o.id_seccion
        FROM Operacion o
        LEFT JOIN TipoMaquinaria m ON o.id_maquina = m.id
        LEFT JOIN SeccionPrenda s ON o.id_seccion = s.id
    """
    cursor.execute(query)
    filas = cursor.fetchall()
    conexion.close()
    return [
        {
            "id": f[0], 
            "nombre": f[1], 
            "tiempo": f[2], 
            "maquina": f[3] if f[3] else "N/A", 
            "seccion": f[4] if f[4] else "N/A",
            "id_maquina": f[5],
            "id_seccion": f[6]
        } for f in filas
    ]

def insertar_operacion(nombre, tiempo, id_maquina, id_seccion):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO Operacion (nombre_operacion, tiempo_segundos, id_maquina, id_seccion)
        VALUES (?, ?, ?, ?)
    """, (nombre, tiempo, id_maquina, id_seccion))
    conexion.commit()
    conexion.close()

def actualizar_operacion(id_operacion, nombre, tiempo, id_maquina, id_seccion):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE Operacion 
        SET nombre_operacion = ?, tiempo_segundos = ?, id_maquina = ?, id_seccion = ?
        WHERE id = ?
    """, (nombre, tiempo, id_maquina, id_seccion, id_operacion))
    conexion.commit()
    conexion.close()

def eliminar_operacion(id_operacion):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM Operacion WHERE id = ?", (id_operacion,))
    conexion.commit()
    conexion.close()

# --- REFERENCIAS ---

def crear_referencia(nombre, especificaciones=None, foto=None):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO ReferenciaProducto (nombre_referencia, especificaciones, foto) VALUES (?, ?, ?)", (nombre, especificaciones, foto))
    ref_id = cursor.lastrowid
    conexion.commit()
    conexion.close()
    return ref_id

def actualizar_referencia(id_ref, nombre, especificaciones=None, foto=None):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE ReferenciaProducto SET nombre_referencia = ?, especificaciones = ?, foto = ? WHERE id = ?",
                   (nombre, especificaciones, foto, id_ref))
    conexion.commit()
    conexion.close()

def actualizar_foto_referencia(id_ref, foto):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE ReferenciaProducto SET foto = ? WHERE id = ?", (foto, id_ref))
    conexion.commit()
    conexion.close()

def duplicar_referencia(id_origen, nuevo_nombre):
    conexion = _conexion()
    cursor = conexion.cursor()
    
    # 1. Obtener datos origen
    cursor.execute("SELECT especificaciones, foto FROM ReferenciaProducto WHERE id = ?", (id_origen,))
    row = cursor.fetchone()
    if not row:
        conexion.close()
        return None # No existe
    
    especificaciones, foto = row
    
    # 2. Crear nueva referencia
    cursor.execute("INSERT INTO ReferenciaProducto (nombre_referencia, especificaciones, foto) VALUES (?, ?, ?)",
                   (nuevo_nombre, especificaciones, foto))
    nuevo_id = cursor.lastrowid
    
    # 3. Copiar detalles
    cursor.execute("SELECT id_operacion, letra_secuencia, predecesoras, orden_fila FROM ReferenciaDetalle WHERE id_referencia = ?", (id_origen,))
    detalles = cursor.fetchall()
    
    for d in detalles:
        cursor.execute("""
            INSERT INTO ReferenciaDetalle (id_referencia, id_operacion, letra_secuencia, predecesoras, orden_fila)
            VALUES (?, ?, ?, ?, ?)
        """, (nuevo_id, d[0], d[1], d[2], d[3]))
        
    conexion.commit()
    conexion.close()
    return nuevo_id

def obtener_horas():
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, hora_inicio, hora_fin FROM HorasProduccion ORDER BY id")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "hora_inicio": f[2], "hora_fin": f[3]} for f in filas]

def insertar_hora(nombre, hora_inicio=None, hora_fin=None):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO HorasProduccion (nombre, hora_inicio, hora_fin) VALUES (?, ?, ?)",
                   (nombre, hora_inicio, hora_fin))
    conexion.commit()
    conexion.close()

def obtener_jornada_segundos():
    """Duración de la jornada (en segundos) según el catálogo de horas.
    Suma las duraciones (hora_fin - hora_inicio) de todas las horas del catálogo."""
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT hora_inicio, hora_fin FROM HorasProduccion WHERE hora_inicio IS NOT NULL AND hora_fin IS NOT NULL")
    filas = cursor.fetchall()
    conexion.close()

    from datetime import datetime
    total = 0
    formato = "%H:%M"
    for inicio, fin in filas:
        try:
            t0 = datetime.strptime(inicio.strip(), formato)
            t1 = datetime.strptime(fin.strip(), formato)
            total += (t1 - t0).total_seconds()
        except ValueError:
            continue
    return max(0, int(total))

def obtener_paradas():
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, tiempo_segundos, tipo, frecuencia FROM ParadasProgramadas")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "tiempo": f[2], "tipo": f[3] or 'Opcional', "frecuencia": f[4] or 'Diaria'} for f in filas]

def insertar_parada(nombre, tiempo, tipo='Opcional', frecuencia='Diaria'):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO ParadasProgramadas (nombre, tiempo_segundos, tipo, frecuencia) VALUES (?, ?, ?, ?)",
                   (nombre, tiempo, tipo, frecuencia))
    conexion.commit()
    conexion.close()

# --- ASIGNACIÓN DE REFERENCIAS ---

def obtener_asignaciones():
    conexion = _conexion()
    cursor = conexion.cursor()
    query = """
        SELECT a.id, o.nombre_orden, r.nombre_referencia, m.nombre, a.cantidad_asignada, o.cantidad_lote, o.id
        FROM AsignacionModulo a
        JOIN OrdenProduccion o ON a.id_orden = o.id
        JOIN ReferenciaProducto r ON o.id_referencia = r.id
        JOIN ModuloConfeccion m ON a.id_modulo = m.id
        ORDER BY a.id DESC
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conexion.close()
    return [{
        "id": row[0],
        "orden": row[1],
        "referencia": row[2],
        "modulo": row[3],
        "cantidad": row[4],
        "total_lote": row[5],
        "id_orden": row[6]
    } for row in data]

def obtener_disponibilidad(id_orden):
    conexion = _conexion()
    cursor = conexion.cursor()
    
    # 1. Obtener lote total (de la orden)
    cursor.execute("SELECT cantidad_lote FROM OrdenProduccion WHERE id = ?", (id_orden,))
    res = cursor.fetchone()
    if not res:
        conexion.close()
        return None
    total_lote = res[0]
    
    # 2. Obtener ya asignado (por orden)
    cursor.execute("SELECT SUM(cantidad_asignada) FROM AsignacionModulo WHERE id_orden = ?", (id_orden,))
    res_asignado = cursor.fetchone()
    total_asignado = res_asignado[0] if res_asignado[0] else 0
    
    conexion.close()
    return {
        "total": total_lote,
        "asignado": total_asignado,
        "disponible": total_lote - total_asignado
    }

def asignar_referencia_modulo(id_orden, id_mod, cantidad):
    disp = obtener_disponibilidad(id_orden)
    if not disp:
        return {"error": "Orden no encontrada"}
    
    if cantidad > disp['disponible']:
        return {"error": f"Excede disponibilidad. Disponible: {disp['disponible']}"}
    
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO AsignacionModulo (id_orden, id_modulo, cantidad_asignada) VALUES (?, ?, ?)", 
                   (id_orden, id_mod, cantidad))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Asignado correctamente"}

def eliminar_asignacion(id_asignacion):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM AsignacionModulo WHERE id = ?", (id_asignacion,))
    conexion.commit()
    conexion.close()

def actualizar_asignacion(id_asignacion, nueva_cantidad):
    conexion = _conexion()
    cursor = conexion.cursor()
    
    # Obtener datos actuales
    cursor.execute("SELECT id_orden, cantidad_asignada FROM AsignacionModulo WHERE id = ?", (id_asignacion,))
    row = cursor.fetchone()
    if not row:
        conexion.close()
        return {"error": "Asignación no encontrada"}
    
    id_orden, cantidad_anterior = row
    
    # Verificar disponibilidad con el ajuste
    disp = obtener_disponibilidad(id_orden)
    # Al hacer update, el 'disponible' real es: disponible_actual + cantidad_anterior
    max_posible = disp['disponible'] + cantidad_anterior
    
    if nueva_cantidad > max_posible:
        conexion.close()
        return {"error": f"Excede máximo posible ({max_posible})"}
        
    cursor.execute("UPDATE AsignacionModulo SET cantidad_asignada = ? WHERE id = ?", (nueva_cantidad, id_asignacion))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Actualizado correctamente"}

def obtener_ordenes_disponibles():
    """Órdenes abiertas cuyo lote > asignado."""
    conexion = _conexion()
    cursor = conexion.cursor()
    query = """
        SELECT o.id, o.nombre_orden, r.nombre_referencia
        FROM OrdenProduccion o
        JOIN ReferenciaProducto r ON o.id_referencia = r.id
        LEFT JOIN AsignacionModulo a ON o.id = a.id_orden
        GROUP BY o.id
        HAVING o.cantidad_lote > COALESCE(SUM(a.cantidad_asignada), 0)
        AND o.estado != 'Cerrada'
    """
    cursor.execute(query)
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre_orden": f[1], "referencia": f[2]} for f in filas]

def obtener_referencias():
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre_referencia, especificaciones, foto, fecha_creacion FROM ReferenciaProducto ORDER BY id DESC")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "especificaciones": f[2], "foto": f[3], "fecha": f[4]} for f in filas]

def eliminar_referencia(id_ref):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # No permitir eliminar si tiene órdenes de producción asociadas
    cursor.execute("SELECT COUNT(*) FROM OrdenProduccion WHERE id_referencia = ?", (id_ref,))
    if cursor.fetchone()[0] > 0:
        conexion.close()
        return {"error": "No se puede eliminar: la referencia tiene órdenes de producción asociadas. Elimine o reasigne las órdenes primero."}

    try:
        cursor.execute("DELETE FROM ReferenciaProducto WHERE id = ?", (id_ref,))
        conexion.commit()
        conexion.close()
        return {"mensaje": "Referencia eliminada"}
    except sqlite3.IntegrityError as e:
        conexion.close()
        return {"error": "No se puede eliminar la referencia porque tiene datos asociados."}


# --- ORDENES DE PRODUCCIÓN (LOTES) ---

def _obtener_operaciones_referencia(cursor, id_referencia):
    """Operaciones (actividades) de la referencia."""
    cursor.execute("SELECT id_operacion FROM ReferenciaDetalle WHERE id_referencia = ?", (id_referencia,))
    return [r[0] for r in cursor.fetchall()]

def _calcular_gorras_completas(cursor, id_orden):
    """Gorras TERMINADAS de una orden: el mínimo de producción entre TODAS sus actividades.
    Una gorra está completa solo si pasó por cada actividad (A..Q) del diagrama de la referencia."""
    cursor.execute("SELECT id_referencia FROM OrdenProduccion WHERE id = ?", (id_orden,))
    fila = cursor.fetchone()
    if not fila:
        return 0
    id_referencia = fila[0]
    ops = _obtener_operaciones_referencia(cursor, id_referencia)
    if not ops:
        return 0

    # Producción por cada actividad de esta orden en UNA sola consulta
    cursor.execute("""
        SELECT id_operacion, COALESCE(SUM(cantidad_producida),0)
        FROM RegistroProduccion
        WHERE id_orden = ? AND id_operacion IN (%s)
        GROUP BY id_operacion
    """ % ",".join("?" * len(ops)), [id_orden] + ops)
    producido = dict(cursor.fetchall())

    return min([producido.get(op, 0) for op in ops])

def _calcular_gorras_completas_por_orden(cursor, ids_orden):
    """Gorras completas para varias órdenes en una sola consulta (sin N+1)."""
    if not ids_orden:
        return {}
    cursor.execute("SELECT id, id_referencia FROM OrdenProduccion WHERE id IN (%s)" % ",".join("?" * len(ids_orden)), ids_orden)
    orden_ref = dict(cursor.fetchall())

    cursor.execute("SELECT id_referencia, id_operacion FROM ReferenciaDetalle WHERE id_referencia IN (%s)" % ",".join("?" * len(set(orden_ref.values()))), list(set(orden_ref.values())))
    ops_por_ref = {}
    for id_ref, id_op in cursor.fetchall():
        ops_por_ref.setdefault(id_ref, []).append(id_op)

    cursor.execute("""
        SELECT id_orden, id_operacion, COALESCE(SUM(cantidad_producida),0)
        FROM RegistroProduccion
        WHERE id_orden IN (%s)
        GROUP BY id_orden, id_operacion
    """ % ",".join("?" * len(ids_orden)), ids_orden)
    producido = {}
    for id_orden, id_operacion, cant in cursor.fetchall():
        producido.setdefault(id_orden, {})[id_operacion] = cant

    resultado = {}
    for id_orden in ids_orden:
        id_ref = orden_ref.get(id_orden)
        ops = ops_por_ref.get(id_ref, [])
        if not ops:
            resultado[id_orden] = 0
        else:
            resultado[id_orden] = min([producido.get(id_orden, {}).get(op, 0) for op in ops])
    return resultado

def obtener_ordenes():
    conexion = _conexion()
    cursor = conexion.cursor()
    query = """
        SELECT o.id, o.nombre_orden, r.nombre_referencia, o.cantidad_lote,
               o.estado, o.fecha_creacion, r.id as id_referencia
        FROM OrdenProduccion o
        JOIN ReferenciaProducto r ON o.id_referencia = r.id
        ORDER BY o.id DESC
    """
    cursor.execute(query)
    filas = cursor.fetchall()
    ids = [f[0] for f in filas]
    completas = _calcular_gorras_completas_por_orden(cursor, ids)

    resultado = []
    for f in filas:
        id_orden = f[0]
        cantidad_lote = f[3]
        comp = completas.get(id_orden, 0)
        resultado.append({
            "id": id_orden,
            "nombre_orden": f[1],
            "referencia": f[2],
            "cantidad_lote": cantidad_lote,
            "estado": f[4],
            "fecha_creacion": f[5],
            "id_referencia": f[6],
            "gorras_completas": comp,
            "produccion_total": 0,
            "porcentaje_cumplimiento": round(comp / cantidad_lote * 100, 1) if cantidad_lote and cantidad_lote > 0 else 0
        })
    conexion.close()
    return resultado

def crear_orden(id_referencia, nombre_orden, cantidad_lote):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO OrdenProduccion (id_referencia, nombre_orden, cantidad_lote)
        VALUES (?, ?, ?)
    """, (id_referencia, nombre_orden, cantidad_lote))
    orden_id = cursor.lastrowid
    conexion.commit()
    conexion.close()
    return orden_id

def actualizar_orden(id_orden, cantidad_lote=None, estado=None):
    conexion = _conexion()
    cursor = conexion.cursor()
    campos = []
    valores = []
    if cantidad_lote is not None:
        campos.append("cantidad_lote = ?")
        valores.append(cantidad_lote)
    if estado:
        campos.append("estado = ?")
        valores.append(estado)
    if not campos:
        conexion.close()
        return {"mensaje": "Nada que actualizar"}
    valores.append(id_orden)
    cursor.execute(f"UPDATE OrdenProduccion SET {', '.join(campos)} WHERE id = ?", valores)
    conexion.commit()
    conexion.close()
    return {"mensaje": "Orden actualizada"}

def _cerrar_orden_si_completa(cursor, id_orden):
    """Si las GORRAS COMPLETAS de la orden alcanzan (o superan) el lote, la cierra."""
    cursor.execute("SELECT cantidad_lote FROM OrdenProduccion WHERE id = ?", (id_orden,))
    fila = cursor.fetchone()
    if not fila:
        return
    cantidad_lote = fila[0]
    completas = _calcular_gorras_completas(cursor, id_orden)
    if cantidad_lote and cantidad_lote > 0 and completas >= cantidad_lote:
        cursor.execute("UPDATE OrdenProduccion SET estado = 'Cerrada' WHERE id = ? AND estado != 'Cerrada'", (id_orden,))

def obtener_cumplimiento_orden(id_orden):
    """Devuelve gorras completas, lote y % de cumplimiento de una orden.
    El cumplimiento se basa en gorras TERMINADAS (mínimo de producción entre todas las actividades)."""
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT cantidad_lote FROM OrdenProduccion WHERE id = ?", (id_orden,))
    fila = cursor.fetchone()
    if not fila:
        conexion.close()
        return None
    cantidad_lote = fila[0]
    completas = _calcular_gorras_completas(cursor, id_orden)
    conexion.close()
    return {
        "cantidad_lote": cantidad_lote,
        "gorras_completas": completas,
        "porcentaje_cumplimiento": round(completas / cantidad_lote * 100, 1) if cantidad_lote and cantidad_lote > 0 else 0
    }

def eliminar_orden(id_orden):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM OrdenProduccion WHERE id = ?", (id_orden,))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Orden eliminada"}


# ============================================================
# MATERIALES (BOM)
# ============================================================

def obtener_materiales():
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, unidad, costo_unitario, proveedor, descripcion FROM Materiales ORDER BY nombre")
    filas = cursor.fetchall()
    conexion.close()
    return [{
        "id": f[0],
        "nombre": f[1],
        "unidad": f[2],
        "costo_unitario": f[3],
        "proveedor": f[4],
        "descripcion": f[5]
    } for f in filas]

def insertar_material(nombre, unidad=None, costo_unitario=None, proveedor=None, descripcion=None):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO Materiales (nombre, unidad, costo_unitario, proveedor, descripcion)
        VALUES (?, ?, ?, ?, ?)
    """, (nombre, unidad, costo_unitario, proveedor, descripcion))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Material guardado", "id": cursor.lastrowid}

def actualizar_material(id_material, nombre, unidad=None, costo_unitario=None, proveedor=None, descripcion=None):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE Materiales
        SET nombre=?, unidad=?, costo_unitario=?, proveedor=?, descripcion=?
        WHERE id=?
    """, (nombre, unidad, costo_unitario, proveedor, descripcion, id_material))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Material actualizado"}

def eliminar_material(id_material):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM Materiales WHERE id = ?", (id_material,))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Material eliminado"}

def obtener_materiales_referencia(id_referencia):
    """Materiales asociados a una referencia (BOM)."""
    conexion = _conexion()
    cursor = conexion.cursor()
    query = """
        SELECT rm.id, m.nombre, m.unidad, rm.cantidad_por_unidad,
               rm.merma_porcentaje, rm.nota, m.id as id_material,
               m.costo_unitario
        FROM ReferenciaMaterial rm
        JOIN Materiales m ON rm.id_material = m.id
        WHERE rm.id_referencia = ?
        ORDER BY m.nombre
    """
    cursor.execute(query, (id_referencia,))
    filas = cursor.fetchall()
    conexion.close()
    return [{
        "id": f[0],
        "nombre": f[1],
        "unidad": f[2],
        "cantidad_por_unidad": f[3],
        "merma_porcentaje": f[4] or 0,
        "nota": f[5],
        "id_material": f[6],
        "costo_unitario": f[7]
    } for f in filas]

def agregar_material_referencia(id_referencia, id_material, cantidad_por_unidad, merma_porcentaje=0, nota=None):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO ReferenciaMaterial (id_referencia, id_material, cantidad_por_unidad, merma_porcentaje, nota)
        VALUES (?, ?, ?, ?, ?)
    """, (id_referencia, id_material, cantidad_por_unidad, merma_porcentaje, nota))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Material asociado a la referencia"}

def eliminar_material_referencia(id_material_ref):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM ReferenciaMaterial WHERE id = ?", (id_material_ref,))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Material removido de la referencia"}

def calcular_materiales_orden(id_orden):
    """Calcula el requerimiento total de materiales para un lote:
    cantidad_por_unidad * cantidad_lote * (1 + merma/100)."""
    conexion = _conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT cantidad_lote, id_referencia, nombre_orden FROM OrdenProduccion WHERE id = ?", (id_orden,))
    fila = cursor.fetchone()
    if not fila:
        conexion.close()
        return None
    cantidad_lote, id_referencia, nombre_orden = fila

    cursor.execute("""
        SELECT m.nombre, m.unidad, rm.cantidad_por_unidad, rm.merma_porcentaje,
               rm.nota, m.costo_unitario
        FROM ReferenciaMaterial rm
        JOIN Materiales m ON rm.id_material = m.id
        WHERE rm.id_referencia = ?
        ORDER BY m.nombre
    """, (id_referencia,))
    filas = cursor.fetchall()
    conexion.close()

    materiales = []
    total_costo = 0.0
    for f in filas:
        nombre, unidad, cantidad_unidad, merma, nota, costo = f
        factor = 1 + (merma or 0) / 100.0
        requerido = round(cantidad_unidad * cantidad_lote * factor, 2)
        costo_total = round(requerido * (costo or 0), 2) if costo else 0
        total_costo += costo_total
        materiales.append({
            "nombre": nombre,
            "unidad": unidad,
            "cantidad_por_unidad": cantidad_unidad,
            "merma_porcentaje": merma or 0,
            "cantidad_requerida": requerido,
            "nota": nota,
            "costo_estimado": costo_total
        })

    return {
        "nombre_orden": nombre_orden,
        "cantidad_lote": cantidad_lote,
        "materiales": materiales,
        "total_costo_estimado": round(total_costo, 2)
    }

def agregar_detalle_referencia(id_ref, id_op, letra, predecesoras, orden):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO ReferenciaDetalle (id_referencia, id_operacion, letra_secuencia, predecesoras, orden_fila)
        VALUES (?, ?, ?, ?, ?)
    """, (id_ref, id_op, letra, predecesoras, orden))
    conexion.commit()
    conexion.close()

def obtener_detalles_referencia(id_ref):
    conexion = _conexion()
    cursor = conexion.cursor()
    query = """
        SELECT 
            rd.id, 
            rd.letra_secuencia, 
            o.nombre_operacion, 
            tm.nombre as maquina, 
            o.tiempo_segundos, 
            rd.predecesoras,
            rd.orden_fila,
            o.id as id_operacion,
            tm.id_modulo as id_modulo_maquina,
            tm.id as id_maquina
        FROM ReferenciaDetalle rd
        INNER JOIN Operacion o ON rd.id_operacion = o.id
        LEFT JOIN TipoMaquinaria tm ON o.id_maquina = tm.id
        WHERE rd.id_referencia = ?
        ORDER BY rd.orden_fila ASC
    """
    cursor.execute(query, (id_ref,))
    filas = cursor.fetchall()
    conexion.close()
    return [
        {
            "id": f[0], 
            "letra": f[1], 
            "nombre_operacion": f[2], 
            "maquina": f[3] if f[3] else "N/A", 
            "tiempo": f[4], 
            "predecesoras": f[5],
            "orden": f[6],
            "id_operacion": f[7],
            "id_modulo_maquina": f[8],
            "id_maquina": f[9]
        } for f in filas
    ]

def eliminar_detalle(id_detalle):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM ReferenciaDetalle WHERE id = ?", (id_detalle,))
    conexion.commit()
    conexion.close()

def obtener_modulos():
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, capacidad_maxima, ubicacion, supervisor, estado FROM ModuloConfeccion")
    filas = cursor.fetchall()
    cursor.execute("SELECT modulo_asignado, COUNT(*) FROM Empleados WHERE rol='Operador' AND estado='Activo' AND modulo_asignado IS NOT NULL GROUP BY modulo_asignado")
    conteo_operadores = dict(cursor.fetchall())
    conexion.close()
    return [{
        "id": f[0], "nombre": f[1], "capacidad_maxima": f[2], "ubicacion": f[3],
        "supervisor": f[4], "estado": f[5] or 'Activo',
        "operadores_actuales": conteo_operadores.get(f[0], 0)
    } for f in filas]

def insertar_modulo(nombre, capacidad_maxima=None, ubicacion=None, supervisor=None, estado='Activo'):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO ModuloConfeccion (nombre, capacidad_maxima, ubicacion, supervisor, estado) VALUES (?, ?, ?, ?, ?)",
                   (nombre, capacidad_maxima, ubicacion, supervisor, estado))
    conexion.commit()
    conexion.close()

# --- FUNCIONES CONTROL HORA A HORA ---

def obtener_referencias_por_modulo(id_modulo):
    """
    Obtiene las asignaciones (orden + referencia) de un módulo específico.
    """
    conexion = _conexion()
    cursor = conexion.cursor()
    query = """
        SELECT a.id, r.nombre_referencia, r.id, o.id, o.nombre_orden
        FROM AsignacionModulo a
        JOIN OrdenProduccion o ON a.id_orden = o.id
        JOIN ReferenciaProducto r ON o.id_referencia = r.id
        WHERE a.id_modulo = ?
    """
    cursor.execute(query, (id_modulo,))
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "id_referencia": f[2], "id_orden": f[3], "nombre_orden": f[4]} for f in filas]

def obtener_operadores_linea(id_modulo):
    """Operadores activos asignados a una línea (módulo), con su máquina/puesto."""
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT e.id, e.nombre, e.id_maquina, COALESCE(tm.nombre, '') AS nombre_maquina,
               COALESCE(tm.id_modulo, e.modulo_asignado) AS id_modulo_efectivo
        FROM Empleados e
        LEFT JOIN TipoMaquinaria tm ON e.id_maquina = tm.id
        WHERE e.rol = 'Operador'
          AND e.estado = 'Activo'
          AND e.modulo_asignado = ?
        ORDER BY e.nombre
    """, (id_modulo,))
    filas = cursor.fetchall()
    conexion.close()
    return [
        {
            "id_empleado": f[0],
            "nombre": f[1],
            "id_maquina": f[2],
            "nombre_maquina": f[3] or '-',
            "id_modulo": f[4] or id_modulo
        }
        for f in filas
    ]

def obtener_actividades_por_orden(id_orden):
    """Actividades de la secuencia de la referencia de una orden, con su máquina y tiempo."""
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT rd.id_operacion, o.nombre_operacion, o.id_maquina,
               COALESCE(o.tiempo_segundos, 0), rd.letra_secuencia, rd.orden_fila
        FROM OrdenProduccion ord
        JOIN ReferenciaDetalle rd ON rd.id_referencia = ord.id_referencia
        JOIN Operacion o ON rd.id_operacion = o.id
        WHERE ord.id = ?
        ORDER BY rd.orden_fila
    """, (id_orden,))
    filas = cursor.fetchall()
    conexion.close()
    return [
        {
            "id_operacion": f[0],
            "nombre": f[1],
            "id_maquina": f[2],
            "tiempo_segundos": f[3] or 0,
            "letra": f[4],
            "orden": f[5]
        }
        for f in filas
    ]

# ============================================================
# EMPLEADOS
# ============================================================

def obtener_empleados():
    """Retorna todos los empleados con módulo y máquina asignados."""
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT e.id, e.nombre, e.numero_documento, e.cargo, e.rol,
               e.fecha_ingreso, e.estado, e.telefono, e.email,
               e.modulo_asignado, m.nombre as nombre_modulo,
               e.id_maquina, tm.nombre as nombre_maquina
        FROM Empleados e
        LEFT JOIN ModuloConfeccion m ON e.modulo_asignado = m.id
        LEFT JOIN TipoMaquinaria tm ON e.id_maquina = tm.id
        ORDER BY e.nombre
    """)
    filas = cursor.fetchall()
    conexion.close()
    return [
        {
            "id": f[0],
            "nombre": f[1],
            "numero_documento": f[2],
            "cargo": f[3],
            "rol": f[4],
            "fecha_ingreso": f[5],
            "estado": f[6],
            "telefono": f[7],
            "email": f[8],
            "modulo_asignado": f[9],
            "nombre_modulo": f[10],
            "id_maquina": f[11],
            "nombre_maquina": f[12]
        }
        for f in filas
    ]


def obtener_empleado(id_empleado):
    """Retorna un empleado específico por ID."""
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT e.id, e.nombre, e.numero_documento, e.cargo, e.rol,
               e.fecha_ingreso, e.estado, e.telefono, e.email,
               e.modulo_asignado, m.nombre as nombre_modulo,
               e.id_maquina, tm.nombre as nombre_maquina
        FROM Empleados e
        LEFT JOIN ModuloConfeccion m ON e.modulo_asignado = m.id
        LEFT JOIN TipoMaquinaria tm ON e.id_maquina = tm.id
        WHERE e.id = ?
    """, (id_empleado,))
    fila = cursor.fetchone()
    conexion.close()
    if fila:
        return {
            "id": fila[0],
            "nombre": fila[1],
            "numero_documento": fila[2],
            "cargo": fila[3],
            "rol": fila[4],
            "fecha_ingreso": fila[5],
            "estado": fila[6],
            "telefono": fila[7],
            "email": fila[8],
            "modulo_asignado": fila[9],
            "nombre_modulo": fila[10],
            "id_maquina": fila[11],
            "nombre_maquina": fila[12]
        }
    return None


def _validar_maquina_modulo(cursor, id_maquina, modulo_asignado):
    """Valida que la máquina del empleado pertenezca al módulo asignado.
    Si el empleado tiene máquina y módulo, deben coincidir. Retorna error o None."""
    if id_maquina and modulo_asignado:
        cursor.execute("SELECT id_modulo FROM TipoMaquinaria WHERE id = ?", (id_maquina,))
        r = cursor.fetchone()
        if r and r[0] and r[0] != int(modulo_asignado):
            return {"error": "La máquina del empleado pertenece a otro módulo. La máquina debe estar en el mismo módulo asignado."}
    return None


def _deducir_modulo_maquina(cursor, id_maquina):
    """Devuelve el módulo al que pertenece la máquina (o None)."""
    if not id_maquina:
        return None
    cursor.execute("SELECT id_modulo FROM TipoMaquinaria WHERE id = ?", (id_maquina,))
    r = cursor.fetchone()
    return r[0] if r else None


def _verificar_capacidad_modulo(cursor, id_modulo, id_empleado_excluir=None):
    """Cuenta operadores ACTIVOS del módulo y valida contra 'capacidad_maxima'.
    Retorna None si hay cupo, o un dict de error. Excluye id_empleado_excluir (para updates)."""
    cursor.execute("SELECT capacidad_maxima FROM ModuloConfeccion WHERE id = ?", (id_modulo,))
    fila = cursor.fetchone()
    if not fila:
        return {"error": "El módulo no existe"}
    capacidad = fila[0]
    if not capacidad:
        return None  # Sin límite definido → no validar

    query = "SELECT COUNT(*) FROM Empleados WHERE rol = 'Operador' AND estado = 'Activo' AND modulo_asignado = ?"
    params = [id_modulo]
    if id_empleado_excluir:
        query += " AND id != ?"
        params.append(id_empleado_excluir)
    cursor.execute(query, params)
    ocupados = cursor.fetchone()[0]

    if ocupados >= capacidad:
        return {"error": f"El módulo está completo ({ocupados}/{capacidad} operadores). No puede asignar más operadores."}
    return None


def insertar_empleado(nombre, numero_documento, cargo, rol='Operador',
                      fecha_ingreso=None, estado='Activo', telefono=None, email=None,
                      modulo_asignado=None, id_maquina=None):
    """Inserta un nuevo empleado.
    Operador → opera una máquina (modulo_asignado = módulo de la máquina).
    Supervisor → supervisa uno o varios módulos (líneas a las que tiene acceso)."""
    conexion = _conexion()
    cursor = conexion.cursor()
    try:
        # Validaciones por rol
        if rol == 'Supervisor':
            id_maquina = None
            modulo_asignado = None
        else:  # Operador
            if not id_maquina:
                conexion.close()
                return {"error": "Un operador debe tener una máquina asignada."}
            modulo_asignado = _deducir_modulo_maquina(cursor, id_maquina)
            if not modulo_asignado:
                conexion.close()
                return {"error": "La máquina del operador no está asignada a ninguna línea."}

        # Capacidad del módulo (solo operadores con módulo)
        if rol == 'Operador' and modulo_asignado:
            err_cap = _verificar_capacidad_modulo(cursor, modulo_asignado)
            if err_cap:
                conexion.close()
                return err_cap

        cursor.execute("""
            INSERT INTO Empleados (nombre, numero_documento, cargo, rol,
                                   fecha_ingreso, estado, telefono, email, modulo_asignado, id_maquina)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, numero_documento, cargo, rol, fecha_ingreso,
              estado, telefono, email, modulo_asignado, id_maquina))
        conexion.commit()
        nuevo_id = cursor.lastrowid

        conexion.close()
        return {"mensaje": "Empleado guardado con éxito", "id": nuevo_id}
    except sqlite3.IntegrityError:
        conexion.close()
        return {"error": "El número de documento ya existe"}


def actualizar_empleado(id_empleado, nombre, numero_documento, cargo, rol='Operador',
                        fecha_ingreso=None, estado='Activo', telefono=None,
                        email=None, modulo_asignado=None, id_maquina=None):
    """Actualiza un empleado existente."""
    conexion = _conexion()
    cursor = conexion.cursor()
    try:
        if rol == 'Supervisor':
            id_maquina = None
            modulo_asignado = None
        else:
            if not id_maquina:
                conexion.close()
                return {"error": "Un operador debe tener una máquina asignada."}
            modulo_asignado = _deducir_modulo_maquina(cursor, id_maquina)
            if not modulo_asignado:
                conexion.close()
                return {"error": "La máquina del operador no está asignada a ninguna línea."}

        # Capacidad del módulo (solo operadores con módulo), excluyendo al propio empleado en updates
        if rol == 'Operador' and modulo_asignado:
            err_cap = _verificar_capacidad_modulo(cursor, modulo_asignado, id_empleado_excluir=id_empleado)
            if err_cap:
                conexion.close()
                return err_cap

        cursor.execute("""
            UPDATE Empleados
            SET nombre=?, numero_documento=?, cargo=?, rol=?,
                fecha_ingreso=?, estado=?, telefono=?, email=?, modulo_asignado=?, id_maquina=?
            WHERE id=?
        """, (nombre, numero_documento, cargo, rol, fecha_ingreso,
              estado, telefono, email, modulo_asignado, id_maquina, id_empleado))
        conexion.commit()

        conexion.close()
        return {"mensaje": "Empleado actualizado con éxito"}
    except sqlite3.IntegrityError:
        conexion.close()
        return {"error": "El número de documento ya existe"}


def eliminar_empleado(id_empleado):
    """Elimina un empleado por ID."""
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM Empleados WHERE id = ?", (id_empleado,))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Empleado eliminado con éxito"}


# ============================================================
# USUARIOS Y LOGIN
# ============================================================

def verificar_login(nombre_usuario, password):
    """Valida credenciales y devuelve el usuario con sus líneas asignadas."""
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT u.id, u.nombre_usuario, u.rol, u.id_empleado, e.nombre, e.modulo_asignado, e.rol as empleado_rol
        FROM Usuario u
        LEFT JOIN Empleados e ON u.id_empleado = e.id
        WHERE u.nombre_usuario = ? AND u.password = ? AND u.activo = 1
    """, (nombre_usuario, password))
    fila = cursor.fetchone()
    if not fila:
        conexion.close()
        return None

    usuario = {
        "id": fila[0],
        "nombre_usuario": fila[1],
        "rol": fila[2],
        "id_empleado": fila[3],
        "nombre_empleado": fila[4],
        "modulo_asignado_empleado": fila[5],
        "empleado_rol": fila[6]
    }

    # Admin ve TODAS las líneas de la planta
    if usuario["rol"] == 'Admin':
        cursor.execute("SELECT id, nombre FROM ModuloConfeccion ORDER BY id")
        usuario["lineas"] = [{"id": r[0], "nombre": r[1]} for r in cursor.fetchall()]
        conexion.close()
        return usuario

    # Líneas habilitadas: para supervisor SIEMPRE desde AsignacionUsuarioLinea;
    # para operador fallback al módulo del empleado si no hay asignación explícita.
    cursor.execute("SELECT m.id, m.nombre FROM AsignacionUsuarioLinea aul JOIN ModuloConfeccion m ON aul.id_modulo = m.id WHERE aul.id_usuario = ?", (usuario["id"],))
    lineas = [{"id": r[0], "nombre": r[1]} for r in cursor.fetchall()]
    if not lineas and usuario["empleado_rol"] != 'Supervisor' and usuario["modulo_asignado_empleado"]:
        cursor.execute("SELECT id, nombre FROM ModuloConfeccion WHERE id = ?", (usuario["modulo_asignado_empleado"],))
        r = cursor.fetchone()
        if r:
            lineas = [{"id": r[0], "nombre": r[1]}]

    usuario["lineas"] = lineas
    conexion.close()
    return usuario

def obtener_configuracion(clave, default=None):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT valor FROM Configuracion WHERE clave = ?", (clave,))
    fila = cursor.fetchone()
    conexion.close()
    return fila[0] if fila else default

def guardar_configuracion(clave, valor):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO Configuracion (clave, valor) VALUES (?, ?) ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor", (clave, valor))
    conexion.commit()
    conexion.close()

def obtener_usuarios():
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT u.id, u.nombre_usuario, u.rol, u.id_empleado, e.nombre, u.activo
        FROM Usuario u
        LEFT JOIN Empleados e ON u.id_empleado = e.id
        ORDER BY u.nombre_usuario
    """)
    filas = cursor.fetchall()

    # Líneas por usuario (asignación + módulo del empleado como respaldo)
    cursor.execute("""
        SELECT aul.id_usuario, m.nombre
        FROM AsignacionUsuarioLinea aul
        JOIN ModuloConfeccion m ON aul.id_modulo = m.id
        ORDER BY m.nombre
    """)
    lineas_dict = {}
    for id_usuario, nombre_modulo in cursor.fetchall():
        lineas_dict.setdefault(id_usuario, []).append(nombre_modulo)

    modulos_empleado = {}
    for f in filas:
        id_emp = f[3]
        if id_emp and id_emp not in modulos_empleado:
            cursor.execute("SELECT nombre FROM ModuloConfeccion WHERE id = (SELECT modulo_asignado FROM Empleados WHERE id = ?)", (id_emp,))
            r = cursor.fetchone()
            modulos_empleado[id_emp] = [r[0]] if r and r[0] else []

    conexion.close()
    return [{
        "id": f[0], "nombre_usuario": f[1], "rol": f[2],
        "id_empleado": f[3], "nombre_empleado": f[4], "activo": f[5],
        "lineas": lineas_dict.get(f[0], None) or modulos_empleado.get(f[3], [])
    } for f in filas]

def crear_usuario(nombre_usuario, password, rol, id_empleado):
    conexion = _conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("INSERT INTO Usuario (nombre_usuario, password, rol, id_empleado) VALUES (?, ?, ?, ?)",
                       (nombre_usuario, password, rol, id_empleado))
        conexion.commit()
        nuevo_id = cursor.lastrowid
        conexion.close()
        return {"mensaje": "Usuario creado", "id": nuevo_id}
    except sqlite3.IntegrityError:
        conexion.close()
        return {"error": "El nombre de usuario ya existe"}

def actualizar_usuario(id_usuario, nombre_usuario, password, rol, id_empleado):
    conexion = _conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("UPDATE Usuario SET nombre_usuario=?, password=?, rol=?, id_empleado=? WHERE id=?",
                       (nombre_usuario, password, rol, id_empleado, id_usuario))
        conexion.commit()
        conexion.close()
        return {"mensaje": "Usuario actualizado"}
    except sqlite3.IntegrityError:
        conexion.close()
        return {"error": "El nombre de usuario ya existe"}

def eliminar_usuario(id_usuario):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM Usuario WHERE id = ?", (id_usuario,))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Usuario eliminado"}

def obtener_lineas_usuario(id_usuario):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_modulo FROM AsignacionUsuarioLinea WHERE id_usuario = ?", (id_usuario,))
    filas = cursor.fetchall()
    conexion.close()
    return [f[0] for f in filas]

def asignar_lineas_usuario(id_usuario, ids_modulos):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM AsignacionUsuarioLinea WHERE id_usuario = ?", (id_usuario,))
    for mid in ids_modulos:
        cursor.execute("INSERT INTO AsignacionUsuarioLinea (id_usuario, id_modulo) VALUES (?, ?)", (id_usuario, mid))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Líneas asignadas"}

def obtener_causas_parada():
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM CausaParada ORDER BY nombre")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1]} for f in filas]

def insertar_causa_parada(nombre):
    conexion = _conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("INSERT INTO CausaParada (nombre) VALUES (?)", (nombre,))
        conexion.commit()
        conexion.close()
        return {"mensaje": "Causa guardada"}
    except sqlite3.IntegrityError:
        conexion.close()
        return {"error": "La causa ya existe"}

def eliminar_causa_parada(id_causa):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM CausaParada WHERE id = ?", (id_causa,))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Causa eliminada"}


# ============================================================
# REGISTRO DE PRODUCCIÓN (NUEVO)
# ============================================================

def obtener_registros_dia(fecha_desde, fecha_hasta=None, id_usuario=None):
    fecha_hasta = fecha_hasta or fecha_desde
    conexion = _conexion()
    cursor = conexion.cursor()
    query = """
        SELECT r.id, r.fecha, m.nombre, o.nombre_orden, ref.nombre_referencia,
               r.porcion_tiempo, r.cantidad_operarios,
               r.cantidad_producida, r.cantidad_defectuosa, r.observaciones,
               u.nombre_usuario, r.id_modulo, r.id_orden, r.id_operacion,
               op.nombre_operacion, rdl.letra_secuencia,
               (SELECT SUM(t.tiempo_segundos) FROM Operacion t
                WHERE t.id IN (SELECT id_operacion FROM ReferenciaDetalle WHERE id_referencia = ref.id)) as tc,
               tm.nombre as maquina_nombre, r.created_at, r.id_hora,
               (SELECT nombre FROM HorasProduccion WHERE id = r.id_hora) as hora_nombre,
               r.id_operador, COALESCE(e.nombre, '') as nombre_operador
        FROM RegistroProduccion r
        JOIN ModuloConfeccion m ON r.id_modulo = m.id
        JOIN OrdenProduccion o ON r.id_orden = o.id
        JOIN ReferenciaProducto ref ON o.id_referencia = ref.id
        JOIN Usuario u ON r.id_usuario = u.id
        LEFT JOIN Operacion op ON r.id_operacion = op.id
        LEFT JOIN TipoMaquinaria tm ON op.id_maquina = tm.id
        LEFT JOIN ReferenciaDetalle rdl ON r.id_operacion = rdl.id_operacion AND rdl.id_referencia = ref.id
        LEFT JOIN Empleados e ON r.id_operador = e.id
        WHERE r.fecha BETWEEN ? AND ?
    """
    params = [fecha_desde, fecha_hasta]
    if id_usuario:
        query += " AND r.id_usuario = ?"
        params.append(id_usuario)
    query += " ORDER BY r.id DESC"
    cursor.execute(query, params)
    filas = cursor.fetchall()

    # Paradas por registro
    paradas_dict = {}
    cursor.execute("""
        SELECT p.id_registro, p.tiempo_segundos,
               pp.nombre, cp.nombre, p.descripcion
        FROM ParadaRegistro p
        LEFT JOIN ParadasProgramadas pp ON p.id_parada_programada = pp.id
        LEFT JOIN CausaParada cp ON p.id_causa = cp.id
    """)
    for f in cursor.fetchall():
        paradas_dict.setdefault(f[0], []).append({
            "tiempo": f[1], "parada_programada": f[2], "causa": f[3], "descripcion": f[4]
        })
    conexion.close()

    return [{
        "id": f[0], "fecha": f[1], "modulo": f[2], "orden": f[3], "referencia": f[4],
        "timestamp": f[18] or f[1],
        "porcion_tiempo": f[5], "cantidad_operarios": f[6],
        "cantidad_producida": f[7], "cantidad_defectuosa": f[8], "observaciones": f[9],
        "usuario": f[10], "id_modulo": f[11], "id_orden": f[12],
        "id_operacion": f[13], "nombre_operacion": f[14], "letra": f[15],
        "tc": f[16] or 0, "maquina": f[17] or '',
        "id_hora": f[19], "hora_nombre": f[20] or '',
        "id_operador": f[21], "nombre_operador": f[22] or '',
        "paradas": paradas_dict.get(f[0], [])
    } for f in filas]

def obtener_fechas_con_registros(limit=120):
    """Fechas que tienen registros de producción, más recientes primero."""
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT DISTINCT fecha FROM RegistroProduccion ORDER BY fecha DESC LIMIT ?", (limit,))
    filas = cursor.fetchall()
    conexion.close()
    return [f[0] for f in filas]

def resumen_registros_hora(fecha, id_modulo, id_hora=None, id_operacion=None):
    """Devuelve la cantidad del día (módulo+operación opcional) y el total del día.
    Sin hora operativa: la marca temporal es created_at, no hay asignación por hora."""
    conexion = _conexion()
    cursor = conexion.cursor()
    params = [fecha, id_modulo]
    query = """
        SELECT COALESCE(SUM(cantidad_producida), 0) FROM RegistroProduccion
        WHERE fecha = ? AND id_modulo = ?
    """
    if id_hora:
        query += " AND id_hora = ?"
        params.append(id_hora)
    if id_operacion:
        query += " AND id_operacion = ?"
        params.append(id_operacion)
    cursor.execute(query, params)
    hora = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COALESCE(SUM(cantidad_producida), 0) FROM RegistroProduccion
        WHERE fecha = ?
    """, (fecha,))
    dia = cursor.fetchone()[0]
    conexion.close()
    return {"hora": hora, "dia": dia}

def _validar_operacion_en_modulo(cursor, id_operacion, id_modulo, id_maquina=None):
    """Valida que la operación se ejecute en la máquina indicada y que esa máquina
    pertenezca al módulo de registro. Retorna None si es válido, o un dict de error."""
    if not id_operacion:
        return {"error": "Debe seleccionar una actividad (operación)"}
    cursor.execute("""
        SELECT o.id_maquina, tm.id_modulo, tm.nombre
        FROM Operacion o
        LEFT JOIN TipoMaquinaria tm ON o.id_maquina = tm.id
        WHERE o.id = ?
    """, (id_operacion,))
    fila = cursor.fetchone()
    if not fila:
        return {"error": "La actividad seleccionada no existe"}
    id_maquina_op = fila[0]
    modulo_maquina = fila[1]
    nombre_maquina = fila[2]

    # La operación debe ejecutarse en la máquina seleccionada (si se envía)
    if id_maquina and id_maquina_op and int(id_maquina) != id_maquina_op:
        return {"error": f"La actividad '{nombre_maquina}' no se ejecuta en la máquina seleccionada. Verifique que la máquina coincida con la actividad."}
    # La máquina de la operación debe pertenecer al módulo de registro
    # (se permite si la máquina NO tiene módulo definido)
    if modulo_maquina and modulo_maquina != int(id_modulo):
        return {"error": f"La actividad usa '{nombre_maquina}' que pertenece a otro módulo. Verifique que la línea de registro coincida con la actividad."}
    return None

def insertar_registro_produccion(datos, id_usuario):
    conexion = _conexion()
    cursor = conexion.cursor()

    # Validar que la operación (actividad) corresponde a la máquina y al módulo de registro
    err_op = _validar_operacion_en_modulo(cursor, datos.get('id_operacion'), datos.get('id_modulo'), datos.get('id_maquina'))
    if err_op:
        conexion.close()
        return err_op

    cursor.execute("""
        INSERT INTO RegistroProduccion (
            fecha, id_modulo, id_hora, id_orden, id_operacion, porcion_tiempo,
            cantidad_operarios, cantidad_producida, cantidad_defectuosa,
            observaciones, id_usuario, id_operador
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos['fecha'], datos['id_modulo'], datos.get('id_hora'), datos['id_orden'],
        datos.get('id_operacion'), datos.get('porcion_tiempo', 1.0), datos.get('cantidad_operarios', 1),
        datos['cantidad_producida'], datos.get('cantidad_defectuosa', 0),
        datos.get('observaciones', ''), id_usuario, datos.get('id_operador')
    ))
    registro_id = cursor.lastrowid

    # Paradas
    for par in (datos.get('paradas') or []):
        cursor.execute("""
            INSERT INTO ParadaRegistro (id_registro, id_parada_programada, id_causa, tiempo_segundos, descripcion)
            VALUES (?, ?, ?, ?, ?)
        """, (registro_id, par.get('id_parada_programada'), par.get('id_causa'),
              par.get('tiempo_segundos', 0), par.get('descripcion')))

    # Si con este registro la producción real alcanza el lote, cierra la orden
    _cerrar_orden_si_completa(cursor, datos['id_orden'])
    conexion.commit()

    # Verificar si la orden quedó completa para informarlo
    conexion2 = _conexion()
    c2 = conexion2.cursor()
    c2.execute("SELECT estado FROM OrdenProduccion WHERE id = ?", (datos['id_orden'],))
    estado2 = c2.fetchone()
    conexion2.close()

    conexion.close()
    res = {"mensaje": "Registro guardado", "id": registro_id}
    if estado2 and estado2[0] == 'Cerrada':
        res["orden_completada"] = True
    return res

def insertar_registros_masivo(datos, id_usuario):
    """Guarda varios registros de producción a la vez (grilla por operador).
    Cada item de `registros` es {id_operador, id_operacion, cantidad, defectuosas, [paradas]}.
    Si un item trae `paradas` propias, se usan esas; si no, se aplican las paradas de línea (datos['paradas'])."""
    registros = datos.get('registros') or []
    registros = [r for r in registros if (r.get('cantidad') or 0) > 0]
    if not registros:
        return {"error": "No hay cantidades para guardar"}

    paradas_linea = datos.get('paradas') or []

    conexion = _conexion()
    cursor = conexion.cursor()

    for r in registros:
        err_op = _validar_operacion_en_modulo(cursor, r.get('id_operacion'), datos.get('id_modulo'), None)
        if err_op:
            conexion.close()
            return err_op

        cursor.execute("""
            INSERT INTO RegistroProduccion (
                fecha, id_modulo, id_hora, id_orden, id_operacion, porcion_tiempo,
                cantidad_operarios, cantidad_producida, cantidad_defectuosa,
                observaciones, id_usuario, id_operador
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos['fecha'], datos['id_modulo'], datos.get('id_hora'), datos['id_orden'],
            r.get('id_operacion'), datos.get('porcion_tiempo', 1.0), 1,
            r['cantidad'], r.get('defectuosas') or 0,
            datos.get('observaciones', ''), id_usuario, r.get('id_operador')
        ))
        registro_id = cursor.lastrowid

        # Paradas: las propias del operador si vienen en el item, si no las de línea
        paradas_reg = r.get('paradas')
        if paradas_reg is None:
            paradas_reg = paradas_linea
        for par in paradas_reg:
            cursor.execute("""
                INSERT INTO ParadaRegistro (id_registro, id_parada_programada, id_causa, tiempo_segundos, descripcion)
                VALUES (?, ?, ?, ?, ?)
            """, (registro_id, par.get('id_parada_programada'), par.get('id_causa'),
                  par.get('tiempo_segundos', 0), par.get('descripcion')))

    _cerrar_orden_si_completa(cursor, datos['id_orden'])
    conexion.commit()

    conexion2 = _conexion()
    c2 = conexion2.cursor()
    c2.execute("SELECT estado FROM OrdenProduccion WHERE id = ?", (datos['id_orden'],))
    estado2 = c2.fetchone()
    conexion2.close()

    conexion.close()
    res = {"mensaje": f"{len(registros)} registros guardados", "cantidad": len(registros)}
    if estado2 and estado2[0] == 'Cerrada':
        res["orden_completada"] = True
    return res

def eliminar_registro_produccion(id_registro):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_orden FROM RegistroProduccion WHERE id = ?", (id_registro,))
    fila = cursor.fetchone()
    id_orden = fila[0] if fila else None

    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM RegistroProduccion WHERE id = ?", (id_registro,))
    cursor.execute("DELETE FROM ParadaRegistro WHERE id_registro = ?", (id_registro,))

    # Re-evaluar la orden eliminada: si ya no cumple el lote, reabrirla
    if id_orden:
        _reabrir_orden_si_incompleta(cursor, id_orden)

    conexion.commit()
    conexion.close()
    return {"mensaje": "Registro eliminado"}

def _reabrir_orden_si_incompleta(cursor, id_orden):
    """Si la orden está Cerrada pero ya no tiene gorras completas suficientes, la reabre."""
    cursor.execute("SELECT estado, cantidad_lote FROM OrdenProduccion WHERE id = ?", (id_orden,))
    fila = cursor.fetchone()
    if not fila:
        return
    estado, cantidad_lote = fila
    if estado != 'Cerrada':
        return
    completas = _calcular_gorras_completas(cursor, id_orden)
    if completas < cantidad_lote:
        cursor.execute("UPDATE OrdenProduccion SET estado = 'Abierta' WHERE id = ?", (id_orden,))

def obtener_registros_rango(fecha_inicio, fecha_fin, id_orden=None):
    """Registros de producción en rango con paradas agregadas y defectos (para el tablero)."""
    conexion = _conexion()
    cursor = conexion.cursor()
    query = """
        SELECT r.id, r.fecha, m.nombre, o.nombre_orden, ref.nombre_referencia,
               r.porcion_tiempo, r.cantidad_operarios,
               r.cantidad_producida, r.cantidad_defectuosa,
               ref.id as id_referencia, r.id_operacion,
               COALESCE(op.tiempo_segundos, 0) as tiempo_operacion,
               COALESCE(tm.nombre, '') as maquina_nombre,
               COALESCE(op.nombre_operacion, '') as operacion_nombre,
               r.created_at, r.id_operador, COALESCE(e.nombre, '') as nombre_operador
        FROM RegistroProduccion r
        JOIN ModuloConfeccion m ON r.id_modulo = m.id
        JOIN OrdenProduccion o ON r.id_orden = o.id
        JOIN ReferenciaProducto ref ON o.id_referencia = ref.id
        LEFT JOIN Operacion op ON r.id_operacion = op.id
        LEFT JOIN TipoMaquinaria tm ON op.id_maquina = tm.id
        LEFT JOIN Empleados e ON r.id_operador = e.id
        WHERE r.fecha BETWEEN ? AND ?
    """
    params = [fecha_inicio, fecha_fin]
    if id_orden:
        query += " AND r.id_orden = ?"
        params.append(id_orden)
    query += " ORDER BY m.id ASC"
    cursor.execute(query, params)
    filas = cursor.fetchall()

    # Paradas solo de los registros del rango (no de toda la tabla)
    ids_registros = [f[0] for f in filas]
    paradas = {}
    if ids_registros:
        placeholders = ",".join("?" * len(ids_registros))
        cursor.execute(f"SELECT id_registro, tiempo_segundos FROM ParadaRegistro WHERE id_registro IN ({placeholders})", ids_registros)
        for id_reg, tiempo in cursor.fetchall():
            paradas.setdefault(id_reg, 0)
            paradas[id_reg] += tiempo

    conexion.close()
    return [{
        "id": f[0], "fecha": f[1], "modulo": f[2], "orden": f[3], "referencia": f[4],
        "timestamp": f[14] or f[1],
        "porcion_tiempo": f[5] or 1.0, "cantidad_operarios": f[6] or 0,
        "cantidad": f[7], "cantidad_defectuosa": f[8] or 0,
        "id_referencia": f[9], "id_operacion": f[10], "tiempo_operacion": f[11] or 0,
        "maquina": f[12] or '', "operacion_nombre": f[13] or '',
        "tiempo_total_parada": paradas.get(f[0], 0),
        "id_operador": f[15], "nombre_operador": f[16] or ''
    } for f in filas]

def reporte_progreso_orden(id_orden):
    """Progreso de producción de una orden por actividad.
    Calcula qué unidades COMPLETAS se han logrado: el mínimo logrado entre
    todas las actividades (una gorra está completa si pasó por todas las operaciones)."""
    conexion = _conexion()
    cursor = conexion.cursor()

    # Info de la orden + referencia
    cursor.execute("""
        SELECT o.nombre_orden, o.cantidad_lote, o.estado, r.nombre_referencia, r.id
        FROM OrdenProduccion o
        JOIN ReferenciaProducto r ON o.id_referencia = r.id
        WHERE o.id = ?
    """, (id_orden,))
    fila = cursor.fetchone()
    if not fila:
        conexion.close()
        return None
    nombre_orden, cantidad_lote, estado, ref_nombre, ref_id = fila

    # Actividades de la referencia (diagrama) con tiempos
    cursor.execute("""
        SELECT rd.orden_fila, rd.letra_secuencia, o.nombre_operacion, o.tiempo_segundos, o.id
        FROM ReferenciaDetalle rd
        JOIN Operacion o ON rd.id_operacion = o.id
        WHERE rd.id_referencia = ?
        ORDER BY rd.orden_fila
    """, (ref_id,))
    actividades = [{
        "orden": a[0], "letra": a[1], "nombre": a[2],
        "tiempo_segundos": a[3], "id_operacion": a[4],
        "producido": 0, "defectuoso": 0, "avance": 0, "necesario": cantidad_lote
    } for a in cursor.fetchall()]

    # Producción real por actividad
    cursor.execute("""
        SELECT id_operacion, SUM(cantidad_producida), SUM(cantidad_defectuosa)
        FROM RegistroProduccion
        WHERE id_orden = ?
        GROUP BY id_operacion
    """, (id_orden,))
    for id_op, producido, defectuoso in cursor.fetchall():
        for a in actividades:
            if a["id_operacion"] == id_op:
                a["producido"] = producido or 0
                a["defectuoso"] = defectuoso or 0
                a["avance"] = round(min(100, (producido or 0) / cantidad_lote * 100), 1) if cantidad_lote > 0 else 0
                break

    # Unidades completas = mínimo logrado entre todas las actividades (botella)
    unidades_completas = min((a["producido"] for a in actividades), default=0) if actividades else 0
    tiempo_total_seg = sum(a["tiempo_segundos"] for a in actividades)
    unidades_objetivo = cantidad_lote

    conexion.close()
    return {
        "id_orden": id_orden,
        "nombre_orden": nombre_orden,
        "cantidad_lote": cantidad_lote,
        "estado": estado,
        "referencia": ref_nombre,
        "actividades": actividades,
        "unidades_completas": unidades_completas,
        "unidades_objetivo": unidades_objetivo,
        "porcentaje_total": round(unidades_completas / unidades_objetivo * 100, 1) if unidades_objetivo > 0 else 0,
        "tiempo_total_seg": tiempo_total_seg
    }

if __name__ == "__main__":
    inicializar_base_de_datos()
