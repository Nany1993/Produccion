"""Simulación realista del mes de agosto para la planta de gorras.
- 1 referencia: Gorra Snapback Pro 6 Paneles
- Máquinas y líneas reales de la industria de la gorra
- 3 órdenes de producción en agosto (inicio, mitad, fin)
- Registro diario por ACTIVIDAD con horas, operarios, paradas y defectuosas
"""

import sqlite3
import random
from datetime import date, timedelta
from database import inicializar_base_de_datos

DB_NAME = "balanceo_produccion.db"

def con():
    c = sqlite3.connect(DB_NAME)
    c.execute("PRAGMA foreign_keys = ON;")
    return c

def limpiar(conn):
    cur = conn.cursor()
    tablas = ["ParadaRegistro", "RegistroProduccion", "AsignacionUsuarioLinea", "Usuario",
              "Empleados", "AsignacionModulo", "OrdenProduccion",
              "ReferenciaMaterial", "ReferenciaDetalle", "ReferenciaProducto", "Operacion",
              "TipoMaquinaria", "SeccionPrenda", "ModuloConfeccion", "HorasProduccion",
              "ParadasProgramadas", "Materiales", "CausaParada"]
    for t in tablas:
        cur.execute(f"DELETE FROM {t}")
        cur.execute(f"DELETE FROM sqlite_sequence WHERE name='{t}'")
    conn.commit()

def maquinas_reales(conn):
    cur = conn.cursor()
    # Máquinas reales de la industria de gorras, cada una asignada a su línea (módulo)
    # Orden de líneas: 1=Corte, 2=Paneles, 3=Viseras, 4=Ensamble, 5=Bordado, 6=Terminado
    cur.execute("SELECT id FROM ModuloConfeccion ORDER BY id")
    lineas = [r[0] for r in cur.fetchall()]
    # id_modulo: corte, paneles, viseras, ensamble, bordado, terminado (y 7-9 en líneas de acabado/terminal)
    maquinas = [
        ("Recta JUKI DDL-8700", "Costura recta de alta velocidad para paneles y ensamble", 140, "Activa", lineas[3]),
        ("Fileteadora JUKI MO-6714", "Sobrehilado y acabado de bordes", 120, "Activa", lineas[1]),
        ("Bordadora Tajima TMAR-K1506", "Bordado multicolor de logos frontal y lateral", 60, "Activa", lineas[4]),
        ("Ojetera industriel", "Colocación de ojetes de ventilación", 180, "Activa", lineas[5]),
        ("Botonera/premilladora CAMPO", "Colocación de botón superior y snaps del cierre", 160, "Activa", lineas[5]),
        ("Ribeteadora de visera", "Ribete y ala de la visera con molde curvo", 90, "Activa", lineas[2]),
        ("Prensa de visera térmica", "Moldeado y fijación de forma de la visera", 70, "Activa", lineas[2]),
        ("Cortadora de tela (mesa)", "Cortado de paneles, viseras y entretelas", 200, "Activa", lineas[0]),
        ("Mesa de revisión y empaque", "Control de calidad, etiquetado y empaque final", 0, "Activa", lineas[5]),
    ]
    cur.executemany("INSERT INTO TipoMaquinaria (nombre, descripcion, velocidad_tipica, estado, id_modulo) VALUES (?,?,?,?,?)", maquinas)

def secciones_gorra(conn):
    cur = conn.cursor()
    secciones = [
        ("CORONA / PANELES", "Ses partes que forman la copa de la gorra", 1),
        ("VISERA", "Parte frontal rígida con molde curvo o plano", 2),
        ("BANDA INTERIOR", "Cinta/sweatband y unión corona-visera", 3),
        ("CIERRE / AJUSTE", "Snapback, velcro o tira y hebilla", 4),
        ("ACABADOS", "Botón, ojetes, molde final, calidad, etiqueta, empaque", 5),
        ("BORDADO", "Bordados de logos y marca", 6),
    ]
    cur.executemany("INSERT INTO SeccionPrenda (nombre, descripcion, orden_proceso) VALUES (?,?,?)", secciones)

def lineas_reales(conn):
    cur = conn.cursor()
    lineas = [
        ("Línea 1 - Corte y Preparación", 6, "Nave A - Piso 1", "Carlos Rodriguez", "Activo"),
        ("Línea 2 - Paneles y Corona", 8, "Nave A - Piso 1", "Maria Gonzalez", "Activo"),
        ("Línea 3 - Viseras", 6, "Nave A - Piso 2", "Laura Ramirez", "Activo"),
        ("Línea 4 - Ensamble Principal", 10, "Nave B - Piso 1", "Juan Martinez", "Activo"),
        ("Línea 5 - Bordado", 4, "Nave B - Piso 2", "Diego Torres", "Activo"),
        ("Línea 6 - Terminado y Empaque", 6, "Nave B - Piso 2", "Sofia Vargas", "Activo"),
    ]
    cur.executemany("INSERT INTO ModuloConfeccion (nombre, capacidad_maxima, ubicacion, supervisor, estado) VALUES (?,?,?,?,?)", lineas)

def horas(conn):
    cur = conn.cursor()
    hrs = [("Hora 1","07:00","08:00"), ("Hora 2","08:00","09:00"),
           ("Hora 3","09:00","10:00"), ("Hora 4","10:00","11:00"),
           ("Hora 5","11:00","12:00"), ("Hora 6","13:00","14:00"),
           ("Hora 7","14:00","15:00"), ("Hora 8","15:00","16:00"),
           ("Hora 9","16:00","17:00"), ("Hora Extra","17:00","18:00")]
    cur.executemany("INSERT INTO HorasProduccion (nombre, hora_inicio, hora_fin) VALUES (?,?,?)", hrs)

def paradas(conn):
    cur = conn.cursor()
    ps = [("Desayuno", 900, "Obligatoria", "Diaria"),
          ("Almuerzo", 1800, "Obligatoria", "Diaria"),
          ("Pausa Activa", 300, "Opcional", "Diaria"),
          ("Cambio de referencia", 600, "Obligatoria", "Por cambio de ref"),
          ("Mantenimiento preventivo", 1200, "Obligatoria", "Semanal"),
          ("Ninguna", 0, "Opcional", "Diaria")]
    cur.executemany("INSERT INTO ParadasProgramadas (nombre, tiempo_segundos, tipo, frecuencia) VALUES (?,?,?,?)", ps)

def causas(conn):
    cur = conn.cursor()
    cs = ["Falta de material", "Avería de máquina", "Cambio de operario", "Problema de calidad",
          "Falta de energía", "Reunión/socialización", "Espera de instrucciones", "Cambio de referencia", "Otro"]
    cur.executemany("INSERT INTO CausaParada (nombre) VALUES (?)", [(c,) for c in cs])

def materiales(conn):
    cur = conn.cursor()
    mats = [
        ("Tela poliéster 300D", "metros", 3500, "Textiles Andinos", "Tela principal para paneles"),
        ("Malla de ventilación", "metros", 2200, "Textiles Andinos", "Paneles traseros tipo trucker"),
        ("Entretela termo adhesiva", "metros", 980, "Suministros AB", "Rigidez de visera y panel frontal"),
        ("Cinta sweatband 1.5\"", "metros", 740, "Suministros AB", "Banda interior absorbente"),
        ("Cinta de refuerzo", "metros", 520, "Sombreritos SA", "Refuerzo de costuras"),
        ("Cierre snapback (broche)", "unidades", 1250, "Cierres Expertos", "Ajuste trasero con broche"),
        ("Botón superior de metal", "unidades", 320, "Badia & Cía", "Botón de remate de paneles"),
        ("Ojete de latón", "unidades", 95, "Badia & Cía", "Ojetes de ventilación (x4)"),
        ("Hilo de poliéster", "conos", 14500, "Hilaza Nacional", "Hilo de costura (usan varios colores)"),
        ("Etiqueta de talla y marca", "unidades", 210, "Etiquetas PRO", "Etiqueta interior"),
        ("Bolsa de empaque", "unidades", 160, "Empaques Eco", "Bolsa individual"),
    ]
    cur.executemany("INSERT INTO Materiales (nombre, unidad, costo_unitario, proveedor, descripcion) VALUES (?,?,?,?,?)", mats)

def empleados(conn):
    cur = conn.cursor()
    # (nombre, doc, cargo libre, rol, turno, ingres, estado, tel, email, modulo, id_maquina o None)
    # ids máquinas: 1=Recta,2=Fileteadora,3=Bordadora,4=Ojetera,5=Botonera,6=Ribeteadora,7=Prensa,8=Cortadora,9=Mesa
    emp = [
        ("Carlos Rodriguez", "12345678", "Jefe de línea de ensamble", "Supervisor", "Mañana", "2022-03-15", "Activo", "3001112233", "carlos@planta.com", None, None),
        ("Maria Gonzalez", "23456789", "Operaria de fileteado", "Operador", "Mañana", "2021-08-20", "Activo", "3002223344", "maria@planta.com", 2, 2),
        ("Juan Martinez", "34567890", "Operario de costura recta", "Operador", "Mañana", "2020-01-10", "Activo", "3003334455", "juan@planta.com", 4, 1),
        ("Laura Ramirez", "45678901", "Operaria de ribete y prensa", "Operador", "Mañana", "2023-06-01", "Activo", "3004445566", "laura@planta.com", 3, 6),
        ("Pedro Sanchez", "56789012", "Operario de corte", "Operador", "Mañana", "2022-11-15", "Activo", "3005556677", "pedro@planta.com", 1, 8),
        ("Lucia Herrera", "67890123", "Operaria de bordado", "Operador", "Tarde", "2021-04-22", "Activo", "3006667788", "lucia@planta.com", 5, 3),
        ("Diego Torres", "78901234", "Jefe de línea de bordado", "Supervisor", "Tarde", "2019-09-05", "Activo", "3007778899", "diego@planta.com", None, None),
        ("Ana Lopez", "89012345", "Operaria de botonera y ojetes", "Operador", "Tarde", "2023-01-18", "Activo", "3008889900", "ana@planta.com", 6, 5),
        ("Miguel Castro", "90123456", "Mecánico de mantenimiento", "Operador", "Mañana", "2020-02-28", "Activo", "3009990011", "miguel@planta.com", 1, None),
        ("Isabel Moreno", "01234567", "Control de calidad", "Operador", "Tarde", "2022-05-12", "Activo", "3010001122", "isabel@planta.com", 6, 9),
        ("Roberto Jimenez", "11223344", "Operario de empaque", "Operador", "Tarde", "2021-10-30", "Activo", "3011112233", "roberto@planta.com", 6, 9),
        ("Carmen Delgado", "22334455", "Operaria de costura recta", "Operador", "Tarde", "2022-07-14", "Activo", "3012223344", "carmen@planta.com", 4, 1),
        ("Andres Pino", "33445566", "Operario de fileteado", "Operador", "Mañana", "2023-02-18", "Activo", "3013334455", "andres@planta.com", 2, 2),
        ("Sofia Vargas", "44556677", "Jefe de línea de terminado", "Supervisor", "Tarde", "2019-12-08", "Activo", "3014445566", "sofia@planta.com", None, None),
        ("Admin Sistema", "99999999", "Administrador de plataforma", "Admin", "Mañana", "2020-01-01", "Activo", "3015556677", "admin@planta.com", None, None),
    ]
    cur.executemany("INSERT INTO Empleados (nombre, numero_documento, cargo, rol, turno, fecha_ingreso, estado, telefono, email, modulo_asignado, id_maquina) VALUES (?,?,?,?,?,?,?,?,?,?,?)", emp)

def usuarios(conn):
    cur = conn.cursor()
    cur.execute("SELECT id FROM Empleados WHERE rol='Supervisor' ORDER BY nombre")
    sups = [r[0] for r in cur.fetchall()]
    def crear(nombre, rol, id_emp):
        cur.execute("INSERT INTO Usuario (nombre_usuario, password, rol, id_empleado) VALUES (?,?,?,?)",
                    (nombre, '1234', rol, id_emp))
        return cur.lastrowid
    if len(sups) >= 3:
        carlos_id = crear('carlos', 'Supervisor', sups[0])
        diego_id = crear('diego', 'Supervisor', sups[1])
        sofia_id = crear('sofia', 'Supervisor', sups[2])
    elif len(sups) >= 2:
        carlos_id = crear('carlos', 'Supervisor', sups[0])
        diego_id = crear('diego', 'Supervisor', sups[1])
        sofia_id = carlos_id
    else:
        carlos_id = crear('carlos', 'Supervisor', sups[0])
        diego_id = carlos_id
        sofia_id = carlos_id
    # operario: usar el primer empleado que no sea supervisor
    cur.execute("SELECT id FROM Empleados WHERE rol != 'Supervisor' ORDER BY nombre LIMIT 1")
    emp_op = cur.fetchone()[0]
    cur.execute("INSERT INTO Usuario (nombre_usuario, password, rol, id_empleado) VALUES ('operario','1234','Operador', ?)", (emp_op,))

    # admin: controla la modalidad de registro a nivel plataforma
    cur.execute("SELECT id FROM Empleados WHERE rol='Admin' LIMIT 1")
    admin_emp = cur.fetchone()
    if admin_emp:
        crear('admin', 'Admin', admin_emp[0])

    # Módulos a supervisar = líneas de acceso del usuario (mismo concepto que antes)
    # carlos (línea 4 - ensamble) supervisa 2,3,4,5,6 ; diego (5) ; sofia (6)
    for m in [2,3,4,5,6]: cur.execute("INSERT INTO AsignacionUsuarioLinea (id_usuario, id_modulo) VALUES (?,?)", (carlos_id, m))
    cur.execute("INSERT INTO AsignacionUsuarioLinea (id_usuario, id_modulo) VALUES (?,?)", (diego_id, 5))
    cur.execute("INSERT INTO AsignacionUsuarioLinea (id_usuario, id_modulo) VALUES (?,?)", (sofia_id, 6))

def actividades_y_referencia(conn):
    cur = conn.cursor()
    # Diagrama de actividades lógico para Snapback Pro 6P (con precedencias coherentes)
    seq = [
        # (letra, nombre_operacion, id_maquina, id_seccion, predecesoras)
        ("A", "Corte de paneles (6 piezas) y forro", 8, 1, "N/A"),
        ("B", "Fileteado de bordes de paneles", 2, 1, "A"),
        ("C", "Ensamble de paneles de corona", 1, 1, "B"),
        ("D", "Aplicación de entretela a panel frontal", 8, 1, "A"),
        ("E", "Corte y armado de visera con entretela", 8, 2, "N/A"),
        ("F", "Ribeteo y moldeado de visera", 6, 2, "E"),
        ("G", "Prensado térmico de visera", 7, 2, "F"),
        ("H", "Unión de visera a corona (pega contorno)", 1, 3, "C,G"),
        ("I", "Colocación de banda interior (sweatband)", 1, 3, "H"),
        ("J", "Fileteado de unión corona-visera", 2, 3, "I"),
        ("K", "Bordado de logo frontal (hasta 6 colores)", 3, 6, "C"),
        ("L", "Colocación de ojetes de ventilación (4)", 4, 5, "J"),
        ("M", "Colocación de botón superior de metal", 5, 5, "J"),
        ("N", "Colocación de cierre trasero snapback", 5, 4, "J"),
        ("O", "Prensado y moldeado final de la gorra", 7, 5, "K,L,M,N"),
        ("P", "Control de calidad y etiquetado", 9, 5, "O"),
        ("Q", "Empaque final en bolsa", 9, 5, "P"),
    ]
    # insertar operaciones
    for letra, nombre, maq, sec, pred in seq:
        cur.execute("INSERT INTO Operacion (nombre_operacion, tiempo_segundos, id_maquina, id_seccion) VALUES (?,?,?,?)",
                    (nombre, random.randint(15, 55), maq, sec))
        op_id = cur.lastrowid
        if letra == 'A':
            ref_id = None
    # referencia
    cur.execute("SELECT id FROM Operacion ORDER BY id")
    # Insertar operaciones con tiempos más realistas ya cargados para mapear
    # Re-creamos limpiando y cargando tiempos fijos
    cur.execute("DELETE FROM Operacion")
    cur.execute("DELETE FROM sqlite_sequence WHERE name='Operacion'")
    tiempos = {
        "A": 38, "B": 30, "C": 48, "D": 22, "E": 35, "F": 42, "G": 28,
        "H": 52, "I": 30, "J": 26, "K": 65, "L": 18, "M": 12, "N": 28,
        "O": 25, "P": 20, "Q": 12
    }
    ops = {}
    for letra, nombre, maq, sec, pred in seq:
        cur.execute("INSERT INTO Operacion (nombre_operacion, tiempo_segundos, id_maquina, id_seccion) VALUES (?,?,?,?)",
                    (nombre, tiempos[letra], maq, sec))
        ops[letra] = cur.lastrowid

    cur.execute("""INSERT INTO ReferenciaProducto (nombre_referencia, especificaciones)
        VALUES ('Gorra Snapback Pro 6 Paneles',
                'Gorra snapback 6 paneles con forro, visera plana con entrete y prensado térmico 90°, 4 ojetes de latón, bordado frontal hasta 6 colores, botón metálico superior y cierre trasero con broche snapback. Tela poliéster 300D, banda interior sweatband.')""")
    ref_id = cur.lastrowid

    # materiales BOM
    cur.execute("SELECT id, nombre FROM Materiales")
    mats = {m[1]: m[0] for m in cur.fetchall()}
    bom = [
        ("Tela poliéster 300D", 0.32, 5),
        ("Malla de ventilación", 0.15, 3),
        ("Entretela termo adhesiva", 0.22, 4),
        ("Cinta sweatband 1.5\"", 0.30, 2),
        ("Cinta de refuerzo", 0.10, 0),
        ("Cierre snapback (broche)", 1, 0),
        ("Botón superior de metal", 1, 0),
        ("Ojete de latón", 4, 0),
        ("Hilo de poliéster", 0.08, 0),
        ("Etiqueta de talla y marca", 1, 0),
        ("Bolsa de empaque", 1, 0),
    ]
    for nombre, cant, merma in bom:
        cur.execute("INSERT INTO ReferenciaMaterial (id_referencia, id_material, cantidad_por_unidad, merma_porcentaje) VALUES (?,?,?,?)",
                    (ref_id, mats[nombre], cant, merma))

    # Detalle de secuencia
    for letra, nombre, maq, sec, pred in seq:
        cur.execute("INSERT INTO ReferenciaDetalle (id_referencia, id_operacion, letra_secuencia, predecesoras, orden_fila) VALUES (?,?,?,?,?)",
                    (ref_id, ops[letra], letra, pred, "ABCDEFGHIJKLMNOPQ".index(letra)+1))

    return ref_id

def ordenes_agosto(conn, ref_id):
    cur = conn.cursor()
    ordenes = [
        ("LOTE-AGO-001", 2400, "Abierta", "2026-08-03"),
        ("LOTE-AGO-002", 1800, "Abierta", "2026-08-12"),
        ("LOTE-AGO-003", 1500, "Abierta", "2026-08-21"),
    ]
    ids = []
    for nombre, cant, estado, fec in ordenes:
        cur.execute("INSERT INTO OrdenProduccion (id_referencia, nombre_orden, cantidad_lote, estado, fecha_creacion) VALUES (?,?,?,?,?)",
                    (ref_id, nombre, cant, estado, fec))
        oid = cur.lastrowid
        ids.append(oid)
        # asignar a líneas según el lote
        cur.execute("INSERT INTO AsignacionModulo (id_orden, id_modulo, cantidad_asignada) VALUES (?,?,?)", (oid, 1, int(cant*0.25)))
        cur.execute("INSERT INTO AsignacionModulo (id_orden, id_modulo, cantidad_asignada) VALUES (?,?,?)", (oid, 2, int(cant*0.30)))
        cur.execute("INSERT INTO AsignacionModulo (id_orden, id_modulo, cantidad_asignada) VALUES (?,?,?)", (oid, 4, int(cant*0.35)))
        cur.execute("INSERT INTO AsignacionModulo (id_orden, id_modulo, cantidad_asignada) VALUES (?,?,?)", (oid, 5, int(cant*0.05)))
        cur.execute("INSERT INTO AsignacionModulo (id_orden, id_modulo, cantidad_asignada) VALUES (?,?,?)", (oid, 3, int(cant*0.05)))
    return ids

def simular_agosto(conn, ref_id, orden_ids):
    """Genera registros de producción diarios de agosto (1 al 31) por actividad con hora, paradas y defectos."""
    cur = conn.cursor()
    cur.execute("SELECT id, nombre_operacion FROM Operacion ORDER BY id")
    opciones = cur.fetchall()  # (op_id, nombre)
    op_ids = [o[0] for o in opciones]

    cur.execute("SELECT id, tiempo_segundos FROM ParadasProgramadas")
    paradas_prog = cur.fetchall()
    ning = [p for p in paradas_prog if p[1] == 0][0]
    reales = [p for p in paradas_prog if p[1] > 0]
    cur.execute("SELECT id FROM CausaParada WHERE nombre != 'Otro'")
    causas_np = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id FROM Usuario WHERE nombre_usuario IN ('carlos','diego','sofia')")
    usuarios = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT id, nombre FROM ModuloConfeccion")
    modulos = cur.fetchall()

    # velocidad por operación según la línea
    # línea por operación: 1:corte(A,D,E), 2:filete/recta(B,C,I,J), 3:visera(F,G), 4:ensamble(H), 5:bordado(K), 6:acabados(L,M,N,O,P,Q)
    linea_op = {
        op_ids[0]: 1, op_ids[1]: 2, op_ids[2]: 2, op_ids[3]: 1, op_ids[4]: 1,
        op_ids[5]: 3, op_ids[6]: 3, op_ids[7]: 4, op_ids[8]: 4, op_ids[9]: 2,
        op_ids[10]: 5, op_ids[11]: 6, op_ids[12]: 6, op_ids[13]: 6, op_ids[14]: 6,
        op_ids[15]: 6, op_ids[16]: 6,
    }

    random.seed(42)
    registros = []
    paradas_reg = []
    producido_acum = {oid: {op: 0 for op in op_ids} for oid in orden_ids}

    # días hábiles de agosto (lun-vie)
    dias = []
    for d in range(1, 32):
        try:
            fd = date(2026, 8, d)
        except ValueError:
            continue
        if fd.weekday() < 5:
            dias.append(fd)

    for dia in dias:
        # qué órdenes están activas ese día por su fecha de inicio
        activas = [oid for oid in orden_ids]
        # 1-11 ago: solo lote 1; 12-20: lote1(lento)+lote2; 21+: los 3
        d = dia.day
        if d >= 21:
            act = [orden_ids[0], orden_ids[1], orden_ids[2]]
        elif d >= 12:
            act = [orden_ids[0], orden_ids[1]]
        else:
            act = [orden_ids[0]]
        for oid in act:
            meta_orden = 100 if oid == orden_ids[0] else (60 if oid == orden_ids[1] else 80)
            # producción por actividad en el día (cercano a meta pero con variación)
            for op in op_ids:
                # eficiencia por actividad: primeras van más rápido, avanzadas más lento
                idx = op_ids.index(op)
                eficiencia = random.uniform(0.75, 1.05)
                cantidad = int(meta_orden * eficiencia * random.uniform(0.75, 1.0))
                cantidad = max(0, cantidad)
                defectuosas = int(cantidad * random.uniform(0.005, 0.04))

                # Sin hora operativa: un solo registro por actividad (marca temporal automática)
                cant_h = cantidad
                def_h = max(0, defectuosas)
                if cant_h <= 0:
                    continue
                modulo_sel = [m for m in modulos if m[0] == linea_op[op]]
                mod_id = modulo_sel[0][0] if modulo_sel else modulos[0][0]
                usuario_sel = usuarios[random.randint(0, len(usuarios)-1)]

                # paradas: programada (desayuno 60%) o causa np (30%) o ninguna
                paradas = []
                if random.random() < 0.55:
                    pp = reales[random.randint(0, len(reales)-1)]
                    paradas.append({"id_pp": pp[0], "causa": None, "tiempo": pp[1]})
                if random.random() < 0.30:
                    cp = causas_np[random.randint(0, len(causas_np)-1)]
                    paradas.append({"id_pp": None, "causa": cp, "tiempo": random.randint(300, 1200)})

                registros.append((
                    dia.isoformat(), mod_id, oid, op, 1.0,
                    random.randint(4, 8), cant_h, def_h, "", usuario_sel,
                ))
                reg_idx = len(registros) - 1  # índice 0-based en la lista
                for par in paradas:
                    paradas_reg.append((reg_idx, par["id_pp"], par["causa"], par["tiempo"]))

    cur.executemany("""INSERT INTO RegistroProduccion
        (fecha, id_modulo, id_orden, id_operacion, porcion_tiempo,
         cantidad_operarios, cantidad_producida, cantidad_defectuosa, observaciones, id_usuario)
        VALUES (?,?,?,?,?,?,?,?,?,?)""", registros)
    # paradas: necesitamos mapear registros recién insertados con su id real.
    # Como INSERT no nos dio los ids, re-leemos en orden de inserción.
    cur.execute("SELECT id FROM RegistroProduccion ORDER BY id")
    todos_ids = [r[0] for r in cur.fetchall()]
    for i, (rid, pp, causa, tiempo) in enumerate(paradas_reg):
        real_id = todos_ids[i]
        cur.execute("INSERT INTO ParadaRegistro (id_registro, id_parada_programada, id_causa, tiempo_segundos) VALUES (?,?,?,?)",
                    (real_id, pp, causa, tiempo))
    conn.commit()
    return len(registros)

def main():
    # Eliminar tablas de registro si existen con schema viejo (id_hora NOT NULL)
    # para que inicializar_base_de_datos las recree con id_hora nullable.
    conn_pre = con()
    for t in ["ParadaRegistro", "RegistroProduccion", "HorasProduccion"]:
        conn_pre.execute(f"DROP TABLE IF EXISTS {t}")
    conn_pre.commit()
    conn_pre.close()

    inicializar_base_de_datos()
    conn = con()
    try:
        limpiar(conn)
        lineas_reales(conn)
        maquinas_reales(conn)
        secciones_gorra(conn)
        horas(conn)
        paradas(conn)
        causas(conn)
        materiales(conn)
        empleados(conn)
        usuarios(conn)
        ref_id = actividades_y_referencia(conn)
        orden_ids = ordenes_agosto(conn, ref_id)
        conn.commit()
        n = simular_agosto(conn, ref_id, orden_ids)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM RegistroProduccion")
        print(f"Referencia: Gorra Snapback Pro 6 Paneles (id={ref_id})")
        print(f"3 órdenes de agosto: {orden_ids}")
        print(f"Registros de producción simulados (agosto): {n}")
        print("Simulación completa.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()