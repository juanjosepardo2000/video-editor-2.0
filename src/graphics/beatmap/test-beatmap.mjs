import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const syncScript = path.join(here, "sync-beatmap.mjs");
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "minthy-beatmap-test-"));
const repositoryRoot = path.resolve(here, "../../..");

const header = `# BeatMap

## Configuración global
- Tema: light Apple
- Color de acento: orange
- Fuente principal: Inter Semibold

## Beats
| # | Inicio | Fin | Speech | Escena | Visual | Transición | SFX | Caption |
|---|---|---|---|---|---|---|---|---|`;

const run = ({ markdown, transcript, transcriptPath = "transcript.json" }) => {
  const beatmap = path.join(temporary, `${crypto.randomUUID()}.md`);
  const output = path.join(temporary, `${crypto.randomUUID()}.ts`);
  fs.writeFileSync(beatmap, markdown, "utf8");
  if (transcript) fs.writeFileSync(path.join(temporary, transcriptPath), JSON.stringify(transcript), "utf8");
  const result = spawnSync(process.execPath, [syncScript, `--beatmap=${beatmap}`, `--transcript=${path.join(temporary, transcriptPath)}`, `--output=${output}`], {
    encoding: "utf8",
  });
  return { ...result, output, generated: fs.existsSync(output) ? fs.readFileSync(output, "utf8") : "" };
};

try {
  const valid = `${header}\n| 1 | 00:00.0 | 00:02.0 | hola mundo | CAPTIONS | Hablante | cut | - | hola |\n`;
  const aligned = run({
    markdown: valid,
    transcript: { words: [{ word: "hola", start: 0.1, end: 0.5 }, { word: "mundo", start: 0.6, end: 1.1 }] },
  });
  assert.equal(aligned.status, 0, aligned.stderr);
  assert.match(aligned.generated, /"transcriptSource": "aligned"/);
  assert.match(aligned.generated, /"startFrame": 3/);
  assert.match(aligned.generated, /"profile": "viral-dinamico"/);
  assert.match(aligned.generated, /"accent": "#F28C28"/);
  assert.match(aligned.generated, /"contractVersion": "v1"/);
  assert.match(aligned.generated, /"source": "none"/);
  assert.match(aligned.generated, /"zone": "auto"/);

  const fallback = run({ markdown: valid, transcript: null, transcriptPath: "missing.json" });
  assert.equal(fallback.status, 0, fallback.stderr);
  assert.match(fallback.generated, /"transcriptSource": "uniform"/);
  assert.match(fallback.stderr, /no existe/);

  const oldContract = run({
    markdown: `## Beats\n| Inicio | Fin | Tipo | Texto |\n|---|---|---|---|\n| 0 | 2 | caption | hola |`,
  });
  assert.equal(oldContract.status, 1);
  assert.match(oldContract.stderr, /ERROR BeatMap/);

  const overlap = run({
    markdown: `${header}\n| 1 | 00:00.0 | 00:02.0 | uno | CAPTIONS | A | cut | - | - |\n| 2 | 00:01.5 | 00:03.0 | dos | SPLIT | B | fade | - | - |\n`,
  });
  assert.equal(overlap.status, 1);
  assert.match(overlap.stderr, /solapa/);

  const badScene = run({
    markdown: `${header}\n| 1 | 00:00.0 | 00:02.0 | hola | DESCONOCIDA | A | - | - | - |\n`,
  });
  assert.equal(badScene.status, 1);
  assert.match(badScene.stderr, /Escena desconocido/);

  const badTransition = run({
    markdown: `${header}\n| 1 | 00:00.0 | 00:02.0 | hola | CAPTIONS | A | spin | - | - |\n`,
  });
  assert.equal(badTransition.status, 1);
  assert.match(badTransition.stderr, /Transición desconocida/);

  const incompleteTranscript = run({
    markdown: `${header}\n| 1 | 00:00.0 | 00:02.0 | uno | CAPTIONS | A | cut | - | - |\n| 2 | 00:02.0 | 00:04.0 | dos | SPLIT | B | fade | - | - |\n`,
    transcript: { words: [{ word: "uno", start: 0.2, end: 0.7 }] },
  });
  assert.equal(incompleteTranscript.status, 1);
  assert.match(incompleteTranscript.stderr, /existe transcript/);

  const nonLiteralCaption = run({
    markdown: `${header}\n| 1 | 00:00.0 | 00:02.0 | veinticinco por ciento | CAPTIONS | A | cut | - | 25% |\n`,
  });
  assert.equal(nonLiteralCaption.status, 1);
  assert.match(nonLiteralCaption.stderr, /coincidir literalmente/);

  const currentV1 = run({
    markdown: fs.readFileSync(path.join(repositoryRoot, "pipeline/beatmap.md"), "utf8"),
    transcript: JSON.parse(fs.readFileSync(path.join(repositoryRoot, "pipeline/examples/transcript.prueba.json"), "utf8")),
  });
  assert.equal(currentV1.status, 0, currentV1.stderr);
  assert.match(currentV1.generated, /^\s*"contractVersion": "v1"/m);

  const v2Example = run({
    markdown: fs.readFileSync(path.join(repositoryRoot, "pipeline/examples/beatmap.v2.example.md"), "utf8"),
    transcript: JSON.parse(fs.readFileSync(path.join(repositoryRoot, "pipeline/examples/transcript.prueba.json"), "utf8")),
  });
  assert.equal(v2Example.status, 0, v2Example.stderr);
  assert.match(v2Example.generated, /^\s*"contractVersion": "v2"/m);
  assert.match(v2Example.generated, /"source": "stock"/);
  assert.match(v2Example.generated, /"value": "video editing software screen"/);
  assert.match(v2Example.generated, /"zone": "arriba"/);

  const v2Header = `${header.replace("## Configuración global", "> Contrato: v2\n\n## Configuración global")
    .replace("| Visual | Transición", "| Visual | Texto en pantalla | B-roll | Zona | Transición")
    .replace("|---|---|---|---|---|---|---|---|---|", "|---|---|---|---|---|---|---|---|---|---|---|---|")}`;
  const invalidBroll = run({
    markdown: `${v2Header}\n| 1 | 00:00.0 | 00:02.0 | hola mundo | CAPTIONS | [hablante] Test | - | youtube:clip | auto | cut | - | hola |\n`,
  });
  assert.equal(invalidBroll.status, 1);
  assert.match(invalidBroll.stderr, /Fila 1: B-roll.*own:.*stock:.*ai:/);

  const emptyBroll = run({
    markdown: `${v2Header}\n| 1 | 00:00.0 | 00:02.0 | hola mundo | CAPTIONS | [hablante] Test | - | stock: | auto | cut | - | hola |\n`,
  });
  assert.equal(emptyBroll.status, 1);
  assert.match(emptyBroll.stderr, /necesita contenido/);

  const invalidZone = run({
    markdown: `${v2Header}\n| 1 | 00:00.0 | 00:02.0 | hola mundo | CAPTIONS | [hablante] Test | - | - | centro | cut | - | hola |\n`,
  });
  assert.equal(invalidZone.status, 1);
  assert.match(invalidZone.stderr, /Fila 1: Zona desconocida "centro"/);

  const invalidVisualTag = run({
    markdown: `${v2Header}\n| 1 | 00:00.0 | 00:02.0 | hola mundo | CAPTIONS | [video] Test | - | - | auto | cut | - | hola |\n`,
  });
  assert.equal(invalidVisualTag.status, 1);
  assert.match(invalidVisualTag.stderr, /etiqueta Visual desconocida/);

  const missingVersion = run({
    markdown: `${v2Header.replace("> Contrato: v2\n\n", "")}\n| 1 | 00:00.0 | 00:02.0 | hola mundo | CAPTIONS | [hablante] Test | - | - | auto | cut | - | hola |\n`,
  });
  assert.equal(missingVersion.status, 1);
  assert.match(missingVersion.stderr, /debe declarar la línea "Contrato: v2"/);

  console.log("BeatMap tests: 15/15 OK");
} finally {
  fs.rmSync(temporary, { recursive: true, force: true });
}
