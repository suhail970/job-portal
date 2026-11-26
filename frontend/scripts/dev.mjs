import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";

const rootDir = process.cwd();
const devDistDir = path.join(rootDir, ".next-dev");
const nextBin = path.join(rootDir, "node_modules", "next", "dist", "bin", "next");
const traceHook = path.join(rootDir, "scripts", "dev-trace.cjs").replace(/\\/g, "/");

// Clear stale lock/trace cache from previous runs while keeping fast startup
for (const rel of ["trace", "cache"]) {
  const target = path.join(devDistDir, rel);
  try {
    if (fs.existsSync(target)) {
      fs.rmSync(target, { recursive: true, force: true });
    }
  } catch {
    // Ignore locked transient files
  }
}

const existingNodeOpts = process.env.NODE_OPTIONS ? `${process.env.NODE_OPTIONS} ` : "";
const args = [nextBin, "dev", ...process.argv.slice(2)];

let stopping = false;
let currentChild = null;
const restartTimestamps = [];

function startNextDev() {
  const startedAt = Date.now();
  const child = spawn(process.execPath, args, {
    cwd: rootDir,
    stdio: "inherit",
    env: {
      ...process.env,
      NEXT_TELEMETRY_DISABLED: "1",
      NODE_OPTIONS: `${existingNodeOpts}--require ${traceHook}`,
    },
  });
  currentChild = child;

  child.on("exit", (code, signal) => {
    currentChild = null;
    if (stopping) {
      process.exit(code ?? 0);
      return;
    }

    const uptimeMs = Date.now() - startedAt;
    console.error(`[SkillBridge Frontend] Next dev exited -> code=${code}, signal=${signal}, uptime=${uptimeMs}ms`);

    // Auto-recover if the server was running cleanly (>= 2s) and exited without user Ctrl+C/SIGINT
    const now = Date.now();
    while (restartTimestamps.length > 0 && now - restartTimestamps[0] > 60000) {
      restartTimestamps.shift();
    }
    if (uptimeMs >= 2000 && restartTimestamps.length < 5) {
      restartTimestamps.push(now);
      console.error(`[SkillBridge Frontend] Restarting dev server automatically (${restartTimestamps.length}/5 in 60s)...`);
      setTimeout(startNextDev, 500);
      return;
    }

    console.error("[SkillBridge Frontend] Check .next-dev/dev-exit-trace.log for child exit details.");
    process.exit(code ?? 1);
  });
}

const forwardSignal = (sig) => {
  stopping = true;
  console.error(`[SkillBridge Frontend] Stopping dev server (${sig})...`);
  if (currentChild && !currentChild.killed) {
    currentChild.kill(sig);
  } else {
    process.exit(0);
  }
};
process.on("SIGINT", () => forwardSignal("SIGINT"));
process.on("SIGTERM", () => forwardSignal("SIGTERM"));

startNextDev();
