import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("Home launcher visual pattern", () => {
  it("usa SectionRouteCard + CatalogSearchBar (padrão Comercial)", () => {
    const page = readFileSync(join(dir, "../../pages/HomePage.tsx"), "utf8");
    expect(page).toMatch(/SuppliesSectionRouteCard/);
    expect(page).toMatch(/SuppliesCatalogSearchBar/);
    expect(page).toMatch(/SuppliesHubChipRow/);
    expect(page).toMatch(/SuppliesSectionCard/);
    expect(page).toMatch(/SuppliesLoadingCard/);
    expect(page).toMatch(/sp-home-sections-grid/);
    expect(page).not.toMatch(/sp-home__fav/);
  });

  it("usa SectionHintLabel nos blocos do Início (sem LabelWithHelp/? solto)", () => {
    const page = readFileSync(join(dir, "../../pages/HomePage.tsx"), "utf8");
    const shell = readFileSync(join(dir, "../../app/PluginShell.tsx"), "utf8");
    expect(page).toMatch(/SP_HELP\.home\.attention/);
    expect(page).toMatch(/SP_HELP\.home\.paths/);
    expect(page).toMatch(/SP_HELP\.home\.search/);
    expect(page).toMatch(/SP_HELP\.home\.favorites/);
    expect(page).toMatch(/SP_HELP\.home\.recents/);
    expect(page).toMatch(/SECTION_HINTS/);
    expect(page).toMatch(/SuppliesSectionHintLabel/);
    expect(page).not.toMatch(/LabelWithHelp/);
    expect(page).not.toMatch(/HelpTooltip/);
    expect(page).toMatch(/toggleHomeFavorite/);
    expect(page).toMatch(/onPinClick/);
    expect(shell).toMatch(/SP_HELP\.home\.heroAttention/);
    expect(shell).toMatch(/SP_HELP\.home\.scopeBadge/);
    expect(shell).toMatch(/SuppliesTitleWithHelp|SuppliesSectionHintLabel/);
    expect(shell).not.toMatch(/HelpTooltip/);
  });

  it("hero de saudação fica no PluginShell, não no título Início local", () => {
    const shell = readFileSync(join(dir, "../../app/PluginShell.tsx"), "utf8");
    const page = readFileSync(join(dir, "../../pages/HomePage.tsx"), "utf8");
    expect(shell).toMatch(/SuppliesPageHero/);
    expect(shell).toMatch(/greetingForNow/);
    expect(page).not.toMatch(/HUB_CONTENT\.home\.title/);
  });
});
