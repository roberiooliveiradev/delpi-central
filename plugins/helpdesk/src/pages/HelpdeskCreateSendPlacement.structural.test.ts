import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = dirname(fileURLToPath(import.meta.url));
const page = readFileSync(join(root, "HelpdeskPage.tsx"), "utf8");
const css = readFileSync(join(root, "../index.css"), "utf8");

describe("HELPDESK-P0 Enviar button placement", () => {
  it("single Enviar button lives inside the file-actions row, after the attach control", () => {
    expect(page.match(/helpdesk-create-send/g)).toHaveLength(1);
    const actionsStart = page.indexOf('className="helpdesk-create-files__actions"');
    const actionsEnd = page.indexOf("helpdesk-create-files__hint");
    expect(actionsStart).toBeGreaterThan(0);
    expect(actionsEnd).toBeGreaterThan(actionsStart);
    const block = page.slice(actionsStart, actionsEnd);
    expect(block).toContain("Inserir imagem no texto");
    expect(block).toContain("Anexar arquivo ao chamado");
    expect(block).toContain("helpdesk-create-send");
    expect(block.indexOf("Anexar arquivo ao chamado")).toBeLessThan(
      block.indexOf("helpdesk-create-send"),
    );
    expect(block).toContain('type="submit"');
    expect(block).toContain("Enviando…");
  });

  it("aside no longer carries the removed actions container", () => {
    expect(page).not.toContain("helpdesk-create-layout__aside-actions");
    expect(css).not.toContain("helpdesk-create-layout__aside-actions");
  });

  it("send button is compact and right-aligned within the actions row", () => {
    const ruleStart = css.indexOf(".helpdesk-create-send {");
    expect(ruleStart).toBeGreaterThan(0);
    const rule = css.slice(ruleStart, css.indexOf("}", ruleStart));
    expect(rule).toContain("margin-inline-start: auto");
    expect(rule).not.toContain("flex: 1 1 auto");
  });
});
