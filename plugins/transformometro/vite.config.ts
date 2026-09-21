/// <reference types="vitest/config" />
import path from "node:path";

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";
import { federationReactProxyFixPlugin } from "../vite/federationReactProxyFix";

import {
  FEDERATION_SHARED_WITH_DIAGRAM,
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
              name: "transformometro",
              filename: "remoteEntry.js",
              remotes: pluginUiRemote(),
              exposes: {
                "./App": "./src/bootstrap.tsx",
              },
              shared: { ...FEDERATION_SHARED_WITH_DIAGRAM } as never,
            }),
            federationReactProxyFixPlugin(),
          ]),
      react(),
    ],
    resolve: {
      alias: [
        ...(isVitest ? pluginUiTestAliases(__dirname) : []),
        ...Object.entries({
          ...reactResolveAliases(__dirname),
          "@xyflow/react": path.resolve(__dirname, "node_modules/@xyflow/react"),
          "@delpi/transformometro-meeting-minutes-presentation": path.resolve(
            __dirname,
            "../transformometro-meeting-minutes-presentation/src/index.ts",
          ),
        }).map(([find, replacement]) => ({
          find,
          replacement,
        })),
      ],
      dedupe: ["react", "react-dom", "@xyflow/react"],
    },
    base: "/apps/transformometro/",
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
