import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const syncScript = path.join(here, "sync-beatmap.mjs");
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "minthy-beatmap-test-"));

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
  assert.match(aligned.generated, /"onScreenText": ""/);
  assert.doesNotMatch(aligned.generated, /"onScreenText": "Hablante"/);

  const headerWithScreenText = header.replace("| Visual | Transición", "| Visual | Texto en pantalla | Transición").replace(
    "|---|---|---|---|---|---|---|---|---|",
    "|---|---|---|---|---|---|---|---|---|---|",
  );
  const screenCopy = run({
    markdown: `${headerWithScreenText}\n| 1 | 00:00.0 | 00:02.0 | hola mundo | CAPTION_UI | INSTRUCCION_INTERNA_UNICA | Copy permitido | cut | - | hola |\n`,
    transcript: { words: [{ word: "hola", start: 0.1, end: 0.5 }, { word: "mundo", start: 0.6, end: 1.1 }] },
  });
  assert.equal(screenCopy.status, 0, screenCopy.stderr);
  assert.match(screenCopy.generated, /"onScreenText": "Copy permitido"/);
  assert.doesNotMatch(screenCopy.generated, /"onScreenText": "INSTRUCCION_INTERNA_UNICA"/);

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

  console.log("BeatMap tests: 9/9 OK");
} finally {
  fs.rmSync(temporary, { recursive: true, force: true });
}
