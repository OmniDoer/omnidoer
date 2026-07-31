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
