import streamlit as st
from dados import carregar_medicamentos
from motor import analisar

st.set_page_config(page_title='Apoio à Prescrição', page_icon='💊', layout='wide')
st.title('💊 Apoio à Prescrição Farmacológica')
st.caption('Protótipo académico • Dados fictícios • Análise parcial')
try:
    catalogo = carregar_medicamentos()
except (OSError, ValueError) as erro:
    st.error(str(erro))
    st.stop()
st.session_state.setdefault('paciente', None)
paciente = st.session_state['paciente']
base = paciente or {}
with st.expander('Editar caso' if paciente else 'Preencher caso', expanded=paciente is None):
    with st.form('formulario_paciente'):
        indicacoes = ['Otite média aguda', 'Outra indicação / não estruturada', 'Teste de engenharia']
        indicacao = st.selectbox('Indicação', indicacoes, index=indicacoes.index(base.get('indicacao', indicacoes[0])))
        cols = st.columns(3)
        idade = cols[0].number_input('Idade', min_value=0.0, value=base.get('idade'), step=0.1)
        unidade = cols[1].selectbox('Unidade', ['Anos','Meses'], index=0 if base.get('unidade_idade','Anos')=='Anos' else 1)
        peso = cols[2].number_input('Peso (kg)', min_value=0.0, value=base.get('peso_kg'), step=0.1)
        clcr = st.number_input('ClCr (ml/min) — opcional', min_value=0.0, value=base.get('clcr_ml_min'), help='Valor avaliado pelo profissional. Não copiar diretamente uma eTFG em ml/min/1,73 m². Não calculamos nem convertemos função renal.')
        superficie = st.number_input('Superfície corporal (m²) — apenas teste fictício', min_value=0.0, value=base.get('superficie_m2'))
        hep = ['Não informada','Sem compromisso conhecido','Compromisso hepático referido']
        hepatica = st.selectbox('Situação hepática', hep, index=hep.index(base.get('funcao_hepatica',hep[0])))
        escolhas = ['Não avaliada','Não','Sim']
        alergia = st.selectbox('História de hipersensibilidade às substâncias/penicilinas ou reação imediata grave a outros beta-lactâmicos', escolhas, index=escolhas.index(base.get('alergia_relevante',escolhas[0])))
        historia = st.selectbox('História de icterícia/compromisso hepático devido a amoxicilina/clavulanato', escolhas, index=escolhas.index(base.get('historia_hepatica_associada',escolhas[0])))
        if st.form_submit_button('Guardar caso'):
            if idade is None or peso is None or peso <= 0 or (superficie is not None and superficie <= 0):
                st.error('Preencher idade, peso positivo e, se indicada, superfície positiva.')
            else:
                st.session_state['paciente'] = dict(indicacao=indicacao, idade=idade, unidade_idade=unidade,peso_kg=peso,clcr_ml_min=clcr,superficie_m2=superficie,funcao_hepatica=hepatica,alergia_relevante=alergia,historia_hepatica_associada=historia)
                st.rerun()
paciente = st.session_state['paciente']
if not paciente:
    st.stop()
with st.container(border=True):
    cols=st.columns(3)
    cols[0].write(f"**Idade:** {paciente['idade']:g} {paciente['unidade_idade'].lower()}")
    cols[1].write(f"**Peso:** {paciente['peso_kg']:g} kg")
    cols[2].write('**Indicação:** '+paciente['indicacao'])
    st.caption(f"ClCr: {paciente['clcr_ml_min'] if paciente['clcr_ml_min'] is not None else 'não informada'} ml/min | Hepática: {paciente['funcao_hepatica']}")
por_id={m['id']:m for m in catalogo}
selecionados=st.multiselect('Medicamentos em análise',list(por_id),format_func=lambda i:por_id[i]['nome'])
demo=st.checkbox('Ativar cálculos demonstrativos com regras por validar', value=False)
if demo:
    st.warning('Demonstração matemática com casos fictícios. Não constitui recomendação de dose nem validação clínica.')
if st.button('Analisar prescrição',type='primary',disabled=not selecionados):
    for id in selecionados:
        m=por_id[id]
        with st.container(border=True):
            st.subheader(m['nome'])
            st.caption(m['apresentacao']+' | Estado: '+m['estado'])
            try:
                r=analisar(paciente,m,demonstracao=demo)
            except (ValueError,KeyError) as erro:
                st.error(f'Análise interrompida: {erro}')
                continue
            for a in r['alertas']:
                (st.error if a['tipo']=='bloqueio' else st.info if a['tipo']=='informacao' else st.warning)(a['texto'])
                with st.expander('Fonte da orientação'):
                    st.json(a['fonte'])
            st.markdown('**Pendências e limites da análise**')
            for texto in dict.fromkeys(r['pendencias']): st.write('• '+texto)
            for calc in r['calculos']:
                st.markdown('**Intervalo matemático demonstrativo — '+calc['componente']+'**')
                st.write('Não seleciona uma dose dentro do intervalo nem aprova o esquema.')
                st.write(f"{calc['mg_dia'][0]:g}–{calc['mg_dia'][1]:g} mg/dia; {calc['mg_administracao'][0]:g}–{calc['mg_administracao'][1]:g} mg por administração; {calc['administracoes_dia']} administrações/dia.")
                if 'ml_administracao' in calc:
                    st.write(f"Volume matemático: {calc['ml_administracao'][0]:.3f}–{calc['ml_administracao'][1]:.3f} ml por administração. Sem arredondamento para dispositivo de medida.")
                for aviso in calc['avisos']: st.warning(aviso)
                with st.expander('Evidência do cálculo'): st.json(calc['fonte'])
            with st.expander('Informação adicional do medicamento'):
                for info in r['informacoes']:
                    st.markdown('**'+info['titulo']+'**')
                    st.write(info['texto'])
                    st.json(info['fonte'])
    st.warning('Interações entre selecionados e medicação habitual não avaliadas. Ausência de alerta não significa segurança. Outras contraindicações/precauções do RCM podem não estar representadas.')
