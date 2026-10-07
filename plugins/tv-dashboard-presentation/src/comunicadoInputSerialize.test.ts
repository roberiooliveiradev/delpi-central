import { describe, expect, it } from "vitest";

import { createInputBlock, parseComunicadoConfig, serializeComunicadoConfig } from "./comunicadoHelpers";

describe("serialize input block", () => {
  it("preserva paramKey, defaultValue, iconName e alvo multi-fonte no roundtrip", () => {
    const input = {
      ...createInputBlock({
        paramKey: "branch",
        defaultValue: "01",
        targetScope: "sources",
        targetSourceIds: ["src-gaps"],
        label: "Filial",
        iconName: "Building2",
      }),
      inputParts: {
        label: { style: { fontSize: 16 }, visible: true },
        badge: { visible: false },
      },
    };
    expect(input.frame).toEqual({ x: 8, y: 8, w: 12, h: 5 });
    const serialized = serializeComunicadoConfig({ version: 5, blocks: [input] });
    const block = (serialized.blocks as Array<Record<string, unknown>>)[0];
    expect(block?.type).toBe("input");
    expect(block?.input).toEqual({
      paramKey: "branch",
      label: "Filial",
      iconName: "Building2",
      defaultValue: "01",
      targetScope: "sources",
      targetSourceIds: ["src-gaps"],
    });
    expect(block?.inputParts).toEqual({
      label: { style: { fontSize: 16 }, visible: true },
      badge: { visible: false },
    });

    const parsed = parseComunicadoConfig(serialized);
    const parsedInput = parsed.blocks?.find((item) => item.type === "input");
    expect(parsedInput?.type).toBe("input");
    if (parsedInput?.type === "input") {
      expect(parsedInput.input.paramKey).toBe("branch");
      expect(parsedInput.input.defaultValue).toBe("01");
      expect(parsedInput.input.iconName).toBe("Building2");
      expect(parsedInput.input.targetScope).toBe("sources");
      expect(parsedInput.input.targetSourceIds).toEqual(["src-gaps"]);
      expect(parsedInput.inputParts?.label?.style?.fontSize).toBe(16);
      expect(parsedInput.inputParts?.badge?.visible).toBe(false);
    }
  });

  it("legado sem binding mantém o shape persistido exato (sem chaves novas)", () => {
    const serialized = serializeComunicadoConfig({
      version: 5,
      blocks: [createInputBlock({ paramKey: "periodDays", defaultValue: 30 })],
    });
    const block = (serialized.blocks as Array<Record<string, unknown>>)[0];
    expect(block?.input).toEqual({ paramKey: "periodDays", defaultValue: 30, targetScope: "slide" });
  });
});

const MEETING_DAY_INPUT = {
  binding: { kind: "variable", key: "meeting_day" },
  valueSchema: {
    type: "integer",
    enum: [0, 1, 2, 3, 4],
    enumLabels: { "0": "Segunda-feira", "1": "Terça-feira", "2": "Quarta-feira", "3": "Quinta-feira", "4": "Sexta-feira" },
  },
  label: "Dia de referência da reunião",
  iconName: "CalendarDays",
  defaultValue: 0,
};

describe("serialize input variable", () => {
  it("roundtrip preserva binding, valueSchema, label, iconName e defaultValue", () => {
    const parsed = parseComunicadoConfig({
      version: 5,
      blocks: [{ id: "in-md", type: "input", frame: { x: 1, y: 1, w: 10, h: 5 }, input: MEETING_DAY_INPUT }],
    });
    const serialized = serializeComunicadoConfig(parsed);
    const block = (serialized.blocks as Array<Record<string, unknown>>)[0];
    expect(block?.input).toEqual(MEETING_DAY_INPUT);
  });

  it("carregar variável → editar campo não relacionado → serializar mantém binding/valueSchema", () => {
    const parsed = parseComunicadoConfig({
      version: 5,
      blocks: [
        { id: "in-md", type: "input", frame: { x: 1, y: 1, w: 10, h: 5 }, input: MEETING_DAY_INPUT },
        { id: "txt", type: "text", frame: { x: 1, y: 10, w: 20, h: 5 }, content: "antes" },
      ],
    });
    const edited = {
      ...parsed,
      blocks: (parsed.blocks ?? []).map((item) =>
        item.type === "text" ? { ...item, content: "depois" } : { ...item, frame: { ...item.frame, x: 3 } },
      ),
    };
    const serialized = serializeComunicadoConfig(edited);
    const input = (serialized.blocks as Array<Record<string, unknown>>).find((item) => item.id === "in-md");
    expect(input?.input).toEqual(MEETING_DAY_INPUT);
  });

  it("não persiste resolvedField/paramAvailable nem valores de sessão", () => {
    const parsed = parseComunicadoConfig({
      version: 5,
      blocks: [
        {
          id: "in-md",
          type: "input",
          frame: { x: 1, y: 1, w: 10, h: 5 },
          input: { ...MEETING_DAY_INPUT, resolvedField: { type: "integer" }, paramAvailable: true },
        },
      ],
    });
    const serialized = serializeComunicadoConfig(parsed);
    const input = (serialized.blocks as Array<Record<string, unknown>>)[0]?.input as Record<string, unknown>;
    expect(input).not.toHaveProperty("resolvedField");
    expect(input).not.toHaveProperty("paramAvailable");
  });

  it("data usa o shape de paramSchema (type string + format date)", () => {
    const block = createInputBlock({
      binding: { kind: "variable", key: "reference_date" },
      valueSchema: { type: "string", format: "date" },
      defaultValue: "2026-10-05",
    });
    const serialized = serializeComunicadoConfig({ version: 5, blocks: [block] });
    expect((serialized.blocks as Array<Record<string, unknown>>)[0]?.input).toEqual({
      binding: { kind: "variable", key: "reference_date" },
      valueSchema: { type: "string", format: "date" },
      defaultValue: "2026-10-05",
    });
  });

  it("shape ambíguo (paramKey + variable) é preservado para o backend rejeitar — sem correção silenciosa", () => {
    const parsed = parseComunicadoConfig({
      version: 5,
      blocks: [
        {
          id: "in-x",
          type: "input",
          frame: { x: 1, y: 1, w: 10, h: 5 },
          input: { ...MEETING_DAY_INPUT, paramKey: "branch" },
        },
      ],
    });
    const serialized = serializeComunicadoConfig(parsed);
    const input = (serialized.blocks as Array<Record<string, unknown>>)[0]?.input as Record<string, unknown>;
    expect(input.paramKey).toBe("branch");
    expect(input.binding).toEqual({ kind: "variable", key: "meeting_day" });
  });
});
