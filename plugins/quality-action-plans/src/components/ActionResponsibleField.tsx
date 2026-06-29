import { DelpiUserLinkSection } from "./DelpiUserLinkSection";
import { SelectField } from "./ui/SelectField";
import { TextField } from "./ui/TextField";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { TeamMember } from "../types/rnc8d";
import { buildTeamMemberSelectOptions } from "../utils/teamMemberOptions";
import type { SelectOption } from "./ui/types";

export type ActionResponsibleValue = {
  responsibleUserId: string | null;
  responsibleName: string;
};

type Props = {
  idPrefix?: string;
  value: ActionResponsibleValue;
  onChange: (value: ActionResponsibleValue) => void;
  /** Equipe 8D — vínculo Delpi é definido na seção 2; aqui só seleciona o membro. */
  teamMembers?: TeamMember[];
  teamOptions?: SelectOption[];
};

function resolveTeamMember(
  teamMembers: TeamMember[] | undefined,
  name: string,
): TeamMember | undefined {
  const normalized = name.trim();
  if (!normalized) return undefined;
  return teamMembers?.find((member) => member.member_name?.trim() === normalized);
}

export function ActionResponsibleField({
  idPrefix = "pac-action-responsible",
  value,
  onChange,
  teamMembers,
  teamOptions,
}: Props) {
  const usesTeamFlow = Boolean(teamMembers?.length || teamOptions);
  const options =
    teamOptions ??
    (teamMembers?.length ? buildTeamMemberSelectOptions(teamMembers, [value.responsibleName]) : undefined);

  function handleDirectoryLink(userId: string, displayName: string) {
    onChange({
      responsibleUserId: userId,
      responsibleName: displayName,
    });
  }

  function handleTeamChange(teamName: string) {
    const member = resolveTeamMember(teamMembers, teamName);
    onChange({
      responsibleUserId: member?.member_user_id ?? null,
      responsibleName: teamName,
    });
  }

  return (
    <div className="pac-field pac-field--full pac-action-responsible">
      {options ? (
        <SelectField
          id={`${idPrefix}-team`}
          label="Membro da equipe 8D"
          hint={PAC_HELP_TOOLTIPS.rnc8d.teamMemberSelect}
          options={options}
          value={value.responsibleName}
          onChange={handleTeamChange}
          searchable
          allowEmpty
          emptyLabel="Selecione…"
        />
      ) : null}

      {!usesTeamFlow ? (
        <DelpiUserLinkSection
          idPrefix={`${idPrefix}-directory`}
          userId={value.responsibleUserId}
          displayName={value.responsibleName}
          label="Vincular usuário Delpi"
          hint={PAC_HELP_TOOLTIPS.form.actionResponsibleUserLink}
          unlinkedNote="Sem vínculo com usuário Delpi — a ação não entra na Minha fila até selecionar alguém na pesquisa."
          onLink={handleDirectoryLink}
          onUnlink={() => onChange({ ...value, responsibleUserId: null })}
        />
      ) : null}

      <TextField
        id={`${idPrefix}-name`}
        label="Nome do responsável"
        hint={PAC_HELP_TOOLTIPS.form.actionResponsible}
        value={value.responsibleName}
        onChange={(responsibleName) => onChange({ ...value, responsibleName })}
      />

      {usesTeamFlow && !value.responsibleUserId ? (
        <p className="pac-muted pac-action-responsible__note">
          {PAC_HELP_TOOLTIPS.form.actionResponsibleTeamUnlinked}
        </p>
      ) : null}

      {value.responsibleUserId ? (
        <p className="pac-muted pac-action-responsible__note">
          {PAC_HELP_TOOLTIPS.form.actionResponsibleLinked}
        </p>
      ) : null}
    </div>
  );
}
