import { act, cleanup, render } from "@testing-library/react";
import { useEffect, useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { TvDataModel } from "@delpi/tv-dashboard-presentation";

import { ComunicadoEditorProvider } from "./comunicadoEditorContext";
import {
  useComunicadoEditor,
  type ComunicadoEditorContextValue,
} from "./comunicadoEditorContextCore";

const applyPresentationMutations = vi.fn();

vi.mock("../api/tvDashboardApi", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("../api/tvDashboardApi")>();
  return {
    ...actual,
    applyPresentationMutations: (...args: unknown[]) =>
      applyPresentationMutations(...args),
  };
});

const MODEL: TvDataModel = {
  id: "m1",
  label: "Mensal",
  primaryInputId: "in-a",
  inputs: [
    {
      id: "in-a",
      operationId: "route_a",
      label: "Atual",
      params: { branch: "01" },
    },
    { id: "in-b", operationId: "route_a", label: "Anterior" },
  ],
  fieldLabels: { rol: "ROL" },
};

function makeValue(model: TvDataModel | null = MODEL) {
  return {
    version: 2,
    blocks: [],
    ...(model ? { dataModels: [model] } : {}),
  };
}

let capturedApi: ComunicadoEditorContextValue | null = null;
function Probe() {
  const api = useComunicadoEditor();
  useEffect(() => {
    capturedApi = api;
  });
  return null;
}

function EditorHarness({
  slideId,
  onChange,
  model,
}: {
  slideId?: string;
  onChange?: (config: Record<string, unknown>) => void;
  model?: TvDataModel | null;
}) {
  // Pai stateful: replica o contrato real — `value` segue o último onChange,
  // senão o gate anti-eco do provider reverteria a config para o prop antigo.
  const [value, setValue] = useState<Record<string, unknown>>(() =>
    makeValue(model ?? MODEL),
  );
  return (
    <ComunicadoEditorProvider
      playlistId="pl-1"
      slideId={slideId}
      value={value}
      onChange={(next) => {
        setValue(next);
        onChange?.(next);
      }}
    >
      <Probe />
    </ComunicadoEditorProvider>
  );
}

function mountEditor(options: {
  slideId?: string;
  onChange?: (config: Record<string, unknown>) => void;
  model?: TvDataModel | null;
}) {
  render(<EditorHarness {...options} />);
  if (!capturedApi) throw new Error("context unavailable");
  return capturedApi as ComunicadoEditorContextValue;
}

function persistedModel(): TvDataModel {
  const model = (capturedApi?.config.dataModels ?? [])[0];
  if (!model) throw new Error("model missing");
  return model;
}

afterEach(() => {
  cleanup();
  applyPresentationMutations.mockReset();
});

describe("saveDataModel — roteamento de mutação governada (TV-DM-MUT-002)", () => {
  it("edição pontual de modelo existente usa patch_data_model, nunca upsert", async () => {
    const api = mountEditor({ slideId: "s1" });
    const canonical = {
      version: 2,
      blocks: [],
      dataModels: [
        {
          ...MODEL,
          inputs: [
            { ...MODEL.inputs![0]!, params: { branch: "02" } },
            MODEL.inputs![1]!,
          ],
        },
      ],
    };
    applyPresentationMutations.mockResolvedValue({ nativeConfig: canonical });

    const next = structuredClone(persistedModel());
    next.inputs![0]!.params = { branch: "02" };
    await act(async () => {
      await api.saveDataModel(next);
    });

    expect(applyPresentationMutations).toHaveBeenCalledTimes(1);
    const ops = applyPresentationMutations.mock.calls[0]![2];
    expect(ops).toEqual([
      {
        op: "patch_data_model",
        modelId: "m1",
        inputPatches: [{ inputId: "in-a", params: { set: { branch: "02" } } }],
      },
    ]);
    // estado local substituído pela config canônica do backend
    expect(persistedModel().inputs![0]!.params).toEqual({ branch: "02" });
  });

  it("modelo novo continua em upsert_data_model", async () => {
    const api = mountEditor({ slideId: "s1" });
    applyPresentationMutations.mockResolvedValue({
      nativeConfig: { version: 2, blocks: [], dataModels: [MODEL] },
    });
    const fresh: TvDataModel = {
      id: "m-new",
      primaryInputId: "in-x",
      inputs: [{ id: "in-x", operationId: "route_a" }],
    };
    await act(async () => {
      await api.saveDataModel(fresh);
    });
    const [, , ops] = applyPresentationMutations.mock.calls[0]!;
    expect(ops[0]!.op).toBe("upsert_data_model");
  });

  it("falha de persistência em slide persistido propaga — sem fallback local", async () => {
    const onChange = vi.fn();
    const api = mountEditor({ slideId: "s1", onChange });
    applyPresentationMutations.mockRejectedValue(new Error("boom"));

    const next = structuredClone(persistedModel());
    next.inputs![0]!.params = { branch: "99" };
    await expect(
      act(async () => {
        await api.saveDataModel(next);
      }),
    ).rejects.toThrow("boom");

    // draft local NUNCA foi aplicado como se tivesse persistido
    expect(persistedModel().inputs![0]!.params).toEqual({ branch: "01" });
    expect(onChange).not.toHaveBeenCalled();
  });

  it("editor standalone (sem slideId) mantém fallback local, sem API", async () => {
    const onChange = vi.fn();
    const api = mountEditor({ onChange });
    const next = structuredClone(persistedModel());
    next.inputs![0]!.params = { branch: "07" };
    await act(async () => {
      await api.saveDataModel(next);
    });
    expect(applyPresentationMutations).not.toHaveBeenCalled();
    expect(persistedModel().inputs![0]!.params).toEqual({ branch: "07" });
    expect(onChange).toHaveBeenCalled();
  });
});
