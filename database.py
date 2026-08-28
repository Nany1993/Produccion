import sqlite3
import os

# Configuración del archivo de base de datos
DB_NAME = "balanceo_produccion.db"

def inicializar_base_de_datos():
    """
    Crea las tablas necesarias para la aplicación 'Balanceo' si no existen.
    Garantiza la persistencia de datos al no usar comandos DROP TABLE.
    """
    try:
        # Conectar a la base de datos (se crea el archivo si no existe)
        conexion = sqlite3.connect(DB_NAME)
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
                estado TEXT DEFAULT 'Activa'
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
                especialidad TEXT,
                turno TEXT,
                fecha_ingreso TEXT,
                estado TEXT DEFAULT 'Activo',
                telefono TEXT,
                email TEXT,
                modulo_asignado INTEGER,
                FOREIGN KEY (modulo_asignado) REFERENCES ModuloConfeccion(id)
            );
        """)
        print("- Tabla 'Empleados' lista.")

        # 2g. Tabla AsignacionModulo (NUEVA)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS AsignacionModulo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_referencia INTEGER NOT NULL,
                id_modulo INTEGER NOT NULL,
                cantidad_asignada INTEGER NOT NULL,
                FOREIGN KEY (id_referencia) REFERENCES ReferenciaProducto(id),
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



        # 4. Tabla ReferenciaProducto
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ReferenciaProducto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_referencia TEXT NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("- Tabla 'ReferenciaProducto' lista.")

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

        # MIGRACIÓN: Agregar columna cantidad_lote si no existe
        try:
            cursor.execute("ALTER TABLE ReferenciaProducto ADD COLUMN cantidad_lote INTEGER DEFAULT 0;")
            print("- Migración: Columna 'cantidad_lote' agregada a ReferenciaProducto.")
        except sqlite3.OperationalError:
            # La columna ya existe
            pass

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
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, descripcion, velocidad_tipica, estado FROM TipoMaquinaria")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "descripcion": f[2], "velocidad_tipica": f[3], "estado": f[4] or 'Activa'} for f in filas]

def insertar_maquina(nombre, descripcion=None, velocidad_tipica=None, estado='Activa'):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO TipoMaquinaria (nombre, descripcion, velocidad_tipica, estado) VALUES (?, ?, ?, ?)", 
                   (nombre, descripcion, velocidad_tipica, estado))
    conexion.commit()
    conexion.close()

def obtener_secciones():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, descripcion, orden_proceso FROM SeccionPrenda ORDER BY orden_proceso, id")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "descripcion": f[2], "orden_proceso": f[3]} for f in filas]

def insertar_seccion(nombre, descripcion=None, orden_proceso=None):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO SeccionPrenda (nombre, descripcion, orden_proceso) VALUES (?, ?, ?)",
                   (nombre, descripcion, orden_proceso))
    conexion.commit()
    conexion.close()

def obtener_operaciones_detalladas():
    conexion = sqlite3.connect(DB_NAME)
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
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO Operacion (nombre_operacion, tiempo_segundos, id_maquina, id_seccion)
        VALUES (?, ?, ?, ?)
    """, (nombre, tiempo, id_maquina, id_seccion))
    conexion.commit()
    conexion.close()

def actualizar_operacion(id_operacion, nombre, tiempo, id_maquina, id_seccion):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE Operacion 
        SET nombre_operacion = ?, tiempo_segundos = ?, id_maquina = ?, id_seccion = ?
        WHERE id = ?
    """, (nombre, tiempo, id_maquina, id_seccion, id_operacion))
    conexion.commit()
    conexion.close()

def eliminar_operacion(id_operacion):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM Operacion WHERE id = ?", (id_operacion,))
    conexion.commit()
    conexion.close()

# --- REFERENCIAS ---

def crear_referencia(nombre, cantidad_lote=0):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO ReferenciaProducto (nombre_referencia, cantidad_lote) VALUES (?, ?)", (nombre, cantidad_lote))
    ref_id = cursor.lastrowid
    conexion.commit()
    conexion.close()
    return ref_id

def actualizar_referencia(id_ref, nombre, cantidad_lote):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("UPDATE ReferenciaProducto SET nombre_referencia = ?, cantidad_lote = ? WHERE id = ?", (nombre, cantidad_lote, id_ref))
    conexion.commit()
    conexion.close()

def duplicar_referencia(id_origen, nuevo_nombre):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    # 1. Obtener datos origen
    cursor.execute("SELECT cantidad_lote FROM ReferenciaProducto WHERE id = ?", (id_origen,))
    row = cursor.fetchone()
    if not row:
        conexion.close()
        return None # No existe
    
    cantidad = row[0]
    
    # 2. Crear nueva referencia
    cursor.execute("INSERT INTO ReferenciaProducto (nombre_referencia, cantidad_lote) VALUES (?, ?)", (nuevo_nombre, cantidad))
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
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, hora_inicio, hora_fin, turno FROM HorasProduccion ORDER BY id")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "hora_inicio": f[2], "hora_fin": f[3], "turno": f[4]} for f in filas]

def insertar_hora(nombre, hora_inicio=None, hora_fin=None, turno=None):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO HorasProduccion (nombre, hora_inicio, hora_fin, turno) VALUES (?, ?, ?, ?)",
                   (nombre, hora_inicio, hora_fin, turno))
    conexion.commit()
    conexion.close()

def obtener_paradas():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, tiempo_segundos, tipo, frecuencia FROM ParadasProgramadas")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "tiempo": f[2], "tipo": f[3] or 'Opcional', "frecuencia": f[4] or 'Diaria'} for f in filas]

def insertar_parada(nombre, tiempo, tipo='Opcional', frecuencia='Diaria'):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO ParadasProgramadas (nombre, tiempo_segundos, tipo, frecuencia) VALUES (?, ?, ?, ?)",
                   (nombre, tiempo, tipo, frecuencia))
    conexion.commit()
    conexion.close()

# --- ASIGNACIÓN DE REFERENCIAS ---

def obtener_asignaciones():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    query = """
        SELECT a.id, r.nombre_referencia, m.nombre, a.cantidad_asignada, r.cantidad_lote
        FROM AsignacionModulo a
        JOIN ReferenciaProducto r ON a.id_referencia = r.id
        JOIN ModuloConfeccion m ON a.id_modulo = m.id
        ORDER BY a.id DESC
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conexion.close()
    return [{
        "id": row[0],
        "referencia": row[1],
        "modulo": row[2],
        "cantidad": row[3],
        "total_lote": row[4]
    } for row in data]

def obtener_disponibilidad(id_ref):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    # 1. Obtener lote total
    cursor.execute("SELECT cantidad_lote FROM ReferenciaProducto WHERE id = ?", (id_ref,))
    res = cursor.fetchone()
    if not res:
        conexion.close()
        return None
    total_lote = res[0]
    
    # 2. Obtener ya asignado
    cursor.execute("SELECT SUM(cantidad_asignada) FROM AsignacionModulo WHERE id_referencia = ?", (id_ref,))
    res_asignado = cursor.fetchone()
    total_asignado = res_asignado[0] if res_asignado[0] else 0
    
    conexion.close()
    return {
        "total": total_lote,
        "asignado": total_asignado,
        "disponible": total_lote - total_asignado
    }

def asignar_referencia_modulo(id_ref, id_mod, cantidad):
    disp = obtener_disponibilidad(id_ref)
    if not disp:
        return {"error": "Referencia no encontrada"}
    
    if cantidad > disp['disponible']:
        return {"error": f"Excede disponibilidad. Disponible: {disp['disponible']}"}
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO AsignacionModulo (id_referencia, id_modulo, cantidad_asignada) VALUES (?, ?, ?)", 
                   (id_ref, id_mod, cantidad))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Asignado correctamente"}

def eliminar_asignacion(id_asignacion):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM AsignacionModulo WHERE id = ?", (id_asignacion,))
    conexion.commit()
    conexion.close()

def actualizar_asignacion(id_asignacion, nueva_cantidad):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    # Obtener datos actuales
    cursor.execute("SELECT id_referencia, cantidad_asignada FROM AsignacionModulo WHERE id = ?", (id_asignacion,))
    row = cursor.fetchone()
    if not row:
        conexion.close()
        return {"error": "Asignación no encontrada"}
    
    id_ref, cantidad_anterior = row
    
    # Verificar disponibilidad con el ajuste
    disp = obtener_disponibilidad(id_ref)
    # Al hacer update, el 'disponible' real es: disponible_actual + cantidad_anterior
    max_posible = disp['disponible'] + cantidad_anterior
    
    if nueva_cantidad > max_posible:
        conexion.close()
        return {"error": f"Excede máximo posible ({max_posible})"}
        
    cursor.execute("UPDATE AsignacionModulo SET cantidad_asignada = ? WHERE id = ?", (nueva_cantidad, id_asignacion))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Actualizado correctamente"}

def obtener_referencias_disponibles():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    # Seleccionar referencias cuyo lote > asignado
    # Left join para incluir las que no tienen asignaciones (SUM es null -> 0)
    query = """
        SELECT r.id, r.nombre_referencia
        FROM ReferenciaProducto r
        LEFT JOIN AsignacionModulo a ON r.id = a.id_referencia
        GROUP BY r.id
        HAVING r.cantidad_lote > COALESCE(SUM(a.cantidad_asignada), 0)
    """
    cursor.execute(query)
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1]} for f in filas]

def obtener_referencias():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    # Intentamos seleccionar cantidad_lote, si no existe (versión vieja), no fallará si la migración se hace bien.
    # Pero para seguridad, asumiremos que ya existe tras la migración.
    cursor.execute("SELECT id, nombre_referencia, fecha_creacion, cantidad_lote FROM ReferenciaProducto ORDER BY id DESC")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "fecha": f[2], "cantidad": f[3]} for f in filas]

def eliminar_referencia(id_ref):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM ReferenciaProducto WHERE id = ?", (id_ref,))
    conexion.commit()
    conexion.close()

def agregar_detalle_referencia(id_ref, id_op, letra, predecesoras, orden):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO ReferenciaDetalle (id_referencia, id_operacion, letra_secuencia, predecesoras, orden_fila)
        VALUES (?, ?, ?, ?, ?)
    """, (id_ref, id_op, letra, predecesoras, orden))
    conexion.commit()
    conexion.close()

def obtener_detalles_referencia(id_ref):
    conexion = sqlite3.connect(DB_NAME)
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
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM ReferenciaDetalle WHERE id = ?", (id_detalle,))
    conexion.commit()
    conexion.close()

def obtener_modulos():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, capacidad_maxima, ubicacion, supervisor, estado FROM ModuloConfeccion")
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "capacidad_maxima": f[2], "ubicacion": f[3], "supervisor": f[4], "estado": f[5] or 'Activo'} for f in filas]

def insertar_modulo(nombre, capacidad_maxima=None, ubicacion=None, supervisor=None, estado='Activo'):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO ModuloConfeccion (nombre, capacidad_maxima, ubicacion, supervisor, estado) VALUES (?, ?, ?, ?, ?)",
                   (nombre, capacidad_maxima, ubicacion, supervisor, estado))
    conexion.commit()
    conexion.close()

# --- FUNCIONES CONTROL HORA A HORA ---

def obtener_referencias_por_modulo(id_modulo):
    """
    Obtiene las referencias asignadas a un módulo específico (FK a AsignacionModulo).
    """
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    query = """
        SELECT a.id, r.nombre_referencia, r.id
        FROM AsignacionModulo a
        JOIN ReferenciaProducto r ON a.id_referencia = r.id
        WHERE a.id_modulo = ?
    """
    cursor.execute(query, (id_modulo,))
    filas = cursor.fetchall()
    conexion.close()
    return [{"id": f[0], "nombre": f[1], "id_referencia": f[2]} for f in filas]

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
    conexion = sqlite3.connect(DB_NAME)
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
    conexion = sqlite3.connect(DB_NAME)
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
        JOIN ReferenciaProducto r ON a.id_referencia = r.id
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
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM ControlHoraHora WHERE id = ?", (id_control,))
    conexion.commit()
    conexion.close()

def actualizar_control_hora(id_control, datos):
    conexion = sqlite3.connect(DB_NAME)
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
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    query = """
        SELECT c.id, c.fecha, m.nombre as modulo, r.nombre_referencia as referencia, 
               h.nombre as hora, c.cantidad_producida, c.tiempo_parada_programada, 
               c.tiempo_parada_no_programada, c.porcion_tiempo, c.cantidad_operarios,
               r.id as id_referencia
        FROM ControlHoraHora c
        JOIN ModuloConfeccion m ON c.id_modulo = m.id
        JOIN AsignacionModulo a ON c.id_asignacion = a.id
        JOIN ReferenciaProducto r ON a.id_referencia = r.id
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
    conexion = sqlite3.connect(DB_NAME)
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
    """Retorna todos los empleados con datos del módulo asignado."""
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT e.id, e.nombre, e.numero_documento, e.cargo, e.especialidad,
               e.turno, e.fecha_ingreso, e.estado, e.telefono, e.email,
               e.modulo_asignado, m.nombre as nombre_modulo
        FROM Empleados e
        LEFT JOIN ModuloConfeccion m ON e.modulo_asignado = m.id
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
            "especialidad": f[4],
            "turno": f[5],
            "fecha_ingreso": f[6],
            "estado": f[7],
            "telefono": f[8],
            "email": f[9],
            "modulo_asignado": f[10],
            "nombre_modulo": f[11]
        }
        for f in filas
    ]


def obtener_empleado(id_empleado):
    """Retorna un empleado específico por ID."""
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT e.id, e.nombre, e.numero_documento, e.cargo, e.especialidad,
               e.turno, e.fecha_ingreso, e.estado, e.telefono, e.email,
               e.modulo_asignado, m.nombre as nombre_modulo
        FROM Empleados e
        LEFT JOIN ModuloConfeccion m ON e.modulo_asignado = m.id
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
            "especialidad": fila[4],
            "turno": fila[5],
            "fecha_ingreso": fila[6],
            "estado": fila[7],
            "telefono": fila[8],
            "email": fila[9],
            "modulo_asignado": fila[10],
            "nombre_modulo": fila[11]
        }
    return None


def insertar_empleado(nombre, numero_documento, cargo, especialidad=None, turno=None,
                      fecha_ingreso=None, estado='Activo', telefono=None, email=None,
                      modulo_asignado=None):
    """Inserta un nuevo empleado."""
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            INSERT INTO Empleados (nombre, numero_documento, cargo, especialidad, turno,
                                   fecha_ingreso, estado, telefono, email, modulo_asignado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, numero_documento, cargo, especialidad, turno, fecha_ingreso,
              estado, telefono, email, modulo_asignado))
        conexion.commit()
        nuevo_id = cursor.lastrowid
        conexion.close()
        return {"mensaje": "Empleado guardado con éxito", "id": nuevo_id}
    except sqlite3.IntegrityError:
        conexion.close()
        return {"error": "El número de documento ya existe"}


def actualizar_empleado(id_empleado, nombre, numero_documento, cargo, especialidad=None,
                        turno=None, fecha_ingreso=None, estado='Activo', telefono=None,
                        email=None, modulo_asignado=None):
    """Actualiza un empleado existente."""
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    try:
        cursor.execute("""
            UPDATE Empleados
            SET nombre=?, numero_documento=?, cargo=?, especialidad=?, turno=?,
                fecha_ingreso=?, estado=?, telefono=?, email=?, modulo_asignado=?
            WHERE id=?
        """, (nombre, numero_documento, cargo, especialidad, turno, fecha_ingreso,
              estado, telefono, email, modulo_asignado, id_empleado))
        conexion.commit()
        conexion.close()
        return {"mensaje": "Empleado actualizado con éxito"}
    except sqlite3.IntegrityError:
        conexion.close()
        return {"error": "El número de documento ya existe"}


def eliminar_empleado(id_empleado):
    """Elimina un empleado por ID."""
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM Empleados WHERE id = ?", (id_empleado,))
    conexion.commit()
    conexion.close()
    return {"mensaje": "Empleado eliminado con éxito"}

if __name__ == "__main__":
    inicializar_base_de_datos()
