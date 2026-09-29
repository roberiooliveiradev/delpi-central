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

/**
 * Varredura de imports de hosts: todo nome importado de "@delpi/plugin-ui/index"
 * em plugins/<app>/src precisa existir no chunk do remote — senão o consumer recebe
 * `undefined` e só descobre em runtime (`TypeError: X is not a function`).
 * Imports type-only (símbolo exportado como `export type`/`export interface`)
 * são apagados no build e não são exigidos no chunk.
 */
const pluginsRoot = path.resolve(__dirname, "../..");
const uiSrc = path.resolve(__dirname, "../src");

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

const typeOnly = collectTypeOnlyExports(uiSrc);
const importRe =
  /import\s*(?:type\s*)?\{([^}]*)\}\s*from\s*["']@delpi\/plugin-ui(?:\/index)?["']/g;

const hostMissing = [];
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
        if (!source.includes(local)) {
          hostMissing.push(`${local} (${path.relative(pluginsRoot, file)})`);
        }
      }
    }
  }
}

if (hostMissing.length > 0) {
  console.error(
    `verify-host-exports FAIL: imports de hosts ausentes no remote final:\n  ${[...new Set(hostMissing)].join("\n  ")}`,
  );
  process.exit(1);
}

console.log(
  `verify-host-exports OK (${path.basename(exposePath)}): ${REQUIRED_HOST_EXPORTS.join(", ")}`,
);
