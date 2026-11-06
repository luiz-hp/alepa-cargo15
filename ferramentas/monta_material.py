#!/usr/bin/env python3
"""Monta dados/normas/<arquivo>.json a partir das partes validadas e liga o material à norma em dados/normas.json.

Uso, a partir da pasta do repositório:
  python ferramentas/monta_material.py dl-45-2009 rascunhos/dl45-p1.json rascunhos/dl45-p2.json
  python ferramentas/monta_material.py dl-45-2009 rascunhos/dl45-p1.json --titulo "Decreto Legislativo nº 45/2009 (Tema)" --nota "Texto da nota"
  python ferramentas/monta_material.py res-04-2012 rascunhos/ouv-p4.json --arquivo ouvidoria --acrescentar
  python ferramentas/monta_material.py dl-45-2009 rascunhos/p1.json --ids dl-03-2012 dl-05-2015 --fontes dl-45-2009 dl-03-2012 dl-05-2015

Opções:
  --titulo T       título da página (padrão: tipo, número e ano, conforme dados/normas.json)
  --nota N         nota do quadro "alterações e vigência" no topo da página (pode repetir a opção)
  --arquivo NOME   nome do arquivo em dados/normas/, sem .json (padrão: o id)
  --ids ID ...     outras normas do registro que usam o mesmo material
  --fontes F ...   textos oficiais usados na validação (padrão: o id e os de --ids)
  --acrescentar    acrescenta as partes ao material que já existe
  --substituir     sobrescreve o material que já existe

O material só é gravado se o validador não encontrar ERROS.
"""
import argparse
import json
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
sys.path.insert(0, str(PASTA))
import valida_norma as v  # noqa: E402

REPO = PASTA.parent
REGISTRO = REPO / "dados" / "normas.json"


def grava_json(caminho, obj):
    caminho.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("id")
    ap.add_argument("partes", nargs="+")
    ap.add_argument("--titulo")
    ap.add_argument("--nota", action="append", default=[])
    ap.add_argument("--arquivo")
    ap.add_argument("--ids", nargs="+", default=[])
    ap.add_argument("--fontes", nargs="+")
    grupo = ap.add_mutually_exclusive_group()
    grupo.add_argument("--acrescentar", action="store_true")
    grupo.add_argument("--substituir", action="store_true")
    a = ap.parse_args()

    reg = json.loads(REGISTRO.read_text(encoding="utf-8"))
    por_id = {n["id"]: n for n in reg["normas"]}
    for i in [a.id] + a.ids:
        if i not in por_id:
            print(f"ERRO: o id '{i}' não existe em dados/normas.json.")
            return 1
    meta = por_id[a.id]

    novas = []
    for caminho in a.partes:
        try:
            obj = v.carrega_json(caminho)
            novas += v.lista_partes(obj)
        except (ValueError, OSError) as e:
            print(f"ERRO em {caminho}: {e}")
            return 1

    fontes = a.fontes or [a.id] + a.ids
    try:
        textos = v.carrega_textos(fontes)
    except ValueError as e:
        print(f"ERRO: {e}")
        return 1
    r = v.valida({"partes": novas}, textos)
    v.imprime(r, ", ".join(a.partes), fontes)
    if r.erros:
        print("\nNada foi gravado. Corrija os erros e rode o comando de novo.")
        return 1

    nome = (a.arquivo or a.id).removesuffix(".json") + ".json"
    destino = REPO / "dados" / "normas" / nome
    if destino.exists() and not (a.acrescentar or a.substituir):
        print(f"\nERRO: {destino.relative_to(REPO)} já existe. Use --acrescentar (somar partes) ou --substituir.")
        return 1

    if destino.exists() and a.acrescentar:
        material = json.loads(destino.read_text(encoding="utf-8"))
        proximo = max([p.get("numero", i + 1) for i, p in enumerate(material["partes"])] or [0]) + 1
        material.setdefault("alteracoes", [])
        material["alteracoes"] += [n for n in a.nota if n not in material["alteracoes"]]
        if a.titulo:
            material["titulo"] = a.titulo
    else:
        proximo = 1
        material = {
            "id": a.id,
            "titulo": a.titulo or f"{meta['tipo']} nº {meta['numero']}/{meta['ano']}",
            "ementa": meta["ementa"],
            "fonte": meta["pdfs"][0]["url"] if meta.get("pdfs") else "",
            "alteracoes": list(a.nota),
            "partes": [],
        }
    for parte in novas:
        numero = parte.get("numero") if (parte.get("numero") and not a.acrescentar) else proximo
        proximo = numero + 1
        resto = {k: val for k, val in parte.items() if k != "numero"}
        material["partes"].append({"numero": numero, **resto})
    grava_json(destino, material)

    caminho_rel = f"dados/normas/{nome}"
    for i in [a.id] + a.ids:
        por_id[i]["material"] = caminho_rel
    grava_json(REGISTRO, reg)

    mapa = json.loads(v.FONTES.read_text(encoding="utf-8")) if v.FONTES.exists() else {}
    mapa[nome] = list(dict.fromkeys(mapa.get(nome, []) + fontes))
    grava_json(v.FONTES, mapa)

    total = sum(len(p.get("questoes", [])) for p in material["partes"])
    print(f"\nGravado: {caminho_rel} ({len(material['partes'])} parte(s), {total} questões).")
    print(f"Registro: material ligado a {', '.join([a.id] + a.ids)} em dados/normas.json.")
    print(f"\nPróximo passo: python ferramentas/testa_norma.py {a.id}")
    print(f"Depois, publique: dados/normas/{nome}, dados/normas.json e ferramentas/fontes.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
