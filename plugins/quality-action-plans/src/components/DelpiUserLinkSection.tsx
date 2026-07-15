import { Search } from "lucide-react";
import { useState } from "react";

import type { DirectoryUser } from "../api/directoryApi";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import { formatPersonName } from "../utils/formatPersonName";
import { DelpiUserSearchModal } from "./ui/DelpiUserSearchModal";
import { TextField } from "./ui/TextField";
import { PAC_GHOST_BTN, pacGhostBtn } from "./ui/ghostChrome";

type Props = {
  idPrefix: string;
  userId: string | null | undefined;
  nameLabel: string;
  nameHint?: string;
  nameValue: string;
  onNameChange: (name: string) => void;
  linkedEmail?: string | null;
  linkHint?: string;
  unlinkedNote?: string;
  onLink: (userId: string, displayName: string, email?: string) => void;
  onUnlink: () => void;
};

export function DelpiUserLinkSection({
  idPrefix,
  userId,
  nameLabel,
  nameHint,
  nameValue,
  onNameChange,
  linkedEmail,
  linkHint = PAC_HELP_TOOLTIPS.rnc8d.teamMemberUserLink,
  unlinkedNote = PAC_HELP_TOOLTIPS.rnc8d.teamMemberUnlinked,
  onLink,
  onUnlink,
}: Props) {
  const [modalOpen, setModalOpen] = useState(false);
  const [sessionEmail, setSessionEmail] = useState<string | null>(null);

  const resolvedEmail = userId ? linkedEmail ?? sessionEmail : null;

  function handleSelect(user: DirectoryUser) {
    const name = formatPersonName(user.name) || user.email;
    setSessionEmail(user.email);
    onNameChange(name);
    onLink(user.id, name, user.email);
  }

  function handleUnlink() {
    setSessionEmail(null);
    onUnlink();
  }

  return (
    <div className="pac-user-link-section">
      <div className="pac-customer-section">
        <div className="pac-customer-section__toolbar">
          <button
            id={`${idPrefix}-search-trigger`}
            type="button"
            className={PAC_GHOST_BTN}
            aria-label="Pesquisar usuário na Delpi"
            onClick={() => setModalOpen(true)}
          >
            <Search size={16} aria-hidden="true" />
            Pesquisar usuário na Delpi
          </button>
          {userId ? (
            <button type="button" className={pacGhostBtn("danger")} onClick={handleUnlink}>
              Limpar vínculo
            </button>
          ) : null}
        </div>

        <TextField
          id={`${idPrefix}-name`}
          label={nameLabel}
          hint={nameHint ?? linkHint}
          value={nameValue}
          onChange={onNameChange}
        />
      </div>

      {resolvedEmail ? (
        <p className="pac-muted pac-user-link-section__email">
          E-mail Delpi: {resolvedEmail}
        </p>
      ) : null}

      {!userId ? <p className="pac-muted pac-user-link-section__note">{unlinkedNote}</p> : null}

      {userId ? (
        <p className="pac-muted pac-user-link-section__note">{PAC_HELP_TOOLTIPS.rnc8d.teamMemberLinked}</p>
      ) : null}

      <DelpiUserSearchModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        initialQuery={nameValue.trim() || undefined}
        onSelect={handleSelect}
      />
    </div>
  );
}
