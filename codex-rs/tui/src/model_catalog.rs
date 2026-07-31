use codex_protocol::openai_models::ModelPreset;
use codex_protocol::openai_models::ReasoningEffort;
use codex_protocol::openai_models::ReasoningEffortPreset;
use std::collections::HashMap;
use std::collections::HashSet;
use std::convert::Infallible;

pub(crate) const DEEPSEEK_PROVIDER_ID: &str = "deepseek";
pub(crate) const OPENAI_PROVIDER_ID: &str = "openai";
const DEEPSEEK_V4_FLASH: &str = "deepseek-v4-flash";
const DEEPSEEK_V4_PRO: &str = "deepseek-v4-pro";

#[derive(Debug, Clone)]
pub(crate) struct ModelCatalog {
    models: Vec<ModelPreset>,
    model_providers: HashMap<String, String>,
}

impl ModelCatalog {
    pub(crate) fn new(models: Vec<ModelPreset>) -> Self {
        Self {
            models,
            model_providers: HashMap::new(),
        }
    }

    /// Build the picker catalog from the active provider and add OmniDoer-known models for other
    /// configured providers. Models returned by the active provider win on duplicate slugs.
    pub(crate) fn with_provider_models<'a>(
        mut models: Vec<ModelPreset>,
        current_provider: &str,
        configured_provider_ids: impl IntoIterator<Item = &'a str>,
    ) -> Self {
        let mut configured_provider_ids =
            configured_provider_ids.into_iter().collect::<HashSet<_>>();
        // OpenAI is a built-in provider and is normally absent from the user
        // `model_providers` table. Keep its presets available after a user
        // switches to DeepSeek so `/model` is a reversible choice.
        configured_provider_ids.insert(OPENAI_PROVIDER_ID);
        let mut model_providers = models
            .iter()
            .map(|model| (model.model.clone(), current_provider.to_string()))
            .collect::<HashMap<_, _>>();
        let mut known_models = model_providers.keys().cloned().collect::<HashSet<_>>();

        if current_provider != OPENAI_PROVIDER_ID
            && configured_provider_ids.contains(OPENAI_PROVIDER_ID)
            && let Ok(bundled) = codex_models_manager::bundled_models_response()
        {
            append_provider_models(
                &mut models,
                &mut model_providers,
                &mut known_models,
                OPENAI_PROVIDER_ID,
                bundled.models.into_iter().map(Into::into),
            );
        }

        if configured_provider_ids.contains(DEEPSEEK_PROVIDER_ID) {
            append_provider_models(
                &mut models,
                &mut model_providers,
                &mut known_models,
                DEEPSEEK_PROVIDER_ID,
                deepseek_v4_models(),
            );
        }

        Self {
            models,
            model_providers,
        }
    }

    pub(crate) fn try_list_models(&self) -> Result<Vec<ModelPreset>, Infallible> {
        Ok(self.models.clone())
    }

    pub(crate) fn provider_for_model(&self, model: &str) -> Option<&str> {
        self.model_providers.get(model).map(String::as_str)
    }
}

/// DeepSeek inference is billed by DeepSeek, not against the ChatGPT quota.
/// Keep the existing ChatGPT account status available in `/status` so users
/// can still see their original GPT limits while a DeepSeek model is active.
pub(crate) fn should_preserve_chatgpt_status(
    model_provider_id: &str,
    requires_openai_auth: bool,
) -> bool {
    requires_openai_auth || model_provider_id == DEEPSEEK_PROVIDER_ID
}

fn append_provider_models(
    models: &mut Vec<ModelPreset>,
    model_providers: &mut HashMap<String, String>,
    known_models: &mut HashSet<String>,
    provider: &str,
    provider_models: impl IntoIterator<Item = ModelPreset>,
) {
    for model in provider_models {
        if known_models.insert(model.model.clone()) {
            model_providers.insert(model.model.clone(), provider.to_string());
            models.push(model);
        }
    }
}

fn deepseek_v4_models() -> Vec<ModelPreset> {
    [
        (
            DEEPSEEK_V4_FLASH,
            "DeepSeek V4 Flash",
            "Fast, economical DeepSeek V4 through the configured Responses bridge",
        ),
        (
            DEEPSEEK_V4_PRO,
            "DeepSeek V4 Pro",
            "Flagship DeepSeek V4 reasoning through the configured Responses bridge",
        ),
    ]
    .into_iter()
    .map(|(model, display_name, description)| ModelPreset {
        id: model.to_string(),
        model: model.to_string(),
        display_name: display_name.to_string(),
        description: description.to_string(),
        default_reasoning_effort: ReasoningEffort::High,
        supported_reasoning_efforts: vec![
            ReasoningEffortPreset {
                effort: ReasoningEffort::High,
                description: "Deep reasoning for regular agent work".to_string(),
            },
            ReasoningEffortPreset {
                effort: ReasoningEffort::Max,
                description: "Maximum reasoning for difficult agent work".to_string(),
            },
        ],
        supports_personality: false,
        additional_speed_tiers: Vec::new(),
        service_tiers: Vec::new(),
        default_service_tier: None,
        is_default: false,
        upgrade: None,
        show_in_picker: true,
        multi_agent_version: None,
        availability_nux: None,
        supported_in_api: true,
        input_modalities: vec![codex_protocol::openai_models::InputModality::Text],
    })
    .collect()
}

#[cfg(test)]
#[path = "model_catalog_tests.rs"]
mod tests;
