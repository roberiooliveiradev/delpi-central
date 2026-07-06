import { Check, Circle } from "lucide-react";

import type { FormCompletion } from "../../utils/processoCompletion";

type Props = {
  completion: FormCompletion;
  title?: string;
  compact?: boolean;
};

export function ProcessoFormProgress({
  completion,
  title = "Preenchimento do cadastro",
  compact = false,
}: Props) {
  const { percent, done, total, items } = completion;

  if (compact) {
    return (
      <div className="tm-form-progress tm-form-progress--compact" aria-label={title}>
        <div
          className="tm-form-progress__bar"
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
          title={`${percent}% • ${done}/${total}`}
        >
          <span className="tm-form-progress__fill" style={{ width: `${percent}%` }} />
        </div>
        <span className="tm-form-progress__pct">{percent}%</span>
      </div>
    );
  }

  return (
    <div className="tm-form-progress" aria-label={title}>
      <div className="tm-form-progress__header">
        <span className="tm-form-progress__title">{title}</span>
        <span className="tm-form-progress__pct">
          {percent}% • {done}/{total}
        </span>
      </div>
      <div
        className="tm-form-progress__bar"
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <span className="tm-form-progress__fill" style={{ width: `${percent}%` }} />
      </div>
      <ul className="tm-form-progress__list">
        {items.map((item) => (
          <li
            key={item.id}
            className={
              item.done
                ? "tm-form-progress__item tm-form-progress__item--done"
                : "tm-form-progress__item"
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
