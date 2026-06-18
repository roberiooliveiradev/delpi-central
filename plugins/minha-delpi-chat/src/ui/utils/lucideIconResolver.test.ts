import { describe, expect, it } from "vitest";

import { isLucideIconName, resolveLucideIcon, toKebabCase } from "./lucideIconResolver";

describe("lucideIconResolver", () => {
  it("resolve ícones Lucide em kebab-case", () => {
    expect(resolveLucideIcon("book-open")).not.toBeNull();
    expect(isLucideIconName("book-open")).toBe(true);
  });

  it("converte PascalCase para kebab-case", () => {
    expect(toKebabCase("BookOpen")).toBe("book-open");
  });

  it("retorna null para ícone inválido", () => {
    expect(resolveLucideIcon("icone-invalido-xyz")).toBeNull();
  });
});
