# OmniDoer

![OmniDoer White-Hat-Sicherheitsgrenze](./docs/assets/omnidoer-whitehat-hero.jpg)

[English](./README.md) | [中文](./README.zh-CN.md) | [Español](./README.es.md) | [Français](./README.fr.md) | [日本語](./README.ja.md) | [한국어](./README.ko.md)

**Sichere Kontrolle macht mehr Freiheit möglich.**

Ein White-Hat-Forscher fand die fehlende Grenze bei Cloud-Coding-Agenten: Auf
einem echten Server können Passwörter, SSH-Schlüssel, API-Tokens, private
Schlüssel und Wallet-Secrets nur einen Tool-Aufruf entfernt sein. Das Modell zu
bitten, diese Daten nicht zu lesen, ist eine Verhaltensbitte, keine Isolation.

OmniDoer macht daraus Architektur. Codex bleibt das Gehirn für Reasoning, Login,
Modellwahl und Quota; OmniDoer liefert die sicheren Hände: kontrollierter
Browser, Secret Broker, verschlüsselter Vault, Freigaben, Challenge Relay, Audit
und Control Client halten sensible Aktionen außerhalb des modell-sichtbaren
Zustands.

Live-Seite: [https://omnidoer.github.io/omnidoer/](https://omnidoer.github.io/omnidoer/)

## Schnellinstallation

Empfohlener npm-Bootstrap:

```sh
npm install -g @omnidoer/omnidoer
omnidoer
omnidoer pair
```

Das npm-Paket installiert einen kleinen Node-Launcher. Beim ersten Start klont
er OmniDoer standardmaessig nach `~/.omnidoer/npm-install/omnidoer`, installiert
die Python-Sidecar-Runtime und erhaelt bestehenden Codex-Login, Modell, Quota
und Billing-Pfad. Setze `OMNIDOER_INSTALL_DIR`, um einen vorhandenen Checkout
zu verwenden.

Direkte Source-Installation:

```sh
curl -fsSL https://raw.githubusercontent.com/OmniDoer/omnidoer/main/omnidoer/scripts/install-cloud-direct.sh | sh
```

Cloud-Direct-Server hinter dem eigenen HTTPS-Reverse-Proxy:

```sh
curl -fsSL https://raw.githubusercontent.com/OmniDoer/omnidoer/main/omnidoer/scripts/install-cloud-direct.sh | \
  OMNIDOER_CLOUD_DIRECT=1 OMNIDOER_PUBLIC_URL=https://agent.example.com sh
```

Nach der Installation:

```sh
omnidoer
omnidoer pair
omnidoer control submit-task "Öffne die lokale Demo und lade meine Rechnung herunter"
```

Wenn du den direkten Shell-Installer genutzt hast und `omnidoer` nicht im
`PATH` liegt, verwende `~/omnidoer/.venv/bin/omnidoer` fuer dieselben Befehle.

Der Installer erstellt `~/omnidoer/.venv`, initialisiert OmniDoer, installiert
den Browser-Worker, testet den MCP-Server und registriert `omnidoer mcp serve`,
wenn `codex` CLI verfügbar ist.

Beim Start aus einem interaktiven Terminal prüft `omnidoer`, ob `origin/main`
ein Fast-Forward-Update enthält, und fragt vor `omnidoer upgrade` nach. Starts
ohne TTY überspringen die Abfrage; `OMNIDOER_UPDATE_CHECK=0` deaktiviert sie.

### Kontowechsel in der nativen Konsole

In der nativen Konsole öffnet `/users` den Umschalter für lokal bereits
angemeldete Konten. Die Liste markiert das aktuelle Konto; mit den Pfeiltasten
wählst du aus und mit Enter wechselst du. OmniDoer speichert jedes Konto in
einem eigenen lokalen Auth-Slot, lädt den laufenden app-server neu und behält
den Kontext der aktuellen Unterhaltung. Das hilft, wenn eine Aufgabe ein
ChatGPT/Codex-Konto mit besonderer Fähigkeit braucht oder wenn das Kontingent
eines Kontos erschöpft ist.

Der Umschalter und die Logs geben niemals Tokens, API keys oder private
Schlüssel aus. Der Kontoindex speichert nur Anzeigemetadaten; Secrets bleiben
im konfigurierten lokalen credential store.

OmniDoer erweitert Codex CLI über MCP und einen lokalen beziehungsweise Cloud-Direct-Sidecar. Es ist kein neuer OpenAI API Client. Codex denkt; OmniDoer handelt mit echtem Browser, Secret Broker, Vault, Control Client, Challenge Relay, Human Takeover, Cloud Direct, Approval Gate und Audit.

Wenn ein Mensch eine Aufgabe im Web autorisiert erledigen kann, soll OmniDoer sie sicher ausführen helfen: Registrierung, Anmeldung, Navigation, Formulare, Downloads, Rechnungen, Kaufprüfung, Zahlungsfreigabe und Übergabe an den Nutzer, wenn eine Website menschliches Eingreifen verlangt.

Der Agent darf die Nutzung eines Secrets anfordern, aber er darf das Secret nicht lesen. Passwörter, Verifizierungscodes, TOTP-Seeds, Cookies, private Schlüssel und Zahlungsdaten bleiben im Secret Broker, Vault, Browser Controller und Control Client.

Control Client bündelt Aufgaben, Zugangsdaten, Challenges, Human Takeover, Konto-Registrierung, Zahlungsfreigaben und Auditansicht. Bei CAPTCHA, MFA, Passkey, WebAuthn, 3DS, Registrierungsbestätigung und starken Anti-Bot-Seiten umgeht oder löst OmniDoer nichts automatisch; die Aufgabe geht an den Benutzer.

Cloud Direct Mode verbindet Android-, Windows-11- und PWA-Clients direkt mit dem eigenen Cloud-Server des Benutzers. Dafür sind HTTPS/WSS, Pairing, Geräteidentität, Sessions, CSRF/Origin-Schutz, Rate Limits und E2EE Secret Submission vorgesehen.
