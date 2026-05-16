#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Coletor gratuito de notícias, links e imagens públicas para ClippIA Econoroeste.

O que ele faz:
1. Busca links no Google News RSS por termos.
2. Busca links em páginas oficiais da Ecovias Noroeste Paulista e Free Flow.
3. Tenta capturar imagem pública da notícia via:
   - media:content / media:thumbnail no RSS
   - og:image
   - twitter:image
   - primeira imagem relevante da página

Limite honesto:
- Não garante "todas as imagens de toda a internet".
- Garante coleta dos links/imagens publicamente encontráveis e acessíveis pelo robô.
- Alguns portais bloqueiam robôs, escondem imagens em JavaScript ou usam paywall.
"""

import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

TERMOS = [
    '"Ecovias Noroeste Paulista"',
    '"EcoNoroeste"',
    '"Econoroeste"',
    '"Ecovias Noroeste"',
    '"free flow" "Ecovias Noroeste"',
    '"freeflow" "Ecovias Noroeste"',
    '"pedágio digital" "Ecovias Noroeste"',
    '"pedágio inteligente" "Ecovias Noroeste"',
    '"Ecovias Noroeste Paulista" "Free Flow"',
    '"Ecovias Noroeste Paulista" pedágio',
    '"Ecovias Noroeste Paulista" tarifa',
    '"Ecovias Noroeste Paulista" reajuste',
    '"Ecovias Noroeste Paulista" obras',
    '"Ecovias Noroeste Paulista" interdição',
    '"Ecovias Noroeste Paulista" acidente',
    '"Ecovias Noroeste Paulista" trânsito',
    '"Ecovias Noroeste Paulista" ARTESP',
    '"EcoNoroeste" Free Flow',
    '"EcoNoroeste" pedágio eletrônico',
    '"EcoNoroeste" cobrança',
    '"SP-310" "Ecovias Noroeste"',
    '"SP-326" "Ecovias Noroeste"',
    '"SP-333" "Ecovias Noroeste"',
    '"SP-323" "Ecovias Noroeste"',
    '"SP-351" "Ecovias Noroeste"',
    '"Washington Luís" "Ecovias Noroeste"',
    '"Rodovia Brigadeiro Faria Lima" "Ecovias Noroeste"',
]

PAGINAS_OFICIAIS = [
    "https://www.ecoviasnoroestepaulista.com.br/todas-as-noticias/",
    "https://www.ecoviasnoroestepaulista.com.br/",
    "https://freeflow.ecoviasnoroestepaulista.com.br/",
    "https://freeflow.ecoviasnoroestepaulista.com.br/como-funciona/",
    "https://freeflow.ecoviasnoroestepaulista.com.br/como-pagar/",
    "https://freeflow.ecoviasnoroestepaulista.com.br/beneficios-da-tag/",
    "https://freeflow.ecoviasnoroestepaulista.com.br/fale-conosco/",
    "https://www.ecorodovias.com.br/noticias/free-flow-econoroeste/",
]

MAX_POR_TERMO = 10
MAX_OFICIAIS = 80
ARQUIVO = Path("data/noticias.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ClippIA/1.2; +https://github.com/)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def abrir_url(url, timeout=25):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        final_url = resp.geturl()
        raw = resp.read(2_000_000)
        charset = resp.headers.get_content_charset() or "utf-8"
        try:
            text = raw.decode(charset, errors="replace")
        except Exception:
            text = raw.decode("utf-8", errors="replace")
        return text, final_url

def absolutizar_url(url, base):
    if not url:
        return ""
    return urllib.parse.urljoin(base, html.unescape(url.strip()))

def limpar_html(texto):
    if not texto:
        return ""
    texto = re.sub(r"<script[\s\S]*?</script>", " ", texto, flags=re.I)
    texto = re.sub(r"<style[\s\S]*?</style>", " ", texto, flags=re.I)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = html.unescape(texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def normalizar_data(pubdate):
    if not pubdate:
        return ""
    try:
        dt = parsedate_to_datetime(pubdate)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return pubdate

def categoria_por_texto(texto):
    t = (texto or "").lower()
    if any(x in t for x in ["free flow", "freeflow", "pedágio digital", "pedagio digital", "pedágio inteligente", "pedagio inteligente"]):
        return "free flow"
    if any(x in t for x in ["pedágio", "pedagio", "tarifa", "reajuste", "tag", "duf", "cobrança", "cobranca"]):
        return "pedágio"
    if any(x in t for x in ["acidente", "morte", "ferido", "sinistro"]):
        return "acidente"
    if any(x in t for x in ["obra", "interdição", "interdicao", "bloqueio", "manutenção", "manutencao"]):
        return "obras/interdição"
    if any(x in t for x in ["artesp", "governo", "diário oficial", "diario oficial"]):
        return "regulatório"
    return "geral"

def hash_id(title, link):
    return hashlib.sha256((title + "|" + link).encode("utf-8")).hexdigest()

def extrair_meta(html_text, base_url):
    def meta_prop(*nomes):
        for nome in nomes:
            patterns = [
                rf'<meta[^>]+property=["\']{re.escape(nome)}["\'][^>]+content=["\']([^"\']+)["\']',
                rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(nome)}["\']',
                rf'<meta[^>]+name=["\']{re.escape(nome)}["\'][^>]+content=["\']([^"\']+)["\']',
                rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']{re.escape(nome)}["\']',
            ]
            for pat in patterns:
                m = re.search(pat, html_text, flags=re.I)
                if m:
                    return absolutizar_url(m.group(1), base_url)
        return ""

    title = meta_prop("og:title", "twitter:title")
    desc = meta_prop("og:description", "twitter:description", "description")
    image = meta_prop("og:image", "og:image:secure_url", "twitter:image", "twitter:image:src")

    if not title:
        m = re.search(r"<title[^>]*>([\s\S]*?)</title>", html_text, flags=re.I)
        if m:
            title = limpar_html(m.group(1))

    if not desc:
        m = re.search(r"<p[^>]*>([\s\S]{30,800}?)</p>", html_text, flags=re.I)
        if m:
            desc = limpar_html(m.group(1))

    if not image:
        imgs = re.findall(r'<img[^>]+(?:src|data-src)=["\']([^"\']+)["\']', html_text, flags=re.I)
        for img in imgs:
            img_abs = absolutizar_url(img, base_url)
            low = img_abs.lower()
            if any(x in low for x in ["logo", "icon", "sprite", "placeholder"]):
                continue
            if any(ext in low for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                image = img_abs
                break

    return {
        "title": limpar_html(title),
        "description": limpar_html(desc),
        "image_url": image,
    }

def extrair_imagem_rss(item):
    for child in list(item):
        tag = child.tag.lower()
        if tag.endswith("content") or tag.endswith("thumbnail"):
            url = child.attrib.get("url") or child.attrib.get("href")
            if url:
                return url
    desc = item.findtext("description") or ""
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc, flags=re.I)
    if m:
        return html.unescape(m.group(1))
    return ""

def enriquecer_com_imagem(link):
    try:
        html_text, final_url = abrir_url(link, timeout=15)
        meta = extrair_meta(html_text, final_url)
        return meta.get("image_url", ""), final_url, meta
    except Exception:
        return "", link, {}

def buscar_google_news(termo):
    q = urllib.parse.quote(termo)
    url = f"https://news.google.com/rss/search?q={q}&hl=pt-BR&gl=BR&ceid=BR:pt-419"

    xml, _ = abrir_url(url)
    root = ET.fromstring(xml)
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for item in channel.findall("item")[:MAX_POR_TERMO]:
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        desc = limpar_html(item.findtext("description") or "")
        pub = item.findtext("pubDate") or ""
        source_node = item.find("source")
        source = source_node.text if source_node is not None and source_node.text else ""
        rss_image = extrair_imagem_rss(item)

        image_url = rss_image
        image_source = "RSS media" if rss_image else ""
        final_link = link

        if not image_url:
            image_url, final_link, _meta = enriquecer_com_imagem(link)
            image_source = "og:image/twitter:image" if image_url else ""

        texto_total = " ".join([title, desc, source, termo])

        items.append({
            "id": hash_id(title, link),
            "title": title,
            "source": source or "Google News",
            "link": link,
            "resolved_link": final_link,
            "published": normalizar_data(pub),
            "published_raw": pub,
            "snippet": desc,
            "term": termo,
            "category": categoria_por_texto(texto_total),
            "image_url": image_url,
            "image_source": image_source,
            "collected_at": datetime.now(timezone.utc).isoformat()
        })
    return items

def extrair_links_oficiais(pagina_url):
    html_text, final_url = abrir_url(pagina_url)
    links = set()

    for href in re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', html_text, flags=re.I):
        href = absolutizar_url(href, final_url)
        low = href.lower()
        if not href.startswith("http"):
            continue
        if (
            "ecoviasnoroestepaulista.com.br/noticias/" in low
            or "freeflow.ecoviasnoroestepaulista.com.br" in low
            or "ecorodovias.com.br/noticias/free-flow-econoroeste" in low
        ):
            links.add(href.split("#")[0])

    return list(links)[:MAX_OFICIAIS]

def coletar_pagina_oficial(url, origem):
    html_text, final_url = abrir_url(url)
    meta = extrair_meta(html_text, final_url)

    title = meta.get("title") or url
    desc = meta.get("description") or ""
    image_url = meta.get("image_url") or ""

    pub = ""
    for pat in [
        r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']article:published_time["\']',
        r'<time[^>]+datetime=["\']([^"\']+)["\']'
    ]:
        m = re.search(pat, html_text, flags=re.I)
        if m:
            pub = m.group(1)
            break

    texto_total = " ".join([title, desc, url])
    return {
        "id": hash_id(title, final_url),
        "title": title,
        "source": origem,
        "link": final_url,
        "resolved_link": final_url,
        "published": pub,
        "published_raw": pub,
        "snippet": desc,
        "term": "fonte oficial",
        "category": categoria_por_texto(texto_total),
        "image_url": image_url,
        "image_source": "og:image/twitter:image/fonte oficial" if image_url else "",
        "collected_at": datetime.now(timezone.utc).isoformat()
    }

def carregar_existente():
    if not ARQUIVO.exists():
        return {"updated_at": None, "items": []}
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except Exception:
        return {"updated_at": None, "items": []}

def main():
    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    existente = carregar_existente()
    por_id = {x.get("id"): x for x in existente.get("items", []) if x.get("id")}

    novos = 0
    erros = []

    for termo in TERMOS:
        try:
            for item in buscar_google_news(termo):
                if item["id"] not in por_id:
                    por_id[item["id"]] = item
                    novos += 1
                elif item.get("image_url") and not por_id[item["id"]].get("image_url"):
                    por_id[item["id"]].update({
                        "image_url": item.get("image_url"),
                        "image_source": item.get("image_source"),
                        "resolved_link": item.get("resolved_link")
                    })
        except Exception as e:
            erros.append({"tipo": "google_news", "termo": termo, "erro": str(e)})

    oficiais = set(PAGINAS_OFICIAIS)
    for pagina in PAGINAS_OFICIAIS:
        try:
            for link in extrair_links_oficiais(pagina):
                oficiais.add(link)
        except Exception as e:
            erros.append({"tipo": "extrair_links_oficiais", "url": pagina, "erro": str(e)})

    for link in list(oficiais)[:MAX_OFICIAIS]:
        try:
            item = coletar_pagina_oficial(link, "Fonte oficial Ecovias/Free Flow")
            if item["id"] not in por_id:
                por_id[item["id"]] = item
                novos += 1
            elif item.get("image_url") and not por_id[item["id"]].get("image_url"):
                por_id[item["id"]].update({
                    "image_url": item.get("image_url"),
                    "image_source": item.get("image_source")
                })
        except Exception as e:
            erros.append({"tipo": "coletar_pagina_oficial", "url": link, "erro": str(e)})

    items = list(por_id.values())
    items.sort(key=lambda x: x.get("published") or x.get("collected_at") or "", reverse=True)
    items = items[:500]
    total_imagens = sum(1 for x in items if x.get("image_url"))

    saida = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(items),
        "total_images": total_imagens,
        "new_items": novos,
        "errors": erros,
        "terms": TERMOS,
        "official_pages": PAGINAS_OFICIAIS,
        "items": items
    }

    ARQUIVO.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Arquivo atualizado: {ARQUIVO}")
    print(f"Total links: {len(items)} | Com imagem: {total_imagens} | Novos: {novos} | Erros: {len(erros)}")
    if erros:
        print(json.dumps(erros[:20], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
