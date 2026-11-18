import { mkdirSync, rmSync, copyFileSync } from "node:fs";
import nodePath from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";

const root = new URL("../", import.meta.url);
const path = (name) => fileURLToPath(new URL(name, root));
const controls = path("../plugin-ui/src/native-controls");
/* `x.css?inline` retorna o CSS processado (com @import resolvido) como
 * texto — mesmo contrato do Vite para injeção em shadow DOM. */
const cssInlinePlugin = {
  name: "css-inline",
  setup(api) {
    api.onResolve({ filter: /\.css\?inline$/ }, args => ({
      path: nodePath.resolve(args.resolveDir, args.path.slice(0, -"?inline".length)),
      namespace: "css-inline",
    }));
    api.onLoad({ filter: /.*/, namespace: "css-inline" }, async args => {
      const result = await build({
        ...shared,
        entryPoints: [args.path],
        write: false,
        outdir: "out",
      });
      const css = result.outputFiles.find(file => file.path.endsWith(".css"))?.text ?? "";
      return { contents: `export default ${JSON.stringify(css)};`, loader: "js" };
    });
  },
};

const shared = {
  bundle: true,
  minify: true,
  target: "es2022",
  plugins: [cssInlinePlugin],
  alias: {
    "@delpi/plugin-ui/native-controls": controls + ".ts",
    "@delpi/plugin-ui/native-controls.css": controls + ".css",
  },
  nodePaths: [path("node_modules")],
  tsconfigRaw: { compilerOptions: { jsx: "react-jsx" } },
  define: { "process.env.NODE_ENV": '"production"' },
};

const buildCss = (source, outfile) => build({
  ...shared,
  stdin: {
    contents: `@import "@delpi/plugin-ui/native-controls.css";\n@import "./${source}";`,
    loader: "css",
    resolveDir: path("."),
  },
  outfile: path(outfile),
});

if (process.argv.includes("--assets")) {
  mkdirSync(path("dist/ui"), { recursive: true });
  copyFileSync(path("dist/ui-types/delpi-line-balance-studio/src/ui/studio.d.ts"), path("dist/ui/studio.d.ts"));
  rmSync(path("dist/ui-types"), { recursive: true, force: true });
  await build({ ...shared, entryPoints: [path("src/ui/studio.tsx")], format: "esm", outfile: path("dist/ui/studio.js") });
  /* studio.css já importa native-controls.css — bundle direto, sem wrapper. */
  await build({ ...shared, entryPoints: [path("src/ui/studio.css")], outfile: path("dist/ui/studio.css") });
} else {
  const output = path("preview-dist/");
  rmSync(output, { recursive: true, force: true });
  mkdirSync(output, { recursive: true });
  copyFileSync(path("preview/index.html"), path("preview-dist/index.html"));
  copyFileSync(path("dist/ui/studio.css"), path("preview-dist/studio.css"));
  await buildCss("preview/preview.css", "preview-dist/preview.css");
  await build({
    ...shared,
    entryPoints: [path("preview/demo.tsx")],
    format: "esm",
    outfile: path("preview-dist/demo.js"),
  });
}
