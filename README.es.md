# OmniDoer

![Póster cinematográfico de OmniDoer en español](./docs/assets/localized/omnidoer-readme-es.jpg)

[English](./README.md) | [中文](./README.zh-CN.md) | [Français](./README.fr.md) | [Deutsch](./README.de.md) | [日本語](./README.ja.md) | [한국어](./README.ko.md)

OmniDoer extiende Codex CLI mediante MCP y un sidecar local/cloud-direct. No es un nuevo cliente de OpenAI API. Codex sigue siendo la única entrada de inferencia del modelo, y OmniDoer conserva el modo de autenticación y facturación de Codex.

El agente puede solicitar una acción, pero no puede leer secretos. Las contraseñas, códigos de verificación, semillas TOTP, cookies, claves privadas y credenciales de pago permanecen dentro del Secret Broker, Vault, Browser Controller y Control Client.

Control Client reúne tareas, entrada de credenciales, desafíos de usuario, Human Takeover, registro de cuentas, aprobación de pagos y auditoría. Para CAPTCHA, MFA, Passkey, WebAuthn, 3DS y páginas anti-bot fuertes, OmniDoer no evita ni resuelve el desafío; lo entrega al usuario.

Cloud Direct Mode permite que Android, Windows 11 y clientes PWA se conecten directamente al servidor cloud propio del usuario con HTTPS/WSS, pairing, identidad de dispositivo, sesiones, protección CSRF/Origin, rate limit y envío E2EE de secretos.
