import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Docker do MFE não COPY plugin-ui — imports relativos quebram o vite build.
 * CSS vem do remote `@delpi/plugin-ui/styles` via preparePluginUiRemote.
 */
describe("tv-dashboard-presentation sem import relativo de plugin-ui", () => {
  const srcRoot = dirname(fileURLToPath(import.meta.url));

  function collectTsFiles(dir: string): string[] {
    const out: string[] = [];
    for (const name of readdirSync(dir)) {
      const full = join(dir, name);
      if (statSync(full).isDirectory()) {
        out.push(...collectTsFiles(full));
        continue;
      }
      if (/\.(tsx?|jsx?)$/.test(name) && !name.endsWith(".test.ts") && !name.endsWith(".test.tsx")) {
        out.push(full);
      }
    }
    return out;
  }

  it("não importa CSS/fonte de ../../plugin-ui/", () => {
    const offenders: string[] = [];
    const pattern = /from\s+["']\.\.\/\.\.\/plugin-ui\/|import\s+["']\.\.\/\.\.\/plugin-ui\//;
    for (const file of collectTsFiles(srcRoot)) {
      const text = readFileSync(file, "utf8");
      if (pattern.test(text)) {
        offenders.push(file.replace(srcRoot + "/", ""));
      }
    }
    expect(offenders).toEqual([]);
  });
});
