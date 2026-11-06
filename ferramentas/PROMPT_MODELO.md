# Prompts para gerar o material de uma norma

São quatro mensagens, todas na **mesma conversa nova** do ChatGPT (ou do NotebookLM), uma conversa por norma:

| Mensagem | Quando | Para quê |
|---|---|---|
| 0. Levantamento | Opcional, antes de gerar | O próprio ChatGPT lista números, prazos, órgãos e listas fechadas do texto; a lista vira os "pontos de exatidão" da mensagem 1 |
| 1. Geração | Sempre | Gera a parte em JSON |
| 2. Autorrevisão | Sempre, logo depois | O ChatGPT corrige os defeitos editoriais mais comuns |
| 3. Correção | Só se o validador acusar ERROS | O validador imprime o texto pronto; basta colar |

**Dica que evita a maioria dos erros de literalidade:** cole na conversa o texto de `ferramentas/textos/<id>.txt`, além de anexar o PDF.
O validador compara a base legal com esse arquivo; se o ChatGPT copiar dele, os trechos batem.

Normas longas: divida em partes de 15 a 25 artigos (10 a 16 questões por parte) e gere cada parte numa mensagem 1 separada,
sempre na mesma conversa. Cada parte é salva em seu próprio arquivo (`rascunhos/<id>-p1.json`, `-p2` etc.).

---

## Mensagem 0 — Levantamento (opcional)

```text
Use exclusivamente o texto abaixo, do {NORMA}. Liste, transcrevendo literalmente e indicando o dispositivo:
1) todos os números, quantidades, percentuais, prazos e datas;
2) todos os órgãos, cargos e autoridades, com o que cada um faz;
3) todas as listas fechadas (incisos, alíneas, requisitos, princípios), com a quantidade de itens;
4) palavras que restringem ou ampliam (somente, preferencialmente, vedado, exclusivamente, inclusive);
5) remissões a outras normas e trechos com redação ambígua, grafia incomum ou aparente contradição.
Não interprete nem complete nada com conhecimento externo.

{COLE AQUI O TEXTO DE ferramentas/textos/<id>.txt}
```

---

## Mensagem 1 — Geração

Preencha os campos entre chaves. Em `{PONTOS_DE_EXATIDAO}`, use a resposta da mensagem 0
(ou apague a seção, se não quiser fazer o levantamento).

```text
Você vai produzir material de estudo para o concurso da ALEPA 2026 (banca Fundação CETAP), cargo Analista Legislativo – Assistência Legislativa, usando EXCLUSIVAMENTE a fonte fornecida: {NORMA}. Não use nenhuma outra lei nem conhecimento externo.

IMPORTANTE: responda SOMENTE com o bloco de código JSON descrito no final. Não escreva texto, títulos, tabelas em Markdown nem sugestões antes ou depois do JSON.

TAREFA: gerar uma parte intitulada "{TITULO_DA_PARTE}", que abrange {ARTIGOS}.

DISTRIBUIÇÃO OBRIGATÓRIA DAS {N} QUESTÕES
{DISTRIBUICAO — por exemplo:
- Art. 1º (objeto): 1
- Art. 2º, incisos I a X (competências): 3
- Arts. 3º a 5º (organização): 2
- 1 caso prático que combine artigos}

PONTOS QUE EXIGEM EXATIDÃO (a fonte é a única referência)
{PONTOS_DE_EXATIDAO}

TIPOS DE QUESTÃO
- Pelo menos 35% das questões no formato "assinale a alternativa INCORRETA".
- Estilo de banca: troca de órgãos, de números e prazos, de marcos (publicação x efeitos), de critérios, de qualificativos (somente x preferencialmente; totalmente x parcialmente) e de itens de listas fechadas.

REGRAS DAS QUESTÕES
1. 5 alternativas (A a E), apenas uma correta, todas de tamanho parecido e plausíveis. Não use "todas as anteriores", "nenhuma das anteriores", "apenas I e II" nem itens em algarismos romanos: o site embaralha as alternativas. Não use distratores absurdos (Governador, Polícia Federal, multas, Justiça Federal, prazos sem relação com o texto).
2. Cada pegadinha (troca de número, órgão, prazo, critério ou qualificativo) só pode ser o erro de UMA questão.
3. Nas questões INCORRETA, as quatro alternativas verdadeiras devem afirmar quatro coisas diferentes; nada de duas paráfrases do mesmo trecho.
4. Nenhuma alternativa pode ser verdadeira por obviedade (exemplo: "a norma alcança os servidores da Assembleia Legislativa") nem conter expressão vaga ou sem sentido jurídico.
5. A alternativa errada nasce de uma troca pontual e plausível (palavra, número, órgão, prazo, advérbio), e não de uma frase artificial que nenhuma banca escreveria.
6. Não use, numa alternativa, uma palavra que o texto reserva para outro conceito.
7. Comentário: uma linha por alternativa, na ordem, começando com "A) CORRETA." ou "A) INCORRETA." (nas questões INCORRETA, use "A) CORRETA (opção verdadeira)." e "A) INCORRETA (gabarito)."), com o motivo e o dispositivo. Nunca cite outra letra dentro do comentário. Não afirme nada que a fonte não diga.
8. base_legal: dispositivo e trecho LITERAL completo, copiado da fonte sem alterar nenhuma palavra, nenhum sinal e nenhuma pontuação (inclusive erros de grafia do original), sem reticências e sem rótulos antes do texto (escreva "§ 1º O servidor...", e não "Art. 4º, § 1º O servidor..."; o artigo vai no campo "dispositivo"). Se usar mais de um dispositivo, transcreva todos, separados por \n. A base_legal deve sustentar TODAS as alternativas. Nenhuma questão pode ficar sem base_legal.
9. Gabaritos distribuídos entre A e E, sem passar de 30% em uma mesma letra.
10. Escreva tudo em português, sem notas internas e sem marcadores de citação como [1]. Não numere os enunciados ("Questão 1 —").

RESUMO
- No máximo 250 palavras, em blocos curtos. Use **negrito** para números, órgãos, prazos e palavras-chave.
- Tipos de bloco permitidos: "texto", "lista" (com "itens"), "tabela" e "atencao".
- Tabelas com no máximo 3 colunas e células curtas (o site é lido no celular); na primeira coluna, palavras de até 12 letras.
- 1 bloco "atencao" com as 3 pegadinhas mais prováveis.

FORMATO DE SAÍDA
Responda SOMENTE com um bloco de código JSON válido. Aspas duplas dentro de textos devem ser escapadas (\"). Estrutura:

{
  "titulo": "{TITULO_DA_PARTE}",
  "artigos": "{ARTIGOS}",
  "resumo": [
    { "tipo": "texto", "conteudo": "Parágrafo do resumo." },
    { "tipo": "lista", "itens": ["item", "item"] },
    { "tipo": "tabela", "colunas": ["Tema", "Regra", "Art."], "linhas": [["texto", "texto", "texto"]] },
    { "tipo": "atencao", "conteudo": "Pegadinhas mais prováveis." }
  ],
  "questoes": [
    {
      "enunciado": "De acordo com ...",
      "alternativas": { "A": "texto", "B": "texto", "C": "texto", "D": "texto", "E": "texto" },
      "gabarito": "C",
      "comentario": "A) INCORRETA. Motivo.\nB) INCORRETA. Motivo.\nC) CORRETA. Motivo.\nD) INCORRETA. Motivo.\nE) INCORRETA. Motivo.",
      "base_legal": { "dispositivo": "Art. 1º, parágrafo único", "texto": "Parágrafo único. Texto literal." }
    }
  ]
}

Antes de responder, confira: são {N} questões; a distribuição segue a lista acima; há pelo menos 35% de questões INCORRETA e 1 caso prático; os gabaritos estão espalhados; cada gabarito confere com a base_legal; nenhuma questão está sem base_legal; não há reticências; o JSON é válido.

TEXTO DA NORMA:
{COLE AQUI O TEXTO DE ferramentas/textos/<id>.txt}
```

---

## Mensagem 2 — Autorrevisão

Cole logo depois da resposta da mensagem 1, sem alterar nada:

```text
Revise o JSON que você acabou de gerar, comparando-o com o texto oficial da norma. Não crie questões novas: corrija somente o que violar as regras abaixo e responda apenas com o JSON completo corrigido, sem nenhum texto fora do bloco.

1. Cada base_legal deve ser cópia literal do texto oficial (palavras, sinais, pontuação e erros de grafia do original), sem reticências e sem rótulos antes do texto. Cada linha deve começar no início de um dispositivo (Art., §, Parágrafo único, inciso ou alínea).
2. A base_legal deve sustentar TODAS as alternativas da questão; se alguma alternativa depender de outro dispositivo, acrescente-o, também literal.
3. Cada pegadinha (troca de número, órgão, prazo, critério ou qualificativo) só pode ser o erro de UMA questão. Se a mesma troca aparecer como erro em duas questões, substitua o distrator por outro ponto do mesmo artigo.
4. Nas questões "INCORRETA", as quatro alternativas verdadeiras devem afirmar quatro coisas diferentes; não pode haver duas paráfrases do mesmo trecho.
5. Nenhuma alternativa pode ser verdadeira por obviedade (exemplo: "a norma alcança os servidores da Assembleia Legislativa") nem conter expressão vaga ou sem sentido jurídico.
6. A alternativa errada deve nascer de uma troca pontual e plausível (palavra, número, órgão, prazo, advérbio), e não de uma frase artificial que nenhuma banca escreveria.
7. Não use, numa alternativa, uma palavra que o texto reserva para outro conceito (exemplo: "antiguidade" é dos períodos vencidos; "ordem cronológica" é dos requerimentos).
8. Comentário: 5 linhas, de A a E, iniciadas por "X) CORRETA." ou "X) INCORRETA." (nas questões INCORRETA: "X) CORRETA (opção verdadeira)." e "X) INCORRETA (gabarito)."), indicando o dispositivo, sem citar outras letras e sem afirmar nada que o texto não diga.
9. Gabaritos distribuídos entre A e E, sem passar de 30% em uma mesma letra.
10. Não acrescente conteúdo de outras leis além do que o próprio texto da norma diz.
```

---

## Mensagem 3 — Correção

Não precisa escrever: quando há ERROS, o `valida_norma.py` imprime no fim um bloco que começa com
"O validador automático encontrou os problemas abaixo". Copie o bloco inteiro e cole na mesma conversa.
