import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

describe("AppShell / App route permission gates", () => {
  it("TopBar só mostra fila quando canAccessWorkQueue", () => {
    const shell = read("components/AppShell.tsx");
    expect(shell).toMatch(/canAccessWorkQueue/);
    expect(shell).toMatch(/showWorkQueue/);
    expect(shell).toMatch(/canCreateAnyRequest/);
    expect(shell).not.toMatch(/canCreate\s*=/);
  });

  it("App bloqueia deep link de fila, nova e admin sem permissão", () => {
    const app = read("App.tsx");
    expect(app).toMatch(/canAccessWorkQueue/);
    expect(app).toMatch(/canCreateAnyRequest/);
    expect(app).toMatch(/ForbiddenRoute/);
    expect(app).toMatch(/access\.canManage/);
  });

  it("Nova solicitação filtra cards por canCreateRequestType", () => {
    const page = read("pages/NewRequestPage.tsx");
    expect(page).toMatch(/canCreateRequestType/);
    expect(page).toMatch(/creatableTypes/);
    expect(page).toMatch(/permission_prefix/);
  });
});
