# Control Client

The OmniDoer Control Client is the user control plane for tasks, credential
entry, challenge handling, approval, audit review, and Human Takeover Mode.

MVP commands:

```sh
omnidoer control serve --host 127.0.0.1 --port 8787
omnidoer control requests
omnidoer control input-secret <request_id>
omnidoer control challenge <request_id>
omnidoer control approve <request_id>
omnidoer control deny <request_id>
omnidoer control release <request_id>
```

Secrets are sent to the Secret Broker, not to Agent/LLM context. Challenge
answers are handled by the Challenge Relay or target browser, not by the model.
Human Takeover pauses the Agent and gives the user browser control until
release.
