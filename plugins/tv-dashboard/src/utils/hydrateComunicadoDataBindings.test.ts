import { beforeEach, describe, expect, it } from "vitest";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  buildHydrateBindingsInputFingerprint,
  buildLabelCatalogFromRoutes,
  collectHydrateDataBindingPatches,
  commitHydrateBindingsApplyPlan,
  hydrateComunicadoDataBindings,
  planHydrateBindingsApply,
  projectBranchParamsOntoRouteSchema,
  resetHydrateBindingsSessionFingerprintForTests,
} from "./hydrateComunicadoDataBindings";

const ppmRoute: TvDataRouteCatalogItem = {
  operationId: "get_ppm_internal_summary",
  label: "PPM Interno — realizado",
  labelAliases: ["Qualidade — PPM interno"],
  category: "quality",
  paramSchema: {
    start_date: { type: "string" },
    end_date: { type: "string" },
    branch: { type: "string", optional: true },
  },
};

function sourceBlock(
  operationId: string,
  opts: { label?: string; params?: Record<string, string | number | boolean> } = {},
) {
  return {
    id: `src-${operationId}`,
    type: "data_source" as const,
    frame: { x: 0, y: 0, w: 10, h: 10 },
    dataBinding: {
      operationId,
      params: opts.params ?? {},
      displayMode: "auto" as const,
      label: opts.label,
    },
  };
}

describe("hydrateComunicadoDataBindings", () => {
  it("limpa label catalog-like e remapeia date_start", () => {
    const config = {
      version: 4 as const,
      blocks: [
        sourceBlock("get_ppm_internal_summary", {
          label: "Qualidade — PPM interno",
          params: { date_start: "2026-01-01", date_end: "2026-01-31", obsolete: "x" },
        }),
      ],
    };
    const result = hydrateComunicadoDataBindings(config, [ppmRoute]);
    expect(result.changed).toBe(true);
    expect(result.clearedLabels).toBe(1);
    const binding =
      result.config.blocks?.[0] && "dataBinding" in result.config.blocks[0]
        ? result.config.blocks[0].dataBinding
        : null;
    expect(binding?.label).toBeUndefined();
    expect(binding?.params?.start_date).toBe("2026-01-01");
    expect(binding?.params?.end_date).toBe("2026-01-31");
    expect(binding?.params).not.toHaveProperty("date_start");
    expect(binding?.params).not.toHaveProperty("obsolete");
    expect(result.strippedParamKeys).toContain("obsolete");
  });

  it("preserva rótulo customizado", () => {
    const result = hydrateComunicadoDataBindings(
      {
        version: 4,
        blocks: [sourceBlock("get_ppm_internal_summary", { label: "Meu KPI" })],
      },
      [ppmRoute],
    );
    const binding =
      result.config.blocks?.[0] && "dataBinding" in result.config.blocks[0]
        ? result.config.blocks[0].dataBinding
        : null;
    expect(binding?.label).toBe("Meu KPI");
  });

  it("marca rota órfã sem apagar o bloco", () => {
    const result = hydrateComunicadoDataBindings(
      { version: 4, blocks: [sourceBlock("get_gone_route", { params: { a: 1 } })] },
      [ppmRoute],
    );
    expect(result.orphanOperationIds).toEqual(["get_gone_route"]);
    expect(result.config.blocks).toHaveLength(1);
  });
});

describe("buildLabelCatalogFromRoutes", () => {
  it("expõe label vivo por operationId (mesmo input da aba Dados no Elemento)", () => {
    const catalog = buildLabelCatalogFromRoutes([ppmRoute]);
    expect(catalog.get_ppm_internal_summary).toEqual({
      label: "PPM Interno — realizado",
      labelAliases: ["Qualidade — PPM interno"],
    });
  });
});

const transformaRoute: TvDataRouteCatalogItem = {
  operationId: "get_transforma_mais_summary",
  label: "Resumo Transforma Mais",
  category: "engineering",
  paramSchema: {
    filial_id: { type: "string", optional: true },
    start_date: { type: "string" },
    end_date: { type: "string" },
  },
};

describe("projectBranchParamsOntoRouteSchema", () => {
  it("projeta branch → filial_id do schema", () => {
    const projected = projectBranchParamsOntoRouteSchema(
      { branch: "01", start_date: "2026-01-01" },
      new Set(["filial_id", "start_date", "end_date"]),
    );
    expect(projected.filial_id).toBe("01");
    expect(projected).not.toHaveProperty("branch");
    expect(projected.start_date).toBe("2026-01-01");
  });
});

describe("hydrateComunicadoDataBindings idempotência", () => {
  it("projeta branch e fica estável na segunda passagem (sem loop)", () => {
    const config = {
      version: 4 as const,
      blocks: [
        sourceBlock("get_transforma_mais_summary", {
          params: { branch: "01", start_date: "2026-01-01" },
        }),
      ],
    };
    const first = hydrateComunicadoDataBindings(config, [transformaRoute]);
    expect(first.changed).toBe(true);
    const binding =
      first.config.blocks?.[0] && "dataBinding" in first.config.blocks[0]
        ? first.config.blocks[0].dataBinding
        : null;
    expect(binding?.params?.filial_id).toBe("01");
    expect(binding?.params).not.toHaveProperty("branch");

    const second = hydrateComunicadoDataBindings(first.config, [transformaRoute]);
    expect(second.changed).toBe(false);
    expect(collectHydrateDataBindingPatches(first.config, second.config)).toEqual([]);
  });

  it("planHydrateBindingsApply não reaplica o mesmo input (ribbon + painel)", () => {
    resetHydrateBindingsSessionFingerprintForTests();
    const config = {
      version: 4 as const,
      blocks: [
        sourceBlock("get_transforma_mais_summary", {
          label: "Resumo Transforma Mais",
          params: { branch: "02" },
        }),
      ],
    };
    const plan = planHydrateBindingsApply(config, [transformaRoute]);
    expect(plan).not.toBeNull();
    expect(plan?.patches).toHaveLength(1);
    commitHydrateBindingsApplyPlan(plan!);

    const again = planHydrateBindingsApply(plan!.result.config, [transformaRoute]);
    expect(again).toBeNull();

    // Segunda montagem com o mesmo input pré-hydrate também é no-op após commit do output.
    const twinMount = planHydrateBindingsApply(config, [transformaRoute]);
    expect(twinMount).toBeNull();
  });

  it("fingerprint de input ignora ordem de chaves em params", () => {
    const a = {
      version: 4 as const,
      blocks: [sourceBlock("get_ppm_internal_summary", { params: { branch: "01", start_date: "a" } })],
    };
    const b = {
      version: 4 as const,
      blocks: [sourceBlock("get_ppm_internal_summary", { params: { start_date: "a", branch: "01" } })],
    };
    expect(buildHydrateBindingsInputFingerprint(a, [ppmRoute])).toBe(
      buildHydrateBindingsInputFingerprint(b, [ppmRoute]),
    );
  });
});

describe("reset session", () => {
  beforeEach(() => {
    resetHydrateBindingsSessionFingerprintForTests();
  });

  it("permite novo plan após reset", () => {
    const config = {
      version: 4 as const,
      blocks: [sourceBlock("get_transforma_mais_summary", { params: { branch: "01" } })],
    };
    const plan = planHydrateBindingsApply(config, [transformaRoute]);
    expect(plan).not.toBeNull();
    commitHydrateBindingsApplyPlan(plan!);
    resetHydrateBindingsSessionFingerprintForTests();
    expect(planHydrateBindingsApply(config, [transformaRoute])).not.toBeNull();
  });
});
