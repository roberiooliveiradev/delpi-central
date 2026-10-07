import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ComunicadoInputBlockView, resolveInputDisplayValue } from "./ComunicadoInputBlockView";
import { createInputBlock, parseComunicadoConfig, serializeComunicadoConfig } from "./comunicadoHelpers";
import type { ComunicadoInputBlock, ParamExpressionSpec } from "./comunicadoTypes";
import { buildDataPreviewFingerprint, resolvePreviewRefreshModelIds } from "./dataRefresh";

const TODAY_SPEC: ParamExpressionSpec = {
  expression: { version: 1, expression: { kind: "identifier", value: "today" } },
};

function filterBlock(input: Partial<ComunicadoInputBlock["input"]> = {}): ComunicadoInputBlock {
  return {
    id: "flt",
    type: "input",
    frame: { x: 0, y: 0, w: 30, h: 12 },
    input: { paramKey: "start_date", defaultValue: TODAY_SPEC, ...input },
  };
}

const DATE_FIELD = { type: "string", format: "date", label: "Data início" };

describe("Filtro com ExpressionSpec — parser/serializer", () => {
  it("roundtrip preserva o AST no modo parâmetro de dados", () => {
    const block = createInputBlock({ paramKey: "start_date", defaultValue: TODAY_SPEC });
    const serialized = serializeComunicadoConfig({ version: 5, blocks: [block] });
    const raw = (serialized.blocks as Array<Record<string, unknown>>)[0];
    expect(raw?.input).toEqual({ paramKey: "start_date", defaultValue: TODAY_SPEC, targetScope: "slide" });

    const parsed = parseComunicadoConfig(serialized);
    const reserialized = serializeComunicadoConfig(parsed);
    expect(reserialized).toEqual(serialized);
  });

  it("serializer não persiste decoração de runtime", () => {
    const block = filterBlock();
    (block.input as Record<string, unknown>).resolvedValue = "2026-10-07";
    (block.input as Record<string, unknown>).resolvedDiverged = false;
    const serialized = serializeComunicadoConfig({ version: 5, blocks: [block] });
    const raw = (serialized.blocks as Array<Record<string, unknown>>)[0];
    expect(raw?.input).toEqual({ paramKey: "start_date", defaultValue: TODAY_SPEC, targetScope: "slide" });
  });

  it("variável descarta ExpressionSpec (default escalar)", () => {
    const parsed = parseComunicadoConfig({
      version: 5,
      blocks: [
        {
          id: "v",
          type: "input",
          frame: { x: 0, y: 0, w: 10, h: 5 },
          input: {
            paramKey: "",
            binding: { kind: "variable", key: "day" },
            valueSchema: { type: "string" },
            defaultValue: TODAY_SPEC,
          },
        },
      ],
    });
    const input = parsed.blocks?.[0];
    expect(input?.type === "input" ? input.input.defaultValue : "x").toBeNull();
    const variable = createInputBlock({
      binding: { kind: "variable", key: "day" },
      defaultValue: TODAY_SPEC,
    });
    expect(variable.input.defaultValue).toBeNull();
  });

  it("objeto não canônico continua descartado", () => {
    const parsed = parseComunicadoConfig({
      version: 5,
      blocks: [
        { id: "x", type: "input", frame: { x: 0, y: 0, w: 10, h: 5 }, input: { paramKey: "a", defaultValue: { foo: 1 } } },
      ],
    });
    const input = parsed.blocks?.[0];
    expect(input?.type === "input" ? input.input.defaultValue : "x").toBeNull();
  });
});

describe("Filtro com ExpressionSpec — valor exibido", () => {
  it("override de sessão vence; vazio/null volta para a expressão", () => {
    const block = filterBlock();
    (block.input as Record<string, unknown>).resolvedValue = "2026-10-07";
    expect(resolveInputDisplayValue(block, "2026-05-05", false)).toEqual({
      current: "2026-05-05",
      expressionState: null,
    });
    expect(resolveInputDisplayValue(block, null, false)).toEqual({
      current: "2026-10-07",
      expressionState: "resolved",
    });
    expect(resolveInputDisplayValue(block, "", false).current).toBe("2026-10-07");
  });

  it("divergência e ausência de decoração nunca serializam o AST", () => {
    const diverged = filterBlock();
    (diverged.input as Record<string, unknown>).resolvedDiverged = true;
    expect(resolveInputDisplayValue(diverged, undefined, false)).toEqual({
      current: null,
      expressionState: "diverged",
    });
    expect(resolveInputDisplayValue(filterBlock(), undefined, false)).toEqual({
      current: null,
      expressionState: "pending",
    });
  });

  it("legado mantém value ?? defaultValue (null explícito = vazio)", () => {
    const legacy = filterBlock({ defaultValue: "01", paramKey: "branch" });
    expect(resolveInputDisplayValue(legacy, undefined, false).current).toBe("01");
    expect(resolveInputDisplayValue(legacy, null, false).current).toBeNull();
  });

  it("kiosk mostra o valor resolvido, nunca [object Object]", () => {
    const block = filterBlock();
    (block.input as Record<string, unknown>).resolvedValue = "2026-10-07";
    const { container } = render(<ComunicadoInputBlockView block={block} field={DATE_FIELD} />);
    expect(container.textContent).toContain("2026-10-07");
    expect(container.textContent).not.toContain("[object Object]");
  });

  it("kiosk mostra «Valores diferentes» quando os consumidores divergem", () => {
    const block = filterBlock();
    (block.input as Record<string, unknown>).resolvedDiverged = true;
    const { container } = render(<ComunicadoInputBlockView block={block} field={DATE_FIELD} />);
    expect(container.textContent).toContain("Valores diferentes");
    expect(container.textContent).not.toContain("[object Object]");
  });

  it("kiosk interativo permite override escalar sobre a expressão", () => {
    const block = filterBlock();
    (block.input as Record<string, unknown>).resolvedValue = "2026-10-07";
    render(<ComunicadoInputBlockView block={block} field={DATE_FIELD} interactive />);
    const control = screen.getByLabelText("Data início") as HTMLInputElement;
    expect(control.value).toBe("2026-10-07");
    expect(control.readOnly).toBe(false);
  });

  it("palco do editor (authoring) não oferece controle editável sobre a expressão", () => {
    const { container } = render(
      <ComunicadoInputBlockView
        block={filterBlock()}
        field={DATE_FIELD}
        interactive
        interaction={{ selectedPart: null, selectedParts: null }}
      />,
    );
    expect(container.querySelector("input")).toBeNull();
    expect(container.textContent).toContain("Expressão");
  });
});

describe("Filtro com ExpressionSpec — refresh de DataModels", () => {
  const model = {
    id: "m1",
    label: "Modelo",
    primaryInputId: "i1",
    inputs: [{ id: "i1", operationId: "op", params: {} }],
  };

  function fingerprint(input: ComunicadoInputBlock) {
    return buildDataPreviewFingerprint({ version: 5, blocks: [input], dataModels: [model] } as never, {});
  }

  it("Filtro de escopo slide (expressão) recarrega os modelos", () => {
    const prev = fingerprint(filterBlock({ defaultValue: "2026-01-01" }));
    const next = fingerprint(filterBlock());
    expect(
      resolvePreviewRefreshModelIds({ previousFingerprint: prev, nextFingerprint: next, allModelIds: ["m1"] }),
    ).toEqual(["m1"]);
  });

  it("Filtro «Dado específico» não recarrega modelos", () => {
    const prev = fingerprint(filterBlock({ defaultValue: "2026-01-01", targetScope: "sources", targetSourceIds: ["s"] }));
    const next = fingerprint(filterBlock({ targetScope: "sources", targetSourceIds: ["s"] }));
    expect(
      resolvePreviewRefreshModelIds({ previousFingerprint: prev, nextFingerprint: next, allModelIds: ["m1"] }),
    ).toEqual([]);
  });
});
