#!/usr/bin/env python3
"""Monta a mensagem pronta para o ChatGPT gerar as questões de um bloco do Regimento Interno (Res. 02/2022).

Uso, a partir da pasta do repositório:
  python ferramentas/prompt_ri.py              lista os blocos
  python ferramentas/prompt_ri.py 2 --abrir    grava rascunhos/prompt-ri-b2.txt e o abre no Bloco de Notas

O arquivo gerado já traz as regras, o trecho do Regimento (ferramentas/textos/ri-2022.txt) e, no bloco
"1x", a lista das questões que já existem. Copie tudo e cole numa conversa nova do ChatGPT.
A mensagem de autorrevisão fica em rascunhos/prompt-ri-revisao.txt.
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
TEXTO = PASTA / "textos" / "ri-2022.txt"
RASCUNHOS = REPO / "rascunhos"
ARTIGO = re.compile(r"^Art\.\s?(\d+)")

# bloco: (trechos de artigos, título da parte, número de questões, observação)
BLOCOS = {
    "1x": ([(1, 22)], "Título I: questões extras (arts. 1º a 22)", 15,
           "Já existem questões sobre este trecho (lista no fim desta mensagem): NÃO repita os pontos cobrados nem as pegadinhas usadas; "
           "cubra dispositivos ainda não cobrados."),
    "2": ([(23, 41)], "Mesa Diretora e Comissão de Ética (arts. 23 a 32 e 41)", 15,
          "NÃO faça questões sobre os arts. 33 a 40 (Ouvidoria e Procuradoria da Mulher), que já têm páginas próprias no site."),
    "3": ([(42, 53), (56, 65)], "Comissões: regras gerais e Comissões Permanentes (arts. 42 a 53 e 56 a 65)", 15, ""),
    "4": ([(54, 55)], "Comissões Permanentes e campos temáticos (arts. 54 e 55)", 12,
          "Os incisos X e XIX dos arts. 54 e 55 (Mineração e Energia; Meio Ambiente) já têm questões na página da Resolução nº 02/2023: "
          "dê prioridade às demais Comissões."),
    "5": ([(66, 94)], "Comissões: apreciação das matérias, Comissões Temporárias, CPI e audiência pública (arts. 66 a 94)", 15, ""),
    "6": ([(95, 122)], "Sessões: disposições gerais, expedientes e Ordem do Dia (arts. 95 a 122)", 15, ""),
    "7": ([(123, 166)], "Sessões: discussão, votação, redação final, outras sessões, questões de ordem e ata (arts. 123 a 166)", 18, ""),
    "8": ([(167, 201)], "Proposições, requerimentos, emendas, moções, indicações e pareceres (arts. 167 a 201)", 15, ""),
    "9": ([(202, 235)], "Fases do processo legislativo: apresentação, recebimento, tramitação e quórum (arts. 202 a 235)", 15, ""),
    "10": ([(236, 260)], "Fases do processo legislativo: turnos, urgência, preferência, destaque, sanção, veto e promulgação (arts. 236 a 260)", 15, ""),
    "11": ([(261, 293)], "Matérias sujeitas a disposições especiais (arts. 261 a 293)", 15, ""),
    "12": ([(294, 318)], "Deputados: posse, mandato, licença, vacância, suplentes e decoro (arts. 294 a 318)", 12, ""),
    "13": ([(319, 352)], "Participação da sociedade, administração e disposições finais (arts. 319 a 352)", 12, ""),
}
EXISTENTES_1X = ["rascunhos/ri-p1.json", "rascunhos/ri-p2.json"]

REGRAS = """Você vai produzir material de estudo para o concurso da ALEPA 2026 (banca Fundação CETAP), cargo Analista Legislativo – Assistência Legislativa, usando EXCLUSIVAMENTE o trecho do Regimento Interno da Assembleia Legislativa do Estado do Pará (Resolução nº 02/2022) colado no final desta mensagem. Não use nenhuma outra lei nem conhecimento externo.

IMPORTANTE: responda SOMENTE com o bloco de código JSON descrito abaixo. Não escreva nada antes ou depois do JSON.

TAREFA: gerar uma parte intitulada "{titulo}", com {n} questões.
{obs}
DISTRIBUIÇÃO
- Distribua as questões por todos os capítulos, seções e subseções do trecho, proporcionalmente ao tamanho de cada um; cada seção com conteúdo relevante deve ter pelo menos uma questão.
- Pelo menos {neg} questões no formato "assinale a alternativa INCORRETA".
- Inclua 1 caso prático (uma situação concreta resolvida pelo texto).
- Priorize o que a banca costuma cobrar: prazos, quóruns (maioria simples, absoluta, dois terços), quem decide (Presidente, Mesa, Plenário, Comissão, Líder), números de membros e de dias, exceções e vedações.

REGRAS DAS QUESTÕES
1. 5 alternativas (A a E), apenas uma correta, todas de tamanho parecido e plausíveis. Não use "todas as anteriores", "nenhuma das anteriores", "apenas I e II" nem itens em algarismos romanos: o site embaralha as alternativas. Não use distratores absurdos.
2. Cada pegadinha só pode ser o erro de UMA questão, e uma questão não pode entregar a resposta de outra.
3. Nas questões INCORRETA, as quatro alternativas verdadeiras devem afirmar quatro coisas diferentes, e nenhuma delas pode contradizer diretamente a alternativa errada (isso entrega o gabarito por eliminação).
4. Nenhuma alternativa pode ser verdadeira por obviedade nem conter expressão vaga ou sem sentido jurídico. A alternativa errada nasce de uma troca pontual e plausível (prazo, quórum, órgão, número, exceção), e não de uma frase artificial.
5. Não use, numa alternativa, uma palavra que o texto reserva para outro conceito.
6. Comentário: uma linha por alternativa, na ordem, começando com "A) CORRETA." ou "A) INCORRETA." (nas questões INCORRETA, use "A) CORRETA (opção verdadeira)." e "A) INCORRETA (gabarito)."), com o motivo e o dispositivo. Nunca cite outra letra dentro do comentário. Não afirme nada que o texto não diga.
7. base_legal: dispositivo e trecho LITERAL completo, copiado do texto sem alterar nenhuma palavra, nenhum sinal e nenhuma pontuação, sem reticências e sem rótulos colados antes do texto. Cada dispositivo fica numa única linha: não reproduza as quebras de linha do texto colado. Ao citar inciso, alínea ou parágrafo, inclua também a linha do caput do artigo (ou do inciso que introduz as alíneas). A base_legal deve sustentar TODAS as alternativas.
8. As linhas iniciadas por asterisco, os textos de "redação anterior" que vêm logo depois delas e os títulos de capítulo e seção não são texto normativo: não os use como base_legal nem faça questões sobre redações anteriores.
9. Os enunciados citam o "Regimento Interno da Assembleia Legislativa (Resolução nº 02/2022)" ou "o Regimento Interno". Gabaritos distribuídos entre A e E, sem passar de 30% na mesma letra.
10. Escreva tudo em português, sem notas internas e sem marcadores de citação como [1]. Não numere os enunciados.

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
      "enunciado": "De acordo com o Regimento Interno da Assembleia Legislativa (Resolução nº 02/2022), ...",
      "alternativas": {{ "A": "texto", "B": "texto", "C": "texto", "D": "texto", "E": "texto" }},
      "gabarito": "C",
      "comentario": "A) INCORRETA. Motivo.\\nB) INCORRETA. Motivo.\\nC) CORRETA. Motivo.\\nD) INCORRETA. Motivo.\\nE) INCORRETA. Motivo.",
      "base_legal": {{ "dispositivo": "Art. X, § Y", "texto": "Linha do caput, literal.\\nLinha do parágrafo, literal." }}
    }}
  ]
}}

Antes de responder, confira: são {n} questões; todas as seções relevantes do trecho foram cobertas; há pelo menos {neg} questões INCORRETA e 1 caso prático; os gabaritos estão espalhados; cada gabarito confere com a base_legal; não há reticências; o JSON é válido.
"""

REVISAO = """Revise o JSON que você acabou de gerar, comparando-o com o trecho do Regimento Interno colado na mensagem anterior. Não crie questões novas: corrija somente o que violar as regras abaixo e responda apenas com o JSON completo corrigido, sem nenhum texto fora do bloco.

1. Cada base_legal deve ser cópia literal do texto (palavras, sinais, pontuação e erros de grafia do original), sem reticências, sem rótulos colados antes do texto e sem as notas iniciadas por asterisco. Cada dispositivo fica numa única linha; ao citar inciso, alínea ou parágrafo, inclua a linha do caput.
2. A base_legal deve sustentar TODAS as alternativas; se alguma depender de outro dispositivo, acrescente-o, também literal.
3. Confira, em cada questão, os prazos, quóruns, números e órgãos (Presidente, Mesa, Plenário, Comissão, Líder) contra o texto.
4. Nas questões "INCORRETA", as quatro alternativas verdadeiras devem afirmar quatro coisas diferentes, e nenhuma pode contradizer diretamente a alternativa errada. Se duas alternativas disserem o contrário uma da outra, troque a verdadeira por outra afirmação do texto.
5. Cada pegadinha só pode ser o erro de UMA questão, e uma questão não pode entregar a resposta de outra.
6. Nenhuma alternativa pode ser artificial, absurda ou vaga; a errada deve nascer de uma troca pontual e plausível. Se a alternativa correta for bem mais longa que as outras, equilibre os tamanhos.
7. Comentário: 5 linhas, de A a E, iniciadas por "X) CORRETA." ou "X) INCORRETA." (nas questões INCORRETA: "X) CORRETA (opção verdadeira)." e "X) INCORRETA (gabarito)."), indicando o dispositivo, sem citar outras letras e sem afirmar nada que o texto não diga.
8. Gabaritos distribuídos entre A e E, sem passar de 30% na mesma letra.
9. No resumo, só **negrito** (sem itálico nem asterisco simples) e tabelas de no máximo 3 colunas.
"""


def recorta(linhas, corpo, inicios, a, b):
    ini = inicios[a]
    while ini > corpo and not ARTIGO.match(linhas[ini - 1].strip()) and not linhas[ini - 1].strip().endswith((".", ";", ":")):
        ini -= 1
    proximos = [i for n, i in inicios.items() if n > b]
    fim = min(proximos) if proximos else len(linhas)
    while fim > ini and proximos and not linhas[fim - 1].strip().endswith((".", ";", ":", "”", "\"")):
        fim -= 1
    return "\n".join(l.rstrip() for l in linhas[ini:fim]).strip()


def lista_existentes(caminhos):
    linhas = []
    for c in caminhos:
        p = REPO / c
        if not p.exists():
            raise FileNotFoundError(c)
        obj = json.loads(p.read_text(encoding="utf-8"))
        for q in obj.get("questoes", []):
            linhas.append(f"- {q['enunciado']} [{q['base_legal']['dispositivo']}]")
    return "\n".join(linhas)


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
        print("Blocos do Regimento Interno:")
        for k, (trechos, titulo, n, _) in BLOCOS.items():
            print(f"  {k:>3}  {n:>2} questões  {titulo}")
        print("\nUso: python ferramentas/prompt_ri.py <bloco> --abrir")
        return 0 if not a.bloco else 1

    trechos, titulo, n, obs = BLOCOS[a.bloco]
    linhas = TEXTO.read_text(encoding="utf-8").splitlines()
    corpo = next(i for i, l in enumerate(linhas) if l.strip().startswith("Art. 1° O Poder Legislativo"))
    inicios = {}
    for i in range(corpo, len(linhas)):
        m = ARTIGO.match(linhas[i].strip())
        if m:
            inicios.setdefault(int(m.group(1)), i)

    artigos = re.search(r"\((arts?\..*)\)$", titulo).group(1)
    artigos = artigos[0].upper() + artigos[1:]
    neg = math.ceil(0.35 * n)
    msg = REGRAS.format(titulo=titulo, n=n, neg=neg, artigos=artigos, obs=(obs + "\n") if obs else "")
    texto = "\n\n".join(recorta(linhas, corpo, inicios, x, y) for x, y in trechos)
    msg += "\nTRECHO DO REGIMENTO INTERNO:\n\n" + texto + "\n"
    if a.bloco == "1x":
        try:
            msg += "\nQUESTÕES QUE JÁ EXISTEM SOBRE ESTE TRECHO (não repita estes pontos):\n" + lista_existentes(EXISTENTES_1X) + "\n"
        except FileNotFoundError as e:
            print(f"ERRO: não encontrei {e}. Copie os arquivos ri-p1.json e ri-p2.json para a pasta rascunhos.")
            return 1

    RASCUNHOS.mkdir(exist_ok=True)
    destino = RASCUNHOS / f"prompt-ri-b{a.bloco}.txt"
    destino.write_text(msg, encoding="utf-8")
    (RASCUNHOS / "prompt-ri-revisao.txt").write_text(REVISAO, encoding="utf-8")
    arq = f"rascunhos/ri-b{a.bloco}.json"
    print(f"Mensagem do ChatGPT: {destino.relative_to(REPO)} ({len(msg)} caracteres)")
    print("Autorrevisão:        rascunhos/prompt-ri-revisao.txt")
    print(f"\nDepois, salve a resposta do ChatGPT em {arq} e rode:")
    print(f"  python ferramentas/valida_norma.py {arq} ri-2022")
    print(f"  python ferramentas/monta_material.py res-02-2022 {arq} --acrescentar --fontes ri-2022")
    print("  python ferramentas/testa_norma.py res-02-2022")
    if a.abrir and hasattr(os, "startfile"):
        os.startfile(destino)
    return 0


if __name__ == "__main__":
    sys.exit(main())
