import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ComunicadoInputBlockView } from "./ComunicadoInputBlockView";
import { ComunicadoBlockView } from "./comunicadoBlockView";
import {
  applyRuntimeInputValue,
  collectInputFilterContributions,
  emptyInputFilterContributions,
  hasInputFilterContributions,
  resolveInputRefreshSourceIds,
  serializeInputFilterOverridesQuery,
} from "./comunicadoInputFilters";
import { resolveInputBindingKey, resolveInputVariableBinding } from "./comunicadoInputBinding";
import { buildDataPreviewFingerprint, resolvePreviewRefreshModelIds } from "./dataRefresh";
import type { ComunicadoBlock, ComunicadoConfig, ComunicadoInputBlock } from "./comunicadoTypes";

function variableBlock(id = "in-md", patch: Partial<ComunicadoInputBlock["input"]> = {}): ComunicadoInputBlock {
  return {
    id,
    type: "input",
    frame: { x: 0, y: 0, w: 30, h: 12 },
    input: {
      paramKey: "",
      binding: { kind: "variable", key: "meeting_day" },
      valueSchema: {
        type: "integer",
        enum: [0, 1, 2],
        enumLabels: { "0": "Segunda-feira", "1": "Terça-feira", "2": "Quarta-feira" },
      },
      label: "Dia da reunião",
      defaultValue: 0,
      ...patch,
    },
  };
}

function legacyBlock(): ComunicadoInputBlock {
  return {
    id: "in-branch",
    type: "input",
    frame: { x: 0, y: 0, w: 30, h: 12 },
    input: { paramKey: "branch", defaultValue: "01", targetScope: "slide" },
  };
}

describe("binding helpers", () => {
  it("variable resolve a key; legado cai no paramKey", () => {
    expect(resolveInputVariableBinding(variableBlock().input)).toEqual({ kind: "variable", key: "meeting_day" });
    expect(resolveInputBindingKey(variableBlock().input)).toBe("meeting_day");
    expect(resolveInputVariableBinding(legacyBlock().input)).toBeNull();
    expect(resolveInputBindingKey(legacyBlock().input)).toBe("branch");
  });
});

describe("runtime overrides slide-scoped", () => {
  it("override de variável vai para bySlideId[slide].byInputId[blockId]", () => {
    const next = applyRuntimeInputValue(emptyInputFilterContributions(), variableBlock(), 2, "slide-a");
    expect(next.bySlideId).toEqual({ "slide-a": { byInputId: { "in-md": 2 } } });
    expect(next.slide).toEqual({});
    expect(next.bySourceId).toEqual({});
    expect(hasInputFilterContributions(next)).toBe(true);
  });

  it("mesma key em slides A e B fica isolada; reset remove só a entrada do slide", () => {
    let state = applyRuntimeInputValue(emptyInputFilterContributions(), variableBlock(), 2, "slide-a");
    state = applyRuntimeInputValue(state, variableBlock(), 1, "slide-b");
    expect(state.bySlideId?.["slide-a"]?.byInputId["in-md"]).toBe(2);
    expect(state.bySlideId?.["slide-b"]?.byInputId["in-md"]).toBe(1);
    state = applyRuntimeInputValue(state, variableBlock(), null, "slide-a");
    expect(state.bySlideId?.["slide-a"]).toBeUndefined();
    expect(state.bySlideId?.["slide-b"]?.byInputId["in-md"]).toBe(1);
  });

  it("sem slideId não publica override de variável (fail closed)", () => {
    const base = emptyInputFilterContributions();
    expect(applyRuntimeInputValue(base, variableBlock(), 2)).toBe(base);
  });

  it("variável não vaza para filtros legados (slide/bySourceId)", () => {
    const contributions = collectInputFilterContributions([variableBlock(), legacyBlock()]);
    expect(contributions.slide).toEqual({ branch: "01" });
    expect(contributions.bySourceId).toEqual({});
  });

  it("legado inalterado: override de paramKey continua em slide", () => {
    const next = applyRuntimeInputValue(emptyInputFilterContributions(), legacyBlock(), "02", "slide-a");
    expect(next).toEqual({ slide: { branch: "02" }, bySourceId: {} });
  });
});

describe("serializeInputFilterOverridesQuery", () => {
  it("vazio → null; legado mantém envelope { slide, bySourceId }", () => {
    expect(serializeInputFilterOverridesQuery(emptyInputFilterContributions())).toBeNull();
    expect(serializeInputFilterOverridesQuery({ slide: { branch: "02" }, bySourceId: {} })).toBe(
      JSON.stringify({ slide: { branch: "02" }, bySourceId: {} }),
    );
  });

  it("inclui bySlideId só quando houver override de variável", () => {
    const next = applyRuntimeInputValue(emptyInputFilterContributions(), variableBlock(), 2, "slide-a");
    expect(JSON.parse(serializeInputFilterOverridesQuery(next) ?? "null")).toEqual({
      slide: {},
      bySourceId: {},
      bySlideId: { "slide-a": { byInputId: { "in-md": 2 } } },
    });
  });
});

describe("refresh da variável", () => {
  const source: ComunicadoBlock = {
    id: "src-1",
    type: "data_source",
    frame: { x: 0, y: 0, w: 10, h: 10 },
    dataBinding: { operationId: "op_a", params: {} },
  } as ComunicadoBlock;

  it("refresca todas as fontes fetchable do slide", () => {
    expect(resolveInputRefreshSourceIds(variableBlock(), [variableBlock(), source])).toEqual(["src-1"]);
  });

  it("variável com targetScope residual «sources» ainda refresca todas as fontes", () => {
    const ambiguous = variableBlock("in-md", { targetScope: "sources", targetSourceIds: [] });
    expect(resolveInputRefreshSourceIds(ambiguous, [ambiguous, source])).toEqual(["src-1"]);
  });

  it("mudança de default da variável refresca todos os DataModels", () => {
    const config = (input: ComunicadoInputBlock): ComunicadoConfig => ({
      version: 5,
      blocks: [input, source],
      dataModels: [
        { id: "dm-1", primaryInputId: "i1", inputs: [{ id: "i1", operationId: "op_a", params: {} }] },
      ],
    }) as ComunicadoConfig;
    const before = buildDataPreviewFingerprint(config(variableBlock()));
    const after = buildDataPreviewFingerprint(config(variableBlock("in-md", { defaultValue: 2 })));
    expect(
      resolvePreviewRefreshModelIds({ previousFingerprint: before, nextFingerprint: after, allModelIds: ["dm-1"] }),
    ).toEqual(["dm-1"]);
  });

  it("mudança de valueSchema altera o fingerprint", () => {
    const config = (input: ComunicadoInputBlock): ComunicadoConfig =>
      ({ version: 5, blocks: [input, source] }) as ComunicadoConfig;
    const before = buildDataPreviewFingerprint(config(variableBlock()));
    const after = buildDataPreviewFingerprint(
      config(variableBlock("in-md", { valueSchema: { type: "integer", enum: [0, 1, 2, 3] } })),
    );
    expect(after).not.toBe(before);
  });
});

describe("ComunicadoInputBlockView — variável", () => {
  afterEach(cleanup);

  it("usa valueSchema persistido, rótulos do enum e publica número", () => {
    const onChange = vi.fn();
    render(<ComunicadoInputBlockView block={variableBlock()} interactive onChange={onChange} />);
    expect(screen.getByRole("option", { name: "Quarta-feira" })).toBeTruthy();
    expect(screen.getByText("Variável do slide")).toBeTruthy();
    expect(screen.queryByText("Valor livre")).toBeNull();
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "2" } });
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it("modo leitura mostra o rótulo do valor", () => {
    render(<ComunicadoInputBlockView block={variableBlock()} value={1} />);
    expect(screen.getByText("Terça-feira")).toBeTruthy();
  });

  it("sem binding.key fica indisponível", () => {
    render(
      <ComunicadoInputBlockView
        block={variableBlock("in-md", { binding: { kind: "variable", key: "" } })}
        interactive
      />,
    );
    expect(screen.getByText("Selecione o parâmetro no inspetor")).toBeTruthy();
  });
});

describe("ComunicadoBlockView — variável no quiosque", () => {
  afterEach(cleanup);

  it("input variável é editável no quiosque e publica pelo id do bloco", () => {
    const onInputValueChange = vi.fn();
    render(
      <ComunicadoBlockView block={variableBlock()} inputsInteractive onInputValueChange={onInputValueChange} />,
    );
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "1" } });
    expect(onInputValueChange).toHaveBeenCalledWith("in-md", 1);
  });

  it("variável sem key fica indisponível no quiosque", () => {
    render(
      <ComunicadoBlockView
        block={variableBlock("in-md", { binding: { kind: "variable", key: "" } })}
        inputsInteractive
        onInputValueChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Selecione o parâmetro no inspetor")).toBeTruthy();
  });
});
