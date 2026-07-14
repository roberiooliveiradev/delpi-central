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
});
