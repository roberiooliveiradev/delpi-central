import { Search } from "lucide-react";
import { useState, type DragEvent } from "react";

import type { DirectoryUser } from "../api/directoryApi";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { TeamMember } from "../types/rnc8d";
import { formatPersonName } from "../utils/formatPersonName";
import { FieldLabel } from "./ui/HelpTooltip";
import { DragHandle, type DragHandleProps, RemoveRowButton } from "./ui/RowActions";
import { TextField } from "./ui/TextField";
import { DelpiUserSearchModal } from "./ui/DelpiUserSearchModal";

type RowDropProps = {
  onDragOver: (event: DragEvent) => void;
  onDrop: (event: DragEvent) => void;
};

type Props = {
  index: number;
  member: TeamMember;
  rowClassName: string;
  rowDropProps: RowDropProps;
  canDrag: boolean;
  dragProps: DragHandleProps | null;
  removeDisabled: boolean;
  onChange: (member: TeamMember) => void;
  onLeaderToggle: (checked: boolean) => void;
  onRemove: () => void;
  excludedUserIds?: string[];
};

export function TeamMemberRow({
  index,
  member,
  rowClassName,
  rowDropProps,
  canDrag,
  dragProps,
  removeDisabled,
  onChange,
  onLeaderToggle,
  onRemove,
  excludedUserIds,
}: Props) {
  const [modalOpen, setModalOpen] = useState(false);
  const [sessionEmail, setSessionEmail] = useState<string | null>(null);

  const isLinked = Boolean(member.member_user_id);
  const linkedEmail = sessionEmail;

  function patch(updates: Partial<TeamMember>) {
    onChange({ ...member, ...updates });
  }

  function handleSelect(user: DirectoryUser) {
    const name = formatPersonName(user.name) || user.email;
    setSessionEmail(user.email);
    patch({
      member_user_id: user.id,
      member_name: name,
    });
  }

  function handleUnlink() {
    setSessionEmail(null);
    patch({ member_user_id: null });
  }

  return (
    <article className={rowClassName} {...rowDropProps}>
      <header className="pac-team-card__header">
        <div className="pac-team-card__heading">
          <span className="pac-team-card__index">Membro {index + 1}</span>
          {member.is_leader ? <span className="pac-team-card__leader-badge">Líder</span> : null}
        </div>
        <RemoveRowButton
          onRemove={onRemove}
          removeDisabled={removeDisabled}
          removeTitle={removeDisabled ? "Mantenha ao menos um membro" : "Remover membro"}
          removeAriaLabel="Remover membro da equipe"
        />
      </header>

      <div className="pac-team-card__body">
        <div className="pac-form-grid pac-team-card__fields">
          <div className="pac-team-card__drag" aria-hidden={!canDrag}>
            {canDrag && dragProps ? <DragHandle dragProps={dragProps} /> : null}
          </div>
          <div className="pac-field pac-team-card__name">
            <label className="pac-field__label" htmlFor={`rnc-team-name-${index}`}>
              <FieldLabel label="Nome" hint={PAC_HELP_TOOLTIPS.rnc8d.teamMemberUserLink} />
            </label>
            <input
              id={`rnc-team-name-${index}`}
              className="pac-field__control"
              type="text"
              value={member.member_name}
              placeholder="Nome do membro ou pesquise na Delpi…"
              onChange={(event) => patch({ member_name: event.target.value })}
            />
          </div>

          <TextField
            id={`rnc-team-dept-${index}`}
            className="pac-team-card__department"
            label="Área"
            hint={PAC_HELP_TOOLTIPS.rnc8d.teamMemberArea}
            value={member.department ?? ""}
            onChange={(department) => patch({ department })}
          />

          <div className="pac-team-card__delpi">
            <button
              type="button"
              className="pac-ghost-btn pac-team-card__delpi-btn"
              aria-label="Pesquisar usuário na Delpi"
              onClick={() => setModalOpen(true)}
            >
              <Search size={16} aria-hidden="true" />
              <span>Delpi</span>
            </button>
          </div>

          <label className="pac-checkbox pac-team-card__leader">
            <input
              type="checkbox"
              checked={Boolean(member.is_leader)}
              onChange={(event) => onLeaderToggle(event.target.checked)}
            />
            <FieldLabel label="Líder da equipe" hint={PAC_HELP_TOOLTIPS.rnc8d.teamLeader} />
          </label>
        </div>

        <p className="pac-team-card__link-status pac-muted">
          {isLinked ? (
            <>
              {linkedEmail ? <span>E-mail Delpi: {linkedEmail}</span> : null}
              {linkedEmail ? <span aria-hidden="true"> · </span> : null}
              <span>{PAC_HELP_TOOLTIPS.rnc8d.teamMemberLinked}</span>
              <button type="button" className="pac-text-btn pac-text-btn--danger" onClick={handleUnlink}>
                Desvincular
              </button>
            </>
          ) : (
            PAC_HELP_TOOLTIPS.rnc8d.teamMemberUnlinked
          )}
        </p>
      </div>

      <DelpiUserSearchModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        initialQuery={member.member_name.trim() || undefined}
        excludedUserIds={excludedUserIds}
        onSelect={handleSelect}
      />
    </article>
  );
}
