import io
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import urlopen

from omnidoer.omni_cli.auto_upgrade import UpdateInfo
from omnidoer.omni_cli.auto_upgrade import maybe_prompt_for_upgrade
from omnidoer.omni_cli.console import build_console_env
from omnidoer.omni_audit.audit import AuditLog
from omnidoer.omni_broker.broker import SecretBroker
from omnidoer.omni_control.requests import RequestStore
from omnidoer.omni_control.secure_channel import ReplayGuard, encrypt_for_broker, load_or_create_keypair
from omnidoer.omni_control.devices import DeviceStore
from omnidoer.omni_control.sessions import SessionStore
from omnidoer.omni_control.tasks import TaskStore
from omnidoer.omni_vault.vault import Vault


class CliTest(unittest.TestCase):
    def run_cli(self, args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged = os.environ.copy()
        if env:
            merged.update(env)
        return subprocess.run(
            [sys.executable, "-m", "omnidoer.omni_cli.main", *args],
            cwd=Path(__file__).resolve().parents[1],
            env=merged,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_help(self) -> None:
        result = self.run_cli(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("doctor", result.stdout)
        self.assertIn("upgrade", result.stdout)

    def test_version_uses_utc_timestamp_release_scheme(self) -> None:
        result = self.run_cli(["--version"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout.strip(), r"^omnidoer v20\d{12}$")

    def test_upgrade_dry_run_prints_plan_without_mutating(self) -> None:
        result = self.run_cli(["upgrade", "--dry-run", "--install-dir", "/tmp/omnidoer-install", "--branch", "main"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OmniDoer upgrade plan", result.stdout)
        self.assertIn("install_dir=/tmp/omnidoer-install", result.stdout)
        self.assertIn("pull --ff-only origin main", result.stdout)
        self.assertIn("refresh installed OmniDoer Codex shim", result.stdout)

    def test_console_dry_run_uses_omnidoer_brand(self) -> None:
        result = self.run_cli(
            ["console", "--dry-run", "--version"],
            env={"OMNIDOER_CODEX_BIN": "/bin/echo", "OMNIDOER_DISABLE_SPLASH": "1"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OmniDoer console plan", result.stdout)
        self.assertIn("binary=/bin/echo", result.stdout)
        self.assertIn("brand=omnidoer", result.stdout)
        self.assertIn("--version", result.stdout)

    def test_console_env_uses_unprefixed_brand_version(self) -> None:
        from omnidoer.version import __version__

        env = build_console_env()
        self.assertEqual(env["OMNIDOER_VERSION"], __version__.lstrip("vV"))

    def test_update_prompt_runs_upgrade_when_user_accepts(self) -> None:
        update = UpdateInfo(
            install_dir=Path("/tmp/omnidoer-install"),
            branch="main",
            local_revision="a" * 40,
            remote_revision="b" * 40,
            dirty=False,
            fast_forward=True,
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch("omnidoer.omni_cli.auto_upgrade.check_for_update", return_value=update),
            patch("omnidoer.omni_cli.auto_upgrade.handle_upgrade_command", return_value=0) as upgrade,
        ):
            upgraded = maybe_prompt_for_upgrade(
                input_func=lambda _prompt: "y",
                stdout=stdout,
                stderr=stderr,
                is_interactive=lambda: True,
            )
        self.assertTrue(upgraded)
        self.assertIn("OmniDoer update available", stdout.getvalue())
        upgrade.assert_called_once()
        args = upgrade.call_args.args[0]
        self.assertEqual(args.install_dir, "/tmp/omnidoer-install")
        self.assertEqual(args.branch, "main")

    def test_update_prompt_continues_when_user_declines(self) -> None:
        update = UpdateInfo(
            install_dir=Path("/tmp/omnidoer-install"),
            branch="main",
            local_revision="a" * 40,
            remote_revision="b" * 40,
            dirty=False,
            fast_forward=True,
        )
        stdout = io.StringIO()
        with (
            patch("omnidoer.omni_cli.auto_upgrade.check_for_update", return_value=update),
            patch("omnidoer.omni_cli.auto_upgrade.handle_upgrade_command") as upgrade,
        ):
            upgraded = maybe_prompt_for_upgrade(
                input_func=lambda _prompt: "n",
                stdout=stdout,
                stderr=io.StringIO(),
                is_interactive=lambda: True,
            )
        self.assertFalse(upgraded)
        self.assertIn("Continuing with the installed OmniDoer version.", stdout.getvalue())
        upgrade.assert_not_called()

    def test_update_prompt_is_disabled_by_env(self) -> None:
        with (
            patch.dict(os.environ, {"OMNIDOER_UPDATE_CHECK": "0"}),
            patch("omnidoer.omni_cli.auto_upgrade.check_for_update") as check,
        ):
            upgraded = maybe_prompt_for_upgrade(is_interactive=lambda: True)
        self.assertFalse(upgraded)
        check.assert_not_called()

    def test_update_prompt_skip_once_env_prevents_reexec_loop(self) -> None:
        with (
            patch.dict(os.environ, {"OMNIDOER_UPDATE_CHECK_SKIP_ONCE": "1"}),
            patch("omnidoer.omni_cli.auto_upgrade.check_for_update") as check,
        ):
            upgraded = maybe_prompt_for_upgrade(is_interactive=lambda: True)
        self.assertFalse(upgraded)
        check.assert_not_called()

    def test_no_args_launches_console_instead_of_help(self) -> None:
        result = self.run_cli(
            [],
            env={
                "OMNIDOER_CODEX_BIN": "/bin/echo",
                "OMNIDOER_CONSOLE_DRY_RUN": "1",
                "OMNIDOER_DISABLE_SPLASH": "1",
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OmniDoer console plan", result.stdout)

    def test_unknown_codex_command_delegates_to_console_binary(self) -> None:
        result = self.run_cli(
            ["exec", "--help"],
            env={
                "OMNIDOER_CODEX_BIN": "/bin/echo",
                "OMNIDOER_CONSOLE_DRY_RUN": "1",
                "OMNIDOER_DISABLE_SPLASH": "1",
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OmniDoer console plan", result.stdout)
        self.assertIn("exec --help", result.stdout)

    def test_init_creates_private_state_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "state"
            result = self.run_cli(["init"], env={"OMNIDOER_HOME": str(home)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(stat.S_IMODE(home.stat().st_mode), 0o700)

    def test_control_input_secret_does_not_echo_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("OMNIDOER_HOME")
            os.environ["OMNIDOER_HOME"] = tmp
            env = {
                "OMNIDOER_HOME": tmp,
                "OMNIDOER_CONTROL_TEST_MODE": "1",
                "OMNIDOER_TEST_USERNAME": "demo",
                "OMNIDOER_TEST_PASSWORD": "super-secret-password",
            }
            try:
                store = RequestStore(Path(tmp) / "control_requests.json")
                req = store.create(
                    "credential",
                    origin="http://127.0.0.1:8765",
                    top_level_url="http://127.0.0.1:8765/login",
                    action_summary="login",
                    requested_fields=["username", "password"],
                    allowed_device_id="dev_cli",
                )
                result = self.run_cli(["control", "input-secret", req.request_id], env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                combined = result.stdout + result.stderr
                self.assertNotIn("super-secret-password", combined)
                self.assertIn("Secret Broker", combined)
                stored = RequestStore(Path(tmp) / "control_requests.json").get(req.request_id)
                self.assertEqual(stored.response_ciphertext["device_id"], "dev_cli")
                self.assertEqual(float(stored.response_ciphertext["expires_at"]), stored.expires_at)
                broker = SecretBroker(
                    store=RequestStore(Path(tmp) / "control_requests.json"),
                    replay_guard=ReplayGuard(Path(tmp) / "replay.json"),
                    audit=AuditLog(Path(tmp) / "audit.jsonl"),
                )
                received = broker.receive_from_control_client(req.request_id)
                self.assertEqual(received["fields"], ["username", "password"])
                self.assertNotIn("super-secret-password", repr(received))
            finally:
                if old_home is None:
                    os.environ.pop("OMNIDOER_HOME", None)
                else:
                    os.environ["OMNIDOER_HOME"] = old_home

    def test_control_captcha_challenge_does_not_store_answer_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "OMNIDOER_HOME": tmp,
                "OMNIDOER_CHALLENGE_TEST_MODE": "1",
                "OMNIDOER_TEST_CAPTCHA_ACK": "user-completed-secret",
            }
            store = RequestStore(Path(tmp) / "control_requests.json")
            req = store.create(
                "captcha",
                origin="http://127.0.0.1:8765",
                top_level_url="http://127.0.0.1:8765/captcha",
                action_summary="captcha",
                requested_fields=["ack"],
                challenge_type="captcha",
            )
            result = self.run_cli(["control", "challenge", req.request_id], env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            combined = result.stdout + result.stderr
            self.assertNotIn("user-completed-secret", combined)
            stored = RequestStore(Path(tmp) / "control_requests.json").get(req.request_id)
            self.assertEqual(stored.status, "challenge_completed")
            self.assertIsNone(stored.response_ciphertext)

    def test_control_submit_task_queues_local_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {"OMNIDOER_HOME": tmp}
            result = self.run_cli(["control", "submit-task", "Use the local demo"], env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("queued task", result.stdout)
            tasks = TaskStore(Path(tmp) / "control_tasks.json").list()
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].text, "Use the local demo")

    def test_cred_request_can_be_saved_to_vault_without_echoing_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault_path = Path(tmp) / "vault.json"
            Vault.create(vault_path, "test-passphrase")
            env = {
                "OMNIDOER_HOME": tmp,
                "OMNIDOER_TEST_PASSPHRASE": "test-passphrase",
            }
            requested = self.run_cli(
                [
                    "cred",
                    "request",
                    "--origin",
                    "https://github.com",
                    "--top-level-url",
                    "https://github.com/settings/tokens",
                    "--summary",
                    "Migrate GitHub PAT into Vault",
                    "--ttl",
                    "10m",
                ],
                env=env,
            )
            self.assertEqual(requested.returncode, 0, requested.stderr)
            match = re.search(r"credential_request=(req_[a-f0-9]+)", requested.stdout)
            self.assertIsNotNone(match, requested.stdout)
            request_id = match.group(1)
            self.assertIn("secret_exposed_to_model=false", requested.stdout)

            keypair = load_or_create_keypair(Path(tmp) / "broker_key.json")
            store = RequestStore(Path(tmp) / "control_requests.json")
            request = store.get(request_id)
            envelope = encrypt_for_broker(
                keypair.public_key_b64,
                {
                    "username": "omnidoer",
                    "password": "github_pat_secret_never_echo",
                    "save_to_vault": True,
                },
                request_id=request.request_id,
                origin=request.origin,
                request_type=request.request_type,
            )
            store.submit_ciphertext(request.request_id, envelope)

            saved = self.run_cli(
                [
                    "cred",
                    "save-request",
                    request_id,
                    "--vault",
                    str(vault_path),
                    "--passphrase-env",
                    "OMNIDOER_TEST_PASSPHRASE",
                ],
                env=env,
            )
            self.assertEqual(saved.returncode, 0, saved.stderr)
            combined = requested.stdout + requested.stderr + saved.stdout + saved.stderr
            self.assertNotIn("github_pat_secret_never_echo", combined)
            self.assertIn('"saved_to_vault": true', saved.stdout)
            raw_vault = vault_path.read_text()
            self.assertNotIn("github_pat_secret_never_echo", raw_vault)
            metadata = Vault.load(vault_path).list_metadata()[0]
            self.assertEqual(metadata.allowed_origins, ["https://github.com"])

    def test_git_run_uses_vault_askpass_without_echoing_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault_path = Path(tmp) / "vault.json"
            passphrase_env = "OMNIDOER_TEST_GIT_VAULT_PASSPHRASE"
            vault = Vault.create(vault_path, "test-passphrase")
            vault.add_credential(
                username="omnidoer",
                password="vault-github-token-never-print",
                allowed_origins=["https://github.com"],
            )
            fake_git = Path(tmp) / "fake-git"
            fake_git.write_text(
                """#!/bin/sh
echo "git_args=$*"
if [ -z "${OMNIDOER_TEST_GIT_VAULT_PASSPHRASE+x}" ]; then echo "passphrase-env-absent"; else echo "passphrase-env-present"; fi
if [ -z "${OMNIDOER_GIT_VAULT+x}" ]; then echo "vault-path-env-absent"; else echo "vault-path-env-present"; fi
if [ -z "${OMNIDOER_GIT_PASSPHRASE_ENV+x}" ]; then echo "passphrase-name-env-absent"; else echo "passphrase-name-env-present"; fi
user="$("$GIT_ASKPASS" "Username for 'https://github.com':")" || exit 11
password="$("$GIT_ASKPASS" "Password for 'https://$user@github.com':")" || exit 12
echo "user=$user"
if [ "$password" = "vault-github-token-never-print" ]; then
  echo "password-ok"
else
  echo "password-bad"
  exit 13
fi
"""
            )
            fake_git.chmod(0o700)
            env = {
                "OMNIDOER_HOME": tmp,
                passphrase_env: "test-passphrase",
                "OMNIDOER_GIT_BIN": str(fake_git),
            }
            result = self.run_cli(
                [
                    "git",
                    "run",
                    "--origin",
                    "https://github.com",
                    "--vault",
                    str(vault_path),
                    "--passphrase-env",
                    passphrase_env,
                    "--",
                    "push",
                    "origin",
                    "main",
                ],
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            combined = result.stdout + result.stderr
            self.assertIn("git_args=push origin main", result.stdout)
            self.assertIn("passphrase-env-absent", result.stdout)
            self.assertIn("vault-path-env-absent", result.stdout)
            self.assertIn("passphrase-name-env-absent", result.stdout)
            self.assertIn("user=omnidoer", result.stdout)
            self.assertIn("password-ok", result.stdout)
            self.assertNotIn("vault-github-token-never-print", combined)
            self.assertNotIn("test-passphrase", combined)

    def test_git_askpass_blocks_wrong_prompt_origin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault_path = Path(tmp) / "vault.json"
            passphrase_env = "OMNIDOER_TEST_GIT_VAULT_PASSPHRASE"
            vault = Vault.create(vault_path, "test-passphrase")
            vault.add_credential(
                username="omnidoer",
                password="vault-github-token-never-print",
                allowed_origins=["https://github.com"],
            )
            fake_git = Path(tmp) / "fake-git"
            fake_git.write_text(
                """#!/bin/sh
"$GIT_ASKPASS" "Password for 'https://evil.example':" >/dev/null 2>/dev/null
echo "askpass_exit=$?"
"""
            )
            fake_git.chmod(0o700)
            env = {
                "OMNIDOER_HOME": tmp,
                passphrase_env: "test-passphrase",
                "OMNIDOER_GIT_BIN": str(fake_git),
            }
            result = self.run_cli(
                [
                    "git",
                    "run",
                    "--origin",
                    "https://github.com",
                    "--vault",
                    str(vault_path),
                    "--passphrase-env",
                    passphrase_env,
                    "--",
                    "remote-probe",
                ],
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            combined = result.stdout + result.stderr
            self.assertIn("askpass_exit=1", result.stdout)
            self.assertNotIn("vault-github-token-never-print", combined)

    def test_cloud_direct_cli_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {"OMNIDOER_HOME": tmp}
            refused = self.run_cli(["control", "serve", "--host", "0.0.0.0", "--port", "8787"], env=env)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("0.0.0.0 requires explicit --cloud-direct", refused.stderr + refused.stdout)
            refused_background = self.run_cli(["control", "serve", "--host", "0.0.0.0", "--port", "8787", "--background"], env=env)
            self.assertNotEqual(refused_background.returncode, 0)
            self.assertIn("0.0.0.0 requires explicit --cloud-direct", refused_background.stderr + refused_background.stdout)
            self.assertNotIn("started background process", refused_background.stdout)
            refused_no_tls = self.run_cli(
                [
                    "control",
                    "serve",
                    "--cloud-direct",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "8787",
                    "--public-url",
                    "https://agent.example.com",
                    "--background",
                ],
                env=env,
            )
            self.assertNotEqual(refused_no_tls.returncode, 0)
            self.assertIn("--cloud-direct requires TLS", refused_no_tls.stderr + refused_no_tls.stdout)
            self.assertNotIn("started background process", refused_no_tls.stdout)
            pair = self.run_cli(
                ["control", "pair", "--print-qr", "--expires", "10m", "--public-url", "https://agent.example.com"],
                env=env,
            )
            self.assertEqual(pair.returncode, 0, pair.stderr)
            self.assertIn("pairing_url=https://agent.example.com/pair", pair.stdout)
            self.assertIn("broker_fingerprint=", pair.stdout)
            self.assertIn("Only pair devices you control", pair.stdout)
            self.assertIn("qr_ascii_begin", pair.stdout)
            self.assertIn("qr_ascii_end", pair.stdout)
            self.assertGreater(pair.stdout.count("##"), 100)
            status = self.run_cli(["control", "security-status"], env=env)
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertIn('"mcp_publicly_exposed": false', status.stdout)

    def test_control_device_and_session_cli_redacts_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {"OMNIDOER_HOME": tmp}
            device = DeviceStore(Path(tmp) / "control_devices.json").register(name="Phone", public_key="pub")
            session, token = SessionStore(Path(tmp) / "control_sessions.json").create(device_id=device.device_id)

            devices = self.run_cli(["control", "devices"], env=env)
            self.assertEqual(devices.returncode, 0, devices.stderr)
            self.assertIn(device.device_id, devices.stdout)
            self.assertNotIn("pub", devices.stdout)

            sessions = self.run_cli(["control", "sessions"], env=env)
            self.assertEqual(sessions.returncode, 0, sessions.stderr)
            self.assertIn(session.session_id, sessions.stdout)
            self.assertNotIn(token, sessions.stdout)
            self.assertNotIn("token_hash", sessions.stdout)

            revoked = self.run_cli(["control", "revoke-device", device.device_id], env=env)
            self.assertEqual(revoked.returncode, 0, revoked.stderr)
            self.assertIn("revoked_sessions=1", revoked.stdout)

    def test_demo_background_waits_until_port_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {"OMNIDOER_HOME": tmp}
            result = self.run_cli(["demo", "start", "--host", "127.0.0.1", "--port", "8876", "--background"], env=env)
            pid_match = re.search(r"pid=(\d+)", result.stdout)
            try:
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIsNotNone(pid_match, result.stdout)
                with urlopen("http://127.0.0.1:8876/", timeout=5) as response:
                    self.assertEqual(response.status, 200)
            finally:
                if pid_match:
                    try:
                        os.kill(int(pid_match.group(1)), 15)
                    except ProcessLookupError:
                        pass


if __name__ == "__main__":
    unittest.main()
