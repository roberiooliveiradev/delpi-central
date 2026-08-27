import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";
import { federationReactProxyFixPlugin } from "../vite/federationReactProxyFix";
import { publicHubCacheBustEntryPlugin } from "../vite/cacheBustEntryPlugin";

import {
  FEDERATION_SHARED_REACT,
  pluginUiRemote,
  reactResolveAliases,
} from "../vite/federation.shared";

const PLUGIN_UI_SRC = path.resolve(__dirname, "../plugin-ui/src");

// Shell público (/p/) — styles/splash via MF; assinatura BUNDLED (sem share createPortal).
export default defineConfig({
  plugins: [
    federation({
      name: "public-hub",
      remotes: pluginUiRemote(),
      shared: { ...FEDERATION_SHARED_REACT },
    }),
    federationReactProxyFixPlugin(),
    publicHubCacheBustEntryPlugin(),
    react(),
  ],
  resolve: {
    alias: {
      ...reactResolveAliases(__dirname),
      "lucide-react": path.resolve(__dirname, "node_modules/lucide-react"),
      // Fora do remote `@delpi/plugin-ui` — evita HelpTooltip/createPortal no /sign.
      "@delpi/signature-kit": path.resolve(PLUGIN_UI_SRC, "components/signature/index.ts"),
      "@delpi/tv-dashboard-presentation": path.resolve(
        __dirname,
        "../tv-dashboard-presentation/src/index.ts",
      ),
      "@delpi/transformometro-meeting-minutes-presentation": path.resolve(
        __dirname,
        "../transformometro-meeting-minutes-presentation/src/index.ts",
      ),
      "@delpi/cipa-meeting-minutes-presentation": path.resolve(
        __dirname,
        "../cipa-meeting-minutes-presentation/src/index.ts",
      ),
    },
    dedupe: ["react", "react-dom", "lucide-react"],
  },
  base: "/p/",
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
