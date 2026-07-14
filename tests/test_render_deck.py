import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / ".agents" / "skills" / "slideshow-skill"
SCRIPT = SKILL_ROOT / "scripts" / "render_deck.py"
EXAMPLE_BRIEF = SKILL_ROOT / "assets" / "example-brief.json"

SPEC = importlib.util.spec_from_file_location("slideshow_skill_renderer", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
render_deck = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(render_deck)


class RenderDeckTest(unittest.TestCase):
    def test_example_brief_renders_portable_html(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "example.html"
            report = render_deck.build(EXAMPLE_BRIEF, output)
            html = output.read_text(encoding="utf-8")

        self.assertEqual(report["pages"], 9)
        self.assertEqual(report["warnings"], [])
        self.assertIn("现代生活的两种尺度", html)
        self.assertIn("data:image/svg+xml;base64,", html)
        self.assertEqual(html.count('class="slide '), 9)
        self.assertEqual(html.count('data-screen-label="'), 9)
        self.assertEqual(html.count('data-od-id="slide-'), 9)

    def test_html_has_standalone_and_open_design_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "example.html"
            render_deck.build(EXAMPLE_BRIEF, output)
            html = output.read_text(encoding="utf-8")

        self.assertIn('id="deck-cur"', html)
        self.assertNotIn('id="deck-current"', html)
        self.assertIn('data.type !== "od:slide"', html)
        self.assertIn('data.action === "go"', html)
        self.assertIn("MutationObserver", html)
        self.assertIn("@media print", html)
        self.assertIn(".slide.active", html)
        self.assertIn("上一页", html)

    def test_unknown_component_is_rejected(self) -> None:
        brief = json.loads(EXAMPLE_BRIEF.read_text(encoding="utf-8"))
        brief["pages"][0]["type"] = "freeform_canvas"

        with self.assertRaisesRegex(ValueError, "pages\\[0\\]\\.type"):
            render_deck.validate_brief(brief)


if __name__ == "__main__":
    unittest.main()
