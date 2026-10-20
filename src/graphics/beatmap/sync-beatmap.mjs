import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(scriptDirectory, "../../..");
const readArgument = (name) => process.argv.find((argument) => argument.startsWith(`--${name}=`))?.slice(name.length + 3);
const beatMapPath = path.resolve(repositoryRoot, readArgument("beatmap") ?? "pipeline/beatmap.md");
const transcriptPath = path.resolve(repositoryRoot, readArgument("transcript") ?? "pipeline/transcript.json");
const outputPath = path.resolve(repositoryRoot, readArgument("output") ?? path.relative(repositoryRoot, path.join(scriptDirectory, "generated-beatmap.ts")));
const validationProfile = readArgument("validation-profile");
const sceneCodes = new Set(["CAPTIONS", "CAPTION_UI", "SPLIT", "FULLSCREEN"]);
const transitionCodes = new Set(["cut", "fade", "slide-up", "zoom-in"]);
const zoneCodes = new Set(["arriba", "abajo", "lado", "auto"]);
const brollSources = new Set(["own", "stock", "ai"]);
const visualTags = new Set(["contador", "comparacion", "titular", "busqueda", "lista", "cifra", "tarjeta", "interludio", "recuadro", "hablante", "broll"]);
const v1Headers = ["#", "Inicio", "Fin", "Speech", "Escena", "Visual", "Texto en pantalla", "Transición", "SFX", "Caption"];
const legacyHeaders = v1Headers.filter((header) => header !== "Texto en pantalla");
const v2Headers = ["#", "Inicio", "Fin", "Speech", "Escena", "Visual", "Texto en pantalla", "B-roll", "Zona", "Transición", "SFX", "Caption"];

const normalize = (value) =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9#]+/g, " ")
    .trim();

const parseTime = (value, rowNumber, column) => {
  const match = String(value).trim().match(/^(\d{2,}):(\d{2})\.(\d+)$/);
  if (!match) throw new Error(`Fila ${rowNumber}: ${column} debe usar mm:ss.s; recibido "${value}".`);
  const minutes = Number(match[1]);
  const seconds = Number(`${match[2]}.${match[3]}`);
  if (seconds >= 60) throw new Error(`Fila ${rowNumber}: ${column} contiene segundos >= 60.`);
  return minutes * 60 + seconds;
};

const cells = (line) => line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((cell) => cell.trim());

const matchingContract = (rawHeaders, markdown) => {
  const matches = (list) => rawHeaders.length === list.length && rawHeaders.every((header, index) => header === list[index]);
  const declaredVersion = markdown.match(/Contrato:\s*`?v([12])\b/i)?.[1];
  const detectedVersion = matches(v2Headers) ? "v2" : matches(v1Headers) || matches(legacyHeaders) ? "v1" : null;
  if (!detectedVersion) {
    throw new Error(
      `Contrato inválido. Columnas v1: ${v1Headers.join(" | ")}. Columnas v2: ${v2Headers.join(" | ")}. Recibidas: ${rawHeaders.join(" | ")}.`,
    );
  }
  if (declaredVersion && `v${declaredVersion}` !== detectedVersion) {
    throw new Error(`Contrato declarado v${declaredVersion}, pero las columnas corresponden a ${detectedVersion}.`);
  }
  if (detectedVersion === "v2" && declaredVersion !== "2") {
    throw new Error('El contrato v2 debe declarar la línea "Contrato: v2" en el encabezado.');
  }
  return detectedVersion;
};

const parseBroll = (value, rowNumber, contractVersion) => {
  if (contractVersion === "v1") return { source: "none", value: "" };
  const raw = String(value ?? "").trim();
  if (raw === "-") return { source: "none", value: "" };
  const match = raw.match(/^([a-z]+):(.*)$/i);
  if (!match || !brollSources.has(match[1].toLowerCase())) {
    throw new Error(`Fila ${rowNumber}: B-roll debe ser "-" o comenzar con own:, stock: o ai:; recibido "${raw}".`);
  }
  const content = match[2].trim();
  if (!content) throw new Error(`Fila ${rowNumber}: B-roll "${match[1]}:" necesita contenido después del prefijo.`);
  return { source: match[1].toLowerCase(), value: content };
};

const parseZone = (value, rowNumber, contractVersion) => {
  if (contractVersion === "v1") return "auto";
  const zone = String(value ?? "").trim().toLowerCase();
  if (!zoneCodes.has(zone)) {
    throw new Error(`Fila ${rowNumber}: Zona desconocida "${value}". Válidas: ${[...zoneCodes].join(", ")}.`);
  }
  return zone;
};

const parseVisualTag = (visual, rowNumber) => {
  const match = visual.match(/^\[([^\]]+)\]/);
  if (!match) return null;
  const tag = normalize(match[1]).replace(/\s+/g, "");
  if (!visualTags.has(tag)) {
    throw new Error(`Fila ${rowNumber}: etiqueta Visual desconocida "[${match[1]}]". Válidas: ${[...visualTags].map((item) => `[${item}]`).join(", ")}.`);
  }
  return tag;
};

const parseConfig = (markdown) => {
  const declared = markdown.match(/^-\s*Perfil:\s*`?([a-z0-9_-]+)`?\s*$/im)?.[1];
  const activePath = path.join(repositoryRoot, "profiles/ACTIVE");
  if (!fs.existsSync(activePath)) throw new Error("No existe profiles/ACTIVE; Juan debe seleccionar un perfil.");
  const configuredActive = fs.readFileSync(activePath, "utf8").trim();
  const active = validationProfile ?? configuredActive;
  if (validationProfile) {
    console.warn(`Validación aislada: se usa el perfil "${validationProfile}" sin modificar profiles/ACTIVE.`);
  }
  if (!active || active === "_template") throw new Error("profiles/ACTIVE no contiene un perfil utilizable.");
  if (declared && declared !== active) {
    throw new Error(`El perfil del BeatMap "${declared}" no coincide con profiles/ACTIVE "${active}".`);
  }
  const profileName = declared ?? active;
  if (!/^[a-z0-9_-]+$/.test(profileName)) throw new Error(`Nombre de perfil inválido "${profileName}".`);
  const profilePath = path.join(repositoryRoot, "profiles", profileName, "profile.json");
  if (!fs.existsSync(profilePath)) throw new Error(`No existe profiles/${profileName}/profile.json.`);
  let profile;
  try {
    profile = JSON.parse(fs.readFileSync(profilePath, "utf8"));
  } catch (error) {
    throw new Error(`profiles/${profileName}/profile.json no es JSON válido: ${error.message}`);
  }
  const width = Number(profile.format?.width);
  const height = Number(profile.format?.height);
  const fps = Number(profile.format?.fps);
  if (![width, height, fps].every((value) => Number.isInteger(value) && value > 0)) {
    throw new Error(`profiles/${profileName}/profile.json debe definir format.width, format.height y format.fps positivos.`);
  }
  if (typeof profile.theme?.mode !== "string" || typeof profile.theme?.accent !== "string" || typeof profile.theme?.fonts?.primary !== "string") {
    throw new Error(`profiles/${profileName}/profile.json debe definir theme.mode, theme.accent y theme.fonts.primary.`);
  }
  const captionStyle = profile.editing?.captionStyle;
  if (!new Set(["word-by-word", "phrase"]).has(captionStyle)) {
    throw new Error(`profiles/${profileName}/profile.json debe definir editing.captionStyle como "word-by-word" o "phrase".`);
  }
  return {
    profile: profileName,
    theme: profile.theme.mode,
    accent: profile.theme.accent,
    font: profile.theme.fonts.primary,
    headlineFont: profile.theme.fonts.headline ?? profile.theme.fonts.primary,
    accentFont: profile.theme.fonts.accentScript ?? profile.theme.fonts.primary,
    textColor: profile.theme.text ?? "#1D1D1F",
    textSecondary: profile.theme.textSecondary ?? "#6E6E73",
    captionStyle,
    width,
    height,
    fps,
  };
};

const parseTable = (markdown, fps) => {
  const lines = markdown.split(/\r?\n/);
  const headerIndex = lines.findIndex((line) => {
    const normalized = normalize(line);
    return line.trim().startsWith("|") && normalized.includes("inicio") && normalized.includes("fin");
  });
  if (headerIndex < 0) throw new Error("No se encontró la tabla '## Beats' con columnas Inicio y Fin.");

  const rawHeaders = cells(lines[headerIndex]);
  const contractVersion = matchingContract(rawHeaders, markdown);
  const headers = rawHeaders.map(normalize);
  const rows = [];
  for (let lineIndex = headerIndex + 2; lineIndex < lines.length; lineIndex += 1) {
    if (!lines[lineIndex].trim().startsWith("|")) break;
    const values = cells(lines[lineIndex]);
    if (values.length < 2) continue;
    rows.push(Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
  }

  const warnings = [];
  const beats = [];
  let previousEnd = 0;

  for (const [rowIndex, row] of rows.entries()) {
    const rowNumber = rowIndex + 1;
    const startSeconds = parseTime(row.inicio, rowNumber, "Inicio");
    const endSeconds = parseTime(row.fin, rowNumber, "Fin");
    if (endSeconds <= startSeconds) throw new Error(`Fila ${rowNumber}: Fin debe ser posterior a Inicio.`);
    if (startSeconds < previousEnd) throw new Error(`Fila ${rowNumber}: la escena se solapa con la anterior.`);
    previousEnd = endSeconds;
    const index = Number.parseInt(row["#"], 10);
    if (!Number.isInteger(index) || index < 1) throw new Error(`Fila ${rowNumber}: # debe ser un entero positivo.`);
    const scene = row.escena.trim();
    if (!sceneCodes.has(scene)) throw new Error(`Fila ${rowNumber}: código Escena desconocido "${scene}".`);
    const speech = row.speech.trim();
    const visual = row.visual.trim();
    if (!speech) throw new Error(`Fila ${rowNumber}: Speech no puede estar vacío.`);
    if (!visual) throw new Error(`Fila ${rowNumber}: Visual no puede estar vacío.`);
    const transition = row.transicion.trim();
    if (!transitionCodes.has(transition)) {
      throw new Error(`Fila ${rowNumber}: Transición desconocida "${transition}". Válidas: ${[...transitionCodes].join(", ")}.`);
    }
    const caption = row.caption.trim() === "-" ? "" : row.caption.trim();
    const accentKeywords = caption.split(/[,;/]+|\s+en\s+acento$/i).map((value) => value.trim()).filter(Boolean);
    const broll = parseBroll(row["b roll"], rowNumber, contractVersion);
    const zone = parseZone(row.zona, rowNumber, contractVersion);
    beats.push({
      contractVersion,
      id: `beat-${String(index).padStart(2, "0")}`,
      index,
      startSeconds,
      endSeconds,
      startFrame: Math.round(startSeconds * fps),
      endFrame: Math.max(Math.round(endSeconds * fps), Math.round(startSeconds * fps) + 2),
      speech,
      scene,
      visual,
      visualTag: parseVisualTag(visual, rowNumber),
      onScreenText: (row["texto en pantalla"] ?? "").trim() === "-" ? "" : (row["texto en pantalla"] ?? "").trim(),
      broll,
      zone,
      transition,
      sfx: row.sfx.trim() === "-" ? "" : row.sfx.trim(),
      caption,
      accentKeywords,
      words: [],
    });
  }
  if (beats.length === 0) throw new Error("La tabla Beats no contiene escenas.");
  return { contractVersion, beats, warnings };
};

const normalizeWord = (value) => normalize(value).replace(/\s+/g, "");

const containsPhrase = (haystack, needle) => {
  if (needle.length === 0 || needle.length > haystack.length) return false;
  return haystack.some((_, index) => needle.every((word, offset) => haystack[index + offset] === word));
};

const uniformWords = (beat) => {
  const tokens = beat.speech.split(/\s+/).filter(Boolean);
  const span = beat.endFrame - beat.startFrame;
  return tokens.map((text, index) => ({
    text,
    startFrame: Math.floor((index / tokens.length) * span),
    endFrame: Math.max(Math.ceil(((index + 1) / tokens.length) * span), Math.floor((index / tokens.length) * span) + 3),
  }));
};

const readTranscript = () => {
  if (!fs.existsSync(transcriptPath)) return null;
  let transcript;
  try {
    transcript = JSON.parse(fs.readFileSync(transcriptPath, "utf8"));
  } catch (error) {
    throw new Error(`pipeline/transcript.json no es JSON válido: ${error.message}`);
  }
  if (!Array.isArray(transcript.words)) throw new Error("pipeline/transcript.json debe contener un array 'words'.");
  for (const [index, word] of transcript.words.entries()) {
    if (typeof word.word !== "string" || !Number.isFinite(word.start) || !Number.isFinite(word.end) || word.end <= word.start) {
      throw new Error(`pipeline/transcript.json: palabra ${index + 1} debe tener word, start y end válidos.`);
    }
  }
  return transcript.words;
};

try {
  if (!fs.existsSync(beatMapPath)) throw new Error("No existe pipeline/beatmap.md.");
  const markdown = fs.readFileSync(beatMapPath, "utf8");
  const config = parseConfig(markdown);
  const parsed = parseTable(markdown, config.fps);
  const transcriptWords = readTranscript();
  let transcriptSource = transcriptWords ? "aligned" : "uniform";
  if (!transcriptWords) parsed.warnings.push(`${path.relative(repositoryRoot, transcriptPath).replaceAll("\\", "/")} no existe; se repartieron las palabras uniformemente dentro de cada escena.`);

  parsed.beats = parsed.beats.map((beat) => {
    const aligned = transcriptWords
      ? transcriptWords
          .filter((word) => word.start < beat.endSeconds && word.end > beat.startSeconds)
          .map((word) => ({
            text: word.word,
            startFrame: Math.max(0, Math.round((word.start - beat.startSeconds) * config.fps)),
            endFrame: Math.min(beat.endFrame - beat.startFrame, Math.round((word.end - beat.startSeconds) * config.fps)),
          }))
      : [];
    if (transcriptWords && aligned.length === 0) {
      throw new Error(`Beat ${beat.index}: existe transcript, pero no contiene palabras en este intervalo. Regenera el transcript con los tiempos del rough cut.`);
    }
    const words = transcriptWords ? aligned : uniformWords(beat);
    const speechWords = words.map((word) => normalizeWord(word.text));
    for (const keyword of beat.accentKeywords) {
      const keywordWords = keyword.split(/\s+/).map(normalizeWord).filter(Boolean);
      if (!containsPhrase(speechWords, keywordWords)) {
        throw new Error(`Beat ${beat.index}: Caption "${keyword}" debe coincidir literalmente y en orden con Speech/transcript.`);
      }
    }
    return { ...beat, words };
  });

  const durationInFrames = Math.max(...parsed.beats.map((beat) => beat.endFrame), config.fps);
  const relativeSource = path.relative(repositoryRoot, beatMapPath).replaceAll("\\", "/");
  const payload = {
    contractVersion: parsed.contractVersion,
    fps: config.fps,
    source: "pipeline",
    sourcePath: relativeSource,
    transcriptSource,
    config,
    warnings: parsed.warnings,
    durationInFrames,
    beats: parsed.beats,
  };
  const source = `import type { GeneratedBeatMap } from "./types";\n\nexport const generatedBeatMap = ${JSON.stringify(payload, null, 2)} as const satisfies GeneratedBeatMap;\n`;
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, source, "utf8");
  console.log(`BeatMap sincronizado: ${parsed.beats.length} escenas, ${durationInFrames} frames, transcript ${transcriptSource}.`);
  for (const warning of parsed.warnings) console.warn(`Aviso: ${warning}`);
} catch (error) {
  console.error(`ERROR BeatMap: ${error.message}`);
  process.exit(1);
}
