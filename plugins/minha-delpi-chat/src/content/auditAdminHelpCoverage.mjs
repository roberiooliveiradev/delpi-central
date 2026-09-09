/**
 * Auditor estrutural de Ajuda in-app do admin e do Studio (minha-delpi-chat).
 * Falha se faltar helpHint/hint/FieldLabel nas superfícies P0.
 */
import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";

/** @typedef {{ file: string, kind: string, id: string }} HelpCoverageGap */

export const SKIP_FILES = new Set([
  "ui/components/admin/shared/AdminTabHeader.tsx",
  "ui/components/admin/shared/AdminKpiCard.tsx",
  "ui/components/admin/shared/AdminFormCheckbox.tsx",
  "ui/components/admin/shared/chatAdminFormFields.ts",
  "ui/components/admin/shared/AdminDataTable.tsx",
  "ui/components/workspace/agentBuilder/AgentBuilderCheckbox.tsx",
  "content/auditAdminHelpCoverage.mjs",
]);

const STUDIO_FILES = [
  "ui/pages/ChatAgentsPage.tsx",
  "ui/pages/ChatAgentBuilderPage.tsx",
  "ui/pages/ChatAgentActionsPage.tsx",
  "ui/pages/ChatAgentSkillsPage.tsx",
];

/**
 * @param {string} source
 * @param {number} start
 * @returns {{ end: number, text: string } | null}
 */
export function extractJsxElement(source, start) {
  if (source[start] !== "<") return null;
  let i = start + 1;
  let brace = 0;
  let paren = 0;
  let bracket = 0;
  /** @type {'"' | "'" | "`" | null} */
  let quote = null;
  let escaped = false;
  while (i < source.length) {
    const ch = source[i];
    if (quote) {
      if (escaped) escaped = false;
      else if (ch === "\\") escaped = true;
      else if (ch === quote) quote = null;
      i += 1;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === "`") {
      quote = ch;
      i += 1;
      continue;
    }
    if (ch === "{") brace += 1;
    else if (ch === "}") brace = Math.max(0, brace - 1);
    else if (ch === "(") paren += 1;
    else if (ch === ")") paren = Math.max(0, paren - 1);
    else if (ch === "[") bracket += 1;
    else if (ch === "]") bracket = Math.max(0, bracket - 1);
    else if (brace === 0 && paren === 0 && bracket === 0) {
      if (ch === "/" && source[i + 1] === ">") {
        return { end: i + 2, text: source.slice(start, i + 2) };
      }
      if (ch === ">") {
        return { end: i + 1, text: source.slice(start, i + 1) };
      }
    }
    i += 1;
  }
  return null;
}

function elementHasHint(elementText) {
  return /\bhint\s*=/.test(elementText) || /\bhelpHint\s*=/.test(elementText);
}

function elementId(elementText, fallback) {
  const labelMatch = elementText.match(
    /\b(?:label|title)\s*=\s*(?:\{`([^`]+)`\}|"([^"]+)"|'([^']+)')/,
  );
  if (labelMatch) {
    return (labelMatch[1] || labelMatch[2] || labelMatch[3] || fallback).trim();
  }
  const idMatch = elementText.match(/\bid\s*=\s*(?:"([^"]+)"|'([^']+)'|\{"([^"]+)"\})/);
  if (idMatch) return (idMatch[1] || idMatch[2] || idMatch[3]).trim();
  return fallback;
}

/**
 * @param {string} dir
 * @param {string[]} out
 */
function walkTsx(dir, out) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name === "dist") continue;
      walkTsx(full, out);
      continue;
    }
    if (!/\.(tsx|ts)$/.test(entry.name)) continue;
    if (/\.test\.(tsx|ts|mjs)$/.test(entry.name)) continue;
    if (entry.name.endsWith(".d.ts")) continue;
    out.push(full);
  }
}

/**
 * @param {string} srcRoot
 * @returns {string[]}
 */
export function listAdminHelpSourceFiles(srcRoot) {
  /** @type {string[]} */
  const out = [];
  walkTsx(join(srcRoot, "ui/components/admin"), out);
  walkTsx(join(srcRoot, "ui/pages/agent-actions"), out);
  for (const rel of STUDIO_FILES) {
    out.push(join(srcRoot, rel));
  }
  return [...new Set(out)].sort();
}

/**
 * @param {string} relativeFile
 * @param {string} source
 * @param {RegExp} tagRe
 * @param {string} kind
 * @returns {HelpCoverageGap[]}
 */
function findTagGaps(relativeFile, source, tagRe, kind) {
  /** @type {HelpCoverageGap[]} */
  const gaps = [];
  const re = new RegExp(tagRe.source, "g");
  let match;
  while ((match = re.exec(source)) !== null) {
    const extracted = extractJsxElement(source, match.index);
    if (!extracted) continue;
    if (elementHasHint(extracted.text)) {
      re.lastIndex = extracted.end;
      continue;
    }
    gaps.push({
      file: relativeFile,
      kind,
      id: elementId(extracted.text, kind),
    });
    re.lastIndex = extracted.end;
  }
  return gaps;
}

/**
 * @param {string} relativeFile
 * @param {string} source
 * @returns {HelpCoverageGap[]}
 */
export function auditSource(relativeFile, source) {
  return [
    ...findTagGaps(relativeFile, source, /<AdminTabHeader\b/, "tab-header"),
    ...findTagGaps(relativeFile, source, /<ChatAdminNative(?:Text|Select|TextArea)Field\b/, "native-field"),
    ...findTagGaps(relativeFile, source, /<AdminKpiCard\b/, "kpi"),
    ...findTagGaps(relativeFile, source, /<(?:AdminFormCheckbox|NativeCheckboxControl|AgentBuilderCheckbox)\b/, "checkbox"),
    ...findRawAdminFieldLabels(relativeFile, source),
  ];
}

/**
 * @param {string} relativeFile
 * @param {string} source
 * @returns {HelpCoverageGap[]}
 */
export function findRawAdminFieldLabels(relativeFile, source) {
  /** @type {HelpCoverageGap[]} */
  const gaps = [];
  const re = /<label\b[^>]*className="[^"]*mdc-admin-field[^"]*"/g;
  let match;
  while ((match = re.exec(source)) !== null) {
    gaps.push({
      file: relativeFile,
      kind: "raw-admin-label",
      id: `line:${source.slice(0, match.index).split("\n").length}`,
    });
  }
  return gaps;
}

/**
 * @param {string} srcRoot
 * @returns {HelpCoverageGap[]}
 */
export function collectAdminHelpCoverageGaps(srcRoot) {
  /** @type {HelpCoverageGap[]} */
  const gaps = [];
  for (const abs of listAdminHelpSourceFiles(srcRoot)) {
    const rel = relative(srcRoot, abs).replace(/\\/g, "/");
    if (SKIP_FILES.has(rel)) continue;
    const source = readFileSync(abs, "utf8");
    gaps.push(...auditSource(rel, source));
  }
  const seen = new Set();
  return gaps.filter((gap) => {
    const key = gapKey(gap);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/** @param {HelpCoverageGap} gap */
export function gapKey(gap) {
  return `${gap.file}::${gap.kind}::${gap.id}`;
}

/**
 * @param {HelpCoverageGap[]} gaps
 * @param {HelpCoverageGap[]} allowlist
 */
export function partitionAgainstAllowlist(gaps, allowlist) {
  const allowed = new Set(allowlist.map(gapKey));
  const unexpected = gaps.filter((gap) => !allowed.has(gapKey(gap)));
  const allowlisted = gaps.filter((gap) => allowed.has(gapKey(gap)));
  const staleAllowlist = allowlist.filter(
    (entry) => !gaps.some((gap) => gapKey(gap) === gapKey(entry)),
  );
  return { unexpected, allowlisted, staleAllowlist };
}

/**
 * @param {string} absPath
 */
export function loadAllowlist(absPath) {
  const raw = JSON.parse(readFileSync(absPath, "utf8"));
  const entries = Array.isArray(raw) ? raw : raw.gaps || [];
  return entries.map((entry) => ({
    file: String(entry.file),
    kind: String(entry.kind),
    id: String(entry.id),
  }));
}
