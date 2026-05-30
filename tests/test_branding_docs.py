import json
import pathlib
import re
import stat
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
            "docs/assets/omnidoer-cloud-control-service.jpg",
            "docs/assets/omnidoer-cloud-control-service.png",
            "docs/assets/omnidoer-feature-matrix.jpg",
            "docs/assets/omnidoer-feature-matrix.png",
            "docs/assets/omnidoer-human-loop-web-agent.jpg",
            "docs/assets/omnidoer-human-loop-web-agent.png",
            "docs/assets/omnidoer-omni-action-poster.jpg",
            "docs/assets/omnidoer-omni-action-poster.png",
            "docs/assets/omnidoer-secure-credential-flow.svg",
            "docs/assets/omnidoer-human-takeover-state-machine.svg",
            "docs/assets/omnidoer-linux-cloud-runtime.svg",
            "docs/assets/omnidoer-mark.svg",
            "docs/assets/omnidoer-cloud-direct.svg",
            "omnidoer/omni_control/static/icon-192.png",
            "omnidoer/omni_control/static/icon-512.png",
        ):
            self.assertTrue((self.root / relative).is_file(), relative)
        for lang in ("en", "zh-CN", "es", "fr", "de", "ja", "ko"):
            self.assertTrue((self.root / f"docs/assets/localized/omnidoer-readme-{lang}.jpg").is_file(), lang)
            self.assertTrue((self.root / f"docs/assets/localized/omnidoer-readme-{lang}.png").is_file(), lang)

    def test_readme_and_agents_keep_multilingual_product_constraints(self) -> None:
        readme = (self.root / "README.md").read_text()
        agents = (self.root / "AGENTS.md").read_text()
        self.assertIn("English", readme)
        self.assertIn("中文", readme)
        self.assertIn("Español", readme)
        self.assertIn("Français", readme)
        self.assertIn("Deutsch", readme)
        self.assertIn("日本語", readme)
        self.assertIn("한국어", readme)
        self.assertIn("does not call OpenAI APIs directly", readme)
        self.assertIn("Cloud Direct Mode", readme)
        self.assertIn("All-purpose web action, inside the security boundary.", readme)
        self.assertIn("The agent can act only through the controlled security boundary.", readme)
        self.assertIn("OpenClaw", readme)
        self.assertIn("Practical comparison", readme)
        self.assertIn("Security validation and test contracts", readme)
        self.assertIn("OmniDoer is not a CAPTCHA bypasser.", readme)
        self.assertIn("guarded browser 2FA", readme)
        self.assertIn("Payments, purchases, account changes, OAuth grants, message sending", readme)
        self.assertIn("OmniDoer does not bypass the mechanism", readme)
        self.assertIn("One-Command Install", readme)
        self.assertIn("install-cloud-direct.sh", readme)
        self.assertIn("OMNIDOER_CLOUD_DIRECT=1", readme)
        self.assertNotIn("智能体可以行动，但秘密必须留在本地。", readme)
        pkg_info = self.root / "omnidoer.egg-info" / "PKG-INFO"
        if pkg_info.exists():
            self.assertNotIn("智能体可以行动，但秘密必须留在本地。", pkg_info.read_text())
        self.assertIn("不要把 OmniDoer 做成默认 OpenAI API 客户端", agents)
        self.assertIn("docs/assets/localized", agents)

    def test_english_readme_lead_has_no_stray_chinese_body_copy(self) -> None:
        readme = (self.root / "README.md").read_text()
        lead = readme.split("## Available translations", 1)[0]
        allowed_labels = (
            "One-Command Install",
            "[中文](./README.zh-CN.md)",
            "[日本語](./README.ja.md)",
        )
        for allowed in allowed_labels:
            lead = lead.replace(allowed, "")
        self.assertIsNone(re.search(r"[\u4e00-\u9fff]", lead), lead)

    def test_security_model_documents_handover_stream_contract(self) -> None:
        security = (self.root / "docs" / "security-model.md").read_text()
        self.assertIn("Challenge-stream contract", security)
        self.assertIn("streams the live control", security)
        self.assertIn("surface to the paired client", security)
        self.assertIn("model context", security)
        self.assertIn("Reproducible safety guarantees", security)

    def test_one_command_installer_is_documented_and_executable(self) -> None:
        installer = self.root / "omnidoer" / "scripts" / "install-cloud-direct.sh"
        content = installer.read_text()
        self.assertTrue(installer.is_file())
        self.assertTrue(installer.stat().st_mode & stat.S_IXUSR)
        self.assertIn("OMNIDOER_CLOUD_DIRECT", content)
        self.assertIn("OMNIDOER_PUBLIC_URL", content)
        self.assertIn("mcp serve --self-test", content)
        self.assertIn("control pair --print-qr", content)
        self.assertIn("codex mcp add omnidoer", content)

    def test_localized_readmes_use_distinct_cinematic_images(self) -> None:
        expected = {
            "README.md": "docs/assets/localized/omnidoer-readme-en.jpg",
            "README.zh-CN.md": "docs/assets/localized/omnidoer-readme-zh-CN.jpg",
            "README.es.md": "docs/assets/localized/omnidoer-readme-es.jpg",
            "README.fr.md": "docs/assets/localized/omnidoer-readme-fr.jpg",
            "README.de.md": "docs/assets/localized/omnidoer-readme-de.jpg",
            "README.ja.md": "docs/assets/localized/omnidoer-readme-ja.jpg",
            "README.ko.md": "docs/assets/localized/omnidoer-readme-ko.jpg",
        }
        for readme_name, image in expected.items():
            content = (self.root / readme_name).read_text()
            self.assertIn(image, content, readme_name)
            self.assertIn("Codex", content, readme_name)
            self.assertIn("OpenAI API", content, readme_name)
            self.assertIn("install-cloud-direct.sh", content, readme_name)
            self.assertIn("OMNIDOER_CLOUD_DIRECT=1", content, readme_name)

    def test_github_pages_intro_exists(self) -> None:
        page = (self.root / "docs" / "index.html").read_text()
        self.assertIn("OmniDoer", page)
        self.assertIn("Secrets Stay Out Of The Model", page)
        self.assertIn("Cloud Direct Architecture", page)
        self.assertIn("System Blueprints", page)
        self.assertIn("Agent Runtime Visuals", page)
        self.assertIn("One-Command Install", page)
        self.assertIn("Beyond Automation-First Agents", page)
        self.assertIn("Technical Proof of OmniDoer Superiority", page)
        self.assertIn('id="technical-proof"', page)
        self.assertIn("proof_heading", page)
        self.assertIn("Technical Proof", page)
        self.assertIn("install-cloud-direct.sh", page)
        self.assertIn("OMNIDOER_CLOUD_DIRECT=1", page)
        self.assertIn("All-purpose web action on the user's own server", page)
        self.assertIn("install_after_commands", page)
        self.assertIn("打开本地 demo 并下载我的发票", page)
        self.assertIn('href="#install"', page)
        self.assertIn('class="language-switcher"', page)
        self.assertIn('data-lang="zh-CN"', page)
        self.assertIn('data-lang="es"', page)
        self.assertIn('data-i18n="hero_tagline"', page)
        self.assertIn("heroImageByLang", page)
        self.assertIn("assets/localized/omnidoer-readme-en.jpg", page)
        self.assertIn("assets/omnidoer-cinematic-share.jpg", page)
        self.assertIn("assets/omnidoer-human-loop-web-agent.jpg", page)
        self.assertIn("assets/omnidoer-cloud-control-service.jpg", page)
        self.assertIn("assets/omnidoer-feature-matrix.jpg", page)
        self.assertIn("assets/omnidoer-omni-action-poster.jpg", page)
        self.assertIn("assets/omnidoer-secure-credential-flow.svg", page)
        self.assertIn("assets/omnidoer-human-takeover-state-machine.svg", page)
        self.assertIn("assets/omnidoer-linux-cloud-runtime.svg", page)
        self.assertNotIn("Localized README Posters", page)
        self.assertNotIn("多语言简介", page)
        self.assertNotIn("Try The Control Client", page)

    def test_pwa_manifest_declares_icons(self) -> None:
        manifest = json.loads((self.root / "omnidoer/omni_control/static/manifest.json").read_text())
        self.assertEqual(manifest["name"], "OmniDoer Control Client")
        icon_srcs = {icon["src"] for icon in manifest["icons"]}
        self.assertEqual(icon_srcs, {"/icon-192.png", "/icon-512.png"})

    def test_pages_i18n_has_technical_proof_keys_for_all_languages(self) -> None:
        page = (self.root / "docs" / "index.html").read_text()
        languages = ("en", "zh-CN", "es", "fr", "de", "ja", "ko")
        required_keys = (
            "nav_proof",
            "proof_heading",
            "proof_copy",
            "proof_boundary_title",
            "proof_boundary_copy",
            "proof_projection_title",
            "proof_projection_copy",
            "proof_approval_title",
            "proof_approval_copy",
            "proof_tests_intro",
            "proof_tests_1",
            "proof_tests_2",
            "proof_tests_3",
        )
        def extract_language_block(content: str, lang: str) -> str:
            marker = f'\n      "{lang}": {{'
            block_start = content.find(marker)
            if block_start < 0:
                raise AssertionError(f"missing language block: {lang}")
            brace_start = content.find("{", block_start + len(marker) - 1)
            if brace_start < 0:
                raise AssertionError(f"missing block start brace for {lang}")

            depth = 0
            for idx in range(brace_start, len(content)):
                if content[idx] == "{":
                    depth += 1
                elif content[idx] == "}":
                    depth -= 1
                    if depth == 0:
                        return content[block_start : idx + 1]
            raise AssertionError(f"could not close language block: {lang}")

        for lang in languages:
            block = extract_language_block(page, lang)
            for key in required_keys:
                self.assertIn(f"{key}:", block, f"{lang} missing {key}")


if __name__ == "__main__":
    unittest.main()
