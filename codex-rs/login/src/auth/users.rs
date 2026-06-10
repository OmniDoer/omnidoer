use chrono::DateTime;
use chrono::Utc;
use codex_app_server_protocol::AuthMode;
use codex_config::types::AuthCredentialsStoreMode;
use codex_protocol::account::PlanType as AccountPlanType;
use serde::Deserialize;
use serde::Serialize;
use sha2::Digest;
use sha2::Sha256;
use std::fs::OpenOptions;
use std::io::Read;
use std::io::Write;
#[cfg(unix)]
use std::os::unix::fs::OpenOptionsExt;
use std::path::Path;
use std::path::PathBuf;

use super::storage::AuthDotJson;
use super::storage::create_auth_storage;

const AUTH_USERS_INDEX_FILE: &str = "auth-users.json";
const AUTH_USERS_DIR: &str = "auth-users";
const AUTH_USERS_VERSION: u32 = 1;

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq)]
struct AuthUsersIndex {
    version: u32,
    active_user_id: Option<String>,
    users: Vec<AuthUserMetadata>,
}

impl Default for AuthUsersIndex {
    fn default() -> Self {
        Self {
            version: AUTH_USERS_VERSION,
            active_user_id: None,
            users: Vec::new(),
        }
    }
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq)]
struct AuthUserMetadata {
    id: String,
    label: String,
    auth_mode: AuthMode,
    email: Option<String>,
    account_id: Option<String>,
    plan_type: Option<AccountPlanType>,
    updated_at: DateTime<Utc>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct AuthUserSummary {
    pub id: String,
    pub label: String,
    pub auth_mode: AuthMode,
    pub email: Option<String>,
    pub account_id: Option<String>,
    pub plan_type: Option<AccountPlanType>,
    pub updated_at: DateTime<Utc>,
    pub is_current: bool,
}

fn users_index_path(codex_home: &Path) -> PathBuf {
    codex_home.join(AUTH_USERS_INDEX_FILE)
}

fn user_auth_home(codex_home: &Path, user_id: &str) -> PathBuf {
    codex_home.join(AUTH_USERS_DIR).join(user_id)
}

fn load_index(codex_home: &Path) -> std::io::Result<AuthUsersIndex> {
    let path = users_index_path(codex_home);
    let mut file = match std::fs::File::open(&path) {
        Ok(file) => file,
        Err(err) if err.kind() == std::io::ErrorKind::NotFound => {
            return Ok(AuthUsersIndex::default());
        }
        Err(err) => return Err(err),
    };

    let mut contents = String::new();
    file.read_to_string(&mut contents)?;
    let mut index: AuthUsersIndex = serde_json::from_str(&contents)?;
    if index.version == 0 {
        index.version = AUTH_USERS_VERSION;
    }
    Ok(index)
}

fn save_index(codex_home: &Path, index: &AuthUsersIndex) -> std::io::Result<()> {
    let path = users_index_path(codex_home);
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)?;
    }

    let json_data = serde_json::to_string_pretty(index)?;
    let mut options = OpenOptions::new();
    options.truncate(true).write(true).create(true);
    #[cfg(unix)]
    {
        options.mode(0o600);
    }
    let mut file = options.open(path)?;
    file.write_all(json_data.as_bytes())?;
    file.flush()?;
    Ok(())
}

fn load_stored_auth(
    codex_home: &Path,
    auth_credentials_store_mode: AuthCredentialsStoreMode,
) -> std::io::Result<Option<AuthDotJson>> {
    let storage = create_auth_storage(codex_home.to_path_buf(), auth_credentials_store_mode);
    storage.load()
}

fn save_stored_auth(
    codex_home: &Path,
    auth: &AuthDotJson,
    auth_credentials_store_mode: AuthCredentialsStoreMode,
) -> std::io::Result<()> {
    let storage = create_auth_storage(codex_home.to_path_buf(), auth_credentials_store_mode);
    storage.save(auth)
}

fn delete_stored_auth(
    codex_home: &Path,
    auth_credentials_store_mode: AuthCredentialsStoreMode,
) -> std::io::Result<bool> {
    let storage = create_auth_storage(codex_home.to_path_buf(), auth_credentials_store_mode);
    storage.delete()
}

fn resolved_auth_mode(auth: &AuthDotJson) -> AuthMode {
    if let Some(mode) = auth.auth_mode {
        return mode;
    }
    if auth.openai_api_key.is_some() {
        return AuthMode::ApiKey;
    }
    AuthMode::Chatgpt
}

fn hash_id(parts: &[&str]) -> String {
    let mut hasher = Sha256::new();
    for part in parts {
        hasher.update(part.as_bytes());
        hasher.update([0u8]);
    }
    format!("{:x}", hasher.finalize())
        .chars()
        .take(32)
        .collect()
}

fn secret_tail(secret: &str) -> String {
    let tail = secret
        .chars()
        .rev()
        .take(4)
        .collect::<String>()
        .chars()
        .rev()
        .collect::<String>();
    if tail.is_empty() {
        "unknown".to_string()
    } else {
        format!("...{tail}")
    }
}

fn metadata_from_auth(auth: &AuthDotJson) -> AuthUserMetadata {
    let auth_mode = resolved_auth_mode(auth);
    let updated_at = Utc::now();

    match auth_mode {
        AuthMode::ApiKey => {
            let api_key = auth.openai_api_key.as_deref().unwrap_or_default();
            let id = hash_id(&["api-key", api_key]);
            AuthUserMetadata {
                id,
                label: format!("API key {}", secret_tail(api_key)),
                auth_mode,
                email: None,
                account_id: None,
                plan_type: None,
                updated_at,
            }
        }
        AuthMode::Chatgpt | AuthMode::ChatgptAuthTokens => {
            let tokens = auth.tokens.as_ref();
            let account_id = tokens.and_then(|tokens| {
                tokens
                    .account_id
                    .clone()
                    .or_else(|| tokens.id_token.chatgpt_account_id.clone())
            });
            let email = tokens.and_then(|tokens| tokens.id_token.email.clone());
            let plan_type = tokens.and_then(|tokens| {
                tokens
                    .id_token
                    .chatgpt_plan_type
                    .clone()
                    .map(AccountPlanType::from)
            });
            let id = if let Some(account_id) = account_id.as_deref() {
                hash_id(&["chatgpt-account", account_id])
            } else if let Some(email) = email.as_deref() {
                hash_id(&["chatgpt-email", email])
            } else {
                let access_token = tokens
                    .map(|tokens| tokens.access_token.as_str())
                    .unwrap_or_default();
                let refresh_token = tokens
                    .map(|tokens| tokens.refresh_token.as_str())
                    .unwrap_or_default();
                hash_id(&["chatgpt-token", access_token, refresh_token])
            };
            let label = email
                .clone()
                .or_else(|| account_id.as_ref().map(|id| format!("ChatGPT {id}")))
                .unwrap_or_else(|| "ChatGPT account".to_string());
            AuthUserMetadata {
                id,
                label,
                auth_mode,
                email,
                account_id,
                plan_type,
                updated_at,
            }
        }
        AuthMode::AgentIdentity => {
            let agent_identity = auth.agent_identity.as_deref().unwrap_or_default();
            let id = hash_id(&["agent-identity", agent_identity]);
            AuthUserMetadata {
                id,
                label: "Agent identity".to_string(),
                auth_mode,
                email: None,
                account_id: None,
                plan_type: None,
                updated_at,
            }
        }
        AuthMode::PersonalAccessToken => {
            let personal_access_token = auth.personal_access_token.as_deref().unwrap_or_default();
            let id = hash_id(&["personal-access-token", personal_access_token]);
            AuthUserMetadata {
                id,
                label: format!(
                    "Personal access token {}",
                    secret_tail(personal_access_token)
                ),
                auth_mode,
                email: None,
                account_id: None,
                plan_type: None,
                updated_at,
            }
        }
    }
}

fn summary_from_metadata(metadata: AuthUserMetadata, current_id: Option<&str>) -> AuthUserSummary {
    AuthUserSummary {
        is_current: current_id == Some(metadata.id.as_str()),
        id: metadata.id,
        label: metadata.label,
        auth_mode: metadata.auth_mode,
        email: metadata.email,
        account_id: metadata.account_id,
        plan_type: metadata.plan_type,
        updated_at: metadata.updated_at,
    }
}

fn upsert_index_metadata(
    codex_home: &Path,
    metadata: AuthUserMetadata,
    make_active: bool,
) -> std::io::Result<AuthUserMetadata> {
    let mut index = load_index(codex_home)?;
    if let Some(existing) = index.users.iter_mut().find(|user| user.id == metadata.id) {
        *existing = metadata.clone();
    } else {
        index.users.push(metadata.clone());
    }
    if make_active {
        index.active_user_id = Some(metadata.id.clone());
    }
    save_index(codex_home, &index)?;
    Ok(metadata)
}

pub fn save_auth_user(
    codex_home: &Path,
    auth: &AuthDotJson,
    auth_credentials_store_mode: AuthCredentialsStoreMode,
) -> std::io::Result<Option<AuthUserSummary>> {
    if auth_credentials_store_mode == AuthCredentialsStoreMode::Ephemeral {
        return Ok(None);
    }

    let metadata = metadata_from_auth(auth);
    let auth_home = user_auth_home(codex_home, &metadata.id);
    save_stored_auth(&auth_home, auth, auth_credentials_store_mode)?;
    let metadata = upsert_index_metadata(codex_home, metadata, /*make_active*/ true)?;
    Ok(Some(summary_from_metadata(metadata, None)))
}

pub fn save_current_auth_user(
    codex_home: &Path,
    auth_credentials_store_mode: AuthCredentialsStoreMode,
) -> std::io::Result<Option<AuthUserSummary>> {
    if auth_credentials_store_mode == AuthCredentialsStoreMode::Ephemeral {
        return Ok(None);
    }

    match load_stored_auth(codex_home, auth_credentials_store_mode)? {
        Some(auth) => save_auth_user(codex_home, &auth, auth_credentials_store_mode),
        None => Ok(None),
    }
}

pub fn remove_auth_user(
    codex_home: &Path,
    auth: &AuthDotJson,
    auth_credentials_store_mode: AuthCredentialsStoreMode,
) -> std::io::Result<bool> {
    if auth_credentials_store_mode == AuthCredentialsStoreMode::Ephemeral {
        return Ok(false);
    }

    let metadata = metadata_from_auth(auth);
    let mut index = load_index(codex_home)?;
    let original_len = index.users.len();
    index.users.retain(|user| user.id != metadata.id);
    if index.active_user_id.as_deref() == Some(metadata.id.as_str()) {
        index.active_user_id = None;
    }
    save_index(codex_home, &index)?;

    let auth_home = user_auth_home(codex_home, &metadata.id);
    let deleted = delete_stored_auth(&auth_home, auth_credentials_store_mode)?;
    let _ = std::fs::remove_dir_all(auth_home);
    Ok(deleted || index.users.len() != original_len)
}

pub fn list_auth_users(
    codex_home: &Path,
    auth_credentials_store_mode: AuthCredentialsStoreMode,
) -> std::io::Result<Vec<AuthUserSummary>> {
    if auth_credentials_store_mode != AuthCredentialsStoreMode::Ephemeral {
        let _ = save_current_auth_user(codex_home, auth_credentials_store_mode)?;
    }

    let current_id = load_stored_auth(codex_home, auth_credentials_store_mode)?
        .map(|auth| metadata_from_auth(&auth).id)
        .or_else(|| {
            load_index(codex_home)
                .ok()
                .and_then(|index| index.active_user_id)
        });
    let mut users = load_index(codex_home)?
        .users
        .into_iter()
        .map(|metadata| summary_from_metadata(metadata, current_id.as_deref()))
        .collect::<Vec<_>>();
    users.sort_by(|a, b| {
        b.is_current
            .cmp(&a.is_current)
            .then_with(|| a.label.to_lowercase().cmp(&b.label.to_lowercase()))
    });
    Ok(users)
}

pub fn switch_auth_user(
    codex_home: &Path,
    user_id: &str,
    auth_credentials_store_mode: AuthCredentialsStoreMode,
) -> std::io::Result<AuthUserSummary> {
    if auth_credentials_store_mode == AuthCredentialsStoreMode::Ephemeral {
        return Err(std::io::Error::other(
            "user switching is unavailable for ephemeral auth",
        ));
    }

    let _ = save_current_auth_user(codex_home, auth_credentials_store_mode)?;
    let index = load_index(codex_home)?;
    let metadata = index
        .users
        .into_iter()
        .find(|user| user.id == user_id)
        .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::NotFound, "user not found"))?;

    let auth_home = user_auth_home(codex_home, &metadata.id);
    let auth = load_stored_auth(&auth_home, auth_credentials_store_mode)?.ok_or_else(|| {
        std::io::Error::new(
            std::io::ErrorKind::NotFound,
            "stored credentials for user were not found",
        )
    })?;
    save_stored_auth(codex_home, &auth, auth_credentials_store_mode)?;
    let metadata = upsert_index_metadata(codex_home, metadata, /*make_active*/ true)?;
    Ok(summary_from_metadata(metadata, Some(user_id)))
}

pub fn same_auth_user(a: &AuthDotJson, b: &AuthDotJson) -> bool {
    metadata_from_auth(a).id == metadata_from_auth(b).id
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::token_data::IdTokenInfo;
    use crate::token_data::TokenData;
    use codex_protocol::auth::PlanType as InternalPlanType;
    use tempfile::tempdir;

    fn chatgpt_auth(email: &str, account_id: &str) -> AuthDotJson {
        AuthDotJson {
            auth_mode: Some(AuthMode::Chatgpt),
            openai_api_key: None,
            tokens: Some(TokenData {
                id_token: IdTokenInfo {
                    email: Some(email.to_string()),
                    chatgpt_account_id: Some(account_id.to_string()),
                    chatgpt_plan_type: Some(InternalPlanType::from_raw_value("pro")),
                    ..Default::default()
                },
                access_token: format!("access-{account_id}"),
                refresh_token: format!("refresh-{account_id}"),
                account_id: Some(account_id.to_string()),
            }),
            last_refresh: Some(Utc::now()),
            agent_identity: None,
            personal_access_token: None,
        }
    }

    #[test]
    fn saves_and_switches_auth_users_without_exposing_secrets_in_index() {
        let codex_home = tempdir().unwrap();
        let first = chatgpt_auth("first@example.com", "account-first");
        let second = chatgpt_auth("second@example.com", "account-second");

        save_auth_user(codex_home.path(), &first, AuthCredentialsStoreMode::File)
            .expect("save first user");
        save_stored_auth(codex_home.path(), &second, AuthCredentialsStoreMode::File)
            .expect("save active second auth");
        save_auth_user(codex_home.path(), &second, AuthCredentialsStoreMode::File)
            .expect("save second user");

        let users = list_auth_users(codex_home.path(), AuthCredentialsStoreMode::File)
            .expect("list auth users");
        assert_eq!(users.len(), 2);
        assert!(users.iter().any(|user| user.label == "first@example.com"));
        assert!(users.iter().any(|user| user.label == "second@example.com"));

        let first_id = metadata_from_auth(&first).id;
        switch_auth_user(codex_home.path(), &first_id, AuthCredentialsStoreMode::File)
            .expect("switch to first user");
        let active = load_stored_auth(codex_home.path(), AuthCredentialsStoreMode::File)
            .expect("load active auth")
            .expect("active auth");
        assert_eq!(metadata_from_auth(&active).id, first_id);

        let index_contents =
            std::fs::read_to_string(users_index_path(codex_home.path())).expect("read index");
        assert!(!index_contents.contains("access-account-first"));
        assert!(!index_contents.contains("refresh-account-first"));
    }
}
