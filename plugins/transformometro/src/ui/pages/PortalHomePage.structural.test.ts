import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "PortalHomePage.tsx"), "utf8");

describe("PortalHomePage shared chrome", () => {
  it("compõe hero, eventos, busca, recentes e cards com estrela", () => {
    expect(source).toMatch(/PageHeader/);
    expect(source).toMatch(/highlights=/);
    expect(source).toMatch(/EventsSection/);
    expect(source).toMatch(/CatalogSearchBar/);
    expect(source).toMatch(/RecentAccessStrip/);
    expect(source).toMatch(/SectionRouteCard/);
    expect(source).toMatch(/onPinClick/);
    expect(source).not.toMatch(/label="Favoritos"/);
    expect(source).not.toMatch(/HubChipRow/);
    expect(source).not.toMatch(/from ["']@delpi\/commercial/);
  });
});
