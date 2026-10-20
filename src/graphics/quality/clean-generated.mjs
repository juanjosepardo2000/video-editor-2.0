import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../../..");
const output = path.resolve(root, "out");
if (path.dirname(output) !== root || path.basename(output) !== "out") throw new Error("Ruta de limpieza insegura.");
const apply = process.argv.includes("--apply");
const entries = fs.readdirSync(output, {withFileTypes: true}).filter((entry) => entry.name !== ".gitkeep");
const bytes = (target) => {
  const stat = fs.statSync(target);
  return stat.isDirectory() ? fs.readdirSync(target).reduce((sum, name) => sum + bytes(path.join(target, name)), 0) : stat.size;
};
const total = entries.reduce((sum, entry) => sum + bytes(path.join(output, entry.name)), 0);
console.log(`${apply ? "Eliminando" : "Simulación: se eliminarían"} ${entries.length} elemento(s), ${(total / 1024 / 1024).toFixed(1)} MB, solo dentro de ${output}.`);
if (apply) for (const entry of entries) fs.rmSync(path.join(output, entry.name), {recursive: true, force: true});
if (!apply) console.log("Ejecuta npm run clean:generated -- --apply para confirmar.");
