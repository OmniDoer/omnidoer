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

6. Use the Vault-backed GitHub API client for repository operations that are not
   plain Git pushes:

   ```sh
   omnidoer github api \
     GET /repos/OmniDoer/omnidoer/actions/runs \
     --vault ~/.omnidoer/vault.json \
     --passphrase-env OMNIDOER_VAULT_PASSPHRASE
   ```

`omnidoer git run` only invokes `git ...`, creates a temporary askpass helper,
and validates that Git's credential prompt matches the configured origin before
supplying the Vault credential to Git. The decrypted credential stays in the
parent-side in-memory askpass broker; the Git subprocess receives only a
temporary Unix socket path and one-time grant token, not the Vault path,
passphrase environment variable name, passphrase value, or PAT. The PAT must
not be printed, embedded in the remote URL, or returned to the model.

`omnidoer github api` sends the Vault token only as an Authorization header to
`https://api.github.com` by default. It rejects non-HTTPS and non-GitHub API
origins unless an explicit insecure development flag is used for local tests.
It does not follow HTTP redirects, so the Authorization header is not carried to
a different origin. Response text is redacted against the exact token and known
secret patterns before it is printed.
