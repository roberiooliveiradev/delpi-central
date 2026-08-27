/// <reference types="vitest/config" />
import path from "node:path";
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
      ...(isVitest
        ? []
        : [
            federation({
              name: "cipa",
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
        {
          find: "@delpi/cipa-meeting-minutes-presentation",
          replacement: path.resolve(
            __dirname,
            "../cipa-meeting-minutes-presentation/src/index.ts",
          ),
        },
      ],
      dedupe: ["react", "react-dom"],
    },
    base: "/apps/cipa/",
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
