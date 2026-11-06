# Como publicar o material de uma norma

Este roteiro permite gerar, conferir e publicar uma norma **sem depender de uma IA específica**.
A geração fica com o ChatGPT (ou o NotebookLM). A conferência mecânica fica com os scripts desta pasta.
O Claude entra só na revisão final e nas questões de vigência.

## Arquivos desta pasta

| Arquivo | Para que serve |
|---|---|
| `PROMPT_MODELO.md` | As mensagens para o ChatGPT: levantamento, geração, autorrevisão e correção |
| `valida_norma.py` | Confere o JSON contra o texto oficial e imprime os erros prontos para colar no ChatGPT |
| `monta_material.py` | Grava `dados/normas/<arquivo>.json` e liga o material à norma em `dados/normas.json` |
| `testa_norma.py` | Abre a página num navegador invisível, responde todas as questões e confere o layout no celular |
| `textos/` | Texto extraído dos PDFs oficiais das 65 normas e do Regimento Interno de 2022 (`ri-2022.txt`) |
| `fontes.json` | Quais textos oficiais cada material usa (o validador lê daqui quando você não informa as fontes) |

## Preparação (uma vez só)

1. Python 3.10 ou mais novo.
2. No terminal: `pip install playwright` e depois `python -m playwright install chromium`.
3. Clone o repositório (`git clone https://github.com/luiz-hp/alepa-cargo15.git`) ou use o GitHub Desktop.
4. Crie a pasta `rascunhos/` na raiz do repositório. Ela não vai para o GitHub (está no `.gitignore`).

Todos os comandos abaixo são rodados **na raiz do repositório**.

## Fluxo de cada norma

| Passo | Onde | O que fazer |
|---|---|---|
| 1 | `dados/normas.json` | Anote o `id` da norma (por exemplo `dl-45-2009`), a ementa e o link do PDF |
| 2 | ChatGPT, conversa nova | Mensagem 0 (opcional) e mensagem 1 do `PROMPT_MODELO.md`, colando o texto de `ferramentas/textos/<id>.txt` |
| 3 | ChatGPT | Mensagem 2 (autorrevisão) |
| 4 | Seu computador | Salve a resposta em `rascunhos/<id>-p1.json` e rode `python ferramentas/valida_norma.py rascunhos/<id>-p1.json <id>` |
| 5 | ChatGPT | Se houver ERROS, cole o bloco que o validador imprimiu. Repita os passos 4 e 5 até zerar os erros |
| 6 | Você ou o Claude | Leia os AVISOS e faça a revisão editorial (veja "Quando chamar o Claude") |
| 7 | Seu computador | `python ferramentas/monta_material.py <id> rascunhos/<id>-p1.json --titulo "..." --nota "..."` |
| 8 | Seu computador | `python ferramentas/testa_norma.py <id>` (acrescente `--foto teste.png` para ver a página) |
| 9 | GitHub | Publique `dados/normas/<arquivo>.json`, `dados/normas.json` e `ferramentas/fontes.json` |
| 10 | Seu computador | Um ou dois minutos depois: `python ferramentas/testa_norma.py <id> --site https://luiz-hp.github.io/alepa-cargo15/` |

**Publicar com Git (passo 9):**

```bash
git add dados ferramentas/fontes.json
git commit -m "Adiciona material do DL 45/2009"
git push
```

**Publicar pelo site do GitHub (sem Git):** abra a pasta no GitHub, clique em *Add file → Upload files*,
envie o arquivo e confirme em *Commit changes*. Faça isso para cada arquivo, cada um na sua pasta
(`dados/normas/`, `dados/` e `ferramentas/`).

### Casos especiais do `monta_material.py`

| Situação | Comando |
|---|---|
| Norma em várias partes | `python ferramentas/monta_material.py <id> rascunhos/<id>-p1.json rascunhos/<id>-p2.json` |
| Uma página para várias normas (a norma principal e as que a alteram) | `... <id> <partes> --ids <id2> <id3> --fontes <id> <id2> <id3>` |
| Acrescentar uma parte a uma página que já existe | `... <id> rascunhos/nova-parte.json --arquivo <arquivo> --acrescentar` |
| Refazer uma página | `... <id> <partes> --substituir` |
| Base legal que cita outra norma (por exemplo, o RI 2022) | Inclua o texto em `--fontes` e, na base legal, use um rótulo entre colchetes numa linha própria: `[Regimento Interno de 2022]` |

O `monta_material.py` valida tudo de novo e **não grava nada se houver erros**.

## Quando chamar o Claude

| Situação | Modelo sugerido | O que enviar |
|---|---|---|
| Revisão editorial final de uma norma comum | Sonnet | O JSON já aprovado pelo validador e o pedido abaixo |
| Norma revogada, alterada ou com conflito de vigência | Opus | O JSON, o texto da norma e o texto das normas posteriores relacionadas |

Pedido para a revisão final (conversa nova, um JSON por vez):

```text
Revise o JSON abaixo, da {NORMA}, já aprovado por um validador automático que confere a literalidade da base legal e o formato. Não altere a base_legal. Aponte e corrija: distratores implausíveis ou óbvios; a mesma pegadinha cobrada em mais de uma questão; afirmações nos comentários que o texto não sustenta; resumo impreciso ou incompleto. Sugira notas de vigência e alteração, se houver. Devolva o JSON completo e, depois dele, uma lista curta do que mudou.
```

## Vigência e alterações já apuradas

| Tema | O que vale | Fundamento literal |
|---|---|---|
| Regimento Interno de 1994 | Revogado pela Resolução nº 02/2022, que aprova o Regimento atual (`textos/ri-2022.txt`) | Res. 02/2022, art. 4º: "Revoga-se a Resolução nº 02, de 2 de dezembro de 1994, com suas respectivas alterações." |
| Normas administrativas anteriores | Continuam valendo no que não contrariarem o novo Regimento | Res. 02/2022, art. 3º: "Ficam mantidas as normas administrativas em vigor, no que não contrarie o anexo Regimento Interno [...]" |
| Ouvidoria | A Res. 04/2012 acrescentou os arts. 27-A a 27-E ao Regimento de 1994; hoje a Ouvidoria está nos arts. 33 a 37 do RI 2022 | RI 2022, art. 33: "Compete à Ouvidoria da Assembleia Legislativa:" |
| Procuradoria da Mulher | A Res. 04/2019 não foi revogada expressamente, mas o RI 2022 (arts. 38 a 40) regula de outro modo | RI 2022, art. 39: "A Procuradoria da Mulher será constituída de uma Procuradora e de duas Procuradoras Adjuntas, eleitas pelas Deputadas da Casa [...]" |
| Res. 01/2017 | Trata dos arts. 30 e 31 do Regimento de 1994, que foi revogado: confira a vigência antes de gerar questões | Ementa em `dados/normas.json` |
| Departamento Financeiro (citado no DL 02/2022) | Transformado em Diretoria de Planejamento, Orçamento e Finanças | DL 11/2025, art. 15: "O Departamento Financeiro, fica transformado em Diretoria de Planejamento, Orçamento e Finanças, vinculada à Secretaria Administrativa" |
| Cargos em comissão | O Anexo Único do DL 11/2025 é o quadro consolidado; confira nele vagas e referências (DAS) citadas em normas anteriores | `textos/dl-11-2025.txt` |
| DL 45/2009, DL 03/2012 e DL 05/2015 | O DL 03/2012 altera os DLs 01/2006 e 45/2009; o DL 05/2015 altera os DLs 10/2007 e 03/2012 | Ementas em `dados/normas.json` |

**Não confundir** (mesmo número e ano): DL 04/2012 (PCCR) × Res. 04/2012 (Ouvidoria); DL 02/2022 (férias e licenças-prêmio) × Res. 02/2022 (Regimento Interno).

**Normas com dois PDFs no registro:** Res. 02/1993, Res. 04/1993, Res. 04/1995 (são dois atos com o mesmo número) e Res. 18/1989.
Os textos estão em `textos/<id>.txt` e `textos/<id>__2.txt`.

## Fila

Ordem combinada para as próximas páginas:

1. DL 45/2009, com as alterações do DL 03/2012 e do DL 05/2015, numa página só (`--ids dl-03-2012 dl-05-2015`).
2. DL 02/2017 (Departamento de Memorial do Legislativo).
3. Bateria de vigência: questões sobre o que foi revogado ou substituído (tabela acima).

Normas ainda sem material em 06/11/2026 (45): DL 32/1993, DL 53/1993, DL 29/1995, DL 06/1997, DL 14/1997, DL 36/1997,
DL 41/1997, DL 04/2000, DL 22/2003, DL 01/2006, DL 01/2007, DL 04/2007, DL 10/2007, DL 04/2008, DL 45/2009,
DL 06/2010, DL 03/2012, DL 18/2013, DL 27/2014, DL 05/2015, DL 02/2017, DL 111/2020, DL 15/2021, DL 36/2021,
DL 13/2024, DL 13/2025, Res. 11/1991, Res. 13/1991, Res. 18/1991, Res. 62/1991, Res. 14/1992, Res. 02/1993,
Res. 04/1993, Res. 05/1993, Res. 18/1993, Res. 29/1993, Res. 04/1995, Res. 01/1999, Res. 03/2013, Res. 01/2017,
Res. 05/2017, Res. 02/2021, Res. 01/2025, Res. 02/2025 e Res. 18/1989.
A lista sempre atual é a das normas com `"material": null` em `dados/normas.json`.

## O que o validador confere

| Confere sozinho (ERRO) | Sinaliza para revisão (AVISO) | Não confere: revisão humana ou do Claude |
|---|---|---|
| JSON válido; 5 alternativas; gabarito de A a E | Gabaritos concentrados ou três iguais seguidos | Plausibilidade dos distratores |
| Base legal literal (mostra o trecho oficial mais próximo) | Poucas questões INCORRETA | Mesma pegadinha com palavras diferentes |
| Comentário com 5 linhas e rótulos coerentes com o tipo da questão | Alternativa repetida em outra questão ou quase igual | Afirmações dos comentários que o texto não sustenta |
| Gabarito igual à alternativa que o comentário aponta | Alternativa correta muito mais longa que as demais | Vigência e alterações posteriores |
| Comentário que cita outra letra | Termos suspeitos ou leis que não aparecem no texto | Qualidade do resumo |
| Reticências, "Questão N", marcadores [1] | Aspas simples; tabela com mais de 3 colunas | |
| Blocos do resumo e tabelas com número certo de células | | |
