import { Check, Circle } from "lucide-react";

import { computeKaizenFormCompletion } from "../../utils/kaizenFormCompletion";
import type { KaizenFormValues } from "../../types/kaizen";

type Props = {
  values: KaizenFormValues;
};

export function KaizenFormProgress({ values }: Props) {
  const { percent, done, total, items } = computeKaizenFormCompletion(values);

  return (
    <div className="kz-form-progress" aria-label="Preenchimento do cadastro">
      <div className="kz-form-progress__header">
        <span className="kz-form-progress__title">Preenchimento do cadastro</span>
        <span className="kz-form-progress__pct">
          {percent}% • {done}/{total}
        </span>
      </div>
      <div
        className="kz-form-progress__bar"
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <span className="kz-form-progress__fill" style={{ width: `${percent}%` }} />
      </div>
      <ul className="kz-form-progress__list">
        {items.map((item) => (
          <li
            key={item.id}
            className={
              item.done
                ? "kz-form-progress__item kz-form-progress__item--done"
                : "kz-form-progress__item"
            }
          >
            {item.done ? (
              <Check size={13} aria-hidden="true" />
            ) : (
              <Circle size={13} aria-hidden="true" />
            )}
            <span>{item.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
