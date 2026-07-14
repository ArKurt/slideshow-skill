#!/usr/bin/env python3
"""Render a structured curatorial storybook brief to HTML and optional PDF."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


COMPONENTS = {
    "cover_split",
    "statement_centered",
    "chapter_opener",
    "image_text_spread",
    "compare",
    "card_grid",
    "timeline",
    "asset_manifest",
    "closing_quote",
}
THEMES = {"light", "dark", "oxblood"}
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

DEFAULT_STYLE = {
    "paper": "#f1ecdf",
    "ink": "#191714",
    "muted": "#756f65",
    "dark": "#181512",
    "oxblood": "#762b25",
    "brass": "#b08b57",
    "serif": "Noto Serif CJK SC",
    "sans": "Noto Sans CJK SC",
}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read brief {path}: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError("The brief root must be a JSON object")
    return payload


def validate_brief(brief: dict[str, Any]) -> None:
    meta = brief.get("meta")
    if not isinstance(meta, dict) or not str(meta.get("title", "")).strip():
        raise ValueError("meta.title is required")
    assets = brief.get("assets", {})
    if not isinstance(assets, dict):
        raise ValueError("assets must be an object keyed by asset id")
    pages = brief.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("pages must be a non-empty array")
    for index, page in enumerate(pages, start=1):
        if not isinstance(page, dict):
            raise ValueError(f"pages[{index - 1}] must be an object")
        component = page.get("type")
        if component not in COMPONENTS:
            raise ValueError(
                f"pages[{index - 1}].type must be one of {sorted(COMPONENTS)}"
            )
        theme = page.get("theme", "light")
        if theme not in THEMES:
            raise ValueError(f"pages[{index - 1}].theme must be one of {sorted(THEMES)}")


def _text(value: Any) -> str:
    return escape(str(value or ""), quote=True).replace("\n", "<br />")


def _paragraphs(value: Any) -> str:
    values = value if isinstance(value, list) else [value]
    return "".join(f'<p class="copy">{_text(item)}</p>' for item in values if item)


def _title_size(value: Any) -> str:
    length = len(str(value or "").replace("\n", ""))
    if length <= 18:
        return "title-xl"
    if length <= 34:
        return "title-lg"
    if length <= 60:
        return "title-md"
    return "title-sm"


def _style_values(brief: dict[str, Any]) -> dict[str, str]:
    supplied = brief.get("style", {})
    if not isinstance(supplied, dict):
        supplied = {}
    style = dict(DEFAULT_STYLE)
    for key in ("paper", "ink", "muted", "dark", "oxblood", "brass"):
        value = supplied.get(key)
        if isinstance(value, str) and HEX_COLOR.match(value):
            style[key] = value
    for key in ("serif", "sans"):
        value = supplied.get(key)
        if isinstance(value, str) and value.strip():
            style[key] = value.strip().replace('"', "")
    return style


def _asset_source(
    asset_id: str,
    asset: dict[str, Any],
    brief_path: Path,
    asset_mode: str,
    warnings: list[str],
) -> str:
    raw_path = str(asset.get("path", "")).strip()
    if not raw_path:
        warnings.append(f"Asset {asset_id!r} has no path; rendered as a placeholder")
        return ""
    parsed = urlparse(raw_path)
    if parsed.scheme in {"http", "https"}:
        warnings.append(
            f"Asset {asset_id!r} is remote; renderer links it but never downloads it"
        )
        return raw_path
    local_path = Path(raw_path).expanduser()
    if not local_path.is_absolute():
        local_path = brief_path.parent / local_path
    local_path = local_path.resolve()
    if not local_path.is_file():
        warnings.append(f"Asset {asset_id!r} was not found at {local_path}")
        return ""
    if asset_mode == "link":
        return local_path.as_uri()
    mime = mimetypes.guess_type(local_path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(local_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _prepare_assets(
    brief: dict[str, Any], brief_path: Path, asset_mode: str, warnings: list[str]
) -> dict[str, dict[str, Any]]:
    prepared: dict[str, dict[str, Any]] = {}
    for asset_id, value in brief.get("assets", {}).items():
        if not isinstance(value, dict):
            warnings.append(f"Asset {asset_id!r} is not an object and was ignored")
            continue
        asset = dict(value)
        asset["src"] = _asset_source(str(asset_id), asset, brief_path, asset_mode, warnings)
        prepared[str(asset_id)] = asset
    return prepared


def _image(
    asset_id: str | None,
    assets: dict[str, dict[str, Any]],
    warnings: list[str],
    *,
    large: bool = False,
) -> str:
    asset = assets.get(str(asset_id)) if asset_id else None
    classes = "image-panel large" if large else "image-panel"
    if asset is None:
        if asset_id:
            warnings.append(f"Page references unknown asset {asset_id!r}")
        label = str(asset_id or "IMAGE")
        return f'<figure class="{classes}"><div class="placeholder">{_text(label)}</div></figure>'
    label = asset.get("title") or asset.get("alt") or asset_id
    caption = asset.get("caption") or asset.get("credit") or ""
    fit = "contain" if asset.get("fit") == "contain" else "cover"
    position = str(asset.get("position", "center")).replace('"', "")
    if asset.get("src"):
        content = (
            f'<img class="fit-{fit}" src="{_text(asset["src"])}" '
            f'alt="{_text(asset.get("alt") or label)}" '
            f'style="object-position:{_text(position)}" />'
        )
    else:
        content = f'<div class="placeholder">{_text(label)}</div>'
    figcaption = f'<figcaption>{_text(caption)}</figcaption>' if caption else ""
    return f'<figure class="{classes}">{content}{figcaption}</figure>'


def _facts(items: Any) -> str:
    if not isinstance(items, list) or not items:
        return ""
    rows = []
    for item in items:
        if isinstance(item, dict):
            rows.append(
                '<div class="fact"><b>'
                + _text(item.get("label"))
                + "</b><span>"
                + _text(item.get("value"))
                + "</span></div>"
            )
    return '<div class="facts">' + "".join(rows) + "</div>"


def _heading(page: dict[str, Any]) -> str:
    eyebrow = f'<div class="eyebrow">{_text(page.get("eyebrow"))}</div>' if page.get("eyebrow") else ""
    title = page.get("title", "")
    heading = f'<h2 class="title {_title_size(title)}">{_text(title)}</h2>' if title else ""
    subtitle = f'<div class="subtitle">{_text(page.get("subtitle"))}</div>' if page.get("subtitle") else ""
    return eyebrow + heading + subtitle


def _render_component(
    page: dict[str, Any], assets: dict[str, dict[str, Any]], warnings: list[str]
) -> str:
    component = page["type"]
    if component == "cover_split":
        image_ids = page.get("images", [])
        if not isinstance(image_ids, list):
            image_ids = []
        images = "".join(_image(str(asset_id), assets, warnings) for asset_id in image_ids[:2])
        if not images:
            images = _image(None, assets, warnings)
        return (
            '<div class="cover-grid"><div class="cover-copy">'
            + _heading(page)
            + _paragraphs(page.get("body"))
            + '</div><div class="cover-images">'
            + images
            + "</div></div>"
        )
    if component == "statement_centered":
        return '<div class="statement">' + _heading(page) + '<div class="rule"></div>' + _paragraphs(page.get("body")) + "</div>"
    if component == "chapter_opener":
        return '<div class="chapter">' + _heading(page) + _paragraphs(page.get("body")) + "</div>"
    if component == "image_text_spread":
        image_html = _image(str(page.get("image", "")), assets, warnings, large=True)
        copy_html = '<div class="spread-copy">' + _heading(page) + _paragraphs(page.get("body")) + _facts(page.get("facts")) + "</div>"
        if page.get("image_side", "right") == "left":
            return '<div class="spread">' + image_html + copy_html + "</div>"
        return '<div class="spread">' + copy_html + image_html + "</div>"
    if component == "compare":
        columns = page.get("columns", [])
        cards = []
        if isinstance(columns, list):
            for column in columns[:3]:
                if isinstance(column, dict):
                    cards.append(
                        '<article class="compare-card"><h3>'
                        + _text(column.get("title"))
                        + "</h3>"
                        + _paragraphs(column.get("body"))
                        + "</article>"
                    )
        return _heading(page) + _paragraphs(page.get("body")) + f'<div class="compare columns-{max(1, len(cards))}">' + "".join(cards) + "</div>"
    if component == "card_grid":
        cards = []
        items = page.get("cards", [])
        if isinstance(items, list):
            for index, item in enumerate(items[:6], start=1):
                if isinstance(item, dict):
                    cards.append(
                        '<article class="grid-card"><div class="card-num">'
                        + _text(item.get("number") or f"{index:02d}")
                        + "</div><h3>"
                        + _text(item.get("title"))
                        + "</h3>"
                        + _paragraphs(item.get("body"))
                        + "</article>"
                    )
        return _heading(page) + f'<div class="card-grid cards-{min(4, max(1, len(cards)))}">' + "".join(cards) + "</div>"
    if component == "timeline":
        items = page.get("items", [])
        cards = []
        if isinstance(items, list):
            for index, item in enumerate(items[:6], start=1):
                if isinstance(item, dict):
                    cards.append(
                        '<article class="timeline-item"><div class="timeline-kicker">'
                        + _text(item.get("kicker") or f"{index:02d}")
                        + "</div><h3>"
                        + _text(item.get("title"))
                        + "</h3>"
                        + _paragraphs(item.get("body"))
                        + "</article>"
                    )
        return _heading(page) + f'<div class="timeline-grid items-{min(4, max(1, len(cards)))}">' + "".join(cards) + "</div>"
    if component == "asset_manifest":
        requested = page.get("assets")
        asset_ids = requested if isinstance(requested, list) else list(assets)
        rows = []
        for asset_id in asset_ids:
            asset = assets.get(str(asset_id), {})
            rows.append(
                "<tr><td>"
                + _text(asset.get("title") or asset_id)
                + "</td><td>"
                + _text(asset.get("credit"))
                + "</td><td>"
                + _text(asset.get("license_status", "unknown"))
                + "</td><td>"
                + _text(asset.get("review", "pending"))
                + "</td><td>"
                + _text(asset.get("source_page"))
                + "</td></tr>"
            )
        return (
            _heading(page)
            + '<table class="asset-table"><thead><tr><th>Asset</th><th>Credit</th><th>Rights</th><th>Review</th><th>Source</th></tr></thead><tbody>'
            + "".join(rows)
            + "</tbody></table>"
            + _paragraphs(page.get("body"))
        )
    if component == "closing_quote":
        return '<div class="closing">' + _heading(page) + '<div class="rule centered"></div>' + _paragraphs(page.get("body")) + "</div>"
    raise AssertionError(component)


def _css(style: dict[str, str]) -> str:
    return """
@page { size: A4 landscape; margin: 0; }
* { box-sizing: border-box; }
:root {
  --paper: %(paper)s; --ink: %(ink)s; --muted: %(muted)s;
  --dark: %(dark)s; --oxblood: %(oxblood)s; --brass: %(brass)s;
  --serif: "%(serif)s", "Source Han Serif SC", serif;
  --sans: "%(sans)s", "Source Han Sans SC", sans-serif;
}
html, body { margin: 0; background: #e6dfd1; }
body { color: var(--ink); font-family: var(--sans); }
.slide { width: 297mm; height: 210mm; page-break-after: always; overflow: hidden; position: relative; padding: 16mm 16mm 12mm; background: var(--paper); }
.slide.dark { color: #f5eddf; background: var(--dark); }
.slide.oxblood { color: #f7eee1; background: var(--oxblood); }
.slide-content { height: 172mm; overflow: hidden; }
.eyebrow { color: var(--brass); font-size: 9px; font-weight: 700; letter-spacing: .34em; text-transform: uppercase; }
.title { margin: 8mm 0 0; font-family: var(--serif); font-weight: 400; line-height: 1.14; letter-spacing: .015em; }
.title-xl { font-size: 58px; }.title-lg { font-size: 46px; }.title-md { font-size: 34px; }.title-sm { font-size: 27px; }
.subtitle { margin-top: 7mm; color: var(--brass); font-family: var(--serif); font-size: 19px; line-height: 1.55; }
.copy { max-width: 132mm; margin: 7mm 0 0; color: #3e3931; font-size: 14px; line-height: 1.82; }
.dark .copy, .oxblood .copy { color: #efe6d8; }
.rule { width: 28mm; height: 1px; margin-top: 8mm; background: var(--brass); }.centered { margin-left: auto; margin-right: auto; }
.footer { position: absolute; left: 16mm; right: 16mm; bottom: 8mm; display: grid; grid-template-columns: 1fr auto auto; gap: 12mm; color: var(--muted); font-size: 8px; letter-spacing: .25em; text-transform: uppercase; }
.dark .footer, .oxblood .footer { color: #b9aa95; }
.cover-grid { display: grid; grid-template-columns: minmax(0, 46fr) minmax(0, 54fr); gap: 12mm; height: 100%%; }.cover-copy { padding-top: 5mm; }.cover-copy .copy { margin-top: 18mm; }.cover-images { display: grid; grid-auto-rows: minmax(0, 1fr); gap: 7mm; min-height: 0; }
.image-panel { position: relative; margin: 0; min-height: 62mm; overflow: hidden; background: linear-gradient(135deg, rgba(176,139,87,.24), rgba(118,43,37,.10)), #ded4c2; }
.image-panel.large { min-height: 144mm; height: 144mm; }.image-panel img { display: block; width: 100%%; height: 100%%; min-height: inherit; }.fit-cover { object-fit: cover; }.fit-contain { object-fit: contain; }
.image-panel figcaption { position: absolute; left: 5mm; right: 5mm; bottom: 4mm; color: #fff8ec; font-size: 9px; line-height: 1.45; text-shadow: 0 1px 5px #000; }
.placeholder { height: 100%%; min-height: inherit; display: grid; place-items: center; padding: 8mm; color: #5f5548; font-family: var(--serif); font-size: 21px; text-align: center; }
.statement { padding: 12mm 10mm; }.statement .title { max-width: 225mm; }.statement .copy { margin-top: 12mm; max-width: 155mm; }
.chapter { height: 100%%; display: flex; flex-direction: column; justify-content: center; }.chapter .title { max-width: 230mm; }.chapter .copy { max-width: 155mm; }
.spread { display: grid; grid-template-columns: 1fr 1fr; gap: 14mm; align-items: start; }.spread-copy { padding-top: 3mm; }.spread-copy .copy { max-width: 118mm; }
.facts { margin-top: 9mm; border-top: 1px solid rgba(176,139,87,.7); }.fact { display: grid; grid-template-columns: 28mm 1fr; gap: 7mm; padding: 4mm 0; border-bottom: 1px solid rgba(176,139,87,.35); font-size: 11px; }.fact b { color: var(--brass); }
.compare { display: grid; gap: 10mm; margin-top: 13mm; }.columns-1 { grid-template-columns: 1fr; }.columns-2 { grid-template-columns: repeat(2, 1fr); }.columns-3 { grid-template-columns: repeat(3, 1fr); }
.compare-card { border-top: 1px solid var(--brass); padding-top: 6mm; }.compare-card h3, .grid-card h3, .timeline-item h3 { margin: 0; font-family: var(--serif); font-size: 23px; font-weight: 400; }.compare-card .copy, .grid-card .copy, .timeline-item .copy { max-width: none; margin-top: 4mm; font-size: 12px; }
.card-grid { display: grid; gap: 7mm; margin-top: 14mm; }.cards-1 { grid-template-columns: 1fr; }.cards-2 { grid-template-columns: repeat(2, 1fr); }.cards-3 { grid-template-columns: repeat(3, 1fr); }.cards-4 { grid-template-columns: repeat(4, 1fr); }
.grid-card { min-height: 67mm; border-top: 2px solid var(--brass); padding-top: 5mm; }.card-num { margin-bottom: 5mm; color: var(--brass); font-family: var(--serif); font-size: 28px; }
.timeline-grid { display: grid; gap: 7mm; margin-top: 16mm; grid-template-columns: repeat(4, 1fr); }.timeline-item { border-top: 1px solid var(--brass); padding-top: 6mm; }.timeline-kicker { margin-bottom: 5mm; color: var(--brass); font-size: 10px; letter-spacing: .18em; }
.asset-table { width: 100%%; margin-top: 10mm; border-collapse: collapse; table-layout: fixed; font-size: 10px; }.asset-table th { color: var(--brass); font-size: 8px; letter-spacing: .16em; text-align: left; text-transform: uppercase; }.asset-table th, .asset-table td { padding: 3.5mm 2mm; border-bottom: 1px solid rgba(176,139,87,.35); vertical-align: top; overflow-wrap: anywhere; }.asset-table th:last-child, .asset-table td:last-child { width: 35%%; }
.closing { height: 100%%; display: grid; align-content: center; justify-items: center; text-align: center; }.closing .title { max-width: 220mm; }.closing .copy { max-width: 145mm; }
.deck-nav { display: none; }
.deck-hint { display: none; }
@media screen {
  html, body { width: 100%%; height: 100%%; overflow: hidden; }
  .slide { display: none; position: absolute; inset: 0 auto auto 0; margin: 0; transform-origin: top left; box-shadow: 0 10px 32px rgba(30,24,18,.12); }
  .slide.active { display: block; }
  .deck-nav { position: fixed; z-index: 20; left: 50%%; bottom: 10px; display: grid; grid-template-columns: auto auto auto; align-items: stretch; transform: translateX(-50%%); color: #f1ecdf; background: #181512; border: 1px solid rgba(176,139,87,.55); font-family: var(--sans); }
  .deck-nav button { min-width: 84px; padding: 12px 18px; color: inherit; background: transparent; border: 0; cursor: pointer; font: inherit; }
  .deck-nav button:hover:not(:disabled) { background: var(--oxblood); }
  .deck-nav button:disabled { opacity: .35; cursor: default; }
  .deck-count { min-width: 92px; padding: 12px 18px; border-inline: 1px solid rgba(176,139,87,.4); text-align: center; font-variant-numeric: tabular-nums; letter-spacing: .18em; }
  .deck-hint { position: fixed; right: 16px; bottom: 12px; z-index: 20; display: block; color: #756f65; font: 11px var(--sans); letter-spacing: .12em; }
}
@media print {
  html, body { background: #fff; overflow: visible; }
  .slide { display: block !important; position: relative; transform: none !important; box-shadow: none; }
  .deck-nav, .deck-hint { display: none !important; }
}
""" % style


def render_html(
    brief: dict[str, Any], brief_path: Path, *, asset_mode: str = "embed"
) -> tuple[str, list[str]]:
    validate_brief(brief)
    warnings: list[str] = []
    assets = _prepare_assets(brief, brief_path, asset_mode, warnings)
    meta = brief["meta"]
    slides = []
    for index, page in enumerate(brief["pages"], start=1):
        theme = page.get("theme", "light")
        footer = (
            '<footer class="footer"><span>'
            + _text(meta.get("footer_label") or meta["title"])
            + "</span><span>"
            + _text(page.get("section") or page["type"].replace("_", " "))
            + f"</span><span>{index:02d}</span></footer>"
        )
        active = " active" if index == 1 else ""
        label = page.get("section") or page["type"].replace("_", " ")
        slides.append(
            f'<section class="slide {theme}{active}" data-page="{index}" '
            f'data-screen-label="{index:02d} {_text(label)}" data-od-id="slide-{index:02d}">'
            '<div class="slide-content">'
            + _render_component(page, assets, warnings)
            + "</div>"
            + footer
            + "</section>"
        )
    style = _style_values(brief)
    language = str(meta.get("language", "zh-CN"))
    is_chinese = language.lower().startswith("zh")
    nav_text = {
        "label": "演示文稿导航" if is_chinese else "Presentation navigation",
        "previous": "上一页" if is_chinese else "Previous",
        "previous_aria": "上一页" if is_chinese else "Previous slide",
        "next": "下一页" if is_chinese else "Next",
        "next_aria": "下一页" if is_chinese else "Next slide",
        "hint": "← → · 空格" if is_chinese else "← → · Space",
    }
    html = """<!doctype html>
<html lang="%(language)s"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>%(title)s</title><style>%(css)s</style></head>
<body data-overflow-pages=""><main class="deck" data-od-id="storybook-deck">%(slides)s</main>
<nav class="deck-nav" aria-label="%(nav_label)s" data-od-id="deck-navigation">
  <button type="button" id="deck-prev" aria-label="%(previous_aria)s">%(previous)s</button>
  <span class="deck-count" aria-live="polite"><span id="deck-cur">01</span> / <span id="deck-total">%(page_count)02d</span></span>
  <button type="button" id="deck-next" aria-label="%(next_aria)s">%(next)s</button>
</nav>
<div class="deck-hint" aria-hidden="true">%(hint)s</div>
<script>
(function () {
  const slides = Array.from(document.querySelectorAll(".slide"));
  const previous = document.getElementById("deck-prev");
  const next = document.getElementById("deck-next");
  const current = document.getElementById("deck-cur");
  const total = document.getElementById("deck-total");
  const storeKey = "slideshow-skill:%(storage_key)s:page";
  let index = 0;
  let painting = false;

  function pad(value) { return String(value).padStart(2, "0"); }

  function readInitialIndex() {
    const hashMatch = location.hash.match(/^#page-(\\d{1,3})$/);
    if (hashMatch) return Number(hashMatch[1]) - 1;
    try { return Number(localStorage.getItem(storeKey) || 0); } catch (_) { return 0; }
  }

  function fit() {
    const page = slides[index];
    if (!page || matchMedia("print").matches) return;
    const pageWidth = page.offsetWidth;
    const pageHeight = page.offsetHeight;
    const scale = Math.min((innerWidth - 32) / pageWidth, (innerHeight - 88) / pageHeight);
    const x = Math.max(16, (innerWidth - pageWidth * scale) / 2);
    const y = Math.max(16, (innerHeight - 72 - pageHeight * scale) / 2);
    slides.forEach((slide) => {
      slide.style.transform = `translate(${x}px, ${y}px) scale(${scale})`;
    });
  }

  function updateChrome(updateLocation) {
    current.textContent = pad(index + 1);
    total.textContent = pad(slides.length);
    previous.disabled = index === 0;
    next.disabled = index === slides.length - 1;
    if (updateLocation) {
      try { localStorage.setItem(storeKey, String(index)); } catch (_) {}
      history.replaceState(null, "", `#page-${pad(index + 1)}`);
    }
    fit();
  }

  function paint(updateLocation = true) {
    painting = true;
    slides.forEach((slide, slideIndex) => slide.classList.toggle("active", slideIndex === index));
    painting = false;
    updateChrome(updateLocation);
  }

  function go(target, updateLocation = true) {
    index = Math.max(0, Math.min(slides.length - 1, Number(target) || 0));
    paint(updateLocation);
  }

  function actionTarget(data) {
    if (data.action === "go" && Number.isFinite(data.index)) return data.index;
    if (data.action === "next") return index + 1;
    if (data.action === "prev") return index - 1;
    if (data.action === "first") return 0;
    if (data.action === "last") return slides.length - 1;
    return null;
  }

  function onKey(event) {
    const target = event.target;
    if (target && (target.matches("input, textarea, select") || target.isContentEditable)) return;
    if (["ArrowRight", "PageDown", " "].includes(event.key)) {
      event.preventDefault();
      go(index + 1);
    } else if (["ArrowLeft", "PageUp"].includes(event.key)) {
      event.preventDefault();
      go(index - 1);
    } else if (event.key === "Home") {
      event.preventDefault();
      go(0);
    } else if (event.key === "End") {
      event.preventDefault();
      go(slides.length - 1);
    }
  }

  function measureOverflow() {
    const overflowPages = [];
    slides.forEach((slide, slideIndex) => {
      const wasActive = slide.classList.contains("active");
      slide.classList.add("active");
      const content = slide.querySelector(".slide-content");
      if (content && (content.scrollHeight > content.clientHeight + 2 || content.scrollWidth > content.clientWidth + 2)) overflowPages.push(slideIndex + 1);
      if (!wasActive) slide.classList.remove("active");
    });
    document.body.dataset.overflowPages = overflowPages.join(",");
  }

  previous.addEventListener("click", () => go(index - 1));
  next.addEventListener("click", () => go(index + 1));
  window.addEventListener("keydown", onKey, true);
  window.addEventListener("resize", fit);
  window.addEventListener("hashchange", () => {
    const match = location.hash.match(/^#page-(\\d{1,3})$/);
    if (match) go(Number(match[1]) - 1, false);
  });
  window.addEventListener("message", (event) => {
    const data = event && event.data;
    if (!data || data.type !== "od:slide") return;
    const target = actionTarget(data);
    if (target !== null) go(target);
  });

  const observer = new MutationObserver(() => {
    if (painting) return;
    const active = slides.findIndex((slide) => slide.classList.contains("active") || slide.classList.contains("is-active") || slide.classList.contains("current"));
    if (active >= 0 && active !== index) {
      index = active;
      updateChrome(true);
    }
  });
  slides.forEach((slide) => observer.observe(slide, { attributes: true, attributeFilter: ["class"] }));

  index = Math.max(0, Math.min(slides.length - 1, readInitialIndex()));
  paint();
  measureOverflow();
})();
</script></body></html>
""" % {
        "language": _text(language),
        "title": _text(meta["title"]),
        "css": _css(style),
        "slides": "".join(slides),
        "page_count": len(slides),
        "storage_key": re.sub(r"[^a-z0-9]+", "-", str(meta["title"]).lower()).strip("-") or "deck",
        "nav_label": _text(nav_text["label"]),
        "previous": _text(nav_text["previous"]),
        "previous_aria": _text(nav_text["previous_aria"]),
        "next": _text(nav_text["next"]),
        "next_aria": _text(nav_text["next_aria"]),
        "hint": _text(nav_text["hint"]),
    }
    return html, warnings


def build(
    brief_path: Path,
    output_html: Path,
    *,
    asset_mode: str = "embed",
) -> dict[str, Any]:
    brief_path = brief_path.resolve()
    brief = _read_json(brief_path)
    html, warnings = render_html(brief, brief_path, asset_mode=asset_mode)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(html, encoding="utf-8")
    return {
        "brief": str(brief_path),
        "html": str(output_html.resolve()),
        "pages": len(brief["pages"]),
        "warnings": warnings,
    }


def _find_browser() -> str | None:
    for name in (
        "chromium",
        "chromium-browser",
        "google-chrome",
        "google-chrome-stable",
        "chrome",
        "chrome.exe",
        "msedge",
        "msedge.exe",
    ):
        found = shutil.which(name)
        if found:
            return found
    candidates = []
    local = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("PROGRAMFILES")
    program_files_x86 = os.environ.get("PROGRAMFILES(X86)")
    if local:
        candidates.append(Path(local) / "Google/Chrome/Application/chrome.exe")
    for root in (program_files, program_files_x86):
        if root:
            candidates.extend(
                [
                    Path(root) / "Google/Chrome/Application/chrome.exe",
                    Path(root) / "Microsoft/Edge/Application/msedge.exe",
                ]
            )
    return str(next((path for path in candidates if path.is_file()), "")) or None


def _run_browser(html_path: Path, extra: list[str]) -> subprocess.CompletedProcess[bytes]:
    browser = _find_browser()
    if not browser:
        raise RuntimeError("Chrome, Chromium, or Edge was not found")
    with tempfile.TemporaryDirectory(prefix="storybook-browser-") as profile:
        command = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-crash-reporter",
            f"--user-data-dir={profile}",
            *extra,
            html_path.resolve().as_uri(),
        ]
        return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def preflight(html_path: Path) -> list[int]:
    result = _run_browser(html_path, ["--dump-dom", "--virtual-time-budget=1000"])
    if result.returncode:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Browser preflight failed ({result.returncode}): {stderr}")
    dom = result.stdout.decode("utf-8", errors="replace")
    match = re.search(r'data-overflow-pages="([0-9,]*)"', dom)
    if not match or not match.group(1):
        return []
    return [int(value) for value in match.group(1).split(",")]


def export_pdf(html_path: Path, pdf_path: Path) -> Path:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    result = _run_browser(html_path, [f"--print-to-pdf={pdf_path.resolve()}"])
    if result.returncode:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"PDF export failed ({result.returncode}): {stderr}")
    if not pdf_path.is_file():
        raise RuntimeError("Browser returned success but did not create the PDF")
    return pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="output HTML path")
    parser.add_argument("--asset-mode", choices=("embed", "link"), default="embed")
    parser.add_argument("--pdf", type=Path, help="optional PDF output path")
    parser.add_argument("--preflight", action="store_true", help="check rendered page overflow")
    parser.add_argument("--strict", action="store_true", help="exit 2 if preflight finds overflow")
    args = parser.parse_args()

    try:
        report = build(args.brief, args.output, asset_mode=args.asset_mode)
        if args.preflight:
            report["overflow_pages"] = preflight(args.output)
        if args.pdf:
            report["pdf"] = str(export_pdf(args.output, args.pdf).resolve())
    except (RuntimeError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.strict and report.get("overflow_pages"):
        sys.exit(2)


if __name__ == "__main__":
    main()
