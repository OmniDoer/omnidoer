# OmniDoer

![OmniDoer frontera de seguridad white-hat](./docs/assets/omnidoer-whitehat-hero.jpg)

[English](./README.md) | [中文](./README.zh-CN.md) | [Français](./README.fr.md) | [Deutsch](./README.de.md) | [日本語](./README.ja.md) | [한국어](./README.ko.md)

**El control seguro es lo que permite más libertad.**

Un investigador white-hat encontró la frontera ausente de los agentes de código
en la nube: en un servidor real, contraseñas, claves SSH, tokens API, claves
privadas y secretos de wallet pueden quedar a una llamada de herramienta. Pedirle
al modelo que no los lea es una petición de conducta, no una frontera de
aislamiento.

OmniDoer convierte ese hallazgo en arquitectura. Codex conserva el cerebro de
razonamiento, login, modelo y cuota; OmniDoer aporta las manos seguras:
navegador controlado, Secret Broker, Vault cifrado, aprobaciones, Challenge
Relay, auditoría y Control Client para mantener las acciones sensibles fuera del
estado visible para el modelo.

Página: [https://omnidoer.github.io/omnidoer/](https://omnidoer.github.io/omnidoer/)

## Instalación rápida

Bootstrap npm recomendado:

```sh
npm install -g @omnidoer/omnidoer
omnidoer
omnidoer pair
```

El paquete npm instala un lanzador Node ligero. En el primer uso clona OmniDoer
en `~/.omnidoer/npm-install/omnidoer` por defecto, instala el runtime sidecar de
Python y conserva tu login, modelo, cuota y facturacion de Codex. Define
`OMNIDOER_INSTALL_DIR` para usar un checkout existente.

Instalación directa desde codigo fuente:

```sh
curl -fsSL https://raw.githubusercontent.com/OmniDoer/omnidoer/main/omnidoer/scripts/install-cloud-direct.sh | sh
```

Servidor Cloud Direct detrás de tu propio proxy HTTPS:

```sh
curl -fsSL https://raw.githubusercontent.com/OmniDoer/omnidoer/main/omnidoer/scripts/install-cloud-direct.sh | \
  OMNIDOER_CLOUD_DIRECT=1 OMNIDOER_PUBLIC_URL=https://agent.example.com sh
```

Después de instalar:

```sh
omnidoer
omnidoer pair
omnidoer control submit-task "Abre la demo local y descarga mi factura"
```

Si usaste el instalador shell directo y `omnidoer` no esta en `PATH`, usa
`~/omnidoer/.venv/bin/omnidoer` para los mismos comandos.

El instalador crea `~/omnidoer/.venv`, inicializa OmniDoer, instala el browser
worker, prueba el servidor MCP y registra `omnidoer mcp serve` si `codex` CLI
está disponible.

Al iniciar desde una terminal interactiva, `omnidoer` comprueba si `origin/main`
tiene una actualización fast-forward y pregunta antes de ejecutar
`omnidoer upgrade`. Los lanzamientos sin TTY omiten el aviso, y
`OMNIDOER_UPDATE_CHECK=0` lo desactiva.

### Cambio de cuenta en la consola nativa

En la consola nativa, `/users` abre el selector de cuentas locales ya iniciadas.
La lista marca la cuenta actual y permite moverse con las flechas y confirmar
con Enter. OmniDoer guarda cada cuenta en su propio espacio de autenticación
local, recarga el app-server en ejecución y conserva el contexto de la
conversación actual. Sirve para cambiar a una cuenta ChatGPT/Codex con una
capacidad concreta o para continuar con otra cuota cuando una cuenta se agota.

El selector y los logs nunca imprimen tokens, API keys ni claves privadas. El
índice de cuentas guarda solo metadatos de visualización; los secretos siguen
en el credential store local configurado.

OmniDoer extiende Codex CLI mediante MCP y un sidecar local/cloud-direct. No es un nuevo cliente de OpenAI API. Codex razona; OmniDoer actúa con un navegador real, Secret Broker, Vault, Control Client, Challenge Relay, Human Takeover, Cloud Direct, Approval Gate y auditoría.

Si una persona puede hacerlo en la web con autorización, OmniDoer está diseñado para ayudar a ejecutarlo de forma segura: registro, inicio de sesión, navegación, formularios, descargas, facturas, revisión de compras, aprobación de pagos y traspaso al usuario cuando el sitio exige intervención humana.

El agente puede solicitar una acción, pero no puede leer secretos. Las contraseñas, códigos de verificación, semillas TOTP, cookies, claves privadas y credenciales de pago permanecen dentro del Secret Broker, Vault, Browser Controller y Control Client.

Control Client reúne tareas, entrada de credenciales, desafíos de usuario, Human Takeover, registro de cuentas, aprobación de pagos y auditoría. Para CAPTCHA, MFA, Passkey, WebAuthn, 3DS, confirmación de registro y páginas anti-bot fuertes, OmniDoer no evita ni resuelve el desafío; lo entrega al usuario.

Cloud Direct Mode permite que Android, Windows 11 y clientes PWA se conecten directamente al servidor cloud propio del usuario con HTTPS/WSS, pairing, identidad de dispositivo, sesiones, protección CSRF/Origin, rate limit y envío E2EE de secretos.
