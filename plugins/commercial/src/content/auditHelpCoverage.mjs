/**
 * Shared help-coverage auditor for Portal Comercial.
 * Detects Commercial*Field without hint / labels.hint and DataTable columns
 * with header but without headerHint.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

export const FIELD_TAG_RE =
  /Commercial(?:Text|Select|MultiSelect|Date|TextArea)Field\b/;

export const EXEMPT_COLUMN_KEYS = new Set([
  "actions",
  "action",
  "expand",
  "index",
  "#",
  "rowIndex",
]);

export const SKIP_FILES = new Set(["app/commercialUi.ts"]);

/** @typedef {{ file: string, kind: "field" | "column", id: string }} HelpCoverageGap */

/**
 * @param {string} rootDir absolute path to plugins/commercial/src
 * @returns {string[]}
 */
export function listSourceFiles(rootDir) {
  /** @type {string[]} */
  const out = [];
  function walk(dir) {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === "node_modules" || entry.name === "dist") continue;
        walk(full);
        continue;
      }
      if (!/\.(tsx|ts)$/.test(entry.name)) continue;
      if (/\.test\.(tsx|ts|mjs)$/.test(entry.name)) continue;
      if (entry.name.endsWith(".d.ts")) continue;
      out.push(full);
    }
  }
  walk(rootDir);
  return out.sort();
}

/**
 * Extract a balanced JSX element starting at `<` index.
 * @param {string} source
 * @param {number} start index of `<`
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
      if (escaped) {
        escaped = false;
      } else if (ch === "\\") {
        escaped = true;
      } else if (ch === quote) {
        quote = null;
      }
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
        // opening tag only — treat as self-contained for props scan
        return { end: i + 1, text: source.slice(start, i + 1) };
      }
    }
    i += 1;
  }
  return null;
}

/**
 * @param {string} elementText
 * @returns {boolean}
 */
export function fieldElementHasHint(elementText) {
  if (/\bhint\s*=/.test(elementText)) return true;
  // labels={{ ... hint: ... }} or labels={{ hint: ...}}
  if (/\blabels\s*=\s*\{\{[\s\S]*?\bhint\s*:/.test(elementText)) return true;
  return false;
}

/**
 * @param {string} elementText
 * @returns {boolean}
 */
export function fieldElementHasLabel(elementText) {
  return (
    /\blabel\s*=/.test(elementText) ||
    /\bfieldLabel\s*=/.test(elementText) ||
    /\blabels\s*=\s*\{\{[\s\S]*?\btitle\s*:/.test(elementText)
  );
}

/**
 * @param {string} elementText
 * @returns {string}
 */
export function fieldElementId(elementText) {
  const labelMatch = elementText.match(/\blabel\s*=\s*(?:\{`([^`]+)`\}|"([^"]+)"|'([^']+)'|\{CM_HELP\.[^}]+\})/);
  if (labelMatch) {
    return (labelMatch[1] || labelMatch[2] || labelMatch[3] || "label").trim();
  }
  const nameMatch = elementText.match(/\bname\s*=\s*(?:"([^"]+)"|'([^']+)'|\{"([^"]+)"\})/);
  if (nameMatch) return (nameMatch[1] || nameMatch[2] || nameMatch[3]).trim();
  const valueMatch = elementText.match(/\bvalue\s*=\s*\{([a-zA-Z0-9_.]+)\}/);
  if (valueMatch) return valueMatch[1].trim();
  // stable short fingerprint
  const compact = elementText.replace(/\s+/g, " ").slice(0, 80);
  return `anon:${compact.length}:${compact.slice(0, 40)}`;
}

/**
 * Find Commercial*Field usages missing hint.
 * @param {string} relativeFile
 * @param {string} source
 * @returns {HelpCoverageGap[]}
 */
export function findFieldGaps(relativeFile, source) {
  /** @type {HelpCoverageGap[]} */
  const gaps = [];
  const re = /<(Commercial(?:Text|Select|MultiSelect|Date|TextArea)Field)\b/g;
  let match;
  while ((match = re.exec(source)) !== null) {
    const extracted = extractJsxElement(source, match.index);
    if (!extracted) continue;
    const text = extracted.text;
    if (!fieldElementHasLabel(text)) continue;
    if (fieldElementHasHint(text)) continue;
    gaps.push({
      file: relativeFile,
      kind: "field",
      id: fieldElementId(text),
    });
    re.lastIndex = extracted.end;
  }
  return gaps;
}

/**
 * Scan object literals that look like DataTableColumn definitions.
 * Heuristic: `{` … `key:` … `header:` … `}` at brace depth 1 from start.
 * @param {string} relativeFile
 * @param {string} source
 * @returns {HelpCoverageGap[]}
 */
export function findColumnGaps(relativeFile, source) {
  /** @type {HelpCoverageGap[]} */
  const gaps = [];
  for (let i = 0; i < source.length; i += 1) {
    if (source[i] !== "{") continue;
    // quick reject: next ~400 chars must contain key: and header:
    const window = source.slice(i, i + 600);
    if (!/\bkey\s*:/.test(window) || !/\bheader\s*:/.test(window)) continue;

    const block = extractObjectLiteral(source, i);
    if (!block) continue;
    const body = block.text;
    // Must be a column-like object: has key + header as props, not nested-only
    const keyMatch = body.match(
      /(?:^|[,{])\s*key\s*:\s*(?:"([^"]+)"|'([^']+)'|`([^`]+)`)/,
    );
    const headerMatch = body.match(/(?:^|[,{]|\n)\s*header\s*:/);
    if (!keyMatch || !headerMatch) {
      i = block.end - 1;
      continue;
    }
    const key = (keyMatch[1] || keyMatch[2] || keyMatch[3] || "").trim();
    if (!key || EXEMPT_COLUMN_KEYS.has(key)) {
      i = block.end - 1;
      continue;
    }
    // headerHint at top level of this object (not only nested)
    if (/(?:^|[,{]|\n)\s*headerHint\s*:/.test(body)) {
      i = block.end - 1;
      continue;
    }
    // Avoid matching random objects: require render or sortable or align or header string
    const looksLikeColumn =
      /\brender\s*:/.test(body) ||
      /\bsortable\s*:/.test(body) ||
      /\balign\s*:/.test(body) ||
      /\bheader\s*:\s*["'`]/.test(body);
    if (!looksLikeColumn) {
      i = block.end - 1;
      continue;
    }
    gaps.push({ file: relativeFile, kind: "column", id: key });
    i = block.end - 1;
  }
  return gaps;
}

/**
 * @param {string} source
 * @param {number} start index of `{`
 * @returns {{ end: number, text: string } | null}
 */
export function extractObjectLiteral(source, start) {
  if (source[start] !== "{") return null;
  let depth = 0;
  /** @type {'"' | "'" | "`" | null} */
  let quote = null;
  let escaped = false;
  for (let i = start; i < source.length; i += 1) {
    const ch = source[i];
    if (quote) {
      if (escaped) escaped = false;
      else if (ch === "\\") escaped = true;
      else if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === "`") {
      quote = ch;
      continue;
    }
    if (ch === "{") depth += 1;
    else if (ch === "}") {
      depth -= 1;
      if (depth === 0) {
        return { end: i + 1, text: source.slice(start, i + 1) };
      }
    }
  }
  return null;
}

/**
 * @param {string} srcRoot
 * @returns {HelpCoverageGap[]}
 */
export function collectHelpCoverageGaps(srcRoot) {
  /** @type {HelpCoverageGap[]} */
  const gaps = [];
  const columnHelpModule = join(srcRoot, "utils/customersColumnHelp.ts");
  let columnHelpSource = "";
  try {
    columnHelpSource = readFileSync(columnHelpModule, "utf8");
  } catch {
    columnHelpSource = "";
  }
  const helpMaps = loadColumnHelpMaps(columnHelpSource);

  for (const abs of listSourceFiles(srcRoot)) {
    const rel = relative(srcRoot, abs).replace(/\\/g, "/");
    if (SKIP_FILES.has(rel)) continue;
    if (rel.endsWith("auditHelpCoverage.mjs")) continue;
    if (rel.endsWith("customersColumnHelp.ts")) continue;
    const source = readFileSync(abs, "utf8");
    gaps.push(...findFieldGaps(rel, source));
    const columnGaps = findColumnGaps(rel, source);
    const coveredKeys = resolveWithColumnHelpKeys(source, helpMaps);
    for (const gap of columnGaps) {
      if (coveredKeys.has(gap.id)) continue;
      gaps.push(gap);
    }
  }
  // de-dupe
  const seen = new Set();
  return gaps.filter((g) => {
    const k = gapKey(g);
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

/**
 * @param {string} moduleSource
 * @returns {Record<string, Set<string>>}
 */
export function loadColumnHelpMaps(moduleSource) {
  /** @type {Record<string, Set<string>>} */
  const maps = {};
  const re = /export const (\w+)\s*[:=][^{]*\{([\s\S]*?)\n\};/g;
  let match;
  while ((match = re.exec(moduleSource)) !== null) {
    const name = match[1];
    if (!/HELP|COLUMN/i.test(name)) continue;
    const body = match[2];
    const keys = new Set();
    for (const keyMatch of body.matchAll(/["']?([A-Za-z0-9_-]+)["']?\s*:/g)) {
      keys.add(keyMatch[1]);
    }
    maps[name] = keys;
  }
  return maps;
}

/**
 * @param {string} source
 * @param {Record<string, Set<string>>} helpMaps
 */
export function resolveWithColumnHelpKeys(source, helpMaps) {
  const covered = new Set();
  const re = /withColumnHelp\s*\(\s*[\w.]+\s*,\s*(\w+)\s*\)/g;
  let match;
  while ((match = re.exec(source)) !== null) {
    const keys = helpMaps[match[1]];
    if (!keys) continue;
    for (const key of keys) covered.add(key);
  }
  return covered;
}

/** @param {HelpCoverageGap} g */
export function gapKey(g) {
  return `${g.file}::${g.kind}::${g.id}`;
}

/**
 * @param {HelpCoverageGap[]} gaps
 * @param {HelpCoverageGap[]} allowlist
 */
export function partitionAgainstAllowlist(gaps, allowlist) {
  const allowed = new Set(allowlist.map(gapKey));
  const unexpected = gaps.filter((g) => !allowed.has(gapKey(g)));
  const allowlisted = gaps.filter((g) => allowed.has(gapKey(g)));
  const staleAllowlist = allowlist.filter((a) => !gaps.some((g) => gapKey(g) === gapKey(a)));
  return { unexpected, allowlisted, staleAllowlist };
}

/**
 * @param {HelpCoverageGap[]} gaps
 */
export function formatGapsMarkdown(gaps) {
  const lines = [
    "| File | Kind | Id |",
    "|------|------|----|",
    ...gaps.map((g) => `| \`${g.file}\` | ${g.kind} | \`${g.id}\` |`),
  ];
  return lines.join("\n");
}

export function loadAllowlist(absPath) {
  const raw = JSON.parse(readFileSync(absPath, "utf8"));
  const entries = Array.isArray(raw) ? raw : raw.gaps || [];
  return entries.map((e) => ({
    file: String(e.file),
    kind: e.kind === "column" ? "column" : "field",
    id: String(e.id),
  }));
}
