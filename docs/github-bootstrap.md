# GitHub Bootstrap

Bootstrap steps for this repository:

1. Read the local Flask env credential named `omnidoer` without printing the PAT.
2. Call `GET /user` and confirm the authenticated account is `omnidoer`.
3. Call `POST /repos/openai/codex/forks` with:

```json
{
  "name": "omnidoer",
  "default_branch_only": false
}
```

4. Poll `GET /repos/omnidoer/omnidoer` until available.
5. Clone `https://github.com/omnidoer/omnidoer.git`.
6. Create `omnidoer-mvp`.
7. Add `upstream = https://github.com/openai/codex.git`.

Never print the PAT, put it into a remote URL, enable shell tracing, or write it
to repository files.
