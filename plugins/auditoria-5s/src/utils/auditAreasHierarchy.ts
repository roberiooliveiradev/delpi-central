import type { AuditArea } from "../api/audit5sApi";

/** Áreas auditáveis (folhas): não são agregadoras. */
export function leafAreas(areas: AuditArea[]): AuditArea[] {
  return areas.filter((area) => !area.is_aggregator);
}

export function aggregatorAreas(areas: AuditArea[]): AuditArea[] {
  return areas.filter((area) => Boolean(area.is_aggregator));
}

export function ungroupedLeafAreas(areas: AuditArea[]): AuditArea[] {
  return areas.filter((area) => !area.is_aggregator && !area.is_sub_area);
}

export function childrenOf(areas: AuditArea[], parentId: string): AuditArea[] {
  return areas.filter((area) => area.parent_area_id === parentId);
}

/** Candidatas a subárea no modal (não agregadoras). */
export function eligibleSubAreaCandidates(
  areas: AuditArea[],
  parentId: string | null,
): AuditArea[] {
  return areas.filter((area) => {
    if (area.is_aggregator) return false;
    if (parentId && area.id === parentId) return false;
    return true;
  });
}
