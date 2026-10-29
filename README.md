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
prompts/notebooklm.md       prompt para gerar o material de uma norma
```

O site não tem etapa de compilação: tudo o que está no repositório é publicado como está.

## Como incluir o material de uma norma

1. Gere as partes no NotebookLM com o prompt de `prompts/notebooklm.md`.
2. Crie (ou abra) o arquivo `dados/normas/<id>.json`. Use `dados/normas/dl-70-1990.json` como modelo.
   O `<id>` segue o padrão de `dados/normas.json`: `dl-70-1990`, `res-11-1991` etc.
3. Cole cada parte gerada dentro da lista `"partes": [ ]`, separando as partes por vírgula:

   ```json
   "partes": [
     { "titulo": "...", "artigos": "...", "resumo": [...], "questoes": [...] },
     { "titulo": "...", "artigos": "...", "resumo": [...], "questoes": [...] }
   ]
   ```

4. Em `dados/normas.json`, localize a norma e troque `"material": null` pelo caminho do arquivo,
   por exemplo `"material": "dados/normas/res-11-1991.json"`.
5. Salve e envie para o GitHub (commit). O site atualiza sozinho em um ou dois minutos.

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
