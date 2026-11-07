#!/usr/bin/env python3
"""Valida o material de uma norma contra o texto oficial.

Aceita a saída do ChatGPT ou do NotebookLM (uma parte, com ou sem o bloco ```json)
ou um arquivo já montado em dados/normas/<arquivo>.json.

Uso, a partir da pasta do repositório:
  python ferramentas/valida_norma.py rascunhos/dl-45-2009.json dl-45-2009
  python ferramentas/valida_norma.py rascunhos/ouvidoria-p3.json res-04-2012 ri-2022
  python ferramentas/valida_norma.py dados/normas/ouvidoria.json

As fontes podem ser ids (procurados em ferramentas/textos/) ou caminhos de arquivos .txt.
Sem fontes, o validador usa ferramentas/fontes.json (materiais já publicados) ou o "id" do JSON.

ERROS impedem a publicação. AVISOS pedem uma revisão humana.
Havendo erros, o validador imprime no fim um bloco pronto para colar no ChatGPT.
Código de saída: 0 sem erros; 1 com erros.
"""
import difflib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

PASTA = Path(__file__).resolve().parent
TEXTOS = PASTA / "textos"
FONTES = PASTA / "fontes.json"
LETRAS = list("ABCDE")
NEGATIVA = re.compile(r"INCORRETA|\bNÃO\b|EXCETO")
ROTULO = re.compile(r"\[[^\]]+\]")
INICIO_DISPOSITIVO = re.compile(
    r"(?=\bArt\. ?\d)|(?=§ ?\d)|(?=Parágrafo único)|(?=\b[IVXLC]+ ?[–-] )|(?=(?<![\w(])[a-z]\) )"
)
LINHA_INICIA = re.compile(r"^(Art\.?\s?\d|§|Parágrafo|[IVXLC]+\s?[-–]|[a-z]\)|\d+\.\s|“|\*|À |Ao |Aos |Às )")
LINHA_FECHA = re.compile(r"([.;:!?”\"]|[;,]\s(e|ou))$")
PALAVRA_SOLTA = re.compile(r"\b(de|do|da|dos|das|em|no|na|nos|nas|a|o|as|os|e|ou|por|para|com|que|ao|à|aos|às|pelo|pela|"
                           r"pelos|pelas|um|uma|se|sobre|entre|seu|sua|seus|suas)$", re.I)
CITA_LETRA = re.compile(r"\b(?:alternativa|letra|opção|item)\s+[A-E]\b", re.I)
CITA_LEI = re.compile(r"Lei(?: Complementar| Federal| Estadual)? (?:nº|n\.º|n°|n\.°)\s?([\d.]+)")
SUSPEITOS = ["Governador", "Polícia Federal", "Justiça Federal", "Ministério Público Federal",
             "Tribunal de Justiça", "multa", "detenção", "reclusão"]


def cap(s):
    """Primeira letra maiúscula, sem alterar o resto (str.capitalize rebaixaria siglas)."""
    return s[:1].upper() + s[1:]


def norm(s):
    """Junta espaços e quebras de linha e reata palavras hifenizadas na quebra de linha do PDF."""
    return re.sub(r"(\w)-\s+(\w)", r"\1-\2", re.sub(r"\s+", " ", s)).strip()


def corta(s, n=320):
    s = s.strip()
    return s if len(s) <= n else s[:n].rstrip() + " (trecho cortado)"


def carrega_json(caminho):
    """Lê o JSON, tolerando o bloco ```json``` e texto antes ou depois do objeto."""
    bruto = Path(caminho).read_text(encoding="utf-8-sig")
    m = re.search(r"```(?:json)?\s*\n(.*?)\n\s*```", bruto, re.S)
    texto = m.group(1) if m else bruto
    ini, fim = texto.find("{"), texto.rfind("}")
    if ini == -1 or fim == -1:
        raise ValueError("não encontrei um objeto JSON ({ ... }) no arquivo.")
    texto = texto[ini:fim + 1]
    try:
        return json.loads(texto)
    except json.JSONDecodeError as e:
        linhas = texto.split("\n")
        trecho = linhas[e.lineno - 1].strip() if 0 < e.lineno <= len(linhas) else ""
        raise ValueError(f"o JSON está inválido na linha {e.lineno}, coluna {e.colno} do bloco ({e.msg}). "
                         f"Linha com problema: {corta(trecho, 200)}")


def resolve_fonte(arg):
    p = Path(arg)
    if p.suffix == ".txt":
        if p.exists():
            return [p]
        raise ValueError(f"arquivo de texto não encontrado: {arg}")
    achados = sorted(TEXTOS.glob(f"{arg}.txt")) + sorted(TEXTOS.glob(f"{arg}__*.txt"))
    if not achados:
        raise ValueError(f"texto oficial não encontrado para '{arg}' (procurei {TEXTOS / (arg + '.txt')}).")
    return achados


def carrega_textos(fontes):
    textos = {}
    for f in fontes:
        for p in resolve_fonte(f):
            textos[p.stem] = norm(p.read_text(encoding="utf-8"))
    return textos


def fontes_padrao(caminho_json, obj):
    nome = Path(caminho_json).name
    if FONTES.exists():
        mapa = json.loads(FONTES.read_text(encoding="utf-8"))
        if nome in mapa:
            return mapa[nome]
    if isinstance(obj, dict) and obj.get("id"):
        return [obj["id"]]
    return []


def lista_partes(obj):
    if isinstance(obj, dict) and isinstance(obj.get("partes"), list):
        return obj["partes"]
    if isinstance(obj, dict) and "questoes" in obj:
        return [obj]
    raise ValueError('o JSON precisa ter "questoes" (uma parte) ou "partes" (material completo).')


class Resultado:
    def __init__(self):
        self.erros, self.avisos, self.resumo_partes = [], [], []
        self.fontes_usadas = set()


def valida(obj, textos):
    """Valida o objeto contra os textos normalizados ({nome: texto}). Devolve um Resultado."""
    r = Resultado()
    unido = " ‖ ".join(textos.values())
    segmentos = []
    for t in textos.values():
        segmentos += [s.strip() for s in INICIO_DISPOSITIVO.split(t) if len(s.strip()) > 15]

    partes = lista_partes(obj)
    varias = len(partes) > 1
    todas_alts = []

    for ip, parte in enumerate(partes, 1):
        rot_p = f"Parte {parte.get('numero', ip)}, " if varias else ""
        for chave in ("titulo", "artigos"):
            if not parte.get(chave):
                r.avisos.append(cap(f'{rot_p}falta o campo "{chave}" da parte.'))
        valida_resumo(parte.get("resumo"), rot_p, r)

        questoes = parte.get("questoes") or []
        if not questoes:
            r.erros.append(cap(f'{rot_p}a parte não tem questões ("questoes" vazio ou ausente).'))
            continue
        gabaritos, negativas = [], 0
        for k, q in enumerate(questoes, 1):
            rot = cap(f"{rot_p}questão {k}")
            negativas += valida_questao(q, rot, unido, segmentos, textos, r)
            gabaritos.append(str(q.get("gabarito", "?")))
            for letra, alt in (q.get("alternativas") or {}).items():
                todas_alts.append((rot, letra, str(alt)))

        n = len(questoes)
        cont = Counter(gabaritos)
        limite = max(2, math.ceil(0.3 * n))
        excesso = [f"{l} ({c} vezes)" for l, c in sorted(cont.items()) if c > limite]
        if excesso:
            r.avisos.append(cap(f"{rot_p}gabaritos concentrados: {', '.join(excesso)}; o máximo recomendado é {limite} "
                                f"por letra em {n} questões. Redistribua trocando a posição das alternativas."))
        for i in range(len(gabaritos) - 2):
            if gabaritos[i] == gabaritos[i + 1] == gabaritos[i + 2]:
                r.avisos.append(cap(f"{rot_p}três gabaritos seguidos iguais ({gabaritos[i]}) a partir da questão {i + 1}."))
                break
        minimo = round(0.35 * n)
        if n >= 6 and negativas < minimo:
            r.avisos.append(cap(f'{rot_p}só {negativas} questão(ões) no formato "assinale a INCORRETA"; '
                                f'o prompt pede pelo menos {minimo} em {n}.'))
        r.resumo_partes.append((parte.get("numero", ip), n, "".join(gabaritos), dict(sorted(cont.items())), negativas))

    # alternativas repetidas ou quase iguais em todo o arquivo
    vistos, quase = {}, 0
    for rot, letra, alt in todas_alts:
        chave = norm(alt).lower()
        if chave in vistos:
            outra_rot, outra_letra = vistos[chave]
            if outra_rot == rot:
                r.erros.append(f"{rot}: as alternativas {outra_letra} e {letra} têm o mesmo texto.")
            else:
                r.avisos.append(f"{rot}, alternativa {letra}: texto idêntico ao de {outra_rot.lower()}, alternativa "
                                f"{outra_letra}; evite repetir a mesma alternativa em questões diferentes.")
        else:
            vistos[chave] = (rot, letra)
    for i in range(len(todas_alts)):
        for j in range(i + 1, len(todas_alts)):
            (ra, la, a), (rb, lb, b) = todas_alts[i], todas_alts[j]
            if ra == rb or norm(a).lower() == norm(b).lower():
                continue
            sm = difflib.SequenceMatcher(None, a, b)
            if sm.real_quick_ratio() > 0.92 and sm.quick_ratio() > 0.92 and sm.ratio() > 0.92:
                quase += 1
                if quase <= 5:
                    r.avisos.append(f"{ra}, alternativa {la}, é quase igual a {rb.lower()}, alternativa {lb}: "
                                    f"confira se a mesma pegadinha não se repete.")
    return r


def valida_resumo(resumo, rot_p, r):
    if not isinstance(resumo, list) or not resumo:
        r.avisos.append(cap(f'{rot_p}a parte não tem "resumo".'))
        return
    for i, bloco in enumerate(resumo, 1):
        tipo = bloco.get("tipo") if isinstance(bloco, dict) else None
        onde = cap(f"{rot_p}resumo, bloco {i}")
        if tipo == "lista":
            itens = bloco.get("itens")
            if not isinstance(itens, list) or not itens or not all(isinstance(i, str) and i.strip() for i in itens):
                r.erros.append(f'{onde} (lista): "itens" deve ser uma lista de textos.')
        elif tipo in ("texto", "atencao"):
            conteudo = bloco.get("conteudo")
            if not isinstance(conteudo, str) or not conteudo.strip():
                r.erros.append(f'{onde} ({tipo}): falta o texto em "conteudo".')
            elif "..." in conteudo or "…" in conteudo:
                r.avisos.append(f"{onde}: há reticências no texto do resumo.")
        elif tipo == "tabela":
            colunas, linhas = bloco.get("colunas"), bloco.get("linhas")
            if not isinstance(colunas, list) or not isinstance(linhas, list):
                r.erros.append(f'{onde} (tabela): precisa de "colunas" e "linhas" em forma de lista.')
                continue
            if len(colunas) > 3:
                r.avisos.append(f"{onde}: a tabela tem {len(colunas)} colunas; no celular, use no máximo 3.")
            for k, linha in enumerate(linhas, 1):
                if not isinstance(linha, list) or len(linha) != len(colunas):
                    r.erros.append(f"{onde}, linha {k} da tabela: deve ter {len(colunas)} células, uma para cada coluna.")
        else:
            r.erros.append(f'{onde}: tipo "{tipo}" inválido; use "texto", "lista", "tabela" ou "atencao".')


def valida_questao(q, rot, unido, segmentos, textos, r):
    """Valida uma questão; devolve 1 se ela for do tipo negativo (INCORRETA, NÃO, EXCETO)."""
    enun = str(q.get("enunciado", ""))
    alts = q.get("alternativas") or {}
    gab = q.get("gabarito")
    com = str(q.get("comentario", ""))
    base = q.get("base_legal") or {}
    neg = bool(NEGATIVA.search(enun))

    if not enun.strip():
        r.erros.append(f"{rot}: enunciado vazio.")
    if re.match(r"\s*Quest[ãa]o\s*\d", enun):
        r.erros.append(f'{rot}: retire a numeração do enunciado ("Questão N").')
    if not isinstance(alts, dict) or sorted(alts) != LETRAS or any(not str(v).strip() for v in alts.values()):
        r.erros.append(f"{rot}: são exigidas exatamente 5 alternativas, A a E, todas preenchidas.")
        alts = alts if isinstance(alts, dict) else {}
    if gab not in LETRAS:
        r.erros.append(f'{rot}: gabarito "{gab}" inválido; use uma letra de A a E.')

    # comentário: 5 linhas, uma por alternativa, com o rótulo certo
    linhas = [l.strip() for l in com.split("\n") if l.strip()]
    if [l[:3] for l in linhas] != [f"{L}) " for L in LETRAS]:
        r.erros.append(f"{rot}: o comentário deve ter 5 linhas, começando por A), B), C), D) e E), nesta ordem.")
    else:
        if neg:
            ok, marca = ("CORRETA (opção verdadeira).", "INCORRETA (gabarito)."), "INCORRETA (gabarito)."
            modelo = '"X) CORRETA (opção verdadeira)." ou "X) INCORRETA (gabarito)."'
            tipo = "negativa (pede a INCORRETA, o que NÃO ou o EXCETO)"
        else:
            ok, marca = ("CORRETA.", "INCORRETA."), "CORRETA."
            modelo = '"X) CORRETA." ou "X) INCORRETA."'
            tipo = "positiva (pede a CORRETA)"
        ruins = [l[0] for l in linhas if not l[3:].startswith(ok)]
        if ruins:
            r.erros.append(f"{rot}: a questão é {tipo}; as linhas {', '.join(ruins)} do comentário devem começar com {modelo}")
        else:
            marcadas = [l[0] for l in linhas if l[3:].startswith(marca)]
            if len(marcadas) != 1:
                r.erros.append(f"{rot}: o comentário aponta {len(marcadas)} alternativas como resposta "
                               f"({', '.join(marcadas) or 'nenhuma'}); deve apontar só uma.")
            elif marcadas[0] != gab:
                r.erros.append(f"{rot}: o gabarito é {gab}, mas o comentário aponta {marcadas[0]} como resposta.")
        for l in linhas:
            if CITA_LETRA.search(l[3:]):
                r.erros.append(f"{rot}: a linha {l[0]} do comentário cita outra letra; como o site embaralha as alternativas, "
                               f"explique pelo conteúdo, sem citar letras.")

    texto_q = " ".join([enun, com, " ".join(map(str, alts.values()))])
    tudo = texto_q + " " + str(base.get("texto", ""))
    if "..." in tudo or "…" in tudo:
        r.erros.append(f"{rot}: há reticências no enunciado, nas alternativas, no comentário ou na base legal; "
                       f"transcreva os trechos por inteiro.")
    if re.search(r"\[\d+\]", tudo):
        r.erros.append(f"{rot}: retire os marcadores de citação como [1].")
    if re.search(r"(?<!\w)'[^'\n]{2,80}'(?!\w)", tudo):
        r.avisos.append(f"{rot}: há aspas simples; prefira aspas duplas escapadas ou nenhuma.")

    # possíveis distratores absurdos ou conhecimento externo
    for termo in SUSPEITOS:
        if re.search(rf"\b{re.escape(termo)}", texto_q, re.I) and termo.lower() not in unido.lower():
            r.avisos.append(f'{rot}: menciona "{termo}", que não aparece no texto oficial; confira se não é um distrator absurdo.')
    for num in sorted(set(CITA_LEI.findall(texto_q))):
        num = num.rstrip(".")
        if num and num not in unido:
            r.avisos.append(f"{rot}: cita a Lei nº {num}, que não aparece no texto oficial; confira se não é conhecimento externo.")

    # alternativa do gabarito muito mais longa que as demais (dica involuntária)
    if gab in alts and len(alts) == 5 and not neg:
        outras = [len(str(v)) for k, v in alts.items() if k != gab]
        tam = len(str(alts[gab]))
        if tam > 1.7 * (sum(outras) / 4) and tam > 1.3 * max(outras):
            r.avisos.append(f"{rot}: a alternativa do gabarito é bem mais longa que as outras, o que denuncia a resposta.")

    # base legal literal
    texto_base = str(base.get("texto", "")).strip()
    if not texto_base or not str(base.get("dispositivo", "")).strip():
        r.erros.append(f'{rot}: falta a base_legal ("dispositivo" e "texto").')
        return int(neg)
    linhas_base = [l for l in texto_base.split("\n") if l.strip()]
    for n in range(1, len(linhas_base)):
        ant, cur = linhas_base[n - 1].strip(), linhas_base[n].strip()
        if ROTULO.fullmatch(ant) or ROTULO.fullmatch(cur) or ant.isupper() or cur.isupper():
            continue
        if (not LINHA_FECHA.search(ant) and not LINHA_INICIA.match(cur)
                and (PALAVRA_SOLTA.search(ant) or cur[:1].islower())):
            r.avisos.append(f"{rot}, base_legal, linha {n + 1}: parece continuação da linha anterior (quebra de linha do texto "
                            f"colado); junte as duas numa linha só, para o site não mostrar a frase cortada.")
            break
    for n, linha in enumerate(linhas_base, 1):
        if ROTULO.fullmatch(linha.strip()):
            continue
        alvo = norm(linha)
        achou = [nome for nome, t in textos.items() if alvo in t]
        if achou:
            r.fontes_usadas.update(achou)
            continue
        msg = f"{rot}, base_legal, linha {n}: o trecho não aparece no texto oficial.\n    Enviado: «{corta(linha)}»"
        perto = difflib.get_close_matches(alvo, segmentos, n=1, cutoff=0.45)
        if perto:
            msg += f"\n    Texto oficial mais próximo: «{corta(perto[0])}»"
        r.erros.append(msg)
    return int(neg)


def imprime(r, caminho, fontes):
    print(f"Validação de {caminho}")
    print(f"Textos oficiais: {', '.join(fontes)}")
    for numero, n, gabs, cont, neg in r.resumo_partes:
        dist = " ".join(f"{l}{c}" for l, c in cont.items())
        print(f"Parte {numero}: {n} questões · gabaritos {gabs} ({dist}) · negativas {neg}")
    print()
    if r.erros:
        print(f"ERROS ({len(r.erros)}), que impedem a publicação:")
        for i, e in enumerate(r.erros, 1):
            print(f" {i}. {e}")
        print()
    if r.avisos:
        print(f"AVISOS ({len(r.avisos)}), para revisar:")
        for i, a in enumerate(r.avisos, 1):
            print(f" {i}. {a}")
        print()
    if not r.erros and not r.avisos:
        print("Nenhum erro e nenhum aviso.")
    elif not r.erros:
        print("Nenhum erro. Revise os avisos antes de montar o material.")
    else:
        print("=" * 70)
        print("Cole no ChatGPT, na mesma conversa:")
        print("-" * 70)
        print("O validador automático encontrou os problemas abaixo. Corrija somente esses pontos, sem alterar o restante, "
              "copiando os trechos de base_legal do texto oficial, e devolva o JSON completo, sem texto fora do bloco.")
        for i, e in enumerate(r.erros, 1):
            print(f"{i}. {e}")
        print("-" * 70)


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 2
    caminho = argv[1]
    try:
        obj = carrega_json(caminho)
    except (ValueError, OSError) as e:
        print(f"ERRO: {e}")
        print(f"\nCole no ChatGPT: O JSON que você devolveu não pôde ser lido: {e} "
              f"Corrija a sintaxe e devolva o JSON completo, sem texto fora do bloco.")
        return 1
    fontes = argv[2:] or fontes_padrao(caminho, obj)
    if not fontes:
        print("Informe o texto oficial: python ferramentas/valida_norma.py <arquivo.json> <id-da-norma>")
        return 2
    try:
        textos = carrega_textos(fontes)
        r = valida(obj, textos)
    except ValueError as e:
        print(f"ERRO: {e}")
        return 1
    imprime(r, caminho, fontes)
    return 1 if r.erros else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
