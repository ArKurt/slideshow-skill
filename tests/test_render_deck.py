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

    def test_unknown_component_is_rejected(self) -> None:
        brief = json.loads(EXAMPLE_BRIEF.read_text(encoding="utf-8"))
        brief["pages"][0]["type"] = "freeform_canvas"

        with self.assertRaisesRegex(ValueError, "pages\\[0\\]\\.type"):
            render_deck.validate_brief(brief)


if __name__ == "__main__":
    unittest.main()
