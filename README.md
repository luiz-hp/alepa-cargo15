# Legislação da ALEPA para o Cargo 15

Site de estudo com resumos e questões comentadas dos decretos legislativos e resoluções cobrados no
Concurso Público nº 002/2026 da ALEPA, Cargo 15 (Analista Legislativo – Assistência Legislativa).

## Estrutura

```
index.html                  página única do site
assets/estilo.css           aparência
assets/app.js               lógica (lista de normas, resumos e questões)
dados/normas.json           as 65 normas do edital, com ementa e link oficial
dados/normas/<id>.json      material de cada norma (resumo + questões)
prompts/notebooklm.md       prompt antigo do NotebookLM (substituído por ferramentas/PROMPT_MODELO.md)
ferramentas/                validador, montador, teste, textos oficiais e roteiro de publicação
```

O site não tem etapa de compilação: tudo o que está no repositório é publicado como está.

## Como incluir o material de uma norma

Siga o roteiro de [`ferramentas/COMO_PUBLICAR.md`](ferramentas/COMO_PUBLICAR.md). Em resumo:

1. Gere a parte no ChatGPT com as mensagens de `ferramentas/PROMPT_MODELO.md` e salve em `rascunhos/`.
2. Confira: `python ferramentas/valida_norma.py rascunhos/<id>-p1.json <id>`.
3. Monte: `python ferramentas/monta_material.py <id> rascunhos/<id>-p1.json`.
4. Teste: `python ferramentas/testa_norma.py <id>`.
5. Publique `dados/normas/<arquivo>.json`, `dados/normas.json` e `ferramentas/fontes.json`.
   O site atualiza sozinho em um ou dois minutos.

## Ver o site no computador antes de publicar

O navegador não deixa a página ler os arquivos JSON quando o `index.html` é aberto com dois cliques.
Use um servidor local:

```bash
cd alepa-cargo15
python -m http.server 8000
```

Depois abra http://localhost:8000 no navegador.

## Fonte dos textos

Banco de Leis da Assembleia Legislativa do Estado do Pará: https://bancodeleis.alepa.pa.gov.br/
Os textos não substituem a publicação no Diário Oficial.
