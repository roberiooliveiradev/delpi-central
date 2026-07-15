import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";
import { federationReactProxyFixPlugin } from "../vite/federationReactProxyFix";

import {
  FEDERATION_SHARED_REACT,
  pluginUiRemote,
  reactResolveAliases,
} from "../vite/federation.shared";

/**
 * Em desenvolvimento, CSS do kit vem do source local para o standalone Vite
 * funcionar sem depender do remoteEntry gerado só no build do plugin-ui.
 * Em production build, o remote MF continua canônico.
 */
export default defineConfig(({ mode }) => ({
  plugins: [
    federation({
      name: "guias-procedimentos",
      filename: "remoteEntry.js",
      remotes: pluginUiRemote(),
      exposes: {
        "./App": "./src/bootstrap.tsx",
      },
      shared: { ...FEDERATION_SHARED_REACT },
    }),
    federationReactProxyFixPlugin(),
    react(),
  ],
  resolve: {
    alias: {
      ...reactResolveAliases(__dirname),
      ...(mode === "development"
        ? {
            "@delpi/plugin-ui/styles": path.resolve(
              __dirname,
              "../plugin-ui/src/styles.css",
            ),
          }
        : {}),
    },
    dedupe: ["react", "react-dom"],
  },
  base: "/apps/guias-procedimentos/",
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
}));
