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

/** Instância canônica de React — portal/MFE semeiam antes do mount; importShared atualiza. */
export const DELPI_MF_REACT_GLOBAL = "__DELPI_MF_REACT__";

function isUsableReact(mod: unknown): mod is { useRef: (...args: unknown[]) => unknown } {
  return typeof (mod as { useRef?: unknown })?.useRef === "function";
}

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
    `$1==="react"&&${REACT_PUBLISH_GUARD}&&($2)`,
  );
}

const DELPI_MF_REACT_RESOLVE = `globalThis.${DELPI_MF_REACT_GLOBAL}?.useRef?globalThis.${DELPI_MF_REACT_GLOBAL}:`;

/**
 * App/recharts importam React bundled (index-*.js) fora do importShared.
 * Shims cacheiam `var e=Nu()` na 1ª execução — redireciona para o global canônico.
 */
export function patchBundledReactConsumerChunk(code: string): string {
  const importMatch = code.match(/import\{r as (\w+)\}from"\.\/index-[^"]+\.js"/);
  if (!importMatch) {
    return code;
  }
  const reactBridge = importMatch[1];
  if (!code.includes(`${reactBridge}()`)) {
    return code;
  }
  const resolveExpr = `(${DELPI_MF_REACT_RESOLVE}${reactBridge}())`;
  return code.replace(new RegExp(`${reactBridge}\\(\\)`, "g"), resolveExpr);
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
  let out = upgradeUnconditionalReactGlobalPublish(code);

  if (!out.includes("=e.default,e.default") && !out.includes("=_delpiMod,_delpiMod")) {
    return out;
  }
  if (out.includes(REACT_PUBLISH_GUARD)) {
    return out;
  }
  return out
    .replace(
      /(\w+)\[(\w+)\]=e\.default,e\.default/g,
      (_, cache, pkg) =>
        `${cache}[${pkg}]=e.default,${REACT_PUBLISH(cache, pkg)},e.default`,
    )
    .replace(
      /(\w+)\[(\w+)\]=(_delpiMod|e),\3(?=[\)}])/g,
      (_, cache, pkg, ret) =>
        `${cache}[${pkg}]=${ret},${REACT_PUBLISH(cache, pkg)},${ret}`,
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
    `function ${fnName}(){const __g=globalThis.${DELPI_MF_REACT_GLOBAL};if(__g)return __g;return`,
  );
}

function isBundledReactCoreChunk(code: string): boolean {
  return code.includes("n.useRef=function");
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
      if (chunk.fileName.includes("__federation_fn_import")) {
        return patchFederationImportPublishReact(patchFederationFlattenModule(code));
      }
      if (isBundledReactCoreChunk(code)) {
        return patchBundledReactCjsBridge(code);
      }
      if (isAppOrExposeChunk(chunk.fileName)) {
        return patchBundledReactConsumerChunk(code);
      }
      return null;
    },
    generateBundle(_outputOptions, bundle) {
      for (const item of Object.values(bundle)) {
        if (item.type !== "chunk") continue;

        if (item.fileName.includes("__federation_fn_import")) {
          item.code = patchFederationImportPublishReact(patchFederationFlattenModule(item.code));
          continue;
        }

        if (isBundledReactCoreChunk(item.code)) {
          item.code = patchBundledReactCjsBridge(item.code);
          continue;
        }

        if (isAppOrExposeChunk(item.fileName)) {
          item.code = patchBundledReactConsumerChunk(item.code);
        }
      }
    },
  };
}
