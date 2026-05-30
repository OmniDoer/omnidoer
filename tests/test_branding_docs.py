import json
import pathlib
import unittest


class BrandingDocsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = pathlib.Path(__file__).resolve().parents[1]

    def test_uploaded_icon_was_renamed_to_canonical_icon(self) -> None:
        self.assertTrue((self.root / "icon.png").is_file())
        self.assertFalse((self.root / "file_000000000d447206b4d8684c9ff6c66c.png").exists())

    def test_public_visual_assets_exist_in_multiple_formats(self) -> None:
        for relative in (
            "docs/assets/icon.png",
            "docs/assets/omnidoer-card.png",
            "docs/assets/omnidoer-hero.jpg",
            "docs/assets/omnidoer-cinematic-poster.png",
            "docs/assets/omnidoer-cinematic-poster.jpg",
            "docs/assets/omnidoer-cinematic-readme.png",
            "docs/assets/omnidoer-cinematic-share.jpg",
            "docs/assets/omnidoer-mark.svg",
            "docs/assets/omnidoer-cloud-direct.svg",
            "omnidoer/omni_control/static/icon-192.png",
            "omnidoer/omni_control/static/icon-512.png",
        ):
            self.assertTrue((self.root / relative).is_file(), relative)

    def test_readme_and_agents_keep_multilingual_product_constraints(self) -> None:
        readme = (self.root / "README.md").read_text()
        agents = (self.root / "AGENTS.md").read_text()
        self.assertIn("Languages / 多语言", readme)
        self.assertIn("English", readme)
        self.assertIn("中文", readme)
        self.assertIn("Español", readme)
        self.assertIn("Français", readme)
        self.assertIn("Deutsch", readme)
        self.assertIn("日本語", readme)
        self.assertIn("한국어", readme)
        self.assertIn("does not call OpenAI APIs directly", readme)
        self.assertIn("Cloud Direct Mode", readme)
        self.assertIn("不要把 OmniDoer 做成默认 OpenAI API 客户端", agents)

    def test_github_pages_intro_exists(self) -> None:
        page = (self.root / "docs" / "index.html").read_text()
        self.assertIn("OmniDoer", page)
        self.assertIn("Secrets Stay Out Of The Model", page)
        self.assertIn("Cloud Direct Architecture", page)
        self.assertIn("多语言简介", page)
        self.assertIn("assets/omnidoer-cinematic-poster.jpg", page)
        self.assertIn("assets/omnidoer-cinematic-share.jpg", page)

    def test_pwa_manifest_declares_icons(self) -> None:
        manifest = json.loads((self.root / "omnidoer/omni_control/static/manifest.json").read_text())
        self.assertEqual(manifest["name"], "OmniDoer Control Client")
        icon_srcs = {icon["src"] for icon in manifest["icons"]}
        self.assertEqual(icon_srcs, {"/icon-192.png", "/icon-512.png"})


if __name__ == "__main__":
    unittest.main()
