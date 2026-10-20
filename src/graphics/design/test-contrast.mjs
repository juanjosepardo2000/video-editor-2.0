import assert from "node:assert/strict";
import { contrastRatio, ensureTextContrast, readableTextOn } from "./contrast.mjs";

const corporateAccent = "#5B7C99";
const darkCaptionSurface = "#040C0A";
const viralAccent = "#F28C28";
const lightCaptionSurface = "#F5F8F6";

const accessibleCorporate = ensureTextContrast(corporateAccent, darkCaptionSurface);
const accessibleViral = ensureTextContrast(viralAccent, lightCaptionSurface);

assert.ok(contrastRatio(accessibleCorporate, darkCaptionSurface) >= 4.5);
assert.ok(contrastRatio(accessibleViral, lightCaptionSurface) >= 4.5);
assert.ok(contrastRatio(readableTextOn(corporateAccent), corporateAccent) >= 4.5);
assert.equal(ensureTextContrast("#FFFFFF", "#000000"), "#FFFFFF");

console.log("Graphics contrast tests: 4/4 OK");
