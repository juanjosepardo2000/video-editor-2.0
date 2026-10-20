import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../../..");
const argument = (name) => process.argv.find((item) => item.startsWith(`--${name}=`))?.slice(name.length + 3);
const seconds = Number(argument("video-seconds") ?? 60);
if (!Number.isFinite(seconds) || seconds <= 0 || seconds > 60) throw new Error("--video-seconds debe estar entre 0 y 60.");
const frames = Math.ceil(seconds * 30);
const reportPath = path.resolve(root, argument("report") ?? "pipeline/perf_report.json");
const outputPath = path.resolve(root, argument("output") ?? "out/perf/benchmark.mov");
const keep = process.argv.includes("--keep-output");
const cli = path.join(root, "node_modules/@remotion/cli/remotion-cli.js");
fs.mkdirSync(path.dirname(outputPath), {recursive: true});

const start = process.hrtime.bigint();
const result = spawnSync(process.execPath, [cli, "render", "src/graphics/index.ts", "G8PerformanceBenchmark", outputPath, "--frames", `0-${frames - 1}`, "--public-dir=out/remotion-public", "--image-format=png", "--pixel-format=yuva444p10le", "--codec=prores", "--prores-profile=4444", "--log=error"], {cwd: root, stdio: "inherit", shell: false});
const renderSeconds = Number(process.hrtime.bigint() - start) / 1e9;
if (result.status !== 0) process.exit(result.status ?? 1);
const diskMb = Number((fs.statSync(outputPath).size / (1024 * 1024)).toFixed(2));
const report = {
  video_s: seconds,
  render_s: Number(renderSeconds.toFixed(2)),
  ratio: Number((renderSeconds / seconds).toFixed(3)),
  machine: `${os.platform()} ${os.arch()} CPU (${os.cpus()[0]?.model ?? "desconocida"})`,
  frames,
  disk_used_mb: diskMb,
  target_60s_under_180s: seconds === 60 ? renderSeconds < 180 : null,
};
fs.mkdirSync(path.dirname(reportPath), {recursive: true});
fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
if (!keep) fs.rmSync(outputPath, {force: true});
console.log(`Benchmark: ${seconds}s en ${report.render_s}s (${report.ratio}x), ${diskMb} MB${keep ? "" : "; video temporal eliminado"}.`);
console.log(`Reporte: ${path.relative(root, reportPath)}`);
