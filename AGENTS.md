# Slideshow Skill

This repository packages a client-facing Codex skill for turning curatorial copy and approved local images into editorial HTML/PDF storybook decks.

## Boundaries

- Treat `inputs/` as private client material. Do not commit or upload it.
- Treat `outputs/` as generated deliverables. Do not commit it.
- Use public or user-supplied assets only; preserve source, rights, and review notes.
- Do not fetch remote images or bypass authentication, paywalls, CAPTCHA, DRM, signed links, or anti-bot controls.
- PDF is the primary deliverable. HTML and the JSON brief are generation sources.
- Native editable slide formats are out of scope. PPTX requires a separate validated pilot.

## Workflow

Use `$slideshow-skill` for deck requests. Derive the narrative from the supplied copy, select page components, render, inspect representative pages, fix issues, and render again.

## Verification

```bash
python -m unittest discover -v
python -m compileall -q .agents/skills/slideshow-skill/scripts tests
python .agents/skills/slideshow-skill/scripts/render_deck.py \
  .agents/skills/slideshow-skill/assets/example-brief.json \
  --output outputs/example/deck.html
```

When a Chromium-family browser is available, also run PDF export with `--preflight` and visually inspect the generated pages.
