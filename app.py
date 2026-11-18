import json
import streamlit as st
from dados import carregar_medicamentos
from motor import analisar
from questionario import recolher_perguntas
from rcm import ler_rcm
from apresentacao import texto_rcm, texto_fonte, formatar_valor

st.set_page_config(page_title='Apoio à Prescrição',page_icon='💊',layout='wide')
st.markdown("""<style>
.block-container {max-width: 1180px; padding-top: 2rem; padding-bottom: 3rem;}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {font-size: 1.08rem; line-height: 1.65;}
[data-testid="stWidgetLabel"] p {font-size: 1.04rem; font-weight: 600;}
[data-testid="stCaptionContainer"] p {font-size: .96rem; line-height: 1.5; color: #536174;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 14px;}
.stButton button {min-height: 46px; padding: .5rem 1.1rem; font-size: 1.05rem;}
h1 {font-size: 2.25rem !important;} h2 {font-size: 1.65rem !important;}
h3 {font-size: 1.35rem !important;}
</style>""", unsafe_allow_html=True)


def mostrar_fonte(fonte):
    st.write(texto_fonte(fonte))
    if fonte.get('excerto_secao'):
        for paragrafo in texto_rcm([{'texto': linha} for linha in fonte['excerto_secao'].splitlines()]).split('\n\n'):
            st.write(paragrafo)


def mostrar_informacao_materna(paciente, medicamentos):
    contextos = (('gravidez', 'Gravidez'), ('aleitamento', 'Aleitamento'))
    for chave, titulo in contextos:
        if not paciente.get(chave):
            continue
        for medicamento in medicamentos:
            with st.container(border=True):
                st.markdown(f"**{titulo} · {medicamento['nome']}**")
                st.caption(medicamento['apresentacao'])
                nota = medicamento.get('informacao_materna', {}).get(chave)
                if nota:
                    st.write(nota['texto'])
                    st.caption(texto_fonte(nota['fonte']) + ' · Transcrição por rever')
                else:
                    st.info('Informação ainda não registada para esta apresentação.')


st.title('Apoio à Prescrição Pediátrica')
st.caption('Protótipo académico • Casos fictícios • Informação por validar')
aba_caso,aba_rcm=st.tabs(['Apoiar a prescrição','Consultar um RCM'])
with aba_rcm:
    st.write('Carregar o documento para consultar secções e preparar a revisão. A leitura não publica regras nem gera automaticamente recomendações.')
    ficheiro=st.file_uploader('RCM em PDF',type=['pdf'])
    if ficheiro:
        try:
            leitura=ler_rcm(ficheiro.getvalue())
            st.caption(f"Documento com {leitura['numero_paginas']} páginas. Selecione uma secção para ler.")
            if leitura['paginas_sem_texto']:st.warning('Páginas sem texto detetadas; pode ser necessário OCR.')
            for secao in ('4.1','4.2','4.3','4.4','4.5'):
                info=leitura['secoes'].get(secao)
                with st.expander(f"{secao} — {info['titulo'] if info else 'Não localizada'}"):
                    if info:
                        paginas = sorted({t['pagina'] for t in info['trechos']})
                        st.caption("Localização no documento: páginas " + ", ".join(map(str, paginas)))
                        for paragrafo in texto_rcm(info['trechos']).split("\n\n"):
                            st.write(paragrafo)
            st.download_button('Guardar leitura para revisão',json.dumps(leitura,ensure_ascii=False,indent=2),'leitura_rcm.json','application/json')
        except Exception as erro:
            st.error(f'Não foi possível ler o PDF: {erro}')
with aba_caso:
    try:catalogo=carregar_medicamentos()
    except (OSError,ValueError) as erro:
        st.error(str(erro));st.stop()
    st.session_state.setdefault('paciente',None)
    base=st.session_state['paciente'] or {}
    with st.expander('Editar dados do episódio' if base else 'Dados do episódio',expanded=not bool(base)):
        with st.form('episodio'):
            indicacao=st.text_area('Indicação e contexto clínico',value=base.get('indicacao',''))
            cols=st.columns(3)
            idade=cols[0].number_input('Idade',min_value=0.0,value=base.get('idade'),step=1.0,format='%g')
            unidade=cols[1].selectbox('Unidade da idade',['Anos','Meses'],index=0 if base.get('unidade_idade','Anos')=='Anos' else 1)
            peso=cols[2].number_input('Peso em kg',min_value=0.0,value=base.get('peso_kg'),step=0.1,format='%g')
            renal_op=['Não informada','Sem compromisso conhecido','Compromisso renal referido']
            hep_op=['Não informada','Sem compromisso conhecido','Compromisso hepático referido']
            renal=st.selectbox('Situação renal',renal_op,index=renal_op.index(base.get('funcao_renal',renal_op[0])))
            hepatica=st.selectbox('Situação hepática',hep_op,index=hep_op.index(base.get('funcao_hepatica',hep_op[0])))
            coluna_gravidez, coluna_aleitamento = st.columns(2)
            gravidez = coluna_gravidez.checkbox('Grávida', value=base.get('gravidez', False))
            aleitamento = coluna_aleitamento.checkbox('Em aleitamento', value=base.get('aleitamento', False))
            if st.form_submit_button('Guardar episódio'):
                if not indicacao.strip() or idade is None or peso is None or peso<=0:
                    st.error('Preencher contexto, idade e peso positivo.')
                else:
                    st.session_state['paciente']=dict(indicacao=indicacao.strip(),idade=idade,unidade_idade=unidade,peso_kg=peso,funcao_renal=renal,funcao_hepatica=hepatica,gravidez=gravidez,aleitamento=aleitamento)
                    # Uma edição invalida respostas anteriores; evita reutilização entre casos.
                    for chave in list(st.session_state):
                        if chave.startswith('pergunta_') or chave.startswith('confirmacao_'):del st.session_state[chave]
                    st.rerun()
    paciente=st.session_state['paciente']
    if paciente:
        with st.container(border=True):
            st.write(f"**Idade:** {paciente['idade']:g} {paciente['unidade_idade'].lower()}  |  **Peso:** {paciente['peso_kg']:g} kg")
            st.write(paciente['indicacao'])
            st.caption(f"Renal: {paciente['funcao_renal']} | Hepática: {paciente['funcao_hepatica']}")
        por_id={m['id']:m for m in catalogo}
        ids=st.multiselect('Medicamentos e apresentações',list(por_id),format_func=lambda i:por_id[i]['nome']+' — '+por_id[i]['apresentacao'])
        meds=[por_id[i] for i in ids]
        mostrar_informacao_materna(paciente, meds)
        if paciente.get('gravidez') or paciente.get('aleitamento'):
            if meds:
                st.caption('O cálculo disponível neste protótipo é pediátrico.')
            st.stop()
        respostas={}
        try:perguntas=recolher_perguntas(meds)
        except ValueError as erro:st.error(str(erro));st.stop()
        if perguntas:
            st.subheader('Dados adicionais necessários')
            for q in perguntas:
                st.caption('Solicitado por: '+', '.join(q['medicamentos']))
                if q['tipo']=='numero':
                    respostas[q['id']]=st.number_input(q['texto'],min_value=0.0,value=None,format='%g',key='pergunta_'+q['id'],help=q.get('ajuda'))
                else:
                    respostas[q['id']]=st.selectbox(q['texto'],q['opcoes'],key='pergunta_'+q['id'])
                with st.expander('Por que é pedido este dado?'):
                    st.write(q.get('explicacao', 'Este dado é necessário para verificar uma condição documentada para o medicamento selecionado.'))
                    mostrar_fonte(q['fonte'])
        confirmacoes={}
        for m in meds:
            opcoes=['Por confirmar']+sorted({e['condicao']['todas'][0]['valor'] for e in m['esquemas'] if 'todas' in e['condicao']} or {e['condicao']['valor'] for e in m['esquemas']})
            confirmacoes[m['id']]=st.selectbox('Confirme a indicação documentada para '+m['nome'],opcoes,key='confirmacao_'+m['id'])
        st.caption('O contexto permanece em texto livre. A confirmação explícita evita inferir uma indicação clínica a partir de palavras semelhantes.')
        demo=st.checkbox('Cálculo demonstrativo com regras por validar')
        if st.button('Atualizar análise',type='primary',disabled=not meds):
            esquerda,direita=st.columns([1,2.2],gap='large')
            with esquerda:
                st.subheader('Dados usados')
                with st.container(border=True):
                    st.markdown('**Contexto clínico**')
                    st.write(paciente['indicacao'])
                    st.write(f"Idade: {paciente['idade']:g} {paciente['unidade_idade'].lower()}")
                    st.write(f"Peso: {paciente['peso_kg']:g} kg")
                    st.write('Situação renal: ' + paciente['funcao_renal'])
                    st.write('Situação hepática: ' + paciente['funcao_hepatica'])
                with st.expander('Respostas adicionais utilizadas'):
                    for pergunta in perguntas:
                        st.markdown('**' + pergunta['texto'] + '**')
                        st.write(formatar_valor(respostas.get(pergunta['id'])))
            with direita:
                st.subheader('Resultado para rever')
                for m in meds:
                    contexto=dict(paciente,**respostas)
                    contexto['indicacao']=confirmacoes[m['id']]
                    try:r=analisar(contexto,m,demo)
                    except (ValueError,KeyError) as erro:st.error(str(erro));continue
                    with st.container(border=True):
                        st.subheader(m['nome'])
                        for alerta in r['alertas']:
                            (st.error if alerta['tipo']=='bloqueio' else st.info if alerta['tipo']=='informacao' else st.warning)(alerta['texto'])
                            with st.expander('Consultar orientação no RCM'):mostrar_fonte(alerta['fonte'])
                        for pendencia in dict.fromkeys(r['pendencias']):st.write('• '+pendencia)
                        for c in r['calculos']:
                            st.markdown('**Intervalo por administração — '+c['componente']+'**')
                            st.write(f"{c['mg_administracao'][0]:g}–{c['mg_administracao'][1]:g} mg, {c['administracoes_dia']} vezes/dia")
                            if 'ml_administracao' in c:st.write(f"{c['ml_administracao'][0]:.3f}–{c['ml_administracao'][1]:.3f} ml por administração; sem arredondamento para dispositivo.")
                            st.caption('Demonstração matemática; não seleciona nem recomenda uma dose dentro do intervalo.')
                            with st.expander('Como foi calculada e evidência'):
                                st.write(f"Peso usado: {paciente['peso_kg']:g} kg. Quantidade diária dividida por {c['administracoes_dia']} administrações.")
                                diario = c['mg_dia']
                                por_toma = c['mg_administracao']
                                tomas = c['administracoes_dia']
                                st.write(f"Intervalo diário: {diario[0]:g}–{diario[1]:g} mg/dia.")
                                st.write(f"Por administração: {diario[0]:g} ÷ {tomas} = {por_toma[0]:g} mg; {diario[1]:g} ÷ {tomas} = {por_toma[1]:g} mg.")
                                for aviso in c.get('avisos', []): st.warning(aviso)
                                mostrar_fonte(c['fonte'])
                        with st.expander('Informação adicional'):
                            for info in r['informacoes']:st.write(info['titulo']+': '+info['texto'])
                st.warning('Avaliação parcial. Interações globais e outras advertências podem não estar representadas. Ausência de alerta não significa segurança.')
