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
