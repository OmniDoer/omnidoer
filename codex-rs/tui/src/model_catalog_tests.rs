use super::*;
use pretty_assertions::assert_eq;

#[test]
fn configured_deepseek_provider_adds_v4_models() {
    let catalog = ModelCatalog::with_provider_models(
        Vec::new(),
        OPENAI_PROVIDER_ID,
        [OPENAI_PROVIDER_ID, DEEPSEEK_PROVIDER_ID],
    );

    let models = catalog.try_list_models().expect("infallible model list");
    assert_eq!(
        models
            .iter()
            .map(|preset| preset.model.as_str())
            .collect::<Vec<_>>(),
        vec![DEEPSEEK_V4_FLASH, DEEPSEEK_V4_PRO]
    );
    assert_eq!(
        catalog.provider_for_model(DEEPSEEK_V4_FLASH),
        Some(DEEPSEEK_PROVIDER_ID)
    );
    assert_eq!(
        catalog.provider_for_model(DEEPSEEK_V4_PRO),
        Some(DEEPSEEK_PROVIDER_ID)
    );
}

#[test]
fn active_provider_model_wins_over_known_duplicate() {
    let deepseek_model = deepseek_v4_models()
        .into_iter()
        .find(|preset| preset.model == DEEPSEEK_V4_PRO)
        .expect("DeepSeek V4 Pro preset");
    let catalog = ModelCatalog::with_provider_models(
        vec![deepseek_model],
        "company-proxy",
        [OPENAI_PROVIDER_ID, DEEPSEEK_PROVIDER_ID, "company-proxy"],
    );

    assert_eq!(
        catalog.provider_for_model(DEEPSEEK_V4_PRO),
        Some("company-proxy")
    );
    assert_eq!(
        catalog
            .try_list_models()
            .expect("infallible model list")
            .iter()
            .filter(|preset| preset.model == DEEPSEEK_V4_PRO)
            .count(),
        1
    );
}

#[test]
fn deepseek_catalog_keeps_builtin_openai_models_for_switching_back() {
    let gpt = ModelPreset {
        id: "gpt-test".to_string(),
        model: "gpt-test".to_string(),
        display_name: "GPT Test".to_string(),
        ..deepseek_v4_models()
            .into_iter()
            .next()
            .expect("DeepSeek preset")
    };
    let catalog =
        ModelCatalog::with_provider_models(vec![gpt], DEEPSEEK_PROVIDER_ID, [DEEPSEEK_PROVIDER_ID]);

    assert_eq!(
        catalog.provider_for_model("gpt-test"),
        Some(DEEPSEEK_PROVIDER_ID)
    );
    assert!(
        catalog
            .try_list_models()
            .expect("infallible model list")
            .iter()
            .any(|preset| preset.model.starts_with("gpt-"))
    );
}

#[test]
fn deepseek_preserves_chatgpt_status_without_billing_inference_to_openai() {
    assert!(should_preserve_chatgpt_status(DEEPSEEK_PROVIDER_ID, false));
    assert!(should_preserve_chatgpt_status(OPENAI_PROVIDER_ID, true));
    assert!(!should_preserve_chatgpt_status("amazon-bedrock", false));
}
