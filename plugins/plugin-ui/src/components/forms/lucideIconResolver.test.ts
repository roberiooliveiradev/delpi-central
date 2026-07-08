import { describe, expect, it } from "vitest";
import {
  isLucideIconName,
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
});
