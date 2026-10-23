import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));
const srcDir = join(dir, "../..");

// HOME-ATTENTION.P3: the Home must not trigger the heavy operational
// composition (SC summary, late POs, late deliveries, safety stock). No
// canonical user-task source exists, so the Atenção section was removed —
// these guards keep it from coming back without a proven source.
describe("Home sem seção Atenção (P3)", () => {
  it("client e store de atenção não existem mais", () => {
    expect(existsSync(join(srcDir, "api/homeAttention.ts"))).toBe(false);
    expect(existsSync(join(srcDir, "app/homeAttentionStore.ts"))).toBe(false);
  });

  it("HomePage não consulta nem renderiza atenção", () => {
    const page = readFileSync(join(srcDir, "pages/HomePage.tsx"), "utf8");
    expect(page).not.toMatch(/homeAttention/);
    expect(page).not.toMatch(/SuppliesEventsSection|SuppliesLoadingCard|SuppliesStateBanner/);
    expect(page).not.toMatch(/attentionTitle|attentionLoading|attentionError|attentionQueueOk/);
    expect(page).not.toMatch(/sp-home-attention|sp-home-queue-ok/);
  });

  it("PluginShell não carrega atenção nem destaque derivado", () => {
    const shell = readFileSync(join(srcDir, "app/PluginShell.tsx"), "utf8");
    expect(shell).not.toMatch(/homeAttention/);
    expect(shell).not.toMatch(/attentionValue|attentionClear|heroAttention/);
  });

  it("conteúdo da Home não expõe chaves de atenção", () => {
    const catalog = readFileSync(
      join(srcDir, "content/pluginRouteCatalog.ts"),
      "utf8",
    );
    expect(catalog).not.toMatch(/attentionTitle|attentionSubtitle|attentionQueueOk|attentionPartial/);
  });

  it("nenhuma chamada a /home/attention permanece no MFE", () => {
    const page = readFileSync(join(srcDir, "pages/HomePage.tsx"), "utf8");
    const shell = readFileSync(join(srcDir, "app/PluginShell.tsx"), "utf8");
    expect(page + shell).not.toMatch(/home\/attention/);
  });

  it("demais blocos da Home permanecem (busca, recentes, caminhos)", () => {
    const page = readFileSync(join(srcDir, "pages/HomePage.tsx"), "utf8");
    expect(page).toMatch(/SuppliesCatalogSearchBar/);
    expect(page).toMatch(/SuppliesRecentAccessStrip/);
    expect(page).toMatch(/SuppliesSectionRouteCard/);
    expect(page).toMatch(/navigatePluginView/);
  });
});
