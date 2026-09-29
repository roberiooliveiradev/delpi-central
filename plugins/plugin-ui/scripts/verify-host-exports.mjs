/**
 * Gate pós-build: exports do Index usados só por hosts MFE (sem consumo interno
 * no remote) não podem sumir do chunk federado — sintoma típico:
 * `TypeError: X is not a function` no consumer.
 *
 * A verificação usa a cláusula `export { ... }` real do chunk — não substring,
 * que daria falso positivo com nomes colados (ex.: `parseMarkdownImagesX`).
 *
 * Uso: node scripts/verify-host-exports.mjs [dist/assets]
 *      node scripts/verify-host-exports.mjs --selftest
 */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** Símbolos host-only que o Index MF deve preservar no bundle. */
const REQUIRED_HOST_EXPORTS = [
  "resolveColorFamily",
  "listColorFamilies",
  "getColorFamilyDefinition",
  "createDashboardTopBarFavoritesStrip",
  "createDashboardTopBarUtilityCluster",
  "createDashboardTopBarUserIdentity",
  "createDashboardUserManual",
  "createDashboardEntityAvatarLabel",
  "createDashboardEventsSection",
  "createDashboardRecentAccessStrip",
  "formatPortalGreeting",
  "firstNameFromDisplay",
  "portalDayPeriodGreeting",
  "createDashboardDepartmentScoreBadge",
  "DepartmentScoreBadge",
  "LoadingActivityBadge",
  "DeckContentRunsView",
  "plainTextFromDeckContentRuns",
  "shouldPersistDeckContentRuns",
  "TaskEditorFrame",
  "TaskEmptyState",
  "TaskItemsTable",
  "TaskSearchField",
  "TaskWorklistSection",
  "TaskWorkspacePage",
  "buildTaskWorkspaceHighlights",
  "QuickPeriodSelector",
  "createDashboardQuickPeriodSelector",
  "resolvePeriodPreset",
  "todayIsoInTimeZone",
  "detectPeriodPreset",
  "resolveEffectivePeriodPreset",
  "PERIOD_PRESET_OPTIONS",
  "RoomSharedItemList",
  "createDashboardRoomSharedItemList",
  "InteractionRoomPage",
  "INTERACTION_ROOM_PAGE_LABELS_PT",
  "parseMarkdownImages",
  "listInlinePendingIdsFromMarkdown",
  "listInlineAttachmentIdsFromMarkdown",
  "rewriteInlinePendingInMarkdown",
  "PluginErrorBoundary",
  "pluginErrorBoundaryBemClasses",
  "PortalUserProfilePage",
  "createDashboardPortalUserProfilePage",
  "portalUserProfilePageBemClasses",
  "PORTAL_USER_PROFILE_LABELS_PT",
  "reactionLabelForCode",
  "aggregateReactionBarItems",
];

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

/**
 * Extrai os nomes realmente exportados pelo chunk federado a partir das
 * cláusulas `export { a as b, c }` — superfície efetiva do módulo remoto.
 */
function collectRealExports(source) {
  const names = new Set();
  const exportBlock = /export\s*\{([^}]*)\}/g;
  for (const m of source.matchAll(exportBlock)) {
    for (const spec of m[1].split(",")) {
      const s = spec.trim();
      if (!s) continue;
      const exported = s.split(/\s+as\s+/).at(-1)?.trim();
      if (exported) names.add(exported.replace(/^["']|["']$/g, ""));
    }
  }
  return names;
}

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name !== "node_modules") walk(full, out);
    } else if (/\.(ts|tsx)$/.test(entry.name)) {
      out.push(full);
    }
  }
  return out;
}

function collectTypeOnlyExports(dir) {
  const types = new Set();
  const decl = /\bexport\s+(?:type|interface)\s+([A-Za-z_$][\w$]*)/g;
  const grouped = /export\s+type\s*\{([^}]*)\}/g;
  const namedBlock = /export\s*\{([^}]*)\}/g;
  for (const file of walk(dir)) {
    const text = fs.readFileSync(file, "utf8");
    for (const m of text.matchAll(decl)) types.add(m[1]);
    for (const m of text.matchAll(grouped)) {
      for (const spec of m[1].split(",")) {
        const name = spec.trim().split(/\s+as\s+/).pop()?.trim();
        if (name) types.add(name);
      }
    }
    for (const m of text.matchAll(namedBlock)) {
      for (const spec of m[1].split(",")) {
        const s = spec.trim();
        if (!s.startsWith("type ")) continue;
        const name = s.slice(5).trim().split(/\s+as\s+/).pop()?.trim();
        if (name) types.add(name);
      }
    }
  }
  return types;
}

/**
 * Varredura de imports de hosts: todo nome importado de "@delpi/plugin-ui/index"
 * em plugins/<app>/src precisa existir como export real do remote — senão o
 * consumer recebe `undefined` e só descobre em runtime.
 */
function collectHostImportsMissing(realExports, typeOnly, pluginsRoot) {
  const importRe =
    /import\s*(?:type\s*)?\{([^}]*)\}\s*from\s*["']@delpi\/plugin-ui(?:\/index)?["']/g;
  const missing = [];
  for (const pluginDir of fs.readdirSync(pluginsRoot, { withFileTypes: true })) {
    if (!pluginDir.isDirectory() || pluginDir.name === "plugin-ui") continue;
    const srcDir = path.join(pluginsRoot, pluginDir.name, "src");
    if (!fs.existsSync(srcDir)) continue;
    for (const file of walk(srcDir)) {
      if (file.endsWith(".d.ts") || /\.test\.tsx?$/.test(file)) continue;
      const text = fs.readFileSync(file, "utf8");
      for (const m of text.matchAll(importRe)) {
        for (const spec of m[1].split(",")) {
          const name = spec.trim();
          if (!name || name.startsWith("type ")) continue;
          const local = name.split(/\s+as\s+/)[0].trim();
          if (!local || typeOnly.has(local)) continue;
          if (!realExports.has(local)) {
            missing.push(`${local} (${path.relative(pluginsRoot, file)})`);
          }
        }
      }
    }
  }
  return missing;
}

function verifyAssets(assetsDir, { checkHosts = true } = {}) {
  const exposePath = findIndexExpose(assetsDir);
  if (!exposePath) {
    return {
      ok: false,
      error: `verify-host-exports: não achei __federation_expose_Index-*.js em ${assetsDir}`,
    };
  }

  const source = fs.readFileSync(exposePath, "utf8");
  const realExports = collectRealExports(source);
  const missing = REQUIRED_HOST_EXPORTS.filter((name) => !realExports.has(name));

  let hostMissing = [];
  if (checkHosts) {
    const pluginsRoot = path.resolve(__dirname, "../..");
    const uiSrc = path.resolve(__dirname, "../src");
    const typeOnly = collectTypeOnlyExports(uiSrc);
    hostMissing = collectHostImportsMissing(realExports, typeOnly, pluginsRoot);
  }

  if (missing.length === 0 && hostMissing.length === 0) {
    return { ok: true, exposePath };
  }
  const parts = [];
  if (missing.length > 0) {
    parts.push(`exports obrigatórios ausentes: ${missing.join(", ")}`);
  }
  if (hostMissing.length > 0) {
    parts.push(
      `imports de hosts ausentes no remote:\n  ${[...new Set(hostMissing)].join("\n  ")}`,
    );
  }
  return {
    ok: false,
    exposePath,
    error: `verify-host-exports FAIL (${path.basename(exposePath)}): ${parts.join("\n")}`,
  };
}

/**
 * Teste negativo: copia o chunk real para um tmp dir, remove um export usado
 * por host e prova que o gate falha — inclusive onde `includes()` passaria
 * (a substring continua presente em `parseMarkdownImagesDisabled`).
 */
function selftest(assetsDir) {
  const exposePath = findIndexExpose(assetsDir);
  if (!exposePath) {
    console.error(`selftest: chunk não encontrado em ${assetsDir}`);
    return 1;
  }
  const real = fs.readFileSync(exposePath, "utf8");
  if (!/ as parseMarkdownImages[,}\s]/.test(real)) {
    console.error("selftest: chunk real não exporta parseMarkdownImages — corrija o build antes do selftest");
    return 1;
  }

  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "verify-exports-"));
  try {
    const name = path.basename(exposePath);
    fs.writeFileSync(path.join(tmp, name), real);
    const positive = verifyAssets(tmp, { checkHosts: false });
    if (!positive.ok) {
      console.error(`selftest FAIL: cópia intacta deveria passar: ${positive.error}`);
      return 1;
    }

    const mutated = real.replace(" as parseMarkdownImages", " as parseMarkdownImagesDisabled");
    if (mutated === real) {
      console.error("selftest FAIL: mutação não aplicada");
      return 1;
    }
    fs.writeFileSync(path.join(tmp, name), mutated);
    const negative = verifyAssets(tmp, { checkHosts: false });
    if (negative.ok) {
      console.error("selftest FAIL: gate passou com export removido");
      return 1;
    }
    if (!negative.error.includes("parseMarkdownImages")) {
      console.error(`selftest FAIL: ausência detectada, mas símbolo errado: ${negative.error}`);
      return 1;
    }
    console.log(
      `selftest OK: positivo passa (${path.basename(name)}) e remoção de parseMarkdownImages falha como esperado`,
    );
    return 0;
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

const argv = process.argv.slice(2);
const selftestMode = argv.includes("--selftest");
const assetsDir = path.resolve(
  __dirname,
  "..",
  argv.find((a) => !a.startsWith("--")) ?? "dist/assets",
);

if (selftestMode) {
  process.exit(selftest(assetsDir));
}

const result = verifyAssets(assetsDir);
if (!result.ok) {
  console.error(result.error);
  process.exit(1);
}

console.log(
  `verify-host-exports OK (${path.basename(result.exposePath)}): ${REQUIRED_HOST_EXPORTS.join(", ")}`,
);
