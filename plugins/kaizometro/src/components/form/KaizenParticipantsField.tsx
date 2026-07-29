import { Plus, Trash2 } from "lucide-react";
import { NativeSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";

import { PARTICIPANT_ROLES } from "../../constants/kaizen";
import type { KaizenParticipant, ParticipantRole } from "../../types/kaizen";
import { EmptyHint } from "../ui";
import { KZ_GHOST_BTN } from "../ui/ghostChrome";

type KaizenParticipantsFieldProps = {
  participants: KaizenParticipant[];
  onChange: (participants: KaizenParticipant[]) => void;
};

export function KaizenParticipantsField({ participants, onChange }: KaizenParticipantsFieldProps) {
  function update(index: number, patch: Partial<KaizenParticipant>) {
    onChange(participants.map((p, i) => (i === index ? { ...p, ...patch } : p)));
  }

  function remove(index: number) {
    onChange(participants.filter((_, i) => i !== index));
  }

  function add() {
    onChange([...participants, { name: "", role: "participante" }]);
  }

  return (
    <div className="kz-participants">
      {participants.length === 0 ? (
        <EmptyHint className="kz-participants__empty">
          Nenhum participante. Adicione o responsável e a equipe.
        </EmptyHint>
      ) : null}

      {participants.map((participant, index) => (
        <div className="kz-participant-row" key={index}>
          <NativeTextControl
            className="kz-participant-row__name"
            placeholder="Nome"
            aria-label={`Nome do participante ${index + 1}`}
            value={participant.name}
            maxLength={200}
            onChange={(name) => update(index, { name })}
          />
          <NativeSelectControl
            className="kz-participant-row__role"
            aria-label={`Papel do participante ${index + 1}`}
            value={participant.role}
            onChange={(role) => update(index, { role: role as ParticipantRole })}
            options={PARTICIPANT_ROLES}
          />
          <button
            type="button"
            className="kz-danger-btn"
            onClick={() => remove(index)}
            aria-label="Remover participante"
          >
            <Trash2 size={14} aria-hidden="true" />
          </button>
        </div>
      ))}

      <button type="button" className={`${KZ_GHOST_BTN} kz-participants__add`} onClick={add}>
        <Plus size={14} aria-hidden="true" />
        Adicionar participante
      </button>
    </div>
  );
}
