// Bundles the canonical auto-layout pipeline (plugins/bpmn-editor/
// src/layout/nodeEntry.ts) into a single CJS file executed by `node`
// inside the transformometro-api container. The DOM polyfill banner
// provides DOMParser/XMLSerializer before any module code runs.
import { build } from "esbuild";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const layoutSrc =
  process.env.LAYOUT_SRC ||
  path.resolve(here, "../../../plugins/bpmn-editor/src/layout");

await build({
  entryPoints: [path.join(layoutSrc, "nodeEntry.ts")],
  outfile: path.join(here, "out/organize.cjs"),
  bundle: true,
  platform: "node",
  format: "cjs",
  target: "node18",
  nodePaths: [path.join(here, "node_modules")],
  banner: {
    js: 'const {DOMParser,XMLSerializer}=require("@xmldom/xmldom");globalThis.DOMParser=DOMParser;globalThis.XMLSerializer=XMLSerializer;',
  },
  logLevel: "info",
});

console.log("bundle →", path.join(here, "out/organize.cjs"));
