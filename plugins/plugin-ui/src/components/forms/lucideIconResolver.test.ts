import { describe, expect, it } from "vitest";
import { countLucideIconPtLabels } from "./lucideIconPtLabels";
import {
  buildLucideIconOptions,
  countLucideCatalogSize,
  DECK_QUICK_LUCIDE_ICON_NAMES,
  groupLucideIconsBySection,
  isLucideIconName,
  isPascalCaseLucideExport,
  listLucideIconNames,
  lucideIconPtLabel,
  resolveLucideIcon,
  resolveLucideIconOrFallback,
  toKebabCase,
  toPascalCaseFromKebab,
} from "./lucideIconResolver";

describe("lucideIconResolver", () => {
  it("converte kebab ↔ pascal", () => {
    expect(toPascalCaseFromKebab("check-circle-2")).toBe("CheckCircle2");
    expect(toKebabCase("CheckCircle2")).toBe("check-circle-2");
  });

  it("resolve nomes kebab e PascalCase", () => {
    expect(resolveLucideIcon("eye")).not.toBeNull();
    expect(resolveLucideIcon("Eye")).not.toBeNull();
    expect(isLucideIconName("heart")).toBe(true);
    expect(isLucideIconName("not-a-real-icon-xyz")).toBe(false);
  });

  it("resolve nomes PascalCase compostos (TV/KPI)", () => {
    expect(resolveLucideIcon("TrendingUp")).not.toBeNull();
    expect(resolveLucideIcon("AlertTriangle")).not.toBeNull();
    expect(resolveLucideIcon("CheckCircle2")).not.toBeNull();
  });

  it("resolveLucideIconOrFallback usa fallback para nome inválido", () => {
    const icon = resolveLucideIconOrFallback("not-a-real-icon-xyz", "Star");
    expect(icon).toBe(resolveLucideIconOrFallback("Star", "Star"));
  });

  it("buildLucideIconOptions monta rótulos PT", () => {
    const options = buildLucideIconOptions(DECK_QUICK_LUCIDE_ICON_NAMES);
    expect(options.length).toBe(DECK_QUICK_LUCIDE_ICON_NAMES.length);
    expect(options[0]?.name).toBe("Star");
    expect(options[0]?.label).toBe("Estrela");
  });

  it("catálogo pt-BR cobre todos os kebabs do Lucide", () => {
    const kebabs = new Set(listLucideIconNames().map(toKebabCase));
    expect(countLucideIconPtLabels()).toBe(kebabs.size);
    expect(lucideIconPtLabel("Eye")).toBe("Olho");
    expect(lucideIconPtLabel("trending-up")).toBe("Tendência");
    expect(lucideIconPtLabel("FolderOpen")).not.toBe("folder-open");
    for (const kebab of kebabs) {
      const label = lucideIconPtLabel(kebab);
      expect(label.length).toBeGreaterThan(0);
      expect(label).not.toBe(kebab);
    }
  });

  it("exclui aliases *Icon da lista canônica", () => {
    expect(isPascalCaseLucideExport("Eye")).toBe(true);
    expect(isPascalCaseLucideExport("EyeIcon")).toBe(false);
    const names = listLucideIconNames();
    expect(names).toContain("Eye");
    expect(names).not.toContain("EyeIcon");
    expect(countLucideCatalogSize()).toBeGreaterThan(1000);
  });

  it("agrupa seções sem busca", () => {
    const sections = groupLucideIconsBySection({ curatedOnly: false, query: "" });
    expect(sections.length).toBeGreaterThan(5);
    expect(sections.some((section) => section.id === "featured")).toBe(true);
    expect(sections.every((section) => section.icons.length > 0)).toBe(true);
  });

  it("busca no catálogo Lucide completo", () => {
    const sections = groupLucideIconsBySection({
      curatedOnly: false,
      query: "plane",
      maxResults: 80,
    });
    const flat = sections.flatMap((section) => section.icons);
    expect(flat.length).toBeGreaterThan(0);
    expect(flat).toContain("Plane");
  });

  it("busca por alias em português", () => {
    const sections = groupLucideIconsBySection({
      curatedOnly: false,
      query: "indicador",
      maxResults: 80,
    });
    const flat = sections.flatMap((section) => section.icons);
    expect(flat).toContain("Gauge");
  });

  it("exclui prefixo Lucide* da lista", () => {
    expect(isPascalCaseLucideExport("LucideEye")).toBe(false);
    expect(listLucideIconNames()).not.toContain("LucideEye");
  });
});
