import unittest
from apresentacao import texto_rcm,texto_fonte,formatar_valor
class ApresentacaoTest(unittest.TestCase):
 def test_sem_prefixo(self):
  t=texto_rcm([dict(pagina=1,texto='• Infeções cutâneas e'),dict(pagina=2,texto='dos tecidos moles.')])
  self.assertEqual(t,'• Infeções cutâneas e dos tecidos moles.')
 def test_fonte_texto(self):
  self.assertIn('Páginas 2, 3',texto_fonte(dict(secao='4.2',paginas=[2,3])))
 def test_nulo(self):self.assertEqual(formatar_valor(None),'Não informado')
