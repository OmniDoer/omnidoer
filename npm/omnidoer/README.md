# @omnidoer/omnidoer

NPM bootstrap for OmniDoer.

```sh
npm install -g @omnidoer/omnidoer
omnidoer --version
```

The npm package is intentionally small. On first run it clones
`https://github.com/OmniDoer/omnidoer.git` into
`~/.omnidoer/npm-install/omnidoer`, installs the Python package, then delegates
to `python -m omnidoer.omni_cli.main`.

## Requirements

- Node.js 18+
- Python 3.11+
- Git

## 中文

这是 OmniDoer 的 npm 启动器。首次运行时会把 GitHub 上的 OmniDoer 仓库克隆到
`~/.omnidoer/npm-install/omnidoer`，安装 Python 包，然后执行真正的
`omnidoer` CLI。
