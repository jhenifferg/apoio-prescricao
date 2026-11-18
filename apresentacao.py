"""Apresentação legível, sem alterar a evidência guardada."""
import re


def texto_rcm(trechos):
    paragrafos=[]
    atual=''
    for trecho in trechos:
        linha=trecho['texto'].strip()
        if not linha:
            if atual:paragrafos.append(atual);atual=''
            continue
        novo=linha.startswith(('•','- ')) or bool(re.match(r'^\d+\.\d+\s',linha))
        if novo and atual:paragrafos.append(atual);atual=''
        atual=(atual+' '+linha).strip()
        if linha.endswith(('.',':',';')):
            paragrafos.append(atual);atual=''
    if atual:paragrafos.append(atual)
    return '\n\n'.join(paragrafos)


def texto_fonte(fonte):
    partes=[fonte.get('documento','RCM do medicamento')]
    if fonte.get('secao'):partes.append('Secção '+fonte['secao'])
    if fonte.get('paginas'):partes.append('Páginas '+', '.join(str(p) for p in fonte['paginas']))
    partes.append('Revisão do documento: '+(fonte.get('data_revisao') or 'não identificada'))
    return ' · '.join(partes)


def formatar_valor(valor):
    if valor is None:return 'Não informado'
    if isinstance(valor,(int,float)):return f'{valor:g}'
    return str(valor)
