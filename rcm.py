"""Leitura documental; não converte texto em regras clínicas automaticamente."""
from hashlib import sha256
from io import BytesIO
import re


def ler_rcm(conteudo):
    from pypdf import PdfReader
    pdf = PdfReader(BytesIO(conteudo))
    paginas = [{'pagina': i + 1, 'texto': pagina.extract_text() or ''}
               for i, pagina in enumerate(pdf.pages)]
    secoes = {}
    atual = None
    for pagina in paginas:
        for linha in pagina['texto'].splitlines():
            match = re.match(r'^\s*(\d+\.\d+)\s+(.+)', linha)
            if match and match.group(1) in ('4.1','4.2','4.3','4.4','4.5','4.6','4.7','4.8','4.9','5.1','5.2','5.3','6.1','6.2','6.3','6.4','6.5','6.6'):
                atual=match.group(1)
                secoes.setdefault(atual, {'titulo':match.group(2).strip(),'trechos':[]})
            if atual:
                secoes[atual]['trechos'].append({'pagina':pagina['pagina'],'texto':linha.strip()})
    return {'sha256':sha256(conteudo).hexdigest(),'numero_paginas':len(paginas),
            'secoes':secoes,'estado':'Leitura textual — exige revisão; não cria regras aprovadas',
            'paginas_sem_texto':[p['pagina'] for p in paginas if not p['texto'].strip()]}
