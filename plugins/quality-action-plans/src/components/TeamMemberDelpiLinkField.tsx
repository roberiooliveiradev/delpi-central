import { UserRound, X } from "lucide-react";
import { useCallback } from "react";

import { searchDirectoryUsers } from "../api/directoryApi";
import { QUALITY_ACTION_PLANS_APP_ID } from "../constants/actionPlans";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import { formatPersonName } from "../utils/formatPersonName";
import { DelpiAsyncLookupField, type DelpiLookupOption } from "./ui/DelpiAsyncLookupField";

type Props = {
  idPrefix: string;
  memberUserId: string | null | undefined;
  memberName: string;
  onLink: (userId: string, displayName: string) => void;
  onUnlink: () => void;
};

export function TeamMemberDelpiLinkField({
  idPrefix,
  memberUserId,
  memberName,
  onLink,
  onUnlink,
}: Props) {
  const searchUsers = useCallback(async (query: string, signal: AbortSignal) => {
    const users = await searchDirectoryUsers(query, {
      limit: 10,
      appId: QUALITY_ACTION_PLANS_APP_ID,
      signal,
    });
    return users.map(
      (user): DelpiLookupOption<{ email: string }> => ({
        value: user.id,
        label: `${formatPersonName(user.name) || user.email} · ${user.email}`,
        meta: { email: user.email },
      }),
    );
  }, []);

  function handleSelect(option: DelpiLookupOption<{ email: string }>) {
    const name = option.label.split(" · ")[0]?.trim() || option.label;
    onLink(option.value, name);
  }

  if (memberUserId) {
    return (
      <div className="pac-team-member-link pac-team-member-link--linked">
        <span className="pac-team-member-link__icon" aria-hidden="true">
          <UserRound size={16} />
        </span>
        <div className="pac-team-member-link__copy">
          <strong>{memberName || "Usuário vinculado"}</strong>
          <span className="pac-muted">{PAC_HELP_TOOLTIPS.rnc8d.teamMemberLinked}</span>
        </div>
        <button
          type="button"
          className="pac-ghost-btn pac-ghost-btn--icon pac-team-member-link__unlink"
          title="Remover vínculo com usuário Delpi"
          onClick={onUnlink}
        >
          <X size={16} aria-hidden="true" />
          <span>Desvincular</span>
        </button>
      </div>
    );
  }

  return (
    <div className="pac-team-member-link">
      <DelpiAsyncLookupField
        id={`${idPrefix}-directory`}
        label="Vincular usuário Delpi"
        hint={PAC_HELP_TOOLTIPS.rnc8d.teamMemberUserLink}
        value=""
        onChange={() => undefined}
        onSelect={handleSelect}
        searchOptions={searchUsers}
        placeholder="Buscar por nome ou e-mail…"
        minQueryLength={2}
      />
      <p className="pac-muted pac-team-member-link__note">
        {PAC_HELP_TOOLTIPS.rnc8d.teamMemberUnlinked}
      </p>
    </div>
  );
}
