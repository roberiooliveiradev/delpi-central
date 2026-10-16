/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";
import { federationReactProxyFixPlugin } from "../vite/federationReactProxyFix";

import {
  FEDERATION_SHARED_REACT,
  pluginUiRemote,
  pluginUiTestAliases,
  reactResolveAliases,
} from "../vite/federation.shared";

export default defineConfig(({ mode }) => {
  const isVitest = mode === "test" || Boolean(process.env.VITEST);

  return {
    plugins: [
      // Sob vitest o remote `@delpi/plugin-ui` é substituído por aliases de
      // source — o plugin federation reescreveria o import para o remoteEntry
      // (URL do gateway) e quebraria todo teste que toca o kit.
      ...(isVitest
        ? []
        : [
            federation({
              name: "production-control",
              filename: "remoteEntry.js",
              remotes: pluginUiRemote(),
              exposes: {
                "./App": "./src/bootstrap.tsx",
              },
              shared: { ...FEDERATION_SHARED_REACT },
            }),
            federationReactProxyFixPlugin(),
          ]),
      react(),
    ],
    resolve: {
      alias: [
        ...(isVitest ? pluginUiTestAliases(__dirname) : []),
        ...Object.entries(reactResolveAliases(__dirname)).map(([find, replacement]) => ({
          find,
          replacement,
        })),
      ],
      dedupe: ["react", "react-dom"],
    },
    base: "/apps/production-control/",
    build: {
      target: "esnext",
      modulePreload: false,
      cssCodeSplit: false,
    },
    test: {
      environment: "node",
      include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
      alias: pluginUiTestAliases(__dirname),
    },
  };
});
