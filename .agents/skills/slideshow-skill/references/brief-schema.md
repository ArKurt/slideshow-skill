# Storybook brief contract

Use UTF-8 JSON. Paths are resolved relative to the brief file. The renderer reads local files only and never downloads an asset.

## Root fields

| Field | Required | Meaning |
| --- | --- | --- |
| `schema_version` | yes | Use `0.1.0` for this contract. |
| `meta` | yes | Deck identity and language. |
| `style` | no | Warm-editorial color and font overrides. |
| `assets` | yes | Asset records keyed by stable IDs. May be empty. |
| `pages` | yes | Ordered component records; at least one page. |

## `meta`

```json
{
  "title": "项目名称",
  "subtitle": "可选副标题",
  "language": "zh-CN",
  "footer_label": "PROJECT STORYBOOK",
  "status": "internal_review"
}
```

Only `title` is required. `status` is source metadata and is not rendered automatically.

## `style`

All colors must be six-digit hex values. Font values are installed font-family names, not font files.

```json
{
  "paper": "#f1ecdf",
  "ink": "#191714",
  "muted": "#756f65",
  "dark": "#181512",
  "oxblood": "#762b25",
  "brass": "#b08b57",
  "serif": "Noto Serif CJK SC",
  "sans": "Noto Sans CJK SC"
}
```

## `assets`

Keep provenance with every retained image. The renderer consumes `path`, `alt`, `caption`, `fit`, and `position`; the other fields remain in the editable brief and appear on `asset_manifest` pages.

```json
{
  "hero-a": {
    "path": "images/hero-a.jpg",
    "title": "作品或场景名称",
    "alt": "无障碍描述",
    "caption": "图片说明",
    "credit": "摄影 / 品牌 / 档案来源",
    "fit": "cover",
    "position": "50% 40%",
    "source_page": "https://example.org/source",
    "asset_url": "https://example.org/original.jpg",
    "product_id": "optional-stable-id",
    "retrieved_at": "2026-07-12T00:00:00Z",
    "sha256": "optional-checksum",
    "license_status": "unknown",
    "license_notes": "Review before external publication.",
    "review": "pending"
  }
}
```

`fit` is `cover` or `contain`. `position` accepts CSS `object-position`. Remote `http`/`https` paths are linked but never fetched; local assets are embedded by default.

## Common page fields

Every page requires `type`. These fields are shared when relevant:

```json
{
  "type": "statement_centered",
  "theme": "light",
  "section": "curatorial statement",
  "eyebrow": "CURATORIAL STATEMENT · 策展命题",
  "title": "一页只讲一个判断",
  "subtitle": "可选副标题",
  "body": ["第一段。", "可选第二段。"]
}
```

`theme` is `light`, `dark`, or `oxblood`. `body` may be a string or an array of paragraphs.

## Page components

### `cover_split`

Uses common heading fields plus `images`, an array of up to two asset IDs.

### `statement_centered` and `chapter_opener`

Use only common heading and body fields. Choose `chapter_opener` for a pacing break.

### `image_text_spread`

```json
{
  "type": "image_text_spread",
  "image": "hero-a",
  "image_side": "right",
  "facts": [
    {"label": "地点", "value": "苏州"},
    {"label": "阶段", "value": "概念方案"}
  ]
}
```

`image_side` is `left` or `right`.

### `compare`

Use two or three columns:

```json
{
  "type": "compare",
  "columns": [
    {"title": "线索 A", "body": "说明。"},
    {"title": "线索 B", "body": "说明。"}
  ]
}
```

### `card_grid`

Use up to six cards. Four or fewer are safest for normal copy length.

```json
{
  "type": "card_grid",
  "cards": [
    {"number": "01", "title": "材料", "body": "说明。"}
  ]
}
```

### `timeline`

Use up to six items; four or fewer are safest.

```json
{
  "type": "timeline",
  "items": [
    {"kicker": "01 · INPUT", "title": "整理输入", "body": "说明。"}
  ]
}
```

### `asset_manifest`

Set `assets` to an ordered list of asset IDs. Omit it to show every asset. The page renders title, credit, rights status, review status, and source page.

### `closing_quote`

Use common heading and body fields. Keep the title concise.

## Preflight interpretation

`--preflight` asks a local Chromium-family browser to measure page content. `overflow_pages` identifies pages whose content box exceeded its fixed print boundary. A clean result does not detect poor line breaks, image crops, font substitutions, or visual imbalance; always inspect rendered pages.
