import {
  useRef,
  type CSSProperties,
  type KeyboardEvent,
  type ReactNode,
} from "react";

import { delpiUiClass } from "../../../utils/delpiUiClass";

import { NotApplicableOption } from "./NotApplicableOption";

export type RatingScaleValue = number | "na" | null;

export type RatingScaleEndLabels = {
  min: ReactNode;
  max: ReactNode;
};

export type RatingScaleProps = {
  /** `name` compartilhado por todas as opções (notas + N/A). */
  name: string;
  min: number;
  max: number;
  value: RatingScaleValue;
  onChange: (value: RatingScaleValue) => void;
  /** Nome acessível de cada nota (ex.: n => `${n} — Satisfeito`). */
  optionLabel: (value: number) => string;
  /** Textos das pontas da escala. */
  endLabels: RatingScaleEndLabels;
  endLabelsPosition?: "below" | "above";
  /** Colunas em tela estreita; padrão = quantidade de notas (0–10 usa 6). */
  narrowColumns?: number;
  /** Linha exibida só após escolher uma NOTA (nunca com "na"). */
  selectionCaption?: (value: number) => ReactNode;
  /** Renderiza a opção "não se aplica" no mesmo grupo. */
  notApplicable?: { label: string };
  /** Borda `--delpi-ui-danger` nos botões + `aria-invalid` nos `input`. */
  invalid?: boolean;
  /** Id de elemento que descreve o grupo (ex.: erro do cartão). */
  describedBy?: string;
  disabled?: boolean;
  prefix?: string;
  className?: string;
};

/**
 * Escala numérica genérica (1–5, 0–10…): um grupo `radio` nativo exclusivo
 * cujos `input` ficam recortados e o `label` vira o botão visual. Teclado:
 * setas/Home/End movem e escolhem dentro do grupo (natas via `preventDefault`
 * + foco/clique, determinístico inclusive em jsdom); Enter nunca envia.
 */
export function RatingScale({
  name,
  min,
  max,
  value,
  onChange,
  optionLabel,
  endLabels,
  endLabelsPosition = "below",
  narrowColumns,
  selectionCaption,
  notApplicable,
  invalid = false,
  describedBy,
  disabled = false,
  prefix = "ds",
  className,
}: RatingScaleProps) {
  const rowRef = useRef<HTMLDivElement>(null);

  const notes: number[] = [];
  for (let n = min; n <= max; n += 1) notes.push(n);

  const columns = narrowColumns ?? notes.length;
  const dense = max - min >= 10;
  // `value` pode ser 0 — comparação estrita, nunca truthiness.
  const numericValue = typeof value === "number" ? value : null;

  const cn = (suffix: string) =>
    delpiUiClass(`${prefix}-form-scale${suffix}`, `delpi-ui-form-scale${suffix}`);

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Enter") {
      // Enter nunca envia o formulário ao redor.
      event.preventDefault();
      return;
    }
    const radios = Array.from(
      rowRef.current?.querySelectorAll<HTMLInputElement>(
        'input[type="radio"]',
      ) ?? [],
    ).filter((radio) => !radio.disabled);
    const current = radios.indexOf(event.target as HTMLInputElement);
    if (current < 0) return;

    let next = -1;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      next = (current + 1) % radios.length;
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      next = (current - 1 + radios.length) % radios.length;
    } else if (event.key === "Home") {
      next = 0;
    } else if (event.key === "End") {
      next = radios.length - 1;
    }
    if (next < 0) return;

    event.preventDefault();
    radios[next].focus();
    radios[next].click();
  };

  const endsBlock = (
    <div className={cn("__ends")}>
      <span className={cn("__end")}>{endLabels.min}</span>
      <span className={cn("__end")}>{endLabels.max}</span>
    </div>
  );

  return (
    <div
      className={[
        cn(""),
        endLabelsPosition === "above" ? cn("--ends-above") : "",
        invalid ? cn("--invalid") : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      role="group"
      aria-describedby={describedBy}
    >
      <div
        ref={rowRef}
        className={cn("__options-row")}
        onKeyDown={handleKeyDown}
      >
        <div className={cn("__main")}>
          {endLabelsPosition === "above" && endsBlock}
          <div
            className={[
              cn("__options"),
              dense ? cn("__options--dense") : "",
            ]
              .filter(Boolean)
              .join(" ")}
            style={{ "--delpi-ui-form-scale-cols": columns } as CSSProperties}
          >
          {notes.map((note) => (
            <label key={note} className={cn("__option")}>
              <input
                type="radio"
                name={name}
                value={String(note)}
                className={cn("__input")}
                checked={value === note}
                onChange={() => onChange(note)}
                disabled={disabled}
                aria-label={optionLabel(note)}
                aria-invalid={invalid || undefined}
              />
              <span className={cn("__num")} aria-hidden="true">
                {note}
              </span>
            </label>
          ))}
          </div>
          {endLabelsPosition === "below" && endsBlock}
        </div>
        {numericValue != null && selectionCaption != null && (
          <p className={cn("__caption")}>{selectionCaption(numericValue)}</p>
        )}
        {notApplicable != null && (
          <>
            <span className={cn("__divider")} aria-hidden="true" />
            <NotApplicableOption
              name={name}
              label={notApplicable.label}
              checked={value === "na"}
              onChange={() => onChange("na")}
              disabled={disabled}
              invalid={invalid}
              prefix={prefix}
              className={cn("__na")}
            />
          </>
        )}
      </div>
    </div>
  );
}
