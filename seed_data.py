import sqlite3
import random
from datetime import date, timedelta

DB_NAME = "balanceo_produccion.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def limpiar_tablas(conn):
    cursor = conn.cursor()
    tablas = [
        "ControlHoraHora",
        "Empleados",
        "AsignacionModulo",
        "ReferenciaDetalle",
        "ReferenciaProducto",
        "Operacion",
        "TipoMaquinaria",
        "SeccionPrenda",
        "ModuloConfeccion",
        "HorasProduccion",
        "ParadasProgramadas"
    ]
    for t in tablas:
        cursor.execute(f"DELETE FROM {t}")
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{t}'")
    conn.commit()
    print("Tablas limpiadas.")

def seed_catalogos(conn):
    cursor = conn.cursor()

    maquinas = [
        ("PLANA", "Costura recta general para uniones principales", 150, "Activa"),
        ("FILETEADORA", "Acabado de bordes y costuras para evitar deshilachado", 120, "Activa"),
        ("BORDADORA", "Bordado de logos y diseños decorativos", 80, "Activa"),
        ("OJETERA", "Colocación de ojetes metálicos para ventilación", 200, "Activa"),
        ("BOTONERA", "Colocación de botones, broches y snaps", 180, "Activa"),
        ("RIBETADORA", "Ribete y acabado de viseras", 100, "Activa"),
        ("PRENSA TERMICA", "Moldeo, planchado y aplicación de transfers", 90, "Activa"),
        ("CORTADORA", "Corte de telas y materiales con precisión", 250, "Activa")
    ]
    cursor.executemany("INSERT INTO TipoMaquinaria (nombre, descripcion, velocidad_tipica, estado) VALUES (?, ?, ?, ?)", maquinas)

    secciones = [
        ("CORONA (PANELES)", "Paneles que forman la copa de la gorra", 1),
        ("VISERA", "Parte frontal rígida que protege del sol", 2),
        ("BANDA INTERIOR", "Sweatband y unión corona-visera", 3),
        ("CIERRE/AJUSTE", "Sistemas de cierre trasero (snapback, velcro, hebilla)", 4),
        ("ACABADOS", "Botón superior, ojetes, control de calidad y empaque", 5),
        ("BORDADO/LOGO", "Bordados decorativos y logos de marca", 6)
    ]
    cursor.executemany("INSERT INTO SeccionPrenda (nombre, descripcion, orden_proceso) VALUES (?, ?, ?)", secciones)

    modulos = [
        ("Línea 1", 8, "Nave A - Piso 1", "Carlos Rodríguez", "Activo"),
        ("Línea 2", 8, "Nave A - Piso 1", "María González", "Activo"),
        ("Línea 3", 6, "Nave A - Piso 2", "Juan Martínez", "Activo"),
        ("Línea 4", 6, "Nave A - Piso 2", "Ana López", "Activo"),
        ("Línea 5", 8, "Nave B - Piso 1", "Pedro Sánchez", "Activo"),
        ("Línea 6", 8, "Nave B - Piso 1", "Laura Ramírez", "Activo"),
        ("Línea 7", 6, "Nave B - Piso 2", "Diego Torres", "Activo"),
        ("Línea 8", 6, "Nave B - Piso 2", "Sofía Vargas", "Activo")
    ]
    cursor.executemany("INSERT INTO ModuloConfeccion (nombre, capacidad_maxima, ubicacion, supervisor, estado) VALUES (?, ?, ?, ?, ?)", modulos)

    horas = [
        ("Hora 1", "07:00", "08:00", "Mañana"),
        ("Hora 2", "08:00", "09:00", "Mañana"),
        ("Hora 3", "09:00", "10:00", "Mañana"),
        ("Hora 4", "10:00", "11:00", "Mañana"),
        ("Hora 5", "11:00", "12:00", "Mañana"),
        ("Hora 6", "13:00", "14:00", "Tarde"),
        ("Hora 7", "14:00", "15:00", "Tarde"),
        ("Hora 8", "15:00", "16:00", "Tarde"),
        ("Hora 9", "16:00", "17:00", "Tarde"),
        ("Hora Extra", "17:00", "18:00", "Extra")
    ]
    cursor.executemany("INSERT INTO HorasProduccion (nombre, hora_inicio, hora_fin, turno) VALUES (?, ?, ?, ?)", horas)

    paradas = [
        ("Desayuno", 900, "Obligatoria", "Diaria"),
        ("Almuerzo", 1800, "Obligatoria", "Diaria"),
        ("Pausa Activa", 300, "Opcional", "Diaria"),
        ("Cambio de Referencia", 600, "Obligatoria", "Por cambio de ref"),
        ("Mantenimiento", 1200, "Opcional", "Semanal"),
        ("Ninguna", 0, "Opcional", "Diaria")
    ]
    cursor.executemany("INSERT INTO ParadasProgramadas (nombre, tiempo_segundos, tipo, frecuencia) VALUES (?, ?, ?, ?)", paradas)

    conn.commit()
    print("Catalogos insertados.")

def seed_operaciones(conn):
    cursor = conn.cursor()

    operaciones = [
        ("Cortar paneles de corona", 35, 8, 1),
        ("Filetear bordes de paneles", 25, 2, 1),
        ("Unir paneles de corona (6 piezas)", 45, 1, 1),
        ("Pegar entretela a visera", 30, 1, 2),
        ("Cortar visera", 20, 8, 2),
        ("Ribetear visera", 40, 6, 2),
        ("Unir visera a corona", 50, 1, 3),
        ("Colocar banda interior (sweatband)", 55, 1, 3),
        ("Filetear unión corona-visera", 30, 2, 3),
        ("Colocar cierre trasero (snapback)", 35, 5, 4),
        ("Colocar ajuste velcro", 30, 1, 4),
        ("Colocar ajuste hebilla metalica", 40, 1, 4),
        ("Bordar logo frontal", 60, 3, 6),
        ("Bordar logo lateral", 45, 3, 6),
        ("Colocar boton superior", 15, 5, 5),
        ("Colocar ojetes de ventilacion", 25, 4, 5),
        ("Prensar y dar forma final", 35, 7, 5),
        ("Control de calidad visual", 20, 1, 5),
        ("Colocar etiqueta interior", 15, 1, 5),
        ("Empacar unidad", 10, 1, 5),
    ]
    cursor.executemany(
        "INSERT INTO Operacion (nombre_operacion, tiempo_segundos, id_maquina, id_seccion) VALUES (?, ?, ?, ?)",
        operaciones
    )
    conn.commit()
    print(f"{len(operaciones)} operaciones insertadas.")

def seed_referencias(conn):
    cursor = conn.cursor()

    referencias = [
        ("Gorra Snapback Clasica", 30000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 15, 16, 17, 18, 19, 20]),
        ("Gorra Trucker Malla", 25000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 16, 17, 18, 19, 20]),
        ("Gorra Dad Hat Curvada", 20000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 13, 15, 16, 17, 18, 19, 20]),
        ("Gorra 5 Panel Camp", 18000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 17, 18, 19, 20]),
        ("Gorra Deportiva Dry-Fit", 35000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 16, 17, 18, 19, 20]),
        ("Gorra Military Flat", 15000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 15, 17, 18, 19, 20]),
        ("Gorra Bucket Hat", 28000, [1, 2, 3, 7, 8, 9, 15, 17, 18, 19, 20]),
        ("Gorra Snapback Premium Bordada", 12000, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20]),
    ]

    for nombre, lote, ops in referencias:
        cursor.execute(
            "INSERT INTO ReferenciaProducto (nombre_referencia, cantidad_lote) VALUES (?, ?)",
            (nombre, lote)
        )
        ref_id = cursor.lastrowid

        letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, op_id in enumerate(ops):
            letra = letras[i]
            pred = "N/A" if i == 0 else letras[i - 1]
            cursor.execute(
                "INSERT INTO ReferenciaDetalle (id_referencia, id_operacion, letra_secuencia, predecesoras, orden_fila) VALUES (?, ?, ?, ?, ?)",
                (ref_id, op_id, letra, pred, i + 1)
            )

    conn.commit()
    print(f"{len(referencias)} referencias con secuencias insertadas.")

def seed_asignaciones(conn):
    cursor = conn.cursor()

    cursor.execute("SELECT id, cantidad_lote FROM ReferenciaProducto")
    refs = cursor.fetchall()

    cursor.execute("SELECT id FROM ModuloConfeccion")
    modulos = [r[0] for r in cursor.fetchall()]

    asignaciones = []
    for ref_id, lote in refs:
        modulos_usados = random.sample(modulos, min(random.randint(2, 4), len(modulos)))
        restante = lote
        for i, mod_id in enumerate(modulos_usados):
            if i == len(modulos_usados) - 1:
                cant = restante
            else:
                cant = random.randint(restante // (len(modulos_usados) - i) // 2, restante // (len(modulos_usados) - i))
                cant = min(cant, restante)
            restante -= cant
            asignaciones.append((ref_id, mod_id, cant))

    cursor.executemany(
        "INSERT INTO AsignacionModulo (id_referencia, id_modulo, cantidad_asignada) VALUES (?, ?, ?)",
        asignaciones
    )
    conn.commit()
    print(f"{len(asignaciones)} asignaciones insertadas.")

def seed_control_hora(conn, target_registros=1500):
    cursor = conn.cursor()

    cursor.execute("SELECT id, id_referencia, id_modulo, cantidad_asignada FROM AsignacionModulo")
    asignaciones = cursor.fetchall()

    cursor.execute("SELECT id FROM HorasProduccion")
    horas = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT id, tiempo_segundos FROM ParadasProgramadas")
    paradas = cursor.fetchall()
    parada_ninguna = [p for p in paradas if p[1] == 0][0]
    paradas_reales = [p for p in paradas if p[1] > 0]

    cursor.execute("SELECT id_referencia, SUM(o.tiempo_segundos) FROM ReferenciaDetalle rd JOIN Operacion o ON rd.id_operacion = o.id GROUP BY rd.id_referencia")
    tc_cache = dict(cursor.fetchall())

    hoy = date.today()
    dias_atras = 30
    registros = []
    produccion_acumulada = {a[0]: 0 for a in asignaciones}

    intentos = 0
    max_intentos = target_registros * 5

    while len(registros) < target_registros and intentos < max_intentos:
        intentos += 1

        asig_disponibles = [a for a in asignaciones if produccion_acumulada[a[0]] < a[3]]
        if not asig_disponibles:
            break

        asig = random.choice(asig_disponibles)
        asig_id, ref_id, mod_id, cant_asignada = asig

        saldo = cant_asignada - produccion_acumulada[asig_id]
        if saldo <= 0:
            continue

        dias_offset = random.randint(0, dias_atras)
        fecha = (hoy - timedelta(days=dias_offset)).isoformat()

        id_hora = random.choice(horas)
        porcion = round(random.choice([0.5, 0.5, 1.0, 1.0, 1.0]), 1)

        tc = tc_cache.get(ref_id, 300)
        num_operarios = random.randint(4, 8)

        if random.random() < 0.3:
            parada = random.choice(paradas_reales)
            parada_id, parada_tiempo = parada
        else:
            parada_id, parada_tiempo = parada_ninguna

        td = (num_operarios * 3600 * porcion) - (parada_tiempo * num_operarios if parada_tiempo > 0 else 0)
        meta = max(1, int(td / tc)) if tc > 0 else 1

        eficiencia_factor = random.uniform(0.65, 1.15)
        cantidad = max(1, int(meta * eficiencia_factor))
        cantidad = min(cantidad, saldo)

        if cantidad <= 0:
            continue

        produccion_acumulada[asig_id] += cantidad

        desc_np = ""
        tiempo_np = 0
        if random.random() < 0.1:
            causas = [
                ("Falta de material", random.randint(300, 900)),
                ("Averia de maquina", random.randint(600, 1800)),
                ("Cambio de operario", random.randint(120, 600)),
                ("Problema de calidad", random.randint(300, 900)),
            ]
            desc_np, tiempo_np = random.choice(causas)

        registros.append((
            fecha, mod_id, asig_id, id_hora, porcion,
            float(num_operarios), cantidad, parada_id, parada_tiempo,
            desc_np, tiempo_np
        ))

    cursor.executemany("""
        INSERT INTO ControlHoraHora (
            fecha, id_modulo, id_asignacion, id_hora, porcion_tiempo,
            cantidad_operarios, cantidad_producida, id_parada_programada,
            tiempo_parada_programada, descripcion_parada_no_programada,
            tiempo_parada_no_programada
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, registros)

    conn.commit()
    print(f"{len(registros)} registros de control hora a hora insertados.")

def seed_empleados(conn):
    cursor = conn.cursor()
    
    empleados = [
        ("Carlos Rodríguez", "12345678", "Operario", "PLANA", "Mañana", "2023-03-15", "Activo", "123-456-7890", "carlos.r@empresa.com", 1),
        ("María González", "23456789", "Operario", "FILETEADORA", "Mañana", "2022-08-20", "Activo", "234-567-8901", "maria.g@empresa.com", 1),
        ("Juan Martínez", "34567890", "Supervisor", "PLANA", "Mañana", "2020-01-10", "Activo", "345-678-9012", "juan.m@empresa.com", 1),
        ("Ana López", "45678901", "Operario", "BORDADORA", "Tarde", "2023-06-01", "Activo", "456-789-0123", "ana.l@empresa.com", 2),
        ("Pedro Sánchez", "56789012", "Operario", "OJETERA", "Tarde", "2022-11-15", "Activo", "567-890-1234", "pedro.s@empresa.com", 2),
        ("Laura Ramírez", "67890123", "Supervisor", "FILETEADORA", "Tarde", "2021-04-22", "Activo", "678-901-2345", "laura.r@empresa.com", 2),
        ("Diego Torres", "78901234", "Operario", "BOTONERA", "Mañana", "2023-09-05", "Activo", "789-012-3456", "diego.t@empresa.com", 3),
        ("Sofía Vargas", "89012345", "Operario", "RIBETADORA", "Mañana", "2022-07-18", "Activo", "890-123-4567", "sofia.v@empresa.com", 3),
        ("Miguel Ángel Castro", "90123456", "Mecánico", "PLANA", "Mañana", "2021-02-28", "Activo", "901-234-5678", "miguel.c@empresa.com", 4),
        ("Isabel Moreno", "01234567", "Operario", "PRENSA TERMICA", "Tarde", "2023-01-12", "Activo", "012-345-6789", "isabel.m@empresa.com", 4),
        ("Roberto Jiménez", "11223344", "Operario", "CORTADORA", "Mañana", "2022-05-30", "Activo", "112-233-4455", "roberto.j@empresa.com", 5),
        ("Patricia Flores", "22334455", "Auxiliar", "PLANA", "Tarde", "2023-08-14", "Activo", "223-344-5566", "patricia.f@empresa.com", 5),
        ("Fernando Ruiz", "33445566", "Operario", "FILETEADORA", "Mañana", "2021-11-08", "Activo", "334-455-6677", "fernando.r@empresa.com", 6),
        ("Carmen Delgado", "44556677", "Operario", "BORDADORA", "Tarde", "2022-09-25", "Activo", "445-566-7788", "carmen.d@empresa.com", 6),
        ("Alejandro Vega", "55667788", "Supervisor", "PLANA", "Mañana", "2020-06-17", "Activo", "556-677-8899", "alejandro.v@empresa.com", 7),
        ("Lucía Herrera", "66778899", "Operario", "OJETERA", "Mañana", "2023-04-03", "Activo", "667-788-9900", "lucia.h@empresa.com", 7),
        ("Gabriel Mendoza", "77889900", "Operario", "BOTONERA", "Tarde", "2022-12-19", "Activo", "778-899-0011", "gabriel.m@empresa.com", 8),
        ("Valentina Ortega", "88990011", "Operario", "RIBETADORA", "Tarde", "2023-07-07", "Activo", "889-900-1122", "valentina.o@empresa.com", 8),
        ("Ricardo Peña", "99001122", "Mecánico", "FILETEADORA", "Mañana", "2021-10-11", "Activo", "990-011-2233", "ricardo.p@empresa.com", 1),
        ("Daniela Cruz", "10112233", "Auxiliar", "BORDADORA", "Tarde", "2023-02-26", "Activo", "101-122-3344", "daniela.c@empresa.com", 2),
    ]
    
    cursor.executemany("""
        INSERT INTO Empleados (nombre, numero_documento, cargo, especialidad, turno,
                               fecha_ingreso, estado, telefono, email, modulo_asignado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, empleados)
    
    conn.commit()
    print(f"{len(empleados)} empleados insertados.")


def main():
    conn = get_connection()
    try:
        limpiar_tablas(conn)
        seed_catalogos(conn)
        seed_operaciones(conn)
        seed_referencias(conn)
        seed_asignaciones(conn)
        seed_control_hora(conn, target_registros=1200)
        seed_empleados(conn)
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ControlHoraHora")
        total = cursor.fetchone()[0]
        print(f"\nTotal registros en ControlHoraHora: {total}")
        print("Seed completado exitosamente.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
