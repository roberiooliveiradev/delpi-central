import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";
import { federationReactProxyFixPlugin } from "../vite/federationReactProxyFix";
import path from "node:path";

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
            name: "tv-dashboard",
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
        find: "@delpi/tv-dashboard-presentation",
        replacement: path.resolve(__dirname, "../tv-dashboard-presentation/src/index.ts"),
      },
      ...(isVitest ? pluginUiTestAliases(__dirname) : []),
      ...Object.entries(reactResolveAliases(__dirname)).map(([find, replacement]) => ({
        find,
        replacement,
      })),
    ],
    dedupe: ["react", "react-dom"],
  },
  base: "/apps/tv-dashboard/",
  test: {
    environment: "happy-dom",
    alias: pluginUiTestAliases(__dirname),
  },
  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
};
});
