import type { AdminGuideline, AdminGuidelineStatus } from "../../../../data/api/adminTypes";

export type GuidelineStatusFilter = "all" | AdminGuidelineStatus;

export type GuidelinesSummary = {
  total: number;
  active: number;
  draft: number;
  archived: number;
};

export function computeGuidelinesSummary(
  guidelines: AdminGuideline[],
): GuidelinesSummary {
  let active = 0;
  let draft = 0;
  let archived = 0;

  for (const guideline of guidelines) {
    if (guideline.status === "active") {
      active += 1;
    } else if (guideline.status === "draft") {
      draft += 1;
    } else if (guideline.status === "archived") {
      archived += 1;
    }
  }

  return {
    total: guidelines.length,
    active,
    draft,
    archived,
  };
}

export function filterGuidelinesByStatus(
  guidelines: AdminGuideline[],
  filter: GuidelineStatusFilter,
): AdminGuideline[] {
  if (filter === "all") {
    return guidelines;
  }

  return guidelines.filter((guideline) => guideline.status === filter);
}
