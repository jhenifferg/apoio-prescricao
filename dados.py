import json
from pathlib import Path


def carregar_medicamentos():
    caminho = Path(__file__).parent / 'medicamentos.json'
    dados = json.loads(caminho.read_text(encoding='utf-8'))
    if not isinstance(dados, list):
        raise ValueError('O catálogo deve ser uma lista.')
    ids = set()
    for medicamento in dados:
        for campo in ('id', 'nome', 'apresentacao', 'regras', 'esquemas'):
            if campo not in medicamento:
                raise ValueError(f'Campo obrigatório ausente: {campo}')
        if medicamento['id'] in ids:
            raise ValueError('Identificador duplicado: ' + medicamento['id'])
        ids.add(medicamento['id'])
    return dados
