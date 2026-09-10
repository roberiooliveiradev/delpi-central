/**
 * Gate pós-build: exports do Index usados só por hosts MFE (sem consumo interno
 * no remote) não podem sumir do chunk federado — sintoma típico:
 * `TypeError: X is not a function` no consumer.
 *
 * Uso: node scripts/verify-host-exports.mjs [dist/assets]
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const assetsDir = path.resolve(
  __dirname,
  "..",
  process.argv[2] ?? "dist/assets",
);

/** Símbolos host-only que o Index MF deve preservar no bundle. */
const REQUIRED_HOST_EXPORTS = ["resolveColorFamily", "listColorFamilies", "getColorFamilyDefinition"];

function findIndexExpose(dir) {
  if (!fs.existsSync(dir)) {
    return null;
  }

  return (
    fs
      .readdirSync(dir)
      .filter((name) => name.startsWith("__federation_expose_Index-") && name.endsWith(".js"))
      .map((name) => path.join(dir, name))
      .sort()
      .at(-1) ?? null
  );
}

const exposePath = findIndexExpose(assetsDir);

if (!exposePath) {
  console.error(
    `verify-host-exports: não achei __federation_expose_Index-*.js em ${assetsDir}`,
  );
  process.exit(1);
}

const source = fs.readFileSync(exposePath, "utf8");
const missing = REQUIRED_HOST_EXPORTS.filter((name) => !source.includes(name));

if (missing.length > 0) {
  console.error(
    `verify-host-exports FAIL (${path.basename(exposePath)}): ausentes: ${missing.join(", ")}`,
  );
  process.exit(1);
}

console.log(
  `verify-host-exports OK (${path.basename(exposePath)}): ${REQUIRED_HOST_EXPORTS.join(", ")}`,
);
