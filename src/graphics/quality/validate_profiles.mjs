import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../../..");
const generatedPath = path.join(root, "src/graphics/beatmap/generated-beatmap.ts");
const syncScript = path.join(root, "src/graphics/beatmap/sync-beatmap.mjs");
const beatmapPath = path.join(root, "pipeline/beatmap.md");
const transcriptPath = path.join(root, "pipeline/examples/transcript.fixture.json");
const outputDirectory = path.join(root, "out/profile-validation");
const remotionCli = path.join(root, "node_modules/@remotion/cli/remotion-cli.js");
const profiles = ["viral-dinamico", "corporativo-sobrio"];
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "minthy-profiles-"));
const originalGenerated = fs.readFileSync(generatedPath, "utf8");

const run = (command, args) => {
  const result = spawnSync(command, args, { cwd: root, encoding: "utf8", shell: false });
  if (result.status !== 0) {
    throw new Error(`${command} falló:\n${result.stdout}\n${result.stderr}`);
  }
  return result;
};

const readGeneratedConfig = () => {
  const source = fs.readFileSync(generatedPath, "utf8");
  const match = source.match(/export const generatedBeatMap = ([\s\S]+) as const satisfies/);
  if (!match) throw new Error("No se pudo leer generated-beatmap.ts");
  return JSON.parse(match[1]).config;
};

try {
  fs.mkdirSync(outputDirectory, { recursive: true });
  const beatmap = fs.readFileSync(beatmapPath, "utf8");
  const report = [];
  for (const profileName of profiles) {
    const isolatedBeatmap = beatmap.replace(
      /^-\s*Perfil:\s*`?[a-z0-9_-]+`?\s*$/im,
      `- Perfil: \`${profileName}\``,
    );
    const isolatedPath = path.join(temporary, `${profileName}.md`);
    fs.writeFileSync(isolatedPath, isolatedBeatmap, "utf8");
    run(process.execPath, [
      syncScript,
      `--beatmap=${isolatedPath}`,
      `--transcript=${transcriptPath}`,
      `--validation-profile=${profileName}`,
      `--output=${generatedPath}`,
    ]);
    const config = readGeneratedConfig();
    const stillPath = path.join(outputDirectory, `${profileName}.png`);
    run(process.execPath, [remotionCli,
      "still", "src/graphics/index.ts", "BeatMapOverlay", stillPath,
      "--frame=45", "--image-format=png",
    ]);
    report.push({
      profile: profileName,
      captionStyle: config.captionStyle,
      theme: config.theme,
      accent: config.accent,
      primaryFont: config.font,
      headlineFontRequested: config.headlineFont,
      headlineFontResolved: "Inter",
      accentFont: config.accentFont,
      still: path.relative(root, stillPath).replaceAll("\\", "/"),
      sha256: crypto.createHash("sha256").update(fs.readFileSync(stillPath)).digest("hex"),
    });
  }
  assert.equal(report[0].captionStyle, "word-by-word");
  assert.equal(report[1].captionStyle, "phrase");
  assert.notEqual(report[0].theme, report[1].theme);
  assert.notEqual(report[0].accent, report[1].accent);
  assert.notEqual(report[0].sha256, report[1].sha256);
  fs.writeFileSync(
    path.join(outputDirectory, "report.json"),
    `${JSON.stringify({ valid: true, profiles: report }, null, 2)}\n`,
    "utf8",
  );
  console.log(`Perfiles validados: ${report.map((item) => `${item.profile} (${item.captionStyle})`).join(", ")}.`);
  console.log(`Reporte: ${path.join(outputDirectory, "report.json")}`);
} finally {
  fs.writeFileSync(generatedPath, originalGenerated, "utf8");
  fs.rmSync(temporary, { recursive: true, force: true });
}

