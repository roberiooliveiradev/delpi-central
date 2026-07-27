/**
 * Configuração compartilhada de Module Federation para plugins MFE.
 *
 * Doc: plugins/plugin-ui/docs/module-federation.md
 */
import path from "node:path";
import { REACT_PINNED_VERSION } from "./reactPinnedVersion";

export { REACT_PINNED_VERSION } from "./reactPinnedVersion";

/** URL do remoteEntry servido pelo container delpi-plugin-ui (via gateway). */
export const PLUGIN_UI_REMOTE_ENTRY = "/apps/plugin-ui/assets/remoteEntry.js";

/** Porta padrão do `vite dev` do plugin-ui local. */
export const PLUGIN_UI_DEV_PORT = 5010;

export { federationReactProxyFixPlugin } from "./federationReactProxyFix";

/** URL do remoteEntry em dev local (plugin-ui rodando com npm run dev). */
export const PLUGIN_UI_DEV_REMOTE_ENTRY = `http://localhost:${PLUGIN_UI_DEV_PORT}/apps/plugin-ui/assets/remoteEntry.js`;

/** Singleton MF — mesma versão exata em portal + MFEs + plugin-ui (evita React #527). */
export const FEDERATION_SHARED_REACT = {
  react: {
    singleton: true,
    strictVersion: true,
    requiredVersion: REACT_PINNED_VERSION,
    version: REACT_PINNED_VERSION,
  },
  "react-dom": {
    singleton: true,
    strictVersion: true,
    requiredVersion: REACT_PINNED_VERSION,
    version: REACT_PINNED_VERSION,
  },
  "lucide-react": { singleton: true, version: "0.0.0" },
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
  const indexTs = path.join(uiRoot, "index.ts");
  const stylesCss = path.join(uiRoot, "styles.css");
  const logoMarkStub = path.resolve(pluginDir, "src/test-stubs/delpiLogoMark.stub.ts");
  const logoRawStub = path.resolve(pluginDir, "src/test-stubs/logoDelpiMark.svg.raw.js");
  return [
    {
      find: path.join(uiRoot, "brand/delpiLogoMark.ts"),
      replacement: logoMarkStub,
    },
    {
      find: /[/\\]brand[/\\]delpiLogoMark\.ts$/,
      replacement: logoMarkStub,
    },
    {
      find: path.join(uiRoot, "assets/logoDelpiMark.svg?raw"),
      replacement: logoRawStub,
    },
    {
      find: /logoDelpiMark\.svg\?raw$/,
      replacement: logoRawStub,
    },
    { find: "@delpi/plugin-ui/index", replacement: indexTs },
    { find: "@delpi/plugin-ui/styles", replacement: stylesCss },
    { find: "@delpi/plugin-ui", replacement: indexTs },
  ];
}
