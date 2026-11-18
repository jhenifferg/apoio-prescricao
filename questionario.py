def recolher_perguntas(medicamentos):
    """Agrupa perguntas equivalentes; não une significados incompatíveis."""
    resultado={}
    for medicamento in medicamentos:
        for original in medicamento.get('perguntas',[]):
            pergunta=dict(original)
            id=pergunta['id']
            if id in resultado:
                anterior=resultado[id]
                if any(anterior.get(k)!=pergunta.get(k) for k in ('texto','tipo','opcoes')):
                    raise ValueError('Perguntas incompatíveis para o parâmetro '+id)
                anterior['medicamentos'].append(medicamento['nome'])
            else:
                pergunta['medicamentos']=[medicamento['nome']]
                resultado[id]=pergunta
    return list(resultado.values())
