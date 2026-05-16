#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib, html, json, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

TERMOS = [
    '"Ecovias Noroeste Paulista"',
    '"EcoNoroeste"',
    '"Econoroeste"',
    '"Ecovias Noroeste"',
    '"free flow" "Ecovias Noroeste"',
    '"pedágio eletrônico" "Ecovias Noroeste"',
    '"pedágio inteligente" "Ecovias Noroeste"',
    '"Ecovias Noroeste Paulista" pedágio',
    '"Ecovias Noroeste Paulista" tarifa',
    '"Ecovias Noroeste Paulista" reajuste',
    '"Ecovias Noroeste Paulista" obras',
    '"Ecovias Noroeste Paulista" interdição',
    '"Ecovias Noroeste Paulista" acidente',
    '"Ecovias Noroeste Paulista" ARTESP',
    '"SP-310" "Ecovias Noroeste"',
    '"SP-326" "Ecovias Noroeste"',
    '"SP-333" "Ecovias Noroeste"',
    '"SP-323" "Ecovias Noroeste"',
    '"SP-351" "Ecovias Noroeste"',
]
ARQUIVO = Path("data/noticias.json")
MAX_POR_TERMO = 8
HEADERS = {"User-Agent": "Mozilla/5.0 ClippIA/1.0"}

def abrir(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read(1200000)
        return raw.decode(r.headers.get_content_charset() or "utf-8", errors="replace"), r.geturl()

def limpar(t):
    t = re.sub(r"<[^>]+>", " ", t or "")
    return re.sub(r"\s+", " ", html.unescape(t)).strip()

def data(pub):
    try:
        d = parsedate_to_datetime(pub)
        if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
        return d.isoformat()
    except: return pub or ""

def cat(txt):
    t = txt.lower()
    if "free flow" in t or "freeflow" in t or "pedágio eletrônico" in t or "pedágio inteligente" in t: return "free flow"
    if "pedágio" in t or "tarifa" in t or "reajuste" in t or "tag" in t: return "pedágio"
    if "acidente" in t or "morte" in t or "ferido" in t: return "acidente"
    if "obra" in t or "interdição" in t or "bloqueio" in t: return "obras/interdição"
    if "artesp" in t: return "regulatório"
    return "geral"

def img_rss(item):
    for child in list(item):
        tag = child.tag.lower()
        if tag.endswith("content") or tag.endswith("thumbnail"):
            u = child.attrib.get("url") or child.attrib.get("href")
            if u: return u
    desc = item.findtext("description") or ""
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc, re.I)
    return html.unescape(m.group(1)) if m else ""

def buscar(termo):
    url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(termo) + "&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    xml, _ = abrir(url)
    root = ET.fromstring(xml)
    ch = root.find("channel")
    out = []
    if ch is None: return out
    for item in ch.findall("item")[:MAX_POR_TERMO]:
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        desc = limpar(item.findtext("description") or "")
        pub = item.findtext("pubDate") or ""
        src = item.find("source")
        source = src.text if src is not None and src.text else "Google News"
        image = img_rss(item)
        uid = hashlib.sha256((title+"|"+link).encode()).hexdigest()
        texto = " ".join([title, desc, source, termo])
        out.append({
            "id": uid, "title": title, "source": source, "link": link,
            "published": data(pub), "published_raw": pub, "snippet": desc,
            "term": termo, "category": cat(texto), "image_url": image,
            "image_source": "RSS media" if image else "",
            "collected_at": datetime.now(timezone.utc).isoformat()
        })
    return out

def carregar():
    if ARQUIVO.exists():
        try: return json.loads(ARQUIVO.read_text(encoding="utf-8"))
        except: pass
    return {"items":[]}

def main():
    ARQUIVO.parent.mkdir(exist_ok=True)
    atual = carregar()
    por_id = {x.get("id"): x for x in atual.get("items", []) if x.get("id")}
    erros, novos = [], 0
    for termo in TERMOS:
        try:
            for item in buscar(termo):
                if item["id"] not in por_id:
                    por_id[item["id"]] = item
                    novos += 1
        except Exception as e:
            erros.append({"termo": termo, "erro": str(e)})
    items = list(por_id.values())
    items.sort(key=lambda x: x.get("published") or x.get("collected_at") or "", reverse=True)
    items = items[:350]
    saida = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(items),
        "total_images": sum(1 for x in items if x.get("image_url")),
        "new_items": novos,
        "errors": erros,
        "terms": TERMOS,
        "items": items
    }
    ARQUIVO.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK", len(items), "novos", novos, "erros", len(erros))

if __name__ == "__main__":
    main()
