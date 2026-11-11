import unittest
from dados import carregar_medicamentos
from motor import analisar, avaliar, calcular_intervalo
class TestMotor(unittest.TestCase):
 def setUp(self):
  self.m=carregar_medicamentos()[0]
  self.p=dict(idade=4,unidade_idade='Anos',peso_kg=20,indicacao='Otite média aguda',clcr_ml_min=60,funcao_hepatica='Sem compromisso conhecido',alergia_relevante='Não',historia_hepatica_associada='Não')
 def test_validacao(self): self.assertEqual(analisar(self.p,self.m)['calculos'],[])
 def test_demo(self):
  c=analisar(self.p,self.m,True)['calculos'][0]
  self.assertEqual(c['mg_dia'],[500,900]); self.assertEqual(c['ml_administracao'],[3.125,5.625])
 def test_bloqueios(self):
  for a in [dict(peso_kg=40),dict(clcr_ml_min=29),dict(clcr_ml_min=30),dict(clcr_ml_min=None),dict(idade=1,unidade_idade='Meses'),dict(alergia_relevante='Sim'),dict(historia_hepatica_associada='Sim'),dict(funcao_hepatica='Não informada'),dict(funcao_hepatica='Compromisso hepático referido'),dict(indicacao='Otite leve')]:
   with self.subTest(a=a): self.assertEqual(analisar(dict(self.p,**a),self.m,True)['calculos'],[])
 def test_desconhecido(self): self.assertIsNone(avaliar(dict(parametro='x',operador='>',valor=2),{}))
 def test_operador(self):
  with self.assertRaises(ValueError): avaliar(dict(parametro='x',operador='EXEC',valor=2),{'x':1})
 def test_superficie(self):
  d=dict(componente='Fictícia',minimo=10,maximo=20,unidade='mg/m2/dia',administracoes_dia=2)
  self.assertEqual(calcular_intervalo(d,{'superficie_m2':1.2})['mg_dia'],[12,24])
 def test_invalidos(self):
  for peso in [-1,float('nan'),float('inf')]:
   with self.assertRaises(ValueError): analisar(dict(self.p,peso_kg=peso),self.m,True)
if __name__=='__main__': unittest.main()
