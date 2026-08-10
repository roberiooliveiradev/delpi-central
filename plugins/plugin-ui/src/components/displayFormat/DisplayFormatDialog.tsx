import { useEffect, useMemo, useState } from "react";

import {
  DISPLAY_FORMAT_CATEGORIES,
  formatDisplayValue,
  presetsForCategory,
  specFromPresetId,
  type DisplayFormatCategory,
  type DisplayFormatSpec,
  type DisplayFormatTarget,
} from "../../displayFormat";
import { ActionButton } from "../actions/ActionButton";
import {
  createHostContainedModalShell,
  modalShellBemClasses,
} from "../feedback/ModalShell";
import { DisplayFormatTargetHint } from "./DisplayFormatTargetHint";
import { DEFAULT_DISPLAY_FORMAT_CN } from "./displayFormatClasses";

export type DisplayFormatDialogProps = {
  open: boolean;
  onClose: () => void;
  spec: DisplayFormatSpec;
  onApply: (spec: DisplayFormatSpec) => void;
  sampleValue?: unknown;
  target: DisplayFormatTarget;
  portalScopeClassName?: string;
};

export function DisplayFormatDialog({
  open,
  onClose,
  spec,
  onApply,
  sampleValue = 30,
  target,
  portalScopeClassName = "delpi-ui",
}: DisplayFormatDialogProps) {
  const cn = DEFAULT_DISPLAY_FORMAT_CN;
  const Modal = useMemo(
    () =>
      createHostContainedModalShell({
        prefix: "delpi-ui",
        classNames: modalShellBemClasses("delpi-ui"),
        portalScopeClassName,
        containedLayout: "dialog",
      }),
    [portalScopeClassName],
  );
  const [draft, setDraft] = useState<DisplayFormatSpec>(spec);

  useEffect(() => {
    if (open) setDraft(spec);
  }, [open, spec]);

  const types = draft.category === "custom" ? [] : presetsForCategory(draft.category);
  const preview = formatDisplayValue(sampleValue, draft);

  const selectCategory = (category: DisplayFormatCategory) => {
    if (category === "custom") {
      setDraft({
        category: "custom",
        presetId: "custom",
        pattern: draft.pattern?.trim() || inferPatternHint(draft),
      });
      return;
    }
    const meta = DISPLAY_FORMAT_CATEGORIES.find((item) => item.category === category);
    setDraft(specFromPresetId(meta?.defaultPresetId ?? category));
  };

  return (
    <Modal
      open={open}
      title="Formatar"
      onClose={onClose}
      footer={
        <div className={cn.footer}>
          <ActionButton variant="ghost" onClick={onClose}>
            Cancelar
          </ActionButton>
          <ActionButton
            variant="primary"
            onClick={() => {
              onApply(draft);
              onClose();
            }}
          >
            Aplicar
          </ActionButton>
        </div>
      }
    >
      <div className={cn.dialogBody}>
        <DisplayFormatTargetHint target={target} className={cn.dialogHint} />
        <div className={cn.dialogGrid}>
          <div className={cn.categoryList} role="listbox" aria-label="Categoria">
            {DISPLAY_FORMAT_CATEGORIES.map((item) => {
              const active = draft.category === item.category;
              return (
                <button
                  key={item.category}
                  type="button"
                  role="option"
                  aria-selected={active}
                  className={[cn.categoryBtn, active ? cn.categoryBtnActive : ""].filter(Boolean).join(" ")}
                  onClick={() => selectCategory(item.category)}
                >
                  {item.label}
                </button>
              );
            })}
          </div>
          <div>
            <div className={cn.sample}>
              <span className={cn.sampleLabel}>Exemplo</span>
              <strong className={cn.sampleValue}>{preview}</strong>
            </div>
            {draft.category === "custom" ? (
              <>
                <label className={cn.customField}>
                  Tipo (máscara)
                  <input
                    value={draft.pattern ?? ""}
                    onChange={(event) =>
                      setDraft({ category: "custom", presetId: "custom", pattern: event.target.value })
                    }
                    placeholder='"R$" #.##0,00'
                    aria-label="Máscara personalizada"
                  />
                </label>
                <p className={cn.customHelp}>
                  dd/mm/yyyy · HH:mm · 0,00% · 0,00E+00 — mm = mês; HH:mm → mm = minuto
                </p>
              </>
            ) : (
              <div className={cn.typeList} role="listbox" aria-label="Tipo">
                {types.map((preset) => {
                  const active = draft.presetId === preset.id;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      role="option"
                      aria-selected={active}
                      className={[cn.typeBtn, active ? cn.typeBtnActive : ""].filter(Boolean).join(" ")}
                      onClick={() => setDraft({ ...preset.spec, presetId: preset.id })}
                    >
                      <span>{preset.label}</span>
                      {preset.spec.pattern ? (
                        <span className={cn.typeMeta}>{preset.spec.pattern}</span>
                      ) : null}
                    </button>
                  );
                })}
              </div>
            )}
            <p className={cn.locale}>Localidade: Português (Brasil)</p>
          </div>
        </div>
      </div>
    </Modal>
  );
}

function inferPatternHint(spec: DisplayFormatSpec): string {
  if (spec.category === "date") return "dd/mm/yyyy";
  if (spec.category === "time") return "HH:mm";
  if (spec.category === "percent") return "0,0%";
  if (spec.category === "currency" || spec.category === "accounting") return '"R$" #.##0,00';
  if (spec.category === "scientific") return "0,00E+00";
  return "0,00";
}
