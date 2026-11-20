"""Identifica candidatos a regras de dose por peso na secção 4.2 de um RCM."""

import argparse
import json
import re
from pathlib import Path

from rcm import ler_rcm


NUMERO = r"\d+(?:[,.]\d+)?"
POR_PESO = r"mg\s*/\s*kg"
POR_DIA = r"\s*/\s*dia\b"
VETO_NUMERICO = r"(?<![\w/.,])"
PADROES = re.compile(
    rf"{VETO_NUMERICO}(?P<composto>{NUMERO}\s*mg\s*/\s*{NUMERO}\s*{POR_PESO}"
    rf"(?:{POR_DIA})?(?:\s+a\s+{NUMERO}\s*mg\s*/\s*{NUMERO}\s*{POR_PESO}(?:{POR_DIA})?)?)"
    rf"|{VETO_NUMERICO}(?P<primeiro>{NUMERO})(?:\s*[-–]\s*(?P<segundo>{NUMERO}))?"
    rf"\s*{POR_PESO}\b(?P<diaria>{POR_DIA}|\s+de\s+peso\s+corporal\s+por\s+dia\b)?",
    re.IGNORECASE,
)


def blocos(trechos):
    """Preserva o contexto do parágrafo e as páginas que o sustentam."""
    bloco = []
    for trecho in trechos:
        if trecho['texto'].strip():
            bloco.append(trecho)
        elif bloco:
            yield bloco
            bloco = []
    if bloco:
        yield bloco


def propor_regras(leitura):
    secao = leitura['secoes'].get('4.2')
    candidatos = []
    for bloco in blocos(secao['trechos'] if secao else []):
        excerto = ' '.join(t['texto'].strip() for t in bloco)
        paginas = sorted({t['pagina'] for t in bloco})
        for ocorrencia in PADROES.finditer(excerto):
            limites = None
            if ocorrencia['composto']:
                tipo = 'dose_por_peso_multicomponente'
            elif ocorrencia['diaria']:
                tipo = 'dose_diaria_por_peso'
                primeiro = float(ocorrencia['primeiro'].replace(',', '.'))
                segundo = float((ocorrencia['segundo'] or ocorrencia['primeiro']).replace(',', '.'))
                if 0 < primeiro <= segundo:
                    limites = {'minimo': primeiro, 'maximo': segundo, 'unidade': 'mg/kg/dia'}
            else:
                tipo = 'dose_por_peso_periodicidade_a_confirmar'
            candidatos.append({
                'tipo': tipo,
                'expressao': ocorrencia.group(),
                'intervalo': limites,
                'fonte': {'secao': '4.2', 'paginas': paginas, 'excerto': excerto},
            })
    return {
        'estado': 'pendente_revisao' if candidatos else 'sem_candidatos',
        'secao_4_2_encontrada': bool(secao),
        'paginas_sem_texto': leitura['paginas_sem_texto'],
        'candidatos': candidatos,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    args = parser.parse_args()
    leitura = ler_rcm(args.pdf.read_bytes())
    saida = {'documento': args.pdf.name, 'sha256': leitura['sha256'], **propor_regras(leitura)}
    print(json.dumps(saida, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
