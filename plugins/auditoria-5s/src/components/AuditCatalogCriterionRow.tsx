import { Trash2 } from "lucide-react";

import type { EditableCriterion } from "../utils/catalogEditor";

type Props = {
  item: EditableCriterion;
  index: number;
  onChange: (clientId: string, patch: Partial<Pick<EditableCriterion, "code" | "description" | "sort_order">>) => void;
  onRemove: (clientId: string) => void;
  canRemove: boolean;
};

export function AuditCatalogCriterionRow({
  item,
  index,
  onChange,
  onRemove,
  canRemove,
}: Props) {
  return (
    <article className="a5s-catalog-row">
      <div className="a5s-catalog-row__index" aria-hidden>
        {index}
      </div>
      <input
        id={`catalog-code-${item.clientId}`}
        className="a5s-catalog-row__input a5s-catalog-row__input--code"
        value={item.code}
        onChange={(event) => onChange(item.clientId, { code: event.target.value })}
        maxLength={20}
        aria-label={`Código do critério ${index}`}
        placeholder="Ex.: U01"
      />
      <textarea
        id={`catalog-desc-${item.clientId}`}
        className="a5s-catalog-row__input a5s-catalog-row__input--description"
        rows={3}
        value={item.description}
        onChange={(event) => onChange(item.clientId, { description: event.target.value })}
        aria-label={`Descrição do critério ${index}`}
        placeholder="Descreva o que será avaliado neste critério"
      />
      <button
        type="button"
        className="a5s-btn a5s-btn--ghost a5s-catalog-row__remove"
        onClick={() => onRemove(item.clientId)}
        disabled={!canRemove}
        aria-label={`Remover critério ${item.code || index}`}
      >
        <Trash2 size={16} aria-hidden />
      </button>
    </article>
  );
}
