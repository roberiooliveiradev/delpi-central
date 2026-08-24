import type {
  FinishedProductShortageMaterial,
  FinishedProductShortageSet,
  MaterialsIssueId,
  MaterialsSetStatus,
  PpcBranch,
} from "../types";
import { buildPpcHref } from "./routeParser";

const PRODUCT_CODE = /^\d{8,}$/;
const SET_STATUSES = new Set<MaterialsSetStatus>(["shortage", "no_commitment", "ok", "all"]);

export function asMaterialsWorkspace(issue: string | null): MaterialsIssueId {
  if (issue === "shortage" || issue === "pa-shortage") return issue;
  return "excess";
}

export function canQueryFinishedProductShortages(code: string | null | undefined): boolean {
  return PRODUCT_CODE.test((code ?? "").trim());
}

export function finishedProductShortageQueryCode(
  workspace: MaterialsIssueId,
  search: string | null | undefined,
): string {
  if (workspace !== "pa-shortage") return "";
  const token = (search ?? "").trim();
  return canQueryFinishedProductShortages(token) ? token : "";
}

export function machineLoadLocateHref(branch: PpcBranch, productionOrder: string): string {
  return buildPpcHref({
    subpluginId: "machine-load",
    branch,
    locateQuery: productionOrder,
  });
}

export function deliveryMapOrderHref(branch: PpcBranch, productionOrder: string): string {
  return buildPpcHref({
    subpluginId: "delivery-map",
    branch,
    deliveryMapSearch: productionOrder,
  });
}

export function asMaterialsSetStatus(value: string | null | undefined): MaterialsSetStatus {
  const token = (value ?? "").trim() as MaterialsSetStatus;
  return SET_STATUSES.has(token) ? token : "all";
}

export function safetyStockHref(productCode: string): string {
  const params = new URLSearchParams({ q: productCode });
  return `/apps/estoque-seguranca?${params.toString()}`;
}

const MATERIAL_STATUS_RANK: Record<FinishedProductShortageMaterial["status"], number> = {
  shortage: 0,
  no_commitment: 1,
  ok: 2,
};

export function sortSetMaterials(
  materials: readonly FinishedProductShortageMaterial[],
): FinishedProductShortageMaterial[] {
  return [...materials].sort((left, right) => {
    const rank = MATERIAL_STATUS_RANK[left.status] - MATERIAL_STATUS_RANK[right.status];
    if (rank !== 0) return rank;
    return left.product_code.localeCompare(right.product_code, "pt-BR");
  });
}

export function countSetMaterialsByStatus(
  materials: readonly FinishedProductShortageMaterial[],
): Record<MaterialsSetStatus, number> {
  return {
    all: materials.length,
    shortage: materials.filter((item) => item.status === "shortage").length,
    no_commitment: materials.filter((item) => item.status === "no_commitment").length,
    ok: materials.filter((item) => item.status === "ok").length,
  };
}

export function filterSetMaterials(
  materials: readonly FinishedProductShortageMaterial[],
  status: MaterialsSetStatus,
): FinishedProductShortageMaterial[] {
  const sorted = sortSetMaterials(materials);
  if (status === "all") return sorted;
  return sorted.filter((item) => item.status === status);
}

export function uniqueMaterialAvailability(sets: readonly FinishedProductShortageSet[]): {
  ok: number;
  total: number;
  percent: number;
} {
  const worst = new Map<string, FinishedProductShortageMaterial["status"]>();
  for (const set of sets) {
    for (const material of set.materials) {
      const previous = worst.get(material.product_code);
      if (
        previous == null ||
        MATERIAL_STATUS_RANK[material.status] < MATERIAL_STATUS_RANK[previous]
      ) {
        worst.set(material.product_code, material.status);
      }
    }
  }
  const total = worst.size;
  const ok = [...worst.values()].filter((status) => status === "ok").length;
  return {
    ok,
    total,
    percent: total ? Math.round((ok / total) * 100) : 0,
  };
}
