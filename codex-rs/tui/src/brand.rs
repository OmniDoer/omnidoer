//! Runtime branding hooks for downstream OmniDoer console builds.

pub(crate) fn is_omnidoer() -> bool {
    matches!(
        std::env::var("OMNIDOER_CODEX_BRAND")
            .or_else(|_| std::env::var("CODEX_CLI_BRAND"))
            .as_deref(),
        Ok("omnidoer") | Ok("OmniDoer")
    ) || std::env::var("OMNIDOER_CONSOLE").is_ok()
}

pub(crate) fn product_name() -> &'static str {
    if is_omnidoer() {
        "OmniDoer"
    } else {
        "OpenAI Codex"
    }
}

pub(crate) fn short_name() -> &'static str {
    if is_omnidoer() { "OmniDoer" } else { "Codex" }
}

pub(crate) fn placeholder() -> &'static str {
    if is_omnidoer() {
        "Ask OmniDoer to do anything"
    } else {
        "Ask Codex to do anything"
    }
}

pub(crate) fn display_version(default_version: &str) -> String {
    if is_omnidoer() {
        std::env::var("OMNIDOER_VERSION")
            .ok()
            .filter(|version| !version.trim().is_empty())
            .unwrap_or_else(|| default_version.to_string())
    } else {
        default_version.to_string()
    }
}
