import unittest


FORBIDDEN_TOOL_NAMES = {
    "get_password",
    "decrypt_password",
    "get_totp_code",
    "get_cookie",
    "get_api_key",
    "export_secret",
    "print_secret",
    "copy_secret_to_clipboard",
    "dump_cookies",
    "dump_local_storage",
    "dump_password_values",
    "read_private_key",
    "export_private_key",
}

ALLOWED_TOOL_NAMES = {
    "browser.open",
    "browser.observe",
    "browser.click",
    "browser.type_text",
    "browser.select",
    "browser.download_current_file",
    "browser.current_origin",
    "credential.list_for_current_origin",
    "credential.create_interactive",
    "credential.fill_current_origin_login",
    "credential.fill_current_origin_totp",
    "approval.request",
    "payment.prepare_review",
    "payment.request_user_approval",
    "audit.show_recent_events",
    "policy.explain_current_block",
}


class ForbiddenSecretToolTest(unittest.TestCase):
    def test_allowed_tool_schema_has_no_secret_returners(self) -> None:
        normalized = {tool.replace(".", "_") for tool in ALLOWED_TOOL_NAMES}
        self.assertTrue(FORBIDDEN_TOOL_NAMES.isdisjoint(normalized))


if __name__ == "__main__":
    unittest.main()
