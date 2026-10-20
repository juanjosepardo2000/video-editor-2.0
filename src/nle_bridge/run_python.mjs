import { spawnSync } from "node:child_process";

const candidates = process.platform === "win32"
  ? [["py", ["-3"]], ["python", []], ["python3", []]]
  : [["python3", []], ["python", []]];

const forwarded = process.argv.slice(2);
if (forwarded[0] === "--") forwarded.shift();

for (const [command, prefix] of candidates) {
  const probe = spawnSync(command, [...prefix, "--version"], { encoding: "utf8", shell: false });
  if (probe.error?.code === "ENOENT" || probe.status !== 0) continue;

  const result = spawnSync(command, [...prefix, ...forwarded], { stdio: "inherit", shell: false });
  if (result.error) {
    console.error(`No se pudo ejecutar ${command}: ${result.error.message}`);
    process.exit(1);
  }
  process.exit(result.status ?? 1);
}

console.error("No se encontró Python 3. Instala python3 (macOS/Linux), python o py -3 (Windows).");
process.exit(1);
