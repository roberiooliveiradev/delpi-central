/**
 * Corrige flattenModule do @originjs/vite-plugin-federation (React 19).
 *
 * Object.assign({}, module.default, module) congela __CLIENT_INTERNALS.H = null
 * → useState/useRef null em recharts, zustand, plugin-ui (#294, #534, #741).
 * Substituído por Proxy com live bindings (upstream PR #743 — não publicado em 1.4.1).
 */
import type { Plugin } from "vite";

const OBJECT_ASSIGN_FLATTEN =
  /e\.default&&\(e=Object\.assign\(\{\},e\.default,e\)\)/g;

const PROXY_FLATTEN = String.raw`e.default&&(e=(o=e,m=e.default,new Proxy(m,{get(p,r){return r!=="default"&&r in o?o[r]:p[r]},has(p,r){return r in o||r in p},ownKeys(p){const r=new Set([...Reflect.ownKeys(p),...Reflect.ownKeys(o)]);return r.delete("default"),[...r]}})))`;

/** Aplica patch em código gerado do runtime MF. */
export function patchFederationFlattenModule(code: string): string {
  if (!code.includes("Object.assign({},e.default,e)")) {
    return code;
  }
  return code.replace(OBJECT_ASSIGN_FLATTEN, PROXY_FLATTEN);
}

export function federationReactProxyFixPlugin(): Plugin {
  return {
    name: "federation-react-proxy-fix",
    apply: "build",
    generateBundle(_outputOptions, bundle) {
      for (const item of Object.values(bundle)) {
        if (item.type !== "chunk") continue;
        if (!item.fileName.includes("__federation_fn_import")) continue;
        item.code = patchFederationFlattenModule(item.code);
      }
    },
  };
}
