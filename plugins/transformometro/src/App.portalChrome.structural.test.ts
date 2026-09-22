import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = dirname(fileURLToPath(import.meta.url));

describe("Portal topbar global chrome", () => {
  it("App monta PortalTopBar uma vez para todas as rotas", () => {
    const app = readFileSync(join(root, "App.tsx"), "utf8");
    expect(app).toMatch(/tm-portal-frame/);
    expect(app).toMatch(/<PortalTopBar currentPath=\{pathname\} onNavigate=\{onNavigate\} \/>/);
    expect(app.match(/<PortalTopBar[\s\S]*?\/>/g)?.length).toBe(1);
  });

  it("PageHeader não remonta a TopBar do portal", () => {
    const header = readFileSync(join(root, "components/PageHeader.tsx"), "utf8");
    expect(header).not.toMatch(/PortalTopBar/);
  });

  it("salas e perfil não duplicam PortalTopBar", () => {
    const rooms = readFileSync(join(root, "ui/pages/InteractionRoomsPage.tsx"), "utf8");
    const person = readFileSync(join(root, "ui/pages/PersonDirectoryPage.tsx"), "utf8");
    expect(rooms).not.toMatch(/PortalTopBar/);
    expect(person).not.toMatch(/PortalTopBar/);
  });

  it("PortalTopBar passa ícones lucide nos itens (padrão portal Comercial)", () => {
    const nav = readFileSync(join(root, "components/TransformometroNav.tsx"), "utf8");
    expect(nav).toMatch(/PORTAL_TOPBAR_ICONS/);
    expect(nav).toMatch(/icon: PORTAL_TOPBAR_ICONS\[item\.id\]/);
    expect(nav).toMatch(/from "lucide-react"/);
    expect(nav).toMatch(/Home/);
    expect(nav).toMatch(/MessagesSquare/);
    expect(nav).toMatch(/FolderKanban/);
    expect(nav).toMatch(/BookOpen/);
  });
});
