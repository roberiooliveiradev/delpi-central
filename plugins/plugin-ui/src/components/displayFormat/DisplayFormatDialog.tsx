import { useEffect, useMemo, useRef, useState } from "react";

import {
  DISPLAY_FORMAT_CATEGORIES,
  presetsForCategory,
  specFromPresetId,
  type DisplayFormatCategory,
  type DisplayFormatPreviewLoader,
  type DisplayFormatPreviewOption,
  type DisplayFormatPreviewResponse,
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
  /** Semantic type from backend/schema when known (date|datetime|number|…). */
  semanticType?: string | null;
  /** authoritative | representative | sample | none */
  valueSource?: "authoritative" | "representative" | "sample" | "none";
  /**
   * Server-owned catalog + previews. Required for canonical picker behaviour.
   * Without a loader the dialog cannot invent previews (no client formatter authority).
   */
  previewLoader?: DisplayFormatPreviewLoader;
  target: DisplayFormatTarget;
  /** Rótulo fino do alvo (ex.: Coluna "Qtd"). */
  targetHint?: string;
  portalScopeClassName?: string;
};

export function DisplayFormatDialog({
  open,
  onClose,
  spec,
  onApply,
  sampleValue = null,
  semanticType = null,
  valueSource = "authoritative",
  previewLoader,
  target,
  targetHint,
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
  const [previewPayload, setPreviewPayload] = useState<DisplayFormatPreviewResponse | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);
  const requestGen = useRef(0);

  useEffect(() => {
    if (open) {
      setDraft(spec);
      setApplyError(null);
    }
  }, [open, spec]);

  useEffect(() => {
    if (!open) return;
    if (!previewLoader) {
      setPreviewPayload(null);
      setLoadError("Pré-visualização indisponível (servidor não configurado).");
      setLoading(false);
      return;
    }
    const gen = ++requestGen.current;
    const controller = new AbortController();
    setLoading(true);
    setLoadError(null);
    void previewLoader({
      value: sampleValue,
      semanticType,
      locale: "pt-BR",
      valueSource,
      customPattern: draft.category === "custom" ? draft.pattern ?? "" : null,
      selectedSpec: draft,
    })
      .then((payload) => {
        if (gen !== requestGen.current) return;
        setPreviewPayload(payload);
        setLoading(false);
      })
      .catch((error: unknown) => {
        if (gen !== requestGen.current) return;
        setPreviewPayload(null);
        setLoading(false);
        setLoadError(error instanceof Error ? error.message : "Falha ao carregar formatos.");
      });
    return () => {
      controller.abort();
    };
  }, [
    open,
    previewLoader,
    sampleValue,
    semanticType,
    valueSource,
    draft.category,
    draft.presetId,
    draft.pattern,
    draft.decimalPlaces,
    draft.useThousandsSeparator,
  ]);

  const categoryOptions = useMemo(() => {
    if (!previewPayload) return [] as DisplayFormatPreviewOption[];
    if (draft.category === "custom") return [];
    return previewPayload.options.filter((item) => item.category === draft.category);
  }, [previewPayload, draft.category]);

  const selectedPreview = useMemo(() => {
    if (!previewPayload) return null;
    if (draft.category === "custom") return previewPayload.custom;
    const byId = draft.presetId
      ? previewPayload.options.find((item) => item.formatId === draft.presetId)
      : undefined;
    if (byId) return byId;
    return (
      previewPayload.options.find(
        (item) =>
          item.category === draft.category &&
          JSON.stringify(item.spec) === JSON.stringify(draft),
      ) ?? null
    );
  }, [previewPayload, draft]);

  const selectCategory = (category: DisplayFormatCategory) => {
    setApplyError(null);
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

  const canApply = Boolean(selectedPreview?.convertible) || draft.category === "general";

  const handleApply = () => {
    if (!previewLoader) {
      setApplyError("Não é possível aplicar sem pré-visualização do servidor.");
      return;
    }
    if (selectedPreview && !selectedPreview.convertible && draft.category !== "general") {
      setApplyError(
        selectedPreview.reason ?? "Não é possível aplicar este formato ao valor atual.",
      );
      return;
    }
    if (draft.category === "custom" && !String(draft.pattern ?? "").trim()) {
      setApplyError("Informe uma máscara personalizada válida.");
      return;
    }
    onApply(draft);
    onClose();
  };

  const samplePrimary = (() => {
    if (loading) return "Carregando…";
    if (loadError) return "Pré-visualização indisponível";
    if (!selectedPreview) return "—";
    if (!selectedPreview.convertible) {
      return selectedPreview.reason ?? "Não foi possível converter este valor.";
    }
    return selectedPreview.preview ?? "—";
  })();

  const sampleIsError = Boolean(
    !loading && (loadError || (selectedPreview && !selectedPreview.convertible)),
  );

  /* Fallback list labels only while loading — never used as format authority. */
  const fallbackTypes =
    draft.category === "custom" ? [] : presetsForCategory(draft.category);

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
          <ActionButton variant="primary" onClick={handleApply} disabled={!canApply && !loading}>
            Aplicar
          </ActionButton>
        </div>
      }
    >
      <div className={cn.dialogBody}>
        <DisplayFormatTargetHint target={target} label={targetHint} className={cn.dialogHint} />
        {valueSource === "sample" ? (
          <p className={cn.locale}>Pré-visualização com valor de exemplo (não é o dado real).</p>
        ) : null}
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
                  onPointerDown={(event) => event.stopPropagation()}
                >
                  {item.label}
                </button>
              );
            })}
          </div>
          <div>
            <div
              className={[cn.sample, sampleIsError ? cn.sampleError : ""].filter(Boolean).join(" ")}
              aria-live="polite"
            >
              <span className={cn.sampleLabel}>Exemplo</span>
              <strong className={cn.sampleValue}>{samplePrimary}</strong>
              {sampleIsError && sampleValue != null && sampleValue !== "" ? (
                <span className={cn.sampleDetail}>
                  Valor recebido: {summarizeValue(sampleValue)}
                </span>
              ) : null}
            </div>
            {applyError ? <p className={cn.applyError}>{applyError}</p> : null}
            {draft.category === "custom" ? (
              <>
                <label className={cn.customField}>
                  Tipo (máscara)
                  <input
                    value={draft.pattern ?? ""}
                    onChange={(event) =>
                      setDraft({
                        category: "custom",
                        presetId: "custom",
                        pattern: event.target.value,
                      })
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
                {loading && !categoryOptions.length
                  ? fallbackTypes.map((preset) => (
                      <div key={preset.id} className={cn.typeSkeleton} aria-hidden>
                        <span className={cn.typePreview}>…</span>
                        <span className={cn.typeMeta}>{preset.description ?? preset.label}</span>
                      </div>
                    ))
                  : null}
                {(categoryOptions.length ? categoryOptions : []).map((option) => {
                  const active = draft.presetId === option.formatId;
                  const disabled = !option.convertible;
                  return (
                    <button
                      key={option.formatId}
                      type="button"
                      role="option"
                      aria-selected={active}
                      aria-disabled={disabled}
                      disabled={disabled}
                      title={disabled ? option.reason ?? undefined : undefined}
                      className={[
                        cn.typeBtn,
                        active ? cn.typeBtnActive : "",
                        disabled ? cn.typeBtnDisabled : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      onClick={() => {
                        if (disabled) return;
                        setApplyError(null);
                        setDraft({ ...option.spec, presetId: option.formatId });
                      }}
                      onPointerDown={(event) => event.stopPropagation()}
                    >
                      <span className={cn.typePreview}>
                        {option.convertible
                          ? option.preview ?? "—"
                          : option.reason ?? "Não conversível"}
                      </span>
                      <span className={cn.typeMeta}>
                        {option.pattern ?? option.label}
                      </span>
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

function summarizeValue(value: unknown): string {
  const text = String(value);
  if (text.length <= 48) return `"${text}"`;
  return `"${text.slice(0, 45)}…"`;
}
