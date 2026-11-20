"""Exporta a secção 4.2 de cada PDF para conferência documental."""

import argparse
from pathlib import Path

from rcm import ler_rcm


def relatorio(pdf):
    linhas = [pdf.name, '', 'Secção 4.2 — Posologia e modo de administração', '']
    try:
        leitura = ler_rcm(pdf.read_bytes())
    except Exception as erro:
        return '\n'.join([*linhas, f'Falha de leitura ({type(erro).__name__}).', ''])

    trechos = leitura['secoes'].get('4.2', {}).get('trechos', [])
    paginas = sorted({trecho['pagina'] for trecho in trechos})
    if paginas:
        linhas.append('Páginas identificadas no PDF: ' + ', '.join(map(str, paginas)))
    else:
        linhas.append('Secção 4.2 não encontrada no texto extraído.')
    if leitura['paginas_sem_texto']:
        linhas.append('Páginas sem texto extraído: ' + ', '.join(map(str, leitura['paginas_sem_texto'])))
    linhas.extend(['Conferir a completude e a ordem do texto e das tabelas com o PDF original.', ''])
    pagina_anterior = None
    for trecho in trechos:
        if trecho['pagina'] != pagina_anterior:
            pagina_anterior = trecho['pagina']
            linhas.extend(['', f'Página {pagina_anterior} do PDF', ''])
        linhas.append(trecho['texto'])
    return '\n'.join(linhas).rstrip() + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdfs', nargs='+', type=Path)
    parser.add_argument('--saida', required=True, type=Path)
    args = parser.parse_args()
    nomes = [pdf.stem.casefold() for pdf in args.pdfs]
    if len(nomes) != len(set(nomes)):
        parser.error('Cada PDF deve ter um nome distinto.')
    import pypdf  # Verifica a dependência antes de iniciar o lote.

    args.saida.mkdir(parents=True, exist_ok=True)
    for pdf in args.pdfs:
        destino = args.saida / f'{pdf.stem}.txt'
        destino.write_text(relatorio(pdf), encoding='utf-8')
        print(destino)


if __name__ == '__main__':
    main()
