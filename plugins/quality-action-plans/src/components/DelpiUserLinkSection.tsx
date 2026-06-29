import { Search } from "lucide-react";
import { useState } from "react";

import type { DirectoryUser } from "../api/directoryApi";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import { formatPersonName } from "../utils/formatPersonName";
import { DelpiUserSearchModal } from "./ui/DelpiUserSearchModal";
import { FieldLabel } from "./ui/HelpTooltip";
import { ReadOnlyField } from "./ui/ReadOnlyField";

type Props = {
  idPrefix: string;
  userId: string | null | undefined;
  displayName: string;
  linkedEmail?: string | null;
  label?: string;
  hint?: string;
  unlinkedNote?: string;
  onLink: (userId: string, displayName: string, email?: string) => void;
  onUnlink: () => void;
};

export function DelpiUserLinkSection({
  idPrefix,
  userId,
  displayName,
  linkedEmail,
  label = "Vincular usuário Delpi",
  hint = PAC_HELP_TOOLTIPS.rnc8d.teamMemberUserLink,
  unlinkedNote = PAC_HELP_TOOLTIPS.rnc8d.teamMemberUnlinked,
  onLink,
  onUnlink,
}: Props) {
  const [modalOpen, setModalOpen] = useState(false);
  const [sessionEmail, setSessionEmail] = useState<string | null>(null);

  const resolvedName = userId ? displayName || "Usuário vinculado" : "";
  const resolvedEmail = userId ? linkedEmail ?? sessionEmail ?? "—" : "";

  function handleSelect(user: DirectoryUser) {
    const name = formatPersonName(user.name) || user.email;
    setSessionEmail(user.email);
    onLink(user.id, name, user.email);
  }

  function handleUnlink() {
    setSessionEmail(null);
    onUnlink();
  }

  return (
    <div className="pac-user-link-section">
      <label className="pac-field__label" htmlFor={`${idPrefix}-search-trigger`}>
        <FieldLabel label={label} hint={hint} />
      </label>

      <div className="pac-customer-section">
        <div className="pac-customer-section__toolbar">
          <button
            id={`${idPrefix}-search-trigger`}
            type="button"
            className="pac-ghost-btn"
            onClick={() => setModalOpen(true)}
          >
            <Search size={16} aria-hidden="true" />
            Pesquisar usuário na Delpi
          </button>
          {userId ? (
            <button type="button" className="pac-ghost-btn pac-ghost-btn--danger" onClick={handleUnlink}>
              Limpar vínculo
            </button>
          ) : null}
        </div>

        <div className="pac-form-grid">
          <ReadOnlyField
            id={`${idPrefix}-delpi-name`}
            label="Nome Delpi"
            hint={PAC_HELP_TOOLTIPS.tables.directoryUserName}
            value={resolvedName || "—"}
          />
          <ReadOnlyField
            id={`${idPrefix}-delpi-email`}
            label="E-mail Delpi"
            hint={PAC_HELP_TOOLTIPS.tables.directoryUserEmail}
            value={resolvedEmail || "—"}
          />
        </div>
      </div>

      {!userId ? <p className="pac-muted pac-user-link-section__note">{unlinkedNote}</p> : null}

      {userId ? (
        <p className="pac-muted pac-user-link-section__note">{PAC_HELP_TOOLTIPS.rnc8d.teamMemberLinked}</p>
      ) : null}

      <DelpiUserSearchModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        initialQuery={displayName.trim() || undefined}
        onSelect={handleSelect}
      />
    </div>
  );
}
