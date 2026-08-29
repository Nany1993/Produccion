import sqlite3
import random
from datetime import date, timedelta
from database import inicializar_base_de_datos

DB_NAME = "balanceo_produccion.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def main():
    inicializar_base_de_datos()
    conn = get_connection()
    cursor = conn.cursor()

    # Limpiar todo (menos catálogos maestros)
    for t in ["ParadaRegistro", "RegistroProduccion", "AsignacionUsuarioLinea", "Usuario",
              "ControlHoraHora", "Empleados", "AsignacionModulo", "OrdenProduccion",
              "ReferenciaMaterial", "ReferenciaDetalle", "ReferenciaProducto", "Operacion",
              "TipoMaquinaria", "SeccionPrenda", "ModuloConfeccion", "HorasProduccion",
              "ParadasProgramadas", "Materiales", "CausaParada"]:
        cursor.execute(f"DELETE FROM {t}")
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{t}'")

    # Catálogos maestros necesarios
    maquinas = ["PLANA", "FILETEADORA", "BORDADORA", "OJETERA", "BOTONERA", "RIBETADORA", "PRENSA TERMICA", "CORTADORA"]
    cursor.executemany("INSERT INTO TipoMaquinaria (nombre) VALUES (?)", [(m,) for m in maquinas])

    secciones = ["CORONA (PANELES)", "VISERA", "BANDA INTERIOR", "CIERRE/AJUSTE", "ACABADOS", "BORDADO/LOGO"]
    cursor.executemany("INSERT INTO SeccionPrenda (nombre) VALUES (?)", [(s,) for s in secciones])

    for i in range(1, 9):
        cursor.execute("INSERT INTO ModuloConfeccion (nombre) VALUES (?)", (f"Línea {i}",))
    hor = [("Hora 1", "07:00", "08:00", "Mañana"), ("Hora 2", "08:00", "09:00", "Mañana"),
           ("Hora 3", "09:00", "10:00", "Mañana"), ("Hora 4", "10:00", "11:00", "Mañana"),
           ("Hora 5", "11:00", "12:00", "Mañana"), ("Hora 6", "13:00", "14:00", "Tarde"),
           ("Hora 7", "14:00", "15:00", "Tarde"), ("Hora 8", "15:00", "16:00", "Tarde"),
           ("Hora 9", "16:00", "17:00", "Tarde"), ("Hora Extra", "17:00", "18:00", "Extra")]
    cursor.executemany("INSERT INTO HorasProduccion (nombre, hora_inicio, hora_fin, turno) VALUES (?, ?, ?, ?)", hor)

    paradas = [("Desayuno", 900, "Obligatoria", "Diaria"), ("Almuerzo", 1800, "Obligatoria", "Diaria"),
               ("Pausa Activa", 300, "Opcional", "Diaria"), ("Cambio de Referencia", 600, "Obligatoria", "Por cambio de ref"),
               ("Mantenimiento", 1200, "Opcional", "Semanal"), ("Ninguna", 0, "Opcional", "Diaria")]
    cursor.executemany("INSERT INTO ParadasProgramadas (nombre, tiempo_segundos, tipo, frecuencia) VALUES (?, ?, ?, ?)", paradas)

    # Operaciones del diagrama de la gorra
    operaciones = [
        ("Cortar paneles de corona", 35, 8, 1),
        ("Filetear bordes de paneles", 25, 2, 1),
        ("Unir paneles de corona (6 piezas)", 45, 1, 1),
        ("Pegar entretela a visera", 30, 1, 2),
        ("Cortar visera", 20, 8, 2),
        ("Ribetear visera", 40, 6, 2),
        ("Unir visera a corona", 50, 1, 3),
        ("Colocar banda interior (sweatband)", 55, 1, 3),
        ("Filetear union corona-visera", 30, 2, 3),
        ("Bordar logo frontal", 60, 3, 6),
        ("Colocar ojetes de ventilacion", 25, 4, 5),
        ("Colocar boton superior", 15, 5, 5),
        ("Colocar cierre trasero (snapback)", 35, 5, 4),
        ("Prensar y dar forma final", 35, 7, 5),
        ("Control de calidad visual", 20, 1, 5),
        ("Colocar etiqueta interior", 15, 1, 5),
        ("Empacar unidad", 10, 1, 5),
    ]
    cursor.executemany("""
        INSERT INTO Operacion (nombre_operacion, tiempo_segundos, id_maquina, id_seccion)
        VALUES (?, ?, ?, ?)
    """, operaciones)

    # Materiales
    materiales = [
        ("Popelín 120g/m²", "metros", 2500, "Textiles Andinos", "Tela base para corona"),
        ("Entretela de visera", "metros", 900, "Suministros AB", "Rigidez para visera"),
        ("Banda interior", "metros", 700, "Suministros AB", "Cinta sweatband absorbente"),
        ("Cierre snapback", "unidades", 1200, "Cierres Expertos", "Ajuste trasero con broches"),
        ("Botón superior", "unidades", 150, "Badia & Cía", "Botón de cierre de paneles"),
        ("Ojete metálico", "unidades", 80, "Badia & Cía", "Ojetes de ventilación (x2)"),
        ("Hilo de coser", "conos", 15000, "Hilaza Nacional", "Hilo para costura general"),
        ("Etiqueta interior", "unidades", 200, "Etiquetas PRO", "Etiqueta de talla y marca"),
        ("Empaque / bolsa", "unidades", 150, "Empaques Eco", "Bolsa para unidad"),
    ]
    cursor.executemany("INSERT INTO Materiales (nombre, unidad, costo_unitario, proveedor, descripcion) VALUES (?, ?, ?, ?, ?)", materiales)

    conn.commit()

    # Solo la referencia Snapback Clásica
    cursor.execute("""
        INSERT INTO ReferenciaProducto (nombre_referencia, especificaciones)
        VALUES ('Gorra Snapback Clasica',
                'Gorra 6 paneles, corte con costura, visera curva 60° con 7 líneas de costura, cierre trasero snapback ajustable, banda interior absorbente. Material: popelín 120g/m².')
    """)
    ref_id = cursor.lastrowid

    # Diagrama de actividades coherente: letras A..Q con precedencias encadenadas
    secuencia = [
        ("Cortar paneles de corona", "A", "N/A"),
        ("Filetear bordes de paneles", "B", "A"),
        ("Unir paneles de corona (6 piezas)", "C", "B"),
        ("Pegar entretela a visera", "D", "N/A"),
        ("Cortar visera", "E", "D"),
        ("Ribetear visera", "F", "E"),
        ("Unir visera a corona", "G", "C,F"),
        ("Colocar banda interior (sweatband)", "H", "G"),
        ("Filetear union corona-visera", "I", "H"),
        ("Bordar logo frontal", "J", "C"),
        ("Colocar ojetes de ventilacion", "K", "I"),
        ("Colocar boton superior", "L", "I"),
        ("Colocar cierre trasero (snapback)", "M", "I"),
        ("Prensar y dar forma final", "N", "K,L,M"),
        ("Control de calidad visual", "O", "N"),
        ("Colocar etiqueta interior", "P", "O"),
        ("Empacar unidad", "Q", "P"),
    ]

    cursor.execute("SELECT id, nombre_operacion, id_maquina, id_seccion FROM Operacion")
    ops = {row[1]: row[0] for row in cursor.fetchall()}

    for nombre, letra, pred in secuencia:
        id_op = ops[nombre]
        cursor.execute("""
            INSERT INTO ReferenciaDetalle (id_referencia, id_operacion, letra_secuencia, predecesoras, orden_fila)
            VALUES (?, ?, ?, ?, ?)
        """, (ref_id, id_op, letra, pred, secuencia.index((nombre, letra, pred)) + 1))

    # BOM de la gorra
    cursor.execute("SELECT id, nombre FROM Materiales")
    mats = {m[1]: m[0] for m in cursor.fetchall()}

    bom = [
        ("Popelín 120g/m²", 0.30, 5),
        ("Entretela de visera", 0.20, 3),
        ("Banda interior", 0.28, 2),
        ("Cierre snapback", 1, 0),
        ("Botón superior", 1, 0),
        ("Ojete metálico", 2, 0),
        ("Hilo de coser", 0.05, 0),
        ("Etiqueta interior", 1, 0),
        ("Empaque / bolsa", 1, 0),
    ]
    for mat_nombre, cant, merma in bom:
        cursor.execute("""
            INSERT INTO ReferenciaMaterial (id_referencia, id_material, cantidad_por_unidad, merma_porcentaje)
            VALUES (?, ?, ?, ?)
        """, (ref_id, mats[mat_nombre], cant, merma))

    # Dos órdenes de producción de la misma referencia
    cursor.execute("SELECT id FROM ModuloConfeccion")
    modulos = [m[0] for m in cursor.fetchall()]

    ordenes = [
        ("LOTE-SNP-001", 30000, "Abierta"),
        ("LOTE-SNP-002", 15000, "Abierta"),
    ]
    for nombre_orden, cantidad, estado in ordenes:
        cursor.execute("""
            INSERT INTO OrdenProduccion (id_referencia, nombre_orden, cantidad_lote, estado)
            VALUES (?, ?, ?, ?)
        """, (ref_id, nombre_orden, cantidad, estado))
        orden_id = cursor.lastrowid

        mod = random.choice(modulos)
        cursor.execute("""
            INSERT INTO AsignacionModulo (id_orden, id_modulo, cantidad_asignada)
            VALUES (?, ?, ?)
        """, (orden_id, mod, int(cantidad * random.uniform(0.3, 0.6))))

    # Recrear empleados (mínimo)
    cursor.execute("DELETE FROM Empleados")
    cursor.execute("DELETE FROM Usuario")
    cursores_empleados = [
        ("Carlos Rodriguez", "12345678", "Supervisor", "PLANA", "Manana", "2023-03-15", "Activo", "1234567890", "carlos@planta.com", modulos[0]),
        ("Maria Gonzalez", "23456789", "Operario", "FILETEADORA", "Manana", "2022-08-20", "Activo", "2345678901", "maria@planta.com", modulos[1]),
        ("Juan Martinez", "34567890", "Operario", "BORDADORA", "Tarde", "2021-01-10", "Activo", "3456789012", "juan@planta.com", modulos[2]),
        ("Ana Lopez", "45678901", "Operario", "OJETERA", "Tarde", "2023-06-01", "Activo", "4567890123", "ana@planta.com", modulos[3]),
    ]
    cursor.executemany("""
        INSERT INTO Empleados (nombre, numero_documento, cargo, especialidad, turno, fecha_ingreso, estado, telefono, email, modulo_asignado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, cursores_empleados)

    # Usuarios iniciales (login sencillo, si no existen)
    cursor.execute("SELECT COUNT(*) FROM Usuario")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id FROM Empleados WHERE cargo = 'Supervisor' LIMIT 1")
        sup_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO Usuario (nombre_usuario, password, rol, id_empleado) VALUES ('carlos', '1234', 'Supervisor', ?)", (sup_id,))
        cursor.execute("SELECT id FROM Empleados WHERE cargo != 'Supervisor' LIMIT 1")
        emp_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO Usuario (nombre_usuario, password, rol, id_empleado) VALUES ('operario', '1234', 'Operador', ?)", (emp_id,))

    # Causas de parada (si la limpieza las borró, se regeneran)
    cursor.execute("SELECT COUNT(*) FROM CausaParada")
    if cursor.fetchone()[0] == 0:
        causas = ["Falta de material", "Avería de máquina", "Cambio de operario",
                  "Problema de calidad", "Falta de energía", "Reunión/socialización",
                  "Espera de instrucciones", "Cambio de referencia", "Otro"]
        cursor.executemany("INSERT INTO CausaParada (nombre) VALUES (?)", [(c,) for c in causas])

    conn.commit()

    print(f"Referencia única: Gorra Snapback Clasica (id={ref_id})")
    print(f"Secuencia: {len(secuencia)} operaciones (A-Q)")
    print(f"BOM: {len(bom)} materiales")
    print(f"Órdenes: {len(ordenes)}")
    print("BD reconstruida.")

    conn.close()

if __name__ == "__main__":
    main()