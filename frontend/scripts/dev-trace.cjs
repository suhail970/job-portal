const fs = require("node:fs");
const path = require("node:path");
const cp = require("node:child_process");

const logPath = path.join(process.cwd(), ".next-dev", "dev-exit-trace.log");
function writeTrace(msg) {
  try {
    fs.mkdirSync(path.dirname(logPath), { recursive: true });
    fs.appendFileSync(logPath, `[${new Date().toISOString()}] pid=${process.pid} ppid=${process.ppid} ${msg}\n`);
  } catch {}
}

const origFork = cp.fork;
cp.fork = function patchedFork(...args) {
  const child = origFork.apply(this, args);
  const target = String(args[0] || "");
  writeTrace(`forked pid=${child.pid} target=${target}`);
  child.on("exit", (code, signal) => {
    const hex = typeof code === "number" ? " (0x" + (code >>> 0).toString(16) + ")" : "";
    const msg = `child exit pid=${child.pid} code=${code}${hex} signal=${signal} target=${target}`;
    writeTrace(msg);
    if (code !== 0 && code !== 77) {
      console.error(`[SkillBridge Frontend Trace] ${msg}`);
    }
  });
  return child;
};

const origExit = process.exit.bind(process);
process.exit = function patchedExit(code) {
  const stack = new Error(`process.exit(${code})`).stack || "";
  writeTrace(stack.replace(/\r?\n/g, " | "));
  return origExit(code);
};

for (const sig of ["SIGINT", "SIGTERM", "SIGHUP", "SIGBREAK"]) {
  try {
    process.on(sig, () => writeTrace(`signal=${sig}`));
  } catch {}
}
process.on("beforeExit", (code) => writeTrace(`beforeExit code=${code}`));
process.on("uncaughtExceptionMonitor", (err) => writeTrace(`uncaughtException: ${err && (err.stack || err)}`));
