const el = id => document.getElementById(id);
const normalizar = texto => texto.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();
const numero = valor => valor === '' ? null : Number(valor);
const formatar = valor => valor.toLocaleString('pt-PT', {maximumFractionDigits: 3});
let catalogo = [];
let revisao = 0;

function criar(tag, texto, classe) {
    const item = document.createElement(tag);
    item.textContent = texto;
    if (classe) item.className = classe;
    return item;
}

function fonte(dados) {
    const texto = [dados.documento, dados.secao && 'Secção ' + dados.secao,
        dados.paginas?.length && 'p. ' + dados.paginas.join(', ')].filter(Boolean).join(' · ');
    const linha = criar('p', texto, 'fonte');
    if (dados.url && /^https:\/\//.test(dados.url)) {
        const link = criar('a', 'Consultar fonte');
        link.href = dados.url;
        linha.append(' · ', link);
    }
    return linha;
}

function atualizarOpcoes() {
    const area = el('sugestoes');
    const busca = normalizar(el('pesquisa').value.trim());
    area.replaceChildren();
    if (busca.length < 2) return;
    const termos = busca.split(/\s+/).filter(termo => termo !== '+');
    if (!termos.length) return;
    const encontrados = catalogo.filter(m => {
        const texto = normalizar([m.nome, m.substancia_ativa, m.apresentacao].join(' '));
        return termos.every(termo => texto.includes(termo));
    });
    if (!encontrados.length) {
        area.append(criar('p', 'Sem resultados no catálogo carregado.'));
        return;
    }
    for (const m of encontrados.slice(0, 8)) {
        const botao = criar('button', m.nome + ' · ' + m.apresentacao, 'sugestao');
        botao.type = 'button';
        botao.addEventListener('click', () => {
            el('medicamento').value = m.id;
            el('pesquisa').value = m.nome;
            area.replaceChildren();
            atualizarFicha();
        });
        area.append(botao);
    }
    if (encontrados.length > 8) area.append(criar('p', 'Escreve mais para afinar a pesquisa.'));
}

function pergunta(id, texto, opcoes) {
    const label = criar('label', texto);
    const campo = document.createElement(opcoes ? 'select' : 'input');
    campo.name = id;
    if (opcoes) {
        campo.append(new Option('Por confirmar', ''), ...opcoes.map(opcao => new Option(opcao)));
    } else {
        campo.type = 'number';
        campo.min = '0';
        campo.step = 'any';
    }
    label.append(campo);
    el('perguntas').append(label);
}

function atualizarFicha() {
    const m = catalogo.find(item => item.id === el('medicamento').value);
    el('titulo').textContent = m?.nome ?? 'Ficha do medicamento';
    el('apresentacao').textContent = [m?.apresentacao, m?.fonte_catalogo].filter(Boolean).join(' · ');
    el('materna').replaceChildren();
    el('perguntas').replaceChildren();
    if (m) {
        const contextos = [['gravidez', 'Gravidez'], ['aleitamento', 'Aleitamento']];
        const ativos = contextos.filter(([id]) => el(id).checked);
        for (const [id, titulo] of ativos) {
            const nota = m.informacao_materna?.[id];
            const painel = criar('section', '', 'nota');
            painel.append(criar('h2', titulo), criar('p', nota?.texto ?? 'Informação ainda não registada para esta apresentação.'));
            if (nota) painel.append(fonte(nota.fonte), criar('p', 'Transcrição por rever', 'fonte'));
            el('materna').append(painel);
        }
        if (!ativos.length && m.id === 'amoxicilina_250') {
            pergunta('tfg', 'TFG absoluta em mL/min');
            pergunta('dialise', 'Em diálise?', ['Não', 'Sim']);
            pergunta('alergia', 'Alergia relevante a penicilinas ou reação imediata grave a outro beta-lactâmico?', ['Não', 'Sim']);
        } else if (!ativos.length && m.esquemas?.length) {
            pergunta('funcao_renal', 'Situação renal', m.opcoes_funcao_renal ?? ['Sem compromisso conhecido', 'Compromisso renal referido']);
            pergunta('funcao_hepatica', 'Situação hepática', ['Sem compromisso conhecido', 'Compromisso hepático referido']);
            const indicacoes = m.esquemas.flatMap(e => [e.condicao, ...(e.condicao.todas ?? [])])
                .filter(c => c.parametro === 'indicacao').map(c => c.valor);
            if (m.indicacao_demo) {
                el('perguntas').append(criar('p', 'Cenário demonstrativo · ' + m.indicacao_demo, 'fonte'));
            } else if (indicacoes.length) {
                pergunta('indicacao', 'Indicação', [...new Set(indicacoes)]);
            }
            for (const q of m.perguntas ?? []) pergunta(q.id, q.texto, q.tipo === 'numero' ? null : q.opcoes);
        }
    }
    atualizarCalculo();
}

async function atualizarCalculo() {
    const pedido = ++revisao;
    const resultado = el('resultado');
    resultado.replaceChildren();
    const caso = {
        medicamento: el('medicamento').value, idade: numero(el('idade').value),
        unidade_idade: el('unidade_idade').value, peso_kg: numero(el('peso').value),
        gravidez: el('gravidez').checked, aleitamento: el('aleitamento').checked,
        demonstracao: true,
    };
    if (!caso.medicamento || caso.gravidez || caso.aleitamento) return;
    for (const campo of el('perguntas').querySelectorAll('input,select')) {
        caso[campo.name] = campo.type === 'number' ? numero(campo.value) : campo.value || null;
    }
    try {
        const resposta = await fetch('/api/analisar', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(caso),
        });
        const dados = await resposta.json();
        if (pedido !== revisao) return;
        if (!resposta.ok) throw new Error(dados.erro);
        if (dados.faixa_etaria) {
            resultado.append(criar('p', 'Classificação etária · ' + dados.faixa_etaria, 'fonte'));
        }
        if (!dados.calculos?.length) {
            const estado = criar('section', '', 'nota');
            estado.append(criar('h2', 'Dose ainda indisponível'));
            for (const motivo of dados.pendencias ?? []) estado.append(criar('p', motivo));
            resultado.append(estado);
        }
        const intervalo = valores => valores[0] === valores[1] ? formatar(valores[0]) : valores.map(formatar).join('–');
        for (const c of dados.calculos ?? []) {
            const cartao = criar('section', '', 'dose');
            cartao.append(criar('h2', c.nome), criar('strong', intervalo(c.mg_administracao) + ' mg por toma'),
                criar('p', c.componente + ' · ' + c.administracoes_dia + ' toma(s)/dia · ' + intervalo(c.mg_dia) + ' mg/dia'));
            if (c.ml_administracao) cartao.append(criar('p', intervalo(c.ml_administracao) + ' mL por toma'));
            if (c.explicacao) cartao.append(criar('p', c.explicacao));
            cartao.append(fonte(c.fonte));
            resultado.append(cartao);
        }
        for (const alerta of dados.alertas ?? []) {
            const bloco = criar('div', alerta.texto, 'nota');
            bloco.append(fonte(alerta.fonte));
            resultado.append(bloco);
        }
        for (const info of dados.informacoes ?? []) {
            const painel = criar('details', '', 'nota');
            painel.append(criar('summary', info.titulo), criar('p', info.texto));
            if (info.fonte) painel.append(fonte(info.fonte));
            resultado.append(painel);
        }
        if (dados.calculos?.length) {
            for (const aviso of dados.pendencias ?? []) resultado.append(criar('p', aviso));
        }
    } catch (erro) {
        if (pedido === revisao) resultado.append(criar('p', erro.message));
    }
}

el('pesquisa').addEventListener('input', () => {
    if (el('medicamento').value) {
        el('medicamento').value = '';
        atualizarFicha();
    }
    atualizarOpcoes();
});
el('pesquisa').addEventListener('keydown', evento => {
    if (evento.key === 'Escape') el('sugestoes').replaceChildren();
    if (evento.key === 'ArrowDown') el('sugestoes').querySelector('button')?.focus();
});
for (const id of ['medicamento', 'gravidez', 'aleitamento']) el(id).addEventListener('change', atualizarFicha);
for (const id of ['idade', 'unidade_idade', 'peso', 'perguntas']) el(id).addEventListener('input', atualizarCalculo);
fetch('/api/catalogo').then(r => r.json()).then(dados => {
    if (!Array.isArray(dados)) throw new Error('Catálogo indisponível');
    catalogo = dados;
    atualizarOpcoes();
}).catch(() => el('resultado').append(criar('p', 'Não foi possível carregar o catálogo.')));
