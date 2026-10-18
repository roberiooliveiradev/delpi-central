import { ArrowDown, ArrowUp, Plus, X } from "lucide-react";
import { useMemo, useState } from "react";

import type { SequencingCriterionType } from "../types";
import {
  addCriterion,
  availableCriteria,
  moveCriterion,
  parseProductGroups,
  removeCriterion,
  type CriteriaEditorItem,
} from "../utils/sequencingProfiles";
import { copy } from "../content/copy";

type Props = {
  items: CriteriaEditorItem[];
  onChange: (items: CriteriaEditorItem[]) => void;
  disabled?: boolean;
};

const CRITERION_LABELS: Record<SequencingCriterionType, string> = {
  pa_due_date: "Entrega do PA",
  tool_group: "Ferramenta",
  material_code: "Código do cabo",
};

const CRITERION_HINTS: Record<SequencingCriterionType, string> = {
  pa_due_date:
    "Sempre o primeiro critério — a data de entrega do PA manda em tudo.",
  tool_group: "Agrupa operações que usam a mesma ferramenta.",
  material_code:
    "Agrupa operações que usam o mesmo cabo, pelo código exato do material.",
};

function MaterialGroupsField({
  item,
  index,
  disabled,
  onGroups,
}: {
  item: CriteriaEditorItem;
  index: number;
  disabled?: boolean;
  onGroups: (index: number, groups: string[]) => void;
}) {
  const texts = copy.sequencingProfiles.criteria;
  const [rejected, setRejected] = useState<string[]>([]);
  const value = item.groups.join(", ");
  return (
    <div className="seq-editor__groups">
      <label className="seq-editor__groups-label" htmlFor={`seq-groups-${index}`}>
        {texts.groupsLabel}
      </label>
      <textarea
        id={`seq-groups-${index}`}
        className="seq-input seq-editor__groups-input"
        rows={2}
        value={value}
        disabled={disabled}
        placeholder={texts.groupsPlaceholder}
        onChange={(event) => {
          const parsed = parseProductGroups(event.target.value);
          setRejected(parsed.rejected);
          onGroups(index, parsed.groups);
        }}
      />
      <p className="seq-editor__hint">{texts.groupsHint}</p>
      {rejected.length > 0 ? (
        <p className="seq-editor__warning" role="alert">
          {texts.groupsRejected(rejected.join(", "))}
        </p>
      ) : null}
      {item.groups.length === 0 ? (
        <p className="seq-editor__warning" role="alert">
          {texts.groupsRequired}
        </p>
      ) : null}
    </div>
  );
}

export function SequencingCriteriaEditor({ items, onChange, disabled }: Props) {
  const texts = copy.sequencingProfiles.criteria;
  const available = useMemo(() => availableCriteria(items), [items]);

  const handleGroups = (index: number, groups: string[]) => {
    onChange(items.map((item, i) => (i === index ? { ...item, groups } : item)));
  };

  return (
    <div className="seq-editor" aria-label={texts.label}>
      <ol className="seq-editor__list">
        {items.map((item, index) => {
          const locked = index === 0;
          return (
            <li key={item.type} className="seq-editor__item">
              <span className="seq-editor__order" aria-hidden>
                {index + 1}
              </span>
              <div className="seq-editor__body">
                <div className="seq-editor__head">
                  <strong>{CRITERION_LABELS[item.type]}</strong>
                  {locked ? (
                    <span className="seq-editor__locked">{texts.lockedFirst}</span>
                  ) : null}
                </div>
                <p className="seq-editor__hint">{CRITERION_HINTS[item.type]}</p>
                {item.type === "material_code" ? (
                  <MaterialGroupsField
                    item={item}
                    index={index}
                    disabled={disabled}
                    onGroups={handleGroups}
                  />
                ) : null}
              </div>
              <div className="seq-editor__actions">
                <button
                  type="button"
                  className="ppc-icon-btn"
                  disabled={disabled || locked || index <= 1}
                  title={texts.moveUp}
                  aria-label={`${texts.moveUp} ${CRITERION_LABELS[item.type]}`}
                  onClick={() => onChange(moveCriterion(items, index, -1))}
                >
                  <ArrowUp size={16} aria-hidden />
                </button>
                <button
                  type="button"
                  className="ppc-icon-btn"
                  disabled={disabled || locked || index >= items.length - 1}
                  title={texts.moveDown}
                  aria-label={`${texts.moveDown} ${CRITERION_LABELS[item.type]}`}
                  onClick={() => onChange(moveCriterion(items, index, 1))}
                >
                  <ArrowDown size={16} aria-hidden />
                </button>
                <button
                  type="button"
                  className="ppc-icon-btn"
                  disabled={disabled || locked}
                  title={texts.remove}
                  aria-label={`${texts.remove} ${CRITERION_LABELS[item.type]}`}
                  onClick={() => onChange(removeCriterion(items, index))}
                >
                  <X size={16} aria-hidden />
                </button>
              </div>
            </li>
          );
        })}
      </ol>
      {available.length > 0 ? (
        <div className="seq-editor__add">
          {available.map((type) => (
            <button
              key={type}
              type="button"
              className="seq-btn seq-btn--ghost"
              disabled={disabled}
              onClick={() => onChange(addCriterion(items, type))}
            >
              <Plus size={15} aria-hidden /> {texts.add} {CRITERION_LABELS[type]}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
