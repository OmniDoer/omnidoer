const I18N = {
  en: {
    appTitle: "OmniDoer Control Client",
    appSubtitle: "Secure approvals, credentials, challenges, and human takeover.",
    navOverview: "Home",
    navRequests: "Requests",
    navTasks: "Chat",
    navDevices: "Devices",
    navSecurity: "Security",
    navTakeover: "Takeover",
    takeoverTabLive: "Live",
    takeoverTabPreview: "View",
    navPayments: "Payments",
    navPair: "Pair",
    checkingRuntime: "Checking runtime...",
    runtimeModeCloudDirect: (mode) => `Control Service: ${mode}`,
    runtimeModeAttached: "Current CLI synced",
    runtimeModeLegacyRelay: "Server paired; current session not natively synced",
    runtimeModeServerOnly: "Server paired; current CLI not attached",
    runtimeModeUnpaired: "Control Service reachable",
    runtimeModeBackground: "Background runner",
    runtimeModeOffline: "Control Service offline",
    runtimeDetail: "Control Client does not call OpenAI APIs or models directly.",
    runtimeUnpairedDetail: "This browser is not paired yet. Open a fresh pairing link on this device and tap Pair Device before using requests or session sync.",
    runtimeOffline: "Runtime offline",
    runtimeOfflineDetail: "Start omnidoer control serve.",
    runtimeBridgeActive: "Live Linux console bridge is active; messages sync with the current TUI.",
    runtimeLegacyRelayActive: "Pairing only authenticates this browser to the server. Temporary terminal relay can paste messages into the visible console, but full current-session context sync needs restart:",
    runtimeLegacyRelayPause: "Pause sends Ctrl-C to the current console before delivering your instruction.",
    runtimeNativeBridgeReady: "Full structured bridge is installed; restart will switch this session to native sync.",
    runtimeActiveConsoleNeedsBinaryRestart: "The active console is still running an older Codex binary. Restart keeps this thread but loads the installed native bridge.",
    runtimeNativeBridgeNotReady: "Native structured bridge is not installed yet; update OmniDoer before restarting.",
    runtimeWaitingForConsoleRestart: "Linux console is active but not yet bridged. Restart OmniDoer console with:",
    runtimeBackgroundRunner: "No live Linux console bridge; queued messages use the background Codex runner.",
    chatSessionCheckingTitle: "Checking current CLI session",
    chatSessionCheckingDetail: "Pairing authenticates this browser; session sync also needs a live CLI bridge.",
    chatSessionUnpairedTitle: "Pair this browser",
    chatSessionUnpairedDetail: "This browser has not authenticated to the Control Service yet. Pair it before using chat, requests, or session sync.",
    chatSessionAttachedTitle: "Current CLI session attached",
    chatSessionAttachedDetail: "Phone messages and streamed output are synced with the active Linux TUI.",
    chatSessionLegacyTitle: "Server paired; current session not synced",
    chatSessionLegacyDetail: "This browser is authenticated to the server. Until current-session sync is enabled, messages are only temporary tmux paste into the visible console, not a native client for this conversation.",
    chatSessionServerOnlyTitle: "Paired to server only",
    chatSessionServerOnlyDetail: "This browser is authenticated, but the current CLI session is not attached yet. Restart the bridge before using this as the same conversation.",
    chatSessionBackgroundTitle: "Background runner",
    chatSessionBackgroundDetail: "Messages are handled by a background Codex runner because no live CLI bridge is attached.",
    chatSessionOfflineTitle: "Control Service offline",
    chatSessionOfflineDetail: "Reconnect to the Control Service before sending messages.",
    chatSyncDiagnosticNative: "Diagnostic: native two-way sync is active.",
    chatSyncDiagnosticLegacy: "Diagnostic: server pairing is active, but full context memory and structured streaming are not attached.",
    chatSyncDiagnosticStaleBinary: "Diagnostic: this is the current console, but its running binary lacks the native bridge. Restart is required for structured two-way sync.",
    chatSyncDiagnosticWaiting: "Diagnostic: paired to this server, but the current CLI conversation is not attached yet.",
    chatSyncDiagnosticBackground: "Diagnostic: using background runner, not a live CLI conversation.",
    overviewTitle: "Control Center",
    overviewIntro: "Session sync, requests, browser handoff, and chat stay in one touch-first workspace.",
    overviewNextActionTitle: "Next action",
    overviewSyncTitle: "Session sync",
    overviewRequestsTitle: "Requests",
    overviewBrowserTitle: "Browser",
    overviewChatTitle: "Chat",
    overviewPairingTitle: "Pairing",
    overviewOpenRequests: (open, total) => `${open} open / ${total} total`,
    overviewChatRecords: (messages, records) => `${messages} messages · ${records} activity records`,
    overviewPaired: "Paired",
    overviewUnpaired: "Not paired",
    overviewSyncAttached: "Native sync active",
    overviewSyncNeedsRestart: "Enable current session sync",
    overviewSyncServerOnly: "CLI not attached",
    overviewSyncBackground: "Background runner",
    overviewSyncOffline: "Offline",
    overviewBrowserIdle: "No live browser handoff.",
    overviewBrowserPreview: "Browser preview available.",
    overviewBrowserActive: "You control the browser.",
    overviewNoUrgentAction: "No urgent action",
    overviewNoUrgentDetail: "Use Chat or Takeover when you need to direct the Agent.",
    overviewActionPairTitle: "Pair this browser",
    overviewActionPairDetail: "Pair this device before using requests or current-session sync.",
    overviewActionSyncTitle: "Approve current-session sync",
    overviewActionSyncDetail: "Restart the active Linux CLI to attach this phone to the same thread.",
    overviewActionRequestTitle: (type) => `Review ${type}`,
    overviewActionRequestDetail: (summary) => summary || "A request needs your attention.",
    overviewActionBrowserTitle: "Take over browser",
    overviewActionBrowserDetail: "A live browser can be viewed or paused for human control.",
    overviewActionChatTitle: "Open chat",
    overviewPrimaryAction: "Open",
    overviewSecondaryAction: "Details",
    sendToCurrentCli: "Send to current CLI",
    sendToCurrentConsole: "Paste to CLI",
    sendToBackgroundRunner: "Send to background",
    sendUnavailable: "Restart bridge first",
    chatPlaceholderLegacy: "Temporary paste only; enable current session sync for shared context",
    chatPlaceholderUnavailable: "Restart the bridge before sending into this conversation",
    chatSendBlocked: "Chat not attached",
    chatDeliveredToConsole: "Pasted to Linux console",
    chatDeliveredToConsoleDetail: "Temporary terminal relay pasted this message into the active TUI; this is not native session sync.",
    chatQueuedForBridge: "Message queued for console bridge",
    chatQueuedForBridgeDetail: "The Control Service accepted the message; it will deliver when the bridge is ready.",
    copyCommand: "Copy command",
    copiedCommand: "Command copied",
    copyCommandFailed: "Copy failed",
    restartBridge: "Restart bridge",
    enableCurrentSessionSync: "Enable current session sync",
    restartBridgeConfirm: "Restart the active Linux console in its tmux pane to enable full phone sync?",
    restartBridgeConfirmDetailed: (threadId) => `Enable full phone sync for thread ${threadId || "current"}? This restarts the active Codex TUI in its tmux pane, keeps the same thread, and loads the installed native bridge.`,
    restartBridgeStarted: "Console bridge restart started",
    restartBridgeChecking: "Waiting for native bridge heartbeat...",
    restartBridgeActivated: "Current CLI session sync is active.",
    restartBridgeStillWaiting: "Restart was requested, but the current CLI is still not publishing native bridge heartbeats.",
    restartBridgeFailed: "Restart failed",
    restartBridgeApprovalRequested: "Sync enablement needs approval",
    restartBridgeApprovalRequestedDetail: "A high-risk request was created and kept visible for 30 minutes. Review and approve it in Requests to restart the current CLI.",
    reviewSyncRequest: "Review sync request",
    chatSyncApprovalPending: "A current-session sync approval request is pending.",
    syncApprovalTitle: "Current session sync pending",
    syncApprovalDetail: "Approve to restart the active Linux CLI in its tmux pane and attach this device to the same conversation.",
    syncApprovalThread: "Thread",
    syncApprovalPid: "CLI PID",
    syncApprovalCommand: "Command",
    syncApprovalExpires: "Expires",
    syncApprovalRenewing: "Refreshing sync request...",
    syncApprovalRenewed: "Sync request refreshed",
    syncApprovalExpired: "Sync approval expired; request a fresh sync.",
    syncApprovalConfirmText: "I understand this restarts the active Codex TUI and keeps the same thread.",
    syncApprovalOpenRequest: "Open full request",
    syncApprovalApprove: "Approve sync",
    consoleRestartReviewRequired: "Current session sync needs confirmation",
    consoleRestartReviewRequiredDetail: "Check the restart details before approving.",
    consoleRestartConfirmText: "I understand this restarts the active Codex TUI in its tmux pane and keeps the same thread.",
    consoleRestartThread: "Thread",
    consoleRestartCommand: "Restart command",
    consoleRestartCurrentState: "Current state",
    consoleRestartCurrentPid: "Current CLI PID",
    consoleRestartPane: "tmux pane",
    consoleRestartNativeSync: "Native sync active",
    consoleRestartAfterApproval: "After approval",
    legacyTerminalTitle: "Live Linux Console",
    requestsCount: (open, total) => `Requests: ${open} open / ${total} total`,
    attentionTitle: (count) => `${count} request${count === 1 ? " needs" : "s need"} attention`,
    attentionDetail: (type, status) => `${type} · ${status}`,
    attentionAction: "Review",
    requestsTitle: "Open Requests",
    requestsIntro: "Handle the items that need your attention. Secrets stay encrypted to the local broker.",
    requestFiltersLabel: "Request filters",
    filterOpen: "Open",
    filterAll: "All",
    filterCredential: "Secrets",
    filterChallenge: "Challenges",
    filterApproval: "Approvals",
    filterTakeover: "Takeover",
    loading: "Loading...",
    noOpenRequests: "No open requests.",
    noMatchingOpenRequests: "No open requests match this filter.",
    pairToViewRequests: "Pair this device to view requests in Cloud Direct Mode.",
    pairToReceiveEvents: "Pair this device to receive signed request events in Cloud Direct Mode.",
    waitingForUserAction: "Waiting for user action",
    credentialClosed: (status) => `Credential request is ${status}.`,
    challengeClosed: (status) => `Challenge request is ${status}.`,
    takeoverClosed: (status) => `Takeover request is ${status}.`,
    secretNote: "Secret fields are encrypted locally before submission. They are not sent to Agent/LLM context, MCP return values, logs, or DOM observation.",
    username: "Username",
    password: "Password",
    totpSeed: "TOTP seed",
    saveInVault: "Save encrypted in Vault",
    submitCredential: "Submit Credential",
    challengeNote: "Complete the challenge yourself. OmniDoer does not bypass CAPTCHA/MFA/Passkey/WebAuthn/3DS.",
    visualChallengeNote: "No challenge answer is submitted to OmniDoer. Complete it in the controlled browser or external device, then mark it complete.",
    submitChallenge: "Submit Challenge",
    markUserCompleted: "Mark User Completed",
    requestSubmitFailed: "Request submit failed",
    requestSubmitFailedDetail: "Pair again if this is Cloud Direct Mode.",
    actionFailed: "Action failed",
    pairTitle: "Pair Device",
    pairIntro: "Connect this browser to your own Control Service. Pair only devices you control.",
    pairSecurity: "After pairing, secret and challenge submissions are encrypted locally.",
    pairButton: "Pair Device",
    forgetPairing: "Forget Local Pairing",
    notPaired: "Not paired.",
    controlOffline: "Control Service is offline.",
    localTrustedMode: "Local trusted mode is active. Pairing is not required on localhost.",
    localTrustedDevice: "local trusted mode",
    pairingCodeLoaded: "Pairing code loaded. Confirm the server details, then pair this device.",
    pairFreshLink: "This browser is not paired. Pairing is per browser because the device key stays local; open a fresh pairing link on this device.",
    checkingCachedSession: "Checking cached pairing session...",
    sessionHidden: "This browser is authenticated. The current session is not visible in the latest session list.",
    sessionRevoked: "This browser's cached session was revoked. Pair again to continue.",
    pairedCached: "Paired. This browser stays paired long-term unless the session is revoked or browser data is cleared.",
    sessionValidUntil: (value) => `valid until ${value}`,
    cachedPairingRejected: "This browser has local pairing data, but its session cookie or signature was rejected. Open the same HTTPS origin, enable cookies, or pair again.",
    pairingDevice: "Pairing this device...",
    pairingFailed: "Pairing failed.",
    pairingFailedDetail: (reason) => `Pairing failed: ${reason}`,
    pairingExpired: "Pairing code expired. Open a fresh pairing link on this device.",
    pairingAlreadyUsed: "Pairing code reached its 10-use limit. Generate a fresh link for more devices.",
    pairingInvalid: "Pairing code is invalid. Open the latest pairing link.",
    pairedDevice: (name) => `Paired ${name}. This browser will stay paired long-term unless the session is revoked or browser data is cleared.`,
    localPairingRemoved: "Local pairing was removed from this browser. Server-side devices and sessions can still be revoked after pairing again.",
    deviceTitle: "Devices / Sessions",
    deviceIntro: "Review paired Control Clients and active sessions.",
    refresh: "Refresh",
    pairedDevices: "Paired Devices",
    sessions: "Sessions",
    pairToViewDevices: "Pair this device to view paired devices.",
    pairToViewSessions: "Pair this device to view sessions.",
    noPairedDevices: "No paired devices.",
    noSessions: "No sessions.",
    securityTitle: "Security",
    taskTitle: "Chat",
    taskIntro: "Messages stream through your paired Control Service.",
    chatComposerLabel: "Message",
    chatPlaceholder: "Write to OmniDoer",
    chatFilesLabel: "Attach",
    chatSelectedFiles: "Selected files",
    uploadFailed: "Upload failed",
    sendMessage: "Send Message",
    noChatMessages: "No chat messages yet.",
    pairToViewChat: "Pair this device to view and send chat messages.",
    chatStatusQueued: "Queued",
    chatStatusClaimed: "Delivered",
    chatStatusStreaming: "Streaming",
    chatStatusCompleted: "Completed",
    chatRecordDelta: "Delta",
    chatRecordStatus: "Status",
    chatRecordToolCall: "Tool call",
    chatRecordToolOutput: "Tool output",
    chatToolCalling: (name) => `Calling ${name}`,
    chatToolReturned: (name) => `${name} returned`,
    chatToolShell: "shell",
    chatToolWebSearch: "web search",
    chatToolUnknown: "tool",
    chatToolOutputNoContent: "no visible output",
    chatToolOutputLines: (count) => `${count} lines`,
    chatRecordReasoning: "Reasoning",
    chatRecordTerminal: "Terminal",
    chatRecordTerminalInput: "Terminal input",
    chatRecordTerminalSnapshot: "Snapshot",
    chatRecordTerminalDelta: "Delta",
    chatRecordChunks: (count) => `${count} chunks`,
    chatConversationTitle: "Conversation",
    chatActivityTitle: "Live activity",
    chatUserRole: "You",
    chatAssistantRole: "OmniDoer",
    chatRecordNumber: (sequence) => `record #${sequence}`,
    submitTask: "Submit Task",
    noQueuedTasks: "No queued tasks.",
    pairToViewTasks: "Pair this device to view task queue in Cloud Direct Mode.",
    takeoverTitle: "Human Takeover",
    takeoverNoActive: "No active takeover",
    noActiveBrowserHandoff: "No active browser handoff.",
    activeBrowserReady: "Active browser detected. Pause Agent to take over this browser.",
    activeBrowserPreview: "Live browser preview. Pause Agent to take control.",
    activeBrowserPreviewWaiting: "Waiting for live browser preview.",
    takeoverFrameWaiting: "Waiting for browser handoff",
    takeoverFrameWaitingControlled: "Waiting for the controlled browser frame...",
    takeoverFrameNextWaiting: "Waiting for next browser frame",
    takeoverFrameFresh: (seconds) => `Fresh ${seconds}s`,
    takeoverFrameStale: (seconds) => `Stale ${seconds}s - refresh before input`,
    takeoverFrameAdaptive: "adaptive",
    takeoverConnected: "connected",
    takeoverConnectedWebSocket: "connected - websocket",
    takeoverConnecting: "connecting",
    takeoverPausedHidden: "paused - page hidden",
    takeoverResuming: "resuming",
    takeoverPanOn: "Pan On",
    takeoverPanView: "Pan View",
    takeoverPanSuffix: " pan",
    refreshFrame: "Refresh Frame",
    zoomOut: "Zoom out",
    zoomReset: "Reset",
    zoomIn: "Zoom in",
    takeoverAgentPausedStatus: "Agent paused - user control active",
    takeoverFrameReady: "Live browser frame ready. Input is bound to the frame currently visible here.",
    takeoverFrameReadyWebSocket: "Live browser frame ready over WebSocket. Input is bound to the frame currently visible here.",
    takeoverDisconnected: "Browser context is not connected in this process.",
    takeoverWebSocketDisconnected: "Live frame WebSocket disconnected.",
    takeoverFrameFetchFailed: "Browser frame fetch failed.",
    takeoverReconnectRetry: (attempt) => `reconnecting - retry ${attempt}`,
    takeoverKeepingLastFrameShort: "keeping last frame",
    takeoverKeepingLastFrame: (message) => `${message} Keeping the last frame visible; stale frames remain blocked for input.`,
    takeoverInactive: "Takeover is not active. Agent control can resume after release.",
    takeoverLoadingFrame: "Loading control-only browser frame...",
    takeoverInputStateActive: "Touch, keyboard, and text input are routed to the controlled browser only.",
    takeoverInputHidden: "Input is blocked while this Control Client is hidden or frame polling is paused. Bring it to the foreground and refresh the frame before sending input.",
    takeoverInputNoFrame: "Wait for the current browser frame before sending input.",
    takeoverInputRefreshingStale: "Frame is stale; refreshing before input.",
    takeoverInputDelivered: (eventType) => `${eventType} delivered to controlled browser.`,
    takeoverInputQueued: (eventType) => `${eventType} queued for browser relay.`,
    takeoverInputFrameChanged: "Frame changed before input was delivered. Refreshing current browser frame.",
    takeoverInputDeliveryFailed: "Input was not delivered. The browser context may be disconnected.",
    takeoverInputStillPending: "Input is still waiting for browser acknowledgement. Refresh the frame before sending another action.",
    takeoverPinchZooming: "Pinch zooming local browser frame. Input is not sent to the controlled browser.",
    takeoverPollingPausedHidden: "Frame polling paused while this Control Client is hidden. Last frame is retained and stale input remains blocked.",
    takeoverVisibleRefreshing: "Control Client visible again; refreshing current browser frame.",
    controlledBrowserFrameAlt: "Controlled browser frame",
    browserHandoffPreviewTitle: "Browser ready to view",
    browserHandoffPreviewDetail: "Pause Agent to control the active browser, or open Takeover to inspect the live preview first.",
    browserHandoffActiveTitle: "You control the browser",
    browserHandoffActiveDetail: "Touch, scroll, and text input are routed to the controlled browser until you continue the Agent.",
    browserHandoffView: "View",
    browserHandoffPause: "Pause Agent",
    browserHandoffContinue: "Continue Agent",
    browserHandoffNoUrl: "Active browser",
    browserTakeoverCreated: "Browser takeover started",
    browserTakeoverCreatedDetail: "The active browser is now streaming to this Control Client.",
    paymentTitle: "Payment Approval",
    noPendingPayment: "No pending payment approval.",
    paymentReviewRequired: "Payment approval requires review",
    paymentReviewRequiredDetail: "Confirm the payment details before approving.",
    approve: "Approve",
    deny: "Deny",
    pauseAgent: "Pause Agent",
    pauseAgentRequested: "Pause requested",
    pauseAgentRequestDetail: "The request was queued for the active Linux console. When the TUI bridge is active, the current turn will pause before this instruction is handled.",
    takeoverPausePrompt: "Pause current browser automation now and hand the active browser to my Control Client. If a browser is running, create or keep a Human Takeover request, stream the page to me, and wait until I tap Continue Agent before resuming.",
    takeoverReleasePrompt: "I have finished controlling the browser. Continue from the current page state and resume the task.",
    takeoverReleased: "Browser control released",
    takeoverReleasedDetail: "Agent can continue from the browser state you left on screen.",
    releaseControl: "Continue Agent",
    openCurrentUrl: "Open current URL",
    externalHandoffNote: "Open the current URL in your browser, complete the site action yourself, then continue the Agent. No password, OTP, passkey, or recovery code is sent to the model.",
    browserStreamNote: "The browser is streamed to this Control Client. Agent paused. User in control. Sensitive input is not recorded.",
    registrationHandoffNote: "Registration Handoff: complete account creation directly. OmniDoer does not automate fake or bulk registration.",
    takeoverTextLabel: "Text to controlled browser",
    takeoverTextPlaceholder: "Only for the streamed browser",
    sendText: "Send Text",
    sendEnter: "Enter",
    challengeCode: "One-time code",
    anyPairedDevice: "any paired device",
    serverPinned: "server pinned",
    notVisible: "not visible",
    metadataLabels: {
      request_id: "Request ID",
      origin: "Origin",
      current_url: "Current URL",
      expires_at: "Expires",
      allowed_device: "Allowed device",
      broker_fingerprint: "Broker fingerprint"
    },
    statusLabels: {
      pending: "Pending",
      user_control: "User control",
      fulfilled: "Fulfilled",
      released: "Released",
      approved: "Approved",
      consumed: "Consumed",
      denied: "Denied",
      expired: "Expired",
      challenge_completed: "Challenge completed"
    },
    requestTypeLabels: {
      credential: "Credential",
      human_takeover: "Human takeover",
      account_registration: "Account registration",
      payment_approval: "Payment approval",
      console_restart: "Current session sync",
      two_factor_change: "Two-factor change",
      oauth_approval: "OAuth approval",
      one_time_code: "One-time code",
      totp: "TOTP",
      sms_code: "SMS code",
      email_code: "Email code",
      passkey: "Passkey",
      webauthn: "WebAuthn",
      device_confirmation: "Device confirmation"
    }
  },
  zh: {
    appTitle: "OmniDoer 控制客户端",
    appSubtitle: "安全处理授权、凭证、验证和人工接管。",
    navOverview: "总览",
    navRequests: "请求",
    navTasks: "对话",
    navDevices: "设备",
    navSecurity: "安全",
    navTakeover: "接管",
    takeoverTabLive: "实时",
    takeoverTabPreview: "可看",
    navPayments: "支付",
    navPair: "配对",
    checkingRuntime: "正在检查运行状态...",
    runtimeModeCloudDirect: (mode) => `控制服务：${mode}`,
    runtimeModeAttached: "当前 CLI 已同步",
    runtimeModeLegacyRelay: "已配对服务器；当前会话未原生同步",
    runtimeModeServerOnly: "已配对服务器；当前 CLI 尚未接入",
    runtimeModeUnpaired: "Control Service 可达",
    runtimeModeBackground: "后台 runner",
    runtimeModeOffline: "控制服务离线",
    runtimeDetail: "控制客户端不会直接调用 OpenAI API 或模型。",
    runtimeUnpairedDetail: "当前浏览器尚未配对。请在此设备上打开新的配对链接，并点击配对设备后再使用请求或会话同步。",
    runtimeOffline: "运行服务离线",
    runtimeOfflineDetail: "请启动 omnidoer control serve。",
    runtimeBridgeActive: "Linux 控制台实时桥接已启用；消息会同步到当前 TUI。",
    runtimeLegacyRelayActive: "配对只代表此浏览器已认证到服务器。临时终端 relay 可把消息粘贴到可见 console，但完整当前会话上下文同步需要重启：",
    runtimeLegacyRelayPause: "点击暂停会先向当前 console 发送 Ctrl-C，再投递你的指令。",
    runtimeNativeBridgeReady: "完整结构化桥接已经安装；重启后会切换到原生同步。",
    runtimeActiveConsoleNeedsBinaryRestart: "当前 console 仍在运行旧的 Codex 二进制。重启会保留这个 thread，并加载已安装的原生桥接。",
    runtimeNativeBridgeNotReady: "原生结构化桥接尚未安装；重启前请先更新 OmniDoer。",
    runtimeWaitingForConsoleRestart: "Linux 控制台仍在运行但尚未桥接。请用下面命令重启 OmniDoer console：",
    runtimeBackgroundRunner: "没有实时 Linux 控制台桥接；排队消息将由后台 Codex runner 处理。",
    chatSessionCheckingTitle: "正在检查当前 CLI 会话",
    chatSessionCheckingDetail: "配对只代表此浏览器已认证；要同步当前会话还需要实时 CLI 桥接。",
    chatSessionUnpairedTitle: "配对此浏览器",
    chatSessionUnpairedDetail: "当前浏览器尚未通过 Control Service 认证。请先完成配对，再使用对话、请求或会话同步。",
    chatSessionAttachedTitle: "已接入当前 CLI 会话",
    chatSessionAttachedDetail: "手机消息和流式输出会同步到活跃 Linux TUI。",
    chatSessionLegacyTitle: "已配对服务器；当前会话未同步",
    chatSessionLegacyDetail: "此浏览器只是认证到了服务器。启用当前会话同步前，消息只能临时通过 tmux 粘贴进可见 console，它还不是这段对话的原生客户端。",
    chatSessionServerOnlyTitle: "仅配对到服务器",
    chatSessionServerOnlyDetail: "此浏览器已认证，但当前 CLI 会话尚未接入。把它当作同一段对话使用前，请先重启桥接。",
    chatSessionBackgroundTitle: "后台 runner",
    chatSessionBackgroundDetail: "当前没有实时 CLI 桥接，消息会由后台 Codex runner 处理。",
    chatSessionOfflineTitle: "Control Service 离线",
    chatSessionOfflineDetail: "重新连接到 Control Service 后才能发送消息。",
    chatSyncDiagnosticNative: "诊断：原生双向同步已启用。",
    chatSyncDiagnosticLegacy: "诊断：服务器配对已生效，但完整上下文记忆和结构化流式输出尚未接入。",
    chatSyncDiagnosticStaleBinary: "诊断：这是当前 console，但正在运行的二进制缺少原生桥接。结构化双向同步必须重启后才能启用。",
    chatSyncDiagnosticWaiting: "诊断：已配对到这台服务器，但当前 CLI 对话尚未接入。",
    chatSyncDiagnosticBackground: "诊断：正在使用后台 runner，不是实时 CLI 对话。",
    overviewTitle: "控制中心",
    overviewIntro: "会话同步、待处理请求、浏览器接管和对话集中在一个适合触屏操作的工作区。",
    overviewNextActionTitle: "下一步",
    overviewSyncTitle: "会话同步",
    overviewRequestsTitle: "请求",
    overviewBrowserTitle: "浏览器",
    overviewChatTitle: "对话",
    overviewPairingTitle: "配对",
    overviewOpenRequests: (open, total) => `${open} 个待处理 / 共 ${total} 个`,
    overviewChatRecords: (messages, records) => `${messages} 条消息 · ${records} 条活动记录`,
    overviewPaired: "已配对",
    overviewUnpaired: "未配对",
    overviewSyncAttached: "原生同步已启用",
    overviewSyncNeedsRestart: "启用当前会话同步",
    overviewSyncServerOnly: "CLI 尚未接入",
    overviewSyncBackground: "后台 runner",
    overviewSyncOffline: "离线",
    overviewBrowserIdle: "没有实时浏览器交接。",
    overviewBrowserPreview: "可查看实时浏览器。",
    overviewBrowserActive: "你正在控制浏览器。",
    overviewNoUrgentAction: "暂无紧急操作",
    overviewNoUrgentDetail: "需要指挥 Agent 时，可进入对话或接管页。",
    overviewActionPairTitle: "配对此浏览器",
    overviewActionPairDetail: "配对此设备后才能使用请求和当前会话同步。",
    overviewActionSyncTitle: "批准当前会话同步",
    overviewActionSyncDetail: "重启活跃 Linux CLI，把手机接入同一个 thread。",
    overviewActionRequestTitle: (type) => `处理${type}`,
    overviewActionRequestDetail: (summary) => summary || "有一个请求需要你处理。",
    overviewActionBrowserTitle: "接管浏览器",
    overviewActionBrowserDetail: "实时浏览器可查看，也可暂停 Agent 后人工控制。",
    overviewActionChatTitle: "打开对话",
    overviewPrimaryAction: "打开",
    overviewSecondaryAction: "详情",
    sendToCurrentCli: "发送到当前 CLI",
    sendToCurrentConsole: "临时粘贴到 CLI",
    sendToBackgroundRunner: "发送到后台",
    sendUnavailable: "请先重启桥接",
    chatPlaceholderLegacy: "仅临时粘贴；启用当前会话同步后才共享上下文",
    chatPlaceholderUnavailable: "请先重启桥接，再发送到这段对话",
    chatSendBlocked: "对话尚未接入",
    chatDeliveredToConsole: "已临时粘贴到 Linux console",
    chatDeliveredToConsoleDetail: "临时终端 relay 已把这条消息粘贴进活跃 TUI；这还不是原生会话同步。",
    chatQueuedForBridge: "消息已进入 console 桥接队列",
    chatQueuedForBridgeDetail: "Control Service 已接收消息；bridge 就绪后会继续投递。",
    copyCommand: "复制命令",
    copiedCommand: "命令已复制",
    copyCommandFailed: "复制失败",
    restartBridge: "重启桥接",
    enableCurrentSessionSync: "启用当前会话同步",
    restartBridgeConfirm: "要在当前 tmux pane 中重启 Linux console 以启用完整手机同步吗？",
    restartBridgeConfirmDetailed: (threadId) => `要为线程 ${threadId || "当前线程"} 启用完整手机同步吗？这会在当前 tmux pane 中重启活跃 Codex TUI，保留同一个 thread，并加载已安装的原生桥接。`,
    restartBridgeStarted: "控制台桥接重启已开始",
    restartBridgeChecking: "正在等待原生桥接心跳...",
    restartBridgeActivated: "当前 CLI 会话同步已启用。",
    restartBridgeStillWaiting: "已请求重启，但当前 CLI 仍未发布原生桥接心跳。",
    restartBridgeFailed: "重启失败",
    restartBridgeApprovalRequested: "启用同步需要批准",
    restartBridgeApprovalRequestedDetail: "已创建高风险请求，并会保持可见 30 分钟。请在“请求”里审核并批准，以重启当前 CLI。",
    reviewSyncRequest: "查看同步请求",
    chatSyncApprovalPending: "当前会话同步批准请求正在等待处理。",
    syncApprovalTitle: "当前会话同步待批准",
    syncApprovalDetail: "批准后会在 tmux pane 中重启活跃 Linux CLI，并把此设备接入同一段对话。",
    syncApprovalThread: "线程",
    syncApprovalPid: "CLI PID",
    syncApprovalCommand: "命令",
    syncApprovalExpires: "过期时间",
    syncApprovalRenewing: "正在刷新同步请求...",
    syncApprovalRenewed: "同步请求已刷新",
    syncApprovalExpired: "同步批准请求已过期，请重新发起。",
    syncApprovalConfirmText: "我理解这会重启活跃 Codex TUI，并保留同一个 thread。",
    syncApprovalOpenRequest: "打开完整请求",
    syncApprovalApprove: "批准同步",
    consoleRestartReviewRequired: "当前会话同步需要确认",
    consoleRestartReviewRequiredDetail: "请先检查重启详情再批准。",
    consoleRestartConfirmText: "我理解这会在当前 tmux pane 中重启活跃 Codex TUI，并保留同一个 thread。",
    consoleRestartThread: "线程",
    consoleRestartCommand: "重启命令",
    consoleRestartCurrentState: "当前状态",
    consoleRestartCurrentPid: "当前 CLI PID",
    consoleRestartPane: "tmux pane",
    consoleRestartNativeSync: "原生同步已启用",
    consoleRestartAfterApproval: "批准后",
    legacyTerminalTitle: "实时 Linux 控制台",
    requestsCount: (open, total) => `请求：${open} 个待处理 / 共 ${total} 个`,
    attentionTitle: (count) => `${count} 个请求需要处理`,
    attentionDetail: (type, status) => `${type} · ${status}`,
    attentionAction: "查看处理",
    requestsTitle: "待处理请求",
    requestsIntro: "优先处理需要你操作的项目。敏感凭证只会加密提交到本地 broker。",
    requestFiltersLabel: "请求筛选",
    filterOpen: "待处理",
    filterAll: "全部",
    filterCredential: "凭证",
    filterChallenge: "验证",
    filterApproval: "授权",
    filterTakeover: "接管",
    loading: "加载中...",
    noOpenRequests: "没有待处理请求。",
    noMatchingOpenRequests: "当前筛选下没有待处理请求。",
    pairToViewRequests: "请先配对此设备以查看 Cloud Direct 请求。",
    pairToReceiveEvents: "请先配对此设备以接收签名请求事件。",
    waitingForUserAction: "等待用户操作",
    credentialClosed: (status) => `凭证请求状态：${status}。`,
    challengeClosed: (status) => `验证请求状态：${status}。`,
    takeoverClosed: (status) => `接管请求状态：${status}。`,
    secretNote: "敏感字段会在本地加密后提交，不会进入 Agent/LLM 上下文、MCP 返回值、日志或 DOM 观察结果。",
    username: "用户名",
    password: "密码",
    totpSeed: "TOTP 种子",
    saveInVault: "加密保存到 Vault",
    submitCredential: "提交凭证",
    challengeNote: "验证由你本人完成。OmniDoer 不绕过 CAPTCHA/MFA/Passkey/WebAuthn/3DS。",
    visualChallengeNote: "无需向 OmniDoer 提交验证答案。在受控浏览器或外部设备完成后标记完成即可。",
    submitChallenge: "提交验证码",
    markUserCompleted: "标记已完成",
    requestSubmitFailed: "请求提交失败",
    requestSubmitFailedDetail: "如果这是 Cloud Direct 模式，请重新配对。",
    actionFailed: "操作失败",
    pairTitle: "配对此设备",
    pairIntro: "将此浏览器连接到你自己的 Control Service。只配对你控制的设备。",
    pairSecurity: "配对后，凭证和验证内容会在本地加密后提交。",
    pairButton: "配对设备",
    forgetPairing: "清除本地配对",
    notPaired: "未配对。",
    controlOffline: "Control Service 离线。",
    localTrustedMode: "本地可信模式已启用，localhost 不需要配对。",
    localTrustedDevice: "本地可信模式",
    pairingCodeLoaded: "已载入配对码。确认服务端信息后配对此设备。",
    pairFreshLink: "当前浏览器未配对。配对按浏览器保存，因为设备密钥只留在本机；请在此设备上打开新的配对链接。",
    checkingCachedSession: "正在检查本地配对会话...",
    sessionHidden: "此浏览器已认证，但当前会话不在最新会话列表中。",
    sessionRevoked: "此浏览器缓存的会话已被撤销，请重新配对。",
    pairedCached: "已配对。除非会话被撤销或浏览器数据被清除，此浏览器会长期保持配对。",
    sessionValidUntil: (value) => `有效至 ${value}`,
    cachedPairingRejected: "当前浏览器有本地配对数据，但会话 Cookie 或签名被拒绝。请使用相同 HTTPS 地址、允许 Cookie，或重新配对。",
    pairingDevice: "正在配对此设备...",
    pairingFailed: "配对失败。",
    pairingFailedDetail: (reason) => `配对失败：${reason}`,
    pairingExpired: "配对码已过期。请在此设备上打开新的配对链接。",
    pairingAlreadyUsed: "配对码已达到 10 次使用上限。请生成新链接配对更多设备。",
    pairingInvalid: "配对码无效。请打开最新的配对链接。",
    pairedDevice: (name) => `已配对 ${name}。除非会话被撤销或浏览器数据被清除，此浏览器会长期保持配对。`,
    localPairingRemoved: "已清除本地配对。服务端设备和会话仍可在重新配对后撤销。",
    deviceTitle: "设备 / 会话",
    deviceIntro: "查看已配对的控制客户端和活跃会话。",
    refresh: "刷新",
    pairedDevices: "已配对设备",
    sessions: "会话",
    pairToViewDevices: "请先配对此设备以查看已配对设备。",
    pairToViewSessions: "请先配对此设备以查看会话。",
    noPairedDevices: "没有已配对设备。",
    noSessions: "没有会话。",
    securityTitle: "安全",
    taskTitle: "对话",
    taskIntro: "消息会通过已配对的 Control Service 流式同步。",
    chatComposerLabel: "消息",
    chatPlaceholder: "发送给 OmniDoer",
    chatFilesLabel: "添加附件",
    chatSelectedFiles: "已选文件",
    uploadFailed: "上传失败",
    sendMessage: "发送消息",
    noChatMessages: "还没有对话消息。",
    pairToViewChat: "请先配对此设备以查看和发送对话消息。",
    chatStatusQueued: "待处理",
    chatStatusClaimed: "已送达",
    chatStatusStreaming: "流式回复中",
    chatStatusCompleted: "已完成",
    chatRecordDelta: "增量",
    chatRecordStatus: "状态",
    chatRecordToolCall: "工具调用",
    chatRecordToolOutput: "工具输出",
    chatToolCalling: (name) => `正在调用 ${name}`,
    chatToolReturned: (name) => `${name} 返回`,
    chatToolShell: "shell",
    chatToolWebSearch: "网页搜索",
    chatToolUnknown: "工具",
    chatToolOutputNoContent: "无可见输出",
    chatToolOutputLines: (count) => `${count} 行`,
    chatRecordReasoning: "思考摘要",
    chatRecordTerminal: "终端",
    chatRecordTerminalInput: "终端输入",
    chatRecordTerminalSnapshot: "快照",
    chatRecordTerminalDelta: "增量",
    chatRecordChunks: (count) => `${count} 段`,
    chatConversationTitle: "对话",
    chatActivityTitle: "实时活动",
    chatUserRole: "你",
    chatAssistantRole: "OmniDoer",
    chatRecordNumber: (sequence) => `记录 #${sequence}`,
    submitTask: "提交任务",
    noQueuedTasks: "没有排队任务。",
    pairToViewTasks: "请先配对此设备以查看 Cloud Direct 任务队列。",
    takeoverTitle: "人工接管",
    takeoverNoActive: "没有活跃接管",
    noActiveBrowserHandoff: "没有活跃浏览器接管。",
    activeBrowserReady: "检测到活跃浏览器。点击暂停 Agent 即可接管此浏览器。",
    activeBrowserPreview: "浏览器实时预览。点击暂停 Agent 即可接管。",
    activeBrowserPreviewWaiting: "正在等待浏览器实时预览。",
    takeoverFrameWaiting: "等待浏览器交接",
    takeoverFrameWaitingControlled: "正在等待受控浏览器画面...",
    takeoverFrameNextWaiting: "等待下一帧浏览器画面",
    takeoverFrameFresh: (seconds) => `新鲜 ${seconds}s`,
    takeoverFrameStale: (seconds) => `已过期 ${seconds}s - 输入前请刷新`,
    takeoverFrameAdaptive: "自适应",
    takeoverConnected: "已连接",
    takeoverConnectedWebSocket: "已连接 - WebSocket",
    takeoverConnecting: "正在连接",
    takeoverPausedHidden: "已暂停 - 页面在后台",
    takeoverResuming: "正在恢复",
    takeoverPanOn: "平移开",
    takeoverPanView: "平移视图",
    takeoverPanSuffix: " 平移",
    refreshFrame: "刷新画面",
    zoomOut: "缩小",
    zoomReset: "重置",
    zoomIn: "放大",
    takeoverAgentPausedStatus: "Agent 已暂停 - 用户正在接管",
    takeoverFrameReady: "实时浏览器画面已就绪。输入会发送到当前可见的这一帧。",
    takeoverFrameReadyWebSocket: "WebSocket 实时浏览器画面已就绪。输入会发送到当前可见的这一帧。",
    takeoverDisconnected: "此进程中未连接浏览器上下文。",
    takeoverWebSocketDisconnected: "实时画面 WebSocket 已断开。",
    takeoverFrameFetchFailed: "获取浏览器画面失败。",
    takeoverReconnectRetry: (attempt) => `正在重连 - 第 ${attempt} 次`,
    takeoverKeepingLastFrameShort: "保留最后一帧",
    takeoverKeepingLastFrame: (message) => `${message} 保留最后一帧可见；过期画面仍会阻止输入。`,
    takeoverInactive: "接管未激活。释放后 Agent 可以恢复控制。",
    takeoverLoadingFrame: "正在加载仅控制用浏览器画面...",
    takeoverInputStateActive: "触摸、键盘和文本输入只会发送到受控浏览器。",
    takeoverInputHidden: "Control Client 在后台或画面轮询已暂停时不会发送输入。请切回前台并刷新画面后再输入。",
    takeoverInputNoFrame: "请等待当前浏览器画面后再发送输入。",
    takeoverInputRefreshingStale: "画面已过期；输入前正在刷新。",
    takeoverInputDelivered: (eventType) => `${eventType} 已发送到受控浏览器。`,
    takeoverInputQueued: (eventType) => `${eventType} 已进入浏览器 relay 队列。`,
    takeoverInputFrameChanged: "输入发送前画面已变化。正在刷新当前浏览器画面。",
    takeoverInputDeliveryFailed: "输入未送达。浏览器上下文可能已断开。",
    takeoverInputStillPending: "输入仍在等待浏览器确认。发送下一次操作前请先刷新画面。",
    takeoverPinchZooming: "正在本地双指缩放浏览器画面。此操作不会发送到受控浏览器。",
    takeoverPollingPausedHidden: "Control Client 在后台，画面轮询已暂停。最后一帧会保留，过期输入仍会被阻止。",
    takeoverVisibleRefreshing: "Control Client 已回到前台；正在刷新当前浏览器画面。",
    controlledBrowserFrameAlt: "受控浏览器画面",
    browserHandoffPreviewTitle: "浏览器可查看",
    browserHandoffPreviewDetail: "可以先打开接管页查看实时预览，也可以暂停 Agent 后接管活跃浏览器。",
    browserHandoffActiveTitle: "你正在控制浏览器",
    browserHandoffActiveDetail: "触摸、滚动和文本输入会发送到受控浏览器，直到你点击继续交给 Agent。",
    browserHandoffView: "查看",
    browserHandoffPause: "暂停 Agent",
    browserHandoffContinue: "继续交给 Agent",
    browserHandoffNoUrl: "活跃浏览器",
    browserTakeoverCreated: "浏览器接管已开始",
    browserTakeoverCreatedDetail: "活跃浏览器画面正在流式发送到此 Control Client。",
    paymentTitle: "支付授权",
    noPendingPayment: "没有待处理支付授权。",
    paymentReviewRequired: "支付授权需要确认",
    paymentReviewRequiredDetail: "请先确认支付详情再批准。",
    approve: "批准",
    deny: "拒绝",
    pauseAgent: "暂停 Agent",
    pauseAgentRequested: "已请求暂停",
    pauseAgentRequestDetail: "请求已排队给当前 Linux 控制台。TUI 桥接启用后，当前回合会先暂停再处理这条指令。",
    takeoverPausePrompt: "请立即暂停当前浏览器自动化，并把活跃浏览器交给我的 Control Client。如果正在操作浏览器，请创建或保持一个 Human Takeover 请求，把页面画面流式发送给我，并等待我点击继续交给 Agent 后再恢复。",
    takeoverReleasePrompt: "我已经完成浏览器接管操作。请从当前页面状态继续执行任务。",
    takeoverReleased: "已释放浏览器控制",
    takeoverReleasedDetail: "Agent 可以从你留在屏幕上的浏览器状态继续。",
    releaseControl: "继续交给 Agent",
    openCurrentUrl: "打开当前链接",
    externalHandoffNote: "在浏览器中打开当前链接，由你本人完成网站操作，然后继续交给 Agent。密码、OTP、passkey 或 recovery code 都不会发送给模型。",
    browserStreamNote: "浏览器画面会流式传到此控制客户端。Agent 已暂停，由用户接管。敏感输入不会被记录。",
    registrationHandoffNote: "注册接管：请你直接完成账号创建。OmniDoer 不会自动化虚假或批量注册。",
    takeoverTextLabel: "发送到受控浏览器的文本",
    takeoverTextPlaceholder: "仅用于已流式接管的浏览器",
    sendText: "发送文本",
    sendEnter: "回车",
    challengeCode: "一次性验证码",
    anyPairedDevice: "任意已配对设备",
    serverPinned: "服务端固定",
    notVisible: "不可见",
    metadataLabels: {
      request_id: "请求 ID",
      origin: "来源",
      current_url: "当前链接",
      expires_at: "过期时间",
      allowed_device: "允许设备",
      broker_fingerprint: "Broker 指纹"
    },
    statusLabels: {
      pending: "待处理",
      user_control: "用户接管中",
      fulfilled: "已提交",
      released: "已释放",
      approved: "已批准",
      consumed: "已执行",
      denied: "已拒绝",
      expired: "已过期",
      challenge_completed: "验证已完成"
    },
    requestTypeLabels: {
      credential: "凭证",
      human_takeover: "人工接管",
      account_registration: "账号注册",
      payment_approval: "支付授权",
      console_restart: "当前会话同步",
      two_factor_change: "双重认证变更",
      oauth_approval: "OAuth 授权",
      one_time_code: "一次性验证码",
      totp: "TOTP",
      sms_code: "短信验证码",
      email_code: "邮箱验证码",
      passkey: "Passkey",
      webauthn: "WebAuthn",
      device_confirmation: "设备确认"
    }
  }
};

const EXTRA_I18N = {
  es: {
    appSubtitle: "Aprobaciones, credenciales, verificaciones y toma de control seguras.",
    navOverview: "Inicio", navRequests: "Solicitudes", navTasks: "Chat", navDevices: "Dispositivos", navSecurity: "Seguridad", navTakeover: "Control", navPayments: "Pagos",
    overviewTitle: "Centro de control", overviewNextActionTitle: "Siguiente accion", overviewSyncTitle: "Sesión", overviewRequestsTitle: "Solicitudes", overviewBrowserTitle: "Navegador", overviewChatTitle: "Chat", overviewPairingTitle: "Emparejamiento",
    attentionTitle: (count) => `${count} solicitudes requieren atencion`, attentionDetail: (type, status) => `${type} · ${status}`, attentionAction: "Revisar",
    requestsTitle: "Solicitudes pendientes", filterOpen: "Pendientes", filterAll: "Todas", filterCredential: "Secretos", filterChallenge: "Verificaciones", filterApproval: "Aprobaciones", filterTakeover: "Control",
    chatFilesLabel: "Adjuntar", chatSelectedFiles: "Archivos seleccionados", uploadFailed: "Carga fallida",
    chatConversationTitle: "Conversacion", chatActivityTitle: "Actividad en vivo", chatUserRole: "Tu", chatAssistantRole: "OmniDoer", chatRecordNumber: (sequence) => `registro #${sequence}`,
    copyCommand: "Copiar comando", copiedCommand: "Comando copiado", copyCommandFailed: "Error al copiar",
    syncApprovalTitle: "Sincronizacion pendiente", syncApprovalDetail: "Aprobar reinicia la CLI Linux activa y conecta este dispositivo a la misma conversacion.", syncApprovalThread: "Hilo", syncApprovalPid: "PID CLI", syncApprovalCommand: "Comando", syncApprovalExpires: "Caduca", syncApprovalRenewing: "Actualizando solicitud de sync...", syncApprovalRenewed: "Solicitud de sync actualizada", syncApprovalExpired: "La aprobacion de sync caduco; solicita una nueva.", syncApprovalConfirmText: "Entiendo que esto reinicia la TUI Codex activa y conserva el mismo hilo.", syncApprovalOpenRequest: "Abrir solicitud", syncApprovalApprove: "Aprobar sync",
    pauseAgent: "Pausar Agent", pauseAgentRequested: "Pausa solicitada", pauseAgentRequestDetail: "La solicitud quedo en cola para la consola Linux activa.", takeoverInputStillPending: "La entrada sigue esperando respuesta del navegador. Actualiza el marco antes de enviar otra accion.", takeoverPausePrompt: "Pausa ahora la automatizacion del navegador y entrega el navegador activo a mi Control Client. Si hay un navegador activo, crea o conserva una solicitud Human Takeover, transmite la pagina y espera hasta que toque Continue Agent antes de reanudar.", releaseControl: "Continuar Agent", openCurrentUrl: "Abrir URL actual", externalHandoffNote: "Abre la URL actual, completa la accion en el sitio y continua el Agent. Secretos y codigos no se envian al modelo.",
    submitCredential: "Enviar credencial", submitChallenge: "Enviar codigo", approve: "Aprobar", deny: "Denegar", challengeCode: "Codigo de un solo uso"
  },
  fr: {
    appSubtitle: "Approbations, identifiants, validations et prise de controle securises.",
    navOverview: "Accueil", navRequests: "Demandes", navTasks: "Chat", navDevices: "Appareils", navSecurity: "Securite", navTakeover: "Controle", navPayments: "Paiements",
    overviewTitle: "Centre de controle", overviewNextActionTitle: "Prochaine action", overviewSyncTitle: "Session", overviewRequestsTitle: "Demandes", overviewBrowserTitle: "Navigateur", overviewChatTitle: "Chat", overviewPairingTitle: "Appairage",
    attentionTitle: (count) => `${count} demandes a traiter`, attentionDetail: (type, status) => `${type} · ${status}`, attentionAction: "Examiner",
    requestsTitle: "Demandes en attente", filterOpen: "En attente", filterAll: "Toutes", filterCredential: "Secrets", filterChallenge: "Verifications", filterApproval: "Approbations", filterTakeover: "Controle",
    chatFilesLabel: "Joindre", chatSelectedFiles: "Fichiers selectionnes", uploadFailed: "Echec d'envoi",
    chatConversationTitle: "Conversation", chatActivityTitle: "Activite en direct", chatUserRole: "Vous", chatAssistantRole: "OmniDoer", chatRecordNumber: (sequence) => `journal #${sequence}`,
    copyCommand: "Copier la commande", copiedCommand: "Commande copiee", copyCommandFailed: "Copie impossible",
    syncApprovalTitle: "Synchronisation en attente", syncApprovalDetail: "Approuver redemarre la CLI Linux active et connecte cet appareil a la meme conversation.", syncApprovalThread: "Fil", syncApprovalPid: "PID CLI", syncApprovalCommand: "Commande", syncApprovalExpires: "Expire", syncApprovalRenewing: "Actualisation de la demande sync...", syncApprovalRenewed: "Demande sync actualisee", syncApprovalExpired: "L'approbation sync a expire; demandez-en une nouvelle.", syncApprovalConfirmText: "Je comprends que cela redemarre la TUI Codex active et garde le meme fil.", syncApprovalOpenRequest: "Ouvrir la demande", syncApprovalApprove: "Approuver sync",
    pauseAgent: "Mettre Agent en pause", pauseAgentRequested: "Pause demandee", pauseAgentRequestDetail: "La demande est en file pour la console Linux active.", takeoverInputStillPending: "L'entree attend encore l'accuse du navigateur. Actualisez l'image avant une autre action.", takeoverPausePrompt: "Mettez maintenant l'automatisation du navigateur en pause et remettez le navigateur actif a mon Control Client. Si un navigateur est actif, creez ou gardez une demande Human Takeover, diffusez la page, puis attendez que je touche Continue Agent avant de reprendre.", releaseControl: "Continuer Agent", openCurrentUrl: "Ouvrir l'URL", externalHandoffNote: "Ouvrez l'URL, terminez l'action sur le site, puis continuez l'Agent. Les secrets et codes ne sont pas envoyes au modele.",
    submitCredential: "Envoyer l'identifiant", submitChallenge: "Envoyer le code", approve: "Approuver", deny: "Refuser", challengeCode: "Code a usage unique"
  },
  de: {
    appSubtitle: "Sichere Freigaben, Zugangsdaten, Pruefungen und manuelle Uebernahme.",
    navOverview: "Start", navRequests: "Anfragen", navTasks: "Chat", navDevices: "Geraete", navSecurity: "Sicherheit", navTakeover: "Uebernahme", navPayments: "Zahlungen",
    overviewTitle: "Kontrollzentrum", overviewNextActionTitle: "Naechste Aktion", overviewSyncTitle: "Sitzung", overviewRequestsTitle: "Anfragen", overviewBrowserTitle: "Browser", overviewChatTitle: "Chat", overviewPairingTitle: "Kopplung",
    attentionTitle: (count) => `${count} offene Anfragen`, attentionDetail: (type, status) => `${type} · ${status}`, attentionAction: "Pruefen",
    requestsTitle: "Offene Anfragen", filterOpen: "Offen", filterAll: "Alle", filterCredential: "Secrets", filterChallenge: "Pruefungen", filterApproval: "Freigaben", filterTakeover: "Uebernahme",
    chatFilesLabel: "Anhaengen", chatSelectedFiles: "Ausgewaehlte Dateien", uploadFailed: "Upload fehlgeschlagen",
    chatConversationTitle: "Unterhaltung", chatActivityTitle: "Live-Aktivitaet", chatUserRole: "Du", chatAssistantRole: "OmniDoer", chatRecordNumber: (sequence) => `Eintrag #${sequence}`,
    copyCommand: "Befehl kopieren", copiedCommand: "Befehl kopiert", copyCommandFailed: "Kopieren fehlgeschlagen",
    syncApprovalTitle: "Synchronisierung wartet", syncApprovalDetail: "Genehmigen startet die aktive Linux-CLI neu und verbindet dieses Geraet mit derselben Unterhaltung.", syncApprovalThread: "Thread", syncApprovalPid: "CLI PID", syncApprovalCommand: "Befehl", syncApprovalExpires: "Laeuft ab", syncApprovalRenewing: "Sync-Anfrage wird aktualisiert...", syncApprovalRenewed: "Sync-Anfrage aktualisiert", syncApprovalExpired: "Sync-Freigabe ist abgelaufen; bitte neu anfordern.", syncApprovalConfirmText: "Ich verstehe, dass dies die aktive Codex-TUI neu startet und denselben Thread behaelt.", syncApprovalOpenRequest: "Anfrage oeffnen", syncApprovalApprove: "Sync genehmigen",
    pauseAgent: "Agent pausieren", pauseAgentRequested: "Pause angefordert", pauseAgentRequestDetail: "Die Anfrage wurde fuer die aktive Linux-Konsole eingereiht.", takeoverInputStillPending: "Die Eingabe wartet noch auf die Browser-Bestaetigung. Aktualisiere den Frame vor der naechsten Aktion.", takeoverPausePrompt: "Pausiere jetzt die Browser-Automation und uebergib den aktiven Browser an meinen Control Client. Falls ein Browser aktiv ist, erstelle oder behalte eine Human-Takeover-Anfrage, streame die Seite und warte, bis ich Continue Agent antippe.", releaseControl: "Agent fortsetzen", openCurrentUrl: "Aktuelle URL oeffnen", externalHandoffNote: "Oeffnen Sie die aktuelle URL, erledigen Sie die Aktion selbst und setzen Sie danach den Agent fort. Secrets und Codes werden nicht an das Modell gesendet.",
    submitCredential: "Zugangsdaten senden", submitChallenge: "Code senden", approve: "Genehmigen", deny: "Ablehnen", challengeCode: "Einmalcode"
  },
  ja: {
    appSubtitle: "承認、認証情報、検証、人間による操作を安全に扱います。",
    navOverview: "ホーム", navRequests: "リクエスト", navTasks: "チャット", navDevices: "デバイス", navSecurity: "セキュリティ", navTakeover: "操作", navPayments: "支払い",
    overviewTitle: "コントロールセンター", overviewNextActionTitle: "次の操作", overviewSyncTitle: "セッション", overviewRequestsTitle: "リクエスト", overviewBrowserTitle: "ブラウザ", overviewChatTitle: "チャット", overviewPairingTitle: "ペアリング",
    attentionTitle: (count) => `${count}件の対応が必要`, attentionDetail: (type, status) => `${type} · ${status}`, attentionAction: "確認",
    requestsTitle: "未処理リクエスト", filterOpen: "未処理", filterAll: "すべて", filterCredential: "シークレット", filterChallenge: "検証", filterApproval: "承認", filterTakeover: "操作",
    chatFilesLabel: "添付", chatSelectedFiles: "選択したファイル", uploadFailed: "アップロード失敗",
    chatConversationTitle: "会話", chatActivityTitle: "ライブ活動", chatUserRole: "あなた", chatAssistantRole: "OmniDoer", chatRecordNumber: (sequence) => `記録 #${sequence}`,
    copyCommand: "コマンドをコピー", copiedCommand: "コピーしました", copyCommandFailed: "コピー失敗",
    syncApprovalTitle: "同期の承認待ち", syncApprovalDetail: "承認するとアクティブなLinux CLIを再起動し、この端末を同じ会話に接続します。", syncApprovalThread: "スレッド", syncApprovalPid: "CLI PID", syncApprovalCommand: "コマンド", syncApprovalExpires: "期限", syncApprovalRenewing: "同期リクエストを更新中...", syncApprovalRenewed: "同期リクエストを更新しました", syncApprovalExpired: "同期承認の期限が切れました。再度リクエストしてください。", syncApprovalConfirmText: "アクティブなCodex TUIを再起動し同じスレッドを保持することを理解しました。", syncApprovalOpenRequest: "リクエストを開く", syncApprovalApprove: "同期を承認",
    pauseAgent: "Agentを一時停止", pauseAgentRequested: "一時停止を依頼しました", pauseAgentRequestDetail: "依頼はアクティブなLinuxコンソールにキューされました。", takeoverInputStillPending: "入力はまだブラウザ確認待ちです。次の操作前にフレームを更新してください。", takeoverPausePrompt: "現在のブラウザ自動操作を一時停止し、アクティブなブラウザをControl Clientへ渡してください。ブラウザが動作中ならHuman Takeoverリクエストを作成または維持し、画面をストリーミングして、Continue Agentをタップするまで待機してください。", releaseControl: "Agentを続行", openCurrentUrl: "現在のURLを開く", externalHandoffNote: "現在のURLを開き、サイト上の操作を自分で完了してからAgentを続行してください。パスワードやコードはモデルに送信されません。",
    submitCredential: "認証情報を送信", submitChallenge: "コードを送信", approve: "承認", deny: "拒否", challengeCode: "ワンタイムコード"
  },
  ko: {
    appSubtitle: "승인, 자격 증명, 인증, 사용자 제어를 안전하게 처리합니다.",
    navOverview: "홈", navRequests: "요청", navTasks: "채팅", navDevices: "기기", navSecurity: "보안", navTakeover: "제어", navPayments: "결제",
    overviewTitle: "제어 센터", overviewNextActionTitle: "다음 작업", overviewSyncTitle: "세션", overviewRequestsTitle: "요청", overviewBrowserTitle: "브라우저", overviewChatTitle: "채팅", overviewPairingTitle: "페어링",
    attentionTitle: (count) => `${count}개 요청 처리 필요`, attentionDetail: (type, status) => `${type} · ${status}`, attentionAction: "검토",
    requestsTitle: "대기 중인 요청", filterOpen: "대기", filterAll: "전체", filterCredential: "비밀", filterChallenge: "인증", filterApproval: "승인", filterTakeover: "제어",
    chatFilesLabel: "첨부", chatSelectedFiles: "선택한 파일", uploadFailed: "업로드 실패",
    chatConversationTitle: "대화", chatActivityTitle: "실시간 활동", chatUserRole: "나", chatAssistantRole: "OmniDoer", chatRecordNumber: (sequence) => `기록 #${sequence}`,
    copyCommand: "명령 복사", copiedCommand: "명령 복사됨", copyCommandFailed: "복사 실패",
    syncApprovalTitle: "동기화 승인 대기", syncApprovalDetail: "승인하면 활성 Linux CLI를 다시 시작하고 이 기기를 같은 대화에 연결합니다.", syncApprovalThread: "스레드", syncApprovalPid: "CLI PID", syncApprovalCommand: "명령", syncApprovalExpires: "만료", syncApprovalRenewing: "동기화 요청 새로 고침 중...", syncApprovalRenewed: "동기화 요청 새로 고침됨", syncApprovalExpired: "동기화 승인이 만료되었습니다. 새로 요청하세요.", syncApprovalConfirmText: "활성 Codex TUI를 다시 시작하고 같은 스레드를 유지함을 이해합니다.", syncApprovalOpenRequest: "요청 열기", syncApprovalApprove: "동기화 승인",
    pauseAgent: "Agent 일시 중지", pauseAgentRequested: "일시 중지 요청됨", pauseAgentRequestDetail: "요청이 활성 Linux 콘솔에 대기열로 전달되었습니다.", takeoverInputStillPending: "입력이 아직 브라우저 확인을 기다립니다. 다음 작업 전에 프레임을 새로 고치세요.", takeoverPausePrompt: "현재 브라우저 자동화를 즉시 일시 중지하고 활성 브라우저를 내 Control Client로 넘겨주세요. 브라우저가 실행 중이면 Human Takeover 요청을 만들거나 유지하고, 페이지를 스트리밍한 뒤 내가 Continue Agent를 탭할 때까지 기다려주세요.", releaseControl: "Agent 계속", openCurrentUrl: "현재 URL 열기", externalHandoffNote: "현재 URL을 열고 사이트 작업을 직접 완료한 뒤 Agent를 계속하세요. 비밀번호와 코드는 모델로 전송되지 않습니다.",
    submitCredential: "자격 증명 제출", submitChallenge: "코드 제출", approve: "승인", deny: "거부", challengeCode: "일회용 코드"
  }
};

Object.entries(EXTRA_I18N).forEach(([lang, dict]) => {
  I18N[lang] = { ...I18N.en, ...dict };
});

const LANGUAGE_OPTIONS = [
  ["en", "English"],
  ["zh", "中文"],
  ["es", "Español"],
  ["fr", "Français"],
  ["de", "Deutsch"],
  ["ja", "日本語"],
  ["ko", "한국어"]
];

function initialLanguage() {
  const stored = localStorage.getItem("omnidoer_language");
  if (stored && I18N[stored]) return stored;
  const browserLanguage = navigator.language?.toLowerCase().split("-")[0];
  return I18N[browserLanguage] ? browserLanguage : "en";
}

let currentLanguage = initialLanguage();
const PANEL_IDS = [
  "overview-panel",
  "task-panel",
  "requests-panel",
  "takeover-panel",
  "device-panel",
  "security",
  "payment-approval",
  "pairing-panel"
];
const DEFAULT_PANEL_ID = "overview-panel";
const SYNC_REQUEST_RENEW_WINDOW_MS = 2 * 60 * 1000;
const PAIRING_STEP_TIMEOUT_MS = 15000;

function t(key, ...args) {
  const value = I18N[currentLanguage]?.[key] ?? I18N.en[key] ?? key;
  return typeof value === "function" ? value(...args) : value;
}

function setNodeText(selector, key, ...args) {
  const node = document.querySelector(selector);
  if (node) node.textContent = t(key, ...args);
}

function setButtonText(selector, key) {
  const node = document.querySelector(selector);
  if (node) node.textContent = t(key);
}

function setIconControlLabel(selector, key) {
  const node = document.querySelector(selector);
  if (!node) return;
  const label = t(key);
  node.setAttribute("aria-label", label);
  node.setAttribute("title", label);
}

function languageTag(lang) {
  return { zh: "zh-CN", ja: "ja", ko: "ko", es: "es", fr: "fr", de: "de" }[lang] || "en";
}

function applyLanguage() {
  document.documentElement.lang = languageTag(currentLanguage);
  setNodeText(".app-header h1", "appTitle");
  setNodeText(".app-header p", "appSubtitle");
  setNodeText("#attention-title", "attentionTitle", cachedRequests.filter(isOpenRequest).length);
  setButtonText("#attention-review", "attentionAction");
  const languageSelect = document.querySelector("#language-select");
  if (languageSelect) languageSelect.value = currentLanguage;
  setNodeText('a[href="#overview-panel"]', "navOverview");
  setNodeText('a[href="#requests-panel"]', "navRequests");
  setNodeText('a[href="#task-panel"]', "navTasks");
  setNodeText('a[href="#device-panel"]', "navDevices");
  setNodeText('a[href="#security"]', "navSecurity");
  setNodeText('a[href="#takeover-panel"]', "navTakeover");
  setNodeText('a[href="#payment-approval"]', "navPayments");
  setNodeText('a[href="#pairing-panel"]', "navPair");
  setNodeText("#requests-panel h2", "requestsTitle");
  setNodeText("#requests-panel .panel-heading p", "requestsIntro");
  setNodeText("#overview-title", "overviewTitle");
  setNodeText("#overview-intro", "overviewIntro");
  setNodeText("#overview-next-label", "overviewNextActionTitle");
  setNodeText("#overview-sync-title", "overviewSyncTitle");
  setNodeText("#overview-requests-title", "overviewRequestsTitle");
  setNodeText("#overview-browser-title", "overviewBrowserTitle");
  setNodeText("#overview-chat-title", "overviewChatTitle");
  setNodeText("#overview-pairing-title", "overviewPairingTitle");
  setNodeText("#overview-sync-thread-label", "syncApprovalThread");
  setNodeText("#overview-sync-pid-label", "syncApprovalPid");
  setNodeText("#overview-sync-expires-label", "syncApprovalExpires");
  setNodeText("#overview-sync-confirm-text", "syncApprovalConfirmText");
  document.querySelector(".filter-row")?.setAttribute("aria-label", t("requestFiltersLabel"));
  setButtonText('[data-filter="open"]', "filterOpen");
  setButtonText('[data-filter="all"]', "filterAll");
  setButtonText('[data-filter="credential"]', "filterCredential");
  setButtonText('[data-filter="challenge"]', "filterChallenge");
  setButtonText('[data-filter="approval"]', "filterApproval");
  setButtonText('[data-filter="takeover"]', "filterTakeover");
  setNodeText("#pairing-panel h2", "pairTitle");
  setNodeText("#pairing-panel > p:nth-of-type(1)", "pairIntro");
  setNodeText("#pairing-panel > p:nth-of-type(2)", "pairSecurity");
  setButtonText("#pair-device", "pairButton");
  setButtonText("#forget-local-pairing", "forgetPairing");
  setNodeText("#device-panel h2", "deviceTitle");
  setNodeText("#device-panel .panel-heading p", "deviceIntro");
  setButtonText("#refresh-devices", "refresh");
  setNodeText("#device-panel h3:nth-of-type(1)", "pairedDevices");
  setNodeText("#security h2", "securityTitle");
  setNodeText("#task-panel h2", "taskTitle");
  setNodeText("#task-panel .chat-panel-header p", "taskIntro");
  setNodeText("#chat-session-title", "chatSessionCheckingTitle");
  setNodeText("#chat-session-detail", "chatSessionCheckingDetail");
  setButtonText("#chat-session-restart", "restartBridge");
  setNodeText("#chat-sync-approval-title", "syncApprovalTitle");
  setNodeText("#chat-sync-approval-detail", "syncApprovalDetail");
  setNodeText("#chat-sync-approval-thread-label", "syncApprovalThread");
  setNodeText("#chat-sync-approval-pid-label", "syncApprovalPid");
  setNodeText("#chat-sync-approval-command-label", "syncApprovalCommand");
  setNodeText("#chat-sync-approval-expires-label", "syncApprovalExpires");
  setNodeText("#chat-sync-approval-confirm-text", "syncApprovalConfirmText");
  setButtonText("#chat-sync-approval-view", "syncApprovalOpenRequest");
  setButtonText("#chat-sync-approval-deny", "deny");
  setButtonText("#chat-sync-approval-approve", "syncApprovalApprove");
  setNodeText("#chat-input-label-text", "chatComposerLabel");
  const chatInput = document.querySelector("#chat-input");
  if (chatInput) chatInput.placeholder = t("chatPlaceholder");
  setIconControlLabel("#chat-files-label", "chatFilesLabel");
  setIconControlLabel("#send-chat-message", "sendMessage");
  setButtonText("#submit-task", "submitTask");
  setNodeText("#takeover-panel h2", "takeoverTitle");
  setNodeText("#payment-approval h2", "paymentTitle");
  setNodeText("#approval-status", "noPendingPayment");
  setButtonText("#runtime-copy-command", "copyCommand");
  setButtonText("#request-takeover-pause", "pauseAgent");
  setButtonText("#release-active-takeover", "releaseControl");
  setButtonText("#refresh-takeover-frame", "refreshFrame");
  setButtonText("#zoom-reset-takeover-frame", "zoomReset");
  setNodeText("#active-takeover-text-label", "takeoverTextLabel");
  const activeTakeoverText = document.querySelector("#active-takeover-text");
  if (activeTakeoverText) activeTakeoverText.placeholder = t("takeoverTextPlaceholder");
  setButtonText("#send-active-takeover-text", "sendText");
  setButtonText("#send-active-takeover-enter", "sendEnter");
  const zoomOut = document.querySelector("#zoom-out-takeover-frame");
  if (zoomOut) {
    zoomOut.title = t("zoomOut");
    zoomOut.setAttribute("aria-label", t("zoomOut"));
  }
  const zoomIn = document.querySelector("#zoom-in-takeover-frame");
  if (zoomIn) {
    zoomIn.title = t("zoomIn");
    zoomIn.setAttribute("aria-label", t("zoomIn"));
  }
  updateTakeoverZoomControls();
  setButtonText("#browser-handoff-view", "browserHandoffView");
  setButtonText("#browser-handoff-pause", "browserHandoffPause");
  setButtonText("#browser-handoff-continue", "browserHandoffContinue");
  setButtonText("#approve", "approve");
  setButtonText("#deny", "deny");
  updateAgentControlButtons();
  updateChatSessionStatus(cachedRuntimeStatus?.chat_runner || null);
  updateBrowserHandoffState(findActiveTakeoverRequest(cachedRequests), activeBrowserContext());
  updateOverview();
}

function initialPanelId() {
  const fromHash = window.location.hash.replace(/^#/, "");
  if (PANEL_IDS.includes(fromHash)) return fromHash;
  const stored = localStorage.getItem("omnidoer_active_panel");
  return PANEL_IDS.includes(stored) ? stored : DEFAULT_PANEL_ID;
}

function activatePanel(panelId, { persist = true, updateHash = true } = {}) {
  const activeId = PANEL_IDS.includes(panelId) ? panelId : DEFAULT_PANEL_ID;
  PANEL_IDS.forEach((id) => {
    const panel = document.getElementById(id);
    if (!panel) return;
    panel.classList.add("control-panel");
    const active = id === activeId;
    panel.hidden = !active;
    panel.setAttribute("aria-hidden", active ? "false" : "true");
  });
  document.querySelectorAll(".section-tabs a").forEach((link) => {
    const selected = link.getAttribute("href") === `#${activeId}`;
    link.classList.toggle("active", selected);
    link.setAttribute("aria-selected", selected ? "true" : "false");
    link.setAttribute("role", "tab");
  });
  document.body.dataset.activePanel = activeId;
  if (persist) localStorage.setItem("omnidoer_active_panel", activeId);
  if (updateHash && window.history?.replaceState) {
    window.history.replaceState({}, document.title, `#${activeId}`);
  }
}

function setupPanelNavigation() {
  document.querySelector(".section-tabs")?.setAttribute("role", "tablist");
  document.querySelectorAll(".section-tabs a").forEach((link) => {
    const targetId = link.getAttribute("href")?.replace(/^#/, "") || "";
    link.onclick = (event) => {
      if (!PANEL_IDS.includes(targetId)) return;
      event.preventDefault();
      activatePanel(targetId);
    };
  });
  window.addEventListener("hashchange", () => activatePanel(initialPanelId(), { persist: true, updateHash: false }));
  activatePanel(initialPanelId(), { persist: false, updateHash: false });
}

function updateRequestsTabBadge(openCount, totalCount) {
  const link = document.querySelector('a[href="#requests-panel"]');
  if (!link) return;
  link.dataset.count = String(openCount);
  link.dataset.total = String(totalCount);
  link.classList.toggle("has-open-requests", openCount > 0);
}

function requestAttentionRank(request) {
  if (request.request_type === "console_restart") return 0;
  if (request.request_type === "credential") return 1;
  if (request.request_type === "human_takeover" || request.request_type === "account_registration") return 2;
  if (requestKind(request) === "approval") return 3;
  return 4;
}

function primaryOpenRequest(openRequests) {
  return [...openRequests].sort((left, right) => {
    const rank = requestAttentionRank(left) - requestAttentionRank(right);
    if (rank) return rank;
    return (left.expires_at || 0) - (right.expires_at || 0);
  })[0] || null;
}

function updateMobileAttentionSignals(openCount = cachedRequests.filter(isOpenRequest).length) {
  const handoffState = document.body.dataset.browserHandoffState || "idle";
  if (openCount > 0) {
    document.title = `(${openCount}) ${BASE_DOCUMENT_TITLE}`;
  } else if (handoffState === "active_takeover") {
    document.title = `Live - ${BASE_DOCUMENT_TITLE}`;
  } else if (handoffState === "preview") {
    document.title = `View - ${BASE_DOCUMENT_TITLE}`;
  } else {
    document.title = BASE_DOCUMENT_TITLE;
  }
  const firstUpdate = lastAttentionOpenCount === null;
  const attentionIncreased = !firstUpdate && openCount > lastAttentionOpenCount;
  const handoffActivated = !firstUpdate && handoffState === "active_takeover" && lastAttentionHandoffState !== "active_takeover";
  if ((attentionIncreased || handoffActivated) && navigator.vibrate && Date.now() - lastAttentionSignalAt > 3000) {
    try {
      navigator.vibrate([80]);
      lastAttentionSignalAt = Date.now();
    } catch {
      lastAttentionSignalAt = Date.now();
    }
  }
  lastAttentionOpenCount = openCount;
  lastAttentionHandoffState = handoffState;
}

function updateAttentionStrip(openRequests) {
  const strip = document.querySelector("#attention-strip");
  if (!strip) return;
  const primary = primaryOpenRequest(openRequests);
  updateMobileAttentionSignals(openRequests.length);
  strip.hidden = !primary;
  document.body.dataset.hasAttention = primary ? "true" : "false";
  strip.dataset.requestId = primary?.request_id || "";
  if (!primary) return;
  const title = document.querySelector("#attention-title");
  const detail = document.querySelector("#attention-detail");
  const action = document.querySelector("#attention-review");
  if (title) title.textContent = t("attentionTitle", openRequests.length);
  if (detail) {
    const type = displayRequestType(primary);
    const status = displayStatus(primary.status);
    const summary = primary.action_summary || primary.origin || primary.request_id;
    detail.textContent = `${t("attentionDetail", type, status)} · ${summary}`;
  }
  if (action) action.textContent = t("attentionAction");
}

function updateTakeoverTabBadge(request = null, context = null) {
  const link = document.querySelector('a[href="#takeover-panel"]');
  if (!link) return;
  const hasActiveTakeover = Boolean(request && request.status === "user_control");
  const hasBrowserPreview = !hasActiveTakeover && Boolean(context?.active && context?.current_url);
  link.classList.toggle("has-active-takeover", hasActiveTakeover);
  link.classList.toggle("has-browser-preview", hasBrowserPreview);
  link.dataset.badge = hasActiveTakeover ? t("takeoverTabLive") : hasBrowserPreview ? t("takeoverTabPreview") : "";
  link.dataset.browserContextId = hasActiveTakeover ? request.browser_context_id || "" : hasBrowserPreview ? context.browser_context_id || "" : "";
  document.body.dataset.browserHandoffState = hasActiveTakeover ? "active_takeover" : hasBrowserPreview ? "preview" : "idle";
  updateMobileAttentionSignals();
}

function browserHandoffUrl(request = null, context = null) {
  return request?.top_level_url || request?.origin || context?.current_url || context?.origin || context?.browser_context_id || "";
}

function updateBrowserHandoffState(request = null, context = null) {
  updateTakeoverTabBadge(request, context);
  const strip = document.querySelector("#browser-handoff-strip");
  if (!strip) return;
  const hasActiveTakeover = Boolean(request && request.status === "user_control");
  const hasBrowserPreview = !hasActiveTakeover && Boolean(context?.active && context?.current_url);
  const visible = hasActiveTakeover || hasBrowserPreview;
  strip.hidden = !visible;
  strip.dataset.handoffState = hasActiveTakeover ? "active_takeover" : hasBrowserPreview ? "preview" : "idle";
  if (!visible) return;
  const title = document.querySelector("#browser-handoff-title");
  const detail = document.querySelector("#browser-handoff-detail");
  const meta = document.querySelector("#browser-handoff-meta");
  const view = document.querySelector("#browser-handoff-view");
  const pause = document.querySelector("#browser-handoff-pause");
  const resume = document.querySelector("#browser-handoff-continue");
  if (title) title.textContent = t(hasActiveTakeover ? "browserHandoffActiveTitle" : "browserHandoffPreviewTitle");
  if (detail) detail.textContent = t(hasActiveTakeover ? "browserHandoffActiveDetail" : "browserHandoffPreviewDetail");
  if (meta) meta.textContent = browserHandoffUrl(request, context) || t("browserHandoffNoUrl");
  if (view) view.textContent = t("browserHandoffView");
  if (pause) {
    pause.hidden = hasActiveTakeover;
    pause.textContent = t("browserHandoffPause");
    pause.disabled = agentControlBusy || hasActiveTakeover;
  }
  if (resume) {
    resume.hidden = !hasActiveTakeover;
    resume.textContent = t("browserHandoffContinue");
    resume.disabled = agentControlBusy || !hasActiveTakeover;
  }
}

function setOverviewCard(cardId, { state = "idle", detail = "", meta = "" } = {}) {
  const card = document.querySelector(`#${cardId}`);
  if (!card) return;
  card.dataset.state = state;
  const detailNode = card.querySelector("[data-overview-detail]");
  const metaNode = card.querySelector("[data-overview-meta]");
  if (detailNode) detailNode.textContent = detail;
  if (metaNode) metaNode.textContent = meta;
}

function overviewRuntimeState(runner = cachedRuntimeStatus?.chat_runner || {}) {
  if (!cachedRuntimeStatus) return { state: "blocked", detail: t("overviewSyncOffline") };
  if (modeRequiresPairing(cachedRuntimeStatus.mode) && !cachedPairingAuthenticated) {
    return { state: "blocked", detail: t("overviewUnpaired") };
  }
  if (runner?.tui_bridge_active) return { state: "ok", detail: t("overviewSyncAttached") };
  if (runner?.waiting_for_tui_bridge) {
    return {
      state: runnerCanRestartCurrentConsole(runner) ? "warn" : "blocked",
      detail: runnerCanRestartCurrentConsole(runner) ? t("overviewSyncNeedsRestart") : t("overviewSyncServerOnly")
    };
  }
  if (runner?.thread_id) return { state: "warn", detail: t("overviewSyncBackground") };
  return { state: "blocked", detail: t("overviewSyncOffline") };
}

function setOverviewAction({ title, detail, primaryLabel, primaryAction, secondaryLabel = "", secondaryAction = "" }) {
  setFieldText("#overview-next-title", title, t("overviewNoUrgentAction"));
  setFieldText("#overview-next-detail", detail, "");
  const primary = document.querySelector("#overview-primary-action");
  const secondary = document.querySelector("#overview-secondary-action");
  if (primary) {
    primary.textContent = primaryLabel || t("overviewPrimaryAction");
    primary.dataset.action = primaryAction || "chat";
    primary.disabled = false;
  }
  if (secondary) {
    secondary.hidden = !secondaryAction;
    secondary.textContent = secondaryLabel || t("overviewSecondaryAction");
    secondary.dataset.action = secondaryAction || "";
    secondary.disabled = false;
  }
}

function updateOverviewSyncApprovalButtons() {
  const request = pendingConsoleRestartRequest();
  const confirm = document.querySelector("#overview-sync-confirm");
  const primary = document.querySelector("#overview-primary-action");
  if (primary?.dataset.action === "sync-approve") {
    primary.disabled = !request || !confirm?.checked;
  } else if (primary) {
    primary.disabled = false;
  }
}

function updateOverviewSyncApprovalCard(request = pendingConsoleRestartRequest()) {
  const card = document.querySelector("#overview-sync-approval");
  if (!card) return;
  const visible = Boolean(request);
  card.hidden = !visible;
  const confirm = document.querySelector("#overview-sync-confirm");
  if (!visible) {
    activeOverviewSyncApprovalRequestId = null;
    if (confirm) confirm.checked = false;
    updateOverviewSyncApprovalButtons();
    return;
  }
  if (activeOverviewSyncApprovalRequestId !== request.request_id && confirm) {
    confirm.checked = false;
  }
  activeOverviewSyncApprovalRequestId = request.request_id;
  const details = request.structured_details || {};
  setFieldText("#overview-sync-thread", details.thread_id, request.request_id);
  setFieldText("#overview-sync-pid", details.active_cli_pid, t("notVisible"));
  setFieldText("#overview-sync-expires", request.expires_at ? formatTimestamp(request.expires_at) : "", t("notVisible"));
  updateOverviewSyncApprovalButtons();
}

function updateOverview() {
  const runner = cachedRuntimeStatus?.chat_runner || {};
  const openRequests = cachedRequests.filter(isOpenRequest);
  const primaryRequest = primaryOpenRequest(openRequests);
  const takeoverRequest = findActiveTakeoverRequest(cachedRequests);
  const browserContext = activeBrowserContext();
  const runtime = overviewRuntimeState(runner);
  const paired = cachedRuntimeStatus
    ? (!modeRequiresPairing(cachedRuntimeStatus.mode) || cachedPairingAuthenticated)
    : cachedPairingAuthenticated;
  setOverviewCard("overview-sync-card", {
    state: runtime.state,
    detail: runtime.detail,
    meta: runner.thread_id || cachedRuntimeStatus?.mode || ""
  });
  setOverviewCard("overview-requests-card", {
    state: openRequests.length ? "warn" : "ok",
    detail: t("overviewOpenRequests", openRequests.length, cachedRequests.length),
    meta: primaryRequest ? displayRequestType(primaryRequest) : t("noOpenRequests")
  });
  const browserState = takeoverRequest ? "active" : browserContext ? "warn" : "idle";
  setOverviewCard("overview-browser-card", {
    state: browserState,
    detail: takeoverRequest ? t("overviewBrowserActive") : browserContext ? t("overviewBrowserPreview") : t("overviewBrowserIdle"),
    meta: browserHandoffUrl(takeoverRequest, browserContext)
  });
  setOverviewCard("overview-chat-card", {
    state: document.body.dataset.chatSendMode === "blocked" ? "blocked" : "ok",
    detail: t("overviewChatRecords", cachedChatMessages.length, cachedChatRecords.length),
    meta: document.querySelector("#chat-session-title")?.textContent || ""
  });
  setOverviewCard("overview-pairing-card", {
    state: paired ? "ok" : "blocked",
    detail: paired ? t("overviewPaired") : t("overviewUnpaired"),
    meta: storedPairingIdentity().deviceId || cachedRuntimeStatus?.public_url || window.location.origin
  });

  const syncRequest = pendingConsoleRestartRequest();
  if (!paired) {
    updateOverviewSyncApprovalCard(null);
    setOverviewAction({
      title: t("overviewActionPairTitle"),
      detail: t("overviewActionPairDetail"),
      primaryLabel: t("pairButton"),
      primaryAction: "pair"
    });
    return;
  }
  if (syncRequest) {
    setOverviewAction({
      title: t("overviewActionSyncTitle"),
      detail: t("overviewActionSyncDetail"),
      primaryLabel: t("syncApprovalApprove"),
      primaryAction: "sync-approve",
      secondaryLabel: t("syncApprovalOpenRequest"),
      secondaryAction: "requests"
    });
    updateOverviewSyncApprovalCard(syncRequest);
    return;
  }
  updateOverviewSyncApprovalCard(null);
  if (primaryRequest) {
    setOverviewAction({
      title: t("overviewActionRequestTitle", displayRequestType(primaryRequest)),
      detail: t("overviewActionRequestDetail", primaryRequest.action_summary || primaryRequest.origin || primaryRequest.request_id),
      primaryLabel: t("attentionAction"),
      primaryAction: "requests"
    });
    return;
  }
  if (takeoverRequest || browserContext) {
    setOverviewAction({
      title: takeoverRequest ? t("browserHandoffActiveTitle") : t("overviewActionBrowserTitle"),
      detail: takeoverRequest ? t("browserHandoffActiveDetail") : t("overviewActionBrowserDetail"),
      primaryLabel: takeoverRequest ? t("browserHandoffView") : t("browserHandoffPause"),
      primaryAction: takeoverRequest ? "takeover" : "pause-browser",
      secondaryLabel: t("browserHandoffView"),
      secondaryAction: "takeover"
    });
    return;
  }
  if (runnerNeedsCurrentSessionSync(runner) && runnerCanRestartCurrentConsole(runner)) {
    setOverviewAction({
      title: t("overviewActionSyncTitle"),
      detail: t("overviewActionSyncDetail"),
      primaryLabel: t("enableCurrentSessionSync"),
      primaryAction: "sync"
    });
    return;
  }
  setOverviewAction({
    title: t("overviewNoUrgentAction"),
    detail: t("overviewNoUrgentDetail"),
    primaryLabel: t("overviewActionChatTitle"),
    primaryAction: "chat",
    secondaryLabel: t("browserHandoffView"),
    secondaryAction: "takeover"
  });
}

function runOverviewAction(action) {
  if (action === "pair") {
    activatePanel("pairing-panel");
  } else if (action === "sync-approve") {
    approvePendingSyncRequestFromOverview();
  } else if (action === "sync") {
    const request = pendingConsoleRestartRequest();
    if (request) {
      activatePanel("task-panel", { persist: false });
      document.querySelector("#chat-sync-approval")?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      requestConsoleRestartApproval();
    }
  } else if (action === "requests") {
    if (!openPendingSyncRequest()) {
      setRequestFilter("open");
      activatePanel("requests-panel");
      renderRequestList(cachedRequests, "open");
    }
  } else if (action === "pause-browser") {
    requestTakeoverPause();
  } else if (action === "takeover") {
    activatePanel("takeover-panel");
  } else {
    activatePanel("task-panel");
  }
}

const main = document.querySelector("main");

const runtimeStatus = document.createElement("section");
runtimeStatus.id = "runtime-status";
runtimeStatus.className = "status-strip";
runtimeStatus.innerHTML = `
  <div>
    <strong id="runtime-mode">${t("checkingRuntime")}</strong>
    <span id="runtime-detail">${t("runtimeDetail")}</span>
    <div id="runtime-command-row" class="runtime-command-row" hidden>
      <code id="runtime-command"></code>
      <button id="runtime-copy-command" class="ghost-button runtime-copy-button" type="button">${t("copyCommand")}</button>
      <button id="runtime-restart-bridge" class="ghost-button runtime-restart-button" type="button">${t("restartBridge")}</button>
    </div>
  </div>
  <div class="runtime-actions">
    <button id="runtime-pause-agent" class="quick-pause-button" type="button">${t("pauseAgent")}</button>
    <div id="runtime-counts">${t("requestsCount", 0, 0)}</div>
  </div>
`;
main.insertBefore(runtimeStatus, document.querySelector("#pairing-panel"));

const attentionStrip = document.createElement("section");
attentionStrip.id = "attention-strip";
attentionStrip.className = "attention-strip";
attentionStrip.hidden = true;
attentionStrip.innerHTML = `
  <div>
    <strong id="attention-title">${t("attentionTitle", 0)}</strong>
    <span id="attention-detail"></span>
  </div>
  <button id="attention-review" type="button">${t("attentionAction")}</button>
`;
main.insertBefore(attentionStrip, document.querySelector("#pairing-panel"));

const requestsRoot = document.createElement("section");
requestsRoot.id = "requests-panel";
requestsRoot.className = "priority-panel";
requestsRoot.innerHTML = `
  <div class="panel-heading">
    <div>
      <h2>${t("requestsTitle")}</h2>
      <p>${t("requestsIntro")}</p>
    </div>
    <div class="filter-row" aria-label="${t("requestFiltersLabel")}">
      <button data-filter="open" class="active">${t("filterOpen")}</button>
      <button data-filter="all">${t("filterAll")}</button>
      <button data-filter="credential">${t("filterCredential")}</button>
      <button data-filter="challenge">${t("filterChallenge")}</button>
      <button data-filter="approval">${t("filterApproval")}</button>
      <button data-filter="takeover">${t("filterTakeover")}</button>
    </div>
  </div>
  <div id="requests-list" class="request-grid">${t("loading")}</div>
`;
main.insertBefore(requestsRoot, document.querySelector("#pairing-panel"));
setupPanelNavigation();

const attentionReviewButton = document.querySelector("#attention-review");
if (attentionReviewButton) {
  attentionReviewButton.onclick = () => {
    const requestId = document.querySelector("#attention-strip")?.dataset.requestId || "";
    setRequestFilter("open");
    activatePanel("requests-panel");
    renderRequestList(cachedRequests, "open");
    setTimeout(() => focusRequestCard(requestId), 50);
  };
}

const overviewPrimaryActionButton = document.querySelector("#overview-primary-action");
if (overviewPrimaryActionButton) {
  overviewPrimaryActionButton.onclick = () => runOverviewAction(overviewPrimaryActionButton.dataset.action || "chat");
}

const overviewSecondaryActionButton = document.querySelector("#overview-secondary-action");
if (overviewSecondaryActionButton) {
  overviewSecondaryActionButton.onclick = () => runOverviewAction(overviewSecondaryActionButton.dataset.action || "takeover");
}

const overviewSyncConfirm = document.querySelector("#overview-sync-confirm");
if (overviewSyncConfirm) {
  overviewSyncConfirm.onchange = () => updateOverviewSyncApprovalButtons();
}

document.querySelectorAll(".overview-card").forEach((card) => {
  card.onclick = () => runOverviewAction(card.dataset.action || "chat");
});

const sendChatMessageButton = document.querySelector("#send-chat-message");
if (sendChatMessageButton) {
  sendChatMessageButton.onclick = () => sendChatMessage();
}

const chatFilesInput = document.querySelector("#chat-files");
if (chatFilesInput) {
  chatFilesInput.onchange = () => renderSelectedChatFiles();
}

const chatInput = document.querySelector("#chat-input");
if (chatInput) {
  chatInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      sendChatMessage();
    }
  });
}

const pairDeviceButton = document.querySelector("#pair-device");
if (pairDeviceButton) {
  pairDeviceButton.onclick = () => pairDevice();
}

const forgetLocalPairingButton = document.querySelector("#forget-local-pairing");
if (forgetLocalPairingButton) {
  forgetLocalPairingButton.onclick = () => forgetLocalPairing();
}

const refreshDevicesButton = document.querySelector("#refresh-devices");
if (refreshDevicesButton) {
  refreshDevicesButton.onclick = () => loadDevicesAndSessions();
}

const refreshTakeoverFrameButton = document.querySelector("#refresh-takeover-frame");
if (refreshTakeoverFrameButton) {
  refreshTakeoverFrameButton.onclick = () => refreshActiveTakeoverFrame();
}

const requestTakeoverPauseButton = document.querySelector("#request-takeover-pause");
if (requestTakeoverPauseButton) {
  requestTakeoverPauseButton.onclick = () => requestTakeoverPause();
}

const runtimePauseAgentButton = document.querySelector("#runtime-pause-agent");
if (runtimePauseAgentButton) {
  runtimePauseAgentButton.onclick = () => {
    if (takeoverIsActive()) {
      releaseActiveTakeover();
    } else {
      requestTakeoverPause();
    }
  };
}

const runtimeCopyCommandButton = document.querySelector("#runtime-copy-command");
if (runtimeCopyCommandButton) {
  runtimeCopyCommandButton.onclick = () => copyRuntimeCommand();
}

const runtimeRestartBridgeButton = document.querySelector("#runtime-restart-bridge");
if (runtimeRestartBridgeButton) {
  runtimeRestartBridgeButton.onclick = () => restartConsoleBridge();
}

const browserHandoffViewButton = document.querySelector("#browser-handoff-view");
if (browserHandoffViewButton) {
  browserHandoffViewButton.onclick = () => activatePanel("takeover-panel");
}

const browserHandoffPauseButton = document.querySelector("#browser-handoff-pause");
if (browserHandoffPauseButton) {
  browserHandoffPauseButton.onclick = () => requestTakeoverPause();
}

const browserHandoffContinueButton = document.querySelector("#browser-handoff-continue");
if (browserHandoffContinueButton) {
  browserHandoffContinueButton.onclick = () => releaseActiveTakeover();
}

const chatSessionRestartButton = document.querySelector("#chat-session-restart");
if (chatSessionRestartButton) {
  chatSessionRestartButton.onclick = () => restartConsoleBridge();
}

const chatSyncApprovalConfirm = document.querySelector("#chat-sync-approval-confirm");
if (chatSyncApprovalConfirm) {
  chatSyncApprovalConfirm.onchange = () => updateChatSyncApprovalButtons();
}

const chatSyncApprovalViewButton = document.querySelector("#chat-sync-approval-view");
if (chatSyncApprovalViewButton) {
  chatSyncApprovalViewButton.onclick = () => openOrRefreshPendingSyncRequest();
}

const chatSyncApprovalDenyButton = document.querySelector("#chat-sync-approval-deny");
if (chatSyncApprovalDenyButton) {
  chatSyncApprovalDenyButton.onclick = () => denyPendingSyncRequestFromChat();
}

const chatSyncApprovalApproveButton = document.querySelector("#chat-sync-approval-approve");
if (chatSyncApprovalApproveButton) {
  chatSyncApprovalApproveButton.onclick = () => approvePendingSyncRequestFromChat();
}

const releaseActiveTakeoverButton = document.querySelector("#release-active-takeover");
if (releaseActiveTakeoverButton) {
  releaseActiveTakeoverButton.onclick = () => releaseActiveTakeover();
}

const activeTakeoverTextInput = document.querySelector("#active-takeover-text");
if (activeTakeoverTextInput) {
  activeTakeoverTextInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      sendActiveTakeoverText();
    }
  });
}

const sendActiveTakeoverTextButton = document.querySelector("#send-active-takeover-text");
if (sendActiveTakeoverTextButton) {
  sendActiveTakeoverTextButton.onclick = () => sendActiveTakeoverText();
}

const sendActiveTakeoverEnterButton = document.querySelector("#send-active-takeover-enter");
if (sendActiveTakeoverEnterButton) {
  sendActiveTakeoverEnterButton.onclick = () => sendActiveTakeoverEnter();
}

const zoomOutTakeoverFrameButton = document.querySelector("#zoom-out-takeover-frame");
if (zoomOutTakeoverFrameButton) {
  zoomOutTakeoverFrameButton.onclick = () => setTakeoverFrameZoom(takeoverFrameZoom - TAKEOVER_ZOOM_STEP);
}

const zoomResetTakeoverFrameButton = document.querySelector("#zoom-reset-takeover-frame");
if (zoomResetTakeoverFrameButton) {
  zoomResetTakeoverFrameButton.onclick = () => resetTakeoverFrameView();
}

const zoomInTakeoverFrameButton = document.querySelector("#zoom-in-takeover-frame");
if (zoomInTakeoverFrameButton) {
  zoomInTakeoverFrameButton.onclick = () => setTakeoverFrameZoom(takeoverFrameZoom + TAKEOVER_ZOOM_STEP);
}

const panTakeoverFrameButton = document.querySelector("#pan-takeover-frame");
if (panTakeoverFrameButton) {
  panTakeoverFrameButton.onclick = () => setTakeoverFramePanMode(!takeoverFramePanMode);
}

const approvalConfirmInput = document.querySelector("#approval-confirm");
if (approvalConfirmInput) {
  approvalConfirmInput.onchange = () => updatePaymentApprovalButtons();
}

const approvePaymentButton = document.querySelector("#approve");
if (approvePaymentButton) {
  approvePaymentButton.onclick = () => approveActivePaymentRequest();
}

const denyPaymentButton = document.querySelector("#deny");
if (denyPaymentButton) {
  denyPaymentButton.onclick = () => denyActivePaymentRequest();
}

const languageSelect = document.querySelector("#language-select");
if (languageSelect) {
  LANGUAGE_OPTIONS.forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    languageSelect.append(option);
  });
  languageSelect.value = currentLanguage;
  languageSelect.onchange = () => {
    currentLanguage = languageSelect.value;
    localStorage.setItem("omnidoer_language", currentLanguage);
    applyLanguage();
    renderRequestList(cachedRequests);
    renderChatTimeline(cachedChatMessages, cachedChatRecords, cachedChatTerminal);
  };
}

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.onclick = () => {
    setRequestFilter(button.dataset.filter);
    renderRequestList(cachedRequests, button.dataset.filter);
  };
});

const encoder = new TextEncoder();
const decoder = new TextDecoder();
const BASE_DOCUMENT_TITLE = document.title || "OmniDoer Control Client";
const TAKEOVER_FRAME_MAX_AGE_MS = 30000;
const TAKEOVER_FRAME_POLL_MS = 1500;
const BROWSER_PREVIEW_POLL_MS = 2000;
const TAKEOVER_FRAME_AFTER_INPUT_MS = 180;
const TAKEOVER_FRAME_WS_SNAPSHOTS = 1200;
const TAKEOVER_FRAME_WS_INTERVAL_SECONDS = 0.75;
const TAKEOVER_FRAME_PROFILE_DEFAULT = "balanced";
const TAKEOVER_FRAME_PROFILE_DATA_SAVER = "data_saver";
const TAKEOVER_ZOOM_MIN = 1;
const TAKEOVER_ZOOM_MAX = 3;
const TAKEOVER_ZOOM_STEP = 0.25;
const TAKEOVER_DOUBLE_TAP_MS = 320;
const TAKEOVER_DOUBLE_TAP_DISTANCE = 24;
const PENDING_TAKEOVER_PAUSE_TTL_MS = 60000;
const AUTO_SYNC_REQUEST_COOLDOWN_MS = 60000;
let cachedRequests = [];
let cachedChatMessages = [];
let cachedChatRecords = [];
let cachedChatTerminal = null;
let cachedBrowserContexts = [];
let cachedRuntimeStatus = null;
let lastChatPayloadFingerprint = "";
let realtimeRefreshTimer = null;
let requestStreamActive = false;
let requestStreamRestart = null;
let chatStreamActive = false;
let chatStreamRestart = null;
let browserContextStreamActive = false;
let browserContextStreamRestart = null;
let activeTakeoverFrameRequest = null;
let takeoverFrameTimer = null;
let takeoverFreshnessTimer = null;
let takeoverFrameRefreshTimer = null;
let takeoverFrameFetchInFlight = false;
let takeoverFrameFetchQueued = false;
let takeoverFrameSocket = null;
let takeoverFrameSocketRequest = null;
let takeoverFrameSocketRestart = null;
let browserPreviewTimer = null;
let browserPreviewSocket = null;
let browserPreviewSocketContext = null;
let browserPreviewSocketRestart = null;
let activeBrowserPreviewContext = null;
let takeoverFrameMisses = 0;
let takeoverFrameVisibilityPaused = false;
let takeoverFrameZoom = TAKEOVER_ZOOM_MIN;
let takeoverFramePanMode = false;
let takeoverPendingTap = null;
let takeoverPendingTapTimer = null;
let agentControlBusy = false;
let pendingTakeoverPauseClientMessageId = "";
let pendingTakeoverPauseRequestedAt = 0;
let pendingTakeoverAutoStartBusy = false;
let autoOpenedTakeoverRequestId = "";
let autoOpenedPreviewContextId = "";
let lastAttentionOpenCount = null;
let lastAttentionHandoffState = "idle";
let lastAttentionSignalAt = 0;
let activePaymentApprovalRequest = null;
let renderedPaymentApprovalRequestId = null;
let bridgeActivationMonitor = null;
let bridgeActivationDeadline = 0;
let activeChatSyncApprovalRequestId = null;
let activeOverviewSyncApprovalRequestId = null;
let autoOpenedSyncRequestId = "";
let autoSyncRequestInFlight = false;
let autoSyncRequestLastAt = 0;
let pairingSuccessHoldUntil = 0;
let pairingSuccessMessage = "";
let cachedPairingAuthenticated = false;
let autoPairingStarted = false;
let authenticatedRealtimeStarted = false;

applyLanguage();

const urlParams = new URLSearchParams(window.location.search);
const initialPairingCode = urlParams.get("code");
const initialPairingId = urlParams.get("pairing_id");
if (initialPairingCode) {
  document.querySelector("#pairing-code").value = initialPairingCode;
  document.querySelector("#pairing-code-preview").textContent = initialPairingCode;
  activatePanel("pairing-panel", { persist: false });
}
if (initialPairingId) {
  loadPairingDetails(initialPairingId);
  activatePanel("pairing-panel", { persist: false });
} else {
  document.querySelector("#pairing-server-url").textContent = window.location.origin;
}
if ((initialPairingCode || initialPairingId) && window.history?.replaceState) {
  window.history.replaceState({}, document.title, window.location.pathname || "/");
}

function csrfHeaders() {
  const token = localStorage.getItem("omnidoer_csrf_token");
  return token ? { "x-omnidoer-csrf": token } : {};
}

function modeRequiresPairing(mode) {
  return mode === "cloud_direct" || mode === "lan";
}

function bytesToB64url(bytes) {
  return b64url(bytes);
}

function b64urlToBytes(value) {
  const padded = value + "=".repeat((4 - value.length % 4) % 4);
  const binary = atob(padded.replaceAll("-", "+").replaceAll("_", "/"));
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

function activeFilter() {
  return document.querySelector("[data-filter].active")?.dataset.filter || "open";
}

function formatTimestamp(value) {
  if (!value) return "not set";
  return new Date(value * 1000).toLocaleString();
}

function requestExpiresInMs(request) {
  if (!request?.expires_at) return 0;
  return request.expires_at * 1000 - Date.now();
}

function syncRequestNeedsRefresh(request) {
  if (!request) return false;
  return requestExpiresInMs(request) < SYNC_REQUEST_RENEW_WINDOW_MS;
}

function requestKind(request) {
  if (request.request_type === "credential") return "credential";
  if (request.request_type === "human_takeover" || request.request_type === "account_registration") return "takeover";
  if (["file_upload", "account_delete", "password_change", "two_factor_change", "message_send", "console_restart"].includes(request.request_type)) return "approval";
  if (request.request_type.endsWith("_approval") || request.request_type.includes("approval")) return "approval";
  return "challenge";
}

function displayRequestType(request) {
  return t("requestTypeLabels")?.[request.request_type] || request.request_type.replaceAll("_", " ");
}

function displayStatus(status) {
  return t("statusLabels")?.[status] || status;
}

function displayMetadataLabel(label) {
  return t("metadataLabels")?.[label] || label;
}

function isOpenRequest(request) {
  return ["pending", "user_control"].includes(request.status);
}

function requestMatchesFilter(request, filter) {
  if (filter === "all") return true;
  if (filter === "open") return isOpenRequest(request);
  return isOpenRequest(request) && requestKind(request) === filter;
}

function pendingConsoleRestartRequest() {
  return cachedRequests.find((request) => request.request_type === "console_restart" && request.status === "pending") || null;
}

function upsertCachedRequest(request) {
  if (!request?.request_id) return;
  const existingIndex = cachedRequests.findIndex((item) => item.request_id === request.request_id);
  if (existingIndex >= 0) {
    cachedRequests[existingIndex] = request;
  } else {
    cachedRequests = [request, ...cachedRequests];
  }
}

function updateChatSyncApprovalButtons() {
  const request = pendingConsoleRestartRequest();
  const confirm = document.querySelector("#chat-sync-approval-confirm");
  const approve = document.querySelector("#chat-sync-approval-approve");
  const deny = document.querySelector("#chat-sync-approval-deny");
  const actionable = Boolean(request);
  if (approve) approve.disabled = !actionable || !confirm?.checked;
  if (deny) deny.disabled = !actionable;
}

function updateChatSyncApprovalCard(request = pendingConsoleRestartRequest()) {
  const card = document.querySelector("#chat-sync-approval");
  if (!card) return;
  const visible = Boolean(request);
  card.hidden = !visible;
  const confirm = document.querySelector("#chat-sync-approval-confirm");
  if (!visible) {
    activeChatSyncApprovalRequestId = null;
    if (confirm) confirm.checked = false;
    updateChatSyncApprovalButtons();
    return;
  }
  const details = request.structured_details || {};
  if (activeChatSyncApprovalRequestId !== request.request_id && confirm) {
    confirm.checked = false;
  }
  activeChatSyncApprovalRequestId = request.request_id;
  setFieldText("#chat-sync-approval-thread", details.thread_id, request.request_id);
  setFieldText("#chat-sync-approval-pid", details.active_cli_pid, t("notVisible"));
  setFieldText("#chat-sync-approval-command", details.restart_command, t("notVisible"));
  setFieldText("#chat-sync-approval-expires", request.expires_at ? formatTimestamp(request.expires_at) : "", t("notVisible"));
  setNodeText("#chat-sync-approval-title", "syncApprovalTitle");
  setNodeText("#chat-sync-approval-detail", "syncApprovalDetail");
  setNodeText("#chat-sync-approval-expires-label", "syncApprovalExpires");
  setButtonText("#chat-sync-approval-view", "syncApprovalOpenRequest");
  setButtonText("#chat-sync-approval-deny", "deny");
  setButtonText("#chat-sync-approval-approve", "syncApprovalApprove");
  updateChatSyncApprovalButtons();
  maybeAutoOpenSyncApprovalCard(request);
}

function maybeAutoOpenSyncApprovalCard(request) {
  if (!request || request.request_type !== "console_restart" || request.status !== "pending") {
    if (!request) autoOpenedSyncRequestId = "";
    return;
  }
  if (autoOpenedSyncRequestId === request.request_id) return;
  const activePanel = document.body.dataset.activePanel || DEFAULT_PANEL_ID;
  if (activePanel === "requests-panel" || activePanel === "takeover-panel" || takeoverIsActive()) return;
  autoOpenedSyncRequestId = request.request_id;
  activatePanel("task-panel", { persist: false });
  const scrollToCard = () => {
    document.querySelector("#chat-sync-approval")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  if (window.requestAnimationFrame) {
    window.requestAnimationFrame(scrollToCard);
  } else {
    setTimeout(scrollToCard, 50);
  }
}

function setRequestFilter(filter) {
  document.querySelectorAll("[data-filter]").forEach((item) => {
    item.classList.toggle("active", item.dataset.filter === filter);
  });
}

function focusRequestCard(requestId) {
  if (!requestId) return;
  const card = document.querySelector(`.request[data-request-id="${CSS.escape(requestId)}"]`);
  if (!card) return;
  card.classList.add("request-focus");
  card.scrollIntoView({ behavior: "smooth", block: "center" });
  setTimeout(() => card.classList.remove("request-focus"), 2400);
}

function openPendingSyncRequest() {
  const request = pendingConsoleRestartRequest();
  if (!request) return false;
  setRequestFilter("open");
  activatePanel("requests-panel");
  renderRequestList(cachedRequests, "open");
  setTimeout(() => focusRequestCard(request.request_id), 50);
  return true;
}

async function openOrRefreshPendingSyncRequest() {
  const request = pendingConsoleRestartRequest();
  if (!request) return false;
  if (syncRequestNeedsRefresh(request)) {
    await requestConsoleRestartApproval({ renew: true });
    return true;
  }
  return openPendingSyncRequest();
}

function requestDraftField(input) {
  if (input.dataset.secretField) return `secret:${input.dataset.secretField}`;
  if (input.dataset.challengeField) return `challenge:${input.dataset.challengeField}`;
  if (input.hasAttribute("data-takeover-text")) return "takeover:text";
  return input.name || input.id || "";
}

function requestDraftInputs(root) {
  return Array.from(root.querySelectorAll("[data-secret-field], [data-challenge-field], [data-takeover-text]"));
}

function captureRequestDrafts(list) {
  const drafts = {};
  const active = document.activeElement;
  let activeDraft = null;
  list.querySelectorAll(".request[data-request-id]").forEach((item) => {
    const requestId = item.dataset.requestId;
    if (!requestId) return;
    requestDraftInputs(item).forEach((input) => {
      const field = requestDraftField(input);
      if (!field) return;
      const key = `${requestId}:${field}`;
      const isCheckbox = input.type === "checkbox";
      const value = isCheckbox ? input.checked : input.value;
      if (value || active === input) {
        drafts[key] = { value, isCheckbox };
      }
      if (active === input) {
        activeDraft = {
          key,
          selectionStart: input.selectionStart,
          selectionEnd: input.selectionEnd
        };
      }
    });
  });
  return { drafts, activeDraft };
}

function restoreRequestDrafts(list, captured) {
  if (!captured) return;
  let activeInput = null;
  list.querySelectorAll(".request[data-request-id]").forEach((item) => {
    const requestId = item.dataset.requestId;
    if (!requestId) return;
    requestDraftInputs(item).forEach((input) => {
      const field = requestDraftField(input);
      if (!field) return;
      const key = `${requestId}:${field}`;
      const draft = captured.drafts[key];
      if (!draft) return;
      if (draft.isCheckbox) {
        input.checked = Boolean(draft.value);
      } else {
        input.value = draft.value;
      }
      if (captured.activeDraft?.key === key) activeInput = input;
    });
  });
  if (activeInput) {
    activeInput.focus({ preventScroll: true });
    if (typeof activeInput.setSelectionRange === "function") {
      const start = captured.activeDraft.selectionStart;
      const end = captured.activeDraft.selectionEnd;
      if (start !== null && end !== null) activeInput.setSelectionRange(start, end);
    }
  }
}

function setStatus(
  message,
  detail = "",
  runtimeState = "",
  command = "",
  restartLabelKey = "restartBridge",
  restartActionAvailable = true
) {
  document.querySelector("#runtime-mode").textContent = message;
  document.querySelector("#runtime-detail").textContent = detail;
  const runtimeStatusPanel = document.querySelector("#runtime-status");
  if (runtimeStatusPanel) {
    runtimeStatusPanel.title = detail ? `${message}: ${detail}` : message;
    runtimeStatusPanel.setAttribute("aria-label", runtimeStatusPanel.title);
  }
  const runtimeCommandRow = document.querySelector("#runtime-command-row");
  const runtimeCommand = document.querySelector("#runtime-command");
  const runtimeCopyCommand = document.querySelector("#runtime-copy-command");
  const runtimeRestartBridge = document.querySelector("#runtime-restart-bridge");
  if (runtimeCommand) {
    runtimeCommand.textContent = command;
  }
  if (runtimeCommandRow) {
    runtimeCommandRow.hidden = !command;
  }
  if (runtimeCopyCommand) {
    runtimeCopyCommand.hidden = !command;
    runtimeCopyCommand.textContent = t("copyCommand");
  }
  if (runtimeRestartBridge) {
    runtimeRestartBridge.hidden = !command || !restartActionAvailable;
    runtimeRestartBridge.textContent = t(restartLabelKey);
    runtimeRestartBridge.classList.toggle("primary-action", ["enableCurrentSessionSync", "reviewSyncRequest"].includes(restartLabelKey));
  }
  document.body.dataset.runtimeState = runtimeState;
}

function runnerCanRestartCurrentConsole(runner = {}) {
  runner = runner || {};
  const diagnostics = runner.sync_diagnostics || {};
  if ("restart_current_console_available" in diagnostics) {
    return Boolean(diagnostics.restart_current_console_available);
  }
  const legacyRelay = runner.legacy_tui_relay || {};
  return Boolean(runner.restart_command && legacyRelay.active);
}

function runnerNeedsCurrentSessionSync(runner = {}) {
  runner = runner || {};
  const diagnostics = runner.sync_diagnostics || {};
  if (diagnostics.activation_action) {
    return diagnostics.activation_action === "restart_current_console";
  }
  const activeProcess = runner.active_tui_process_bridge || {};
  return Boolean(
    runner.waiting_for_tui_bridge &&
      runner.restart_command &&
      (activeProcess.installed_bridge_ready || runner.native_console_bridge?.ready)
  );
}

function updateChatSessionStatus(runner, { offline = false } = {}) {
  const panel = document.querySelector("#chat-session-status");
  if (!panel) return;
  const title = document.querySelector("#chat-session-title");
  const detail = document.querySelector("#chat-session-detail");
  const restart = document.querySelector("#chat-session-restart");
  const input = document.querySelector("#chat-input");
  const send = document.querySelector("#send-chat-message");
  const files = document.querySelector("#chat-files");
  const fileLabel = document.querySelector("#chat-files-label");
  const syncRequest = pendingConsoleRestartRequest();
  let state = "checking";
  let titleKey = "chatSessionCheckingTitle";
  let detailKey = "chatSessionCheckingDetail";
  let diagnosticKey = "";
  let sendKey = "sendUnavailable";
  let placeholderKey = "chatPlaceholderUnavailable";
  let canSend = false;
  let canRestart = false;
  if (offline) {
    state = "offline";
    titleKey = "chatSessionOfflineTitle";
    detailKey = "chatSessionOfflineDetail";
  } else if (modeRequiresPairing(cachedRuntimeStatus?.mode) && !cachedPairingAuthenticated) {
    state = "unpaired";
    titleKey = "chatSessionUnpairedTitle";
    detailKey = "chatSessionUnpairedDetail";
  } else if (runner?.tui_bridge_active) {
    state = "attached";
    titleKey = "chatSessionAttachedTitle";
    detailKey = "chatSessionAttachedDetail";
    sendKey = "sendToCurrentCli";
    placeholderKey = "chatPlaceholder";
    canSend = true;
    diagnosticKey = "chatSyncDiagnosticNative";
  } else if (runner?.waiting_for_tui_bridge) {
    const legacyRelay = runner.legacy_tui_relay || {};
    const diagnostics = runner.sync_diagnostics || {};
    const activeProcess = runner.active_tui_process_bridge || {};
    const staleActiveBinary = Boolean(activeProcess.active && !activeProcess.native_bridge_ready && activeProcess.installed_bridge_ready);
    state = legacyRelay.active ? "legacy_relay" : "server_only";
    titleKey = legacyRelay.active ? "chatSessionLegacyTitle" : "chatSessionServerOnlyTitle";
    detailKey = legacyRelay.active ? "chatSessionLegacyDetail" : "chatSessionServerOnlyDetail";
    sendKey = legacyRelay.active ? "sendToCurrentConsole" : "sendUnavailable";
    placeholderKey = legacyRelay.active ? "chatPlaceholderLegacy" : "chatPlaceholderUnavailable";
    canSend = Boolean(legacyRelay.active);
    canRestart = runnerCanRestartCurrentConsole(runner);
    diagnosticKey = staleActiveBinary
      ? "chatSyncDiagnosticStaleBinary"
      : diagnostics.temporary_terminal_relay ? "chatSyncDiagnosticLegacy" : "chatSyncDiagnosticWaiting";
    if (syncRequest) diagnosticKey = "chatSyncApprovalPending";
  } else if (runner?.thread_id) {
    state = "background_runner";
    titleKey = "chatSessionBackgroundTitle";
    detailKey = "chatSessionBackgroundDetail";
    sendKey = "sendToBackgroundRunner";
    placeholderKey = "chatPlaceholder";
    canSend = true;
    diagnosticKey = "chatSyncDiagnosticBackground";
  }
  panel.dataset.sessionState = state;
  document.body.dataset.chatSessionState = state;
  document.body.dataset.chatSendMode = canSend ? state : "blocked";
  if (title) title.textContent = t(titleKey);
  const detailText = `${t(detailKey)}${diagnosticKey ? ` ${t(diagnosticKey)}` : ""}`;
  if (detail) detail.textContent = detailText;
  panel.title = detailText;
  if (restart) {
    restart.hidden = !canRestart;
    restart.textContent = syncRequest ? t("reviewSyncRequest") : t(runnerNeedsCurrentSessionSync(runner) ? "enableCurrentSessionSync" : "restartBridge");
    restart.classList.toggle("primary-action", canRestart && runnerNeedsCurrentSessionSync(runner));
    restart.classList.toggle("pending-sync-request", Boolean(syncRequest));
  }
  if (input) {
    input.disabled = !canSend;
    input.placeholder = t(placeholderKey);
  }
  if (send) {
    send.disabled = !canSend;
    send.setAttribute("aria-label", t(sendKey));
    send.title = t(sendKey);
  }
  if (files) {
    files.disabled = !canSend;
  }
  if (fileLabel) {
    fileLabel.classList.toggle("disabled", !canSend);
    fileLabel.setAttribute("aria-disabled", canSend ? "false" : "true");
  }
  updateChatSyncApprovalCard(syncRequest);
  ensureChatSyncApprovalRequest(runner);
}

async function copyRuntimeCommand() {
  const command = document.querySelector("#runtime-command")?.textContent || "";
  const button = document.querySelector("#runtime-copy-command");
  if (!command || !navigator.clipboard?.writeText) {
    if (button) button.textContent = t("copyCommandFailed");
    return;
  }
  try {
    await navigator.clipboard.writeText(command);
    if (button) button.textContent = t("copiedCommand");
  } catch {
    if (button) button.textContent = t("copyCommandFailed");
  }
}

function stopBridgeActivationMonitor() {
  if (bridgeActivationMonitor) clearTimeout(bridgeActivationMonitor);
  bridgeActivationMonitor = null;
  bridgeActivationDeadline = 0;
}

async function monitorBridgeActivation() {
  if (!bridgeActivationDeadline) bridgeActivationDeadline = Date.now() + 30000;
  if (bridgeActivationMonitor) clearTimeout(bridgeActivationMonitor);
  try {
    await loadRuntimeStatus();
    const runner = cachedRuntimeStatus?.chat_runner || {};
    if (runner.tui_bridge_active) {
      stopBridgeActivationMonitor();
      setStatus(t("runtimeModeAttached"), t("restartBridgeActivated"), "tui_bridge_active");
      return;
    }
    if (Date.now() >= bridgeActivationDeadline) {
      stopBridgeActivationMonitor();
      setStatus(
        t("runtimeModeLegacyRelay"),
        t("restartBridgeStillWaiting"),
        "legacy_tui_relay",
        runner.restart_command || "",
        "enableCurrentSessionSync",
        runnerCanRestartCurrentConsole(runner)
      );
      return;
    }
    setStatus(
      t("restartBridgeStarted"),
      t("restartBridgeChecking"),
      "waiting_for_tui_bridge",
      runner.restart_command || "",
      "enableCurrentSessionSync",
      runnerCanRestartCurrentConsole(runner)
    );
  } catch {
    setStatus(t("restartBridgeStarted"), t("restartBridgeChecking"), "waiting_for_tui_bridge", "", "enableCurrentSessionSync");
  }
  bridgeActivationMonitor = setTimeout(monitorBridgeActivation, 1200);
}

async function ensureChatSyncApprovalRequest(runner) {
  if (!cachedPairingAuthenticated) return;
  if (!runnerCanRestartCurrentConsole(runner) || !runnerNeedsCurrentSessionSync(runner)) return;
  if (pendingConsoleRestartRequest()) return;
  const now = Date.now();
  if (autoSyncRequestInFlight || now - autoSyncRequestLastAt < AUTO_SYNC_REQUEST_COOLDOWN_MS) return;
  autoSyncRequestInFlight = true;
  autoSyncRequestLastAt = now;
  try {
    const response = await signedFetch("/api/console/restart-bridge/request", {
      method: "POST",
      headers: { "content-type": "application/json", ...csrfHeaders() },
      body: "{}"
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || "restart request failed");
    upsertCachedRequest(payload.request);
    renderRequestList(cachedRequests);
    updateChatSessionStatus(runner);
  } catch {
    autoSyncRequestLastAt = Date.now();
  } finally {
    autoSyncRequestInFlight = false;
  }
}

async function requestConsoleRestartApproval({ renew = false } = {}) {
  const buttons = [
    document.querySelector("#runtime-restart-bridge"),
    document.querySelector("#chat-session-restart")
  ].filter(Boolean);
  buttons.forEach((button) => {
    button.disabled = true;
  });
  try {
    if (renew) {
      setStatus(t("syncApprovalRenewing"), "", "waiting_for_tui_bridge", "", "enableCurrentSessionSync");
    }
    const response = await signedFetch("/api/console/restart-bridge/request", {
      method: "POST",
      headers: { "content-type": "application/json", ...csrfHeaders() },
      body: "{}"
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || "restart request failed");
    setStatus(
      t(renew ? "syncApprovalRenewed" : "restartBridgeApprovalRequested"),
      t("restartBridgeApprovalRequestedDetail"),
      "waiting_for_tui_bridge",
      "",
      "enableCurrentSessionSync"
    );
    await loadRequests();
    openPendingSyncRequest();
    return payload;
  } catch {
    stopBridgeActivationMonitor();
    setStatus(t("restartBridgeFailed"), t("runtimeWaitingForConsoleRestart"), "waiting_for_tui_bridge");
  } finally {
    buttons.forEach((button) => {
      button.disabled = false;
    });
  }
}

async function restartConsoleBridge() {
  const request = pendingConsoleRestartRequest();
  if (request && !syncRequestNeedsRefresh(request)) {
    openPendingSyncRequest();
    return;
  }
  await requestConsoleRestartApproval({ renew: Boolean(request) });
}

function displayValue(value, fallback = "pending") {
  if (value === undefined || value === null || value === "") return fallback;
  if (Array.isArray(value)) return value.map((item) => displayValue(item, "")).filter(Boolean).join(", ") || fallback;
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function setFieldText(selector, value, fallback = "pending") {
  const node = document.querySelector(selector);
  if (node) node.textContent = displayValue(value, fallback);
}

function storedPairingIdentity() {
  return {
    deviceId: localStorage.getItem("omnidoer_device_id") || "",
    sessionId: localStorage.getItem("omnidoer_session_id") || "",
    hasPrivateKey: Boolean(localStorage.getItem("omnidoer_device_private_jwk"))
  };
}

function setPairingUiState({ state, message, deviceText = "", forceStatus = false }) {
  const panel = document.querySelector("#pairing-panel");
  const status = document.querySelector("#pairing-status");
  const currentDevice = document.querySelector("#pairing-current-device");
  const forgetButton = document.querySelector("#forget-local-pairing");
  if (panel) panel.dataset.pairingState = state;
  const holdSuccessStatus = pairingSuccessHoldUntil > Date.now() && pairingSuccessMessage && !forceStatus;
  if (status) status.textContent = holdSuccessStatus ? pairingSuccessMessage : message;
  if (currentDevice) currentDevice.textContent = deviceText || t("notPaired");
  if (forgetButton) {
    const identity = storedPairingIdentity();
    forgetButton.disabled = !identity.deviceId && !identity.sessionId && !identity.hasPrivateKey;
  }
}

function isTakeoverRequest(request) {
  return request && (request.request_type === "human_takeover" || request.request_type === "account_registration");
}

function findActiveTakeoverRequest(requests) {
  return requests.find((request) => isTakeoverRequest(request) && request.status === "user_control") || null;
}

function activeTakeoverRequest() {
  return cachedRequests.find((request) => request.request_id === activeTakeoverFrameRequest) || findActiveTakeoverRequest(cachedRequests);
}

function activeBrowserContext() {
  return cachedBrowserContexts.find((context) => context.active && context.current_url) || null;
}

function takeoverFrameAgeMs(stream = document.querySelector("#browser-stream")) {
  const capturedAt = Number(stream?.dataset.frameCapturedAt || 0);
  if (!capturedAt) return null;
  return Math.max(0, Date.now() - capturedAt * 1000);
}

function takeoverFrameIsFresh(stream = document.querySelector("#browser-stream")) {
  const age = takeoverFrameAgeMs(stream);
  return age !== null && age <= TAKEOVER_FRAME_MAX_AGE_MS;
}

function takeoverFrameProfile() {
  const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  if (connection?.saveData) return TAKEOVER_FRAME_PROFILE_DATA_SAVER;
  const effectiveType = connection?.effectiveType || "";
  if (["slow-2g", "2g"].includes(effectiveType)) return TAKEOVER_FRAME_PROFILE_DATA_SAVER;
  return TAKEOVER_FRAME_PROFILE_DEFAULT;
}

function takeoverFrameQuery(extra = {}) {
  const params = new URLSearchParams({ profile: takeoverFrameProfile() });
  Object.entries(extra).forEach(([key, value]) => params.set(key, String(value)));
  return params.toString();
}

function takeoverFrameProfileLabel(frame = null) {
  const transport = frame?.transport || {};
  const profile = transport.profile || takeoverFrameProfile();
  const contentType = transport.content_type || frame?.content_type || "";
  const quality = transport.quality;
  const qualityLabel = quality === undefined || quality === null ? "" : ` q${quality}`;
  const typeLabel = contentType.replace("image/", "") || "frame";
  return `${profile.replaceAll("_", " ")} ${typeLabel}${qualityLabel}`;
}

function updateTakeoverFrameFreshness(stream = document.querySelector("#browser-stream")) {
  const field = document.querySelector("#takeover-frame-freshness");
  if (!field) return;
  const frameId = stream?.dataset.frameId || "";
  const age = takeoverFrameAgeMs(stream);
  if (!frameId || age === null) {
    field.textContent = t("takeoverFrameWaiting");
    field.className = "";
    return;
  }
  const seconds = Math.round(age / 1000);
  const stale = age > TAKEOVER_FRAME_MAX_AGE_MS;
  field.textContent = stale ? t("takeoverFrameStale", seconds) : t("takeoverFrameFresh", seconds);
  field.className = stale ? "frame-stale" : "frame-fresh";
}

function updateTakeoverFrameConnection(state, message) {
  const field = document.querySelector("#takeover-frame-connection");
  if (!field) return;
  field.textContent = message;
  field.className = state ? `frame-${state}` : "";
}

function takeoverIsActive() {
  const request = activeTakeoverRequest();
  return Boolean(request && request.status === "user_control");
}

function takeoverHasVisibleFrame(stream = document.querySelector("#browser-stream")) {
  return Boolean(stream?.querySelector("#takeover-frame") && stream.dataset.frameId);
}

function updateTakeoverZoomControls() {
  const isActive = takeoverIsActive();
  const hasFrame = takeoverHasVisibleFrame();
  const zoomed = takeoverFrameZoom > TAKEOVER_ZOOM_MIN;
  const zoomOut = document.querySelector("#zoom-out-takeover-frame");
  const zoomReset = document.querySelector("#zoom-reset-takeover-frame");
  const zoomIn = document.querySelector("#zoom-in-takeover-frame");
  const pan = document.querySelector("#pan-takeover-frame");
  if (!isActive && !hasFrame) takeoverFramePanMode = false;
  if (zoomOut) zoomOut.disabled = !hasFrame || !zoomed;
  if (zoomReset) zoomReset.disabled = !hasFrame || (!zoomed && !takeoverFramePanMode);
  if (zoomIn) zoomIn.disabled = !hasFrame || takeoverFrameZoom >= TAKEOVER_ZOOM_MAX;
  if (pan) {
    pan.disabled = !hasFrame || !zoomed;
    pan.textContent = takeoverFramePanMode ? t("takeoverPanOn") : t("takeoverPanView");
    pan.setAttribute("aria-pressed", takeoverFramePanMode ? "true" : "false");
  }
}

function updateActiveTakeoverTextControls() {
  const disabled = !takeoverIsActive() || agentControlBusy;
  const input = document.querySelector("#active-takeover-text");
  const sendText = document.querySelector("#send-active-takeover-text");
  const sendEnter = document.querySelector("#send-active-takeover-enter");
  if (input) input.disabled = disabled;
  if (sendText) sendText.disabled = disabled;
  if (sendEnter) sendEnter.disabled = disabled;
}

function applyTakeoverFrameZoom(stream = document.querySelector("#browser-stream")) {
  const image = stream?.querySelector("#takeover-frame") || document.querySelector("#takeover-frame");
  const zoomPercent = Math.round(takeoverFrameZoom * 100);
  const zoomed = takeoverFrameZoom > TAKEOVER_ZOOM_MIN;
  if (stream) {
    stream.classList.toggle("frame-zoomed", zoomed);
    stream.classList.toggle("view-pan", takeoverFramePanMode && zoomed);
  }
  if (image) {
    image.style.width = zoomed ? `${zoomPercent}%` : "";
    image.style.maxWidth = zoomed ? "none" : "100%";
  }
  setFieldText("#takeover-frame-zoom", `${zoomPercent}%${takeoverFramePanMode ? t("takeoverPanSuffix") : ""}`);
  updateTakeoverZoomControls();
}

function setTakeoverFrameZoom(value) {
  const nextZoom = Math.min(TAKEOVER_ZOOM_MAX, Math.max(TAKEOVER_ZOOM_MIN, value));
  takeoverFrameZoom = Math.round(nextZoom / TAKEOVER_ZOOM_STEP) * TAKEOVER_ZOOM_STEP;
  if (takeoverFrameZoom <= TAKEOVER_ZOOM_MIN) takeoverFramePanMode = false;
  applyTakeoverFrameZoom();
}

function setTakeoverFramePanMode(enabled) {
  takeoverFramePanMode = Boolean(enabled) && takeoverFrameZoom > TAKEOVER_ZOOM_MIN;
  applyTakeoverFrameZoom();
}

function resetTakeoverFrameView() {
  takeoverFrameZoom = TAKEOVER_ZOOM_MIN;
  takeoverFramePanMode = false;
  applyTakeoverFrameZoom();
}

function updateTakeoverPanel(request, frame = null, message = null) {
  const status = request ? (request.status === "user_control" ? t("takeoverAgentPausedStatus") : displayStatus(request.status)) : t("takeoverNoActive");
  setFieldText("#takeover-status-label", status);
  setFieldText("#takeover-active-request", request?.request_id, displayStatus("pending"));
  setFieldText("#takeover-current-url", request?.top_level_url || request?.origin, displayStatus("pending"));
  if (frame) {
    setFieldText("#takeover-frame-meta", frame.url || frame.origin || request?.top_level_url, t("takeoverFrameWaiting"));
    setFieldText("#takeover-frame-profile", takeoverFrameProfileLabel(frame), t("takeoverFrameAdaptive"));
  } else {
    setFieldText("#takeover-frame-meta", request ? t("takeoverFrameNextWaiting") : t("takeoverFrameWaiting"));
    setFieldText("#takeover-frame-profile", request ? takeoverFrameProfileLabel() : t("takeoverFrameAdaptive"), t("takeoverFrameAdaptive"));
  }
  setFieldText("#takeover-input-state", message || (request ? t("takeoverInputStateActive") : t("noActiveBrowserHandoff")), "");
  updateTakeoverFrameFreshness();
  const isActive = Boolean(request && request.status === "user_control");
  const refresh = document.querySelector("#refresh-takeover-frame");
  const release = document.querySelector("#release-active-takeover");
  updateAgentControlButtons();
  if (refresh) refresh.disabled = !isActive;
  if (release) release.disabled = !isActive || agentControlBusy;
  updateActiveTakeoverTextControls();
  updateTakeoverZoomControls();
}

function syncTakeoverPanel(requests) {
  const stream = document.querySelector("#browser-stream");
  const request = findActiveTakeoverRequest(requests);
  const context = activeBrowserContext();
  updateBrowserHandoffState(request, context);
  maybeAutoOpenTakeoverPanel(request, context);
  if (!stream) return;
  if (!request) {
    stopTakeoverFramePolling();
    updateTakeoverPanel(null);
    if (context) {
      setFieldText("#takeover-current-url", context.current_url || context.origin, displayStatus("pending"));
      setFieldText("#takeover-frame-meta", context.browser_context_id, t("takeoverFrameWaiting"));
      setFieldText("#takeover-input-state", t("activeBrowserReady"), "");
      startBrowserPreviewPolling(context, stream);
    } else {
      stopBrowserPreviewPolling();
      stream.textContent = t("noActiveBrowserHandoff");
    }
    return;
  }
  stopBrowserPreviewPolling();
  updateTakeoverPanel(request);
  startTakeoverFramePolling(request, stream);
}

function maybeAutoOpenTakeoverPanel(request, context = null) {
  if (request && request.status === "user_control") {
    if (autoOpenedTakeoverRequestId === request.request_id) return;
    autoOpenedTakeoverRequestId = request.request_id;
    activatePanel("takeover-panel", { persist: false });
    return;
  }
  if (!context?.browser_context_id || !context.active || !context.current_url) return;
  if (autoOpenedPreviewContextId === context.browser_context_id) return;
  autoOpenedPreviewContextId = context.browser_context_id;
  activatePanel("takeover-panel", { persist: false });
}

function stopBrowserPreviewPolling() {
  if (browserPreviewTimer) clearInterval(browserPreviewTimer);
  browserPreviewTimer = null;
  closeBrowserPreviewWebSocket();
  activeBrowserPreviewContext = null;
}

async function fetchBrowserContextFrame(context, stream) {
  if (!context?.browser_context_id || !stream || document.hidden || activeBrowserPreviewContext !== context.browser_context_id) return;
  try {
    const response = await signedFetch(`/api/browser/contexts/${encodeURIComponent(context.browser_context_id)}/frame?${takeoverFrameQuery()}`, { cache: "no-store" });
    if (!response.ok) throw new Error("preview unavailable");
    const frame = await response.json();
    renderTakeoverFrame(null, stream, frame, t("activeBrowserPreview"));
  } catch {
    if (!stream.querySelector("#takeover-frame")) {
      stream.textContent = t("activeBrowserPreviewWaiting");
    }
    updateTakeoverFrameConnection("reconnecting", t("activeBrowserPreviewWaiting"));
  }
}

function closeBrowserPreviewWebSocket() {
  if (browserPreviewSocketRestart) clearTimeout(browserPreviewSocketRestart);
  browserPreviewSocketRestart = null;
  if (browserPreviewSocket) {
    browserPreviewSocket.onclose = null;
    browserPreviewSocket.onerror = null;
    browserPreviewSocket.onmessage = null;
    browserPreviewSocket.close();
  }
  browserPreviewSocket = null;
  browserPreviewSocketContext = null;
}

function restartBrowserPreviewWebSocket(context, stream) {
  if (browserPreviewSocketRestart || document.hidden) return;
  browserPreviewSocketRestart = setTimeout(() => {
    browserPreviewSocketRestart = null;
    if (activeBrowserPreviewContext === context.browser_context_id && stream) {
      startBrowserPreviewWebSocket(context, stream);
    }
  }, 3000);
}

async function startBrowserPreviewWebSocket(context, stream) {
  if (!window.WebSocket || document.hidden || !context?.browser_context_id || !stream) return false;
  if (
    browserPreviewSocket
    && browserPreviewSocketContext === context.browser_context_id
    && [WebSocket.CONNECTING, WebSocket.OPEN].includes(browserPreviewSocket.readyState)
  ) {
    return true;
  }
  closeBrowserPreviewWebSocket();
  const path = `/api/ws/browser/contexts/${encodeURIComponent(context.browser_context_id)}/frames`;
  try {
    const protocol = await deviceAuthSubprotocol("GET", path);
    const target = `${path}?${takeoverFrameQuery({ snapshots: TAKEOVER_FRAME_WS_SNAPSHOTS, interval: TAKEOVER_FRAME_WS_INTERVAL_SECONDS })}`;
    const socket = protocol ? new WebSocket(websocketUrl(target), [protocol]) : new WebSocket(websocketUrl(target));
    browserPreviewSocket = socket;
    browserPreviewSocketContext = context.browser_context_id;
    socket.onopen = () => {
      if (activeBrowserPreviewContext !== context.browser_context_id) {
        closeBrowserPreviewWebSocket();
        return;
      }
      if (browserPreviewTimer) clearInterval(browserPreviewTimer);
      browserPreviewTimer = null;
      updateTakeoverFrameConnection("connected", t("takeoverConnectedWebSocket"));
    };
    socket.onmessage = (event) => {
      if (activeBrowserPreviewContext !== context.browser_context_id) return;
      const payload = JSON.parse(event.data);
      if (payload.event === "browser_context_frame" && payload.browser_context_id === context.browser_context_id) {
        if (payload.data?.data_b64) {
          renderTakeoverFrame(null, stream, payload.data, t("activeBrowserPreview"));
        } else if (!stream.querySelector("#takeover-frame")) {
          stream.textContent = t("activeBrowserPreviewWaiting");
        }
      }
    };
    socket.onerror = () => {
      socket.close();
    };
    socket.onclose = () => {
      if (browserPreviewSocket === socket) {
        browserPreviewSocket = null;
        browserPreviewSocketContext = null;
      }
      if (activeBrowserPreviewContext === context.browser_context_id && !document.hidden) {
        updateTakeoverFrameConnection("reconnecting", t("activeBrowserPreviewWaiting"));
        fetchBrowserContextFrame(context, stream);
        if (!browserPreviewTimer) {
          browserPreviewTimer = setInterval(() => fetchBrowserContextFrame(context, stream), BROWSER_PREVIEW_POLL_MS);
        }
        restartBrowserPreviewWebSocket(context, stream);
      }
    };
    return true;
  } catch {
    closeBrowserPreviewWebSocket();
    return false;
  }
}

function startBrowserPreviewPolling(context, stream) {
  if (!context?.browser_context_id || !stream) return;
  if (activeBrowserPreviewContext !== context.browser_context_id) {
    stopBrowserPreviewPolling();
    activeBrowserPreviewContext = context.browser_context_id;
    stream.textContent = t("activeBrowserPreviewWaiting");
    startBrowserPreviewWebSocket(context, stream).then((started) => {
      if (!started && activeBrowserPreviewContext === context.browser_context_id) {
        fetchBrowserContextFrame(context, stream);
        if (!browserPreviewTimer) {
          browserPreviewTimer = setInterval(() => fetchBrowserContextFrame(context, stream), BROWSER_PREVIEW_POLL_MS);
        }
      }
    });
    return;
  }
  if (!browserPreviewSocket && !browserPreviewTimer) {
    startBrowserPreviewWebSocket(context, stream).then((started) => {
      if (!started && activeBrowserPreviewContext === context.browser_context_id && !browserPreviewTimer) {
        browserPreviewTimer = setInterval(() => fetchBrowserContextFrame(context, stream), BROWSER_PREVIEW_POLL_MS);
      }
    });
  }
}

function refreshActiveTakeoverFrame() {
  const request = activeTakeoverRequest();
  const stream = document.querySelector("#browser-stream");
  if (!request || !stream) return;
  fetchTakeoverFrame(request, stream);
}

function scheduleTakeoverFrameRefresh(request = activeTakeoverRequest(), delayMs = 0) {
  const stream = document.querySelector("#browser-stream");
  if (!request || !stream || request.status !== "user_control" || document.hidden) return;
  if (takeoverFrameRefreshTimer) clearTimeout(takeoverFrameRefreshTimer);
  takeoverFrameRefreshTimer = setTimeout(() => {
    takeoverFrameRefreshTimer = null;
    fetchTakeoverFrame(request, stream);
  }, delayMs);
}

async function releaseActiveTakeover() {
  const request = activeTakeoverRequest();
  if (!request) return;
  setPauseButtonsDisabled(true);
  try {
    const actionResponse = await postAction(request, "release");
    if (!actionResponse?.ok) throw new Error("release failed");
    const payload = await actionResponse.json().catch(() => ({}));
    stopTakeoverFramePolling(request.request_id);
    await loadBrowserContexts();
    if (!payload.agent_continue || payload.agent_continue.error) {
      const clientMessageId = `control_continue_${Date.now()}_${Math.random().toString(16).slice(2)}`;
      const response = await postChatMessage(t("takeoverReleasePrompt"), { clientMessageId });
      if (!response.ok) throw new Error("continue message failed");
    }
    await loadChatMessages();
    setStatus(t("takeoverReleased"), t("takeoverReleasedDetail"));
    activatePanel("task-panel", { persist: false });
  } catch {
    setStatus(t("actionFailed"), t("releaseControl"));
  } finally {
    setPauseButtonsDisabled(false);
  }
}

function renderTakeoverFrame(request, stream, frame, message = null) {
  if (!frame.data_b64) {
    markTakeoverFrameReconnect(request, stream, t("takeoverDisconnected"));
    return;
  }
  const image = document.createElement("img");
  image.id = "takeover-frame";
  image.alt = t("controlledBrowserFrameAlt");
  image.src = `data:${frame.content_type};base64,${frame.data_b64}`;
  image.dataset.frameId = frame.frame_id || "";
  image.dataset.frameCapturedAt = frame.captured_at || "";
  stream.replaceChildren(image);
  stream.dataset.frameId = frame.frame_id || "";
  stream.dataset.frameCapturedAt = frame.captured_at || "";
  stream.dataset.frameUrl = frame.url || "";
  stream.dataset.frameOrigin = frame.origin || "";
  stream.dataset.frameProfile = frame.transport?.profile || takeoverFrameProfile();
  stream.dataset.frameContentType = frame.transport?.content_type || frame.content_type || "";
  takeoverFrameMisses = 0;
  takeoverFrameVisibilityPaused = false;
  stream.classList.remove("frame-reconnecting");
  applyTakeoverFrameZoom(stream);
  updateTakeoverFrameConnection("connected", t("takeoverConnected"));
  updateTakeoverPanel(request, frame, message || t("takeoverFrameReady"));
  updateTakeoverFrameFreshness(stream);
}

function detailValue(details, ...keys) {
  for (const key of keys) {
    if (details[key] !== undefined && details[key] !== null && details[key] !== "") {
      return details[key];
    }
  }
  return "";
}

function findCurrentPaymentApproval(requests) {
  return requests.find((request) => request.request_type === "payment_approval" && request.status === "pending")
    || requests.find((request) => request.request_type === "payment_approval")
    || null;
}

function explicitApprovalConfirmationPayload(request) {
  return {
    explicit_user_confirmation: true,
    request_id: request.request_id,
    confirmed_at: new Date().toISOString()
  };
}

function paymentApprovalConfirmationPayload(request) {
  return explicitApprovalConfirmationPayload(request);
}

function updatePaymentApprovalButtons() {
  const confirm = document.querySelector("#approval-confirm");
  const approve = document.querySelector("#approve");
  const deny = document.querySelector("#deny");
  const active = Boolean(activePaymentApprovalRequest && activePaymentApprovalRequest.status === "pending");
  if (confirm) confirm.disabled = !active;
  if (deny) deny.disabled = !active;
  if (approve) approve.disabled = !active || !confirm?.checked;
}

function updatePaymentApprovalPanel(requests) {
  const request = findCurrentPaymentApproval(requests);
  activePaymentApprovalRequest = request && request.status === "pending" ? request : null;
  const details = request?.structured_details || {};
  setFieldText("#merchant", detailValue(details, "merchant"));
  setFieldText("#amount", detailValue(details, "amount"));
  setFieldText("#currency", detailValue(details, "currency"));
  setFieldText("#origin", detailValue(details, "origin") || request?.origin);
  setFieldText("#recipient", detailValue(details, "recipient", "payee"));
  setFieldText("#shipping-address", detailValue(details, "shipping_address"));
  setFieldText("#billing-method-summary", detailValue(details, "billing_method_summary"));
  setFieldText("#subscription-renewal", detailValue(details, "subscription", "renewal"));
  setFieldText("#refund-terms", detailValue(details, "refund_terms", "cancellation_terms"));
  setFieldText("#final-button", detailValue(details, "final_button"));
  setFieldText("#review-fingerprint", request?.approval_fingerprint);
  setFieldText("#after-approval", detailValue(details, "after_approval") || (request ? "Submit only after approval" : ""));
  setFieldText("#approval-status", request ? `${request.status}: ${request.action_summary || request.request_id}` : t("noPendingPayment"), "");
  const confirm = document.querySelector("#approval-confirm");
  if (confirm && renderedPaymentApprovalRequestId !== request?.request_id) confirm.checked = false;
  renderedPaymentApprovalRequestId = request?.request_id || null;
  if (!activePaymentApprovalRequest && confirm) confirm.checked = false;
  updatePaymentApprovalButtons();
}

function approveActivePaymentRequest() {
  if (!activePaymentApprovalRequest) return;
  const confirm = document.querySelector("#approval-confirm");
  if (!confirm?.checked) {
    setStatus(t("paymentReviewRequired"), t("paymentReviewRequiredDetail"));
    updatePaymentApprovalButtons();
    return;
  }
  postAction(activePaymentApprovalRequest, "approve", paymentApprovalConfirmationPayload(activePaymentApprovalRequest));
}

function denyActivePaymentRequest() {
  if (!activePaymentApprovalRequest) return;
  postAction(activePaymentApprovalRequest, "deny");
}

async function loadPairingDetails(pairingId) {
  document.querySelector("#pairing-server-url").textContent = window.location.origin;
  try {
    const response = await fetch(`/api/pairing/${encodeURIComponent(pairingId)}`, { cache: "no-store" });
    if (!response.ok) throw new Error("pairing unavailable");
    const pairing = await response.json();
    document.querySelector("#pairing-server-url").textContent = pairing.public_url || window.location.origin;
    document.querySelector("#pairing-broker-fingerprint").textContent = pairing.broker_fingerprint || "not loaded";
    document.querySelector("#pairing-web-broker-fingerprint").textContent = pairing.web_broker_fingerprint || "not loaded";
    document.querySelector("#pairing-expires-at").textContent = formatTimestamp(pairing.expires_at);
    document.querySelector("#pairing-remaining-uses").textContent = `${pairing.remaining_uses ?? "?"} / ${pairing.max_uses ?? "?"}`;
  } catch {
    document.querySelector("#pairing-broker-fingerprint").textContent = "pairing metadata unavailable";
    document.querySelector("#pairing-web-broker-fingerprint").textContent = "pairing metadata unavailable";
    document.querySelector("#pairing-remaining-uses").textContent = "pairing metadata unavailable";
  }
}

async function deviceKeyPair() {
  const storedPrivate = localStorage.getItem("omnidoer_device_private_jwk");
  const storedPublic = localStorage.getItem("omnidoer_device_public_jwk");
  if (storedPrivate && storedPublic) {
    const privateJwk = JSON.parse(storedPrivate);
    const privateKey = await crypto.subtle.importKey(
      "jwk",
      privateJwk,
      { name: "ECDSA", namedCurve: "P-256" },
      true,
      ["sign"]
    );
    return { publicJwk: JSON.parse(storedPublic), privateKey };
  }
  const key = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
  const privateJwk = await crypto.subtle.exportKey("jwk", key.privateKey);
  const publicJwk = await crypto.subtle.exportKey("jwk", key.publicKey);
  localStorage.setItem("omnidoer_device_private_jwk", JSON.stringify(privateJwk));
  localStorage.setItem("omnidoer_device_public_jwk", JSON.stringify(publicJwk));
  return { publicJwk, privateKey: key.privateKey };
}

function withTimeout(promise, timeoutMs, message) {
  let timeoutId = null;
  const timeout = new Promise((_, reject) => {
    timeoutId = setTimeout(() => reject(new Error(message)), timeoutMs);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timeoutId));
}

async function deviceSignatureHeaders(method, path) {
  const deviceId = localStorage.getItem("omnidoer_device_id");
  const sessionId = localStorage.getItem("omnidoer_session_id");
  const storedPrivate = localStorage.getItem("omnidoer_device_private_jwk");
  if (!deviceId || !sessionId || !storedPrivate) return {};
  const { privateKey } = await deviceKeyPair();
  const timestamp = String(Math.floor(Date.now() / 1000));
  const nonce = bytesToB64url(crypto.getRandomValues(new Uint8Array(16)));
  const message = [
    "omnidoer-device-v1",
    deviceId,
    sessionId,
    method.toUpperCase(),
    path,
    timestamp,
    nonce
  ].join("\n");
  const signature = await crypto.subtle.sign(
    { name: "ECDSA", hash: "SHA-256" },
    privateKey,
    encoder.encode(message)
  );
  return {
    "x-omnidoer-device-id": deviceId,
    "x-omnidoer-device-ts": timestamp,
    "x-omnidoer-device-nonce": nonce,
    "x-omnidoer-device-sig": bytesToB64url(signature)
  };
}

function pairingFailureMessage(error, fallbackReason = "") {
  const value = `${error || ""} ${fallbackReason || ""}`.toLowerCase();
  if (value.includes("expired") || value.includes("pairing_code_expired")) return t("pairingExpired");
  if (value.includes("already used") || value.includes("pairing_code_used")) return t("pairingAlreadyUsed");
  if (value.includes("invalid") || value.includes("pairing_code_invalid")) return t("pairingInvalid");
  return t("pairingFailedDetail", fallbackReason || error || t("pairingFailed"));
}

async function deviceAuthSubprotocol(method, path) {
  const headers = await deviceSignatureHeaders(method, path);
  if (!headers["x-omnidoer-device-id"]) return "";
  const payload = {
    device_id: headers["x-omnidoer-device-id"],
    timestamp: headers["x-omnidoer-device-ts"],
    nonce: headers["x-omnidoer-device-nonce"],
    signature: headers["x-omnidoer-device-sig"]
  };
  return `omnidoer-v1.${b64url(encoder.encode(JSON.stringify(payload)))}`;
}

async function signedFetch(url, options = {}) {
  const target = new URL(url, window.location.origin);
  const method = (options.method || "GET").toUpperCase();
  const headers = {
    ...(options.headers || {}),
    ...(await deviceSignatureHeaders(method, target.pathname))
  };
  return fetch(url, { ...options, method, headers });
}

async function pairDevice() {
  const code = document.querySelector("#pairing-code").value.trim();
  const deviceName = document.querySelector("#device-name").value.trim() || "PWA Control Client";
  if (!code) return;
  setPairingUiState({ state: "checking", message: t("pairingDevice") });
  try {
    const { publicJwk } = await withTimeout(deviceKeyPair(), PAIRING_STEP_TIMEOUT_MS, "device key setup timed out");
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), PAIRING_STEP_TIMEOUT_MS);
    const response = await fetch("/api/pair", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ code, device_name: deviceName, device_public_key: JSON.stringify(publicJwk) }),
      signal: controller.signal
    }).finally(() => clearTimeout(timeoutId));
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(pairingFailureMessage(payload.error, payload.reason));
    }
    localStorage.setItem("omnidoer_device_id", payload.device.device_id);
    localStorage.setItem("omnidoer_session_id", payload.session.session_id);
    localStorage.setItem("omnidoer_csrf_token", payload.csrf_token);
    pairingSuccessMessage = t("pairedDevice", payload.device.name);
    pairingSuccessHoldUntil = Date.now() + 6000;
    cachedPairingAuthenticated = true;
    setPairingUiState({
      state: "paired",
      message: pairingSuccessMessage,
      deviceText: `${payload.device.device_id} - ${t("sessionValidUntil", formatTimestamp(payload.session.expires_at))}`,
      forceStatus: true
    });
    await loadRuntimeStatus();
    await refreshAuthenticatedData();
    startAuthenticatedRealtime();
  } catch (error) {
    pairingSuccessHoldUntil = 0;
    pairingSuccessMessage = "";
    const reason = error?.name === "AbortError" ? "request timed out" : (error?.message || t("pairingFailed"));
    setPairingUiState({ state: "stale", message: reason });
  }
}

async function autoPairFromInitialLink() {
  if (!initialPairingCode || autoPairingStarted) return;
  autoPairingStarted = true;
  try {
    await refreshPairingState();
    if (cachedPairingAuthenticated) return;
    await pairDevice();
  } catch {
    document.querySelector("#pairing-status").textContent = t("pairingFailed");
  }
}

function forgetLocalPairing() {
  pairingSuccessHoldUntil = 0;
  pairingSuccessMessage = "";
  [
    "omnidoer_device_id",
    "omnidoer_session_id",
    "omnidoer_csrf_token",
    "omnidoer_device_private_jwk",
    "omnidoer_device_public_jwk"
  ].forEach((key) => localStorage.removeItem(key));
  cachedRequests = [];
  renderRequestList([]);
  setPairingUiState({
    state: "unpaired",
    message: t("localPairingRemoved")
  });
  const devicesRoot = document.querySelector("#devices-list");
  const sessionsRoot = document.querySelector("#sessions-list");
  if (devicesRoot) devicesRoot.textContent = t("pairToViewDevices");
  if (sessionsRoot) sessionsRoot.textContent = t("pairToViewSessions");
  updateOverview();
}

function b64url(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes))).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

function stableAssociatedData(request) {
  const data = {
    origin: request.origin,
    request_id: request.request_id,
    request_type: request.request_type
  };
  if (request.device_id) data.device_id = request.device_id;
  if (request.expires_at) data.expires_at = request.expires_at;
  const sorted = Object.keys(data).sort().reduce((acc, key) => {
    acc[key] = data[key];
    return acc;
  }, {});
  return encoder.encode(JSON.stringify(sorted));
}

async function deriveAesKey(sharedBits, request) {
  const hkdfBase = await crypto.subtle.importKey("raw", sharedBits, "HKDF", false, ["deriveKey"]);
  const salt = await crypto.subtle.digest("SHA-256", stableAssociatedData(request));
  return crypto.subtle.deriveKey(
    { name: "HKDF", hash: "SHA-256", salt, info: encoder.encode("omnidoer-control-web-v1") },
    hkdfBase,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt"]
  );
}

async function encryptForBroker(payload, request) {
  const requestForAad = {
    ...request,
    device_id: localStorage.getItem("omnidoer_device_id") || undefined,
    expires_at: request.expires_at
  };
  const broker = await signedFetch("/api/broker-key", { cache: "no-store" }).then((r) => r.json());
  const brokerKey = await crypto.subtle.importKey(
    "jwk",
    broker.web_public_jwk,
    { name: "ECDH", namedCurve: "P-256" },
    false,
    []
  );
  const ephemeral = await crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
  const sharedBits = await crypto.subtle.deriveBits({ name: "ECDH", public: brokerKey }, ephemeral.privateKey, 256);
  const key = await deriveAesKey(sharedBits, requestForAad);
  const nonce = crypto.getRandomValues(new Uint8Array(12));
  const aad = stableAssociatedData(requestForAad);
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: nonce, additionalData: aad },
    key,
    encoder.encode(JSON.stringify(payload))
  );
  return {
    version: "web-p256-v1",
    ephemeral_public_jwk: await crypto.subtle.exportKey("jwk", ephemeral.publicKey),
    nonce: b64url(nonce),
    ciphertext: b64url(ciphertext),
    request_id: request.request_id,
    origin: request.origin,
    request_type: request.request_type,
    device_id: requestForAad.device_id,
    expires_at: requestForAad.expires_at
  };
}

async function submitEncrypted(request, payload) {
  const envelope = await encryptForBroker(payload, request);
  const response = await signedFetch(`/api/requests/${request.request_id}/submit`, {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify({ envelope })
  });
  if (!response.ok) {
    setStatus(t("requestSubmitFailed"), t("requestSubmitFailedDetail"));
  }
  await loadRequests();
}

async function postAction(request, action, payload = null) {
  const headers = payload ? { "content-type": "application/json", ...csrfHeaders() } : csrfHeaders();
  const options = { method: "POST", headers };
  if (payload) options.body = JSON.stringify(payload);
  const response = await signedFetch(`/api/requests/${request.request_id}/${action}`, options);
  if (!response.ok) {
    setStatus(t("actionFailed"), `${request.request_type} ${action}`);
  } else if (request.request_type === "console_restart" && action === "approve") {
    setStatus(t("restartBridgeStarted"), t("restartBridgeChecking"), "waiting_for_tui_bridge", "", "enableCurrentSessionSync");
    stopBridgeActivationMonitor();
    bridgeActivationDeadline = Date.now() + 30000;
    bridgeActivationMonitor = setTimeout(monitorBridgeActivation, 1200);
  }
  await loadRequests();
  return response;
}

async function approvePendingSyncRequestFromChat() {
  const request = pendingConsoleRestartRequest();
  const confirm = document.querySelector("#chat-sync-approval-confirm");
  if (!request) return;
  if (requestExpiresInMs(request) <= 0) {
    setStatus(t("syncApprovalExpired"), t("restartBridgeApprovalRequestedDetail"), "waiting_for_tui_bridge");
    await requestConsoleRestartApproval({ renew: true });
    return;
  }
  if (!confirm?.checked) {
    setStatus(t("consoleRestartReviewRequired"), t("consoleRestartReviewRequiredDetail"));
    updateChatSyncApprovalButtons();
    return;
  }
  await postAction(request, "approve", explicitApprovalConfirmationPayload(request));
}

async function approvePendingSyncRequestFromOverview() {
  const request = pendingConsoleRestartRequest();
  const confirm = document.querySelector("#overview-sync-confirm");
  if (!request) return;
  if (requestExpiresInMs(request) <= 0) {
    setStatus(t("syncApprovalExpired"), t("restartBridgeApprovalRequestedDetail"), "waiting_for_tui_bridge");
    await requestConsoleRestartApproval({ renew: true });
    return;
  }
  if (!confirm?.checked) {
    setStatus(t("consoleRestartReviewRequired"), t("consoleRestartReviewRequiredDetail"));
    updateOverviewSyncApprovalButtons();
    return;
  }
  await postAction(request, "approve", explicitApprovalConfirmationPayload(request));
}

async function denyPendingSyncRequestFromChat() {
  const request = pendingConsoleRestartRequest();
  if (!request) return;
  await postAction(request, "deny");
}

async function submitTask() {
  const input = document.querySelector("#task-text");
  const text = input.value.trim();
  if (!text) return;
  await signedFetch("/api/tasks", {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify({ text })
  });
  input.value = "";
  await loadTasks();
}

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function selectedChatFiles() {
  const input = document.querySelector("#chat-files");
  return input?.files ? Array.from(input.files) : [];
}

function renderSelectedChatFiles() {
  const list = document.querySelector("#chat-selected-files");
  if (!list) return;
  list.innerHTML = "";
  const files = selectedChatFiles();
  files.forEach((file) => {
    const chip = document.createElement("span");
    chip.className = "chat-file-chip";
    chip.textContent = `${file.name} · ${formatFileSize(file.size)}`;
    list.append(chip);
  });
}

async function uploadChatAttachments(files) {
  if (!files.length) return [];
  const form = new FormData();
  files.forEach((file) => form.append("files", file, file.name));
  const response = await signedFetch("/api/chat/attachments", {
    method: "POST",
    headers: csrfHeaders(),
    body: form
  });
  if (!response.ok) throw new Error("upload failed");
  const payload = await response.json();
  return payload.attachments || [];
}

async function postChatMessage(text, { clientMessageId = null, attachments = [] } = {}) {
  const messageId = clientMessageId || `client_${Date.now()}_${Math.random().toString(16).slice(2)}`;
  return signedFetch("/api/chat/messages", {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify({ text, client_message_id: messageId, attachments })
  });
}

async function sendChatMessage() {
  const sendButton = document.querySelector("#send-chat-message");
  if (sendButton?.disabled) {
    setStatus(t("chatSendBlocked"), t("chatSessionServerOnlyDetail"), document.body.dataset.runtimeState || "");
    return;
  }
  const input = document.querySelector("#chat-input");
  const fileInput = document.querySelector("#chat-files");
  const text = input.value.trim();
  const files = selectedChatFiles();
  if (!text && !files.length) return;
  let attachments = [];
  try {
    attachments = await uploadChatAttachments(files);
  } catch {
    setStatus(t("uploadFailed"), t("pairToViewChat"));
    return;
  }
  const response = await postChatMessage(text, { attachments });
  if (!response.ok) {
    setStatus(t("actionFailed"), t("pairToViewChat"));
    return;
  }
  let payload = {};
  try {
    payload = await response.json();
  } catch {
    payload = {};
  }
  const delivery = payload.live_console_delivery || {};
  if (delivery.delivered) {
    setStatus(t("chatDeliveredToConsole"), t("chatDeliveredToConsoleDetail"));
  } else if (delivery.attempted || delivery.reason) {
    setStatus(t("chatQueuedForBridge"), t("chatQueuedForBridgeDetail"));
  }
  input.value = "";
  if (fileInput) fileInput.value = "";
  renderSelectedChatFiles();
  await loadChatMessages();
}

function updateAgentControlButtons() {
  const isActive = takeoverIsActive();
  const quick = document.querySelector("#runtime-pause-agent");
  if (quick) {
    quick.textContent = isActive ? t("releaseControl") : t("pauseAgent");
    quick.dataset.agentAction = isActive ? "release" : "pause";
    quick.classList.toggle("quick-continue-button", isActive);
    quick.disabled = agentControlBusy;
  }
  const pause = document.querySelector("#request-takeover-pause");
  if (pause) pause.disabled = agentControlBusy || isActive;
  const handoffPause = document.querySelector("#browser-handoff-pause");
  if (handoffPause) handoffPause.disabled = agentControlBusy || isActive;
  const handoffContinue = document.querySelector("#browser-handoff-continue");
  if (handoffContinue) handoffContinue.disabled = agentControlBusy || !isActive;
  updateActiveTakeoverTextControls();
}

function setPauseButtonsDisabled(disabled) {
  agentControlBusy = Boolean(disabled);
  updateAgentControlButtons();
}

function takeoverPausePending() {
  return Boolean(
    pendingTakeoverPauseClientMessageId &&
      Date.now() - pendingTakeoverPauseRequestedAt <= PENDING_TAKEOVER_PAUSE_TTL_MS
  );
}

function clearPendingTakeoverPause() {
  pendingTakeoverPauseClientMessageId = "";
  pendingTakeoverPauseRequestedAt = 0;
}

async function createBrowserTakeoverFromContext(context, { clientMessageId, notifyAgent = true } = {}) {
  if (!context?.browser_context_id) throw new Error("browser context missing");
  const response = await signedFetch(`/api/browser/contexts/${encodeURIComponent(context.browser_context_id)}/takeover`, {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify({
      reason: t("takeoverPausePrompt"),
      notify_agent: notifyAgent,
      client_message_id: clientMessageId || `control_pause_${Date.now()}_${Math.random().toString(16).slice(2)}`
    })
  });
  if (!response.ok) throw new Error("browser takeover failed");
  return response.json().catch(() => ({}));
}

async function maybeAutoStartPendingTakeover() {
  if (!takeoverPausePending() || pendingTakeoverAutoStartBusy || activeTakeoverRequest()) return;
  const context = activeBrowserContext();
  if (!context) return;
  pendingTakeoverAutoStartBusy = true;
  try {
    await createBrowserTakeoverFromContext(context, {
      clientMessageId: pendingTakeoverPauseClientMessageId,
      notifyAgent: false
    });
    clearPendingTakeoverPause();
    setStatus(t("browserTakeoverCreated"), t("browserTakeoverCreatedDetail"));
    activatePanel("takeover-panel", { persist: false });
    await loadRequests();
  } catch {
    pendingTakeoverPauseRequestedAt = Date.now();
  } finally {
    pendingTakeoverAutoStartBusy = false;
  }
}

async function requestTakeoverPause() {
  setPauseButtonsDisabled(true);
  await loadBrowserContexts();
  const context = activeBrowserContext();
  let browserTakeoverStarted = false;
  let agentPauseQueuedByTakeover = false;
  const clientMessageId = `control_pause_${Date.now()}_${Math.random().toString(16).slice(2)}`;
  if (context) {
    try {
      const payload = await createBrowserTakeoverFromContext(context, { clientMessageId, notifyAgent: true });
      browserTakeoverStarted = true;
      agentPauseQueuedByTakeover = Boolean(payload.reused || (payload.agent_pause && !payload.agent_pause.error));
      clearPendingTakeoverPause();
    } catch {
      setStatus(t("actionFailed"), t("activeBrowserReady"));
    }
  }
  if (!agentPauseQueuedByTakeover) {
    try {
      const response = await postChatMessage(t("takeoverPausePrompt"), { clientMessageId });
      if (!response.ok) throw new Error("pause request failed");
      if (!browserTakeoverStarted) {
        pendingTakeoverPauseClientMessageId = clientMessageId;
        pendingTakeoverPauseRequestedAt = Date.now();
      }
    } catch {
      if (!browserTakeoverStarted) {
        setStatus(t("actionFailed"), t("pairToViewChat"));
        setPauseButtonsDisabled(false);
        return;
      }
    }
  }
  if (browserTakeoverStarted) {
    setStatus(t("browserTakeoverCreated"), t("browserTakeoverCreatedDetail"));
    activatePanel("takeover-panel");
    await loadRequests();
  } else {
    setStatus(t("pauseAgentRequested"), t("pauseAgentRequestDetail"));
    activatePanel("task-panel");
  }
  await loadChatMessages();
  setPauseButtonsDisabled(false);
}

function chatStatusLabel(status) {
  return {
    queued: t("chatStatusQueued"),
    claimed: t("chatStatusClaimed"),
    streaming: t("chatStatusStreaming"),
    completed: t("chatStatusCompleted")
  }[status] || status;
}

function chatRecordTypeLabel(type) {
  return {
    delta: t("chatRecordDelta"),
    status: t("chatRecordStatus"),
    tool_call: t("chatRecordToolCall"),
    tool_output: t("chatRecordToolOutput"),
    reasoning: t("chatRecordReasoning"),
    terminal: t("chatRecordTerminal"),
    terminal_input: t("chatRecordTerminalInput")
  }[type] || type;
}

function shortChatId(value) {
  if (!value) return "";
  const text = String(value);
  if (text.length <= 16) return text;
  return `${text.slice(0, 8)}...${text.slice(-6)}`;
}

function appendTextWithBreaks(parent, text) {
  String(text).split("\n").forEach((part, index) => {
    if (index > 0) parent.append(document.createElement("br"));
    if (part) parent.append(document.createTextNode(part));
  });
}

function safeMarkdownHref(value) {
  const href = String(value || "").trim();
  return /^(https?:|mailto:)/i.test(href) ? href : "";
}

function appendInlineMarkdown(parent, text) {
  const source = String(text || "");
  let index = 0;
  while (index < source.length) {
    const candidates = ["`", "**", "__", "["]
      .map((token) => ({ token, at: source.indexOf(token, index) }))
      .filter((candidate) => candidate.at >= 0)
      .sort((left, right) => left.at - right.at);
    if (!candidates.length) {
      appendTextWithBreaks(parent, source.slice(index));
      return;
    }
    const { token, at } = candidates[0];
    if (at > index) appendTextWithBreaks(parent, source.slice(index, at));
    if (token === "`") {
      const end = source.indexOf("`", at + 1);
      if (end < 0) {
        appendTextWithBreaks(parent, source.slice(at));
        return;
      }
      const code = document.createElement("code");
      code.textContent = source.slice(at + 1, end);
      parent.append(code);
      index = end + 1;
    } else if (token === "**" || token === "__") {
      const end = source.indexOf(token, at + 2);
      if (end < 0) {
        appendTextWithBreaks(parent, source.slice(at));
        return;
      }
      const strong = document.createElement("strong");
      appendInlineMarkdown(strong, source.slice(at + 2, end));
      parent.append(strong);
      index = end + 2;
    } else {
      const labelEnd = source.indexOf("]", at + 1);
      const hrefStart = labelEnd >= 0 ? source.indexOf("(", labelEnd) : -1;
      const hrefEnd = hrefStart === labelEnd + 1 ? source.indexOf(")", hrefStart + 1) : -1;
      if (labelEnd < 0 || hrefStart !== labelEnd + 1 || hrefEnd < 0) {
        appendTextWithBreaks(parent, source.slice(at, at + 1));
        index = at + 1;
        continue;
      }
      const href = safeMarkdownHref(source.slice(hrefStart + 1, hrefEnd));
      if (!href) {
        appendTextWithBreaks(parent, source.slice(at, hrefEnd + 1));
        index = hrefEnd + 1;
        continue;
      }
      const link = document.createElement("a");
      link.href = href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      appendInlineMarkdown(link, source.slice(at + 1, labelEnd));
      parent.append(link);
      index = hrefEnd + 1;
    }
  }
}

function isMarkdownBlockBoundary(line) {
  return (
    !line.trim() ||
    /^```/.test(line) ||
    /^#{1,4}\s+/.test(line) ||
    /^\s*[-*+]\s+/.test(line) ||
    /^\s*\d+[.)]\s+/.test(line) ||
    /^>\s?/.test(line)
  );
}

function appendMarkdownParagraph(parent, lines) {
  const paragraph = document.createElement("p");
  appendInlineMarkdown(paragraph, lines.join("\n"));
  parent.append(paragraph);
}

function appendMarkdownCodeBlock(parent, lines, language = "") {
  const pre = document.createElement("pre");
  const code = document.createElement("code");
  if (language) code.dataset.language = language;
  code.textContent = lines.join("\n");
  pre.append(code);
  parent.append(pre);
}

function appendMarkdown(parent, text, className) {
  const node = document.createElement("div");
  node.className = className ? `${className} markdown-text` : "markdown-text";
  const lines = String(text || " ").replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }
    const fence = line.match(/^```\s*([A-Za-z0-9_-]+)?\s*$/);
    if (fence) {
      const codeLines = [];
      index += 1;
      while (index < lines.length && !/^```\s*$/.test(lines[index])) {
        codeLines.push(lines[index]);
        index += 1;
      }
      if (index < lines.length) index += 1;
      appendMarkdownCodeBlock(node, codeLines, fence[1] || "");
      continue;
    }
    const heading = line.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      const headingNode = document.createElement("p");
      headingNode.className = "markdown-heading";
      appendInlineMarkdown(headingNode, heading[2]);
      node.append(headingNode);
      index += 1;
      continue;
    }
    const unordered = line.match(/^\s*[-*+]\s+(.+)$/);
    const ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);
    if (unordered || ordered) {
      const list = document.createElement(ordered ? "ol" : "ul");
      while (index < lines.length) {
        const itemMatch = lines[index].match(ordered ? /^\s*\d+[.)]\s+(.+)$/ : /^\s*[-*+]\s+(.+)$/);
        if (!itemMatch) break;
        const item = document.createElement("li");
        appendInlineMarkdown(item, itemMatch[1]);
        list.append(item);
        index += 1;
      }
      node.append(list);
      continue;
    }
    if (/^>\s?/.test(line)) {
      const quote = document.createElement("blockquote");
      const quoteLines = [];
      while (index < lines.length && /^>\s?/.test(lines[index])) {
        quoteLines.push(lines[index].replace(/^>\s?/, ""));
        index += 1;
      }
      appendInlineMarkdown(quote, quoteLines.join("\n"));
      node.append(quote);
      continue;
    }
    const paragraphLines = [];
    while (index < lines.length && !isMarkdownBlockBoundary(lines[index])) {
      paragraphLines.push(lines[index]);
      index += 1;
    }
    appendMarkdownParagraph(node, paragraphLines);
  }
  if (!node.childNodes.length) node.append(document.createTextNode(" "));
  parent.append(node);
  return node;
}

function cleanToolName(value) {
  const name = String(value || "").trim();
  if (!name) return t("chatToolUnknown");
  if (name === "$") return t("chatToolShell");
  if (name.toLowerCase() === "web") return t("chatToolWebSearch");
  return name.replace(/^mcp__/, "");
}

function toolNameFromRecord(record) {
  const text = String(record.text || "").trim();
  if (text.startsWith("$ ")) return t("chatToolShell");
  if (/^web search:/i.test(text)) return t("chatToolWebSearch");
  if (record.data?.exit_code !== undefined && record.record_type === "tool_output") return t("chatToolShell");
  const mcpOutput = text.match(/^([A-Za-z0-9_.:-]+)\s+(completed|failed|in_progress|running|pending|cancelled):/i);
  if (mcpOutput) return cleanToolName(mcpOutput[1]);
  const firstToken = text.match(/^([A-Za-z0-9_.:/@-]+)/);
  return cleanToolName(firstToken?.[1] || "");
}

function toolOutputSummary(record) {
  const text = String(record.text || "").trim();
  const parts = [];
  const status = record.data?.status || text.match(/\bstatus=([^\s]+)/)?.[1] || "";
  const exitCode = record.data?.exit_code ?? text.match(/\bexit_code=([^\s]+)/)?.[1];
  if (status) parts.push(status);
  if (exitCode !== undefined && exitCode !== null && exitCode !== "") parts.push(`exit ${exitCode}`);
  if (text) {
    const lines = text.split(/\r?\n/).filter((line) => line.trim()).length;
    parts.push(lines > 1 ? t("chatToolOutputLines", lines) : formatFileSize(new Blob([text]).size));
  } else {
    parts.push(t("chatToolOutputNoContent"));
  }
  return parts.join(" · ");
}

function appendToolSummary(parent, label, summary = "") {
  appendText(parent, "strong", label);
  if (summary) appendText(parent, "span", summary);
}

function renderToolRecord(record) {
  const item = document.createElement("article");
  item.className = `chat-record chat-record-${record.record_type} chat-tool-record`;
  const name = toolNameFromRecord(record);
  if (record.record_type === "tool_call") {
    const details = document.createElement("details");
    details.className = "chat-tool-details";
    const summary = document.createElement("summary");
    summary.className = "chat-tool-summary";
    appendToolSummary(summary, t("chatToolCalling", name), record.data?.status || "");
    details.append(summary);
    const fullText = String(record.text || "").trim();
    if (fullText) appendText(details, "pre", fullText, "chat-tool-full");
    item.append(details);
    return item;
  }
  const line = document.createElement("p");
  line.className = "chat-tool-summary";
  appendToolSummary(line, t("chatToolReturned", name), toolOutputSummary(record));
  item.append(line);
  return item;
}

function renderChatMessage(message) {
  const item = document.createElement("article");
  item.className = `chat-message chat-role-${message.role} chat-status-${message.status}`;
  const header = document.createElement("div");
  header.className = "chat-message-header";
  appendText(header, "strong", message.role === "user" ? t("chatUserRole") : t("chatAssistantRole"));
  appendText(header, "span", chatStatusLabel(message.status), "badge");
  item.append(header);
  appendMarkdown(item, message.text || " ", "chat-message-text");
  const meta = document.createElement("div");
  meta.className = "chat-message-meta";
  appendText(meta, "span", `#${message.sequence}`);
  if (message.source) appendText(meta, "span", message.source);
  item.append(meta);
  return item;
}

function renderChatRecord(record) {
  if (["tool_call", "tool_output"].includes(record.record_type)) {
    return renderToolRecord(record);
  }
  const item = document.createElement("article");
  item.className = `chat-record chat-record-${record.record_type}`;
  const header = document.createElement("div");
  header.className = "chat-message-header";
  appendText(header, "strong", chatRecordTypeLabel(record.record_type));
  if (record.role) appendText(header, "span", record.role, "badge");
  if (record.source) appendText(header, "span", record.source, "badge");
  if (record.record_type === "terminal" && record.data?.terminal_snapshot) {
    appendText(header, "span", t("chatRecordTerminalSnapshot"), "badge");
  } else if (record.record_type === "terminal" && record.data?.terminal_delta) {
    appendText(header, "span", t("chatRecordTerminalDelta"), "badge");
  }
  item.append(header);
  if (["status", "terminal", "terminal_input"].includes(record.record_type)) {
    appendText(item, "p", record.text || " ", "chat-message-text");
  } else {
    appendMarkdown(item, record.text || " ", "chat-message-text");
  }
  const meta = document.createElement("div");
  meta.className = "chat-message-meta";
  const sequenceText = record.data?.sequence_start && record.data?.sequence_end
    ? `${t("chatRecordNumber", record.data.sequence_start)}-${record.data.sequence_end}`
    : t("chatRecordNumber", record.sequence);
  appendText(meta, "span", sequenceText);
  if (record.data?.delta_count) appendText(meta, "span", t("chatRecordChunks", record.data.delta_count));
  if (record.message_id) appendText(meta, "span", shortChatId(record.message_id));
  item.append(meta);
  return item;
}

function compactChatActivityRecords(records = []) {
  const compacted = [];
  const deltaByKey = new Map();
  records.forEach((record) => {
    if (record.record_type !== "delta") {
      compacted.push(record);
      return;
    }
    const key = [record.message_id || "", record.role || "", record.source || ""].join("|");
    let aggregate = deltaByKey.get(key);
    if (!aggregate) {
      aggregate = {
        ...record,
        text: "",
        data: {
          ...(record.data || {}),
          sequence_start: record.sequence,
          sequence_end: record.sequence,
          delta_count: 0
        }
      };
      deltaByKey.set(key, aggregate);
      compacted.push(aggregate);
    }
    aggregate.text += record.text || "";
    aggregate.sequence = record.sequence;
    aggregate.created_at = record.created_at;
    aggregate.data.sequence_end = record.sequence;
    aggregate.data.delta_count += 1;
  });
  return compacted.filter((record) => record.record_type !== "delta" || (record.text || "").trim());
}

function renderLegacyTerminal(terminal) {
  if (!terminal?.available || !terminal.text) return null;
  const item = document.createElement("article");
  item.className = "chat-record chat-terminal-snapshot";
  const header = document.createElement("div");
  header.className = "chat-message-header";
  appendText(header, "strong", t("legacyTerminalTitle"));
  appendText(header, "span", terminal.pane_id || "tmux", "badge");
  item.append(header);
  appendText(item, "pre", terminal.text);
  return item;
}

function renderLiveConsole(terminal) {
  const panel = document.querySelector("#chat-live-console");
  if (!panel) return;
  panel.innerHTML = "";
  const terminalNode = renderLegacyTerminal(terminal);
  if (!terminalNode) {
    panel.hidden = true;
    return;
  }
  panel.hidden = false;
  panel.append(terminalNode);
  const pre = terminalNode.querySelector("pre");
  if (pre) pre.scrollTop = pre.scrollHeight;
}

function renderChatTimeline(messages, records = [], terminal = null) {
  const list = document.querySelector("#chat-messages");
  if (!list) return;
  renderLiveConsole(terminal);
  list.innerHTML = "";

  const conversation = document.createElement("div");
  conversation.className = "chat-conversation";
  appendText(conversation, "div", t("chatConversationTitle"), "chat-lane-title");
  if (messages.length) {
    messages.forEach((message) => conversation.append(renderChatMessage(message)));
  } else {
    appendText(conversation, "p", t("noChatMessages"), "chat-empty-state");
  }
  list.append(conversation);

  if (records.length) {
    const activity = document.createElement("div");
    activity.className = "chat-activity";
    appendText(activity, "div", t("chatActivityTitle"), "chat-lane-title");
    compactChatActivityRecords(records).forEach((record) => activity.append(renderChatRecord(record)));
    list.append(activity);
  }
  list.scrollTop = list.scrollHeight;
}

async function loadChatMessages() {
  const list = document.querySelector("#chat-messages");
  if (!list) return;
  try {
    const payload = await signedFetch("/api/chat/messages", { cache: "no-store" }).then((r) => {
      if (!r.ok) throw new Error("unauthorized");
      return r.json();
    });
    cachedChatMessages = payload.messages || [];
    cachedChatRecords = payload.records || [];
    cachedChatTerminal = payload.terminal || null;
    lastChatPayloadFingerprint = chatPayloadFingerprint(cachedChatMessages, cachedChatRecords, cachedChatTerminal);
    renderChatTimeline(cachedChatMessages, cachedChatRecords, cachedChatTerminal);
  } catch {
    list.textContent = t("pairToViewChat");
  }
}

async function updateTask(task, action) {
  await signedFetch(`/api/tasks/${task.task_id}/${action}`, { method: "POST", headers: csrfHeaders() });
  await loadTasks();
}

async function revokeDevice(device) {
  await signedFetch(`/api/devices/${device.device_id}/revoke`, {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: "{}"
  });
  await loadDevicesAndSessions();
}

async function revokeSession(session) {
  await signedFetch(`/api/sessions/${session.session_id}/revoke`, {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: "{}"
  });
  await loadDevicesAndSessions();
}

function appendText(parent, tag, text, className) {
  const node = document.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  parent.append(node);
  return node;
}

function renderTask(task) {
  const item = document.createElement("article");
  item.className = "task";
  appendText(item, "h3", task.status);
  appendText(item, "p", `task_id: ${task.task_id}`);
  appendText(item, "p", task.text);
  appendText(item, "p", `source: ${task.source}`);
  appendText(item, "p", "Delivery: local queue -> MCP control.next_user_task -> Codex CLI. The Control Client does not call models directly.", "flow-note");
  if (task.status !== "completed" && task.status !== "cancelled") {
    const actions = document.createElement("div");
    actions.className = "button-row";
    const complete = document.createElement("button");
    complete.textContent = "Mark Complete";
    complete.onclick = () => updateTask(task, "complete");
    const cancel = document.createElement("button");
    cancel.textContent = "Cancel";
    cancel.onclick = () => updateTask(task, "cancel");
    actions.append(cancel, complete);
    item.append(actions);
  }
  return item;
}

async function loadTasks() {
  const list = document.querySelector("#tasks-list");
  if (!list) return;
  try {
    const tasks = await signedFetch("/api/tasks", { cache: "no-store" }).then((r) => r.json());
    list.innerHTML = "";
    if (!tasks.length) {
      list.textContent = t("noQueuedTasks");
      return;
    }
    tasks.forEach((task) => list.append(renderTask(task)));
  } catch {
    list.textContent = t("pairToViewTasks");
  }
}

function renderDevice(device) {
  const item = document.createElement("article");
  item.className = "mini-record";
  appendText(item, "h3", device.name || "Control Client");
  appendText(item, "p", `device_id: ${device.device_id}`);
  appendText(item, "p", `fingerprint: ${device.fingerprint || "not visible"}`);
  appendText(item, "p", `status: ${device.revoked ? "revoked" : "active"}`);
  if (!device.revoked) {
    const actions = document.createElement("div");
    actions.className = "button-row";
    const revoke = document.createElement("button");
    revoke.textContent = "Revoke Device";
    revoke.onclick = () => revokeDevice(device);
    actions.append(revoke);
    item.append(actions);
  }
  return item;
}

function renderSession(session) {
  const item = document.createElement("article");
  item.className = "mini-record";
  appendText(item, "h3", session.revoked ? "revoked" : "active");
  appendText(item, "p", `session_id: ${session.session_id}`);
  appendText(item, "p", `device_id: ${session.device_id}`);
  appendText(item, "p", `expires_at: ${formatTimestamp(session.expires_at)}`);
  if (!session.revoked) {
    const actions = document.createElement("div");
    actions.className = "button-row";
    const revoke = document.createElement("button");
    revoke.textContent = "Revoke Session";
    revoke.onclick = () => revokeSession(session);
    actions.append(revoke);
    item.append(actions);
  }
  return item;
}

async function loadDevicesAndSessions() {
  const devicesRoot = document.querySelector("#devices-list");
  const sessionsRoot = document.querySelector("#sessions-list");
  if (!devicesRoot || !sessionsRoot) return;
  try {
    const [devices, sessions] = await Promise.all([
      signedFetch("/api/devices", { cache: "no-store" }).then((r) => {
        if (!r.ok) throw new Error("devices unauthorized");
        return r.json();
      }),
      signedFetch("/api/sessions", { cache: "no-store" }).then((r) => {
        if (!r.ok) throw new Error("sessions unauthorized");
        return r.json();
      })
    ]);
    devicesRoot.innerHTML = "";
    sessionsRoot.innerHTML = "";
    if (!devices.length) {
      devicesRoot.textContent = t("noPairedDevices");
    } else {
      devices.forEach((device) => devicesRoot.append(renderDevice(device)));
    }
    if (!sessions.length) {
      sessionsRoot.textContent = t("noSessions");
    } else {
      sessions.forEach((session) => sessionsRoot.append(renderSession(session)));
    }
  } catch {
    devicesRoot.textContent = t("pairToViewDevices");
    sessionsRoot.textContent = t("pairToViewSessions");
  }
}

async function refreshPairingState() {
  let runtime = null;
  try {
    runtime = await fetch("/api/status", { cache: "no-store" }).then((r) => r.json());
  } catch {
    cachedPairingAuthenticated = false;
    setPairingUiState({ state: "offline", message: t("controlOffline") });
    return false;
  }
  if (runtime.mode === "local_dev") {
    cachedPairingAuthenticated = true;
    setPairingUiState({
      state: "paired",
      message: t("localTrustedMode"),
      deviceText: t("localTrustedDevice")
    });
    return true;
  }
  const identity = storedPairingIdentity();
  if (!identity.deviceId || !identity.sessionId || !identity.hasPrivateKey) {
    const codeLoaded = Boolean(document.querySelector("#pairing-code")?.value.trim());
    cachedPairingAuthenticated = false;
    setPairingUiState({
      state: "unpaired",
      message: codeLoaded
        ? t("pairingCodeLoaded")
        : t("pairFreshLink")
    });
    return false;
  }
  setPairingUiState({
    state: "checking",
    message: t("checkingCachedSession"),
    deviceText: identity.deviceId
  });
  try {
    const sessions = await signedFetch("/api/sessions", { cache: "no-store" }).then((r) => {
      if (!r.ok) throw new Error("session unauthorized");
      return r.json();
    });
    const current = sessions.find((session) => session.session_id === identity.sessionId);
    if (!current) {
      cachedPairingAuthenticated = true;
      setPairingUiState({
        state: "paired",
        message: t("sessionHidden"),
        deviceText: identity.deviceId
      });
      return true;
    }
    if (current.revoked) {
      cachedPairingAuthenticated = false;
      setPairingUiState({
        state: "stale",
        message: t("sessionRevoked"),
        deviceText: `${identity.deviceId} - revoked`
      });
      return false;
    }
    cachedPairingAuthenticated = true;
    setPairingUiState({
      state: "paired",
      message: t("pairedCached"),
      deviceText: `${identity.deviceId} - ${t("sessionValidUntil", formatTimestamp(current.expires_at))}`
    });
    return true;
  } catch {
    cachedPairingAuthenticated = false;
    setPairingUiState({
      state: "stale",
      message: t("cachedPairingRejected"),
      deviceText: identity.deviceId
    });
    return false;
  }
}

async function sendTakeoverInput(request, eventPayload) {
  const stream = document.querySelector("#browser-stream");
  if (document.hidden || takeoverFrameVisibilityPaused) {
    updateTakeoverPanel(request, null, t("takeoverInputHidden"));
    return false;
  }
  const frameId = eventPayload.frame_id || stream?.dataset.frameId || "";
  if (!frameId) {
    updateTakeoverPanel(request, null, t("takeoverInputNoFrame"));
    return false;
  }
  if (!takeoverFrameIsFresh(stream)) {
    updateTakeoverPanel(request, null, t("takeoverInputRefreshingStale"));
    refreshActiveTakeoverFrame();
    return false;
  }
  const payload = {
    ...eventPayload,
    frame_id: frameId,
    frame_captured_at: stream?.dataset.frameCapturedAt || undefined
  };
  const response = await signedFetch(`/api/requests/${request.request_id}/input`, {
    method: "POST",
    headers: { "content-type": "application/json", ...csrfHeaders() },
    body: JSON.stringify(payload)
  });
  let responsePayload = {};
  try {
    responsePayload = await response.json();
  } catch {
    responsePayload = {};
  }
  if (response.ok) {
    const status = responsePayload.status || "";
    const message = status === "event_queued"
      ? t("takeoverInputQueued", eventPayload.event_type)
      : t("takeoverInputDelivered", eventPayload.event_type);
    updateTakeoverPanel(request, null, message);
    if (status === "event_queued" && responsePayload.event_id && request.browser_context_id) {
      pollTakeoverInputResult(request, responsePayload.event_id, eventPayload.event_type);
    }
    scheduleTakeoverFrameRefresh(request, TAKEOVER_FRAME_AFTER_INPUT_MS);
    return true;
  } else {
    const error = responsePayload.error || "";
    if (error === "stale_takeover_frame") {
      updateTakeoverPanel(request, null, t("takeoverInputFrameChanged"));
      refreshActiveTakeoverFrame();
      return false;
    }
    updateTakeoverPanel(request, null, t("takeoverInputDeliveryFailed"));
    scheduleTakeoverFrameRefresh(request, TAKEOVER_FRAME_AFTER_INPUT_MS);
    return false;
  }
}

async function pollTakeoverInputResult(request, eventId, eventType) {
  const contextId = request?.browser_context_id;
  if (!contextId || !eventId) return;
  if (activeTakeoverRequest()?.request_id !== request.request_id) return;
  try {
    const response = await signedFetch(
      `/api/browser/contexts/${encodeURIComponent(contextId)}/input-results/${encodeURIComponent(eventId)}?wait=6`,
      { cache: "no-store" }
    );
    if (activeTakeoverRequest()?.request_id !== request.request_id) return;
    if (response.status === 202) {
      updateTakeoverPanel(request, null, t("takeoverInputStillPending"));
      refreshActiveTakeoverFrame();
      return;
    }
    const result = await response.json();
    if (!response.ok || result.status === "event_failed") {
      updateTakeoverPanel(request, null, t("takeoverInputDeliveryFailed"));
    } else {
      updateTakeoverPanel(request, null, t("takeoverInputDelivered", eventType));
    }
    scheduleTakeoverFrameRefresh(request, TAKEOVER_FRAME_AFTER_INPUT_MS);
  } catch {
    return;
  }
}

async function sendActiveTakeoverText() {
  const request = activeTakeoverRequest();
  const input = document.querySelector("#active-takeover-text");
  const text = input?.value || "";
  if (!request || !text) return;
  const delivered = await sendTakeoverInput(request, { event_type: "type", text });
  if (delivered && input) input.value = "";
}

async function sendActiveTakeoverEnter() {
  const request = activeTakeoverRequest();
  if (!request) return;
  await sendTakeoverInput(request, { event_type: "key", key: "Enter" });
}

function framePoint(event, image) {
  const rect = image.getBoundingClientRect();
  const x = Math.round((event.clientX - rect.left) * (image.naturalWidth / Math.max(1, rect.width)));
  const y = Math.round((event.clientY - rect.top) * (image.naturalHeight / Math.max(1, rect.height)));
  return {
    frame_id: image.dataset.frameId || "",
    x: Math.min(Math.max(0, x), Math.max(0, image.naturalWidth - 1)),
    y: Math.min(Math.max(0, y), Math.max(0, image.naturalHeight - 1))
  };
}

function clearPendingTakeoverTap() {
  if (takeoverPendingTapTimer) clearTimeout(takeoverPendingTapTimer);
  takeoverPendingTapTimer = null;
  takeoverPendingTap = null;
}

function sameTakeoverTapTarget(left, right) {
  if (!left || !right) return false;
  if (left.request_id !== right.request_id || left.frame_id !== right.frame_id) return false;
  return Math.hypot(left.x - right.x, left.y - right.y) <= TAKEOVER_DOUBLE_TAP_DISTANCE;
}

function queueTakeoverTap(request, point) {
  const next = {
    request_id: request.request_id,
    frame_id: point.frame_id || "",
    x: point.x,
    y: point.y,
    at: Date.now()
  };
  if (
    takeoverPendingTap
    && Date.now() - takeoverPendingTap.at <= TAKEOVER_DOUBLE_TAP_MS
    && sameTakeoverTapTarget(takeoverPendingTap, next)
  ) {
    clearPendingTakeoverTap();
    sendTakeoverInput(request, { event_type: "double_click", frame_id: next.frame_id, x: next.x, y: next.y });
    return;
  }
  clearPendingTakeoverTap();
  takeoverPendingTap = next;
  takeoverPendingTapTimer = setTimeout(() => {
    const pending = takeoverPendingTap;
    clearPendingTakeoverTap();
    if (!pending) return;
    sendTakeoverInput(request, { event_type: "tap", frame_id: pending.frame_id, x: pending.x, y: pending.y });
  }, TAKEOVER_DOUBLE_TAP_MS);
}

function installTakeoverPointerHandlers(request, stream) {
  clearTakeoverPointerHandlers(stream);
  let start = null;
  const activeTouchPointers = new Map();
  let pinchGesture = null;
  let suppressTouchInput = false;
  const trackTouchPointer = (event) => {
    if (event.pointerType !== "touch") return;
    activeTouchPointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
  };
  const forgetTouchPointer = (event) => {
    if (event.pointerType !== "touch") return;
    activeTouchPointers.delete(event.pointerId);
    if (!activeTouchPointers.size) {
      pinchGesture = null;
      suppressTouchInput = false;
    }
  };
  const touchDistance = () => {
    const points = Array.from(activeTouchPointers.values());
    if (points.length < 2) return 0;
    return Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y);
  };
  stream.tabIndex = 0;
  stream.onpointerdown = (event) => {
    if (takeoverFramePanMode) return;
    const img = document.querySelector("#takeover-frame");
    if (!img) return;
    if (event.pointerType === "touch") {
      trackTouchPointer(event);
      if (activeTouchPointers.size >= 2) {
        event.preventDefault();
        start = null;
        suppressTouchInput = true;
        pinchGesture = { startDistance: Math.max(1, touchDistance()), startZoom: takeoverFrameZoom };
        updateTakeoverPanel(request, null, t("takeoverPinchZooming"));
        return;
      }
    }
    stream.setPointerCapture(event.pointerId);
    start = { ...framePoint(event, img), frame_id: img.dataset.frameId || "", at: Date.now() };
  };
  stream.onpointermove = (event) => {
    if (event.pointerType !== "touch") return;
    if (!activeTouchPointers.has(event.pointerId)) return;
    trackTouchPointer(event);
    if (pinchGesture && activeTouchPointers.size >= 2) {
      event.preventDefault();
      const distance = Math.max(1, touchDistance());
      setTakeoverFrameZoom(pinchGesture.startZoom * (distance / pinchGesture.startDistance));
      updateTakeoverPanel(request, null, t("takeoverPinchZooming"));
    }
  };
  stream.onpointerup = (event) => {
    if (takeoverFramePanMode) return;
    const suppressed = event.pointerType === "touch" && suppressTouchInput;
    forgetTouchPointer(event);
    if (suppressed) {
      event.preventDefault();
      start = null;
      return;
    }
    const img = document.querySelector("#takeover-frame");
    if (!img || !start) return;
    const end = framePoint(event, img);
    const distance = Math.hypot(end.x - start.x, end.y - start.y);
    const duration = Date.now() - start.at;
    if (distance > 12) {
      sendTakeoverInput(request, { event_type: "drag", frame_id: start.frame_id, x: start.x, y: start.y, to_x: end.x, to_y: end.y });
    } else if (duration > 650) {
      sendTakeoverInput(request, { event_type: "long_press", frame_id: start.frame_id, x: start.x, y: start.y });
    } else {
      queueTakeoverTap(request, { frame_id: end.frame_id || start.frame_id, x: end.x, y: end.y });
    }
    start = null;
  };
  stream.onpointercancel = (event) => {
    forgetTouchPointer(event);
    start = null;
  };
  stream.onlostpointercapture = () => {
    activeTouchPointers.clear();
    pinchGesture = null;
    suppressTouchInput = false;
    start = null;
  };
  stream.onkeydown = (event) => {
    if (takeoverFramePanMode) return;
    if (event.key.length === 1 || ["Enter", "Tab", "Backspace", "Escape", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) {
      event.preventDefault();
      sendTakeoverInput(request, { event_type: "key", key: event.key });
    }
  };
  stream.onwheel = (event) => {
    if (takeoverFramePanMode) return;
    event.preventDefault();
    sendTakeoverInput(request, { event_type: "scroll", delta_y: Math.round(event.deltaY) });
  };
}

function clearTakeoverPointerHandlers(stream = document.querySelector("#browser-stream")) {
  clearPendingTakeoverTap();
  if (!stream) return;
  stream.onpointerdown = null;
  stream.onpointermove = null;
  stream.onpointerup = null;
  stream.onpointercancel = null;
  stream.onlostpointercapture = null;
  stream.onkeydown = null;
  stream.onwheel = null;
  stream.removeAttribute("tabindex");
}

function startTakeoverFrameTimers(request, stream, options = {}) {
  const framePolling = options.framePolling !== false;
  if (framePolling && !takeoverFrameTimer) {
    takeoverFrameTimer = setInterval(() => fetchTakeoverFrame(request, stream), TAKEOVER_FRAME_POLL_MS);
  }
  if (!takeoverFreshnessTimer) {
    takeoverFreshnessTimer = setInterval(() => updateTakeoverFrameFreshness(stream), 1000);
  }
}

function closeTakeoverFrameWebSocket() {
  if (takeoverFrameSocketRestart) clearTimeout(takeoverFrameSocketRestart);
  takeoverFrameSocketRestart = null;
  if (takeoverFrameSocket) {
    takeoverFrameSocket.onclose = null;
    takeoverFrameSocket.onerror = null;
    takeoverFrameSocket.onmessage = null;
    takeoverFrameSocket.close();
  }
  takeoverFrameSocket = null;
  takeoverFrameSocketRequest = null;
}

function restartTakeoverFrameWebSocket(request, stream) {
  if (takeoverFrameSocketRestart || document.hidden) return;
  takeoverFrameSocketRestart = setTimeout(() => {
    takeoverFrameSocketRestart = null;
    const activeRequest = activeTakeoverRequest();
    const activeStream = document.querySelector("#browser-stream");
    if (activeRequest?.request_id === request.request_id && activeStream && activeRequest.status === "user_control") {
      startTakeoverFrameWebSocket(activeRequest, activeStream);
    }
  }, 3000);
}

async function startTakeoverFrameWebSocket(request, stream) {
  if (!window.WebSocket || document.hidden || request.status !== "user_control") return false;
  if (
    takeoverFrameSocket
    && takeoverFrameSocketRequest === request.request_id
    && [WebSocket.CONNECTING, WebSocket.OPEN].includes(takeoverFrameSocket.readyState)
  ) {
    return true;
  }
  closeTakeoverFrameWebSocket();
  const path = `/api/ws/requests/${encodeURIComponent(request.request_id)}/frames`;
  try {
    const protocol = await deviceAuthSubprotocol("GET", path);
    const target = `${path}?${takeoverFrameQuery({ snapshots: TAKEOVER_FRAME_WS_SNAPSHOTS, interval: TAKEOVER_FRAME_WS_INTERVAL_SECONDS })}`;
    const socket = protocol ? new WebSocket(websocketUrl(target), [protocol]) : new WebSocket(websocketUrl(target));
    takeoverFrameSocket = socket;
    takeoverFrameSocketRequest = request.request_id;
    socket.onopen = () => {
      if (activeTakeoverFrameRequest !== request.request_id) {
        closeTakeoverFrameWebSocket();
        return;
      }
      if (takeoverFrameTimer) clearInterval(takeoverFrameTimer);
      takeoverFrameTimer = null;
      startTakeoverFrameTimers(request, stream, { framePolling: false });
      updateTakeoverFrameConnection("connected", t("takeoverConnectedWebSocket"));
    };
    socket.onmessage = (event) => {
      if (activeTakeoverFrameRequest !== request.request_id) return;
      const payload = JSON.parse(event.data);
      if (payload.event === "takeover_frame" && payload.request_id === request.request_id) {
        renderTakeoverFrame(request, stream, payload.data || {}, t("takeoverFrameReadyWebSocket"));
      }
    };
    socket.onerror = () => {
      socket.close();
    };
    socket.onclose = () => {
      if (takeoverFrameSocket === socket) {
        takeoverFrameSocket = null;
        takeoverFrameSocketRequest = null;
      }
      const activeRequest = activeTakeoverRequest();
      const activeStream = document.querySelector("#browser-stream");
      if (activeRequest?.request_id === request.request_id && activeStream && activeRequest.status === "user_control" && !document.hidden) {
        markTakeoverFrameReconnect(request, stream, t("takeoverWebSocketDisconnected"));
        startTakeoverFrameTimers(request, stream);
        fetchTakeoverFrame(request, stream);
        restartTakeoverFrameWebSocket(request, stream);
      }
    };
    return true;
  } catch {
    closeTakeoverFrameWebSocket();
    return false;
  }
}

function pauseTakeoverFramePollingForVisibility() {
  if (!activeTakeoverFrameRequest || !document.hidden) return;
  const request = activeTakeoverRequest();
  const stream = document.querySelector("#browser-stream");
  if (takeoverFrameTimer) clearInterval(takeoverFrameTimer);
  if (takeoverFreshnessTimer) clearInterval(takeoverFreshnessTimer);
  if (takeoverFrameRefreshTimer) clearTimeout(takeoverFrameRefreshTimer);
  closeTakeoverFrameWebSocket();
  takeoverFrameTimer = null;
  takeoverFreshnessTimer = null;
  takeoverFrameRefreshTimer = null;
  takeoverFrameFetchQueued = false;
  takeoverFrameVisibilityPaused = true;
  updateTakeoverFrameConnection("paused", t("takeoverPausedHidden"));
  updateTakeoverFrameFreshness(stream);
  if (request) {
    updateTakeoverPanel(request, null, t("takeoverPollingPausedHidden"));
  }
}

function resumeTakeoverFramePollingFromVisibility() {
  if (document.hidden) return;
  const request = activeTakeoverRequest();
  const stream = document.querySelector("#browser-stream");
  takeoverFrameVisibilityPaused = false;
  if (!request || !stream || request.status !== "user_control") return;
  updateTakeoverFrameConnection("connecting", t("takeoverResuming"));
  updateTakeoverPanel(request, null, t("takeoverVisibleRefreshing"));
  installTakeoverPointerHandlers(request, stream);
  startTakeoverFrameTimers(request, stream, { framePolling: false });
  startTakeoverFrameWebSocket(request, stream).then((started) => {
    if (!started) {
      fetchTakeoverFrame(request, stream);
      startTakeoverFrameTimers(request, stream);
    }
  });
}

function handleTakeoverVisibilityChange() {
  if (document.hidden) {
    if (browserPreviewTimer) clearInterval(browserPreviewTimer);
    browserPreviewTimer = null;
    closeBrowserPreviewWebSocket();
    pauseTakeoverFramePollingForVisibility();
    return;
  }
  resumeTakeoverFramePollingFromVisibility();
  const context = activeBrowserContext();
  const stream = document.querySelector("#browser-stream");
  if (context && stream && !takeoverIsActive()) {
    startBrowserPreviewPolling(context, stream);
  }
}

function stopTakeoverFramePolling(requestId = null) {
  if (requestId && activeTakeoverFrameRequest !== requestId) return;
  if (takeoverFrameTimer) clearInterval(takeoverFrameTimer);
  if (takeoverFreshnessTimer) clearInterval(takeoverFreshnessTimer);
  if (takeoverFrameRefreshTimer) clearTimeout(takeoverFrameRefreshTimer);
  closeTakeoverFrameWebSocket();
  takeoverFrameTimer = null;
  takeoverFreshnessTimer = null;
  takeoverFrameRefreshTimer = null;
  takeoverFrameFetchQueued = false;
  takeoverFrameMisses = 0;
  takeoverFrameVisibilityPaused = false;
  activeTakeoverFrameRequest = null;
  const stream = document.querySelector("#browser-stream");
  clearTakeoverPointerHandlers(stream);
  if (stream) {
    delete stream.dataset.frameId;
    delete stream.dataset.frameCapturedAt;
    stream.classList.remove("frame-reconnecting");
    delete stream.dataset.frameProfile;
    delete stream.dataset.frameContentType;
  }
  resetTakeoverFrameView();
  updateTakeoverFrameConnection("", t("takeoverFrameWaiting"));
  updateTakeoverFrameFreshness(stream);
}

function markTakeoverFrameReconnect(request, stream, message) {
  if (!stream) return;
  takeoverFrameMisses += 1;
  const hasLastFrame = Boolean(stream.querySelector("#takeover-frame") && stream.dataset.frameId);
  const retryLabel = t("takeoverReconnectRetry", takeoverFrameMisses);
  if (hasLastFrame) {
    stream.classList.add("frame-reconnecting");
    updateTakeoverFrameConnection("reconnecting", `${retryLabel}, ${t("takeoverKeepingLastFrameShort")}`);
    updateTakeoverPanel(request, null, t("takeoverKeepingLastFrame", message));
    updateTakeoverFrameFreshness(stream);
    return;
  }
  stream.textContent = t("takeoverFrameWaitingControlled");
  updateTakeoverFrameConnection("connecting", retryLabel);
  updateTakeoverPanel(request, null, t("takeoverFrameWaitingControlled"));
}

async function fetchTakeoverFrame(request, stream) {
  if (activeTakeoverFrameRequest !== request.request_id) return;
  if (document.hidden) {
    pauseTakeoverFramePollingForVisibility();
    return;
  }
  if (takeoverFrameFetchInFlight) {
    takeoverFrameFetchQueued = true;
    return;
  }
  takeoverFrameFetchInFlight = true;
  try {
    const frame = await signedFetch(`/api/requests/${request.request_id}/frame?${takeoverFrameQuery()}`, { cache: "no-store" }).then((r) => r.json());
    if (activeTakeoverFrameRequest !== request.request_id) return;
    if (frame.data_b64) {
      renderTakeoverFrame(request, stream, frame);
    } else {
      markTakeoverFrameReconnect(request, stream, t("takeoverDisconnected"));
    }
  } catch {
    if (activeTakeoverFrameRequest === request.request_id) {
      markTakeoverFrameReconnect(request, stream, t("takeoverFrameFetchFailed"));
    }
  } finally {
    takeoverFrameFetchInFlight = false;
    const hasQueuedFetch = takeoverFrameFetchQueued;
    takeoverFrameFetchQueued = false;
    if (hasQueuedFetch) {
      const nextRequest = activeTakeoverRequest();
      const nextStream = document.querySelector("#browser-stream");
      if (nextRequest && nextStream && nextRequest.status === "user_control") {
        fetchTakeoverFrame(nextRequest, nextStream);
      }
    }
  }
}

function startTakeoverFramePolling(request, stream) {
  if (request.status !== "user_control") {
    stopTakeoverFramePolling(request.request_id);
    stream.textContent = t("takeoverInactive");
    updateTakeoverPanel(request, null, t("takeoverInactive"));
    return;
  }
  if (activeTakeoverFrameRequest && activeTakeoverFrameRequest !== request.request_id) {
    stopTakeoverFramePolling();
  }
  if (activeTakeoverFrameRequest === request.request_id && takeoverFrameTimer) return;
  activeTakeoverFrameRequest = request.request_id;
  takeoverFrameMisses = 0;
  resetTakeoverFrameView();
  stream.textContent = t("takeoverLoadingFrame");
  stream.classList.remove("frame-reconnecting");
  if (document.hidden) {
    takeoverFrameVisibilityPaused = true;
    updateTakeoverFrameConnection("paused", t("takeoverPausedHidden"));
    updateTakeoverPanel(request, null, t("takeoverPollingPausedHidden"));
    installTakeoverPointerHandlers(request, stream);
    return;
  }
  takeoverFrameVisibilityPaused = false;
  updateTakeoverFrameConnection("connecting", t("takeoverConnecting"));
  updateTakeoverPanel(request, null, t("takeoverLoadingFrame"));
  installTakeoverPointerHandlers(request, stream);
  startTakeoverFrameTimers(request, stream, { framePolling: false });
  startTakeoverFrameWebSocket(request, stream).then((started) => {
    if (!started && activeTakeoverFrameRequest === request.request_id) {
      fetchTakeoverFrame(request, stream);
      startTakeoverFrameTimers(request, stream);
    }
  });
}

function requestHeader(request) {
  const header = document.createElement("div");
  header.className = "request-header";
  const titleBlock = document.createElement("div");
  appendText(titleBlock, "h3", displayRequestType(request));
  appendText(titleBlock, "p", request.action_summary || t("waitingForUserAction"), "request-summary");
  const badges = document.createElement("div");
  badges.className = "badge-row";
  appendText(badges, "span", displayStatus(request.status), `badge status-${request.status}`);
  appendText(badges, "span", request.risk_level || "unknown risk", `badge risk-${request.risk_level || "unknown"}`);
  appendText(badges, "span", requestKind(request), "badge");
  header.append(titleBlock, badges);
  return header;
}

function requestMetadata(request) {
  const dl = document.createElement("dl");
  dl.className = "metadata";
  [
    ["request_id", request.request_id],
    ["origin", request.origin],
    ["current_url", request.top_level_url],
    ["expires_at", formatTimestamp(request.expires_at)],
    ["allowed_device", request.allowed_device_id || t("anyPairedDevice")],
    ["broker_fingerprint", request.broker_public_key_fingerprint || t("serverPinned")]
  ].forEach(([label, value]) => {
    const dt = document.createElement("dt");
    dt.textContent = displayMetadataLabel(label);
    const dd = document.createElement("dd");
    if (typeof value === "string" && value.startsWith("https://")) {
      const link = document.createElement("a");
      link.href = value;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = value;
      dd.append(link);
    } else {
      dd.textContent = value || t("notVisible");
    }
    dl.append(dt, dd);
  });
  return dl;
}

function credentialLabel(request, field, fallback) {
  const labels = request.structured_details?.credential_labels || {};
  return displayValue(labels[field], fallback);
}

function credentialFieldRequested(request, field) {
  const fields = request.requested_fields || [];
  return !fields.length || fields.includes(field);
}

function renderCredentialControls(request, item) {
  if (request.status !== "pending") {
    appendText(item, "p", t("credentialClosed", request.status), "flow-note");
    return;
  }
  const vaultSaveAllowed = request.save_to_vault === true;
  const form = document.createElement("form");
  form.className = "secure-form";
  form.innerHTML = `
    <p class="flow-note">${t("secretNote")}</p>
    <label>${t("username")} <input id="username" data-secret-field="username" autocomplete="username"></label>
    <label>${t("password")} <input id="password" data-secret-field="password" type="password" autocomplete="current-password"></label>
    <label>${t("totpSeed")} <input id="totp-seed" data-secret-field="totp_seed" type="password" autocomplete="off"></label>
    <label class="check-row"><input type="checkbox" data-secret-field="save_to_vault" ${vaultSaveAllowed ? "checked" : "disabled"}> ${t("saveInVault")}</label>
    <div class="button-row"><button type="submit">${t("submitCredential")}</button></div>
  `;
  [
    ["username", t("username")],
    ["password", t("password")],
    ["totp_seed", t("totpSeed")]
  ].forEach(([field, fallback]) => {
    const input = form.querySelector(`[data-secret-field='${field}']`);
    if (!input) return;
    if (!credentialFieldRequested(request, field)) {
      input.closest("label")?.remove();
      return;
    }
    input.closest("label").firstChild.textContent = `${credentialLabel(request, field, fallback)} `;
  });
  form.onsubmit = (event) => {
    event.preventDefault();
    const saveToVault = form.querySelector("[data-secret-field='save_to_vault']");
    const valueFor = (field) => form.querySelector(`[data-secret-field='${field}']`)?.value || "";
    const payload = {
      username: valueFor("username"),
      password: valueFor("password"),
      totp_seed: valueFor("totp_seed"),
      save_to_vault: Boolean(vaultSaveAllowed && saveToVault.checked)
    };
    submitEncrypted(request, payload).then(() => {
      const passwordInput = form.querySelector("[data-secret-field='password']");
      const totpInput = form.querySelector("[data-secret-field='totp_seed']");
      if (passwordInput) passwordInput.value = "";
      if (totpInput) totpInput.value = "";
    });
  };
  item.append(form);
}

function renderChallengeControls(request, item) {
  if (request.status !== "pending") {
    appendText(item, "p", t("challengeClosed", request.status), "flow-note");
    return;
  }
  const form = document.createElement("form");
  form.className = "secure-form";
  const isVisualChallenge = ["captcha", "passkey", "webauthn", "device_confirmation"].includes(request.request_type);
  form.innerHTML = isVisualChallenge ? `
    <p class="flow-note">${t("challengeNote")}</p>
    <p class="flow-note">${t("visualChallengeNote")}</p>
    <div class="button-row"><button type="submit">${t("markUserCompleted")}</button></div>
  ` : `
    <p class="flow-note">${t("challengeNote")}</p>
    <label>${t("challengeCode")} <input data-challenge-field="code" inputmode="numeric" autocomplete="one-time-code"></label>
    <div class="button-row"><button type="submit">${t("submitChallenge")}</button></div>
  `;
  form.onsubmit = (event) => {
    event.preventDefault();
    if (isVisualChallenge) {
      postAction(request, "complete-challenge");
      return;
    }
    const field = form.querySelector("[data-challenge-field='code']");
    const value = field.value;
    submitEncrypted(request, { code: value }).then(() => postAction(request, "complete-challenge")).then(() => {
      field.value = "";
    });
  };
  item.append(form);
}

function renderTakeoverControls(request, item) {
  if (request.status !== "user_control") {
    appendText(item, "p", t("takeoverClosed", request.status), "flow-note");
    return;
  }
  if (!request.browser_context_id) {
    appendText(item, "p", t("externalHandoffNote"), "flow-note");
    const actions = document.createElement("div");
    actions.className = "button-row handoff-actions";
    const open = document.createElement("a");
    open.href = request.top_level_url || request.origin || "#";
    open.target = "_blank";
    open.rel = "noopener noreferrer";
    open.className = "button-link";
    open.textContent = t("openCurrentUrl");
    const release = document.createElement("button");
    release.type = "button";
    release.textContent = t("releaseControl");
    release.onclick = () => releaseActiveTakeover();
    actions.append(open, release);
    item.append(actions);
    return;
  }
  const stream = document.querySelector("#browser-stream");
  startTakeoverFramePolling(request, stream);
  if (request.request_type === "account_registration") {
    appendText(item, "p", t("registrationHandoffNote"), "flow-note");
  }
  appendText(item, "p", t("browserStreamNote"), "flow-note");
  const controls = document.createElement("div");
  controls.className = "takeover-controls";
  controls.innerHTML = `
    <label>${t("takeoverTextLabel")} <input type="password" autocomplete="off" data-takeover-text placeholder="${t("takeoverTextPlaceholder")}"></label>
    <div class="button-row">
      <button data-action="send-text">${t("sendText")}</button>
      <button data-action="enter-key">${t("sendEnter")}</button>
      <button data-action="release">${t("releaseControl")}</button>
    </div>
  `;
  controls.querySelector("[data-action='send-text']").onclick = () => {
    const input = controls.querySelector("[data-takeover-text]");
    sendTakeoverInput(request, { event_type: "type", text: input.value }).then((delivered) => {
      if (delivered) input.value = "";
    });
  };
  controls.querySelector("[data-action='enter-key']").onclick = () => sendTakeoverInput(request, { event_type: "key", key: "Enter" });
  controls.querySelector("[data-action='release']").onclick = () => releaseActiveTakeover();
  item.append(controls);
}

function renderApprovalControls(request, item) {
  const details = request.structured_details || {};
  const detailList = document.createElement("dl");
  detailList.className = "metadata approval-details";
  const rows = request.request_type === "console_restart" ? [
    [t("consoleRestartThread"), details.thread_id],
    [t("consoleRestartCurrentState"), details.current_state],
    [t("consoleRestartCurrentPid"), details.active_cli_pid],
    [t("consoleRestartPane"), details.legacy_pane_id],
    [t("consoleRestartNativeSync"), details.native_sync_active],
    [t("consoleRestartCommand"), details.restart_command],
    [t("consoleRestartAfterApproval"), details.after_approval || request.action_summary]
  ] : [
    ["Merchant", details.merchant],
    ["Amount", details.amount],
    ["Currency", details.currency],
    ["Recipient", details.recipient || details.payee],
    ["Shipping address", details.shipping_address],
    ["Billing method summary", details.billing_method_summary],
    ["Subscription / renewal", details.subscription || details.renewal],
    ["Refund / cancellation terms", details.refund_terms || details.cancellation_terms],
    ["Origin", details.origin || request.origin],
    ["Final button text", details.final_button],
    ["Review fingerprint", request.approval_fingerprint],
    ["Agent prepared action", request.action_summary],
    ["After approval", details.after_approval || "Submit only after approval"]
  ];
  rows.forEach(([label, value]) => {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = displayValue(value, "not visible");
    detailList.append(dt, dd);
  });
  item.append(detailList);
  const isActionable = request.status === "pending";
  let confirm = null;
  const needsExplicitConfirmation = request.request_type === "payment_approval" || request.request_type === "console_restart";
  if (needsExplicitConfirmation) {
    const confirmLabel = document.createElement("label");
    confirmLabel.className = "check-row approval-confirm";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.setAttribute(request.request_type === "payment_approval" ? "data-payment-confirm" : "data-approval-confirm", "");
    confirmLabel.append(checkbox, document.createTextNode(` ${
      request.request_type === "console_restart"
        ? t("consoleRestartConfirmText")
        : "I reviewed merchant, amount, recipient, origin, final button text, and after-approval result."
    }`));
    confirm = checkbox;
    confirm.disabled = !isActionable;
    item.append(confirmLabel);
  }
  const actions = document.createElement("div");
  actions.className = "button-row";
  const approve = document.createElement("button");
  approve.textContent = t("approve");
  approve.disabled = confirm ? true : !isActionable;
  if (confirm) confirm.onchange = () => { approve.disabled = !confirm.checked || !isActionable; };
  approve.onclick = () => {
    if (confirm && !confirm.checked) {
      setStatus(
        t(request.request_type === "console_restart" ? "consoleRestartReviewRequired" : "paymentReviewRequired"),
        t(request.request_type === "console_restart" ? "consoleRestartReviewRequiredDetail" : "paymentReviewRequiredDetail")
      );
      return;
    }
    postAction(request, "approve", confirm ? explicitApprovalConfirmationPayload(request) : null);
  };
  const deny = document.createElement("button");
  deny.textContent = t("deny");
  deny.disabled = !isActionable;
  deny.onclick = () => postAction(request, "deny");
  actions.append(deny, approve);
  item.append(actions);
}

function renderRequest(request) {
  const item = document.createElement("article");
  item.className = `request request-${requestKind(request)} ${isOpenRequest(request) ? "request-open" : "request-closed"}`;
  item.dataset.requestId = request.request_id;
  item.append(requestHeader(request));
  item.append(requestMetadata(request));
  if (request.request_type === "credential") {
    renderCredentialControls(request, item);
  } else if (request.request_type === "human_takeover" || request.request_type === "account_registration") {
    renderTakeoverControls(request, item);
  } else if (requestKind(request) === "approval") {
    renderApprovalControls(request, item);
  } else {
    renderChallengeControls(request, item);
  }
  return item;
}

function renderRequestList(requests, filter = activeFilter()) {
  const list = document.querySelector("#requests-list");
  const capturedDrafts = captureRequestDrafts(list);
  list.innerHTML = "";
  const openRequests = requests.filter(isOpenRequest);
  const visible = requests.filter((request) => requestMatchesFilter(request, filter));
  syncTakeoverPanel(requests);
  updatePaymentApprovalPanel(requests);
  updateChatSyncApprovalCard(pendingConsoleRestartRequest());
  updateAttentionStrip(openRequests);
  updateOverview();
  if (activeTakeoverFrameRequest && !requests.some((request) => request.request_id === activeTakeoverFrameRequest && request.status === "user_control")) {
    stopTakeoverFramePolling();
  }
  document.querySelector("#runtime-counts").textContent = t("requestsCount", openRequests.length, requests.length);
  if (!visible.length) {
    updateRequestsTabBadge(openRequests.length, requests.length);
    list.textContent = requests.length ? t("noMatchingOpenRequests") : t("noOpenRequests");
    restoreRequestDrafts(list, capturedDrafts);
    return;
  }
  updateRequestsTabBadge(openRequests.length, requests.length);
  visible.forEach((request) => list.append(renderRequest(request)));
  restoreRequestDrafts(list, capturedDrafts);
}

async function loadRuntimeStatus() {
  try {
    const status = await fetch("/api/status", { cache: "no-store" }).then((r) => r.json());
    cachedRuntimeStatus = status;
    const runner = status.chat_runner || {};
    let mode = t("runtimeModeCloudDirect", status.mode);
    let detail = t("runtimeDetail");
    let runtimeState = "";
    let restartCommand = "";
    let restartLabelKey = "restartBridge";
    let restartActionAvailable = true;
    if (modeRequiresPairing(status.mode) && !cachedPairingAuthenticated) {
      mode = t("runtimeModeUnpaired");
      detail = t("runtimeUnpairedDetail");
      runtimeState = "unpaired";
      restartActionAvailable = false;
    } else if (runner.waiting_for_tui_bridge) {
      const legacyRelay = runner.legacy_tui_relay || {};
      const activeProcess = runner.active_tui_process_bridge || {};
      const staleActiveBinary = Boolean(activeProcess.active && !activeProcess.native_bridge_ready && activeProcess.installed_bridge_ready);
      mode = legacyRelay.active ? t("runtimeModeLegacyRelay") : t("runtimeModeServerOnly");
      detail = legacyRelay.active ? t("runtimeLegacyRelayActive") : t("runtimeWaitingForConsoleRestart");
      if (legacyRelay.capabilities?.interrupt_on_pause) {
        detail = `${detail} ${t("runtimeLegacyRelayPause")}`;
      }
      const nativeBridge = runner.native_console_bridge || {};
      if (staleActiveBinary) {
        detail = `${detail} ${t("runtimeActiveConsoleNeedsBinaryRestart")}`;
      } else {
        detail = `${detail} ${nativeBridge.ready ? t("runtimeNativeBridgeReady") : t("runtimeNativeBridgeNotReady")}`;
      }
      runtimeState = legacyRelay.active ? "legacy_tui_relay" : "waiting_for_tui_bridge";
      restartCommand = runner.restart_command || "";
      restartLabelKey = pendingConsoleRestartRequest() ? "reviewSyncRequest" : runnerNeedsCurrentSessionSync(runner) ? "enableCurrentSessionSync" : "restartBridge";
      restartActionAvailable = runnerCanRestartCurrentConsole(runner);
    } else if (runner.tui_bridge_active) {
      mode = t("runtimeModeAttached");
      detail = t("runtimeBridgeActive");
      runtimeState = "tui_bridge_active";
    } else if (runner.thread_id) {
      mode = t("runtimeModeBackground");
      detail = t("runtimeBackgroundRunner");
      runtimeState = "background_runner";
    }
    updateChatSessionStatus(runner);
    setStatus(mode, detail, runtimeState, restartCommand, restartLabelKey, restartActionAvailable);
    updateOverview();
  } catch {
    cachedRuntimeStatus = null;
    updateChatSessionStatus(null, { offline: true });
    setStatus(t("runtimeModeOffline"), t("runtimeOfflineDetail"), "offline");
    updateOverview();
  }
}

function chatPayloadFingerprint(messages = [], records = [], terminal = null) {
  const lastMessage = messages[messages.length - 1] || {};
  const lastRecord = records[records.length - 1] || {};
  const terminalText = terminal?.text || "";
  return [
    messages.length,
    lastMessage.sequence || "",
    lastMessage.status || "",
    records.length,
    lastRecord.sequence || "",
    lastRecord.record_type || "",
    terminal?.available ? "terminal" : "",
    terminalText.length,
    terminalText.slice(-240)
  ].join("|");
}

function scheduleRealtimeRefreshFromChat() {
  if (realtimeRefreshTimer) return;
  realtimeRefreshTimer = setTimeout(() => {
    realtimeRefreshTimer = null;
    Promise.allSettled([
      loadRuntimeStatus(),
      loadRequests(),
      loadBrowserContexts()
    ]);
  }, 250);
}

async function loadRequests() {
  try {
    const requests = await signedFetch("/api/requests", { cache: "no-store" }).then((r) => {
      if (!r.ok) throw new Error("unauthorized");
      return r.json();
    });
    cachedRequests = requests;
    renderRequestList(requests);
  } catch {
    updateAttentionStrip([]);
    updateRequestsTabBadge(0, 0);
    document.querySelector("#requests-list").textContent = t("pairToViewRequests");
  }
}

async function loadBrowserContexts() {
  try {
    const payload = await signedFetch("/api/browser/contexts", { cache: "no-store" }).then((r) => {
      if (!r.ok) throw new Error("unauthorized");
      return r.json();
    });
    applyBrowserContextsEvent(payload);
  } catch {
    cachedBrowserContexts = [];
  }
}

function applyBrowserContextsEvent(payload) {
  cachedBrowserContexts = payload.contexts || [];
  syncTakeoverPanel(cachedRequests);
  maybeAutoStartPendingTakeover();
  updateOverview();
}

function applyRequestEvent(payload) {
  cachedRequests = payload.requests || [];
  renderRequestList(cachedRequests);
}

function applyChatEvent(payload) {
  const messages = payload.messages || [];
  const records = payload.records || [];
  const terminal = payload.terminal || null;
  const fingerprint = chatPayloadFingerprint(messages, records, terminal);
  const changed = fingerprint !== lastChatPayloadFingerprint;
  lastChatPayloadFingerprint = fingerprint;
  cachedChatMessages = messages;
  cachedChatRecords = records;
  cachedChatTerminal = terminal;
  renderChatTimeline(cachedChatMessages, cachedChatRecords, cachedChatTerminal);
  updateOverview();
  if (changed) scheduleRealtimeRefreshFromChat();
}

function handleSseBlock(block) {
  let eventName = "message";
  let data = "";
  block.split("\n").forEach((line) => {
    if (line.startsWith("event:")) eventName = line.slice(6).trim();
    if (line.startsWith("data:")) data += line.slice(5).trim();
  });
  if (eventName === "requests" && data) {
    applyRequestEvent(JSON.parse(data));
  }
  if (eventName === "chat" && data) {
    applyChatEvent(JSON.parse(data));
  }
  if (eventName === "browser_contexts" && data) {
    applyBrowserContextsEvent(JSON.parse(data));
  }
}

async function startRequestStream() {
  if (requestStreamActive || !window.ReadableStream) return;
  requestStreamActive = true;
  if (requestStreamRestart) clearTimeout(requestStreamRestart);
  try {
    const response = await signedFetch("/api/events?stream=1&snapshots=1200&interval=2", { cache: "no-store" });
    if (!response.ok || !response.body) throw new Error("request stream unavailable");
    const reader = response.body.getReader();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop();
      blocks.filter(Boolean).forEach(handleSseBlock);
    }
  } catch {
    if (!cachedRequests.length) {
      document.querySelector("#requests-list").textContent = t("pairToReceiveEvents");
    }
  } finally {
    requestStreamActive = false;
    requestStreamRestart = setTimeout(startRequestStream, 3000);
  }
}

function websocketUrl(path) {
  const url = new URL(path, window.location.origin);
  url.protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}

async function startRequestWebSocket() {
  if (!window.WebSocket) {
    startRequestStream();
    return;
  }
  if (requestStreamActive) return;
  requestStreamActive = true;
  if (requestStreamRestart) clearTimeout(requestStreamRestart);
  const path = "/api/ws/requests";
  try {
    const protocol = await deviceAuthSubprotocol("GET", path);
    const socket = protocol
      ? new WebSocket(websocketUrl(`${path}?snapshots=1200&interval=2`), [protocol])
      : new WebSocket(websocketUrl(`${path}?snapshots=1200&interval=2`));
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.event === "requests") applyRequestEvent(message.data);
    };
    socket.onerror = () => {
      socket.close();
    };
    socket.onclose = () => {
      requestStreamActive = false;
      requestStreamRestart = setTimeout(startRequestWebSocket, 3000);
    };
  } catch {
    requestStreamActive = false;
    startRequestStream();
  }
}

async function startBrowserContextStream() {
  if (browserContextStreamActive || !window.ReadableStream) return;
  browserContextStreamActive = true;
  if (browserContextStreamRestart) clearTimeout(browserContextStreamRestart);
  try {
    const response = await signedFetch("/api/browser/contexts/events?stream=1&snapshots=1200&interval=1", { cache: "no-store" });
    if (!response.ok || !response.body) throw new Error("browser context stream unavailable");
    const reader = response.body.getReader();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop();
      blocks.filter(Boolean).forEach(handleSseBlock);
    }
  } catch {
    await loadBrowserContexts();
  } finally {
    browserContextStreamActive = false;
    browserContextStreamRestart = setTimeout(startBrowserContextStream, 3000);
  }
}

async function startBrowserContextWebSocket() {
  if (!window.WebSocket) {
    startBrowserContextStream();
    return;
  }
  if (browserContextStreamActive) return;
  browserContextStreamActive = true;
  if (browserContextStreamRestart) clearTimeout(browserContextStreamRestart);
  const path = "/api/ws/browser/contexts";
  try {
    const protocol = await deviceAuthSubprotocol("GET", path);
    const socket = protocol
      ? new WebSocket(websocketUrl(`${path}?snapshots=1200&interval=1`), [protocol])
      : new WebSocket(websocketUrl(`${path}?snapshots=1200&interval=1`));
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.event === "browser_contexts") applyBrowserContextsEvent(message.data);
    };
    socket.onerror = () => {
      socket.close();
    };
    socket.onclose = () => {
      browserContextStreamActive = false;
      browserContextStreamRestart = setTimeout(startBrowserContextWebSocket, 3000);
    };
  } catch {
    browserContextStreamActive = false;
    startBrowserContextStream();
  }
}

async function startChatStream() {
  if (chatStreamActive || !window.ReadableStream) return;
  chatStreamActive = true;
  if (chatStreamRestart) clearTimeout(chatStreamRestart);
  try {
    const response = await signedFetch("/api/chat/events?stream=1&snapshots=1200&interval=0.25", { cache: "no-store" });
    if (!response.ok || !response.body) throw new Error("chat stream unavailable");
    const reader = response.body.getReader();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop();
      blocks.filter(Boolean).forEach(handleSseBlock);
    }
  } catch {
    if (!cachedChatMessages.length && !cachedChatRecords.length) {
      document.querySelector("#chat-messages").textContent = t("pairToViewChat");
    }
  } finally {
    chatStreamActive = false;
    chatStreamRestart = setTimeout(startChatStream, 3000);
  }
}

async function startChatWebSocket() {
  if (!window.WebSocket) {
    startChatStream();
    return;
  }
  if (chatStreamActive) return;
  chatStreamActive = true;
  if (chatStreamRestart) clearTimeout(chatStreamRestart);
  const path = "/api/ws/chat";
  try {
    const protocol = await deviceAuthSubprotocol("GET", path);
    const socket = protocol
      ? new WebSocket(websocketUrl(`${path}?snapshots=1200&interval=0.25`), [protocol])
      : new WebSocket(websocketUrl(`${path}?snapshots=1200&interval=0.25`));
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.event === "chat") applyChatEvent(message.data);
    };
    socket.onerror = () => {
      socket.close();
    };
    socket.onclose = () => {
      chatStreamActive = false;
      chatStreamRestart = setTimeout(startChatWebSocket, 3000);
    };
  } catch {
    chatStreamActive = false;
    startChatStream();
  }
}

function authenticatedApiAvailable() {
  if (cachedPairingAuthenticated) return true;
  if (!cachedRuntimeStatus) return false;
  return !modeRequiresPairing(cachedRuntimeStatus.mode);
}

async function refreshAuthenticatedData() {
  if (!authenticatedApiAvailable()) return;
  await Promise.allSettled([
    loadRequests(),
    loadBrowserContexts(),
    loadChatMessages(),
    loadDevicesAndSessions()
  ]);
}

function startAuthenticatedRealtime() {
  if (!authenticatedApiAvailable() || authenticatedRealtimeStarted) return;
  authenticatedRealtimeStarted = true;
  startRequestWebSocket();
  startBrowserContextWebSocket();
  startChatWebSocket();
}

async function bootstrapControlClient() {
  await loadRuntimeStatus();
  if (initialPairingCode) {
    await autoPairFromInitialLink();
  } else {
    await refreshPairingState();
  }
  await loadRuntimeStatus();
  await refreshAuthenticatedData();
  startAuthenticatedRealtime();
}

bootstrapControlClient().catch(() => {});
document.addEventListener("visibilitychange", handleTakeoverVisibilityChange);
setInterval(loadRuntimeStatus, 10000);
setInterval(refreshPairingState, 30000);
setInterval(() => {
  if (authenticatedApiAvailable()) loadRequests();
}, 15000);
setInterval(() => {
  if (authenticatedApiAvailable()) loadBrowserContexts();
}, 5000);
setInterval(() => {
  if (authenticatedApiAvailable()) loadChatMessages();
}, 5000);
setInterval(() => {
  if (authenticatedApiAvailable()) loadDevicesAndSessions();
}, 15000);
