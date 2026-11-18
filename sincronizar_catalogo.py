"""Aplica lotes normalizados ao catálogo local. Não acede ao CITS."""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

CATALOGO = Path(__file__).with_name('catalogo_apresentacoes.json')
CAMPOS = ('id', 'nome', 'substancia_ativa', 'apresentacao', 'fonte_catalogo')


def ler_json(caminho):
    return json.loads(caminho.read_text(encoding='utf-8'))


def indice(registos):
    if not isinstance(registos, list):
        raise ValueError('As apresentações devem ser uma lista.')
    resultado = {}
    for registo in registos:
        if not isinstance(registo, dict) or any(
            not isinstance(registo.get(c), str) or not registo[c].strip() for c in CAMPOS
        ):
            raise ValueError('Apresentação incompleta.')
        identificador = registo['id'].strip()
        if identificador in resultado:
            raise ValueError(f'Identificador repetido: {identificador}')
        resultado[identificador] = {c: registo[c].strip() for c in CAMPOS}
    return resultado


def ler_apresentacoes(caminho=CATALOGO):
    try:
        dados = ler_json(caminho)
    except FileNotFoundError:
        return []
    return list(indice(dados if isinstance(dados, list) else dados['apresentacoes']).values())


@contextmanager
def bloquear(caminho):
    with caminho.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def guardar(caminho, dados):
    temporario = None
    try:
        with NamedTemporaryFile(mode='w', encoding='utf-8', dir=caminho.parent, delete=False) as ficheiro:
            temporario = Path(ficheiro.name)
            json.dump(dados, ficheiro, ensure_ascii=False, indent=2)
        os.replace(temporario, caminho)
    finally:
        if temporario is not None:
            temporario.unlink(missing_ok=True)


def aplicar(lote, caminho=CATALOGO):
    versao = lote['versao']
    if not isinstance(versao, str) or not versao.strip():
        raise ValueError('Versão do lote inválida.')
    alteracoes = indice(lote['apresentacoes'])
    tipo = lote['tipo']
    removidas = lote.get('removidas', [])
    if not isinstance(removidas, list) or any(
        not isinstance(i, str) or not i.strip() for i in removidas
    ):
        raise ValueError('Identificadores de remoção inválidos.')
    removidas = {i.strip() for i in removidas}
    if tipo not in ('inicial', 'incremental') or removidas & alteracoes.keys():
        raise ValueError('Tipo de lote ou operações incompatíveis.')
    with bloquear(caminho):
        atual = ler_json(caminho) if caminho.exists() else {}
        if isinstance(atual, list):
            atual = {'apresentacoes': atual}
        if atual.get('versao') == versao:
            return False
        if tipo == 'inicial':
            if atual.get('versao') or removidas:
                raise ValueError('A carga inicial exige um catálogo sem versão e sem remoções.')
            registos = alteracoes
        else:
            if not atual.get('versao') or lote.get('base') != atual['versao']:
                raise ValueError('O lote incremental não corresponde à versão instalada.')
            registos = indice(atual['apresentacoes'])
            for identificador in removidas:
                registos.pop(identificador, None)
            registos.update(alteracoes)
        guardar(caminho, {'versao': versao, 'apresentacoes': list(registos.values())})
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lote', type=Path)
    parser.add_argument('--catalogo', type=Path, default=CATALOGO)
    args = parser.parse_args()
    try:
        print('Catálogo atualizado.' if aplicar(ler_json(args.lote), args.catalogo) else 'Lote já aplicado.')
    except (OSError, KeyError, TypeError, ValueError) as erro:
        parser.exit(1, f'Catálogo não atualizado: {erro}\n')
