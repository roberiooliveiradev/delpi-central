import { useMemo } from "react";

import { PAC_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { TeamMember } from "../../types/rnc8d";
import { buildTeamMemberSelectOptions } from "../../utils/teamMemberOptions";
import { SelectField } from "../ui/SelectField";

type Props = {
  id: string;
  label: string;
  hint?: string;
  value: string;
  onChange: (value: string) => void;
  teamMembers: TeamMember[] | undefined;
  extraValues?: Array<string | null | undefined>;
};

export function TeamMemberSelectField({
  id,
  label,
  hint = PAC_HELP_TOOLTIPS.rnc8d.teamMemberSelect,
  value,
  onChange,
  teamMembers,
  extraValues,
}: Props) {
  const options = useMemo(
    () => buildTeamMemberSelectOptions(teamMembers, [value, ...(extraValues ?? [])]),
    [teamMembers, extraValues, value],
  );

  return (
    <SelectField
      id={id}
      label={label}
      hint={hint}
      options={options}
      value={value}
      onChange={onChange}
      searchable
      allowEmpty
      emptyLabel="Selecione…"
    />
  );
}
