import { Plus } from "lucide-react";

import type { EditableCriterion } from "../utils/catalogEditor";
import { AuditCatalogCriterionRow } from "./AuditCatalogCriterionRow";

type Props = {
  sensoOrder: number;
  sensoName: string;
  criteria: EditableCriterion[];
  onAdd: (sensoOrder: number) => void;
  onChange: (
    clientId: string,
    patch: Partial<Pick<EditableCriterion, "code" | "description" | "sort_order">>,
  ) => void;
  onRemove: (clientId: string) => void;
};

export function AuditCatalogEditor({
  sensoOrder,
  sensoName,
  criteria,
  onAdd,
  onChange,
  onRemove,
}: Props) {
  return (
    <section className="a5s-catalog-senso">
      <header className="a5s-catalog-senso__header">
        <div>
          <p className="a5s-catalog-senso__eyebrow">Senso {sensoOrder}</p>
          <h3 className="a5s-catalog-senso__title">{sensoName}</h3>
        </div>
        <button
          type="button"
          className="a5s-btn a5s-btn--ghost a5s-btn--small"
          onClick={() => onAdd(sensoOrder)}
        >
          <Plus size={16} aria-hidden />
          Adicionar critério
        </button>
      </header>

      <div className="a5s-catalog-senso__list">
        {criteria.length === 0 ? (
          <p className="a5s-catalog-senso__empty">
            Nenhum critério neste senso. Adicione ao menos um antes de publicar.
          </p>
        ) : (
          <>
            <div className="a5s-catalog-senso__list-head" aria-hidden>
              <span className="a5s-catalog-senso__list-head-cell a5s-catalog-senso__list-head-cell--index">
                #
              </span>
              <span className="a5s-catalog-senso__list-head-cell">Código</span>
              <span className="a5s-catalog-senso__list-head-cell">Descrição do critério</span>
              <span className="a5s-catalog-senso__list-head-cell a5s-catalog-senso__list-head-cell--action" />
            </div>
            {criteria.map((item, index) => (
              <AuditCatalogCriterionRow
                key={item.clientId}
                item={item}
                index={index + 1}
                onChange={onChange}
                onRemove={onRemove}
                canRemove={criteria.length > 1}
              />
            ))}
          </>
        )}
      </div>
    </section>
  );
}
