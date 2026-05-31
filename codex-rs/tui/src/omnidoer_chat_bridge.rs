//! Bridge the paired OmniDoer Control Client chat into the active TUI session.
//!
//! This is intentionally process-local. The browser client writes to the
//! Control Service chat queue; the active TUI polls and claims those messages,
//! then republishes live TUI events back to the same queue for the phone UI.

use std::env;
use std::ffi::OsString;
use std::path::Path;
use std::path::PathBuf;
use std::process::Stdio;
use std::sync::OnceLock;
use std::time::Duration;

use codex_app_server_protocol::ServerNotification;
use codex_app_server_protocol::ThreadItem;
use codex_app_server_protocol::UserInput;
use serde::Deserialize;
use tokio::process::Command;
use tokio::sync::mpsc;
use tokio::time::MissedTickBehavior;
use tokio::time::timeout;

use crate::app_event::AppEvent;
use crate::app_event_sender::AppEventSender;

const DEFAULT_POLL_INTERVAL_MS: u64 = 1000;
const COMMAND_TIMEOUT: Duration = Duration::from_secs(15);
const RECORD_TEXT_LIMIT: usize = 6000;

static OUTBOUND_TX: OnceLock<mpsc::UnboundedSender<OutboundEvent>> = OnceLock::new();

#[derive(Debug)]
pub(crate) struct RemoteUserMessage {
    pub(crate) message_id: String,
    pub(crate) text: String,
    pub(crate) local_image_paths: Vec<PathBuf>,
}

#[derive(Debug, Deserialize)]
struct ChatNextResponse {
    status: String,
    #[serde(default)]
    message: Option<ControlChatMessage>,
}

#[derive(Debug, Deserialize)]
struct ControlChatMessage {
    message_id: String,
    text: String,
    #[serde(default)]
    attachments: Vec<ControlChatAttachment>,
}

#[derive(Debug, Deserialize)]
struct ControlChatAttachment {
    path: String,
    #[serde(default)]
    content_type: String,
}

#[derive(Debug)]
enum OutboundEvent {
    AssistantDelta(String),
    AssistantFinal(String),
    AssistantComplete,
    Record {
        record_type: &'static str,
        text: String,
        role: Option<&'static str>,
    },
}

pub(crate) fn spawn(app_event_tx: AppEventSender) {
    if !bridge_enabled() {
        return;
    }

    let _ = OUTBOUND_TX.set(spawn_publisher());
    spawn_inbound_poller(app_event_tx);
}

pub(crate) fn publish_server_notification(notification: &ServerNotification) {
    let Some(tx) = OUTBOUND_TX.get() else {
        return;
    };

    match notification {
        ServerNotification::TurnStarted(_) => {
            send_outbound(
                tx,
                OutboundEvent::Record {
                    record_type: "status",
                    text: "Codex turn started in the active TUI.".to_string(),
                    role: Some("system"),
                },
            );
        }
        ServerNotification::TurnCompleted(notification) => {
            let status = format!("Codex turn completed: {:?}", notification.turn.status);
            send_outbound(
                tx,
                OutboundEvent::Record {
                    record_type: "status",
                    text: status,
                    role: Some("system"),
                },
            );
            send_outbound(tx, OutboundEvent::AssistantComplete);
        }
        ServerNotification::AgentMessageDelta(notification) => {
            send_outbound(
                tx,
                OutboundEvent::AssistantDelta(notification.delta.clone()),
            );
        }
        ServerNotification::PlanDelta(notification) => {
            send_outbound(
                tx,
                OutboundEvent::AssistantDelta(notification.delta.clone()),
            );
        }
        ServerNotification::ItemStarted(notification) => {
            if let Some(text) = item_started_record_text(&notification.item) {
                send_outbound(
                    tx,
                    OutboundEvent::Record {
                        record_type: "tool_call",
                        text,
                        role: Some("assistant"),
                    },
                );
            }
        }
        ServerNotification::ItemCompleted(notification) => match &notification.item {
            ThreadItem::UserMessage { content, .. } => {
                let text = user_input_record_text(content);
                if !text.is_empty() {
                    send_outbound(
                        tx,
                        OutboundEvent::Record {
                            record_type: "message",
                            text,
                            role: Some("user"),
                        },
                    );
                }
            }
            ThreadItem::AgentMessage { text, .. } if !text.is_empty() => {
                send_outbound(tx, OutboundEvent::AssistantFinal(text.clone()));
            }
            ThreadItem::CommandExecution {
                status,
                exit_code,
                aggregated_output,
                ..
            } => {
                let mut text = aggregated_output.clone().unwrap_or_default();
                if text.is_empty() {
                    text = format!("status={status:?}");
                }
                text.push_str(&format!("\nexit_code={exit_code:?} status={status:?}"));
                send_outbound(
                    tx,
                    OutboundEvent::Record {
                        record_type: "tool_output",
                        text,
                        role: Some("assistant"),
                    },
                );
            }
            ThreadItem::McpToolCall {
                server,
                tool,
                status,
                result,
                error,
                ..
            } => {
                let record_type = if error.is_some() {
                    "error"
                } else {
                    "tool_output"
                };
                let text = if let Some(error) = error {
                    format!("{server}.{tool} failed: {error:?}")
                } else {
                    format!("{server}.{tool} {status:?}: {result:?}")
                };
                send_outbound(
                    tx,
                    OutboundEvent::Record {
                        record_type,
                        text,
                        role: Some("assistant"),
                    },
                );
            }
            ThreadItem::Plan { text, .. } if !text.is_empty() => {
                send_outbound(tx, OutboundEvent::AssistantFinal(text.clone()));
            }
            _ => {}
        },
        ServerNotification::CommandExecutionOutputDelta(notification) => {
            send_outbound(
                tx,
                OutboundEvent::Record {
                    record_type: "tool_output",
                    text: notification.delta.clone(),
                    role: Some("assistant"),
                },
            );
        }
        ServerNotification::FileChangeOutputDelta(notification) => {
            send_outbound(
                tx,
                OutboundEvent::Record {
                    record_type: "tool_output",
                    text: notification.delta.clone(),
                    role: Some("assistant"),
                },
            );
        }
        ServerNotification::Error(notification) => {
            let mut text = notification.error.message.clone();
            if let Some(details) = &notification.error.additional_details
                && !details.is_empty()
            {
                text.push('\n');
                text.push_str(details);
            }
            send_outbound(
                tx,
                OutboundEvent::Record {
                    record_type: "error",
                    text,
                    role: Some("system"),
                },
            );
        }
        _ => {}
    }
}

fn item_started_record_text(item: &ThreadItem) -> Option<String> {
    match item {
        ThreadItem::CommandExecution { command, .. } => Some(format!("$ {command}")),
        ThreadItem::McpToolCall {
            server,
            tool,
            arguments,
            ..
        } => Some(format!("{server}.{tool} {arguments}")),
        ThreadItem::WebSearch { query, .. } => Some(format!("Web search: {query}")),
        ThreadItem::FileChange { changes, .. } => Some(format!("File changes: {changes:?}")),
        ThreadItem::ImageGeneration { status, .. } => {
            Some(format!("Image generation started: {status}"))
        }
        _ => None,
    }
}

fn user_input_record_text(content: &[UserInput]) -> String {
    content
        .iter()
        .map(|item| match item {
            UserInput::Text { text, .. } => text.clone(),
            UserInput::Image { url, .. } => format!("[image] {url}"),
            UserInput::LocalImage { path, .. } => format!("[local image] {}", path.display()),
            UserInput::Skill { name, path } => format!("[skill] {name}: {}", path.display()),
            UserInput::Mention { name, path } => format!("[mention] {name}: {path}"),
        })
        .filter(|text| !text.is_empty())
        .collect::<Vec<_>>()
        .join("\n")
}

fn send_outbound(tx: &mpsc::UnboundedSender<OutboundEvent>, event: OutboundEvent) {
    if let Err(err) = tx.send(event) {
        tracing::warn!(%err, "failed to queue OmniDoer chat bridge event");
    }
}

fn spawn_inbound_poller(app_event_tx: AppEventSender) {
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(poll_interval());
        interval.set_missed_tick_behavior(MissedTickBehavior::Delay);
        loop {
            interval.tick().await;
            refresh_heartbeat();
            match claim_next_message().await {
                Ok(Some(message)) => {
                    app_event_tx.send(AppEvent::OmniDoerRemoteUserMessage {
                        message_id: message.message_id,
                        text: message.text,
                        local_image_paths: message.local_image_paths,
                    });
                }
                Ok(None) => {}
                Err(err) => {
                    tracing::warn!(%err, "OmniDoer chat bridge failed to claim message");
                }
            }
        }
    });
}

fn spawn_publisher() -> mpsc::UnboundedSender<OutboundEvent> {
    let (tx, mut rx) = mpsc::unbounded_channel();
    tokio::spawn(async move {
        let mut assistant_message_id: Option<String> = None;
        let mut assistant_has_delta = false;
        while let Some(event) = rx.recv().await {
            match event {
                OutboundEvent::AssistantDelta(delta) => {
                    if delta.is_empty() {
                        continue;
                    }
                    if assistant_message_id.is_none() {
                        assistant_message_id = start_assistant_message().await;
                        assistant_has_delta = false;
                    }
                    if let Some(message_id) = assistant_message_id.as_deref() {
                        append_assistant_delta(message_id, &delta).await;
                        assistant_has_delta = true;
                    }
                }
                OutboundEvent::AssistantFinal(text) => {
                    if text.is_empty() {
                        continue;
                    }
                    if assistant_message_id.is_none() {
                        assistant_message_id = start_assistant_message().await;
                        assistant_has_delta = false;
                    }
                    if let Some(message_id) = assistant_message_id.as_deref()
                        && !assistant_has_delta
                    {
                        append_assistant_delta(message_id, &text).await;
                        assistant_has_delta = true;
                    }
                    if let Some(message_id) = assistant_message_id.take() {
                        complete_assistant_message(&message_id).await;
                    }
                    assistant_has_delta = false;
                }
                OutboundEvent::AssistantComplete => {
                    if let Some(message_id) = assistant_message_id.take() {
                        complete_assistant_message(&message_id).await;
                    }
                    assistant_has_delta = false;
                }
                OutboundEvent::Record {
                    record_type,
                    text,
                    role,
                } => {
                    publish_record(record_type, &clip(&text), role).await;
                }
            }
        }
    });
    tx
}

async fn claim_next_message() -> Result<Option<RemoteUserMessage>, String> {
    let stdout = run_omnidoer(["control", "chat-next"].map(OsString::from).to_vec()).await?;
    parse_claimed_message(&stdout)
}

async fn start_assistant_message() -> Option<String> {
    match run_omnidoer(["control", "chat-start"].map(OsString::from).to_vec()).await {
        Ok(stdout) => {
            let message_id = stdout.trim().to_string();
            (!message_id.is_empty()).then_some(message_id)
        }
        Err(err) => {
            tracing::warn!(%err, "failed to start OmniDoer assistant chat message");
            None
        }
    }
}

async fn append_assistant_delta(message_id: &str, delta: &str) {
    let args = vec![
        OsString::from("control"),
        OsString::from("chat-delta"),
        OsString::from(message_id),
        OsString::from(delta),
    ];
    if let Err(err) = run_omnidoer(args).await {
        tracing::warn!(%err, "failed to publish OmniDoer assistant delta");
    }
}

async fn complete_assistant_message(message_id: &str) {
    let args = vec![
        OsString::from("control"),
        OsString::from("chat-complete"),
        OsString::from(message_id),
    ];
    if let Err(err) = run_omnidoer(args).await {
        tracing::warn!(%err, "failed to complete OmniDoer assistant chat message");
    }
}

async fn publish_record(record_type: &str, text: &str, role: Option<&str>) {
    if text.is_empty() {
        return;
    }
    let mut args = vec![
        OsString::from("control"),
        OsString::from("chat-record"),
        OsString::from(record_type),
        OsString::from(text),
    ];
    if let Some(role) = role {
        args.push(OsString::from("--role"));
        args.push(OsString::from(role));
    }
    if let Err(err) = run_omnidoer(args).await {
        tracing::warn!(%err, "failed to publish OmniDoer chat record");
    }
}

async fn run_omnidoer(args: Vec<OsString>) -> Result<String, String> {
    let mut command = omnidoer_command();
    command.args(args);
    command.stdin(Stdio::null());
    command.stderr(Stdio::null());
    command.kill_on_drop(true);
    let output = timeout(COMMAND_TIMEOUT, command.output())
        .await
        .map_err(|_| "omnidoer command timed out".to_string())?
        .map_err(|err| format!("omnidoer command failed: {err}"))?;
    if !output.status.success() {
        return Err(format!("omnidoer command exited with {}", output.status));
    }
    String::from_utf8(output.stdout).map_err(|err| format!("omnidoer output was not UTF-8: {err}"))
}

fn omnidoer_command() -> Command {
    if let Ok(cli) = env::var("OMNIDOER_CLI")
        && !cli.trim().is_empty()
    {
        return Command::new(cli);
    }
    if let Ok(python) = env::var("OMNIDOER_PYTHON")
        && !python.trim().is_empty()
    {
        let mut command = Command::new(python);
        command.arg("-m").arg("omnidoer.omni_cli.main");
        add_install_dir_to_pythonpath(&mut command);
        return command;
    }
    Command::new("omnidoer")
}

fn add_install_dir_to_pythonpath(command: &mut Command) {
    let Some(install_dir) = env::var_os("OMNIDOER_INSTALL_DIR") else {
        return;
    };
    let mut paths = vec![PathBuf::from(install_dir)];
    if let Some(existing) = env::var_os("PYTHONPATH") {
        paths.extend(env::split_paths(&existing));
    }
    if let Ok(joined) = env::join_paths(paths) {
        command.env("PYTHONPATH", joined);
    }
}

fn refresh_heartbeat() {
    let Some(path) = state_file("control_chat_bridge_heartbeat") else {
        return;
    };
    if let Some(parent) = path.parent()
        && let Err(err) = std::fs::create_dir_all(parent)
    {
        tracing::warn!(%err, path = %parent.display(), "failed to create OmniDoer state directory");
        return;
    }
    let now = chrono::Utc::now().timestamp_millis().to_string();
    if let Err(err) = std::fs::write(&path, now) {
        tracing::warn!(
            %err,
            path = %path.display(),
            "failed to write OmniDoer chat bridge heartbeat"
        );
    }
}

fn state_file(name: &str) -> Option<PathBuf> {
    let home = env::var_os("OMNIDOER_HOME")
        .map(PathBuf::from)
        .or_else(|| env::var_os("HOME").map(|home| PathBuf::from(home).join(".omnidoer")))?;
    Some(home.join(name))
}

fn parse_claimed_message(stdout: &str) -> Result<Option<RemoteUserMessage>, String> {
    let payload: ChatNextResponse =
        serde_json::from_str(stdout).map_err(|err| format!("invalid chat-next JSON: {err}"))?;
    match payload.status.as_str() {
        "empty" => Ok(None),
        "ok" => {
            let message = payload
                .message
                .ok_or_else(|| "chat-next ok response omitted message".to_string())?;
            Ok(Some(RemoteUserMessage {
                message_id: message.message_id,
                text: message.text,
                local_image_paths: image_attachment_paths(&message.attachments),
            }))
        }
        other => Err(format!("chat-next returned unexpected status {other:?}")),
    }
}

fn image_attachment_paths(attachments: &[ControlChatAttachment]) -> Vec<PathBuf> {
    attachments
        .iter()
        .filter_map(|attachment| {
            let path = PathBuf::from(attachment.path.trim());
            if is_image_attachment(&path, &attachment.content_type) && path.is_file() {
                Some(path)
            } else {
                None
            }
        })
        .collect()
}

fn is_image_attachment(path: &Path, content_type: &str) -> bool {
    if content_type.starts_with("image/") {
        return true;
    }
    matches!(
        path.extension()
            .and_then(|suffix| suffix.to_str())
            .map(str::to_ascii_lowercase)
            .as_deref(),
        Some("png" | "jpg" | "jpeg" | "gif" | "webp" | "bmp")
    )
}

fn bridge_enabled() -> bool {
    if env_disabled("OMNIDOER_TUI_CHAT_BRIDGE") {
        return false;
    }
    env::var("OMNIDOER_CONSOLE").is_ok() || env_enabled("OMNIDOER_TUI_CHAT_BRIDGE")
}

fn poll_interval() -> Duration {
    let milliseconds = env::var("OMNIDOER_TUI_CHAT_BRIDGE_INTERVAL_MS")
        .ok()
        .and_then(|value| value.parse::<u64>().ok())
        .unwrap_or(DEFAULT_POLL_INTERVAL_MS)
        .clamp(250, 30_000);
    Duration::from_millis(milliseconds)
}

fn env_enabled(name: &str) -> bool {
    env::var(name)
        .map(|value| matches!(value.as_str(), "1" | "true" | "TRUE" | "yes" | "YES"))
        .unwrap_or(false)
}

fn env_disabled(name: &str) -> bool {
    env::var(name)
        .map(|value| matches!(value.as_str(), "0" | "false" | "FALSE" | "no" | "NO"))
        .unwrap_or(false)
}

fn clip(text: &str) -> String {
    if text.len() <= RECORD_TEXT_LIMIT {
        return text.to_string();
    }
    let mut end = RECORD_TEXT_LIMIT;
    while !text.is_char_boundary(end) {
        end -= 1;
    }
    let omitted = text.len() - end;
    format!("{}\n...[truncated {omitted} bytes]", &text[..end])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_empty_chat_next_response() {
        let parsed = parse_claimed_message(r#"{"status":"empty","secret_fields_allowed":false}"#)
            .expect("empty response should parse");
        assert!(parsed.is_none());
    }

    #[test]
    fn parse_claimed_message_with_image_attachment() {
        let temp = tempfile::NamedTempFile::new().expect("temp file");
        let path = temp.path().with_extension("png");
        std::fs::copy(temp.path(), &path).expect("copy temp image");
        let json = format!(
            r#"{{
              "status": "ok",
              "message": {{
                "message_id": "msg_1",
                "text": "see attached",
                "attachments": [{{
                  "path": {},
                  "content_type": "image/png"
                }}]
              }}
            }}"#,
            serde_json::to_string(path.to_str().expect("utf8 path")).expect("path json")
        );
        let parsed = parse_claimed_message(&json)
            .expect("ok response should parse")
            .expect("message should be present");
        assert_eq!(parsed.message_id, "msg_1");
        assert_eq!(parsed.text, "see attached");
        assert_eq!(parsed.local_image_paths, vec![path]);
    }

    #[test]
    fn clip_preserves_utf8_boundary() {
        let text = format!("{}é", "a".repeat(RECORD_TEXT_LIMIT));
        let clipped = clip(&text);
        assert!(clipped.contains("[truncated "));
    }
}
