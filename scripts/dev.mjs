#!/usr/bin/env node
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { spawn } from "child_process";
import { setTimeout as delay } from "timers/promises";
import dotenv from "dotenv";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, "..");
const envPath = path.join(rootDir, ".env");
const envExamplePath = path.join(rootDir, ".env.example");

const dockerCmd = "docker";
const npmCmd = process.platform === "win32" ? "npm.cmd" : "npm";

let frontendProc;
let shuttingDown = false;

function log(message) {
  console.log(`[dev] ${message}`);
}

function ensureEnvFile() {
  if (fs.existsSync(envPath)) {
    return;
  }

  if (!fs.existsSync(envExamplePath)) {
    throw new Error("Missing .env and .env.example; cannot continue.");
  }

  fs.copyFileSync(envExamplePath, envPath);
  log("Created .env from .env.example");
}

function run(cmd, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, { stdio: "inherit", ...options });
    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`${cmd} ${args.join(" ")} exited with code ${code}`));
      }
    });
  });
}

async function waitForHealth(url, timeoutMs = 120000) {
  const start = Date.now();
  const formatter = Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  while (Date.now() - start < timeoutMs) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 5000);
      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(timer);

      if (res.ok) {
        const body = await res.json();
        if (body?.db === true) {
          log(`API is healthy (${formatter.format(new Date())})`);
          return;
        }
      }

      log("API not ready yet, waiting...");
    } catch (err) {
      log(`Waiting for API... (${err.message ?? err})`);
    }

    await delay(1500);
  }

  throw new Error(`API health check did not pass within ${timeoutMs / 1000}s`);
}

async function showApiLogs() {
  try {
    await run(dockerCmd, ["compose", "logs", "--tail", "200", "api"]);
  } catch (err) {
    console.error("Failed to fetch api logs:", err.message ?? err);
  }
}

async function startFrontend() {
  const frontendPort = process.env.FRONTEND_PORT || "3002";
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const env = {
    ...process.env,
    PORT: frontendPort,
    NEXT_PUBLIC_API_URL: apiUrl,
  };

  log(`Starting frontend on http://localhost:${frontendPort} (API ${apiUrl})...`);
  frontendProc = spawn(
    npmCmd,
    ["run", "dev", "--", "--hostname", "0.0.0.0", "--port", frontendPort],
    {
      cwd: path.join(rootDir, "frontend"),
      env,
      stdio: "inherit",
    },
  );

  return new Promise((resolve, reject) => {
    frontendProc.on("error", reject);
    frontendProc.on("exit", (code) => {
      frontendProc = undefined;
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Frontend exited with code ${code}`));
      }
    });
  });
}

async function shutdown(exitCode = 0) {
  if (shuttingDown) return;
  shuttingDown = true;

  if (frontendProc && !frontendProc.killed) {
    frontendProc.kill("SIGINT");
  }

  try {
    await run(dockerCmd, ["compose", "down"]);
  } catch (err) {
    console.error("Failed to stop docker compose:", err.message ?? err);
  }

  process.exit(exitCode);
}

function wireSignals() {
  ["SIGINT", "SIGTERM"].forEach((sig) => {
    process.on(sig, () => {
      log(`Received ${sig}, shutting down...`);
      shutdown(0);
    });
  });
}

async function main() {
  ensureEnvFile();
  dotenv.config({ path: envPath });
  wireSignals();

  log("Starting containers: db, redis, api...");
  await run(dockerCmd, ["compose", "up", "-d", "db", "redis", "api"]);

  log("Waiting for API health...");
  await waitForHealth("http://localhost:8000/health", 120000);

  log("Launching frontend (Next.js)...");
  try {
    await startFrontend();
    // If the frontend exits naturally, shut everything down.
    await shutdown(0);
  } catch (err) {
    console.error(err.message ?? err);
    console.error("Tip: run `npm run dev:logs` to inspect backend logs.");
    await shutdown(1);
  }
}

main().catch(async (err) => {
  console.error(err.message ?? err);
  await showApiLogs();
  await shutdown(1);
});
