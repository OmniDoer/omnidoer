const I18N = {
  en: {
    appTitle: "OmniDoer Control Client",
    appSubtitle: "Secure approvals, credentials, challenges, and human takeover.",
    navRequests: "Requests",
    navTasks: "Chat",
    navDevices: "Devices",
    navSecurity: "Security",
    navTakeover: "Takeover",
    navPayments: "Payments",
    navPair: "Pair",
    checkingRuntime: "Checking runtime...",
    runtimeDetail: "Control Client does not call OpenAI APIs or models directly.",
    runtimeOffline: "Runtime offline",
    runtimeOfflineDetail: "Start omnidoer control serve.",
    runtimeBridgeActive: "Live Linux console bridge is active; messages sync with the current TUI.",
    runtimeLegacyRelayActive: "Temporary terminal relay is active; messages are injected into the current console. Restart for full structured sync:",
    runtimeWaitingForConsoleRestart: "Linux console is active but not yet bridged. Restart OmniDoer console with:",
    runtimeBackgroundRunner: "No live Linux console bridge; queued messages use the background Codex runner.",
    legacyTerminalTitle: "Live Linux Console",
    requestsCount: (open, total) => `Requests: ${open} open / ${total} total`,
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
    pairFreshLink: "Not paired. Use a fresh pairing link only once; after pairing this browser reuses its cached session.",
    checkingCachedSession: "Checking cached pairing session...",
    sessionHidden: "This browser is authenticated. The current session is not visible in the latest session list.",
    sessionRevoked: "This browser's cached session was revoked. Pair again to continue.",
    pairedCached: "Paired. Requests load automatically; pair again only if this session expires or is revoked.",
    cachedPairingRejected: "Cached pairing cannot access this Control Service. Use a fresh pairing link or forget local pairing.",
    pairingDevice: "Pairing this device...",
    pairingFailed: "Pairing failed.",
    pairedDevice: (name) => `Paired ${name}. This browser will reuse the cached session until it expires or is revoked.`,
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
    submitTask: "Submit Task",
    noQueuedTasks: "No queued tasks.",
    pairToViewTasks: "Pair this device to view task queue in Cloud Direct Mode.",
    takeoverTitle: "Human Takeover",
    takeoverNoActive: "No active takeover",
    noActiveBrowserHandoff: "No active browser handoff.",
    activeBrowserReady: "Active browser detected. Pause Agent to take over this browser.",
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
      denied: "Denied",
      expired: "Expired",
      challenge_completed: "Challenge completed"
    },
    requestTypeLabels: {
      credential: "Credential",
      human_takeover: "Human takeover",
      account_registration: "Account registration",
      payment_approval: "Payment approval",
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
    navRequests: "请求",
    navTasks: "对话",
    navDevices: "设备",
    navSecurity: "安全",
    navTakeover: "接管",
    navPayments: "支付",
    navPair: "配对",
    checkingRuntime: "正在检查运行状态...",
    runtimeDetail: "控制客户端不会直接调用 OpenAI API 或模型。",
    runtimeOffline: "运行服务离线",
    runtimeOfflineDetail: "请启动 omnidoer control serve。",
    runtimeBridgeActive: "Linux 控制台实时桥接已启用；消息会同步到当前 TUI。",
    runtimeLegacyRelayActive: "临时终端 relay 已启用；消息会注入当前 console。请重启以获得完整结构化同步：",
    runtimeWaitingForConsoleRestart: "Linux 控制台仍在运行但尚未桥接。请用下面命令重启 OmniDoer console：",
    runtimeBackgroundRunner: "没有实时 Linux 控制台桥接；排队消息将由后台 Codex runner 处理。",
    legacyTerminalTitle: "实时 Linux 控制台",
    requestsCount: (open, total) => `请求：${open} 个待处理 / 共 ${total} 个`,
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
    pairFreshLink: "未配对。配对链接只能使用一次；配对后浏览器会复用本地会话。",
    checkingCachedSession: "正在检查本地配对会话...",
    sessionHidden: "此浏览器已认证，但当前会话不在最新会话列表中。",
    sessionRevoked: "此浏览器缓存的会话已被撤销，请重新配对。",
    pairedCached: "已配对。请求会自动加载；只有会话过期或被撤销时才需要重新配对。",
    cachedPairingRejected: "缓存配对无法访问此 Control Service，请使用新的配对链接或清除本地配对。",
    pairingDevice: "正在配对此设备...",
    pairingFailed: "配对失败。",
    pairedDevice: (name) => `已配对 ${name}。此浏览器会复用本地会话，直到会话过期或被撤销。`,
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
    submitTask: "提交任务",
    noQueuedTasks: "没有排队任务。",
    pairToViewTasks: "请先配对此设备以查看 Cloud Direct 任务队列。",
    takeoverTitle: "人工接管",
    takeoverNoActive: "没有活跃接管",
    noActiveBrowserHandoff: "没有活跃浏览器接管。",
    activeBrowserReady: "检测到活跃浏览器。点击暂停 Agent 即可接管此浏览器。",
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
      denied: "已拒绝",
      expired: "已过期",
      challenge_completed: "验证已完成"
    },
    requestTypeLabels: {
      credential: "凭证",
      human_takeover: "人工接管",
      account_registration: "账号注册",
      payment_approval: "支付授权",
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
    navRequests: "Solicitudes", navTasks: "Tareas", navDevices: "Dispositivos", navSecurity: "Seguridad", navTakeover: "Control", navPayments: "Pagos",
    requestsTitle: "Solicitudes pendientes", filterOpen: "Pendientes", filterAll: "Todas", filterCredential: "Secretos", filterChallenge: "Verificaciones", filterApproval: "Aprobaciones", filterTakeover: "Control",
    chatFilesLabel: "Adjuntar", chatSelectedFiles: "Archivos seleccionados", uploadFailed: "Carga fallida",
    pauseAgent: "Pausar Agent", pauseAgentRequested: "Pausa solicitada", pauseAgentRequestDetail: "La solicitud quedo en cola para la consola Linux activa.", takeoverPausePrompt: "Pausa ahora la automatizacion del navegador y entrega el navegador activo a mi Control Client. Si hay un navegador activo, crea o conserva una solicitud Human Takeover, transmite la pagina y espera hasta que toque Continue Agent antes de reanudar.", releaseControl: "Continuar Agent", openCurrentUrl: "Abrir URL actual", externalHandoffNote: "Abre la URL actual, completa la accion en el sitio y continua el Agent. Secretos y codigos no se envian al modelo.",
    submitCredential: "Enviar credencial", submitChallenge: "Enviar codigo", approve: "Aprobar", deny: "Denegar", challengeCode: "Codigo de un solo uso"
  },
  fr: {
    appSubtitle: "Approbations, identifiants, validations et prise de controle securises.",
    navRequests: "Demandes", navTasks: "Taches", navDevices: "Appareils", navSecurity: "Securite", navTakeover: "Controle", navPayments: "Paiements",
    requestsTitle: "Demandes en attente", filterOpen: "En attente", filterAll: "Toutes", filterCredential: "Secrets", filterChallenge: "Verifications", filterApproval: "Approbations", filterTakeover: "Controle",
    chatFilesLabel: "Joindre", chatSelectedFiles: "Fichiers selectionnes", uploadFailed: "Echec d'envoi",
    pauseAgent: "Mettre Agent en pause", pauseAgentRequested: "Pause demandee", pauseAgentRequestDetail: "La demande est en file pour la console Linux active.", takeoverPausePrompt: "Mettez maintenant l'automatisation du navigateur en pause et remettez le navigateur actif a mon Control Client. Si un navigateur est actif, creez ou gardez une demande Human Takeover, diffusez la page, puis attendez que je touche Continue Agent avant de reprendre.", releaseControl: "Continuer Agent", openCurrentUrl: "Ouvrir l'URL", externalHandoffNote: "Ouvrez l'URL, terminez l'action sur le site, puis continuez l'Agent. Les secrets et codes ne sont pas envoyes au modele.",
    submitCredential: "Envoyer l'identifiant", submitChallenge: "Envoyer le code", approve: "Approuver", deny: "Refuser", challengeCode: "Code a usage unique"
  },
  de: {
    appSubtitle: "Sichere Freigaben, Zugangsdaten, Pruefungen und manuelle Uebernahme.",
    navRequests: "Anfragen", navTasks: "Aufgaben", navDevices: "Geraete", navSecurity: "Sicherheit", navTakeover: "Uebernahme", navPayments: "Zahlungen",
    requestsTitle: "Offene Anfragen", filterOpen: "Offen", filterAll: "Alle", filterCredential: "Secrets", filterChallenge: "Pruefungen", filterApproval: "Freigaben", filterTakeover: "Uebernahme",
    chatFilesLabel: "Anhaengen", chatSelectedFiles: "Ausgewaehlte Dateien", uploadFailed: "Upload fehlgeschlagen",
    pauseAgent: "Agent pausieren", pauseAgentRequested: "Pause angefordert", pauseAgentRequestDetail: "Die Anfrage wurde fuer die aktive Linux-Konsole eingereiht.", takeoverPausePrompt: "Pausiere jetzt die Browser-Automation und uebergib den aktiven Browser an meinen Control Client. Falls ein Browser aktiv ist, erstelle oder behalte eine Human-Takeover-Anfrage, streame die Seite und warte, bis ich Continue Agent antippe.", releaseControl: "Agent fortsetzen", openCurrentUrl: "Aktuelle URL oeffnen", externalHandoffNote: "Oeffnen Sie die aktuelle URL, erledigen Sie die Aktion selbst und setzen Sie danach den Agent fort. Secrets und Codes werden nicht an das Modell gesendet.",
    submitCredential: "Zugangsdaten senden", submitChallenge: "Code senden", approve: "Genehmigen", deny: "Ablehnen", challengeCode: "Einmalcode"
  },
  ja: {
    appSubtitle: "承認、認証情報、検証、人間による操作を安全に扱います。",
    navRequests: "リクエスト", navTasks: "タスク", navDevices: "デバイス", navSecurity: "セキュリティ", navTakeover: "操作", navPayments: "支払い",
    requestsTitle: "未処理リクエスト", filterOpen: "未処理", filterAll: "すべて", filterCredential: "シークレット", filterChallenge: "検証", filterApproval: "承認", filterTakeover: "操作",
    chatFilesLabel: "添付", chatSelectedFiles: "選択したファイル", uploadFailed: "アップロード失敗",
    pauseAgent: "Agentを一時停止", pauseAgentRequested: "一時停止を依頼しました", pauseAgentRequestDetail: "依頼はアクティブなLinuxコンソールにキューされました。", takeoverPausePrompt: "現在のブラウザ自動操作を一時停止し、アクティブなブラウザをControl Clientへ渡してください。ブラウザが動作中ならHuman Takeoverリクエストを作成または維持し、画面をストリーミングして、Continue Agentをタップするまで待機してください。", releaseControl: "Agentを続行", openCurrentUrl: "現在のURLを開く", externalHandoffNote: "現在のURLを開き、サイト上の操作を自分で完了してからAgentを続行してください。パスワードやコードはモデルに送信されません。",
    submitCredential: "認証情報を送信", submitChallenge: "コードを送信", approve: "承認", deny: "拒否", challengeCode: "ワンタイムコード"
  },
  ko: {
    appSubtitle: "승인, 자격 증명, 인증, 사용자 제어를 안전하게 처리합니다.",
    navRequests: "요청", navTasks: "작업", navDevices: "기기", navSecurity: "보안", navTakeover: "제어", navPayments: "결제",
    requestsTitle: "대기 중인 요청", filterOpen: "대기", filterAll: "전체", filterCredential: "비밀", filterChallenge: "인증", filterApproval: "승인", filterTakeover: "제어",
    chatFilesLabel: "첨부", chatSelectedFiles: "선택한 파일", uploadFailed: "업로드 실패",
    pauseAgent: "Agent 일시 중지", pauseAgentRequested: "일시 중지 요청됨", pauseAgentRequestDetail: "요청이 활성 Linux 콘솔에 대기열로 전달되었습니다.", takeoverPausePrompt: "현재 브라우저 자동화를 즉시 일시 중지하고 활성 브라우저를 내 Control Client로 넘겨주세요. 브라우저가 실행 중이면 Human Takeover 요청을 만들거나 유지하고, 페이지를 스트리밍한 뒤 내가 Continue Agent를 탭할 때까지 기다려주세요.", releaseControl: "Agent 계속", openCurrentUrl: "현재 URL 열기", externalHandoffNote: "현재 URL을 열고 사이트 작업을 직접 완료한 뒤 Agent를 계속하세요. 비밀번호와 코드는 모델로 전송되지 않습니다.",
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
  "task-panel",
  "requests-panel",
  "takeover-panel",
  "device-panel",
  "security",
  "payment-approval",
  "pairing-panel"
];
const DEFAULT_PANEL_ID = "task-panel";

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

function languageTag(lang) {
  return { zh: "zh-CN", ja: "ja", ko: "ko", es: "es", fr: "fr", de: "de" }[lang] || "en";
}

function applyLanguage() {
  document.documentElement.lang = languageTag(currentLanguage);
  setNodeText(".app-header h1", "appTitle");
  setNodeText(".app-header p", "appSubtitle");
  const languageSelect = document.querySelector("#language-select");
  if (languageSelect) languageSelect.value = currentLanguage;
  setNodeText('a[href="#requests-panel"]', "navRequests");
  setNodeText('a[href="#task-panel"]', "navTasks");
  setNodeText('a[href="#device-panel"]', "navDevices");
  setNodeText('a[href="#security"]', "navSecurity");
  setNodeText('a[href="#takeover-panel"]', "navTakeover");
  setNodeText('a[href="#payment-approval"]', "navPayments");
  setNodeText('a[href="#pairing-panel"]', "navPair");
  setNodeText("#requests-panel h2", "requestsTitle");
  setNodeText("#requests-panel .panel-heading p", "requestsIntro");
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
  setNodeText("#chat-input-label-text", "chatComposerLabel");
  const chatInput = document.querySelector("#chat-input");
  if (chatInput) chatInput.placeholder = t("chatPlaceholder");
  setNodeText("#chat-files-label", "chatFilesLabel");
  setButtonText("#send-chat-message", "sendMessage");
  setButtonText("#submit-task", "submitTask");
  setNodeText("#takeover-panel h2", "takeoverTitle");
  setNodeText("#payment-approval h2", "paymentTitle");
  setNodeText("#approval-status", "noPendingPayment");
  setButtonText("#request-takeover-pause", "pauseAgent");
  setButtonText("#release-active-takeover", "releaseControl");
  setButtonText("#approve", "approve");
  setButtonText("#deny", "deny");
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

const main = document.querySelector("main");

const runtimeStatus = document.createElement("section");
runtimeStatus.id = "runtime-status";
runtimeStatus.className = "status-strip";
runtimeStatus.innerHTML = `
  <div>
    <strong id="runtime-mode">${t("checkingRuntime")}</strong>
    <span id="runtime-detail">${t("runtimeDetail")}</span>
    <code id="runtime-command" hidden></code>
  </div>
  <div id="runtime-counts">${t("requestsCount", 0, 0)}</div>
`;
main.insertBefore(runtimeStatus, document.querySelector("#pairing-panel"));

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

const releaseActiveTakeoverButton = document.querySelector("#release-active-takeover");
if (releaseActiveTakeoverButton) {
  releaseActiveTakeoverButton.onclick = () => releaseActiveTakeover();
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
    renderChatTimeline(cachedChatMessages, cachedChatRecords);
  };
}

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.onclick = () => {
    document.querySelectorAll("[data-filter]").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    renderRequestList(cachedRequests, button.dataset.filter);
  };
});

const encoder = new TextEncoder();
const decoder = new TextDecoder();
const TAKEOVER_FRAME_MAX_AGE_MS = 30000;
const TAKEOVER_FRAME_POLL_MS = 1500;
const TAKEOVER_FRAME_AFTER_INPUT_MS = 180;
const TAKEOVER_FRAME_WS_SNAPSHOTS = 120;
const TAKEOVER_FRAME_WS_INTERVAL_SECONDS = 0.75;
const TAKEOVER_FRAME_PROFILE_DEFAULT = "balanced";
const TAKEOVER_FRAME_PROFILE_DATA_SAVER = "data_saver";
const TAKEOVER_ZOOM_MIN = 1;
const TAKEOVER_ZOOM_MAX = 3;
const TAKEOVER_ZOOM_STEP = 0.25;
let cachedRequests = [];
let cachedChatMessages = [];
let cachedChatRecords = [];
let cachedBrowserContexts = [];
let requestStreamActive = false;
let requestStreamRestart = null;
let chatStreamActive = false;
let chatStreamRestart = null;
let activeTakeoverFrameRequest = null;
let takeoverFrameTimer = null;
let takeoverFreshnessTimer = null;
let takeoverFrameRefreshTimer = null;
let takeoverFrameFetchInFlight = false;
let takeoverFrameFetchQueued = false;
let takeoverFrameSocket = null;
let takeoverFrameSocketRequest = null;
let takeoverFrameSocketRestart = null;
let takeoverFrameMisses = 0;
let takeoverFrameVisibilityPaused = false;
let takeoverFrameZoom = TAKEOVER_ZOOM_MIN;
let takeoverFramePanMode = false;
let activePaymentApprovalRequest = null;
let renderedPaymentApprovalRequestId = null;

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

function requestKind(request) {
  if (request.request_type === "credential") return "credential";
  if (request.request_type === "human_takeover" || request.request_type === "account_registration") return "takeover";
  if (["file_upload", "account_delete", "password_change", "two_factor_change", "message_send"].includes(request.request_type)) return "approval";
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

function setStatus(message, detail = "", runtimeState = "", command = "") {
  document.querySelector("#runtime-mode").textContent = message;
  document.querySelector("#runtime-detail").textContent = detail;
  const runtimeCommand = document.querySelector("#runtime-command");
  if (runtimeCommand) {
    runtimeCommand.textContent = command;
    runtimeCommand.hidden = !command;
  }
  document.body.dataset.runtimeState = runtimeState;
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

function setPairingUiState({ state, message, deviceText = "" }) {
  const panel = document.querySelector("#pairing-panel");
  const status = document.querySelector("#pairing-status");
  const currentDevice = document.querySelector("#pairing-current-device");
  const forgetButton = document.querySelector("#forget-local-pairing");
  if (panel) panel.dataset.pairingState = state;
  if (status) status.textContent = message;
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
    field.textContent = "waiting for browser handoff";
    field.className = "";
    return;
  }
  const seconds = Math.round(age / 1000);
  const stale = age > TAKEOVER_FRAME_MAX_AGE_MS;
  field.textContent = stale ? `stale ${seconds}s - refresh before input` : `fresh ${seconds}s`;
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

function updateTakeoverZoomControls() {
  const isActive = takeoverIsActive();
  const zoomed = takeoverFrameZoom > TAKEOVER_ZOOM_MIN;
  const zoomOut = document.querySelector("#zoom-out-takeover-frame");
  const zoomReset = document.querySelector("#zoom-reset-takeover-frame");
  const zoomIn = document.querySelector("#zoom-in-takeover-frame");
  const pan = document.querySelector("#pan-takeover-frame");
  if (zoomOut) zoomOut.disabled = !isActive || !zoomed;
  if (zoomReset) zoomReset.disabled = !isActive || (!zoomed && !takeoverFramePanMode);
  if (zoomIn) zoomIn.disabled = !isActive || takeoverFrameZoom >= TAKEOVER_ZOOM_MAX;
  if (pan) {
    pan.disabled = !isActive || !zoomed;
    pan.textContent = takeoverFramePanMode ? "Pan On" : "Pan View";
    pan.setAttribute("aria-pressed", takeoverFramePanMode ? "true" : "false");
  }
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
  setFieldText("#takeover-frame-zoom", `${zoomPercent}%${takeoverFramePanMode ? " pan" : ""}`);
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
  const status = request ? (request.status === "user_control" ? "Agent paused - user control active" : request.status) : t("takeoverNoActive");
  setFieldText("#takeover-status-label", status);
  setFieldText("#takeover-active-request", request?.request_id, "pending");
  setFieldText("#takeover-current-url", request?.top_level_url || request?.origin, "pending");
  if (frame) {
    setFieldText("#takeover-frame-meta", frame.url || frame.origin || request?.top_level_url, "waiting for browser handoff");
    setFieldText("#takeover-frame-profile", takeoverFrameProfileLabel(frame), "adaptive");
  } else {
    setFieldText("#takeover-frame-meta", request ? "waiting for next browser frame" : "waiting for browser handoff");
    setFieldText("#takeover-frame-profile", request ? takeoverFrameProfileLabel() : "adaptive", "adaptive");
  }
  setFieldText("#takeover-input-state", message || (request ? "Touch, keyboard, and text input are routed to the controlled browser only." : t("noActiveBrowserHandoff")), "");
  updateTakeoverFrameFreshness();
  const isActive = Boolean(request && request.status === "user_control");
  const refresh = document.querySelector("#refresh-takeover-frame");
  const pause = document.querySelector("#request-takeover-pause");
  const release = document.querySelector("#release-active-takeover");
  if (pause) pause.disabled = isActive;
  if (refresh) refresh.disabled = !isActive;
  if (release) release.disabled = !isActive;
  updateTakeoverZoomControls();
}

function syncTakeoverPanel(requests) {
  const stream = document.querySelector("#browser-stream");
  const request = findActiveTakeoverRequest(requests);
  if (!stream) return;
  if (!request) {
    stopTakeoverFramePolling();
    updateTakeoverPanel(null);
    const context = activeBrowserContext();
    if (context) {
      setFieldText("#takeover-current-url", context.current_url || context.origin, "pending");
      setFieldText("#takeover-frame-meta", context.browser_context_id, "waiting for browser handoff");
      setFieldText("#takeover-input-state", t("activeBrowserReady"), "");
      stream.textContent = t("activeBrowserReady");
    } else {
      stream.textContent = t("noActiveBrowserHandoff");
    }
    return;
  }
  updateTakeoverPanel(request);
  startTakeoverFramePolling(request, stream);
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

function releaseActiveTakeover() {
  const request = activeTakeoverRequest();
  if (!request) return;
  postAction(request, "release");
}

function renderTakeoverFrame(request, stream, frame, message = "Live browser frame ready. Input is bound to the frame currently visible here.") {
  if (!frame.data_b64) {
    markTakeoverFrameReconnect(request, stream, "Browser context is not connected in this process.");
    return;
  }
  const image = document.createElement("img");
  image.id = "takeover-frame";
  image.alt = "Controlled browser frame";
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
  updateTakeoverFrameConnection("connected", "connected");
  updateTakeoverPanel(request, frame, message);
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

function paymentApprovalConfirmationPayload(request) {
  return {
    explicit_user_confirmation: true,
    request_id: request.request_id,
    confirmed_at: new Date().toISOString()
  };
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
  } catch {
    document.querySelector("#pairing-broker-fingerprint").textContent = "pairing metadata unavailable";
    document.querySelector("#pairing-web-broker-fingerprint").textContent = "pairing metadata unavailable";
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
  const { publicJwk } = await deviceKeyPair();
  const response = await fetch("/api/pair", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ code, device_name: deviceName, device_public_key: JSON.stringify(publicJwk) })
  });
  const payload = await response.json();
  if (!response.ok) {
    document.querySelector("#pairing-status").textContent = t("pairingFailed");
    return;
  }
  localStorage.setItem("omnidoer_device_id", payload.device.device_id);
  localStorage.setItem("omnidoer_session_id", payload.session.session_id);
  localStorage.setItem("omnidoer_csrf_token", payload.csrf_token);
  setPairingUiState({
    state: "paired",
    message: t("pairedDevice", payload.device.name),
    deviceText: `${payload.device.device_id} - session expires ${formatTimestamp(payload.session.expires_at)}`
  });
  await loadRequests();
  await loadDevicesAndSessions();
}

function forgetLocalPairing() {
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
  }
  await loadRequests();
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
  input.value = "";
  if (fileInput) fileInput.value = "";
  renderSelectedChatFiles();
  await loadChatMessages();
}

async function requestTakeoverPause() {
  const button = document.querySelector("#request-takeover-pause");
  if (button) button.disabled = true;
  await loadBrowserContexts();
  const context = activeBrowserContext();
  let browserTakeoverStarted = false;
  if (context) {
    try {
      const response = await signedFetch(`/api/browser/contexts/${encodeURIComponent(context.browser_context_id)}/takeover`, {
        method: "POST",
        headers: { "content-type": "application/json", ...csrfHeaders() },
        body: JSON.stringify({ reason: t("takeoverPausePrompt") })
      });
      if (!response.ok) throw new Error("browser takeover failed");
      browserTakeoverStarted = true;
    } catch {
      setStatus(t("actionFailed"), t("activeBrowserReady"));
    }
  }
  const clientMessageId = `control_pause_${Date.now()}_${Math.random().toString(16).slice(2)}`;
  try {
    const response = await postChatMessage(t("takeoverPausePrompt"), { clientMessageId });
    if (!response.ok) throw new Error("pause request failed");
  } catch {
    setStatus(t("actionFailed"), t("pairToViewChat"));
    if (button) button.disabled = false;
    return;
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
  if (button) button.disabled = false;
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
    tool_output: t("chatRecordToolOutput")
  }[type] || type;
}

function renderChatMessage(message) {
  const item = document.createElement("article");
  item.className = `chat-message chat-role-${message.role} chat-status-${message.status}`;
  const header = document.createElement("div");
  header.className = "chat-message-header";
  appendText(header, "strong", message.role === "user" ? "You" : "OmniDoer");
  appendText(header, "span", chatStatusLabel(message.status), "badge");
  item.append(header);
  appendText(item, "p", message.text || " ", "chat-message-text");
  const meta = document.createElement("div");
  meta.className = "chat-message-meta";
  appendText(meta, "span", `#${message.sequence}`);
  if (message.source) appendText(meta, "span", message.source);
  item.append(meta);
  return item;
}

function renderChatRecord(record) {
  const item = document.createElement("article");
  item.className = `chat-record chat-record-${record.record_type}`;
  const header = document.createElement("div");
  header.className = "chat-message-header";
  appendText(header, "strong", chatRecordTypeLabel(record.record_type));
  if (record.role) appendText(header, "span", record.role, "badge");
  if (record.source) appendText(header, "span", record.source, "badge");
  item.append(header);
  appendText(item, "p", record.text || " ", "chat-message-text");
  const meta = document.createElement("div");
  meta.className = "chat-message-meta";
  appendText(meta, "span", `record #${record.sequence}`);
  if (record.message_id) appendText(meta, "span", record.message_id);
  item.append(meta);
  return item;
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

function renderChatTimeline(messages, records = [], terminal = null) {
  const list = document.querySelector("#chat-messages");
  if (!list) return;
  list.innerHTML = "";
  const terminalNode = renderLegacyTerminal(terminal);
  if (terminalNode) list.append(terminalNode);
  if (records.length) {
    records.forEach((record) => list.append(renderChatRecord(record)));
    list.scrollTop = list.scrollHeight;
    return;
  }
  if (!messages.length) {
    list.textContent = t("noChatMessages");
    return;
  }
  messages.forEach((message) => list.append(renderChatMessage(message)));
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
    renderChatTimeline(cachedChatMessages, cachedChatRecords, payload.terminal || null);
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
    setPairingUiState({ state: "offline", message: t("controlOffline") });
    return false;
  }
  if (runtime.mode === "local_dev") {
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
      setPairingUiState({
        state: "paired",
        message: t("sessionHidden"),
        deviceText: identity.deviceId
      });
      return true;
    }
    if (current.revoked) {
      setPairingUiState({
        state: "stale",
        message: t("sessionRevoked"),
        deviceText: `${identity.deviceId} - revoked`
      });
      return false;
    }
    setPairingUiState({
      state: "paired",
      message: t("pairedCached"),
      deviceText: `${identity.deviceId} - session expires ${formatTimestamp(current.expires_at)}`
    });
    return true;
  } catch {
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
    updateTakeoverPanel(request, null, "Input is blocked while this Control Client is hidden or frame polling is paused. Bring it to the foreground and refresh the frame before sending input.");
    return false;
  }
  const frameId = eventPayload.frame_id || stream?.dataset.frameId || "";
  if (!frameId) {
    updateTakeoverPanel(request, null, "Wait for the current browser frame before sending input.");
    return false;
  }
  if (!takeoverFrameIsFresh(stream)) {
    updateTakeoverPanel(request, null, "Frame is stale; refreshing before input.");
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
  if (response.ok) {
    updateTakeoverPanel(request, null, `${eventPayload.event_type} delivered to controlled browser.`);
    scheduleTakeoverFrameRefresh(request, TAKEOVER_FRAME_AFTER_INPUT_MS);
    return true;
  } else {
    let error = "";
    try {
      error = (await response.json()).error || "";
    } catch {
      error = "";
    }
    if (error === "stale_takeover_frame") {
      updateTakeoverPanel(request, null, "Frame changed before input was delivered. Refreshing current browser frame.");
      refreshActiveTakeoverFrame();
      return false;
    }
    updateTakeoverPanel(request, null, "Input was not delivered. The browser context may be disconnected.");
    scheduleTakeoverFrameRefresh(request, TAKEOVER_FRAME_AFTER_INPUT_MS);
    return false;
  }
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

function installTakeoverPointerHandlers(request, stream) {
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
        updateTakeoverPanel(request, null, "Pinch zooming local browser frame. Input is not sent to the controlled browser.");
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
      updateTakeoverPanel(request, null, "Pinch zooming local browser frame. Input is not sent to the controlled browser.");
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
      sendTakeoverInput(request, { event_type: "tap", frame_id: end.frame_id || start.frame_id, x: end.x, y: end.y });
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
      updateTakeoverFrameConnection("connected", "connected - websocket");
    };
    socket.onmessage = (event) => {
      if (activeTakeoverFrameRequest !== request.request_id) return;
      const payload = JSON.parse(event.data);
      if (payload.event === "takeover_frame" && payload.request_id === request.request_id) {
        renderTakeoverFrame(request, stream, payload.data || {}, "Live browser frame ready over WebSocket. Input is bound to the frame currently visible here.");
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
        markTakeoverFrameReconnect(request, stream, "Live frame WebSocket disconnected.");
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
  updateTakeoverFrameConnection("paused", "paused - page hidden");
  updateTakeoverFrameFreshness(stream);
  if (request) {
    updateTakeoverPanel(request, null, "Frame polling paused while this Control Client is hidden. Last frame is retained and stale input remains blocked.");
  }
}

function resumeTakeoverFramePollingFromVisibility() {
  if (document.hidden) return;
  const request = activeTakeoverRequest();
  const stream = document.querySelector("#browser-stream");
  takeoverFrameVisibilityPaused = false;
  if (!request || !stream || request.status !== "user_control") return;
  updateTakeoverFrameConnection("connecting", "resuming");
  updateTakeoverPanel(request, null, "Control Client visible again; refreshing current browser frame.");
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
    pauseTakeoverFramePollingForVisibility();
    return;
  }
  resumeTakeoverFramePollingFromVisibility();
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
  if (stream) {
    delete stream.dataset.frameId;
    delete stream.dataset.frameCapturedAt;
    stream.classList.remove("frame-reconnecting");
    delete stream.dataset.frameProfile;
    delete stream.dataset.frameContentType;
  }
  resetTakeoverFrameView();
  updateTakeoverFrameConnection("", "waiting for browser handoff");
  updateTakeoverFrameFreshness(stream);
}

function markTakeoverFrameReconnect(request, stream, message) {
  if (!stream) return;
  takeoverFrameMisses += 1;
  const hasLastFrame = Boolean(stream.querySelector("#takeover-frame") && stream.dataset.frameId);
  const retryLabel = `reconnecting - retry ${takeoverFrameMisses}`;
  if (hasLastFrame) {
    stream.classList.add("frame-reconnecting");
    updateTakeoverFrameConnection("reconnecting", `${retryLabel}, keeping last frame`);
    updateTakeoverPanel(request, null, `${message} Keeping the last frame visible; stale frames remain blocked for input.`);
    updateTakeoverFrameFreshness(stream);
    return;
  }
  stream.textContent = "Waiting for the controlled browser frame...";
  updateTakeoverFrameConnection("connecting", retryLabel);
  updateTakeoverPanel(request, null, "Waiting for the controlled browser frame...");
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
      markTakeoverFrameReconnect(request, stream, "Browser context is not connected in this process.");
    }
  } catch {
    if (activeTakeoverFrameRequest === request.request_id) {
      markTakeoverFrameReconnect(request, stream, "Browser frame fetch failed.");
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
    stream.textContent = "Takeover is not active. Agent control can resume after release.";
    updateTakeoverPanel(request, null, "Takeover is not active. Agent control can resume after release.");
    return;
  }
  if (activeTakeoverFrameRequest && activeTakeoverFrameRequest !== request.request_id) {
    stopTakeoverFramePolling();
  }
  if (activeTakeoverFrameRequest === request.request_id && takeoverFrameTimer) return;
  activeTakeoverFrameRequest = request.request_id;
  takeoverFrameMisses = 0;
  resetTakeoverFrameView();
  stream.textContent = "Loading control-only browser frame...";
  stream.classList.remove("frame-reconnecting");
  if (document.hidden) {
    takeoverFrameVisibilityPaused = true;
    updateTakeoverFrameConnection("paused", "paused - page hidden");
    updateTakeoverPanel(request, null, "Frame polling paused while this Control Client is hidden. Last frame is retained and stale input remains blocked.");
    installTakeoverPointerHandlers(request, stream);
    return;
  }
  takeoverFrameVisibilityPaused = false;
  updateTakeoverFrameConnection("connecting", "connecting");
  updateTakeoverPanel(request, null, "Loading control-only browser frame...");
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
    release.onclick = () => postAction(request, "release");
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
  controls.querySelector("[data-action='release']").onclick = () => postAction(request, "release");
  item.append(controls);
}

function renderApprovalControls(request, item) {
  const details = request.structured_details || {};
  const detailList = document.createElement("dl");
  detailList.className = "metadata approval-details";
  [
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
  ].forEach(([label, value]) => {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = displayValue(value, "not visible");
    detailList.append(dt, dd);
  });
  item.append(detailList);
  const isActionable = request.status === "pending";
  let confirm = null;
  if (request.request_type === "payment_approval") {
    const confirmLabel = document.createElement("label");
    confirmLabel.className = "check-row approval-confirm";
    confirmLabel.innerHTML = '<input type="checkbox" data-payment-confirm> I reviewed merchant, amount, recipient, origin, final button text, and after-approval result.';
    confirm = confirmLabel.querySelector("[data-payment-confirm]");
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
      setStatus(t("paymentReviewRequired"), t("paymentReviewRequiredDetail"));
      return;
    }
    postAction(request, "approve", confirm ? paymentApprovalConfirmationPayload(request) : null);
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
    const runner = status.chat_runner || {};
    let detail = t("runtimeDetail");
    let runtimeState = "";
    let restartCommand = "";
    if (runner.waiting_for_tui_bridge) {
      const legacyRelay = runner.legacy_tui_relay || {};
      detail = legacyRelay.active ? t("runtimeLegacyRelayActive") : t("runtimeWaitingForConsoleRestart");
      runtimeState = legacyRelay.active ? "legacy_tui_relay" : "waiting_for_tui_bridge";
      restartCommand = runner.restart_command || "";
    } else if (runner.tui_bridge_active) {
      detail = t("runtimeBridgeActive");
      runtimeState = "tui_bridge_active";
    } else if (runner.thread_id) {
      detail = t("runtimeBackgroundRunner");
      runtimeState = "background_runner";
    }
    setStatus(`Mode: ${status.mode}`, detail, runtimeState, restartCommand);
  } catch {
    setStatus(t("runtimeOffline"), t("runtimeOfflineDetail"), "offline");
  }
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
    document.querySelector("#requests-list").textContent = t("pairToViewRequests");
  }
}

async function loadBrowserContexts() {
  try {
    const payload = await signedFetch("/api/browser/contexts", { cache: "no-store" }).then((r) => {
      if (!r.ok) throw new Error("unauthorized");
      return r.json();
    });
    cachedBrowserContexts = payload.contexts || [];
    syncTakeoverPanel(cachedRequests);
  } catch {
    cachedBrowserContexts = [];
  }
}

function applyRequestEvent(payload) {
  cachedRequests = payload.requests || [];
  renderRequestList(cachedRequests);
}

function applyChatEvent(payload) {
  cachedChatMessages = payload.messages || [];
  cachedChatRecords = payload.records || [];
  renderChatTimeline(cachedChatMessages, cachedChatRecords, payload.terminal || null);
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
}

async function startRequestStream() {
  if (requestStreamActive || !window.ReadableStream) return;
  requestStreamActive = true;
  if (requestStreamRestart) clearTimeout(requestStreamRestart);
  try {
    const response = await signedFetch("/api/events?stream=1&snapshots=30&interval=2", { cache: "no-store" });
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
      ? new WebSocket(websocketUrl(`${path}?snapshots=30&interval=2`), [protocol])
      : new WebSocket(websocketUrl(`${path}?snapshots=30&interval=2`));
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

async function startChatStream() {
  if (chatStreamActive || !window.ReadableStream) return;
  chatStreamActive = true;
  if (chatStreamRestart) clearTimeout(chatStreamRestart);
  try {
    const response = await signedFetch("/api/chat/events?stream=1&snapshots=120&interval=1", { cache: "no-store" });
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
      ? new WebSocket(websocketUrl(`${path}?snapshots=120&interval=1`), [protocol])
      : new WebSocket(websocketUrl(`${path}?snapshots=120&interval=1`));
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

loadRuntimeStatus();
refreshPairingState();
loadRequests();
loadBrowserContexts();
loadChatMessages();
loadDevicesAndSessions();
startRequestWebSocket();
startChatWebSocket();
document.addEventListener("visibilitychange", handleTakeoverVisibilityChange);
setInterval(loadRuntimeStatus, 10000);
setInterval(refreshPairingState, 30000);
setInterval(loadRequests, 15000);
setInterval(loadBrowserContexts, 5000);
setInterval(loadChatMessages, 5000);
setInterval(loadDevicesAndSessions, 15000);
