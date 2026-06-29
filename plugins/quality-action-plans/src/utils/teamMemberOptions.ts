import type { SelectOption } from "../components/ui/types";
import type { TeamMember } from "../types/rnc8d";

/** Opções de select a partir da equipe 8D (seção 2), preservando valores já salvos. */
export function buildTeamMemberSelectOptions(
  members: TeamMember[] | undefined,
  extraValues?: Array<string | null | undefined>,
): SelectOption[] {
  const seen = new Set<string>();
  const options: SelectOption[] = [];

  for (const member of members ?? []) {
    const name = member.member_name?.trim();
    if (!name || seen.has(name)) continue;
    seen.add(name);
    const department = member.department?.trim();
    options.push({
      value: name,
      label: department ? `${name} — ${department}` : name,
    });
  }

  for (const raw of extraValues ?? []) {
    const value = raw?.trim();
    if (!value || seen.has(value)) continue;
    seen.add(value);
    options.push({ value, label: value });
  }

  return options;
}
