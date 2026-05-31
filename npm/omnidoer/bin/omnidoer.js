#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawn, spawnSync } = require("child_process");

const REPO_URL = process.env.OMNIDOER_REPO_URL || "https://github.com/OmniDoer/omnidoer.git";
const BRANCH = process.env.OMNIDOER_BRANCH || "main";
const INSTALL_DIR = path.resolve(
  process.env.OMNIDOER_INSTALL_DIR || path.join(os.homedir(), ".omnidoer", "npm-install", "omnidoer")
);

function hasOmniDoerCheckout() {
  return fs.existsSync(path.join(INSTALL_DIR, "omnidoer", "omni_cli", "main.py"));
}

function runChecked(command, args, options = {}) {
  const result = spawnSync(command, args, {
    stdio: "inherit",
    env: process.env,
    ...options
  });
  if (result.error) {
    console.error(`omnidoer npm bootstrap failed to run ${command}: ${result.error.message}`);
    process.exit(127);
  }
  if (result.status !== 0) {
    process.exit(result.status || 1);
  }
}

function pythonCommand() {
  if (process.env.OMNIDOER_PYTHON) return process.env.OMNIDOER_PYTHON;
  for (const candidate of ["python3", "python"]) {
    const result = spawnSync(candidate, ["--version"], { stdio: "ignore" });
    if (!result.error && result.status === 0) return candidate;
  }
  console.error("omnidoer requires Python 3.11+ on PATH, or set OMNIDOER_PYTHON.");
  process.exit(127);
}

function ensureCheckout() {
  if (hasOmniDoerCheckout()) return;
  fs.mkdirSync(path.dirname(INSTALL_DIR), { recursive: true });
  runChecked("git", ["clone", "--depth=1", "--branch", BRANCH, REPO_URL, INSTALL_DIR]);
  runChecked(pythonCommand(), ["-m", "pip", "install", "-e", INSTALL_DIR]);
}

ensureCheckout();

const child = spawn(
  pythonCommand(),
  ["-m", "omnidoer.omni_cli.main", ...process.argv.slice(2)],
  {
    cwd: INSTALL_DIR,
    stdio: "inherit",
    env: {
      ...process.env,
      OMNIDOER_INSTALL_DIR: INSTALL_DIR
    }
  }
);

child.on("error", (error) => {
  console.error(`omnidoer failed to start: ${error.message}`);
  process.exit(127);
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code || 0);
});
