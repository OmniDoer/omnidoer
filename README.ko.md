# OmniDoer

![OmniDoer 한국어판 시네마틱 포스터](./docs/assets/localized/omnidoer-readme-ko.jpg)

[English](./README.md) | [中文](./README.zh-CN.md) | [Español](./README.es.md) | [Français](./README.fr.md) | [Deutsch](./README.de.md) | [日本語](./README.ja.md)

OmniDoer는 Codex CLI를 MCP와 sidecar 방식으로 확장하는 local-first, cloud-direct 실행 계층입니다. 새로운 OpenAI API 클라이언트가 아닙니다. 모델 추론의 유일한 진입점은 Codex CLI이며, OmniDoer는 Codex의 인증, 과금, 모델 provider 로직을 변경하지 않습니다.

Agent는 secret 사용을 요청할 수 있지만 secret 자체를 읽을 수 없습니다. 비밀번호, 인증 코드, TOTP seed, Cookie, 개인키, 결제 정보는 Secret Broker, Vault, Browser Controller, Control Client의 보안 경계 안에 남습니다.

Control Client는 작업 입력, 자격 증명 입력, challenge 처리, Human Takeover, 계정 등록 위임, 결제 승인, 감사 로그 보기를 통합합니다. CAPTCHA, MFA, Passkey, WebAuthn, 3DS, 강한 anti-bot 페이지에서는 OmniDoer가 우회하거나 자동 풀이하지 않고 사용자가 직접 완료합니다.

Cloud Direct Mode에서는 Android, Windows 11, PWA 클라이언트가 사용자의 클라우드 서버에 직접 연결합니다. HTTPS/WSS, pairing, device identity, session, CSRF/Origin protection, rate limit, E2EE secret submission이 필요합니다.
