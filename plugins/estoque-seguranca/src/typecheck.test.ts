import { execSync } from "node:child_process";
import { existsSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const pluginRoot = process.cwd();
const probePath = join(pluginRoot, "src", "__typecheck_probe__.ts");

function runTypecheck(): { status: number; output: string } {
  try {
    const output = execSync("npm run typecheck", {
      cwd: pluginRoot,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
    });
    return { status: 0, output };
  } catch (error) {
    const execError = error as { status?: number; stdout?: string; stderr?: string };
    return {
      status: execError.status ?? 1,
      output: `${execError.stdout ?? ""}${execError.stderr ?? ""}`,
    };
  }
}

describe("typecheck", () => {
  it("passa no código atual do plugin", () => {
    const result = runTypecheck();
    expect(result.status, result.output).toBe(0);
  });

  it("não atravessa sources de plugin-ui ou vite do monorepo", () => {
    const result = runTypecheck();
    expect(result.output).not.toMatch(/plugins\/plugin-ui\//);
    expect(result.output).not.toMatch(/plugins\/vite\//);
    expect(result.output).not.toMatch(/\.\.\/plugin-ui\//);
  });

  it("detecta erro de tipo no código do plugin", () => {
    writeFileSync(probePath, "const broken: number = 'texto';\nexport {};\n");

    try {
      const result = runTypecheck();
      expect(result.status).not.toBe(0);
      expect(result.output).toMatch(/__typecheck_probe__\.ts/);
      expect(result.output).toMatch(/error TS/);
    } finally {
      if (existsSync(probePath)) {
        rmSync(probePath);
      }
    }
  });
});
