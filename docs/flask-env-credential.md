# Flask Env Credential

This server stores GitHub PAT credentials in the local Flask service's env
credential store. The `omnidoer` credential was used only in process memory for
the GitHub bootstrap.

## Safe Handling Rules

- Read only from localhost-controlled storage.
- Do not print the token.
- Do not echo the token.
- Do not use `set -x`.
- Do not place the token in a git remote URL.
- Do not write the token to source files.
- Use a short-lived process environment or in-memory variable only.
- Remove temporary askpass helpers after authenticated git operations.

If the local credential cannot be read safely, stop and ask the operator to set
`GITHUB_TOKEN` locally. Do not ask anyone to paste a PAT into a model-visible
conversation.

## OmniDoer Vault Migration Path

Preferred flow for future GitHub operations:

1. Create or unlock a local OmniDoer Vault.
2. Create a Control Client credential request scoped to GitHub:

   ```sh
   omnidoer cred request \
     --origin https://github.com \
     --top-level-url https://github.com/settings/tokens \
     --summary "Migrate GitHub PAT into OmniDoer Vault"
   ```

3. Open the paired Control Client and submit the GitHub username plus PAT as the
   password/token field. The token is encrypted in the browser before it reaches
   the broker.
4. Save the fulfilled request into the Vault:

   ```sh
   omnidoer cred save-request <request_id> \
     --vault ~/.omnidoer/vault.json \
     --passphrase-env OMNIDOER_VAULT_PASSPHRASE
   ```

5. Use the Vault-backed Git bridge instead of Flask Env credentials:

   ```sh
   omnidoer git run \
     --origin https://github.com \
     --vault ~/.omnidoer/vault.json \
     --passphrase-env OMNIDOER_VAULT_PASSPHRASE \
     -- push origin main
   ```

`omnidoer git run` only invokes `git ...`, creates a temporary askpass helper,
and validates that Git's credential prompt matches the configured origin before
supplying the Vault credential to Git. The PAT must not be printed, embedded in
the remote URL, or returned to the model.
