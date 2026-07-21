import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Home Power BI: ações da antiga Página Inicial no menu de contexto do card.
 */
describe("playlist home context menu contract", () => {
  const base = dirname(fileURLToPath(import.meta.url));
  const menu = readFileSync(join(base, "PlaylistHomeContextMenu.tsx"), "utf8");
  const page = readFileSync(join(base, "../pages/PlaylistsPage.tsx"), "utf8");
  const app = readFileSync(join(base, "../App.tsx"), "utf8");
  const tips = readFileSync(join(base, "../content/helpTooltips.ts"), "utf8");

  it("expõe ações da antiga Página Inicial", () => {
    for (const label of [
      "C.open",
      "C.duplicate",
      "C.preview",
      "C.share",
      "C.copyLink",
      "C.qr",
      "C.regenerateToken",
      "C.tvOn",
      "C.tvOff",
      "C.delete",
    ]) {
      expect(menu).toContain(label);
    }
  });

  it("home abre o menu no botão direito do card (sem Abrir/Duplicar no rodapé)", () => {
    expect(page).toMatch(/onContextMenu/);
    expect(page).toContain("PlaylistHomeContextMenu");
    expect(page).not.toContain("td-home__card-actions");
  });

  it("App liga prévia e editores a partir da home", () => {
    expect(app).toMatch(/onPreview=\{\(id\) =>/);
    expect(app).toMatch(/onShare=\{\(id\) => navigate\(playlistSharePath/);
  });

  it("textos do menu estão no catálogo de tooltips", () => {
    expect(tips).toMatch(/homeContextMenu:\s*\{/);
    expect(tips).toMatch(/open:\s*"Abrir"/);
    expect(tips).toMatch(/regenerateToken:\s*"Novo link"/);
  });
});
