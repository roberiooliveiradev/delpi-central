import { describe, expect, it } from "vitest";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import { resolveParamSelectOptions } from "./dataParamSchema";
import {
  INPUT_VARIABLE_DEFAULT_FIELD,
  buildVariableDefaultEditorSchema,
  formatEnumOptionsText,
  listSlideInputVariableRefs,
  parseEnumOptionsText,
  parseVariableDefault,
  suggestVariableKey,
  valueSchemaForTypeId,
  valueSchemaTypeId,
  variableKeyIssue,
} from "./inputVariableEditor";

function variable(id: string, key: string): ComunicadoBlock {
  return {
    id,
    type: "input",
    frame: { x: 0, y: 0, w: 10, h: 10 },
    input: { paramKey: "", binding: { kind: "variable", key }, valueSchema: { type: "integer" } },
  } as ComunicadoBlock;
}

const legacy = {
  id: "in-branch",
  type: "input",
  frame: { x: 0, y: 0, w: 10, h: 10 },
  input: { paramKey: "meeting_day", defaultValue: 1 },
} as ComunicadoBlock;

describe("tipo da variável", () => {
  it("data = string + format date (shape de paramSchema)", () => {
    expect(valueSchemaForTypeId("date")).toEqual({ type: "string", format: "date" });
    expect(valueSchemaTypeId({ type: "string", format: "date" })).toBe("date");
    expect(valueSchemaTypeId({ type: "integer" })).toBe("integer");
    expect(valueSchemaTypeId(undefined)).toBe("string");
  });
});

describe("chave da variável", () => {
  it("valida regex e unicidade no slide (ignora o próprio bloco e paramKey legado)", () => {
    const blocks = [variable("a", "meeting_day"), variable("b", "other"), legacy];
    expect(variableKeyIssue("meeting_day", blocks, "a")).toBeNull();
    expect(variableKeyIssue("other", blocks, "a")).toBe("duplicate");
    expect(variableKeyIssue("1bad", blocks, "a")).toBe("invalid");
    expect(variableKeyIssue("input.x", blocks, "a")).toBe("invalid");
    expect(variableKeyIssue("", blocks, "a")).toBe("invalid");
  });

  it("refs do slide: só variáveis únicas; legado e duplicadas ficam de fora", () => {
    expect(listSlideInputVariableRefs([variable("a", "meeting_day"), legacy])).toEqual([
      { key: "meeting_day", label: "meeting_day" },
    ]);
    expect(listSlideInputVariableRefs([variable("a", "dup"), variable("b", "dup")])).toEqual([]);
    expect(listSlideInputVariableRefs(undefined)).toEqual([]);
  });

  it("sugestão evita chaves já usadas", () => {
    expect(suggestVariableKey([])).toBe("variable_1");
    expect(suggestVariableKey([variable("a", "variable_1"), variable("b", "variable_2")])).toBe("variable_3");
  });
});

describe("opções (enum + enumLabels)", () => {
  it("round-trip texto ↔ schema para inteiros", () => {
    const parsed = parseEnumOptionsText("0=Segunda-feira\n1=Terça-feira\n\n2", "integer");
    expect(parsed).toEqual({
      ok: true,
      enum: [0, 1, 2],
      enumLabels: { "0": "Segunda-feira", "1": "Terça-feira" },
    });
    if (!parsed.ok) throw new Error("unreachable");
    expect(formatEnumOptionsText({ type: "integer", enum: parsed.enum, enumLabels: parsed.enumLabels })).toBe(
      "0=Segunda-feira\n1=Terça-feira\n2",
    );
  });

  it("rejeita valor incompatível ou repetido; vazio = sem enum", () => {
    expect(parseEnumOptionsText("0\nabc", "integer")).toEqual({ ok: false, line: 2 });
    expect(parseEnumOptionsText("1.5", "integer")).toEqual({ ok: false, line: 1 });
    expect(parseEnumOptionsText("a\na", "string")).toEqual({ ok: false, line: 2 });
    expect(parseEnumOptionsText("  \n", "string")).toEqual({ ok: true });
  });

  it("enumLabels do campo vence o catálogo por chave", () => {
    const schema = buildVariableDefaultEditorSchema({
      type: "integer",
      enum: [0, 1],
      enumLabels: { "0": "Segunda-feira", "1": "Terça-feira" },
    });
    const field = schema[INPUT_VARIABLE_DEFAULT_FIELD];
    expect(field?.expressionAllowed).toBe(false);
    expect(resolveParamSelectOptions(INPUT_VARIABLE_DEFAULT_FIELD, field!)).toEqual([
      { value: "0", label: "Segunda-feira" },
      { value: "1", label: "Terça-feira" },
    ]);
  });
});

describe("valor padrão", () => {
  it("coage pelo valueSchema; vazio = null", () => {
    expect(parseVariableDefault("2", { type: "integer" })).toBe(2);
    expect(parseVariableDefault("2.7", { type: "integer" })).toBe(2);
    expect(parseVariableDefault("1.5", { type: "number" })).toBe(1.5);
    expect(parseVariableDefault("x", { type: "number" })).toBeNull();
    expect(parseVariableDefault("true", { type: "boolean" })).toBe(true);
    expect(parseVariableDefault("false", { type: "boolean" })).toBe(false);
    expect(parseVariableDefault("2026-10-07", { type: "string", format: "date" })).toBe("2026-10-07");
    expect(parseVariableDefault("", { type: "integer" })).toBeNull();
  });
});
