#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClippIA Econoroeste — coletor público de notícias.

Verdade técnica:
- Coleta por Google News RSS público.
- Recorte principal: últimas 24 horas (when:1d + validação por pubDate).
- Não promete 100% da internet nem todas as imagens.
- Salva data/noticias.json para o painel do GitHub Pages.
"""

import hashlib
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ARQUIVO = Path("data/noticias.json")
MAX_POR_TERMO = 12
PERIODO_HORAS = 24
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ClippIA-Econoroeste/1.0)"}

# Termos amplos, mas ainda focados em EcoNoroeste/Ecovias Noroeste/Free Flow/pedágio.
TERMOS = [
    '"Ecovias Noroeste Paulista"',
    '"EcoNoroeste"',
    '"Econoroeste"',
    '"Ecovias Noroeste"',
    '"Ecovias Noroeste Paulista" "Free Flow"',
    '"Free Flow" "Ecovias Noroeste"',
    '"freeflow" "Ecovias Noroeste"',
    '"pedágio inteligente" "Ecovias Noroeste"',
    '"pedágio digital" "Ecovias Noroeste"',
    '"pedágio eletrônico" "Ecovias Noroeste"',
    '"pedágio sem cancela" "Ecovias Noroeste"',
    '"pórtico" "Ecovias Noroeste"',
    '"cobrança por placa" "Ecovias Noroeste"',
    '"Ecovias Noroeste" TAG',
    '"Ecovias Noroeste" DUF',
    '"Ecovias Noroeste" multa',
    '"Ecovias Noroeste" reclamação',
    '"Ecovias Noroeste" tarifa',
    '"Ecovias Noroeste" reajuste',
    '"Ecovias Noroeste" obras',
    '"Ecovias Noroeste" interdição',
    '"Ecovias Noroeste" acidente',
    '"Ecovias Noroeste" trânsito',
    '"Ecovias Noroeste" ARTESP',
    '"EcoRodovias" "Ecovias Noroeste"',
    '"SP-310" "Ecovias Noroeste"',
    '"SP-323" "Ecovias Noroeste"',
    '"SP-326" "Ecovias Noroeste"',
    '"SP-333" "Ecovias Noroeste"',
    '"SP-351" "Ecovias Noroeste"',
]

def agora_utc():
    return datetime.now(timezone.utc)

def abrir(url, limite=1200000, timeout=25):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(limite)
        return raw.decode(r.headers.get_content_charset() or "utf-8", errors="replace"), r.geturl()

def limpar(t):
    t = re.sub(r"<[^>]+>", " ", t or "")
    return re.sub(r"\s+", " ", html.unescape(t)).strip()

def normalizar(t):
    return re.sub(r"\s+", " ", limpar(t).lower()).strip()

def parse_data_rss(pub):
    try:
        d = parsedate_to_datetime(pub)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None

def data_iso(pub):
    d = parse_data_rss(pub)
    return d.isoformat() if d else (pub or "")

def dentro_24h(pub):
    d = parse_data_rss(pub)
    if not d:
        return True
    return (agora_utc() - d) <= timedelta(hours=PERIODO_HORAS)

def categoria(txt):
    t = txt.lower()
    if any(x in t for x in ["free flow", "freeflow", "pedágio eletrônico", "pedagio eletronico", "pedágio inteligente", "pedagio inteligente", "pedágio digital", "pedagio digital", "sem cancela", "pórtico", "portico"]):
        return "free flow"
    if any(x in t for x in ["pedágio", "pedagio", "tarifa", "reajuste", "tag", "duf", "cobrança", "cobranca", "placa", "multa"]):
        return "pedágio"
    if any(x in t for x in ["acidente", "morte", "morre", "ferido", "risco"]):
        return "acidente/risco"
    if any(x in t for x in ["obra", "interdição", "interdicao", "bloqueio", "manutenção", "manutencao"]):
        return "obras/interdição"
    if "artesp" in t:
        return "regulatório"
    return "geral"

def img_rss(item):
    for child in list(item):
        tag = child.tag.lower()
        if tag.endswith("content") or tag.endswith("thumbnail"):
            u = child.attrib.get("url") or child.attrib.get("href")
            if u:
                return u
    desc = item.findtext("description") or ""
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc, re.I)
    return html.unescape(m.group(1)) if m else ""

def montar_url_google_news(termo):
    # when:1d força o recorte de últimas 24 horas dentro do Google News.
    q = termo + " when:1d"
    return "https://news.google.com/rss/search?q=" + urllib.parse.quote(q) + "&hl=pt-BR&gl=BR&ceid=BR:pt-419"

def buscar(termo):
    url = montar_url_google_news(termo)
    xml, final_url = abrir(url)
    root = ET.fromstring(xml)
    ch = root.find("channel")
    out = []
    if ch is None:
        return out

    for item in ch.findall("item")[:MAX_POR_TERMO]:
        title = limpar(item.findtext("title") or "")
        link = item.findtext("link") or ""
        desc = limpar(item.findtext("description") or "")
        pub = item.findtext("pubDate") or ""

        if not dentro_24h(pub):
            continue

        src = item.find("source")
        source = limpar(src.text) if src is not None and src.text else "Google News"
        image = img_rss(item)
        texto = " ".join([title, desc, source, termo])
        # De-duplicação por conteúdo jornalístico, não por URL do Google News.
        chave = normalizar(title) + "|" + normalizar(source)
        uid = hashlib.sha256(chave.encode("utf-8")).hexdigest()

        out.append({
            "id": uid,
            "title": title,
            "source": source,
            "link": link,
            "resolved_link": "",
            "published": data_iso(pub),
            "published_raw": pub,
            "snippet": desc,
            "term": termo,
            "category": categoria(texto),
            "image_url": image,
            "image_source": "RSS media" if image else "",
            "search_url": final_url,
            "period": "24h",
            "collected_at": agora_utc().isoformat()
        })
    return out

def main():
    ARQUIVO.parent.mkdir(exist_ok=True)
    por_id = {}
    erros = []

    for termo in TERMOS:
        try:
            for item in buscar(termo):
                if item["id"] not in por_id:
                    por_id[item["id"]] = item
                else:
                    # Mantém rastreio de termos que também acharam o mesmo item.
                    anterior = por_id[item["id"]]
                    termos = set(str(anterior.get("term", "")).split(" | "))
                    termos.add(item["term"])
                    anterior["term"] = " | ".join(sorted(x for x in termos if x))
            time.sleep(0.35)
        except Exception as e:
            erros.append({"termo": termo, "erro": str(e)})

    items = list(por_id.values())
    items.sort(key=lambda x: x.get("published") or x.get("collected_at") or "", reverse=True)
    items = items[:350]

    saida = {
        "updated_at": agora_utc().isoformat(),
        "period": "24h",
        "period_hours": PERIODO_HORAS,
        "total": len(items),
        "total_images": sum(1 for x in items if x.get("image_url")),
        "new_items": len(items),
        "errors": erros,
        "terms": TERMOS,
        "limits": [
            "Coleta por Google News RSS público.",
            "Não garante 100% da internet.",
            "Imagens dependem de metadados disponíveis nas fontes.",
            "Revisão humana obrigatória antes de publicar."
        ],
        "items": items
    }

    ARQUIVO.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK", len(items), "notícias 24h", "imagens", saida["total_images"], "erros", len(erros))

if __name__ == "__main__":
    main()
