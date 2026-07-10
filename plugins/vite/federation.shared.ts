/**
 * Configuração compartilhada de Module Federation para plugins MFE.
 *
 * Doc: plugins/plugin-ui/docs/module-federation.md
 */
import path from "node:path";

/** URL do remoteEntry servido pelo container delpi-plugin-ui (via gateway). */
export const PLUGIN_UI_REMOTE_ENTRY = "/apps/plugin-ui/assets/remoteEntry.js";

/** Porta padrão do `vite dev` do plugin-ui local. */
export const PLUGIN_UI_DEV_PORT = 5010;

/** URL do remoteEntry em dev local (plugin-ui rodando com npm run dev). */
export const PLUGIN_UI_DEV_REMOTE_ENTRY = `http://localhost:${PLUGIN_UI_DEV_PORT}/apps/plugin-ui/assets/remoteEntry.js`;

/** Singleton MF — evita React #321 entre portal, MFE e remote plugin-ui. */
export const FEDERATION_SHARED_REACT = {
  react: { singleton: true, requiredVersion: "^19.0.0" },
  "react-dom": { singleton: true, requiredVersion: "^19.0.0" },
  "lucide-react": { singleton: true },
} as const;

/** React Flow — singleton com o host para evitar hooks nulos (useRef / zustand). */
export const FEDERATION_SHARED_XYFLOW = {
  "@xyflow/react": { singleton: true },
} as const;

/** Remote plugin-ui e MFEs com editor de diagrama (ex.: transformometro). */
export const FEDERATION_SHARED_WITH_DIAGRAM = {
  ...FEDERATION_SHARED_REACT,
  ...FEDERATION_SHARED_XYFLOW,
} as const;

/**
 * Resolve a URL do remote `@delpi/plugin-ui`.
 *
 * Prioridade: argumento explícito → env `VITE_PLUGIN_UI_REMOTE` → produção (path relativo).
 * Dev local: `VITE_PLUGIN_UI_DEV=1` ou passe `PLUGIN_UI_DEV_REMOTE_ENTRY`.
 */
export function resolvePluginUiRemoteEntry(explicit?: string): string {
  if (explicit) return explicit;
  if (process.env.VITE_PLUGIN_UI_REMOTE) return process.env.VITE_PLUGIN_UI_REMOTE;
  if (process.env.VITE_PLUGIN_UI_DEV === "1") return PLUGIN_UI_DEV_REMOTE_ENTRY;
  return PLUGIN_UI_REMOTE_ENTRY;
}

/** Bloco `remotes` para vite-plugin-federation. */
export function pluginUiRemote(explicitEntry?: string): Record<string, string> {
  return {
    "@delpi/plugin-ui": resolvePluginUiRemoteEntry(explicitEntry),
  };
}

/** Aliases de dedupe React — evita duas cópias quebrando hooks. */
export function reactResolveAliases(pluginDir: string) {
  return {
    react: path.resolve(pluginDir, "node_modules/react"),
    "react-dom": path.resolve(pluginDir, "node_modules/react-dom"),
  };
}

/** Alias de source para Vitest/tsc (tipos e testes sem remote). */
export function pluginUiTestAliases(pluginDir: string) {
  const uiRoot = path.resolve(pluginDir, "../plugin-ui/src");
  return {
    "@delpi/plugin-ui": path.join(uiRoot, "index.ts"),
    "@delpi/plugin-ui/styles": path.join(uiRoot, "styles.css"),
  };
}
