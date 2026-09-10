import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { GLOSSARY_CONTENT } from "../../content/glossaryContent";
import { USER_MANUAL_CONTENT } from "../../content/userManualContent";
import {
  MANUAL_TOOL_TARGETS,
  splitManualTextWithToolLinks,
} from "../../content/userManualToolLinks";

const dir = dirname(fileURLToPath(import.meta.url));

describe("userManual content", () => {
  it("covers P0 manual sections from HELP-AND-ONBOARDING", () => {
    expect(USER_MANUAL_CONTENT.pageTitle).toBe("Manual do usuário");
    const ids = USER_MANUAL_CONTENT.sections.map((section) => section.id);
    expect(ids).toContain("want");
    expect(ids).toContain("faq");
    expect(ids).toContain("glossary");

    const want = USER_MANUAL_CONTENT.sections.find((section) => section.id === "want");
    expect(want?.links?.some((row) => /SC|solicita/i.test(row.want))).toBe(true);
    expect(want?.links?.some((row) => /ESTSEG|segurança/i.test(row.want))).toBe(true);
    expect(want?.links?.some((row) => /filial padrão|densidade/i.test(row.want))).toBe(true);
    expect(want?.links?.some((row) => /OTD|velocímetro/i.test(row.want))).toBe(true);

    const faq = USER_MANUAL_CONTENT.sections.find((section) => section.id === "faq");
    const questions = (faq?.faqs ?? []).map((item) => item.q).join(" ");
    expect(questions).toMatch(/estoque/i);
    expect(questions).toMatch(/OTD/i);
    expect(questions).toMatch(/Visão geral.*OTD|OTD.*Visão geral/i);
    expect(questions).toMatch(/Sheets|indicadores/i);
    expect(questions).toMatch(/403/);
    expect(questions).toMatch(/filial padrão|densidade/i);
    expect(questions).toMatch(/\/profile|Minha DELPI/i);
  });

  it("exposes glossary terms and tool link targets", () => {
    const terms = GLOSSARY_CONTENT.map((entry) => entry.term);
    for (const required of ["OTD", "ESTSEG", "SC", "PC", "CPV", "Giro", "Filial 01", "Filial 02"]) {
      expect(terms).toContain(required);
    }
    expect(MANUAL_TOOL_TARGETS.some((target) => target.label === "Visão geral")).toBe(true);
    expect(MANUAL_TOOL_TARGETS.some((target) => target.viewId === "analytics_otd")).toBe(true);
    expect(MANUAL_TOOL_TARGETS.some((target) => target.viewId === "purchase_requests")).toBe(
      true,
    );
  });

  it("links known tool labels inside manual text", () => {
    const parts = splitManualTextWithToolLinks("Abra Visão geral depois do Início");
    expect(parts.some((part) => part.kind === "link" && part.value === "Visão geral")).toBe(
      true,
    );
    expect(parts.some((part) => part.kind === "link" && part.value === "Início")).toBe(true);
  });

  it("recomposes with kit PageHero/SectionCard (Commercial family)", () => {
    const page = readFileSync(join(dir, "UserManualPage.tsx"), "utf8");
    expect(page).toContain("SuppliesPageHero");
    expect(page).toContain("SuppliesSectionCard");
    expect(page).toContain("SuppliesActionButton");
    expect(page).not.toContain("sp-user-manual__hero");
    expect(page).not.toMatch(/className=\"sp-home__chip\"/);
  });
});
