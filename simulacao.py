def verificar_idade_peso(paciente, medicamento):
    """Compara idade e peso com as condições registadas."""

    alertas = []

    idade = paciente["idade"]
    unidade = paciente["unidade_idade"]

    if unidade == "Anos":
        idade_meses = idade * 12
    elif unidade == "Meses":
        idade_meses = idade
    else:
        return ["Unidade de idade desconhecida; verificar os dados."]

    valores = {
        "idade_meses": idade_meses,
        "peso_kg": paciente["peso_kg"],
    }

    verificacoes = medicamento.get("verificacoes", [])

    for verificacao in verificacoes:
        parametro = verificacao["parametro"]
        valor = valores.get(parametro)

        if valor is None:
            alertas.append(
                f"Não foi possível avaliar o parâmetro: {parametro}."
            )
            continue

        operador = verificacao["operador"]
        limite = verificacao["limite"]

        if operador == "<":
            condicao_verificada = valor < limite
        elif operador == ">=":
            condicao_verificada = valor >= limite
        else:
            alertas.append(
                f"Operador não implementado na verificação: "
                f"{verificacao['id']}."
            )
            continue

        if condicao_verificada:
            alertas.append(
                f"{verificacao['mensagem']} "
                f"Fonte: {verificacao['fonte']}."
            )

    return alertas

def simular_medicamento(paciente, medicamento):
    """Organiza informação para apoiar a análise da prescrição."""

    alertas = verificar_idade_peso(paciente, medicamento)
    pendencias = []
    informacoes = []

    regras = medicamento.get("regras_posologicas", [])

    # Verificar a informação disponível sobre o paciente.
    situacao_renal = paciente.get("funcao_renal", "Não informada")

    if situacao_renal == "Não informada":
        pendencias.append(
            "Situação renal não informada. "
            "Completar a avaliação quando relevante para este medicamento."
        )

    elif situacao_renal == "Compromisso renal referido":
        alertas.append(
            "Foi referido compromisso renal. É necessário consultar "
            "as orientações específicas do medicamento e os parâmetros "
            "que essas orientações exigem."
        )

    situacao_hepatica = paciente.get("funcao_hepatica", "Não informada")

    if situacao_hepatica == "Não informada":
        pendencias.append(
            "Situação hepática não informada. "
            "Completar a avaliação quando relevante para este medicamento."
        )

    elif situacao_hepatica == "Compromisso hepático referido":
        alertas.append(
            "Foi referido compromisso hepático. Consultar as restrições "
            "e necessidades de monitorização documentadas para o medicamento."
        )

    # Procurar uma correspondência textual da indicação.
    indicacao_caso = paciente["indicacao"].strip().casefold()

    regras_correspondentes = []

    for regra in regras:
        indicacao_regra = regra.get("indicacao", "").strip().casefold()

        if indicacao_caso == indicacao_regra:
            regras_correspondentes.append(regra)

    if not regras_correspondentes:
        pendencias.append(
            "Não foi encontrada correspondência textual exata entre "
            "a indicação introduzida e as regras registadas. "
            "Confirmar a indicação; isto não significa contraindicação."
        )

    for regra in regras_correspondentes:
        texto_posologia = regra.get("posologia_texto")

        if texto_posologia:
            informacoes.append({
                "titulo": "Posologia documentada — aplicabilidade por avaliar",
                "texto": texto_posologia,
                "fonte": regra.get("fonte", {}),
            })
        else:
            pendencias.append(
                "A indicação tem uma regra registada, mas a informação "
                "posológica ainda não foi preenchida."
            )

    # Estas avaliações ainda não fazem parte do protótipo.
    pendencias.append(
        "Alergias, contraindicações e medicação habitual ainda não avaliadas."
    )

    return {
        "medicamento": medicamento["nome"],
        "alertas": alertas,
        "pendencias": pendencias,
        "informacoes": informacoes,
        "estado": "Análise parcial — sem cálculo de dose",
    }