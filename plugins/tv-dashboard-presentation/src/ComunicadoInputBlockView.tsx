import type { CSSProperties, ChangeEvent, PointerEvent as ReactPointerEvent, ReactNode } from "react";

import { resolveComunicadoLucideIcon } from "./comunicadoIconView";
import { resolveInputTargetScope } from "./comunicadoInputFilters";
import {
  INPUT_ICON_DEFAULT_SIZE_PX,
  INPUT_PART_DATA_ATTR,
  INPUT_PART_RESIZE_HANDLES,
  bindInputPartPointer,
  getInputPartState,
  isInputPartRefEqual,
  isInputPartVisible,
  inputPartAllowsResize,
  resolveInputBlockPaintCssVars,
  resolveInputControlPaintCssVars,
  resolveInputContrastBackground,
  resolveInputFrameStateWithDefaults,
  resolveInputIconBoxStyle,
  resolveInputPartFontSize,
  resolveInputPartFrame,
  resolveInputPartLayoutStyle,
  type ComunicadoInputInteraction,
  type ComunicadoInputPartRef,
  type ComunicadoInputPartResizeHandle,
} from "./comunicadoInputParts";
import type { ComunicadoInputBlock } from "./comunicadoTypes";
import { ensureComunicadoDualClass } from "@delpi/plugin-ui/index";

export type InputResolvedField = {
  type?: string;
  label?: string;
  description?: string;
  default?: string | number | boolean;
  optional?: boolean;
  enum?: Array<string | number | boolean>;
  format?: string;
};

export type InputControlKind = "select" | "boolean" | "number" | "date" | "text";

type Props = {
  block: ComunicadoInputBlock;
  /** Snapshot do schema (kiosk via enrich) ou resolvido no editor. */
  field?: InputResolvedField | null;
  value?: string | number | boolean | null;
  interactive?: boolean;
  paramAvailable?: boolean;
  /** Fontes alvo (para badge «N fontes»). */
  linkedSourceCount?: number;
  /** Refresh em andamento das fontes amarradas. */
  dataLoading?: boolean;
  interaction?: ComunicadoInputInteraction | null;
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

/** Tipo de controle no palco — só heurística do paramSchema (sem controlKind persistido). */
export function resolveInputControlKind(
  paramKey: string,
  field: InputResolvedField | null | undefined,
): InputControlKind {
  if (!field) return "text";
  if (field.type === "boolean") return "boolean";
  const rawEnum = Array.isArray(field.enum) ? field.enum.filter((item) => item != null) : [];
  if (rawEnum.length > 0) return "select";
  if (field.type === "integer" || field.type === "number") return "number";
  if (isDateField(paramKey, field)) return "date";
  return "text";
}

function partClass(
  kind: ComunicadoInputPartRef["kind"],
  selected: boolean,
  hasFrame: boolean,
): string {
  return ensureComunicadoDualClass(
    [
      `tdp-comunicado__input-block-part`,
      `tdp-comunicado__input-block-part--${kind}`,
      selected ? "tdp-comunicado__input-block-part--selected" : null,
      hasFrame ? "tdp-comunicado__input-block-part--framed" : null,
    ]
      .filter(Boolean)
      .join(" "),
  );
}

/** Controle de filtro no palco / kiosk — opções só do paramSchema da rota. */
export function ComunicadoInputBlockView({
  block,
  field,
  value,
  interactive = false,
  paramAvailable = true,
  linkedSourceCount,
  dataLoading = false,
  interaction = null,
  onChange,
  className,
  style,
}: Props) {
  const parts = block.inputParts;
  const paramKey = block.input?.paramKey ?? "";
  /** Sem paramKey = filtro não ligado. Schema ausente no enrich não bloqueia o controle. */
  const unavailable = !paramKey.trim();
  const effectiveField: InputResolvedField | null =
    field ??
    (!unavailable
      ? {
          type: "string",
          label: block.input?.label?.trim() || paramKey,
        }
      : null);
  const label =
    block.input?.label?.trim() || effectiveField?.label || paramKey || "Filtro";
  const current = value !== undefined ? value : (block.input?.defaultValue ?? null);
  const options = enumOptions(effectiveField);
  const scope = resolveInputTargetScope(block.input);
  const controlKind = resolveInputControlKind(paramKey, effectiveField);
  const schemaMissing = Boolean(paramKey.trim()) && !paramAvailable;
  const iconName = block.input?.iconName?.trim();
  const Icon = iconName ? resolveComunicadoLucideIcon(iconName) : null;
  const showIcon = Boolean(Icon) && isInputPartVisible(parts, { kind: "icon" });
  const showLabel = isInputPartVisible(parts, { kind: "label" });
  const showBadge = isInputPartVisible(parts, { kind: "badge" });
  const showControl = isInputPartVisible(parts, { kind: "control" });

  const scopeBadge =
    scope === "slide"
      ? "Filtro do slide"
      : `${linkedSourceCount ?? block.input?.targetSourceIds?.length ?? 0} fonte${
          (linkedSourceCount ?? block.input?.targetSourceIds?.length ?? 0) === 1 ? "" : "s"
        }`;

  const contrastBackground = resolveInputContrastBackground(parts, block.style);
  const frameState = resolveInputFrameStateWithDefaults(parts);
  const frameRadius =
    frameState.style?.borderRadius ?? block.style?.borderRadius ?? undefined;
  const paintVars = resolveInputBlockPaintCssVars(contrastBackground, {
    boxShadow: frameState.style?.boxShadow ?? block.style?.boxShadow,
    borderRadius: frameRadius,
  });
  const frameLayout = resolveInputPartLayoutStyle(frameState, {
    partKind: "frame",
    contrastBackground,
  });
  const rootStyle: CSSProperties = {
    ...style,
    ...paintVars,
    ...(frameLayout.background ? { background: frameLayout.background } : {}),
    ...(frameLayout.borderColor ? { borderColor: frameLayout.borderColor } : {}),
    ...(frameLayout.borderWidth ? { borderWidth: frameLayout.borderWidth } : {}),
    ...(frameLayout.borderStyle ? { borderStyle: frameLayout.borderStyle } : {}),
    borderRadius:
      frameLayout.borderRadius ??
      (frameRadius != null ? `${Math.max(0, frameRadius)}px` : undefined),
    ...(frameLayout.boxShadow ? { boxShadow: frameLayout.boxShadow } : {}),
  };

  const handleSelect = (event: ChangeEvent<HTMLSelectElement>) => {
    const next = event.target.value;
    if (effectiveField?.type === "boolean") {
      onChange?.(next === "true");
      return;
    }
    onChange?.(next === "" ? null : next);
  };

  const handleText = (event: ChangeEvent<HTMLInputElement>) => {
    const next = event.target.value;
    if (effectiveField?.type === "integer" || effectiveField?.type === "number") {
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

  const selected = interaction?.selectedPart ?? null;
  /** Editor com interaction: valor só clica quando a parte control está selecionada. */
  const controlValueInteractive =
    !interaction || isInputPartRefEqual(selected, { kind: "control" });
  const controlClass = ensureComunicadoDualClass(
    [
      "tdp-comunicado__input-block-control",
      `tdp-comunicado__input-block-control--${controlKind}`,
      controlValueInteractive ? null : "tdp-comunicado__input-block-control--hit-through",
    ]
      .filter(Boolean)
      .join(" "),
  );

  let controlNode: ReactNode = null;
  if (unavailable) {
    controlNode = (
      <span className={ensureComunicadoDualClass("tdp-comunicado__input-block-unavailable")}>
        Selecione o parâmetro no inspetor
      </span>
    );
  } else if (interactive) {
    const controlPointerStyle: CSSProperties | undefined = controlValueInteractive
      ? undefined
      : { pointerEvents: "none" };
    if (controlKind === "select" || controlKind === "boolean") {
      controlNode = (
        <select
          className={controlClass}
          style={controlPointerStyle}
          value={current === null || current === undefined ? "" : String(current)}
          onChange={handleSelect}
          onPointerDown={(event) => {
            // Isolar do drag do bloco / da parte — o clique deve abrir o seletor.
            event.stopPropagation();
          }}
          aria-label={label}
          disabled={dataLoading}
          tabIndex={controlValueInteractive ? undefined : -1}
        >
          <option value="">—</option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    } else {
      controlNode = (
        <input
          className={controlClass}
          style={controlPointerStyle}
          type={controlKind === "number" ? "number" : controlKind === "date" ? "date" : "text"}
          value={current === null || current === undefined ? "" : String(current)}
          onChange={handleText}
          onPointerDown={(event) => {
            event.stopPropagation();
          }}
          aria-label={label}
          placeholder={effectiveField?.description || paramKey}
          disabled={dataLoading}
          readOnly={!controlValueInteractive}
          tabIndex={controlValueInteractive ? undefined : -1}
        />
      );
    }
  } else {
    controlNode = (
      <span className={ensureComunicadoDualClass("tdp-comunicado__input-block-value")}>
        {current === null || current === undefined || current === "" ? "—" : String(current)}
      </span>
    );
  }

  const hasAnyPartFrame = ["icon", "label", "badge", "control"].some((kind) =>
    Boolean(resolveInputPartFrame(getInputPartState(parts, { kind } as ComunicadoInputPartRef))),
  );

  const renderPartChrome = (ref: ComunicadoInputPartRef) => {
    if (!interaction || !isInputPartRefEqual(selected, ref) || !inputPartAllowsResize(ref)) {
      return null;
    }
    return (
      <span className={ensureComunicadoDualClass("tdp-comunicado__input-part-handles")} aria-hidden>
        {INPUT_PART_RESIZE_HANDLES.map((handle) => (
          <button
            key={handle}
            type="button"
            className={ensureComunicadoDualClass(
              `tdp-comunicado__input-part-handle tdp-comunicado__input-part-handle--${handle}`,
            )}
            onPointerDown={(event: ReactPointerEvent) => {
              event.stopPropagation();
              interaction.onPartResizePointerDown?.(
                ref,
                event,
                handle as ComunicadoInputPartResizeHandle,
              );
            }}
          />
        ))}
      </span>
    );
  };

  const iconState = getInputPartState(parts, { kind: "icon" });
  const labelState = getInputPartState(parts, { kind: "label" });
  const badgeState = getInputPartState(parts, { kind: "badge" });
  const controlState = getInputPartState(parts, { kind: "control" });
  const iconBind = bindInputPartPointer({ kind: "icon" }, interaction);
  const labelBind = bindInputPartPointer({ kind: "label" }, interaction);
  const badgeBind = bindInputPartPointer({ kind: "badge" }, interaction);
  const controlBind = bindInputPartPointer({ kind: "control" }, interaction);
  const frameBind = bindInputPartPointer({ kind: "frame" }, interaction);

  const iconSize =
    iconState?.style?.iconSize != null && iconState.style.iconSize > 0
      ? iconState.style.iconSize
      : INPUT_ICON_DEFAULT_SIZE_PX;

  const labelFont = resolveInputPartFontSize("label", labelState?.style);
  const badgeFont = resolveInputPartFontSize("badge", badgeState?.style);
  const controlFont = resolveInputPartFontSize("control", controlState?.style);

  return (
    <div
      className={ensureComunicadoDualClass(
        [
          "tdp-comunicado__input-block",
          `tdp-comunicado__input-block--scope-${scope}`,
          dataLoading ? "tdp-comunicado__input-block--loading" : null,
          hasAnyPartFrame ? "tdp-comunicado__input-block--free-layout" : null,
          className,
        ]
          .filter(Boolean)
          .join(" "),
      )}
      style={rootStyle}
      data-param-key={paramKey || undefined}
      data-scope={scope}
      data-control={controlKind}
      {...{ [INPUT_PART_DATA_ATTR]: "frame" }}
      {...frameBind}
    >
      {showIcon && Icon ? (
        <span
          className={partClass(
            "icon",
            isInputPartRefEqual(selected, { kind: "icon" }),
            Boolean(resolveInputPartFrame(iconState)),
          )}
          style={resolveInputIconBoxStyle(iconState, contrastBackground)}
          {...{ [INPUT_PART_DATA_ATTR]: "icon" }}
          {...iconBind}
        >
          <Icon size={`${iconSize}px`} strokeWidth={2} />
          {renderPartChrome({ kind: "icon" })}
        </span>
      ) : null}

      {showLabel || showBadge ? (
        <span className={ensureComunicadoDualClass("tdp-comunicado__input-block-heading")}>
          {showLabel ? (
            <span
              className={partClass(
                "label",
                isInputPartRefEqual(selected, { kind: "label" }),
                Boolean(resolveInputPartFrame(labelState)),
              )}
              style={{
                ...resolveInputPartLayoutStyle(labelState, {
                  partKind: "label",
                  contrastBackground,
                }),
                fontSize: `${labelFont}px`,
              }}
              {...{ [INPUT_PART_DATA_ATTR]: "label" }}
              {...labelBind}
            >
              <span className={ensureComunicadoDualClass("tdp-comunicado__input-block-label-text")}>{label}</span>
              {renderPartChrome({ kind: "label" })}
            </span>
          ) : null}
          {showBadge ? (
            <span
              className={ensureComunicadoDualClass(
                [
                  partClass(
                    "badge",
                    isInputPartRefEqual(selected, { kind: "badge" }),
                    Boolean(resolveInputPartFrame(badgeState)),
                  ),
                  "tdp-comunicado__input-block-badge",
                ].join(" "),
              )}
              style={{
                ...resolveInputPartLayoutStyle(badgeState, {
                  partKind: "badge",
                  contrastBackground,
                }),
                fontSize: `${badgeFont}px`,
              }}
              title={scopeBadge}
              {...{ [INPUT_PART_DATA_ATTR]: "badge" }}
              {...badgeBind}
            >
              {scopeBadge}
              {renderPartChrome({ kind: "badge" })}
            </span>
          ) : null}
          {dataLoading ? (
            <span className={ensureComunicadoDualClass("tdp-comunicado__input-block-spinner")} aria-label="Atualizando dados" />
          ) : null}
        </span>
      ) : null}

      {showControl ? (
        <span
          className={partClass(
            "control",
            isInputPartRefEqual(selected, { kind: "control" }),
            Boolean(resolveInputPartFrame(controlState)),
          )}
          style={{
            ...resolveInputPartLayoutStyle(controlState, {
              partKind: "control",
              contrastBackground,
            }),
            ...resolveInputControlPaintCssVars(controlState),
            fontSize: `${controlFont}px`,
          }}
          {...{ [INPUT_PART_DATA_ATTR]: "control" }}
          {...controlBind}
        >
          {controlNode}
          {schemaMissing ? (
            <span
              className={ensureComunicadoDualClass("tdp-comunicado__input-block-schema-hint")}
              title="Schema da rota ausente no enrich — valor livre"
            >
              Valor livre
            </span>
          ) : null}
          {renderPartChrome({ kind: "control" })}
        </span>
      ) : null}
    </div>
  );
}
