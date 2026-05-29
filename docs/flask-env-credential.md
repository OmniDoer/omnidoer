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
