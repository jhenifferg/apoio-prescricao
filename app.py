import json
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Apoio à Prescrição",
    page_icon="💊",
    layout="wide",
)

st.title("💊 Apoio à Prescrição Farmacológica")

## localizar o ficheiro 
caminho_dados = Path(__file__).parent / "medicamentos.json"

## lê os dados e transforma o JSON
with caminho_dados.open(encoding="utf-8") as ficheiro:
    medicamentos = json.load(ficheiro)

st.subheader("Consultar medicamento")

## utilizador vê o nome; a aplicação guarda o índice selecionado.
indice = st.selectbox(
    "Medicamento",
    options=range(len(medicamentos)),
    format_func=lambda i: medicamentos[i]["nome"],
    index=None,
    placeholder="Selecione um medicamento",
)

if indice is not None:
    medicamento = medicamentos[indice]

    st.subheader(medicamento["nome"])

    coluna_1, coluna_2 = st.columns(2)

    with coluna_1:
        st.write("**Substância ativa:**", medicamento["substancia_ativa"])
        st.write("**Apresentação:**", medicamento["apresentacao"])

    with coluna_2:
        st.write("**Via:**", medicamento["via"])
        st.write("**Estado de revisão:**", medicamento["estado_revisao"])

    st.subheader("Informação posológica")

    if not medicamento["regras_posologicas"]:
        st.warning("Ainda não existem regras posológicas registadas.")

    st.subheader("Fonte")

    fonte = medicamento["fonte"]

    if fonte["documento"]:
        st.write(fonte["documento"])
    else:
        st.write("Ainda não foi associado um RCM.")

    if fonte["url"]:
        st.link_button("Consultar documento de origem", fonte["url"])