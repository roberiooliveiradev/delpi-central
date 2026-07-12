import { describe, expect, it } from "vitest";
import {
  countLucideCatalogSize,
  groupLucideIconsBySection,
  isLucideIconName,
  isPascalCaseLucideExport,
  listLucideIconNames,
  resolveLucideIcon,
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
