---
name: slideshow-skill
description: Turn curatorial copy, local image assets, provenance records, and optional visual-reference PDFs into a coherent editorial storybook deck, then render a reviewable HTML/PDF with a structured source brief. Use for exhibition proposals, project storybooks, concept decks, image-and-text presentations, reference-style adaptation, or when a client wants a polished PDF without learning a slide workbench. Do not use it to imitate the source document's subject-matter outline or to bypass image rights review.
---

# Slideshow Skill

Create a content-led deck from a reusable component system. Treat a reference PDF as visual evidence, not as a fixed narrative template. Keep the JSON brief, approved assets, and provenance as source; treat HTML and PDF as generated outputs.

## Workflow

1. Accept input in the form most convenient to the user: pasted copy, conversation attachments, named files, individual paths, or folders. Do not require an `inputs/` folder or any fixed directory layout. Inventory the available copy, images, logos, captions, provenance, output requirements, and optional reference PDF. Resolve every image used by the renderer to an accessible local file. Never fetch restricted or unapproved assets.
2. Choose the visual language. If the user supplies a new visual reference or explicit art direction, inspect it and extract a style contract: page ratio, palette, typography roles, spacing, image treatment, recurring components, and density. Otherwise, use the bundled warm-editorial preset by default without asking the user to provide another reference. Do not copy a reference's content framework unless requested.
3. Derive the page sequence from the project narrative. Give every page one primary claim, then select the smallest suitable component for it.
4. Copy `assets/example-brief.json` to the working output directory and replace its sample content. Read `references/brief-schema.md` when creating or validating the brief.
5. Preserve asset provenance in the `assets` map. Use local paths relative to the brief whenever possible. Record rights uncertainty explicitly.
6. Render HTML with the bundled zero-dependency script:

   ```bash
   python scripts/render_deck.py path/to/brief.json --output path/to/deck.html
   ```

7. When Chrome, Chromium, or Edge is available, export PDF and run overflow preflight:

   ```bash
   python scripts/render_deck.py path/to/brief.json --output path/to/deck.html --pdf path/to/deck.pdf --preflight
   ```

8. Render the PDF to page images or inspect representative screenshots. Perform at least one inspect/fix/re-render cycle. Fix text overflow, font substitution, low-resolution images, awkward crops, inconsistent spacing, and missing credits before delivery.
9. Deliver the PDF for review together with the structured brief and linked/approved source assets when editability matters. Keep client-private files and raw assets out of Git.

Guide nontechnical users through the workflow in plain language. Summarize what was received, infer safe defaults, and ask only for information whose absence would materially change the result. Do not require the user to understand JSON, HTML, command lines, or folder conventions. At the end, report the generated file paths and suggest the most useful pages or issues to review first.

## Component selection

- Use `cover_split` for a title plus one or two establishing images.
- Use `statement_centered` for a single curatorial thesis.
- Use `chapter_opener` for a deliberate pacing break.
- Use `image_text_spread` for an object, place, artist, or case study.
- Use `compare` for two or three parallel ideas.
- Use `card_grid` for exhibition zones, principles, or workstreams.
- Use `timeline` for phases and milestones.
- Use `asset_manifest` to expose image provenance and review state.
- Use `closing_quote` for the final proposition or invitation.

Vary the sequence according to the copy. Do not force every component into every deck.

## Editorial rules

- Keep one main judgment per page.
- Prefer a strong image-text relationship over decorative density.
- Shorten copy before shrinking body text below a comfortable reading size.
- Use explicit line breaks only when they are part of the composition.
- Keep captions and credits close to their images.
- Use the supplied typefaces only when their installation and distribution rights are known; otherwise choose broadly available fallbacks and report substitutions.
- Treat warnings from the renderer as review items, not proof of correctness.

## Reference-style adaptation

Use the bundled warm-editorial preset whenever the user does not provide a new visual reference or explicit style direction. Use an A4 landscape page, warm paper, dark brown, oxblood, brass accents, serif display type, sans-serif body type, generous whitespace, and restrained rules. This preset was derived from the Huqiu reference's visual characteristics only. It is not a hotel, investment, or architecture-story framework.

When a new reference is supplied, update the brief's `style` values and page choices first. Patch the renderer only when the reference demonstrates a reusable component that the current set cannot express.

## Output and compliance

- Default to embedded local images so the HTML is portable. The renderer never downloads remote images.
- PDF is the primary review and delivery format. The JSON brief remains the editable structured source.
- This skill does not currently generate a native office-editable deck. If the client explicitly needs one, treat PPTX as a separate output pilot; do not claim the HTML/PDF is natively editable.
- If an asset has `unknown`, `rights_reserved`, or pending review status, keep that status visible in the brief and avoid external publication without permission.
