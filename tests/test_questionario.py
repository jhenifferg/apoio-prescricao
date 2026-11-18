import unittest
from questionario import recolher_perguntas
from dados import carregar_medicamentos
class PerguntasTest(unittest.TestCase):
 def test_sem_medicamento(self):self.assertEqual(recolher_perguntas([]),[])
 def test_especificas(self):
  meds=carregar_medicamentos()
  self.assertIn('clcr_ml_min',[q['id'] for q in recolher_perguntas([meds[0]])])
  self.assertNotIn('clcr_ml_min',[q['id'] for q in recolher_perguntas([meds[1]])])
 def test_agrupar(self):
  m=carregar_medicamentos()[0]
  self.assertEqual(len(recolher_perguntas([m,m])),len(m['perguntas']))
