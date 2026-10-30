/* Site de estudo ALEPA – Cargo 15.
   Lê dados/normas.json (lista do edital) e dados/normas/<id>.json (material de cada norma). */
"use strict";

const main = document.getElementById("conteudo");
let registro = null;          // conteúdo de dados/normas.json
let normaAtual = null;        // id da norma desenhada na tela

/* ---------- utilitários ---------- */

function el(tag, attrs = {}, ...filhos) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") n.className = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const f of filhos.flat(Infinity)) if (f !== null && f !== undefined) n.append(f);
  return n;
}

/* Texto com **negrito** opcional, sempre inserido como texto (nunca como HTML). */
function inline(texto) {
  const partes = String(texto ?? "").split(/\*\*(.+?)\*\*/g);
  return partes.map((p, i) => (i % 2 ? el("strong", {}, p) : p));
}

async function carregarJSON(caminho) {
  let resp;
  try {
    resp = await fetch(caminho, { cache: "no-cache" });
  } catch (e) {
    if (location.protocol === "file:") {
      throw new Error("Abra o site por um servidor local (python -m http.server) ou pelo GitHub Pages. Abrindo o index.html direto do disco, o navegador bloqueia a leitura dos arquivos JSON.");
    }
    throw new Error(`Não foi possível ler ${caminho}.`);
  }
  if (!resp.ok) throw new Error(`Arquivo ${caminho} não encontrado (erro ${resp.status}).`);
  const texto = await resp.text();
  try {
    return JSON.parse(texto);
  } catch (e) {
    throw new Error(`O arquivo ${caminho} não é um JSON válido: ${e.message}`);
  }
}

function embaralhar(lista) {
  for (let i = lista.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [lista[i], lista[j]] = [lista[j], lista[i]];
  }
  return lista;
}

function mostrarErro(msg) {
  main.replaceChildren(
    el("h1", {}, "Algo não carregou"),
    el("p", { class: "aviso" }, msg),
    el("p", {}, el("a", { href: "#/" }, "Voltar para a lista de normas"))
  );
}

function rotuloNorma(n) {
  const sigla = n.tipo === "Decreto Legislativo" ? "DL" : "Res.";
  return `${sigla} ${n.numero}/${n.ano}`;
}

/* ---------- página inicial ---------- */

function desenharInicio() {
  normaAtual = null;
  document.title = "ALEPA Cargo 15: legislação comentada";
  const normas = registro.normas;
  const prontas = normas.filter((n) => n.material).length;
  const pct = Math.round((prontas / normas.length) * 100);

  const listas = el("div");
  const desenharListas = (soComMaterial) => {
    listas.replaceChildren();
    for (const tipo of ["Decreto Legislativo", "Resolução"]) {
      const doTipo = normas.filter((n) => n.tipo === tipo && (!soComMaterial || n.material));
      if (!doTipo.length) continue;
      listas.append(
        el("h2", {}, tipo === "Decreto Legislativo" ? "Decretos Legislativos" : "Resoluções"),
        el("ul", { class: "lista-normas" }, doTipo.map(itemNorma))
      );
    }
    if (!listas.children.length) listas.append(el("p", { class: "aviso" }, "Nenhuma norma com material ainda."));
  };

  const filtro = el("input", { type: "checkbox", id: "filtro" });
  filtro.addEventListener("change", () => desenharListas(filtro.checked));

  main.replaceChildren(
    el("h1", {}, "Legislação da ALEPA para o Cargo 15"),
    el("p", { class: "ementa" }, "Resumos e questões comentadas dos decretos legislativos e resoluções cobrados no edital do Concurso nº 002/2026."),
    el("p", { class: "progresso" }, `${prontas} de ${normas.length} normas com material`),
    el("div", { class: "barra", role: "presentation" }, el("span", { style: `width:${pct}%` })),
    el("label", { class: "filtro", for: "filtro" }, filtro, "Mostrar só as normas com material"),
    listas
  );
  desenharListas(false);
}

function itemNorma(n) {
  const titulo = n.material
    ? el("a", { href: `#/norma/${n.id}` }, rotuloNorma(n))
    : el("span", {}, rotuloNorma(n));
  const situacao = n.material ? "Resumo e questões" : "Sem material ainda";
  return el("li", { class: n.material ? "tem-material" : "" },
    el("div", { class: "num" }, titulo),
    el("div", { class: "desc" },
      inline(n.ementa),
      n.observacao ? el("span", { class: "situacao" }, n.observacao) : null,
      el("span", { class: "situacao" }, situacao),
      n.pdfs.length > 1
        ? el("span", { class: "situacao" }, n.pdfs.map((p, i) => [i ? " | " : "", el("a", { href: p.url, target: "_blank", rel: "noopener" }, p.rotulo)]))
        : null
    )
  );
}

/* ---------- página da norma ---------- */

async function desenharNorma(id, ancora) {
  const meta = registro.normas.find((n) => n.id === id);
  if (!meta || !meta.material) return mostrarErro(`A norma "${id}" não tem material cadastrado em dados/normas.json.`);

  if (normaAtual !== id) {
    main.replaceChildren(el("p", { class: "carregando" }, "Carregando…"));
    const norma = await carregarJSON(meta.material);
    normaAtual = id;
    document.title = `${rotuloNorma(meta)}: resumo e questões`;
    main.replaceChildren(...conteudoNorma(meta, norma));
  }
  const alvo = ancora && document.getElementById(ancora);
  if (alvo) alvo.scrollIntoView({ block: "start" });
  else { window.scrollTo(0, 0); main.focus({ preventScroll: true }); }
}

function conteudoNorma(meta, norma) {
  const partes = Array.isArray(norma.partes) ? norma.partes : [];
  const nodos = [
    el("a", { class: "voltar", href: "#/" }, "Todas as normas"),
    el("h1", {}, norma.titulo || rotuloNorma(meta)),
    el("p", { class: "ementa" }, inline(norma.ementa || meta.ementa)),
  ];
  const infos = [];
  if (norma.fonte) infos.push(el("li", {}, el("a", { href: norma.fonte, target: "_blank", rel: "noopener" }, "Texto oficial (PDF do Banco de Leis da ALEPA)")));
  for (const a of norma.alteracoes || []) infos.push(el("li", {}, inline(a)));
  if (infos.length) nodos.push(el("ul", { class: "meta" }, infos));

  if (!partes.length) {
    nodos.push(el("p", { class: "aviso" }, "Material em preparação. Volte em breve."));
    return nodos;
  }

  nodos.push(el("nav", { class: "sumario", "aria-label": "Partes desta norma" },
    el("strong", {}, "Nesta página"),
    el("ol", {}, partes.map((p, i) =>
      el("li", {},
        el("a", { href: `#/norma/${meta.id}/parte-${i + 1}` }, p.titulo || `Parte ${i + 1}`),
        p.artigos ? ` (${p.artigos})` : ""
      )))
  ));
  partes.forEach((p, i) => nodos.push(...conteudoParte(p, i + 1)));
  return nodos;
}

function conteudoParte(parte, n) {
  const questoes = Array.isArray(parte.questoes) ? parte.questoes : [];
  const nodos = [
    el("h2", { id: `parte-${n}`, tabindex: "-1" }, `Parte ${n}: ${parte.titulo || ""}`),
    parte.artigos ? el("p", { class: "intervalo" }, parte.artigos) : null,
    el("h3", {}, "Resumo"),
    el("div", { class: "resumo" }, (parte.resumo || []).map(blocoResumo)),
  ];
  if (questoes.length) {
    nodos.push(el("h3", { id: `parte-${n}-questoes` }, `Questões da parte ${n}`));
    nodos.push(bateria(questoes, n));
  }
  return nodos;
}

function blocoResumo(b) {
  switch (b && b.tipo) {
    case "texto":
      return el("p", {}, inline(b.conteudo));
    case "lista":
      return el("ul", {}, (b.itens || []).map((i) => el("li", {}, inline(i))));
    case "tabela":
      return el("div", { class: "tabela" },
        el("table", {},
          el("thead", {}, el("tr", {}, (b.colunas || []).map((c) => el("th", { scope: "col" }, inline(c))))),
          el("tbody", {}, (b.linhas || []).map((l) => el("tr", {}, l.map((c) => el("td", {}, inline(c))))))
        ));
    case "atencao":
      return el("p", { class: "atencao" }, el("strong", {}, "Atenção: "), inline(b.conteudo));
    default:
      return el("p", { class: "erro-dado" }, `Bloco de resumo com tipo desconhecido: ${JSON.stringify(b && b.tipo)}`);
  }
}

/* ---------- questões ---------- */

function bateria(questoes, nParte) {
  const respostas = new Array(questoes.length).fill(null); // true = acerto, false = erro
  const cartao = el("ol", { class: "cartao", "aria-label": "Seu desempenho nesta bateria" });
  const placarTexto = el("span", { class: "placar-texto" });
  const caixa = el("div");

  const atualizarPlacar = () => {
    const feitas = respostas.filter((r) => r !== null).length;
    const acertos = respostas.filter((r) => r === true).length;
    placarTexto.textContent = feitas
      ? `${acertos} de ${feitas} ${feitas === 1 ? "acerto" : "acertos"} (${questoes.length} questões)`
      : `${questoes.length} questões`;
    cartao.replaceChildren(...respostas.map((r, i) =>
      el("li", { class: r === null ? "" : r ? "ok" : "nao", title: `Questão ${i + 1}` }, String(i + 1))));
  };

  const montar = () => {
    respostas.fill(null);
    caixa.replaceChildren(...questoes.map((q, i) =>
      questao(q, i + 1, nParte, (acertou) => { respostas[i] = acertou; atualizarPlacar(); })));
    atualizarPlacar();
  };

  const refazer = el("button", { class: "botao", type: "button" }, "Refazer questões");
  refazer.addEventListener("click", () => {
    montar();
    document.getElementById(`parte-${nParte}-questoes`)?.scrollIntoView({ block: "start" });
  });

  montar();
  return el("div", {}, caixa, el("div", { class: "placar" }, placarTexto, cartao, refazer));
}

function questao(q, num, nParte, aoResponder) {
  const letras = q && q.alternativas ? Object.keys(q.alternativas) : [];
  const problema = !q || !q.enunciado ? "sem enunciado"
    : letras.length < 2 ? "sem alternativas"
    : !letras.includes(q.gabarito) ? `gabarito "${q.gabarito}" não corresponde a nenhuma alternativa`
    : null;

  const bloco = el("article", { class: "questao", "aria-labelledby": `q${nParte}-${num}` },
    el("p", { class: "questao-num", id: `q${nParte}-${num}` }, `Questão ${num}`),
    el("p", { class: "enunciado" }, inline(q && q.enunciado))
  );
  if (problema) {
    bloco.append(el("p", { class: "erro-dado" }, `Esta questão está com erro no JSON: ${problema}.`));
    return bloco;
  }

  /* Embaralha as alternativas a cada exibição (evita decorar a letra do gabarito)
     e reetiqueta A, B, C... na nova ordem, inclusive no comentário ("X) ..."). */
  const ordem = embaralhar([...letras]);
  const novaLetra = {};
  ordem.forEach((original, i) => { novaLetra[original] = letras[i]; });
  const gabarito = novaLetra[q.gabarito];
  const comentario = String(q.comentario || "").split(/\n+/).filter((l) => l.trim())
    .map((l) => l.replace(/^\s*([A-E])\)/, (m, x) => (novaLetra[x] ? `${novaLetra[x]})` : m)))
    .sort((a, b) => {
      const la = /^([A-E])\)/.exec(a), lb = /^([A-E])\)/.exec(b);
      return la && lb ? la[1].localeCompare(lb[1]) : 0;
    });

  const botoes = ordem.map((original, i) => {
    const letra = letras[i];
    return el("button", { class: "alt", type: "button", "data-letra": letra, "aria-pressed": "false" },
      el("span", { class: "bolha", "aria-hidden": "true" }, letra),
      el("span", {}, el("span", { class: "pular" }, `Alternativa ${letra}: `), inline(q.alternativas[original]))
    );
  });
  const resultado = el("div", { "aria-live": "polite" });

  const responder = (letra) => {
    const acertou = letra === gabarito;
    for (const b of botoes) {
      b.disabled = true;
      const l = b.dataset.letra;
      if (l === letra) { b.classList.add("escolhida"); b.setAttribute("aria-pressed", "true"); }
      if (l === gabarito) b.classList.add("correta");
      else if (l === letra) b.classList.add("incorreta");
    }
    const base = q.base_legal || {};
    resultado.replaceChildren(
      el("p", { class: `veredito ${acertou ? "ok" : "nao"}` },
        acertou ? `Certo. Gabarito: ${gabarito}.` : `Errado. Você marcou ${letra}; o gabarito é ${gabarito}.`),
      el("div", { class: "comentario" }, comentario.map((p) => el("p", {}, inline(p)))),
      base.texto ? el("blockquote", { class: "base" },
        base.dispositivo ? el("cite", {}, base.dispositivo) : null,
        inline(base.texto)) : null
    );
    aoResponder(acertou);
  };
  botoes.forEach((b) => b.addEventListener("click", () => responder(b.dataset.letra)));

  bloco.append(el("ul", { class: "alternativas" }, botoes.map((b) => el("li", {}, b))), resultado);
  return bloco;
}

/* ---------- roteamento ---------- */

async function rotear() {
  try {
    if (!registro) registro = await carregarJSON("dados/normas.json");
    const [, rota, id, ancora] = (location.hash || "#/").split("/");
    if (rota === "norma" && id) await desenharNorma(id, ancora);
    else { desenharInicio(); window.scrollTo(0, 0); }
  } catch (e) {
    normaAtual = null;
    mostrarErro(e.message);
  }
}

window.addEventListener("hashchange", rotear);
rotear();
