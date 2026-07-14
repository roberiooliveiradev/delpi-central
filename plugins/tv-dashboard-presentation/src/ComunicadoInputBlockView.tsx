import type { CSSProperties, ChangeEvent } from "react";

import type { ComunicadoInputBlock } from "./comunicadoTypes";

export type InputResolvedField = {
  type?: string;
  label?: string;
  description?: string;
  default?: string | number | boolean;
  optional?: boolean;
  enum?: Array<string | number | boolean>;
  format?: string;
};

type Props = {
  block: ComunicadoInputBlock;
  /** Snapshot do schema (kiosk via enrich) ou resolvido no editor. */
  field?: InputResolvedField | null;
  value?: string | number | boolean | null;
  interactive?: boolean;
  paramAvailable?: boolean;
  onChange?: (value: string | number | boolean | null) => void;
  className?: string;
  style?: CSSProperties;
};

function enumOptions(field: InputResolvedField | null | undefined): Array<{ value: string; label: string }> {
  if (!field) return [];
  if (field.type === "boolean") {
    return [
      { value: "true", label: "Sim" },
      { value: "false", label: "Não" },
    ];
  }
  const raw = Array.isArray(field.enum) ? field.enum.filter((item) => item != null) : [];
  return raw.map((item) => ({ value: String(item), label: String(item) }));
}

function isDateField(key: string, field: InputResolvedField | null | undefined): boolean {
  if (!field) return false;
  const format = String(field.format || "").toLowerCase();
  if (format === "date" || format === "date-time") return true;
  return /date|data|from|to|inicio|fim/i.test(key);
}

/** Controle de filtro no palco / kiosk — opções só do paramSchema da rota. */
export function ComunicadoInputBlockView({
  block,
  field,
  value,
  interactive = false,
  paramAvailable = true,
  onChange,
  className,
  style,
}: Props) {
  const paramKey = block.input?.paramKey ?? "";
  const label = block.input?.label?.trim() || field?.label || paramKey || "Filtro";
  const current = value !== undefined ? value : (block.input?.defaultValue ?? null);
  const options = enumOptions(field);
  const unavailable = !paramAvailable || !paramKey;

  const handleSelect = (event: ChangeEvent<HTMLSelectElement>) => {
    const next = event.target.value;
    if (field?.type === "boolean") {
      onChange?.(next === "true");
      return;
    }
    onChange?.(next === "" ? null : next);
  };

  const handleText = (event: ChangeEvent<HTMLInputElement>) => {
    const next = event.target.value;
    if (field?.type === "integer" || field?.type === "number") {
      if (next === "") {
        onChange?.(null);
        return;
      }
      const parsed = Number(next);
      onChange?.(Number.isFinite(parsed) ? parsed : null);
      return;
    }
    onChange?.(next === "" ? null : next);
  };

  return (
    <div
      className={["tdp-comunicado__input-block", className].filter(Boolean).join(" ")}
      style={style}
      data-param-key={paramKey || undefined}
    >
      <label className="tdp-comunicado__input-block-label">
        <span className="tdp-comunicado__input-block-label-text">{label}</span>
        {unavailable ? (
          <span className="tdp-comunicado__input-block-unavailable">Parâmetro indisponível</span>
        ) : interactive ? (
          options.length > 0 ? (
            <select
              className="tdp-comunicado__input-block-control"
              value={current === null || current === undefined ? "" : String(current)}
              onChange={handleSelect}
              onPointerDown={(event) => event.stopPropagation()}
              aria-label={label}
            >
              <option value="">—</option>
              {options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : (
            <input
              className="tdp-comunicado__input-block-control"
              type={
                field?.type === "integer" || field?.type === "number"
                  ? "number"
                  : isDateField(paramKey, field)
                    ? "date"
                    : "text"
              }
              value={current === null || current === undefined ? "" : String(current)}
              onChange={handleText}
              onPointerDown={(event) => event.stopPropagation()}
              aria-label={label}
              placeholder={field?.description || paramKey}
            />
          )
        ) : (
          <span className="tdp-comunicado__input-block-value">
            {current === null || current === undefined || current === ""
              ? "—"
              : String(current)}
          </span>
        )}
      </label>
    </div>
  );
}
