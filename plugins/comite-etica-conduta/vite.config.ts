/// <reference types="vitest/config" />
import path from "node:path";
import { fileURLToPath } from "node:url";
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

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
  const isVitest = mode === "test" || Boolean(process.env.VITEST);

  return {
    plugins: [
      ...(isVitest
        ? []
        : [
            federation({
              name: "comite-etica-conduta",
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
        ...(isVitest
          ? [
              {
                find: "recharts",
                replacement: path.resolve(__dirname, "node_modules/recharts"),
              },
            ]
          : []),
        ...Object.entries(reactResolveAliases(__dirname)).map(([find, replacement]) => ({
          find,
          replacement,
        })),
      ],
      dedupe: ["react", "react-dom"],
    },
    base: "/apps/comite-etica-conduta/",
    build: {
      target: "esnext",
      modulePreload: false,
      cssCodeSplit: false,
    },
    test: {
      environment: "node",
      include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
      alias: [
        ...pluginUiTestAliases(__dirname),
        {
          find: "recharts",
          replacement: path.resolve(__dirname, "node_modules/recharts"),
        },
      ],
    },
  };
});
