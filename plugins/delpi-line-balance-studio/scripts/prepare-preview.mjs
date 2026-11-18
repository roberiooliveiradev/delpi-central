import { cpSync, mkdirSync, rmSync, copyFileSync } from "node:fs";

const root = new URL("../", import.meta.url);
const path = (name) => new URL(name, root);

copyFileSync(path("src/ui/studio.css"), path("dist/ui/studio.css"));
if (!process.argv.includes("--assets")) {
  const output = path("preview-dist/");
  rmSync(output, { recursive: true, force: true });
  mkdirSync(output, { recursive: true });
  cpSync(path("preview/"), output, { recursive: true });
  cpSync(path("dist/"), path("preview-dist/studio/"), {
    recursive: true,
    filter: (source) => !source.endsWith(".d.ts"),
  });
}
