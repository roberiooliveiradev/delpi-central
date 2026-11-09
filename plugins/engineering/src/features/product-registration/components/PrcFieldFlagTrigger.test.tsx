import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import type { PrcAttendanceFlag } from "../api/productRegistrationApi";
import {
  findOpenFieldFlag,
  findResolvedFieldFlags,
  resolveFlagVisualState,
} from "./PrcFieldFlagTrigger";
import { PRC_FIELD_HELP, PRC_FLAG_ACTION_HELP, prcFieldHelp } from "../prcCopy";

const here = dirname(fileURLToPath(import.meta.url));

function flag(
  partial: Partial<PrcAttendanceFlag> & Pick<PrcAttendanceFlag, "id" | "status">,
): PrcAttendanceFlag {
  return {
    requestId: "r",
    title: partial.title || "t",
    description: "d",
    subject: "FIELD",
    targetPath: "description",
    version: 1,
    createdAt: "2026-01-01T00:00:00Z",
    createdBy: { subject: "u" },
    updatedAt: "2026-01-01T00:00:00Z",
    updatedBy: {},
    ...partial,
  };
}

describe("PrcFieldFlagTrigger — PRC-REF-018", () => {
  it("módulo usa só Flag (sem Plus) e CSS tem azul/vermelho/verde", () => {
    const src = readFileSync(join(here, "PrcFieldFlagTrigger.tsx"), "utf8");
    expect(src).toMatch(/import\s*\{\s*Flag\s*\}\s*from\s*"lucide-react"/);
    expect(src).not.toMatch(/import\s*\{[^}]*\bPlus\b/);
    const css = readFileSync(join(here, "../prc.css"), "utf8");
    expect(css).toMatch(/field-flag--add[\s\S]*#2563eb/);
    expect(css).toMatch(/field-flag--open[\s\S]*#b42318/);
    expect(css).toMatch(/field-flag--resolved[\s\S]*#1a7f37/);
  });

  it("azul sem acompanhamento; vermelho OPEN; verde RESOLVED; OPEN prevalece", () => {
    expect(resolveFlagVisualState(undefined, [])).toBe("add");
    const open = flag({ id: "o", status: "OPEN" });
    const resolved = [flag({ id: "r1", status: "RESOLVED" })];
    expect(resolveFlagVisualState(open, resolved)).toBe("open");
    expect(resolveFlagVisualState(undefined, resolved)).toBe("resolved");
  });

  it("findResolvedFieldFlags retorna múltiplas ordenáveis", () => {
    const flags = [
      flag({
        id: "a",
        status: "RESOLVED",
        resolvedAt: "2026-01-01T00:00:00Z",
      }),
      flag({
        id: "b",
        status: "RESOLVED",
        resolvedAt: "2026-02-01T00:00:00Z",
      }),
      flag({ id: "c", status: "OPEN" }),
      flag({
        id: "d",
        status: "RESOLVED",
        targetPath: "group",
        resolvedAt: "2026-03-01T00:00:00Z",
      }),
    ];
    expect(findOpenFieldFlag(flags, "description")?.id).toBe("c");
    const resolved = findResolvedFieldFlags(flags, "description");
    expect(resolved.map((f) => f.id)).toEqual(["b", "a"]);
  });
});

describe("prcFieldHelp — catálogo central REF-018", () => {
  it("nunca devolve texto legado B1_/A5_", () => {
    expect(prcFieldHelp("group")).toBe(PRC_FIELD_HELP.group);
    expect(
      prcFieldHelp("group", "B1_GRUPO — legado 'grupo'"),
    ).toBe(PRC_FIELD_HELP.group);
    expect(prcFieldHelp("unknown", "B1_FOO legado")).toBeUndefined();
    expect(PRC_FLAG_ACTION_HELP.resolve).toMatch(/Não aprova/);
  });

  it("cobre campos obrigatórios do catálogo", () => {
    for (const key of [
      "officialProductCode",
      "description",
      "group",
      "productKind",
      "unit",
      "defaultWarehouse",
      "accountingAccount",
      "thirdPartyProduct",
      "customerReference",
    ]) {
      expect(PRC_FIELD_HELP[key], key).toBeTruthy();
      expect(PRC_FIELD_HELP[key]).not.toMatch(/B1_|A5_|legado/i);
    }
  });
});

describe("PrcFlagModal — REF-018 surface", () => {
  it("tem legenda e ícones Resolver/Reabrir/Remover sem interrogação", () => {
    const src = readFileSync(join(here, "PrcFlagModal.tsx"), "utf8");
    expect(src).toMatch(/engineering-prc__flag-legend/);
    expect(src).toMatch(/Resolver/);
    expect(src).toMatch(/Reabrir/);
    expect(src).toMatch(/Trash2/);
    expect(src).toMatch(/HelpTooltip/);
    expect(src).not.toMatch(/HelpCircle|circle-help/);
    expect(src).not.toMatch(/trigger=\"icon\"/);
    expect(src).toMatch(/PRC_FLAG_ACTION_HELP\.resolve/);
  });
});

describe("PrcAttendanceFlagsSummary — REF-018", () => {
  it("remove chips de resolvidas e botão Ocultar/Ver resolvidas", () => {
    const src = readFileSync(join(here, "PrcAttendanceFlags.tsx"), "utf8");
    expect(src).toMatch(/Acompanhamento técnico/);
    expect(src).toMatch(/Legenda das bandeiras/);
    expect(src).not.toMatch(/Ocultar resolvidas|Ver resolvidas/);
    expect(src).not.toMatch(/flags-chip--resolved/);
  });
});
