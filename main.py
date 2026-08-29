from flask import Flask, request, jsonify, send_from_directory
from database import (
    inicializar_base_de_datos, 
    obtener_maquinaria, 
    insertar_maquina, 
    obtener_secciones, 
    insertar_seccion,
    obtener_operaciones_detalladas,
    insertar_operacion,
    actualizar_operacion,
    eliminar_operacion,
    crear_referencia,
    obtener_referencias,
    eliminar_referencia,
    actualizar_referencia,
    actualizar_foto_referencia,
    duplicar_referencia,
    agregar_detalle_referencia,
    obtener_horas,
    insertar_hora,
    obtener_paradas,
    insertar_parada,
    obtener_asignaciones,
    asignar_referencia_modulo,
    obtener_disponibilidad,
    eliminar_asignacion,
    actualizar_asignacion,
    obtener_ordenes_disponibles,
    obtener_detalles_referencia,
    eliminar_detalle,
    obtener_ordenes,
    crear_orden,
    actualizar_orden,
    eliminar_orden,
    obtener_materiales,
    insertar_material,
    actualizar_material,
    eliminar_material,
    obtener_materiales_referencia,
    agregar_material_referencia,
    eliminar_material_referencia,
    calcular_materiales_orden,
    obtener_modulos,
    insertar_modulo,
    obtener_referencias_por_modulo,
    insertar_control_hora,
    obtener_controles_hoy,
    eliminar_control_hora,
    actualizar_control_hora,
    obtener_controles_rango,
    obtener_tiempo_ciclo_referencia,
    verificar_login,
    obtener_usuarios,
    crear_usuario,
    actualizar_usuario,
    eliminar_usuario,
    obtener_lineas_usuario,
    asignar_lineas_usuario,
    obtener_causas_parada,
    insertar_causa_parada,
    eliminar_causa_parada,
    obtener_registros_dia,
    resumen_registros_hora,
    insertar_registro_produccion,
    eliminar_registro_produccion,
    obtener_registros_rango,
    reporte_progreso_orden,
    obtener_cumplimiento_orden,
    obtener_empleados,
    obtener_empleado,
    insertar_empleado,
    actualizar_empleado,
    eliminar_empleado
)
from engine import calcular_balanceo_linea
import os

app = Flask(__name__)
PORT = 8000
DIRECTORY = os.getcwd()



# --- SIMULADOR DE BALANCEO ---

@app.route('/api/balanceo/calcular', methods=['POST'])
def calcular_balanceo():
    datos = request.json
    if not datos or 'id_referencia' not in datos or 'num_operarios' not in datos:
        return jsonify({"error": "Faltan datos (id_referencia, num_operarios)"}), 400
    
    id_ref = int(datos['id_referencia'])
    num_ops = int(datos['num_operarios'])
    
    # Obtener operaciones de la referencia
    # Reutilizamos la función existente, que devuelve una lista de diccionarios
    # Campos que devuelve: id, letra, nombre_operacion, maquina, tiempo, predecesoras, orden, id_operacion
    detalles = obtener_detalles_referencia(id_ref)
    
    if not detalles:
        return jsonify({"error": "La referencia no tiene operaciones asignadas"}), 400
    
    # Adaptar claves para el engine si es necesario (maquina vs maquina_asignada)
    # El engine espera keys: 'tiempo', 'maquina', 'predecesoras', 'letra', 'nombre_operacion'
    # obtener_detalles_referencia ya devuelve eso (maquina es el nombre, ej: "PLANA")
    
    # Mapear para uniformidad
    operaciones_sim = []
    for d in detalles:
        operaciones_sim.append({
            "id": d['id'],
            "letra": d['letra'],
            "nombre": d['nombre_operacion'],
            "tiempo": d['tiempo'],           # int
            "maquina": d['maquina'],         # str nombre
            "predecesoras": d['predecesoras']
        })
        
    resultado = calcular_balanceo_linea(operaciones_sim, num_ops)
    
    if 'error' in resultado:
        return jsonify({"error": resultado['error']}), 400
    
    return jsonify(resultado)


@app.route('/')
def index():
    return send_from_directory(DIRECTORY, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(DIRECTORY, path)

# --- API ENDPOINTS ---

@app.route('/api/maquinaria', methods=['GET'])
def get_maquinaria():
    return jsonify(obtener_maquinaria())

@app.route('/api/maquinaria', methods=['POST'])
def add_maquina():
    datos = request.json
    if not datos or 'nombre' not in datos:
        return jsonify({"error": "Nombre requerido"}), 400
    insertar_maquina(
        datos['nombre'],
        datos.get('descripcion'),
        datos.get('velocidad_tipica'),
        datos.get('estado', 'Activa'),
        datos.get('id_modulo')
    )
    return jsonify({"mensaje": "Máquina guardada con éxito"}), 201

@app.route('/api/secciones', methods=['GET'])
def get_secciones():
    return jsonify(obtener_secciones())

@app.route('/api/secciones', methods=['POST'])
def add_seccion():
    datos = request.json
    if not datos or 'nombre' not in datos:
        return jsonify({"error": "Nombre requerido"}), 400
    insertar_seccion(
        datos['nombre'],
        datos.get('descripcion'),
        datos.get('orden_proceso')
    )
    return jsonify({"mensaje": "Sección guardada con éxito"}), 201

# --- NUEVO: MÓDULOS ---
@app.route('/api/modulos', methods=['GET'])
def get_modulos():
    return jsonify(obtener_modulos())

@app.route('/api/modulos', methods=['POST'])
def add_modulos():
    datos = request.json
    if not datos or 'nombre' not in datos:
        return jsonify({"error": "Falta nombre"}), 400
    insertar_modulo(
        datos['nombre'],
        datos.get('capacidad_maxima'),
        datos.get('ubicacion'),
        datos.get('supervisor'),
        datos.get('estado', 'Activo')
    )
    return jsonify({"mensaje": "Módulo guardado con éxito"}), 201

# --- NUEVO: HORAS ---
@app.route('/api/horas', methods=['GET'])
def get_horas():
    return jsonify(obtener_horas())

@app.route('/api/horas', methods=['POST'])
def add_horas():
    datos = request.json
    if not datos or 'nombre' not in datos:
        return jsonify({"error": "Falta nombre"}), 400
    insertar_hora(
        datos['nombre'],
        datos.get('hora_inicio'),
        datos.get('hora_fin'),
        datos.get('turno')
    )
    return jsonify({"mensaje": "Hora guardada con éxito"}), 201

# --- NUEVO: PARADAS ---
@app.route('/api/paradas', methods=['GET'])
def get_paradas():
    return jsonify(obtener_paradas())

@app.route('/api/paradas', methods=['POST'])
def add_parada():
    datos = request.json
    if not datos or 'nombre' not in datos or 'tiempo' not in datos:
        return jsonify({"error": "Faltan datos"}), 400
    insertar_parada(
        datos['nombre'],
        int(datos['tiempo']),
        datos.get('tipo', 'Opcional'),
        datos.get('frecuencia', 'Diaria')
    )
    return jsonify({"mensaje": "Parada guardada con éxito"}), 201

# --- OPERACIONES ---

@app.route('/api/operaciones', methods=['GET'])
def get_operaciones():
    return jsonify(obtener_operaciones_detalladas())

@app.route('/api/operaciones', methods=['POST'])
def add_operacion():
    datos = request.json
    required = ['nombre', 'tiempo', 'id_maquina', 'id_seccion']
    if not all(k in datos for k in required):
        return jsonify({"error": "Faltan datos requeridos"}), 400
    
    insertar_operacion(
        datos['nombre'], 
        int(datos['tiempo']), 
        int(datos['id_maquina']), 
        int(datos['id_seccion'])
    )
    return jsonify({"mensaje": "Operación guardada con éxito"}), 201

@app.route('/api/operaciones/<int:id_operacion>', methods=['PUT'])
def update_operacion(id_operacion):
    datos = request.json
    required = ['nombre', 'tiempo', 'id_maquina', 'id_seccion']
    if not all(k in datos for k in required):
        return jsonify({"error": "Faltan datos requeridos"}), 400
    
    actualizar_operacion(
        id_operacion,
        datos['nombre'],
        int(datos['tiempo']),
        int(datos['id_maquina']),
        int(datos['id_seccion'])
    )
    return jsonify({"mensaje": "Operación actualizada"}), 200

@app.route('/api/operaciones/<int:id_operacion>', methods=['DELETE'])
def delete_operacion(id_operacion):
    eliminar_operacion(id_operacion)
    return jsonify({"mensaje": "Operación eliminada"}), 200

# --- REFERENCIAS ---

@app.route('/api/referencias', methods=['GET'])
def get_referencias():
    return jsonify(obtener_referencias())

@app.route('/api/referencias', methods=['POST'])
def add_referencia():
    datos = request.json
    if not datos or 'nombre' not in datos:
        return jsonify({"error": "Nombre requerido"}), 400
    
    id_ref = crear_referencia(
        datos['nombre'],
        datos.get('especificaciones'),
        datos.get('foto')
    )
    return jsonify({"id": id_ref, "mensaje": "Referencia creada"}), 201

@app.route('/api/referencias/<int:id_ref>', methods=['PUT'])
def update_referencia(id_ref):
    datos = request.json
    if not datos or 'nombre' not in datos:
        return jsonify({"error": "Nombre requerido"}), 400
    
    actualizar_referencia(id_ref, datos['nombre'], datos.get('especificaciones'), datos.get('foto'))
    return jsonify({"mensaje": "Referencia actualizada"}), 200

@app.route('/api/referencias/<int:id_ref>/foto', methods=['POST'])
def upload_foto_referencia(id_ref):
    if 'foto' not in request.files:
        return jsonify({"error": "No se recibió archivo"}), 400
    archivo = request.files['foto']
    if archivo.filename == '':
        return jsonify({"error": "Archivo vacío"}), 400

    from werkzeug.utils import secure_filename
    carpeta = os.path.join(os.getcwd(), 'uploads')
    os.makedirs(carpeta, exist_ok=True)
    nombre_seguro = secure_filename(archivo.filename)
    ruta_guardar = os.path.join(carpeta, f"ref_{id_ref}_{nombre_seguro}")
    archivo.save(ruta_guardar)

    ruta_web = f"/uploads/ref_{id_ref}_{nombre_seguro}"
    actualizar_foto_referencia(id_ref, ruta_web)
    return jsonify({"mensaje": "Foto subida", "foto": ruta_web}), 200

@app.route('/api/referencias/<int:id_ref>/duplicar', methods=['POST'])
def duplicate_referencia_endpoint(id_ref):
    datos = request.json
    nuevo_nombre = datos.get('nombre')
    if not nuevo_nombre:
        return jsonify({"error": "Nombre nuevo requerido"}), 400
        
    nuevo_id = duplicar_referencia(id_ref, nuevo_nombre)
    if not nuevo_id:
        return jsonify({"error": "Referencia original no encontrada"}), 404
        
    return jsonify({"id": nuevo_id, "mensaje": "Referencia duplicada"}), 201

# --- ORDENES DE PRODUCCIÓN (LOTES) ---

@app.route('/api/ordenes', methods=['GET'])
def get_ordenes():
    return jsonify(obtener_ordenes())

@app.route('/api/ordenes', methods=['POST'])
def add_orden():
    datos = request.json
    if not datos or not datos.get('id_referencia') or not datos.get('cantidad_lote'):
        return jsonify({"error": "Faltan datos (id_referencia, cantidad_lote)"}), 400
    if not datos.get('nombre_orden'):
        return jsonify({"error": "Falta nombre_orden"}), 400

    id_orden = crear_orden(
        int(datos['id_referencia']),
        datos['nombre_orden'],
        int(datos['cantidad_lote'])
    )
    return jsonify({"id": id_orden, "mensaje": "Orden creada"}), 201

@app.route('/api/ordenes/<int:id_orden>', methods=['PUT'])
def update_orden_endpoint(id_orden):
    datos = request.json
    res = actualizar_orden(
        id_orden,
        int(datos['cantidad_lote']) if datos.get('cantidad_lote') else None,
        datos.get('estado')
    )
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.route('/api/ordenes/<int:id_orden>', methods=['DELETE'])
def delete_orden_endpoint(id_orden):
    return jsonify(eliminar_orden(id_orden))

# --- MATERIALES (BOM) ---

@app.route('/api/materiales', methods=['GET'])
def get_materiales():
    return jsonify(obtener_materiales())

@app.route('/api/materiales', methods=['POST'])
def add_material():
    datos = request.json
    if not datos or 'nombre' not in datos:
        return jsonify({"error": "Nombre requerido"}), 400
    res = insertar_material(
        datos['nombre'],
        datos.get('unidad'),
        datos.get('costo_unitario'),
        datos.get('proveedor'),
        datos.get('descripcion')
    )
    return jsonify(res), 201

@app.route('/api/materiales/<int:id_material>', methods=['PUT'])
def update_material_endpoint(id_material):
    datos = request.json
    if not datos or 'nombre' not in datos:
        return jsonify({"error": "Nombre requerido"}), 400
    res = actualizar_material(
        id_material,
        datos['nombre'],
        datos.get('unidad'),
        datos.get('costo_unitario'),
        datos.get('proveedor'),
        datos.get('descripcion')
    )
    return jsonify(res)

@app.route('/api/materiales/<int:id_material>', methods=['DELETE'])
def delete_material_endpoint(id_material):
    return jsonify(eliminar_material(id_material))

# Materiales por referencia (BOM)
@app.route('/api/referencias/<int:id_ref>/materiales', methods=['GET'])
def get_materiales_referencia(id_ref):
    return jsonify(obtener_materiales_referencia(id_ref))

@app.route('/api/referencias/<int:id_ref>/materiales', methods=['POST'])
def add_material_referencia(id_ref):
    datos = request.json
    required = ['id_material', 'cantidad_por_unidad']
    if not all(k in datos for k in required):
        return jsonify({"error": "Faltan datos (id_material, cantidad_por_unidad)"}), 400
    res = agregar_material_referencia(
        id_ref,
        int(datos['id_material']),
        float(datos['cantidad_por_unidad']),
        float(datos.get('merma_porcentaje', 0) or 0),
        datos.get('nota')
    )
    return jsonify(res), 201

@app.route('/api/materiales-referencia/<int:id_material_ref>', methods=['DELETE'])
def delete_material_referencia(id_material_ref):
    return jsonify(eliminar_material_referencia(id_material_ref))

# Cálculo de materiales para un lote
@app.route('/api/ordenes/<int:id_orden>/materiales', methods=['GET'])
def get_materiales_orden(id_orden):
    res = calcular_materiales_orden(id_orden)
    if not res:
        return jsonify({"error": "Orden no encontrada"}), 404
    return jsonify(res)

# Cumplimiento real de una orden (producción registrada vs lote)
@app.route('/api/ordenes/<int:id_orden>/cumplimiento', methods=['GET'])
def get_cumplimiento_orden(id_orden):
    res = obtener_cumplimiento_orden(id_orden)
    if not res:
        return jsonify({"error": "Orden no encontrada"}), 404
    return jsonify(res)

# --- ASIGNACIÓN DE REFERENCIAS ---

@app.route('/api/asignaciones', methods=['GET'])
def get_asignaciones():
    return jsonify(obtener_asignaciones())

@app.route('/api/asignaciones', methods=['POST'])
def crear_asignacion():
    datos = request.json
    id_orden = datos.get('id_orden')
    id_mod = datos.get('id_modulo')
    cantidad = datos.get('cantidad')
    
    if not id_orden or not id_mod or not cantidad:
        return jsonify({"error": "Faltan datos"}), 400

    try:
        cantidad = int(cantidad)
    except:
        return jsonify({"error": "Cantidad inválida"}), 400

    res = asignar_referencia_modulo(id_orden, id_mod, cantidad)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res), 201

@app.route('/api/ordenes/<int:id_orden>/disponibilidad', methods=['GET'])
def get_disponibilidad(id_orden):
    res = obtener_disponibilidad(id_orden)
    if not res:
        return jsonify({"error": "Orden no encontrada"}), 404
    return jsonify(res)

@app.route('/api/asignaciones/<int:id_asignacion>', methods=['DELETE'])
def delete_asignacion(id_asignacion):
    eliminar_asignacion(id_asignacion)
    return jsonify({"mensaje": "Eliminado"}), 200

@app.route('/api/ordenes-disponibles', methods=['GET'])
def get_ordenes_disponibles():
    return jsonify(obtener_ordenes_disponibles())

@app.route('/api/asignaciones/<int:id_asignacion>', methods=['PUT'])
def update_asignacion(id_asignacion):
    datos = request.json
    nueva_cantidad = datos.get('cantidad')
    if not nueva_cantidad:
        return jsonify({"error": "Falta cantidad"}), 400
        
    try:
        nueva_cantidad = int(nueva_cantidad)
    except:
        return jsonify({"error": "Cantidad inválida"}), 400

    res = actualizar_asignacion(id_asignacion, nueva_cantidad)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.route('/api/referencias/<int:id_ref>', methods=['DELETE'])
def delete_referencia(id_ref):
    res = eliminar_referencia(id_ref)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.route('/api/referencias/<int:id_ref>/detalles', methods=['GET'])
def get_referencia_detalles(id_ref):
    return jsonify(obtener_detalles_referencia(id_ref))

@app.route('/api/referencias/<int:id_ref>/detalles', methods=['POST'])
def add_referencia_detalle(id_ref):
    datos = request.json
    required = ['id_operacion', 'letra', 'predecesoras', 'orden']
    if not all(k in datos for k in required):
        return jsonify({"error": "Faltan datos"}), 400

    agregar_detalle_referencia(
        id_ref,
        int(datos['id_operacion']),
        datos['letra'],
        datos['predecesoras'],
        int(datos['orden'])
    )
    return jsonify({"mensaje": "Detalle agregado"}), 201

@app.route('/api/detalles/<int:id_detalle>', methods=['DELETE'])
def delete_referencia_detalle(id_detalle):
    eliminar_detalle(id_detalle)
    return jsonify({"mensaje": "Detalle eliminado"}), 200

# --- ENDPOINTS CONTROL HORA A HORA ---

@app.route('/api/modulos/<int:id_mod>/referencias-asignadas', methods=['GET'])
def get_referencias_asignadas(id_mod):
    return jsonify(obtener_referencias_por_modulo(id_mod))

@app.route('/api/control-hora', methods=['POST'])
def save_control_hora():
    datos = request.json
    res = insertar_control_hora(datos)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res), 201

@app.route('/api/control-hora/hoy', methods=['GET'])
def get_control_hoy():
    fecha = request.args.get('fecha') # O se puede automatizar con date.today()
    if not fecha:
        from datetime import date
        fecha = date.today().isoformat()
    return jsonify(obtener_controles_hoy(fecha))

@app.route('/api/control-hora/<int:id_control>', methods=['DELETE'])
def delete_control_hora(id_control):
    eliminar_control_hora(id_control)
    return jsonify({"mensaje": "Registro eliminado"}), 200

@app.route('/api/control-hora/<int:id_control>', methods=['PUT'])
def update_control_hora(id_control):
    datos = request.json
    res = actualizar_control_hora(id_control, datos)
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

# --- REPORTE TABLERO DE EFICIENCIAS ---

@app.route('/api/reportes/eficiencia', methods=['GET'])
def get_reporte_eficiencia():
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    id_referencia = request.args.get('id_referencia', type=int)
    id_orden = request.args.get('id_orden', type=int)
    
    if not fecha_inicio or not fecha_fin:
        from datetime import date
        hoy = date.today().isoformat()
        fecha_inicio = fecha_inicio or hoy
        fecha_fin = fecha_fin or hoy

    controles = obtener_registros_rango(fecha_inicio, fecha_fin, id_orden)
    if id_referencia:
        controles = [c for c in controles if c['id_referencia'] == id_referencia]
    
    # 1. Identificar módulos y horas presentes
    modulos_set = set()
    horas_dict = {} # {hora_nombre: {modulo_nombre: {cantidad:0, meta:0, defectos:0}}}
    
    # Cache para tiempos de ciclo
    tc_cache = {}

    for c in controles:
        id_ref = c['id_referencia']
        if id_ref not in tc_cache:
            tc_cache[id_ref] = obtener_tiempo_ciclo_referencia(id_ref)
        
        tc = tc_cache[id_ref]
        num_op = c['cantidad_operarios'] or 0
        porcion = c['porcion_tiempo'] or 1.0
        p_total = c.get('tiempo_total_parada') or 0
        # Paradas programadas afectan a todos los operarios; no programadas solo al módulo.
        # Como no distinguimos por tipo aquí, usamos tiempo total como no programada para no penalizar doble.
        # Fórmula: TD = (Num_Op * 3600 * Porcion) - Paradas
        td = (num_op * 3600 * porcion) - p_total
        meta = int(td / tc) if tc > 0 else 0
        
        hora = c['hora']
        modulo = c['modulo']
        modulos_set.add(modulo)
        
        if hora not in horas_dict:
            horas_dict[hora] = {}
        
        if modulo not in horas_dict[hora]:
            horas_dict[hora][modulo] = {"cantidad": 0, "meta": 0, "defectos": 0}
            
        horas_dict[hora][modulo]["cantidad"] += c['cantidad']
        horas_dict[hora][modulo]["meta"] += meta
        horas_dict[hora][modulo]["defectos"] += c.get('cantidad_defectuosa') or 0

    # 2. Estructurar respuesta para el frontend
    modulos_lista = sorted(list(modulos_set))
    reporte = []
    
    for hora_nombre in sorted(horas_dict.keys(), key=lambda x: int(x.split()[1]) if len(x.split()) > 1 and x.split()[1].isdigit() else 99):
        datos_modulos = {}
        total_planta_cantidad = 0
        total_planta_meta = 0
        total_planta_defectos = 0
        
        for mod in modulos_lista:
            val = horas_dict[hora_nombre].get(mod, {"cantidad": 0, "meta": 0, "defectos": 0})
            cantidad = val["cantidad"]
            meta = val["meta"]
            defectos = val["defectos"]
            eficiencia = round((cantidad / meta * 100), 1) if meta > 0 else 0
            calidad = round(((cantidad - defectos) / cantidad * 100), 1) if cantidad > 0 else 0
            
            datos_modulos[mod] = {
                "cantidad": cantidad,
                "meta": meta,
                "eficiencia": eficiencia,
                "defectos": defectos,
                "calidad": calidad
            }
            total_planta_cantidad += cantidad
            total_planta_meta += meta
            total_planta_defectos += defectos
            
        eficiencia_total = round((total_planta_cantidad / total_planta_meta * 100), 1) if total_planta_meta > 0 else 0
        calidad_total = round(((total_planta_cantidad - total_planta_defectos) / total_planta_cantidad * 100), 1) if total_planta_cantidad > 0 else 0
        
        reporte.append({
            "hora": hora_nombre,
            "datos_modulos": datos_modulos,
            "total_planta": {
                "cantidad": total_planta_cantidad,
                "meta": total_planta_meta,
                "eficiencia": eficiencia_total,
                "defectos": total_planta_defectos,
                "calidad": calidad_total
            }
        })
        
    return jsonify({
        "modulos": modulos_lista,
        "reporte": reporte
    })

# --- EMPLEADOS ---

@app.route('/api/empleados', methods=['GET'])
def get_empleados():
    return jsonify(obtener_empleados())

@app.route('/api/empleados/<int:id_empleado>', methods=['GET'])
def get_empleado(id_empleado):
    empleado = obtener_empleado(id_empleado)
    if not empleado:
        return jsonify({"error": "Empleado no encontrado"}), 404
    return jsonify(empleado)

@app.route('/api/empleados', methods=['POST'])
def add_empleado():
    datos = request.json
    if not datos or 'nombre' not in datos or 'numero_documento' not in datos or 'cargo' not in datos:
        return jsonify({"error": "Faltan datos requeridos (nombre, numero_documento, cargo)"}), 400
    
    res = insertar_empleado(
        datos['nombre'],
        datos['numero_documento'],
        datos['cargo'],
        datos.get('rol', 'Operador'),
        datos.get('turno'),
        datos.get('fecha_ingreso'),
        datos.get('estado', 'Activo'),
        datos.get('telefono'),
        datos.get('email'),
        datos.get('modulo_asignado'),
        datos.get('id_maquina'),
        [int(x) for x in (datos.get('id_modulos_supervisor') or [])]
    )
    
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res), 201

@app.route('/api/empleados/<int:id_empleado>', methods=['PUT'])
def update_empleado(id_empleado):
    datos = request.json
    if not datos or 'nombre' not in datos or 'numero_documento' not in datos or 'cargo' not in datos:
        return jsonify({"error": "Faltan datos requeridos (nombre, numero_documento, cargo)"}), 400
    
    res = actualizar_empleado(
        id_empleado,
        datos['nombre'],
        datos['numero_documento'],
        datos['cargo'],
        datos.get('rol', 'Operador'),
        datos.get('turno'),
        datos.get('fecha_ingreso'),
        datos.get('estado', 'Activo'),
        datos.get('telefono'),
        datos.get('email'),
        datos.get('modulo_asignado'),
        datos.get('id_maquina'),
        [int(x) for x in (datos.get('id_modulos_supervisor') or [])]
    )
    
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.route('/api/empleados/<int:id_empleado>', methods=['DELETE'])
def delete_empleado(id_empleado):
    res = eliminar_empleado(id_empleado)
    return jsonify(res)

# --- LOGIN ---

@app.route('/api/login', methods=['POST'])
def login():
    datos = request.json
    if not datos or not datos.get('nombre_usuario') or not datos.get('password'):
        return jsonify({"error": "Usuario y contraseña requeridos"}), 400
    usuario = verificar_login(datos['nombre_usuario'], datos['password'])
    if not usuario:
        return jsonify({"error": "Credenciales inválidas"}), 401
    return jsonify(usuario)

# --- USUARIOS ---

@app.route('/api/usuarios', methods=['GET'])
def get_usuarios():
    return jsonify(obtener_usuarios())

@app.route('/api/usuarios', methods=['POST'])
def add_usuario():
    datos = request.json
    required = ['nombre_usuario', 'password', 'rol', 'id_empleado']
    if not all(k in datos for k in required):
        return jsonify({"error": "Faltan datos requeridos"}), 400
    res = crear_usuario(datos['nombre_usuario'], datos['password'], datos['rol'], int(datos['id_empleado']))
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res), 201

@app.route('/api/usuarios/<int:id_usuario>', methods=['PUT'])
def update_usuario(id_usuario):
    datos = request.json
    required = ['nombre_usuario', 'password', 'rol', 'id_empleado']
    if not all(k in datos for k in required):
        return jsonify({"error": "Faltan datos requeridos"}), 400
    res = actualizar_usuario(id_usuario, datos['nombre_usuario'], datos['password'], datos['rol'], int(datos['id_empleado']))
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res)

@app.route('/api/usuarios/<int:id_usuario>', methods=['DELETE'])
def delete_usuario(id_usuario):
    return jsonify(eliminar_usuario(id_usuario))

@app.route('/api/usuarios/<int:id_usuario>/lineas', methods=['GET'])
def get_lineas_usuario(id_usuario):
    return jsonify(obtener_lineas_usuario(id_usuario))

@app.route('/api/usuarios/<int:id_usuario>/lineas', methods=['POST'])
def set_lineas_usuario(id_usuario):
    datos = request.json
    ids = [int(x) for x in datos.get('id_modulos', [])]
    return jsonify(asignar_lineas_usuario(id_usuario, ids))

# --- CAUSAS DE PARADA ---

@app.route('/api/causas-parada', methods=['GET'])
def get_causas_parada():
    return jsonify(obtener_causas_parada())

@app.route('/api/causas-parada', methods=['POST'])
def add_causa_parada():
    datos = request.json
    if not datos or not datos.get('nombre'):
        return jsonify({"error": "Nombre requerido"}), 400
    res = insertar_causa_parada(datos['nombre'])
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res), 201

@app.route('/api/causas-parada/<int:id_causa>', methods=['DELETE'])
def delete_causa_parada(id_causa):
    return jsonify(eliminar_causa_parada(id_causa))

# --- REGISTRO DE PRODUCCIÓN (NUEVO) ---

@app.route('/api/produccion/dia', methods=['GET'])
def get_produccion_dia():
    fecha = request.args.get('fecha')
    id_usuario = request.args.get('id_usuario', type=int)
    if not fecha:
        from datetime import date
        fecha = date.today().isoformat()
    return jsonify(obtener_registros_dia(fecha, id_usuario))

@app.route('/api/produccion/resumen', methods=['GET'])
def get_resumen_produccion():
    fecha = request.args.get('fecha')
    id_modulo = request.args.get('id_modulo', type=int)
    id_hora = request.args.get('id_hora', type=int)
    if not fecha or not id_modulo or not id_hora:
        return jsonify({"error": "Faltan parámetros"}), 400
    return jsonify(resumen_registros_hora(fecha, id_modulo, id_hora))

@app.route('/api/produccion', methods=['POST'])
def add_produccion():
    datos = request.json
    if not datos.get('fecha') or not datos.get('id_modulo') or not datos.get('id_hora') or not datos.get('id_orden'):
        return jsonify({"error": "Faltan datos requeridos"}), 400
    id_usuario = datos.get('id_usuario')
    if not id_usuario:
        return jsonify({"error": "Usuario no identificado"}), 401
    try:
        cantidad = int(datos['cantidad_producida'])
    except:
        return jsonify({"error": "Cantidad inválida"}), 400
    res = insertar_registro_produccion(datos, int(id_usuario))
    if "error" in res:
        return jsonify(res), 400
    return jsonify(res), 201

@app.route('/api/produccion/<int:id_registro>', methods=['DELETE'])
def delete_produccion(id_registro):
    return jsonify(eliminar_registro_produccion(id_registro))

@app.route('/api/progreso/<int:id_orden>', methods=['GET'])
def get_progreso_orden(id_orden):
    res = reporte_progreso_orden(id_orden)
    if not res:
        return jsonify({"error": "Orden no encontrada"}), 404
    return jsonify(res)

if __name__ == "__main__":
    inicializar_base_de_datos()
    app.run(port=PORT, debug=True)
