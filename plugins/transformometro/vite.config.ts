import path from "node:path";

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";
import { federationReactProxyFixPlugin } from "../vite/federationReactProxyFix";

import {
  FEDERATION_SHARED_WITH_DIAGRAM,
  pluginUiRemote,
  reactResolveAliases,
} from "../vite/federation.shared";

export default defineConfig({
  plugins: [
    federation({
      name: "transformometro",
      filename: "remoteEntry.js",
      remotes: pluginUiRemote(),
      exposes: {
        "./App": "./src/bootstrap.tsx",
      },
      shared: { ...FEDERATION_SHARED_WITH_DIAGRAM } as never,
    }),
    federationReactProxyFixPlugin(),
    react(),
  ],
  resolve: {
    alias: {
      ...reactResolveAliases(__dirname),
      "@xyflow/react": path.resolve(__dirname, "node_modules/@xyflow/react"),
      "@delpi/transformometro-meeting-minutes-presentation": path.resolve(
        __dirname,
        "../transformometro-meeting-minutes-presentation/src/index.ts",
      ),
    },
    dedupe: ["react", "react-dom", "@xyflow/react"],
  },
  base: "/apps/transformometro/",
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
