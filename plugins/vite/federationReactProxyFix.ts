/**
 * Corrige flattenModule do @originjs/vite-plugin-federation (React 19).
 *
 * Object.assign({}, module.default, module) congela __CLIENT_INTERNALS.H = null
 * → useState/useRef null em recharts, zustand, plugin-ui (#294, #534, #741).
 * Substituído por Proxy com live bindings (upstream PR #743 — não publicado em 1.4.1).
 *
 * Chunks App-*.js ainda importam React bundled (index-*.js) fora do importShared;
 * o shim CJS é redirecionado para globalThis.__DELPI_MF_REACT__ quando disponível.
 */
import type { Plugin } from "vite";
import { DELPI_MF_PATCH_VERSION } from "./federationPatchVersion.mjs";

/** Instância canônica de React — portal/MFE semeiam antes do mount; importShared atualiza. */
export const DELPI_MF_REACT_GLOBAL = "__DELPI_MF_REACT__";

const REACT_INTERNALS_KEY = "__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE";

function reactHookDispatcher(mod: unknown): unknown {
  return (mod as Record<string, { H?: unknown } | undefined>)?.[REACT_INTERNALS_KEY]?.H;
}

/** React flatten quebrado expõe useRef mas H=null — tratar como inválido. */
export function isUsableReact(mod: unknown): mod is { useRef: (...args: unknown[]) => unknown } {
  return typeof (mod as { useRef?: unknown })?.useRef === "function" && reactHookDispatcher(mod) != null;
}

const USABLE_REACT_GLOBAL_GUARD = `(globalThis.${DELPI_MF_REACT_GLOBAL}&&typeof globalThis.${DELPI_MF_REACT_GLOBAL}.useRef=="function"&&globalThis.${DELPI_MF_REACT_GLOBAL}.${REACT_INTERNALS_KEY}?.H)`;

/** Publica React canônico — não sobrescreve instância válida já semeada pelo portal. */
export function publishDelpiMfReact(react: unknown): void {
  const g = globalThis as Record<string, unknown>;
  if (isUsableReact(g[DELPI_MF_REACT_GLOBAL])) return;
  if (isUsableReact(react)) {
    g[DELPI_MF_REACT_GLOBAL] = react;
  }
}

/** Proxy flatten sem reatribuir parâmetro `e` (strict → Assignment to constant variable). */
const PROXY_FLATTEN_EXPR = String.raw`_delpiMod=e.default?new Proxy(e.default,{get(p,r){return r!=="default"&&r in e?e[r]:p[r]},has(p,r){return r in e||r in p},ownKeys(p){const r=new Set([...Reflect.ownKeys(p),...Reflect.ownKeys(e)]);return r.delete("default"),[...r]}}):e`;

const BROKEN_PROXY_BRANCH =
  /:\(e\.default&&\(e=\(o=e,m=e\.default,new Proxy\(m,\{get\(p,r\)\{return r!=="default"&&r in o\?o\[r\]:p\[r\]\},has\(p,r\)\{return r in o\|\|r in p\},ownKeys\(p\)\{const r=new Set\(\[\.\.\.Reflect\.ownKeys\(p\),\.\.\.Reflect\.ownKeys\(o\)\]\);return r\.delete\("default"\),\[\.\.\.r\]\}\}\)\)\),(\w+)\[(\w+)\]=e,e\)/;

const OBJECT_ASSIGN_BRANCH =
  /:\(e\.default&&\(e=Object\.assign\(\{\},e\.default,e\)\),(\w+)\[(\w+)\]=e,e\)/;

const REACT_PUBLISH_GUARD = `!globalThis.${DELPI_MF_REACT_GLOBAL}`;

const REACT_PUBLISH = (cache: string, pkg: string) =>
  `${pkg}==="react"&&${REACT_PUBLISH_GUARD}&&(globalThis.${DELPI_MF_REACT_GLOBAL}=${cache}[${pkg}])`;

/** Corrige publish incondicional gerado por builds parciais ou runtime MF antigo. */
export function upgradeUnconditionalReactGlobalPublish(code: string): string {
  return code.replace(
    /(\w+)==="react"&&\(globalThis\.(__DELPI_MF_REACT__=\w+\[\w+\])\)/g,
    `$1==="react"&&${REACT_PUBLISH_GUARD}&&(globalThis.$2)`,
  );
}

const DELPI_MF_REACT_RESOLVE = `${USABLE_REACT_GLOBAL_GUARD}?globalThis.${DELPI_MF_REACT_GLOBAL}:`;

/** Identificadores minificados podem começar com `$` (ex.: `$h`) — `\w+` não casa. */
const MF_IDENT = String.raw`[$A-Za-z_][\w$]*`;

const REACT_CLIENT_INTERNALS = "__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE";
const REACT_DOM_INTERNALS = "__DOM_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE";

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Binding atribuído a partir de `id()` — inclui ternário já patchado:
 * `v=((globalThis…)?…:Zv())`.
 */
function findBridgeCallBinding(code: string, id: string): string | null {
  const assignRe = new RegExp(
    String.raw`(${MF_IDENT})=([^;]*${escapeRegExp(id)}\(\))`,
  );
  return code.match(assignRe)?.[1] ?? null;
}

/**
 * Escolhe o bridge CJS de React (não react-dom) entre vários `import{…r as X…}from"./index-*"`.
 *
 * Rollup às vezes emite `$h` = React e `kh` = react-dom. Se o bridge React não é
 * reconhecido, o patch redireciona `kh()`/`Zv()` para `__DELPI_MF_REACT__` →
 * `p.__DOM_INTERNALS` fica undefined → `Cannot read properties of undefined (reading 'd')`.
 *
 * Também casa imports multi-spec (`import{r as Lv,g as Xv}from…`) — o React core
 * costuma exportar `r` + `g`; regex só `{r as X}` ignorava esse bridge (api-delpi-console).
 */
export function resolveBundledReactBridgeName(code: string): string | null {
  const importRe = new RegExp(
    String.raw`import\{(?:[^}"']*,)*r as (${MF_IDENT})(?:,[^}"']*)*\}from"\.\/index-[^"?]+\.js(?:\?v=[^"]+)?"`,
    "g",
  );
  const bridges = [...code.matchAll(importRe)].map((m) => m[1]);
  if (bridges.length === 0) return null;

  for (const id of bridges) {
    if (!code.includes(`${id}()`)) continue;
    const binding = findBridgeCallBinding(code, id);
    if (binding && code.includes(`${binding}.${REACT_CLIENT_INTERNALS}`)) {
      return id;
    }
  }

  for (const id of bridges) {
    if (!code.includes(`${id}()`)) continue;
    const binding = findBridgeCallBinding(code, id);
    if (binding && code.includes(`${binding}.${REACT_DOM_INTERNALS}`)) {
      continue;
    }
    return id;
  }

  return null;
}

/**
 * App/recharts importam React bundled (index-*.js) fora do importShared.
 * Shims cacheiam `var e=Nu()` na 1ª execução — redireciona para o global canônico.
 *
 * Usa lookbehind de identificador: bridge curto (`rs`) não pode casar o sufixo de
 * `getSelectors()` / `getHours()` — isso gerava `get selecto((…` → Unexpected token '('.
 */
export function patchBundledReactConsumerChunk(code: string): string {
  const reactBridge = resolveBundledReactBridgeName(code);
  if (!reactBridge) {
    return code;
  }
  const resolveExpr = `(${DELPI_MF_REACT_RESOLVE}${reactBridge}())`;
  const callRe = new RegExp(`(?<![\\w$])${escapeRegExp(reactBridge)}\\(\\)`, "g");
  return code.replace(callRe, (match, offset: number) => {
    // Idempotente: não re-envolver o fallback já emitido (`…?globalThis.X:rs()`).
    const start = offset - DELPI_MF_REACT_RESOLVE.length;
    if (start >= 0 && code.startsWith(DELPI_MF_REACT_RESOLVE, start)) {
      return match;
    }
    return resolveExpr;
  });
}

function replaceFlattenElseBranch(code: string): string {
  const replacement = `:(${PROXY_FLATTEN_EXPR},$1[$2]=_delpiMod,_delpiMod)`;

  if (BROKEN_PROXY_BRANCH.test(code)) {
    code = code.replace(BROKEN_PROXY_BRANCH, replacement);
  } else if (code.includes("Object.assign({},e.default,e)")) {
    code = code.replace(OBJECT_ASSIGN_BRANCH, replacement);
  } else if (!code.includes("_delpiMod=e.default?new Proxy")) {
    return code;
  }

  if (!code.includes("var _delpiMod")) {
    code = code.replace(/function H\((\w+),(\w+)\)\{/, "function H($1,$2){var _delpiMod;");
  }
  return code;
}

/** Aplica patch Proxy em flattenModule do runtime MF. */
export function patchFederationFlattenModule(code: string): string {
  return replaceFlattenElseBranch(code);
}

/** Publica React no global quando importShared carrega o módulo shared. */
export function patchFederationImportPublishReact(code: string): string {
  let out = patchFederationFlattenModule(code);
  out = upgradeUnconditionalReactGlobalPublish(out);

  if (out.includes(REACT_PUBLISH_GUARD)) {
    return out;
  }

  if (!out.includes("=e.default,e.default") && !out.includes("=_delpiMod") && !out.includes("===\"react\"&&")) {
    return out;
  }

  return upgradeUnconditionalReactGlobalPublish(
    out
      .replace(
        /(\w+)\[(\w+)\]=e\.default,e\.default/g,
        (_, cache, pkg) =>
          `${cache}[${pkg}]=e.default,${REACT_PUBLISH(cache, pkg)},e.default`,
      )
      .replace(
        /(\w+)\[(\w+)\]=(_delpiMod|e),(\3)(?=,|\))/g,
        (_, cache, pkg, ret) =>
          `${cache}[${pkg}]=${ret},${REACT_PUBLISH(cache, pkg)},${ret}`,
      ),
  );
}

/**
 * Chunks index-*.js com React bundled exportam `r` como CJS bridge síncrono.
 * Redireciona para __DELPI_MF_REACT__ quando o share scope já foi semeado.
 */
export function patchBundledReactCjsBridge(code: string): string {
  if (!code.includes("n.useRef=function")) {
    return code;
  }
  const exportMatch = code.match(/export\{(\w+) as r\}/);
  if (!exportMatch) {
    return code;
  }
  const fnName = exportMatch[1];
  const fnStart = new RegExp(`function ${fnName}\\(\\)\\{return`);
  if (!fnStart.test(code)) {
    return code;
  }
  return code.replace(
    fnStart,
    `function ${fnName}(){const __g=globalThis.${DELPI_MF_REACT_GLOBAL};if(__g&&typeof __g.useRef=="function"&&__g.${REACT_INTERNALS_KEY}?.H)return __g;return`,
  );
}

function isBundledReactCoreChunk(code: string): boolean {
  return code.includes("n.useRef=function");
}

function mfCacheBustQuery(): string {
  return `?v=${DELPI_MF_PATCH_VERSION}`;
}

/** Query ?v= nos imports runtime — contorna Cloudflare immutable stale (mesmo hash pós renderChunk). */
export function patchMfRuntimeImportCacheBust(code: string): string {
  const q = mfCacheBustQuery();
  if (code.includes(`${q}"`) || code.includes(`${q}")`)) {
    return code;
  }
  return code
    .replace(/from"(\.\/(?:__federation_fn_import-|index-|App-)[^"?]+\.js)"/g, `from"$1${q}"`)
    .replace(/import\("(\.\/(?:App-|index-|__federation_fn_import-)[^"?]+\.js)"\)/g, `import("$1${q}")`);
}

export function patchRemoteEntryCacheBust(code: string): string {
  const q = mfCacheBustQuery();
  return code.replace(/(\/__federation_expose_[^"?]+\.js)/g, `$1${q}`);
}

function applyMfChunkPatches(code: string, fileName: string): string {
  if (fileName.includes("remoteEntry.js")) {
    return patchRemoteEntryCacheBust(code);
  }
  if (fileName.includes("__federation_fn_import")) {
    return patchMfRuntimeImportCacheBust(patchFederationImportPublishReact(code));
  }
  if (isBundledReactCoreChunk(code)) {
    return patchBundledReactCjsBridge(code);
  }
  if (isAppOrExposeChunk(fileName) || fileName.includes("_virtual___federation__")) {
    return patchMfRuntimeImportCacheBust(patchBundledReactConsumerChunk(code));
  }
  return code;
}

function isAppOrExposeChunk(fileName: string): boolean {
  return /(?:^|\/)App-/.test(fileName) || fileName.includes("__federation_expose_");
}

export function federationReactProxyFixPlugin(): Plugin {
  return {
    name: "federation-react-proxy-fix",
    apply: "build",
    enforce: "post",
    renderChunk(code, chunk) {
      const patched = applyMfChunkPatches(code, chunk.fileName);
      return patched === code ? null : patched;
    },
    generateBundle(_outputOptions, bundle) {
      for (const item of Object.values(bundle)) {
        if (item.type !== "chunk") continue;
        item.code = applyMfChunkPatches(item.code, item.fileName);
      }
    },
  };
}
