# PDFs usados na extração

Os cinco PDFs em `originais/` são as cópias usadas nos testes. Guarda cada nova versão do RCM com um nome distinto para preservar a referência das leituras anteriores.

| Ficheiro | Origem |
| --- | --- |
| `augmentin-duo-400mg-57mg-5ml.pdf` | PDF disponibilizado no projeto como `documento.pdf`. |
| `ben-u-ron-xarope-40mg-ml.pdf` | [Cópia usada na extração](https://cdn-shopkit.com/usercontent/plataforma-de-pedidos/media/files/594d74b-120410-paracetamol-ben-u-ron-xarope-40-mgml.pdf) |
| `brufen-sem-acucar-20mg-ml.pdf` | [Cópia usada na extração](https://cdn-shopkit.com/usercontent/plataforma-de-pedidos/media/files/c0462ff-165024-ibuprofeno-brufen-sem-acucar-suspensao-20-mgml.pdf) |
| `gentamicina-labesfal-80mg-2ml.pdf` | [Cópia usada na extração](https://cdn.shopk.it/usercontent/plataforma-de-pedidos/media/files/7ee1a03-122637-gentamicina-80-mg-2-ml.pdf) |
| `klacid-pediatrico-25mg-ml.pdf` | [Cópia usada na extração](https://ojs.pjp.spp.pt/article/download/6561/11385/17277) |

A partir da raiz do repositório, depois de instalar as dependências de `requirements.txt`:

```sh
python exportar_leitura_rcm.py rcms/originais/*.pdf --saida leituras-reproduzidas
python propor_regras_rcm.py rcms/originais/augmentin-duo-400mg-57mg-5ml.pdf
```

A primeira operação gera os textos numa pasta à parte para comparação com `leituras-rcm/`. A segunda apresenta os candidatos e o SHA-256 do PDF usado.
