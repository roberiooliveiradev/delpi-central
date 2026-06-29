import { UserRound, X } from "lucide-react";
import { useCallback } from "react";

import { searchDirectoryUsers } from "../api/directoryApi";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import { formatPersonName } from "../utils/formatPersonName";
import { DelpiAsyncLookupField, type DelpiLookupOption } from "./ui/DelpiAsyncLookupField";
import { SelectField } from "./ui/SelectField";
import { TextField } from "./ui/TextField";
import type { SelectOption } from "./ui/types";

export type ActionResponsibleValue = {
  responsibleUserId: string | null;
  responsibleName: string;
};

type Props = {
  idPrefix?: string;
  value: ActionResponsibleValue;
  onChange: (value: ActionResponsibleValue) => void;
  teamOptions?: SelectOption[];
};

export function ActionResponsibleField({
  idPrefix = "pac-action-responsible",
  value,
  onChange,
  teamOptions,
}: Props) {
  const searchUsers = useCallback(async (query: string, signal: AbortSignal) => {
    const users = await searchDirectoryUsers(query, 10, signal);
    return users.map(
      (user): DelpiLookupOption<{ email: string }> => ({
        value: user.id,
        label: `${formatPersonName(user.name) || user.email} · ${user.email}`,
        meta: { email: user.email },
      }),
    );
  }, []);

  function handleDirectorySelect(option: DelpiLookupOption<{ email: string }>) {
    const name = option.label.split(" · ")[0]?.trim() || option.label;
    onChange({
      responsibleUserId: option.value,
      responsibleName: name,
    });
  }

  function handleUnlink() {
    onChange({
      ...value,
      responsibleUserId: null,
    });
  }

  function handleTeamChange(teamName: string) {
    onChange({
      responsibleUserId: null,
      responsibleName: teamName,
    });
  }

  return (
    <div className="pac-field pac-field--full pac-action-responsible">
      {teamOptions ? (
        <SelectField
          id={`${idPrefix}-team`}
          label="Membro da equipe 8D"
          hint={PAC_HELP_TOOLTIPS.rnc8d.teamMemberSelect}
          options={teamOptions}
          value={value.responsibleName}
          onChange={handleTeamChange}
          searchable
          allowEmpty
          emptyLabel="Selecione…"
        />
      ) : null}

      {value.responsibleUserId ? (
        <div className="pac-action-responsible__linked">
          <span className="pac-action-responsible__linked-icon" aria-hidden="true">
            <UserRound size={16} />
          </span>
          <div className="pac-action-responsible__linked-copy">
            <strong>{value.responsibleName || "Usuário vinculado"}</strong>
            <span className="pac-muted">{PAC_HELP_TOOLTIPS.form.actionResponsibleLinked}</span>
          </div>
          <button
            type="button"
            className="pac-ghost-btn pac-ghost-btn--icon pac-action-responsible__unlink"
            title="Remover vínculo com usuário Delpi"
            onClick={handleUnlink}
          >
            <X size={16} aria-hidden="true" />
            <span>Desvincular</span>
          </button>
        </div>
      ) : (
        <DelpiAsyncLookupField
          id={`${idPrefix}-directory`}
          label="Vincular usuário Delpi"
          hint={PAC_HELP_TOOLTIPS.form.actionResponsibleUserLink}
          value=""
          onChange={() => undefined}
          onSelect={handleDirectorySelect}
          searchOptions={searchUsers}
          placeholder="Buscar por nome ou e-mail…"
          minQueryLength={2}
        />
      )}

      <TextField
        id={`${idPrefix}-name`}
        label="Nome do responsável"
        hint={PAC_HELP_TOOLTIPS.form.actionResponsible}
        value={value.responsibleName}
        onChange={(responsibleName) => onChange({ ...value, responsibleName })}
      />

      {!value.responsibleUserId ? (
        <p className="pac-muted pac-action-responsible__note">
          Sem vínculo com usuário Delpi — a ação não entra na Minha fila até buscar e selecionar alguém
          acima.
        </p>
      ) : null}
    </div>
  );
}
