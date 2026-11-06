#!/usr/bin/env python3
"""Abre a página de uma norma num navegador invisível, responde todas as questões e confere a página.

Uso, a partir da pasta do repositório:
  python ferramentas/testa_norma.py dl-02-2022
      testa a cópia local (sobe um servidor temporário sozinho)
  python ferramentas/testa_norma.py dl-02-2022 --site https://luiz-hp.github.io/alepa-cargo15/
      testa o site publicado
  python ferramentas/testa_norma.py dl-02-2022 --foto teste.png
      também salva uma foto da página inteira em largura de celular

Requer, uma única vez: pip install playwright   e   python -m playwright install chromium

Confere em 390 px (celular) e 1280 px: se o gabarito de cada questão é aceito como certo,
se há rolagem horizontal, se alguma tabela ficou mais larga que a tela e se há erros de JavaScript.
Código de saída: 0 se tudo passou; 1 se algo falhou.
"""
import argparse
import functools
import http.server
import json
import re
import sys
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


class Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("id")
    ap.add_argument("--site", help="endereço do site publicado; sem esta opção, testa a cópia local")
    ap.add_argument("--foto", help="arquivo .png para a foto da página em largura de celular")
    a = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Instale o Playwright: pip install playwright   e depois   python -m playwright install chromium")
        return 1

    reg = json.loads((REPO / "dados" / "normas.json").read_text(encoding="utf-8"))
    meta = next((n for n in reg["normas"] if n["id"] == a.id), None)
    if not meta or not meta.get("material"):
        print(f"ERRO: '{a.id}' não existe em dados/normas.json ou ainda não tem material.")
        return 1
    material = json.loads((REPO / meta["material"]).read_text(encoding="utf-8"))
    partes = {(p.get("numero") or i + 1): p for i, p in enumerate(material["partes"])}

    servidor = None
    if a.site:
        base = a.site if a.site.endswith("/") else a.site + "/"
    else:
        handler = functools.partial(Silencioso, directory=str(REPO))
        servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{servidor.server_address[1]}/"

    erros_js, falhas = [], []
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        for largura in (390, 1280):
            pg = nav.new_page(viewport={"width": largura, "height": 800})
            pg.on("pageerror", lambda e: erros_js.append(str(e)))
            pg.on("console", lambda m: m.type == "error" and erros_js.append(m.text))
            pg.goto(f"{base}?t={id(pg)}#/norma/{a.id}")
            pg.wait_for_selector("article.questao", timeout=20000)
            total = certas = 0
            for n, p in partes.items():
                for k, q in enumerate(p["questoes"], 1):
                    art = pg.locator(f"article.questao:has(#q{n}-{k})")
                    alvo = re.sub(r"\*\*", "", q["alternativas"][q["gabarito"]])
                    botoes = art.locator("button.alt")
                    achou = False
                    for j in range(botoes.count()):
                        if alvo in botoes.nth(j).inner_text():
                            botoes.nth(j).click()
                            achou = True
                            break
                    veredito = art.locator(".veredito").inner_text() if achou else "alternativa não encontrada"
                    total += 1
                    if veredito.startswith("Certo"):
                        certas += 1
                    else:
                        falhas.append(f"{largura}px, parte {n}, questão {k}: {veredito[:80]}")
            rolagem = pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
            largas = pg.evaluate("[...document.querySelectorAll('table')].filter(t => t.scrollWidth > t.parentElement.clientWidth + 1).length")
            print(f"{largura}px: {certas}/{total} questões aceitas · rolagem horizontal: {'sim' if rolagem else 'não'} · "
                  f"tabelas mais largas que a tela: {largas}")
            if rolagem:
                falhas.append(f"{largura}px: a página rola na horizontal")
            if largas:
                falhas.append(f"{largura}px: {largas} tabela(s) mais larga(s) que a tela; encurte os textos da 1ª coluna")
            if largura == 390 and a.foto:
                pg.screenshot(path=a.foto, full_page=True)
                print(f"Foto salva em {a.foto}")
            pg.close()
        nav.close()
    if servidor:
        servidor.shutdown()

    if erros_js:
        falhas += [f"erro de JavaScript: {e[:160]}" for e in erros_js]
    if falhas:
        print("\nFALHAS:")
        for f in falhas:
            print(" -", f)
        return 1
    print("\nTudo certo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
