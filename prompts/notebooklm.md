# Prompt para o NotebookLM

Suba no NotebookLM apenas o texto da norma (de preferência a redação vigente, sem redações revogadas).
Rode o prompt uma vez para cada parte, trocando os campos entre colchetes.

| Campo | O que colocar | Exemplo |
|---|---|---|
| `[NORMA]` | Nome da norma | Decreto Legislativo nº 70/1990 |
| `[PARTE]` | Número da parte | 1 |
| `[TÍTULO]` | Título da parte | Quadros, cargos e estrutura básica |
| `[ARTIGOS]` | Intervalo de artigos | Arts. 1º a 10 |

```text
Você vai produzir material de estudo para o concurso da ALEPA 2026 (banca Fundação CETAP), cargo Analista Legislativo – Assistência Legislativa, usando EXCLUSIVAMENTE a fonte carregada ([NORMA], redação vigente).

TAREFA: gerar a PARTE [PARTE] do material, intitulada "[TÍTULO]", que abrange os [ARTIGOS].

REGRAS DE CONTEÚDO
1. Use somente o texto da fonte. Não use conhecimento externo, jurisprudência nem outras normas.
2. Resumo: no máximo 250 palavras. Destaque prazos, percentuais, quantidades, exceções e listas taxativas.
3. Questões: 8 questões de múltipla escolha, com 5 alternativas (A a E) e apenas uma correta. Distribua o gabarito entre as letras. Use o estilo de banca: troca de palavras-chave (ex.: "preferencialmente" x "obrigatoriamente"), prazos e percentuais alterados, exceções invertidas e conceitos trocados entre si.
4. Cada questão deve ter: (a) comentário explicando por que a correta está certa e por que cada alternativa errada está errada; (b) base legal com o dispositivo e o trecho LITERAL copiado da fonte, sem alterar nenhuma palavra.
5. Cubra todos os artigos do intervalo e não use o mesmo dispositivo em mais de duas questões.

FORMATO DE SAÍDA
Responda SOMENTE com um bloco de código JSON válido, sem nenhum texto antes ou depois e sem marcadores de citação como [1]. Aspas duplas dentro de textos devem ser escapadas (\"). Use exatamente esta estrutura (os tipos de bloco do resumo podem ser repetidos ou omitidos):

{
  "titulo": "[TÍTULO]",
  "artigos": "[ARTIGOS]",
  "resumo": [
    { "tipo": "texto", "conteudo": "Parágrafo do resumo." },
    { "tipo": "lista", "itens": ["Item 1", "Item 2"] },
    { "tipo": "tabela", "colunas": ["Coluna 1", "Coluna 2"], "linhas": [["valor", "valor"]] },
    { "tipo": "atencao", "conteudo": "Ponto que costuma virar pegadinha." }
  ],
  "questoes": [
    {
      "enunciado": "De acordo com o [NORMA], ...",
      "alternativas": { "A": "...", "B": "...", "C": "...", "D": "...", "E": "..." },
      "gabarito": "C",
      "comentario": "...",
      "base_legal": { "dispositivo": "Art. 5º, § 1º", "texto": "trecho literal da fonte" }
    }
  ]
}
```

## Antes de publicar

- Confira cada gabarito lendo o dispositivo citado em `base_legal`. IA pode errar.
- Se aparecer algum `[1]`, `[2]` etc. no meio do texto, apague.
- Valide o JSON (por exemplo, colando em https://jsonlint.com). Se houver erro, o site mostra a mensagem com a posição do problema.
