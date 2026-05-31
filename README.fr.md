# OmniDoer

![OmniDoer limite de sécurité white-hat](./docs/assets/omnidoer-whitehat-hero.jpg)

[English](./README.md) | [中文](./README.zh-CN.md) | [Español](./README.es.md) | [Deutsch](./README.de.md) | [日本語](./README.ja.md) | [한국어](./README.ko.md)

**Le contrôle sécurisé rend la liberté possible.**

Un chercheur white-hat a trouvé la limite manquante des agents de code cloud :
sur un vrai serveur, mots de passe, clés SSH, tokens API, clés privées et
secrets de wallet peuvent se trouver à un appel d'outil. Demander au modèle de
ne pas les lire reste une consigne de comportement, pas une isolation.

OmniDoer transforme ce constat en architecture. Codex reste le cerveau de
raisonnement avec son login, son choix de modèle et son quota; OmniDoer apporte
les mains sûres : navigateur contrôlé, Secret Broker, Vault chiffré,
approbations, Challenge Relay, audit et Control Client pour garder les actions
sensibles hors de l'état visible par le modèle.

Page : [https://omnidoer.github.io/](https://omnidoer.github.io/)

## Installation rapide

Installation locale :

```sh
curl -fsSL https://raw.githubusercontent.com/OmniDoer/omnidoer/main/omnidoer/scripts/install-cloud-direct.sh | sh
```

Serveur Cloud Direct derrière votre proxy HTTPS :

```sh
curl -fsSL https://raw.githubusercontent.com/OmniDoer/omnidoer/main/omnidoer/scripts/install-cloud-direct.sh | \
  OMNIDOER_CLOUD_DIRECT=1 OMNIDOER_PUBLIC_URL=https://agent.example.com sh
```

Après installation :

```sh
~/omnidoer/.venv/bin/omnidoer
~/omnidoer/.venv/bin/omnidoer control pair --print-qr
~/omnidoer/.venv/bin/omnidoer control submit-task "Ouvre la démo locale et télécharge ma facture"
```

L’installateur crée `~/omnidoer/.venv`, initialise OmniDoer, installe le browser
worker, teste le serveur MCP et enregistre `omnidoer mcp serve` si `codex` CLI
est disponible.

Au lancement depuis un terminal interactif, `omnidoer` vérifie si `origin/main`
contient une mise à jour fast-forward et demande confirmation avant d'exécuter
`omnidoer upgrade`. Cette invite n'apparaît pas sans TTY, et
`OMNIDOER_UPDATE_CHECK=0` la désactive.

### Changement de compte dans la console native

Dans la console native, `/users` ouvre le sélecteur des comptes déjà connectés
sur cette machine. La liste indique le compte courant, se parcourt avec les
flèches; appuyez sur Entrée pour confirmer. OmniDoer conserve chaque compte dans
son propre emplacement d'authentification local, recharge l'app-server en cours
d'exécution et garde le contexte de la conversation actuelle. C'est utile pour
passer à un compte ChatGPT/Codex doté d'une capacité précise ou pour continuer
avec un autre quota lorsqu'un compte est épuisé.

Le sélecteur et les logs n'impriment jamais les tokens, API keys ni clés
privées. L'index des comptes ne contient que des métadonnées d'affichage; les
secrets restent dans le credential store local configuré.

OmniDoer étend Codex CLI au moyen d’un serveur MCP et d’un sidecar local/cloud-direct. Ce n’est pas un nouveau client OpenAI API. Codex raisonne ; OmniDoer agit avec un navigateur réel, Secret Broker, Vault, Control Client, Challenge Relay, Human Takeover, Cloud Direct, Approval Gate et audit.

Si un humain peut l’autoriser et l’effectuer sur le web, OmniDoer vise à l’exécuter en sécurité : inscription, connexion, navigation, formulaires, téléchargements, factures, revue d’achat, approbation de paiement et reprise humaine lorsqu’un site exige l’utilisateur.

L’agent peut demander l’utilisation d’un secret, mais il ne peut jamais le lire. Les mots de passe, codes de vérification, graines TOTP, cookies, clés privées et moyens de paiement restent dans le Secret Broker, le Vault, le Browser Controller et le Control Client.

Control Client regroupe les tâches, la saisie des identifiants, les défis utilisateur, Human Takeover, l’inscription de compte, les approbations de paiement et l’audit. Pour CAPTCHA, MFA, Passkey, WebAuthn, 3DS, confirmation d’inscription et anti-bot fort, OmniDoer ne contourne rien et confie l’action à l’utilisateur.

Cloud Direct Mode permet aux clients Android, Windows 11 et PWA de se connecter directement au serveur cloud de l’utilisateur avec HTTPS/WSS, pairing, identité d’appareil, sessions, protections CSRF/Origin, rate limit et soumission E2EE des secrets.
