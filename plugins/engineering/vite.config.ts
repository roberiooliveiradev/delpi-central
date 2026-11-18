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
              name: "engineering",
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
        {
          find: /^@delpi\/line-balance-studio\/ui$/,
          replacement: path.resolve(__dirname, "../delpi-line-balance-studio/src/ui/studio.tsx"),
        },
        {
          find: /^@delpi\/plugin-ui\/native-controls\.css$/,
          replacement: path.resolve(__dirname, "../plugin-ui/src/native-controls.css"),
        },
        {
          find: /^@delpi\/plugin-ui\/workspace-controls$/,
          replacement: path.resolve(__dirname, "../plugin-ui/src/workspace-controls.ts"),
        },
        {
          find: /^@delpi\/plugin-ui\/workspace-controls\.css$/,
          replacement: path.resolve(__dirname, "../plugin-ui/src/workspace-controls.css"),
        },
        {
          find: /^@delpi\/line-balance-studio$/,
          replacement: path.resolve(__dirname, "../delpi-line-balance-studio/src/index.ts"),
        },
        ...(isVitest ? pluginUiTestAliases(__dirname) : []),
        ...Object.entries(reactResolveAliases(__dirname)).map(([find, replacement]) => ({
          find,
          replacement,
        })),
      ],
      dedupe: ["react", "react-dom"],
    },
    base: "/apps/engineering/",
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
