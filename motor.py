"""Motor declarativo: não contém nomes nem limiares de medicamentos."""
import math
import operator

OPS = {'<': operator.lt, '<=': operator.le, '>': operator.gt,
       '>=': operator.ge, '==': operator.eq, '!=': operator.ne,
       'contém': lambda valor, alvo: alvo in valor}


def avaliar(condicao, contexto):
    """Retorna True, False ou None (dados insuficientes). Nunca usa eval."""
    if 'todas' in condicao or 'alguma' in condicao:
        chave = 'todas' if 'todas' in condicao else 'alguma'
        resultados = [avaliar(c, contexto) for c in condicao[chave]]
        if chave == 'todas':
            return False if False in resultados else (None if None in resultados else True)
        return True if True in resultados else (None if None in resultados else False)
    op = condicao['operador']
    if op not in OPS:
        raise ValueError(f'Operador não suportado: {op}')
    valor = contexto.get(condicao['parametro'])
    if valor is None:
        return None
    try:
        return OPS[op](valor, condicao['valor'])
    except TypeError as erro:
        raise ValueError('Tipos incompatíveis na condição') from erro


def preparar_contexto(paciente):
    contexto = dict(paciente)
    idade = paciente.get('idade')
    unidade = paciente.get('unidade_idade')
    if idade is None or unidade not in ('Anos', 'Meses'):
        contexto['idade_meses'] = None
    else:
        contexto['idade_meses'] = idade * 12 if unidade == 'Anos' else idade
    for campo in ('idade_meses', 'peso_kg', 'altura_cm', 'clcr_ml_min', 'superficie_m2'):
        valor = contexto.get(campo)
        if valor is not None:
            if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
                raise ValueError(f'Valor inválido: {campo}')
            if valor < 0 or (campo in ('peso_kg', 'altura_cm', 'superficie_m2') and valor == 0):
                raise ValueError(f'Valor fora do domínio: {campo}')
    return contexto


def calcular_intervalo(dose, contexto):
    """Aritmética apenas; a seleção clínica do esquema ocorre antes."""
    bases = {'mg/kg/dia': 'peso_kg', 'mg/m2/dia': 'superficie_m2', 'mg/dia': None}
    unidade = dose['unidade']
    if unidade not in bases:
        raise ValueError(f'Unidade não suportada: {unidade}')
    campo = bases[unidade]
    fator = contexto.get(campo) if campo else 1
    if fator is None:
        raise ValueError(f'Falta o parâmetro {campo}')
    minimo, maximo = dose['minimo'], dose['maximo']
    tomas = dose['administracoes_dia']
    numeros = (minimo, maximo, tomas, fator)
    if any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) for v in numeros):
        raise ValueError('Dose com valores inválidos')
    if minimo <= 0 or maximo < minimo or tomas <= 0 or int(tomas) != tomas or fator <= 0:
        raise ValueError('Intervalo ou frequência inválidos')
    diario = [minimo * fator, maximo * fator]
    avisos = []
    teto = dose.get('maximo_diario_mg')
    if teto is not None:
        if not isinstance(teto, (int, float)) or not math.isfinite(teto) or teto <= 0:
            raise ValueError('Limite diário inválido')
        if diario[0] > teto:
            raise ValueError('Todo o intervalo excede o limite diário; rever esquema')
        if diario[1] > teto:
            avisos.append('Extremo superior limitado pelo máximo diário documentado.')
            diario[1] = teto
    por_toma = [v / tomas for v in diario]
    resultado = {'componente': dose['componente'], 'mg_dia': diario,
                 'mg_administracao': por_toma, 'administracoes_dia': tomas, 'avisos': avisos}
    concentracao = dose.get('concentracao_mg_ml')
    if concentracao is not None:
        if not isinstance(concentracao, (int, float)) or not math.isfinite(concentracao) or concentracao <= 0:
            raise ValueError('Concentração inválida')
        resultado['ml_administracao'] = [v / concentracao for v in por_toma]
    return resultado


def analisar(paciente, medicamento, demonstracao=False):
    contexto = preparar_contexto(paciente)
    resultado = {'medicamento': medicamento['nome'], 'alertas': [], 'pendencias': [],
                 'calculos': [], 'informacoes': medicamento.get('informacoes', [])}
    bloqueado = False
    if not medicamento.get('regras'):
        resultado['pendencias'].append('Não existem verificações estruturadas para este medicamento.')
        bloqueado = True
    for regra in medicamento.get('regras', []):
        try:
            estado = avaliar(regra['condicao'], contexto)
        except (ValueError, KeyError) as erro:
            resultado['pendencias'].append(f"Regra {regra.get('id')}: {erro}")
            bloqueado = True
            continue
        if estado is None:
            resultado['pendencias'].append(regra.get('se_desconhecido', 'Faltam dados para avaliar: ' + regra['id']))
            bloqueado = bloqueado or regra.get('necessaria_calculo', True)
        elif estado:
            resultado['alertas'].append({'texto': regra['mensagem'], 'fonte': regra['fonte'],
                                        'tipo': regra['tipo']})
            bloqueado = bloqueado or regra['tipo'] == 'bloqueio'
    for esquema in medicamento.get('esquemas', []):
        try:
            aplicavel = avaliar(esquema['condicao'], contexto)
            if aplicavel is not True:
                resultado['pendencias'].append('Esquema não aplicado: ' + esquema['nome'])
                continue
            if bloqueado:
                resultado['pendencias'].append('Cálculo não apresentado devido a restrições ou dados em falta.')
                continue
            if esquema.get('estado') != 'validado_clinicamente' and not demonstracao:
                resultado['pendencias'].append('Cálculo disponível apenas no modo de demonstração: esquema por validar.')
                continue
            calculo = calcular_intervalo(esquema['dose'], contexto)
            calculo.update({'nome': esquema['nome'], 'fonte': esquema['fonte'],
                            'demonstracao': demonstracao, 'estado': esquema['estado']})
            resultado['calculos'].append(calculo)
        except (ValueError, KeyError) as erro:
            resultado['pendencias'].append(f'Não foi possível calcular: {erro}')
    resultado['pendencias'].append('Análise parcial: não constitui aprovação da prescrição.')
    return resultado
