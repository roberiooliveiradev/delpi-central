import { useState } from "react";
import { Check } from "lucide-react";

import { CHECKLIST_HINT, CHECKLIST_TITLE } from "../content/catalog";
import type { GuideChecklistItem } from "../types/guide";

type GuideChecklistProps = {
  items: GuideChecklistItem[];
};

/**
 * Checklist de sessão — marca/desmarca no estado React, sem persistência.
 */
export function GuideChecklist({ items }: GuideChecklistProps) {
  const [checkedIds, setCheckedIds] = useState<ReadonlySet<string>>(
    () => new Set(),
  );

  function toggle(id: string) {
    setCheckedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <section className="gp-checklist" aria-labelledby="gp-checklist-title">
      <h2 className="gp-checklist__title" id="gp-checklist-title">
        {CHECKLIST_TITLE}
      </h2>
      <p className="gp-checklist__hint">{CHECKLIST_HINT}</p>
      <ul className="gp-checklist__list">
        {items.map((item) => {
          const checked = checkedIds.has(item.id);
          return (
            <li key={item.id}>
              <label
                className={
                  checked
                    ? "gp-checklist__item gp-checklist__item--checked"
                    : "gp-checklist__item"
                }
              >
                <input
                  className="gp-visually-hidden"
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggle(item.id)}
                />
                <span className="gp-checklist__box" aria-hidden="true">
                  {checked ? (
                    <Check size={14} strokeWidth={2.5} />
                  ) : null}
                </span>
                <span className="gp-checklist__label">{item.label}</span>
              </label>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
