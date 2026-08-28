import math

def calcular_balanceo_linea(operaciones, num_operarios):
    """
    Calcula el balanceo de línea asignando operaciones a operarios.
    ENFOQUE: INTEGRIDAD CATEGÓRICA (ROLES DE MÁQUINA FIJOS).
    
    Args:
        operaciones (list): Lista de dicts con {id, letra, nombre, tiempo, maquina, predecesoras}
                            Ordenada por secuencia original.
        num_operarios (int): Número de operarios disponibles.
        
    Returns:
        dict: { 'kpis': {...}, 'operarios': [...] }
    """
    
    # Identificar si hay error de escasez antes de calcular
    # ---------------------------------------------------------
    # 1. FASE DE AGRUPAMIENTO Y DEMANDA (CLUSTERING)
    # ---------------------------------------------------------
    # Agrupar operaciones por tipo de máquina y calcular demanda
    maquinas_demanda = {}
    
    for op in operaciones:
        maq = op['maquina']
        if maq not in maquinas_demanda:
            maquinas_demanda[maq] = 0
        maquinas_demanda[maq] += op['tiempo']
        
    tipos_maquinas = list(maquinas_demanda.keys())
    num_tipos_maquinas = len(tipos_maquinas)
    
    # VALIDACIÓN
    if num_operarios < num_tipos_maquinas:
        return {
            "error": f"No es posible hacer la asignación: Se requieren al menos {num_tipos_maquinas} operarios para cubrir los {num_tipos_maquinas} tipos de máquinas (Plana, Fileteadora, etc). Tienes solo {num_operarios} operarios."
        }
        
    # Calcular Takt Time Teórico Global
    tiempo_total_prenda = sum(op['tiempo'] for op in operaciones)
    takt_time_teorico = tiempo_total_prenda / num_operarios if num_operarios > 0 else 0
    takt_time_teorico = round(takt_time_teorico, 2)

    # ---------------------------------------------------------
    # DEFINICIÓN DE ROLES (Común para ambos escenarios)
    # ---------------------------------------------------------
    # Crear estructura base de operarios con roles asignados
    operarios_base_roles = _asignar_roles(num_operarios, tipos_maquinas, maquinas_demanda)

    # ---------------------------------------------------------
    # EJECUCIÓN DE ESCENARIOS
    # ---------------------------------------------------------
    
    # Escenario A: Secuencial (Respetando Predecesoras)
    # Copiamos operarios base (deben ser copias profundas de la estructura básica)
    op_secuencial = [op.copy() for op in operarios_base_roles]
    for op in op_secuencial: op['tareas'] = [] # Reset tareas por seguridad
    
    res_secuencial = _ejecutar_asignacion(op_secuencial, operaciones, takt_time_teorico, ignorar_precedencia=False)

    # Escenario B: Eficiencia Máxima (Ignorando Predecesoras)
    op_eficiencia = [op.copy() for op in operarios_base_roles]
    for op in op_eficiencia: op['tareas'] = []
    
    res_eficiencia = _ejecutar_asignacion(op_eficiencia, operaciones, takt_time_teorico, ignorar_precedencia=True)

    return {
        "secuencial": res_secuencial,
        "eficiencia": res_eficiencia
    }


def _asignar_roles(num_operarios, tipos_maquinas, maquinas_demanda):
    operarios = []
    for i in range(num_operarios):
        operarios.append({
            'id': i + 1,
            'nombre': f"Operario {i + 1}",
            'maquina_asignada': None,
            'tiempo_acumulado': 0,
            'tareas': [],
            'porcentaje_carga': 0
        })
        
    asignacion_roles = {maq: 0 for maq in tipos_maquinas}
    operarios_disponibles = num_operarios
    
    # Ordenamos máquinas por demanda (mayor a menor)
    tipos_ordenados = sorted(tipos_maquinas, key=lambda m: maquinas_demanda[m], reverse=True)
    
    maquinas_cubiertas = []
    
    # A) Asegurar al menos 1 operario por máquina
    if operarios_disponibles >= len(tipos_maquinas):
        for maq in tipos_ordenados:
            asignacion_roles[maq] = 1
            operarios_disponibles -= 1
            maquinas_cubiertas.append(maq)
    else:
        # Fallback (aunque arriba ya validamos error, dejamos esto por robustez)
        for i in range(operarios_disponibles):
            maq = tipos_ordenados[i]
            asignacion_roles[maq] = 1
            maquinas_cubiertas.append(maq)
        operarios_disponibles = 0
        
    # B) Repartir operarios sobrantes proporcionalmente
    if operarios_disponibles > 0:
        while operarios_disponibles > 0:
            best_maq = None
            max_ratio = -1
            for maq in maquinas_cubiertas:
                ratio = maquinas_demanda[maq] / asignacion_roles[maq]
                if ratio > max_ratio:
                    max_ratio = ratio
                    best_maq = maq
            
            if best_maq:
                asignacion_roles[best_maq] += 1
                operarios_disponibles -= 1
            else:
                break

    # C) Aplicar roles
    op_pointer = 0
    for maq in tipos_ordenados:
        cantidad = asignacion_roles[maq]
        for _ in range(cantidad):
            if op_pointer < num_operarios:
                operarios[op_pointer]['maquina_asignada'] = maq
                op_pointer += 1
                
    return operarios

def _ejecutar_asignacion(operarios, operaciones, takt_time_teorico, ignorar_precedencia=False):
    # Agrupar operarios por rol para acceso rápido
    operarios_por_rol = {}
    for op in operarios:
        m = op['maquina_asignada']
        if m not in operarios_por_rol:
            operarios_por_rol[m] = []
        operarios_por_rol[m].append(op)
        
    maquinas_cubiertas = list(operarios_por_rol.keys())
    
    tareas_pendientes = operaciones.copy()
    letras_asignadas = set()
    
    max_iters = len(operaciones) * len(operarios) * 10
    iters = 0
    
    # Bucle Principal
    while len(tareas_pendientes) > 0 and iters < max_iters:
        hubo_progreso = False
        iters += 1
        
        for maq in maquinas_cubiertas:
            grupo_operarios = operarios_por_rol[maq]
            candidatas = [t for t in tareas_pendientes if t['maquina'] == maq]
            
            # HEURÍSTICA DE EFICIENCIA: LPT (Longest Processing Time first)
            # Si ignoramos precedencia, intentamos encajar las piedras grandes primero
            if ignorar_precedencia:
                candidatas.sort(key=lambda t: t['tiempo'], reverse=True)
            
            for tarea in candidatas:
                # Si NO ignoramos precedencia, validamos
                if not ignorar_precedencia and not predecesoras_cumplidas(tarea, letras_asignadas):
                    continue
                
                # Asignación Greedy dentro del rol
                grupo_operarios.sort(key=lambda x: x['tiempo_acumulado'])
                
                candidato_elegido = grupo_operarios[0]
                # Buscar el primero que quepa en el Takt
                for op in grupo_operarios:
                    if op['tiempo_acumulado'] + tarea['tiempo'] <= (takt_time_teorico * 1.15):
                        candidato_elegido = op
                        break
                
                # Asignar
                candidato_elegido['tareas'].append(tarea)
                candidato_elegido['tiempo_acumulado'] += tarea['tiempo']
                letras_asignadas.add(tarea['letra'])
                
                # Eliminar de pendientes
                for i, tp in enumerate(tareas_pendientes):
                    if tp['id'] == tarea['id']:
                        tareas_pendientes.pop(i)
                        break
                
                hubo_progreso = True
                
        if not hubo_progreso:
            break

    # Calcular KPIs del escenario
    tiempo_ciclo_real = max(op['tiempo_acumulado'] for op in operarios) if operarios else 0
    if tiempo_ciclo_real == 0: tiempo_ciclo_real = 1
    
    tiempo_total_prenda = sum(op['tiempo'] for op in operaciones) # O usar el global
    num_operarios = len(operarios)
    
    produccion_estimada = 3600 / tiempo_ciclo_real
    fuerza_laboral_minutos = tiempo_ciclo_real * num_operarios
    eficiencia = (tiempo_total_prenda / fuerza_laboral_minutos * 100) if fuerza_laboral_minutos > 0 else 0
    
    for op in operarios:
        op['porcentaje_carga'] = min(100, (op['tiempo_acumulado'] / tiempo_ciclo_real * 100)) if tiempo_ciclo_real > 0 else 0
        if op['maquina_asignada'] is None:
            op['maquina_asignada'] = "Sin Asignar"

    return {
        "kpis": {
            "eficiencia": round(eficiencia, 2),
            "produccion_hora": int(produccion_estimada),
            "tiempo_ciclo": tiempo_ciclo_real,
            "takt_target": takt_time_teorico,
            "tiempo_total": tiempo_total_prenda
        },
        "operarios": operarios
    }

def predecesoras_cumplidas(op, asignadas):
    preds = op['predecesoras']
    if not preds or preds == "N/A":
        return True
    
    lista_preds = [p.strip() for p in preds.split(',')]
    for p in lista_preds:
        if p not in asignadas:
            return False
    return True
