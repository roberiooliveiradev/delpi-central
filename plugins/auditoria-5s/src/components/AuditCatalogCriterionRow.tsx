import { Trash2 } from "lucide-react";

import { FieldLabel } from "@delpi/plugin-ui";

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
      <div className="a5s-catalog-row__fields">
        <div className="a5s-catalog-row__code">
          <FieldLabel label="Código" htmlFor={`catalog-code-${item.clientId}`} />
          <input
            id={`catalog-code-${item.clientId}`}
            className="a5s-input"
            value={item.code}
            onChange={(event) => onChange(item.clientId, { code: event.target.value })}
            maxLength={20}
          />
        </div>
        <div className="a5s-catalog-row__description">
          <FieldLabel label="Descrição do critério" htmlFor={`catalog-desc-${item.clientId}`} />
          <textarea
            id={`catalog-desc-${item.clientId}`}
            className="a5s-textarea"
            rows={2}
            value={item.description}
            onChange={(event) => onChange(item.clientId, { description: event.target.value })}
          />
        </div>
      </div>
      <button
        type="button"
        className="a5s-btn a5s-btn--ghost a5s-catalog-row__remove"
        onClick={() => onRemove(item.clientId)}
        disabled={!canRemove}
        aria-label={`Remover critério ${item.code}`}
      >
        <Trash2 size={16} aria-hidden />
      </button>
    </article>
  );
}
