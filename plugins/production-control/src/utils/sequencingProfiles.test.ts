import { describe, expect, it } from "vitest";

import type { SequencingProfile } from "../types";
import {
  addCriterion,
  applyBindingResult,
  canManageSequencingProfiles,
  availableCriteria,
  buildCriteriaPayload,
  criteriaFromProfile,
  DEFAULT_CABLE_GROUPS,
  moveCriterion,
  parseProductGroups,
  removeCriterion,
  validateCriteria,
} from "./sequencingProfiles";

const base = [{ type: "pa_due_date" as const, groups: [] }];

describe("parseProductGroups", () => {
  it("separa por vírgula, espaço e linha; preserva zeros à esquerda", () => {
    const { groups, rejected } = parseProductGroups("1007, 0010\n1053;abc");
    expect(groups).toEqual(["1007", "0010", "1053"]);
    expect(rejected).toEqual(["abc"]);
  });

  it("deduplica mantendo a ordem", () => {
    const { groups } = parseProductGroups("1007 1007 1038");
    expect(groups).toEqual(["1007", "1038"]);
  });
});

describe("criteria editor state", () => {
  it("pa_due_date nunca sai da primeira posição", () => {
    const items = addCriterion(base, "tool_group");
    expect(moveCriterion(items, 1, -1)).toEqual(items); // índice 1 não sobe
    expect(moveCriterion(items, 0, -1)).toEqual(items); // primeiro travado
    expect(removeCriterion(items, 0)).toEqual(items); // primeiro não remove
  });

  it("não permite critério duplicado", () => {
    const items = addCriterion(base, "tool_group");
    expect(addCriterion(items, "tool_group")).toEqual(items);
    expect(availableCriteria(items)).toEqual(["material_code"]);
  });

  it("material_code entra com os grupos padrão de cabos", () => {
    const items = addCriterion(base, "material_code");
    expect(items[1].groups).toEqual([...DEFAULT_CABLE_GROUPS]);
  });

  it("monta payload com parâmetros fixos do material", () => {
    const items = addCriterion(base, "material_code");
    const payload = buildCriteriaPayload(items);
    expect(payload[0]).toEqual({ type: "pa_due_date" });
    expect(payload[1]).toMatchObject({
      type: "material_code",
      params: {
        material_type: "MP",
        identity_source: "operation_then_order",
        ignore_zeroed_allocations: true,
        on_missing: "flag",
        on_ambiguous: "flag",
      },
    });
    expect(
      (payload[1].params as { eligible_product_groups: string[] })
        .eligible_product_groups.length,
    ).toBe(16);
  });
});

describe("criteriaFromProfile", () => {
  it("reidrata critérios e grupos do perfil salvo", () => {
    const profile = {
      id: "1",
      name: "Teste",
      description: null,
      status: "draft",
      revision: 1,
      origin_branch: "01",
      created_at: null,
      created_by: null,
      updated_at: null,
      updated_by: null,
      criteria: [
        { type: "pa_due_date" },
        {
          type: "material_code",
          params: { eligible_product_groups: ["1007", "0101"] },
        },
        { type: "tool_group" },
      ],
    } as SequencingProfile;
    const items = criteriaFromProfile(profile);
    expect(items.map((item) => item.type)).toEqual([
      "pa_due_date",
      "material_code",
      "tool_group",
    ]);
    expect(items[1].groups).toEqual(["1007", "0101"]);
  });
});

describe("preservação de parâmetros do material", () => {
  it("mantém parâmetros já gravados e só sobrescreve os grupos", () => {
    const profile = {
      id: "1",
      name: "Legado",
      description: null,
      status: "active",
      revision: 3,
      origin_branch: "01",
      created_at: null,
      created_by: null,
      updated_at: null,
      updated_by: null,
      criteria: [
        { type: "pa_due_date" },
        {
          type: "material_code",
          params: {
            material_type: "MP",
            eligible_product_groups: ["1007"],
            identity_source: "order_only",
            ignore_zeroed_allocations: false,
            on_missing: "flag",
            on_ambiguous: "flag",
          },
        },
      ],
    } as SequencingProfile;
    const payload = buildCriteriaPayload(criteriaFromProfile(profile));
    const params = payload[1].params as Record<string, unknown>;
    expect(params.ignore_zeroed_allocations).toBe(false);
    expect(params.identity_source).toBe("order_only");
    expect(params.eligible_product_groups).toEqual(["1007"]);
  });

  it("grupos editados substituem os antigos sem perder os demais params", () => {
    const items = [
      { type: "pa_due_date" as const, groups: [] },
      {
        type: "material_code" as const,
        groups: ["0101"],
        params: { ignore_zeroed_allocations: false },
      },
    ];
    const payload = buildCriteriaPayload(items);
    const params = payload[1].params as Record<string, unknown>;
    expect(params.ignore_zeroed_allocations).toBe(false);
    expect(params.eligible_product_groups).toEqual(["0101"]);
  });
});

describe("validateCriteria", () => {
  it("rejeita material sem grupo", () => {
    const items = [
      ...base,
      { type: "material_code" as const, groups: [] },
    ];
    expect(validateCriteria(items)).toMatch(/grupo/i);
  });

  it("aceita configuração mínima válida", () => {
    expect(validateCriteria(base)).toBeNull();
  });
});

describe("permissão administrativa (gate de UI)", () => {
  it("superadmin administra sem concessão explícita", () => {
    expect(canManageSequencingProfiles([], true)).toBe(true);
    expect(canManageSequencingProfiles(undefined, true)).toBe(true);
  });
  it("exige o grant sequencing-profiles.manage para não-superadmin", () => {
    expect(
      canManageSequencingProfiles(
        ["production-control.sequencing-profiles.manage"],
        false,
      ),
    ).toBe(true);
    expect(canManageSequencingProfiles([], false)).toBe(false);
    expect(canManageSequencingProfiles(undefined, undefined)).toBe(false);
  });
});

describe("applyBindingResult", () => {
  const bound = {
    branch: "01",
    work_center: "CT-01",
    profile_id: "p1",
    assigned_by: "pcp",
    assigned_at: "2026-08-20T10:00:00Z",
  };
  it("desvínculo (profile_id null) remove a linha do estado", () => {
    const result = applyBindingResult([bound], {
      branch: "01",
      work_center: "CT-01",
      profile_id: null,
      assigned_by: null,
      assigned_at: null,
    });
    expect(result).toEqual([]);
  });
  it("vínculo preenchido substitui o anterior do mesmo CT", () => {
    const result = applyBindingResult([bound], {
      branch: "01",
      work_center: "CT-01",
      profile_id: "p2",
      assigned_by: "pcp",
      assigned_at: "2026-08-20T11:00:00Z",
    });
    expect(result).toHaveLength(1);
    expect(result[0].profile_id).toBe("p2");
  });
});
