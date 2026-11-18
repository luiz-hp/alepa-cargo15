#!/usr/bin/env python3
"""Monta a mensagem pronta para o ChatGPT gerar as questões de um bloco da Constituição do Estado do Pará.

Uso, a partir da pasta do repositório:
  python ferramentas/prompt_ce.py              lista os blocos
  python ferramentas/prompt_ce.py 1 --abrir    grava rascunhos/prompt-ce-b1.txt e o abre no Bloco de Notas

O arquivo gerado já traz as regras e o trecho da Constituição (ferramentas/textos/ce-pa.txt). Copie tudo e
cole numa conversa nova do ChatGPT. A mensagem de autorrevisão fica em rascunhos/prompt-ce-revisao.txt.

Na primeira execução, a ferramenta também:
  - acrescenta a Constituição do Estado do Pará ao registro (dados/normas.json), se ainda não estiver lá;
  - grava rascunhos/ce-notas.txt, com as notas de alteração e vigência do topo da página.
"""
import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
REPO = PASTA.parent
TEXTO = PASTA / "textos" / "ce-pa.txt"
RASCUNHOS = REPO / "rascunhos"
REGISTRO = REPO / "dados" / "normas.json"
MATERIAL = REPO / "dados" / "normas" / "ce-pa.json"
ARTIGO = re.compile(r"^Art\.\s?(\d+)")

ID = "ce-pa"
TITULO_PAGINA = "Constituição do Estado do Pará (artigos do edital)"

ENTRADA_REGISTRO = {
    "id": ID,
    "tipo": "Constituição Estadual",
    "numero": "",
    "ano": 1989,
    "ementa": "Constituição do Estado do Pará, promulgada em 5 de outubro de 1989. "
              "Artigos cobrados no edital: 11, 86, 90, 92 a 116, 121, 161, 162, 168 e 341.",
    "pdfs": [{
        "rotulo": "Texto oficial (compilação da ALEPA, atualizada até a EC nº 72/2018)",
        "url": "https://www.alepa.pa.gov.br/Content/Docs/constituicao-estado-do-para.pdf",
    }],
    "material": None,
}

NOTAS = [
    "Texto dos artigos do edital atualizado até a **Emenda Constitucional nº 101/2026**. A compilação oficial da ALEPA "
    "(link acima) vai até a EC nº 72/2018; as alterações posteriores estão listadas abaixo.",
    "**EC nº 78/2019**: incluiu o Defensor Público Geral do Estado no art. 92, XXXIV (crimes de responsabilidade julgados "
    "pela Assembleia) e no art. 161, I, \"c\" (mandado de segurança no Tribunal de Justiça); no art. 162, IV, o "
    "\"Procurador-Geral da Defensoria Pública\" passou a ser o \"Defensor Público Geral\".",
    "**EC nº 80/2019**: nova redação do art. 90, parágrafo único (assessoramento da Assembleia pela Procuradoria, "
    "Consultoria Técnica, Assessoria Técnica e Coordenadoria Técnico Legislativo).",
    "**EC nº 81/2020**: acrescentou o §\u00a011 ao art. 99 (sessões e reuniões em períodos excepcionais, inclusive de forma remota).",
    "**EC nº 82/2020**: incluiu a Polícia Penal no art. 113, §\u00a01º, II (leis orgânicas que são leis complementares).",
    "**EC nº 87/2023**: revogou o art. 92, XXIV (autorização para o Governador e o Vice-Governador se ausentarem do País).",
    "**EC nº 96/2025**: no art. 105, II, \"b\", trocou \"inatividade\" por \"aposentadoria\".",
    "**EC nº 101/2026**: nova redação do art. 168 (Justiça Militar: em primeiro grau, Juízes de Direito e Conselhos de "
    "Justiça; em segundo grau, o Tribunal de Justiça).",
    "O site **não cobra** o art. 99, §\u00a02º (redação divergente entre compilações) nem o §\u00a09º (a EC nº 47/2010, que lhe deu "
    "a redação atual, foi declarada inconstitucional pelo STF na ADI nº 4.509).",
    "A Constituição Estadual ainda prevê **voto secreto** na perda de mandato (art. 92, VIII, e art. 97, §\u00a02º) e "
    "**escrutínio secreto** na apreciação do veto (art. 108, §\u00a04º); na Constituição Federal, o voto secreto nesses casos "
    "foi suprimido pela EC nº 76/2013. As questões do site seguem a letra da Constituição Estadual.",
]

# bloco: (primeiro e último artigo do trecho, título da parte, número de questões, observação)
BLOCOS = {
    "1": ((11, 92), "Poderes do Estado, Assembleia Legislativa e competência exclusiva (arts. 11, 86, 90 e 92)", 15,
          "O art. 92 tem quase 40 incisos: distribua as questões entre eles (Mesa e Regimento, Deputados, Governador e "
          "Vice-Governador, Tribunais de Contas, contas, crimes de responsabilidade, processo legislativo) e cobre também o "
          "parágrafo único. NÃO faça questões sobre o art. 92, VII (licença prévia para processar Deputado), que destoa do "
          "regime de sustação do art. 95, §§ 3º a 5º, nem sobre o inciso XXIV, revogado."),
    "2": ((93, 100), "Convocação de autoridades, Deputados, reuniões e Plenário (arts. 93 a 100)", 15,
          "NÃO faça questões sobre o art. 99, §§ 2º e 9º (veja as notas de atenção no texto). Os Deputados (arts. 95 a 98) "
          "e as reuniões (art. 99) devem receber a maior parte das questões."),
    "3": ((101, 104), "Comissões, processo legislativo e emenda à Constituição (arts. 101 a 104)", 12, ""),
    "4": ((105, 114), "Leis: iniciativa privativa, urgência, sanção, veto, leis delegadas e complementares (arts. 105 a 114)", 15,
          "O art. 108 (sanção, veto e promulgação) deve receber pelo menos 3 questões, com prazos diferentes em cada uma."),
    "5": ((115, 121), "Fiscalização, controle externo e controle interno (arts. 115, 116 e 121)", 12, ""),
    "6": ((161, 341), "Tribunal de Justiça, controle de constitucionalidade, Justiça Militar e transição de governo "
                      "(arts. 161, 162, 168 e 341)", 12,
          "Dê prioridade ao controle de constitucionalidade (art. 161, I, \"l\", e art. 162: legitimados, oitiva do "
          "Procurador-Geral de Justiça, citação do Procurador-Geral do Estado e do Procurador-Geral da Assembleia, quórum) e "
          "às competências do Tribunal de Justiça que envolvem a Assembleia e os Deputados. Faça pelo menos 1 questão sobre "
          "o art. 168 e 2 sobre o art. 341."),
}

REGRAS = """Você vai produzir material de estudo para o concurso da ALEPA 2026 (banca Fundação CETAP), cargo Analista Legislativo – Assistência Legislativa, usando EXCLUSIVAMENTE o trecho da Constituição do Estado do Pará colado no final desta mensagem. Não use a Constituição Federal, nenhuma outra lei nem conhecimento externo.

IMPORTANTE: responda SOMENTE com o bloco de código JSON descrito abaixo. Não escreva nada antes ou depois do JSON.

TAREFA: gerar uma parte intitulada "{titulo}", com {n} questões.
{obs}
DISTRIBUIÇÃO
- Distribua as questões por todos os artigos do trecho, proporcionalmente ao tamanho de cada um; cada artigo com conteúdo relevante deve ter pelo menos uma questão.
- Pelo menos {neg} questões no formato "assinale a alternativa INCORRETA".
- Inclua 1 caso prático (uma situação concreta resolvida pelo texto).
- Priorize o que a banca costuma cobrar: prazos, quóruns (maioria, maioria absoluta, dois terços, três quintos, um terço), quem decide ou quem pode agir (Assembleia, Mesa, Plenário, Presidente, Comissão, Governador, Tribunal de Justiça, Tribunal de Contas), legitimados, vedações e exceções.

REGRAS DAS QUESTÕES
1. 5 alternativas (A a E), apenas uma correta, todas de tamanho parecido e plausíveis. Não use "todas as anteriores", "nenhuma das anteriores", "apenas I e II" nem itens em algarismos romanos: o site embaralha as alternativas. Não use distratores absurdos.
2. Cada pegadinha só pode ser o erro de UMA questão, e uma questão não pode entregar a resposta de outra.
3. Nas questões INCORRETA, as quatro alternativas verdadeiras devem afirmar quatro coisas diferentes, e nenhuma delas pode contradizer diretamente a alternativa errada (isso entrega o gabarito por eliminação).
4. Nenhuma alternativa pode ser verdadeira por obviedade nem conter expressão vaga ou sem sentido jurídico. A alternativa errada nasce de uma troca pontual e plausível (prazo, quórum, órgão, autoridade, número, exceção), e não de uma frase artificial.
5. Não use, numa alternativa, uma palavra que o texto reserva para outro conceito.
6. Comentário: uma linha por alternativa, na ordem, começando com "A) CORRETA." ou "A) INCORRETA." (nas questões INCORRETA, use "A) CORRETA (opção verdadeira)." e "A) INCORRETA (gabarito)."), com o motivo e o dispositivo. Nunca cite outra letra dentro do comentário. Não afirme nada que o texto não diga.
7. base_legal: dispositivo e trecho LITERAL completo, copiado do texto sem alterar nenhuma palavra, nenhum sinal e nenhuma pontuação (mantenha a grafia antiga, como "Assembléia"), sem reticências e sem rótulos colados antes do texto. Cada dispositivo fica numa única linha: não reproduza as quebras de linha do texto colado. Ao citar inciso, alínea ou parágrafo, inclua também a linha do caput do artigo (ou do inciso que introduz as alíneas). A base_legal deve sustentar TODAS as alternativas.
8. As linhas iniciadas por asterisco (notas de alteração, de julgamentos do STF e de atenção) e os títulos de título, capítulo, seção e subseção não são texto normativo: não os use como base_legal nem faça questões sobre redações anteriores ou sobre as notas.
9. Quando o texto remeter a um dispositivo que não está no trecho (por exemplo, art. 8º, art. 30, art. 135 ou artigos da Constituição Federal), não faça perguntas sobre o conteúdo do dispositivo remetido.
10. Os enunciados citam "a Constituição do Estado do Pará". Nas alternativas e nos enunciados, use a grafia atual ("Assembleia"). Gabaritos distribuídos entre A e E, sem passar de 30% na mesma letra.
11. Escreva tudo em português, sem notas internas e sem marcadores de citação como [1]. Não numere os enunciados.

RESUMO
- No máximo 250 palavras, em blocos curtos, com **negrito** nos prazos, quóruns, órgãos e palavras-chave. Não use itálico nem asterisco simples: o site só entende **negrito**.
- Tipos de bloco permitidos: "texto", "lista" (com "itens"), "tabela" e "atencao".
- Tabelas com 2 colunas (no máximo 3) e células curtas, porque o site é lido no celular; na primeira coluna, palavras de até 12 letras.
- 1 bloco "atencao" com as 3 pegadinhas mais prováveis.

FORMATO DE SAÍDA
Responda SOMENTE com um bloco de código JSON válido. Aspas duplas dentro de textos devem ser escapadas (\\"). Estrutura:

{{
  "titulo": "{titulo}",
  "artigos": "{artigos}",
  "resumo": [
    {{ "tipo": "texto", "conteudo": "Parágrafo do resumo." }},
    {{ "tipo": "tabela", "colunas": ["Tema", "Regra"], "linhas": [["texto", "texto"]] }},
    {{ "tipo": "atencao", "conteudo": "Pegadinhas mais prováveis." }}
  ],
  "questoes": [
    {{
      "enunciado": "De acordo com a Constituição do Estado do Pará, ...",
      "alternativas": {{ "A": "texto", "B": "texto", "C": "texto", "D": "texto", "E": "texto" }},
      "gabarito": "C",
      "comentario": "A) INCORRETA. Motivo.\\nB) INCORRETA. Motivo.\\nC) CORRETA. Motivo.\\nD) INCORRETA. Motivo.\\nE) INCORRETA. Motivo.",
      "base_legal": {{ "dispositivo": "Art. X, § Y", "texto": "Linha do caput, literal.\\nLinha do parágrafo, literal." }}
    }}
  ]
}}

Antes de responder, confira: são {n} questões; todos os artigos relevantes do trecho foram cobertos; há pelo menos {neg} questões INCORRETA e 1 caso prático; os gabaritos estão espalhados; cada gabarito confere com a base_legal; não há reticências; o JSON é válido.
"""

REVISAO = """Revise o JSON que você acabou de gerar, comparando-o com o trecho da Constituição do Estado do Pará colado na mensagem anterior. Não crie questões novas: corrija somente o que violar as regras abaixo e responda apenas com o JSON completo corrigido, sem nenhum texto fora do bloco.

1. Cada base_legal deve ser cópia literal do texto (palavras, sinais, pontuação e grafia antiga do original, como "Assembléia"), sem reticências, sem rótulos colados antes do texto e sem as notas iniciadas por asterisco. Cada dispositivo fica numa única linha; ao citar inciso, alínea ou parágrafo, inclua a linha do caput.
2. A base_legal deve sustentar TODAS as alternativas; se alguma depender de outro dispositivo do trecho, acrescente-o, também literal. Se depender de dispositivo que não está no trecho (Constituição Federal ou outro artigo), troque a alternativa.
3. Confira, em cada questão, os prazos, quóruns, números, autoridades e órgãos (Assembleia, Mesa, Plenário, Presidente, Governador, Tribunal de Justiça, Tribunal de Contas) contra o texto.
4. Nas questões "INCORRETA", as quatro alternativas verdadeiras devem afirmar quatro coisas diferentes, e nenhuma pode contradizer diretamente a alternativa errada. Se duas alternativas disserem o contrário uma da outra, troque a verdadeira por outra afirmação do texto.
5. Cada pegadinha só pode ser o erro de UMA questão, e uma questão não pode entregar a resposta de outra.
6. Nenhuma alternativa pode ser artificial, absurda ou vaga; a errada deve nascer de uma troca pontual e plausível. Se a alternativa correta for bem mais longa que as outras, equilibre os tamanhos.
7. Comentário: 5 linhas, de A a E, iniciadas por "X) CORRETA." ou "X) INCORRETA." (nas questões INCORRETA: "X) CORRETA (opção verdadeira)." e "X) INCORRETA (gabarito)."), indicando o dispositivo, sem citar outras letras e sem afirmar nada que o texto não diga.
8. Gabaritos distribuídos entre A e E, sem passar de 30% na mesma letra.
9. No resumo, só **negrito** (sem itálico nem asterisco simples) e tabelas de no máximo 3 colunas.
"""


def recorta(linhas, corpo, inicios, a, b):
    """Do artigo a ao artigo b (inclusive), com os títulos de seção que vêm antes do artigo a."""
    ini = inicios[a]
    while ini > corpo and not ARTIGO.match(linhas[ini - 1].strip()) and not linhas[ini - 1].strip().endswith((".", ";", ":")):
        ini -= 1
    proximos = [i for n, i in inicios.items() if n > b]
    fim = min(proximos) if proximos else len(linhas)
    while fim > ini and proximos and not linhas[fim - 1].strip().endswith((".", ";", ":", "”", "\"")):
        fim -= 1
    return "\n".join(l.rstrip() for l in linhas[ini:fim]).strip()


def garante_registro():
    """Acrescenta a Constituição ao registro, no início da lista, se ainda não estiver lá."""
    reg = json.loads(REGISTRO.read_text(encoding="utf-8"))
    lista = reg if isinstance(reg, list) else reg.get("normas")
    if lista is None:
        raise ValueError("formato inesperado em dados/normas.json")
    if any(n.get("id") == ID for n in lista):
        return False
    lista.insert(0, dict(ENTRADA_REGISTRO))
    REGISTRO.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bloco", nargs="?")
    ap.add_argument("--abrir", action="store_true")
    a = ap.parse_args()

    if not a.bloco or a.bloco not in BLOCOS:
        print("Blocos da Constituição do Estado do Pará:")
        for k, (_, titulo, n, _) in BLOCOS.items():
            print(f"  {k:>3}  {n:>2} questões  {titulo}")
        print("\nUso: python ferramentas/prompt_ce.py <bloco> --abrir")
        return 0 if not a.bloco else 1

    (x, y), titulo, n, obs = BLOCOS[a.bloco]
    linhas = TEXTO.read_text(encoding="utf-8").splitlines()
    corpo = next(i for i, l in enumerate(linhas) if ARTIGO.match(l.strip()))
    inicios = {}
    for i in range(corpo, len(linhas)):
        m = ARTIGO.match(linhas[i].strip())
        if m:
            inicios.setdefault(int(m.group(1)), i)

    artigos = re.search(r"\((arts?\..*)\)$", titulo).group(1)
    artigos = artigos[0].upper() + artigos[1:]
    neg = math.ceil(0.35 * n)
    msg = REGRAS.format(titulo=titulo, n=n, neg=neg, artigos=artigos, obs=(obs + "\n") if obs else "")
    msg += "\nTRECHO DA CONSTITUIÇÃO DO ESTADO DO PARÁ:\n\n" + recorta(linhas, corpo, inicios, x, y) + "\n"

    RASCUNHOS.mkdir(exist_ok=True)
    destino = RASCUNHOS / f"prompt-ce-b{a.bloco}.txt"
    destino.write_text(msg, encoding="utf-8")
    (RASCUNHOS / "prompt-ce-revisao.txt").write_text(REVISAO, encoding="utf-8")

    if garante_registro():
        print("Registro: acrescentei a Constituição do Estado do Pará em dados/normas.json.")
    primeira = not MATERIAL.exists()
    if primeira:
        (RASCUNHOS / "ce-notas.txt").write_text("\n".join(NOTAS) + "\n", encoding="utf-8")

    arq = f"rascunhos/ce-b{a.bloco}.json"
    print(f"Mensagem do ChatGPT: {destino.relative_to(REPO)} ({len(msg)} caracteres)")
    print("Autorrevisão:        rascunhos/prompt-ce-revisao.txt")
    print(f"\nDepois, salve a resposta do ChatGPT em {arq} e rode:")
    print(f"  python ferramentas/valida_norma.py {arq} {ID}")
    if primeira:
        print(f'  python ferramentas/monta_material.py {ID} {arq} --titulo "{TITULO_PAGINA}" --notas rascunhos/ce-notas.txt --fontes {ID}')
    else:
        print(f"  python ferramentas/monta_material.py {ID} {arq} --acrescentar --fontes {ID}")
    print(f"  python ferramentas/testa_norma.py {ID}")
    if a.abrir and hasattr(os, "startfile"):
        os.startfile(destino)
    return 0


if __name__ == "__main__":
    sys.exit(main())
