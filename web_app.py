"""Servidor local do protótipo. Executar com python3 web_app.py."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from pathlib import Path

from dados import carregar_medicamentos
from motor import MESES_POR_UNIDADE, analisar, calcular_intervalo, faixa_etaria
from sincronizar_catalogo import ler_apresentacoes

WEB = Path(__file__).parent / 'web'
FONTE = 'https://www.medicines.org.uk/emc/product/14145/smpc'
PILOTO = {
    'id': 'amoxicilina_250', 'nome': 'Amoxicilina',
    'apresentacao': '250 mg/5 mL · suspensão oral',
}


def catalogo_web():
    """Combina pilotos com apresentações importadas, sem herdar posologia por nome."""
    pilotos = [*carregar_medicamentos(), PILOTO]
    importadas = [
        dict(registo, id='catalogo:' + registo['id'], somente_catalogo=True)
        for registo in ler_apresentacoes()
    ]
    return [*pilotos, *importadas]


def calcular_ajuste(caso):
    """Demonstra as duas faixas renais do piloto, fora de diálise."""
    idade, peso, tfg = (caso.get(campo) for campo in ('idade', 'peso_kg', 'tfg'))
    if any(v is None for v in (idade, peso, tfg)):
        return {'pendencias': ['Preenche idade, peso e TFG absoluta em mL/min.']}
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in (idade, peso, tfg)):
        raise ValueError('Parâmetros numéricos inválidos')
    idade_anos = idade * MESES_POR_UNIDADE.get(caso.get('unidade_idade'), 12) / 12
    if not (0 <= idade_anos < 18 and 0 < peso < 40 and 0 <= tfg <= 30):
        return {'pendencias': ['Caso fora do ramo demonstrado. Este piloto cobre pediatria abaixo de 40 kg e TFG até 30 mL/min.']}
    if caso.get('dialise') != 'Não' or caso.get('alergia') != 'Não':
        return {'pendencias': ['O cálculo exige confirmação de ausência de diálise e de alergia relevante.']}
    tomas = 1 if tfg < 10 else 2
    por_toma = min(15 * peso, 500)
    diaria = por_toma * tomas
    dose = dict(componente='Amoxicilina', unidade='mg/dia', minimo=diaria,
                maximo=diaria, administracoes_dia=tomas, concentracao_mg_ml=50)
    resultado = calcular_intervalo(dose, caso)
    resultado.update(nome='Ajuste renal · TFG < 10 mL/min' if tomas == 1 else 'Ajuste renal · TFG 10–30 mL/min',
                     explicacao=f'15 mg/kg × {peso:g} kg, limitado a 500 mg por toma.',
                     fonte={'documento': 'RCM britânico · Amoxicilina 250 mg/5 mL', 'secao': '4.2', 'url': FONTE})
    return {'calculos': [resultado], 'pendencias': [
        'Simulação académica por validar. A fonte refere preferência pela via parentérica na maioria destes casos.',
    ]}


def analisar_caso(caso, medicamento):
    if medicamento.get('somente_catalogo'):
        return {'pendencias': ['Apresentação de catálogo. Cálculo indisponível até existir uma regra associada e revista.']}
    if caso.get('gravidez') or caso.get('aleitamento'):
        return {'pendencias': ['Neste episódio, consulta a informação da ficha.']}
    if medicamento['id'] == PILOTO['id']:
        return calcular_ajuste(caso)
    if medicamento.get('pendencia_calculo'):
        return {'pendencias': [medicamento['pendencia_calculo']],
                'informacoes': medicamento.get('informacoes', [])}
    demonstracao = caso.get('demonstracao') is True
    if demonstracao and medicamento.get('indicacao_demo'):
        caso = dict(caso, indicacao=medicamento['indicacao_demo'])
    resultado = analisar(caso, medicamento, demonstracao=demonstracao)
    motivos = resultado['pendencias']
    descartados = any(m.startswith('Esquema não aplicado:') for m in motivos)
    motivos = [m for m in motivos if not m.startswith('Esquema não aplicado:')]
    if medicamento['id'] == 'gentamicina_labesfal_80_2':
        if caso.get('idade') is None:
            motivos.insert(0, 'Introduz a idade no episódio.')
        if caso.get('peso_kg') is None:
            motivos.insert(0, 'Introduz o peso em kg no episódio.')
    nota = 'Análise parcial: não constitui aprovação da prescrição.'
    if descartados and not resultado['calculos'] and not resultado['alertas'] and motivos == [nota]:
        motivos.insert(0, 'Os dados do episódio estão fora dos esquemas disponíveis.')
    resultado['pendencias'] = list(dict.fromkeys(motivos))
    return resultado


class Handler(BaseHTTPRequestHandler):
    def responder(self, corpo, tipo, status=200):
        self.send_response(status)
        self.send_header('Content-Type', tipo)
        self.end_headers()
        self.wfile.write(corpo)

    def json(self, dados, status=200):
        self.responder(json.dumps(dados, ensure_ascii=False).encode(), 'application/json', status)

    def do_GET(self):
        if self.path == '/api/catalogo':
            try:
                self.json(catalogo_web())
            except (ValueError, OSError):
                self.json({'erro': 'Verifica o ficheiro de catálogo importado.'}, 500)
        elif self.path in ('/', '/style.css', '/app.js'):
            nome, tipo = {
                '/': ('index.html', 'text/html'),
                '/style.css': ('style.css', 'text/css'),
                '/app.js': ('app.js', 'text/javascript'),
            }[self.path]
            self.responder((WEB / nome).read_bytes(), tipo + '; charset=utf-8')
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != '/api/analisar':
            self.send_error(404)
            return
        try:
            tamanho = int(self.headers.get('Content-Length', 0))
            if not 0 < tamanho <= 16384:
                raise ValueError('Pedido inválido')
            caso = json.loads(self.rfile.read(tamanho))
            medicamento = next(m for m in catalogo_web() if m['id'] == caso['medicamento'])
            resultado = analisar_caso(caso, medicamento)
            resultado['faixa_etaria'] = faixa_etaria(caso.get('idade'), caso.get('unidade_idade'))
            self.json(resultado)
        except (ValueError, TypeError, KeyError, StopIteration):
            self.json({'erro': 'Verifica os dados do episódio e a apresentação.'}, 400)


if __name__ == '__main__':
    print('Abre http://127.0.0.1:8765', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
