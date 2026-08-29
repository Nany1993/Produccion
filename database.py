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
                hora_fin TEXT,
                turno TEXT
            );
        """)
        # Seed Horas Produccion
        cursor.execute("SELECT COUNT(*) FROM HorasProduccion")
        if cursor.fetchone()[0] == 0:
            horas = [
                ('Hora 1', '07:00', '08:00', 'Mañana'),
                ('Hora 2', '08:00', '09:00', 'Mañana'),
                ('Hora 3', '09:00', '10:00', 'Mañana'),
                ('Hora 4', '10:00', '11:00', 'Mañana'),
                ('Hora 5', '11:00', '12:00', 'Mañana'),
                ('Hora 6', '13:00', '14:00', 'Tarde'),
                ('Hora 7', '14:00', '15:00', 'Tarde'),
                ('Hora 8', '15:00', '16:00', 'Tarde'),
                ('Hora 9', '16:00', '17:00', 'Tarde'),
                ('Hora Extra', '17:00', '18:00', 'Extra')
            ]
            cursor.executemany("INSERT INTO HorasProduccion (nombre, hora_inicio, hora_fin, turno) VALUES (?, ?, ?, ?)", horas)
        print("- Tabla 'HorasProduccion' lista.")

        # 2f. Tabla Empleados (NUEVA)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Empleados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                numero_documento TEXT UNIQUE NOT NULL,
                cargo TEXT NOT NULL,
                rol TEXT DEFAULT 'Operador',
                turno TEXT,
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RegistroProduccion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                id_modulo INTEGER NOT NULL,
                id_hora INTEGER NOT NULL,
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

        # 2g. Tabla ControlHoraHora [NEW]
        cursor.execute('''CREATE TABLE IF NOT EXISTS ControlHoraHora (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            id_modulo INTEGER NOT NULL,
            id_asignacion INTEGER NOT NULL,
            id_hora INTEGER NOT NULL,
            porcion_tiempo REAL NOT NULL,
            cantidad_operarios REAL,
            cantidad_producida INTEGER NOT NULL,
            id_parada_programada INTEGER NOT NULL,
            tiempo_parada_programada INTEGER NOT NULL,
            descripcion_parada_no_programada TEXT,
            tiempo_parada_no_programada INTEGER,
            FOREIGN KEY (id_modulo) REFERENCES ModuloConfeccion(id),
            FOREIGN KEY (id_asignacion) REFERENCES AsignacionModulo(id),
            FOREIGN KEY (id_hora) REFERENCES HorasProduccion(id),
            FOREIGN KEY (id_parada_programada) REFERENCES ParadasProgramadas(id)
        )''')
        
        # MIGRACIÓN: Agregar cantidad_operarios si no existe
        try:
            cursor.execute("ALTER TABLE ControlHoraHora ADD COLUMN cantidad_operarios REAL")
            print("- Columna 'cantidad_operarios' agregada.")
        except sqlite3.OperationalError:
            pass # Ya existe
            
        print("- Tabla 'ControlHoraHora' lista.")

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
            ("HorasProduccion", "turno", "TEXT"),
            ("ParadasProgramadas", "tipo", "TEXT DEFAULT 'Opcional'"),
            ("ParadasProgramadas", "frecuencia", "TEXT DEFAULT 'Diaria'"),
            ("ReferenciaProducto", "especificaciones", "TEXT"),
            ("ReferenciaProducto", "foto", "TEXT"),
            ("ParadaRegistro", "descripcion", "TEXT"),
            ("RegistroProduccion", "id_operacion", "INTEGER"),
            ("TipoMaquinaria", "id_modulo", "INTEGER"),
            ("Empleados", "id_maquina", "INTEGER"),
            ("Empleados", "rol", "TEXT DEFAULT 'Operador'"),
        ]
        
        for tabla, columna, tipo in migraciones:
            try:
                cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")
                print(f"- Migración: Columna '{columna}' agregada a {tabla}.")
            except sqlite3.OperationalError:
                pass  # La columna ya existe

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
    cursor.execute("SELECT id, nombre, hora_inicio, hora_fin, turno FROM HorasProduccion ORDER BY id")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "hora_inicio": f[2], "hora_fin": f[3], "turno": f[4]} for f in filas]

def insertar_hora(nombre, hora_inicio=None, hora_fin=None, turno=None):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO HorasProduccion (nombre, hora_inicio, hora_fin, turno) VALUES (?, ?, ?, ?)",
                   (nombre, hora_inicio, hora_fin, turno))
    conexion.commit()
    conexion.close()

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

def _calcular_gorras_completas(cursor, id_orden):
    """Gorras TERMINADAS de una orden: el mínimo de producción entre TODAS sus actividades.
    Una gorra está completa solo si pasó por cada actividad (A..Q) del diagrama de la referencia."""
    # Referencia de la orden
    cursor.execute("SELECT id_referencia FROM OrdenProduccion WHERE id = ?", (id_orden,))
    fila = cursor.fetchone()
    if not fila:
        return 0
    id_referencia = fila[0]

    # Operaciones (actividades) de la referencia
    cursor.execute("SELECT id_operacion FROM ReferenciaDetalle WHERE id_referencia = ?", (id_referencia,))
    ops = [r[0] for r in cursor.fetchall()]
    if not ops:
        return 0

    # Producción por cada actividad de esta orden
    producido_por_actividad = []
    for op in ops:
        cursor.execute("SELECT COALESCE(SUM(cantidad_producida),0) FROM RegistroProduccion WHERE id_orden = ? AND id_operacion = ?", (id_orden, op))
        producido_por_actividad.append(cursor.fetchone()[0])

    return min(producido_por_actividad)

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

    resultado = []
    for f in filas:
        id_orden = f[0]
        cantidad_lote = f[3]
        completas = _calcular_gorras_completas(cursor, id_orden)
        resultado.append({
            "id": id_orden,
            "nombre_orden": f[1],
            "referencia": f[2],
            "cantidad_lote": cantidad_lote,
            "estado": f[4],
            "fecha_creacion": f[5],
            "id_referencia": f[6],
            "gorras_completas": completas,
            "produccion_total": 0,
            "porcentaje_cumplimiento": round(completas / cantidad_lote * 100, 1) if cantidad_lote and cantidad_lote > 0 else 0
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
            o.id as id_operacion
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
            "id_operacion": f[7]
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
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "capacidad_maxima": f[2], "ubicacion": f[3], "supervisor": f[4], "estado": f[5] or 'Activo'} for f in filas]

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

def validar_porcion_tiempo(cursor, id_modulo, id_hora, fecha, nueva_porcion, id_control_ignorar=None):
    """
    Verifica si la suma de las porciones de tiempo (existentes + nueva) excede 1.0 para un módulo y hora específicos.
    Retorna True si es válido, False si excede.
    """
    query = "SELECT SUM(porcion_tiempo) FROM ControlHoraHora WHERE id_modulo = ? AND id_hora = ? AND fecha = ?"
    params = [id_modulo, id_hora, fecha]
    
    if id_control_ignorar:
        query += " AND id != ?"
        params.append(id_control_ignorar)
        
    cursor.execute(query, params)
    suma_existente = cursor.fetchone()[0] or 0.0
    
    # Tolerancia pequeña para errores de punto flotante
    return (suma_existente + nueva_porcion) <= 1.0001
    

def insertar_control_hora(datos):
    """
    Inserta un registro de producción hora a hora con validación de saldo.
    """
    conexion = _conexion()
    cursor = conexion.cursor()
    
    id_asignacion = datos['id_asignacion']
    cantidad_nueva = datos['cantidad_producida']
    
    # 1. Obtener cantidad total asignada
    cursor.execute("SELECT cantidad_asignada FROM AsignacionModulo WHERE id = ?", (id_asignacion,))
    res_asig = cursor.fetchone()
    if not res_asig:
        conexion.close()
        return {"error": "No se encontró la asignación (lote/módulo)"}
    total_asignado = res_asig[0]
    
    # 2. Sumar producción histórica para esta asignación
    cursor.execute("SELECT SUM(cantidad_producida) FROM ControlHoraHora WHERE id_asignacion = ?", (id_asignacion,))
    producido_actual = cursor.fetchone()[0] or 0
    
    # 3. Validar Regla de Negocio (Cantidad)
    if (producido_actual + cantidad_nueva) > total_asignado:
        conexion.close()
        return {"error": "La cantidad supera el saldo del lote asignado a este módulo"}

    # 4. Validar Regla de Negocio (Porción de Tiempo)
    if not validar_porcion_tiempo(cursor, datos['id_modulo'], datos['id_hora'], datos['fecha'], datos['porcion_tiempo']):
        conexion.close()
        return {"error": "La suma de las porciones de tiempo para este módulo y hora excede 1.0 (100%)"}
        
    # 5. Insertar
    query = """
        INSERT INTO ControlHoraHora (
            fecha, id_modulo, id_asignacion, id_hora, porcion_tiempo, cantidad_operarios,
            cantidad_producida, id_parada_programada, tiempo_parada_programada,
            descripcion_parada_no_programada, tiempo_parada_no_programada
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        datos['fecha'], datos['id_modulo'], id_asignacion, datos['id_hora'], datos['porcion_tiempo'],
        datos.get('cantidad_operarios', 0),
        cantidad_nueva, datos['id_parada_programada'], datos['tiempo_parada_programada'],
        datos.get('descripcion_parada_no_programada', ''), datos.get('tiempo_parada_no_programada', 0)
    )
    
    cursor.execute(query, params)
    conexion.commit()
    conexion.close()
    return {"mensaje": "Registro guardado con éxito"}

def obtener_controles_hoy(fecha_hoy):
    """
    Retorna los registros de producción del día actual.
    """
    conexion = _conexion()
    cursor = conexion.cursor()
    query = """
        SELECT c.id, c.fecha, m.nombre as modulo, r.nombre_referencia as referencia, 
               h.nombre as hora, c.cantidad_producida, p.nombre as parada_p, 
               c.tiempo_parada_programada, c.tiempo_parada_no_programada,
               c.id_modulo, c.id_asignacion, c.id_hora, c.porcion_tiempo,
               c.id_parada_programada, c.descripcion_parada_no_programada,
               c.cantidad_operarios,
               (SELECT SUM(o.tiempo_segundos) 
                FROM ReferenciaDetalle rd 
                JOIN Operacion o ON rd.id_operacion = o.id 
                WHERE rd.id_referencia = r.id) as tc
        FROM ControlHoraHora c
        JOIN ModuloConfeccion m ON c.id_modulo = m.id
        JOIN AsignacionModulo a ON c.id_asignacion = a.id
        JOIN OrdenProduccion o ON a.id_orden = o.id
        JOIN ReferenciaProducto r ON o.id_referencia = r.id
        JOIN HorasProduccion h ON c.id_hora = h.id
        JOIN ParadasProgramadas p ON c.id_parada_programada = p.id
        WHERE c.fecha = ?
        ORDER BY c.id DESC
    """
    cursor.execute(query, (fecha_hoy,))
    filas = cursor.fetchall()
    conexion.close()
    
    return [{
        "id": f[0], "fecha": f[1], "modulo": f[2], "referencia": f[3],
        "hora": f[4], "cantidad": f[5], "parada": f[6], 
        "tiempo_p": f[7], "tiempo_np": f[8],
        # Raw Data for Edit
        "id_modulo": f[9], "id_asignacion": f[10], "id_hora": f[11],
        "porcion_tiempo": f[12], "id_parada_programada": f[13],
        "descripcion_parada_no_programada": f[14],
        "cantidad_operarios": f[15],
        "tc": f[16] or 0
    } for f in filas]

def eliminar_control_hora(id_control):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM ControlHoraHora WHERE id = ?", (id_control,))
    conexion.commit()
    conexion.close()

def actualizar_control_hora(id_control, datos):
    conexion = _conexion()
    cursor = conexion.cursor()
    
    # 1. Obtener datos antiguos del registro
    cursor.execute("SELECT id_asignacion, cantidad_producida FROM ControlHoraHora WHERE id = ?", (id_control,))
    registro_anterior = cursor.fetchone()
    if not registro_anterior:
        conexion.close()
        return {"error": "Registro no encontrado"}
    
    id_asignacion, cantidad_anterior = registro_anterior
    
    # Manejar caso de que no venga la cantidad (actualización parcial) -> usar anterior
    nueva_cantidad = int(datos.get('cantidad_producida', cantidad_anterior))
    
    # 2. Validar Regla de Negocio (solo si cambia la cantidad)
    if nueva_cantidad != cantidad_anterior:
        # Obtener total asignado
        cursor.execute("SELECT cantidad_asignada FROM AsignacionModulo WHERE id = ?", (id_asignacion,))
        total_asignado = cursor.fetchone()[0]
        
        # Obtener producido total y restar el anterior
        cursor.execute("SELECT SUM(cantidad_producida) FROM ControlHoraHora WHERE id_asignacion = ?", (id_asignacion,))
        producido_total_actual = cursor.fetchone()[0] or 0
        producido_otros = producido_total_actual - cantidad_anterior
        
        if (producido_otros + nueva_cantidad) > total_asignado:
            conexion.close()
            return {"error": f"La nueva cantidad excede el saldo. Máximo posible: {total_asignado - producido_otros}"}

    # Validar Porción de Tiempo si cambia o siempre (para asegurar consistencia)
    nueva_porcion = datos.get('porcion_tiempo')
    if nueva_porcion is not None:
        # Obtenemos datos necesarios para validar (si no vienen en el payload, los buscamos del registro anterior)
        # Pero id_modulo, id_hora y fecha suelen ser consistentes. Consultémoslos por si acaso.
        cursor.execute("SELECT id_modulo, id_hora, fecha FROM ControlHoraHora WHERE id = ?", (id_control,))
        mod, hora, fecha = cursor.fetchone()
        
        # Validar usando los datos que se pretenden guardar (o los existentes si no cambian, pero aquí nueva_porcion viene)
        # Nota: Si el usuario cambia el módulo/hora, deberíamos usar el NUEVO modulo/hora.
        # Asumimos que id_modulo, id_hora, fecha vienen en 'datos' o se mantienen.
        
        check_mod = datos.get('id_modulo', mod)
        check_hora = datos.get('id_hora', hora)
        check_fecha = datos.get('fecha', fecha)
        
        if not validar_porcion_tiempo(cursor, check_mod, check_hora, check_fecha, float(nueva_porcion), id_control_ignorar=id_control):
             conexion.close()
             return {"error": "La suma de las porciones de tiempo excede el límite de 1.0 para este módulo y hora"}

    # 3. Construir Update Dinámico
    campos = []
    valores = []
    
    keys_map = {
        'fecha': 'fecha', 
        'id_modulo': 'id_modulo', 
        'id_hora': 'id_hora', 
        'porcion_tiempo': 'porcion_tiempo',
        'cantidad_operarios': 'cantidad_operarios',
        'cantidad_producida': 'cantidad_producida',
        'id_parada_programada': 'id_parada_programada',
        'tiempo_parada_programada': 'tiempo_parada_programada',
        'descripcion_parada_no_programada': 'descripcion_parada_no_programada',
        'tiempo_parada_no_programada': 'tiempo_parada_no_programada'
    }

    for key, col in keys_map.items():
        if key in datos:
            campos.append(f"{col} = ?")
            valores.append(datos[key])
            
    if not campos:
        conexion.close()
        return {"mensaje": "Nada que actualizar"}
        
    valores.append(id_control)
    query = f"UPDATE ControlHoraHora SET {', '.join(campos)} WHERE id = ?"
    
    try:
        cursor.execute(query, valores)
        conexion.commit()
        conexion.close()
        return {"mensaje": "Registro actualizado correctamente"}
    except Exception as e:
        conexion.close()
        return {"error": str(e)}

def obtener_controles_rango(fecha_inicio, fecha_fin):
    """
    Retorna los registros de producción en un rango de fechas.
    """
    conexion = _conexion()
    cursor = conexion.cursor()
    query = """
        SELECT c.id, c.fecha, m.nombre as modulo, r.nombre_referencia as referencia, 
               h.nombre as hora, c.cantidad_producida, c.tiempo_parada_programada, 
               c.tiempo_parada_no_programada, c.porcion_tiempo, c.cantidad_operarios,
               r.id as id_referencia
        FROM ControlHoraHora c
        JOIN ModuloConfeccion m ON c.id_modulo = m.id
        JOIN AsignacionModulo a ON c.id_asignacion = a.id
        JOIN OrdenProduccion o ON a.id_orden = o.id
        JOIN ReferenciaProducto r ON o.id_referencia = r.id
        JOIN HorasProduccion h ON c.id_hora = h.id
        WHERE c.fecha BETWEEN ? AND ?
        ORDER BY h.id ASC, m.id ASC
    """
    cursor.execute(query, (fecha_inicio, fecha_fin))
    filas = cursor.fetchall()
    conexion.close()
    
    return [{
        "id": f[0], "fecha": f[1], "modulo": f[2], "referencia": f[3],
        "hora": f[4], "cantidad": f[5], "tiempo_p": f[6], "tiempo_np": f[7],
        "porcion_tiempo": f[8], "cantidad_operarios": f[9], "id_referencia": f[10]
    } for f in filas]

def obtener_tiempo_ciclo_referencia(id_ref):
    """
    Calcula el tiempo total de ciclo (TC) sumando los tiempos de todas las operaciones de una referencia.
    """
    conexion = _conexion()
    cursor = conexion.cursor()
    query = """
        SELECT SUM(o.tiempo_segundos) 
        FROM ReferenciaDetalle rd
        INNER JOIN Operacion o ON rd.id_operacion = o.id
        WHERE rd.id_referencia = ?
    """
    cursor.execute(query, (id_ref,))
    res = cursor.fetchone()
    conexion.close()
    return res[0] if res[0] else 0


# ============================================================
# EMPLEADOS
# ============================================================

def obtener_empleados():
    """Retorna todos los empleados con módulo y máquina asignados."""
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT e.id, e.nombre, e.numero_documento, e.cargo, e.rol,
               e.turno, e.fecha_ingreso, e.estado, e.telefono, e.email,
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
            "turno": f[5],
            "fecha_ingreso": f[6],
            "estado": f[7],
            "telefono": f[8],
            "email": f[9],
            "modulo_asignado": f[10],
            "nombre_modulo": f[11],
            "id_maquina": f[12],
            "nombre_maquina": f[13]
        }
        for f in filas
    ]


def obtener_empleado(id_empleado):
    """Retorna un empleado específico por ID."""
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT e.id, e.nombre, e.numero_documento, e.cargo, e.rol,
               e.turno, e.fecha_ingreso, e.estado, e.telefono, e.email,
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
            "turno": fila[5],
            "fecha_ingreso": fila[6],
            "estado": fila[7],
            "telefono": fila[8],
            "email": fila[9],
            "modulo_asignado": fila[10],
            "nombre_modulo": fila[11],
            "id_maquina": fila[12],
            "nombre_maquina": fila[13]
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


def _sincronizar_modulos_supervisor(conexion, cursor, id_empleado, lista_modulos):
    """Para un supervisor: sus módulos a supervisar = líneas de acceso del usuario ligado.
    Actualiza AsignacionUsuarioLinea del usuario asociado al empleado."""
    cursor.execute("SELECT id FROM Usuario WHERE id_empleado = ?", (id_empleado,))
    r = cursor.fetchone()
    if not r:
        return
    id_usuario = r[0]
    cursor.execute("DELETE FROM AsignacionUsuarioLinea WHERE id_usuario = ?", (id_usuario,))
    for mid in lista_modulos or []:
        cursor.execute("INSERT INTO AsignacionUsuarioLinea (id_usuario, id_modulo) VALUES (?, ?)", (id_usuario, mid))


def insertar_empleado(nombre, numero_documento, cargo, rol='Operador', turno=None,
                      fecha_ingreso=None, estado='Activo', telefono=None, email=None,
                      modulo_asignado=None, id_maquina=None, id_modulos_supervisor=None):
    """Inserta un nuevo empleado.
    Operador → opera una máquina (modulo_asignado = módulo de la máquina).
    Supervisor → supervisa uno o varios módulos (líneas a las que tiene acceso)."""
    conexion = _conexion()
    cursor = conexion.cursor()
    try:
        # Validaciones por rol
        if rol == 'Supervisor':
            if not id_modulos_supervisor:
                conexion.close()
                return {"error": "Un supervisor debe tener al menos un módulo a supervisar."}
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

        cursor.execute("""
            INSERT INTO Empleados (nombre, numero_documento, cargo, rol, turno,
                                   fecha_ingreso, estado, telefono, email, modulo_asignado, id_maquina)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, numero_documento, cargo, rol, turno, fecha_ingreso,
              estado, telefono, email, modulo_asignado, id_maquina))
        conexion.commit()
        nuevo_id = cursor.lastrowid

        if rol == 'Supervisor':
            _sincronizar_modulos_supervisor(conexion, cursor, nuevo_id, id_modulos_supervisor)
            conexion.commit()

        conexion.close()
        return {"mensaje": "Empleado guardado con éxito", "id": nuevo_id}
    except sqlite3.IntegrityError:
        conexion.close()
        return {"error": "El número de documento ya existe"}


def actualizar_empleado(id_empleado, nombre, numero_documento, cargo, rol='Operador',
                        turno=None, fecha_ingreso=None, estado='Activo', telefono=None,
                        email=None, modulo_asignado=None, id_maquina=None, id_modulos_supervisor=None):
    """Actualiza un empleado existente."""
    conexion = _conexion()
    cursor = conexion.cursor()
    try:
        if rol == 'Supervisor':
            if not id_modulos_supervisor:
                conexion.close()
                return {"error": "Un supervisor debe tener al menos un módulo a supervisar."}
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

        cursor.execute("""
            UPDATE Empleados
            SET nombre=?, numero_documento=?, cargo=?, rol=?, turno=?,
                fecha_ingreso=?, estado=?, telefono=?, email=?, modulo_asignado=?, id_maquina=?
            WHERE id=?
        """, (nombre, numero_documento, cargo, rol, turno, fecha_ingreso,
              estado, telefono, email, modulo_asignado, id_maquina, id_empleado))
        conexion.commit()

        if rol == 'Supervisor':
            _sincronizar_modulos_supervisor(conexion, cursor, id_empleado, id_modulos_supervisor)
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

def obtener_registros_dia(fecha, id_usuario=None):
    conexion = _conexion()
    cursor = conexion.cursor()
    query = """
        SELECT r.id, r.fecha, m.nombre, o.nombre_orden, ref.nombre_referencia,
               h.nombre, r.porcion_tiempo, r.cantidad_operarios,
               r.cantidad_producida, r.cantidad_defectuosa, r.observaciones,
               u.nombre_usuario, r.id_modulo, r.id_hora, r.id_orden, r.id_operacion,
               op.nombre_operacion, rdl.letra_secuencia,
               (SELECT SUM(t.tiempo_segundos) FROM Operacion t
                WHERE t.id IN (SELECT id_operacion FROM ReferenciaDetalle WHERE id_referencia = ref.id)) as tc
        FROM RegistroProduccion r
        JOIN ModuloConfeccion m ON r.id_modulo = m.id
        JOIN OrdenProduccion o ON r.id_orden = o.id
        JOIN ReferenciaProducto ref ON o.id_referencia = ref.id
        JOIN HorasProduccion h ON r.id_hora = h.id
        JOIN Usuario u ON r.id_usuario = u.id
        LEFT JOIN Operacion op ON r.id_operacion = op.id
        LEFT JOIN ReferenciaDetalle rdl ON r.id_operacion = rdl.id_operacion AND rdl.id_referencia = ref.id
        WHERE r.fecha = ?
    """
    params = [fecha]
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
        "hora": f[5], "porcion_tiempo": f[6], "cantidad_operarios": f[7],
        "cantidad_producida": f[8], "cantidad_defectuosa": f[9], "observaciones": f[10],
        "usuario": f[11], "id_modulo": f[12], "id_hora": f[13], "id_orden": f[14],
        "id_operacion": f[15], "nombre_operacion": f[16], "letra": f[17],
        "tc": f[18] or 0,
        "paradas": paradas_dict.get(f[0], [])
    } for f in filas]

def resumen_registros_hora(fecha, id_modulo, id_hora):
    """Devuelve la cantidad de esa hora y el total del día para la advertencia."""
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(cantidad_producida), 0) FROM RegistroProduccion
        WHERE fecha = ? AND id_modulo = ? AND id_hora = ?
    """, (fecha, id_modulo, id_hora))
    hora = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COALESCE(SUM(cantidad_producida), 0) FROM RegistroProduccion
        WHERE fecha = ?
    """, (fecha,))
    dia = cursor.fetchone()[0]
    conexion.close()
    return {"hora": hora, "dia": dia}

def insertar_registro_produccion(datos, id_usuario):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO RegistroProduccion (
            fecha, id_modulo, id_hora, id_orden, id_operacion, porcion_tiempo,
            cantidad_operarios, cantidad_producida, cantidad_defectuosa,
            observaciones, id_usuario
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos['fecha'], datos['id_modulo'], datos['id_hora'], datos['id_orden'],
        datos.get('id_operacion'), datos.get('porcion_tiempo', 1.0), datos.get('cantidad_operarios', 0),
        datos['cantidad_producida'], datos.get('cantidad_defectuosa', 0),
        datos.get('observaciones', ''), id_usuario
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

def eliminar_registro_produccion(id_registro):
    conexion = _conexion()
    cursor = conexion.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM RegistroProduccion WHERE id = ?", (id_registro,))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Registro eliminado"}

def obtener_registros_rango(fecha_inicio, fecha_fin, id_orden=None):
    """Registros de producción en rango con paradas agregadas y defectos (para el tablero)."""
    conexion = _conexion()
    cursor = conexion.cursor()
    query = """
        SELECT r.id, r.fecha, m.nombre, o.nombre_orden, ref.nombre_referencia,
               h.nombre, r.porcion_tiempo, r.cantidad_operarios,
               r.cantidad_producida, r.cantidad_defectuosa,
               ref.id as id_referencia, r.id_hora
        FROM RegistroProduccion r
        JOIN ModuloConfeccion m ON r.id_modulo = m.id
        JOIN OrdenProduccion o ON r.id_orden = o.id
        JOIN ReferenciaProducto ref ON o.id_referencia = ref.id
        JOIN HorasProduccion h ON r.id_hora = h.id
        WHERE r.fecha BETWEEN ? AND ?
    """
    params = [fecha_inicio, fecha_fin]
    if id_orden:
        query += " AND r.id_orden = ?"
        params.append(id_orden)
    query += " ORDER BY h.id ASC, m.id ASC"
    cursor.execute(query, params)
    filas = cursor.fetchall()

    # Paradas agregadas por registro
    cursor.execute("SELECT id_registro, tiempo_segundos FROM ParadaRegistro")
    paradas = {}
    for id_reg, tiempo in cursor.fetchall():
        paradas.setdefault(id_reg, 0)
        paradas[id_reg] += tiempo

    conexion.close()
    return [{
        "id": f[0], "fecha": f[1], "modulo": f[2], "orden": f[3], "referencia": f[4],
        "hora": f[5], "porcion_tiempo": f[6] or 1.0, "cantidad_operarios": f[7] or 0,
        "cantidad": f[8], "cantidad_defectuosa": f[9] or 0,
        "id_referencia": f[10], "tiempo_total_parada": paradas.get(f[0], 0)
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
