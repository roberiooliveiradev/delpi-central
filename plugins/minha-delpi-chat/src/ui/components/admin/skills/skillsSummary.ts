import type { AdminChatSkill } from "../../../../data/api/adminTypes";

export type SkillStatusFilter = "all" | "active" | "inactive";

export type SkillsSummary = {
  total: number;
  active: number;
  inactive: number;
};

export function computeSkillsSummary(skills: AdminChatSkill[]): SkillsSummary {
  let active = 0;
  let inactive = 0;

  for (const skill of skills) {
    if (skill.isActive) {
      active += 1;
    } else {
      inactive += 1;
    }
  }

  return {
    total: skills.length,
    active,
    inactive,
  };
}

export function filterSkillsByStatus(
  skills: AdminChatSkill[],
  filter: SkillStatusFilter,
): AdminChatSkill[] {
  if (filter === "all") {
    return skills;
  }

  if (filter === "active") {
    return skills.filter((skill) => skill.isActive);
  }

  return skills.filter((skill) => !skill.isActive);
}
