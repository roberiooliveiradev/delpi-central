import { MultiSelectField } from "./ui/MultiSelectField";
import { ActionResponsiblesChips } from "./ActionResponsiblesChips";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { ActionResponsible } from "../types/actionPlan";
import type { TeamMember } from "../types/rnc8d";
import { buildTeamMemberSelectOptions } from "../utils/teamMemberOptions";

type Props = {
  idPrefix?: string;
  value: ActionResponsible[];
  teamMembers?: TeamMember[];
  disabled?: boolean;
  onChange: (value: ActionResponsible[]) => void;
};

function resolveTeamMember(teamMembers: TeamMember[] | undefined, name: string): TeamMember | undefined {
  const normalized = name.trim();
  if (!normalized) return undefined;
  return teamMembers?.find((member) => member.member_name?.trim() === normalized);
}

export function ActionResponsiblesField({
  idPrefix = "pac-action-responsibles",
  value,
  teamMembers = [],
  disabled = false,
  onChange,
}: Props) {
  const selectedNames = value.map((item) => item.display_name);
  const extraNames = selectedNames.filter(
    (name) => !teamMembers.some((member) => member.member_name?.trim() === name.trim()),
  );
  const options = buildTeamMemberSelectOptions(teamMembers, extraNames);
  const linkedCount = value.filter((item) => item.user_id?.trim()).length;
  const unlinkedCount = value.length - linkedCount;

  function handleChange(names: string[]) {
    onChange(
      names.map((display_name) => {
        const member = resolveTeamMember(teamMembers, display_name);
        return {
          display_name: display_name.trim(),
          user_id: member?.member_user_id ?? null,
        };
      }),
    );
  }

  return (
    <div className="pac-field pac-field--full pac-action-responsibles">
      <MultiSelectField
        id={`${idPrefix}-team`}
        label="Responsáveis (equipe 8D)"
        hint={PAC_HELP_TOOLTIPS.form.actionResponsibles}
        options={options}
        selectedValues={selectedNames}
        onChange={handleChange}
        emptyLabel="Selecione um ou mais membros…"
        searchable
        disabled={disabled}
      />
      {value.length ? (
        <ActionResponsiblesChips responsibles={value} layout="stack" showQueueBadge />
      ) : null}
      {linkedCount > 0 ? (
        <p className="pac-muted pac-action-responsible__note">
          {linkedCount === 1
            ? "1 responsável vinculado entra na Minha fila e recebe alertas de prazo."
            : `${linkedCount} responsáveis vinculados entram na Minha fila e recebem alertas de prazo.`}
        </p>
      ) : unlinkedCount > 0 ? (
        <p className="pac-muted pac-action-responsible__note">
          {PAC_HELP_TOOLTIPS.form.actionResponsibleTeamUnlinked}
        </p>
      ) : null}
    </div>
  );
}
