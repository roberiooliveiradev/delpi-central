import { useEffect, useRef, useState } from "react";

import { CreationExistingSuppliersPanel } from "./CreationExistingSuppliersPanel";
import {
  SuppliesActionButton,
  SuppliesSectionCard,
  SuppliesStateBanner,
} from "../../../app/suppliesUi";
import type { SupplierCreateDraft } from "../types";
import {
  caretPosAfterDigits,
  digitsBeforePos,
  digitsOnly,
  formatCnpjDigits,
} from "../taxIdMask";
import { createSupplierPreview } from "./api";
import { CREATION_CONTENT as C, mapCreationPreviewError } from "./content";
import { CreationSuggestionsPanel } from "./CreationSuggestionsPanel";
import {
  buildSuggestionEntries,
  identityChangeCheck,
  isCnpjFormatValid,
  isIdentityCoherent,
  normalizeCnpjDigits,
  searchTaxIdChanged,
} from "./stateMachine";
import type {
  CreationMode,
  SupplierCreationPreview,
  SuggestionEntryMap,
} from "./types";

type CreationAssistedFlowProps = {
  basePath: string;
  draft: SupplierCreateDraft;
  disabled: boolean;
  entries: SuggestionEntryMap;
  onEntriesChange: (entries: SuggestionEntryMap) => void;
  /** Aplica um patch no draft da página (mesmo formulário, mesma revisão). */
  onApplyPatch: (patch: Partial<SupplierCreateDraft>) => void;
};

const MODES: readonly { id: CreationMode; label: string; hint: string }[] = [
  {
    id: "cnpj",
    label: C.modeCnpjLabel,
    hint: C.modeCnpjHint,
  },
  {
    id: "name",
    label: C.modeNameLabel,
    hint: C.modeNameHint,
  },
  {
    id: "manual",
    label: C.modeManualLabel,
    hint: C.modeManualHint,
  },
];

export function CreationAssistedFlow({
  basePath,
  draft,
  disabled,
  entries,
  onEntriesChange,
  onApplyPatch,
}: CreationAssistedFlowProps) {
  const [mode, setMode] = useState<CreationMode>("manual");
  const [cnpjInput, setCnpjInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<SupplierCreationPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  /** CNPJ (14 dígitos) da consulta em andamento ou do último preview válido. */
  const [activeTaxId, setActiveTaxId] = useState<string | null>(null);
  /** Tipo de pessoa retornado pela consulta ativa — parte da identidade. */
  const [activePersonType, setActivePersonType] = useState<string | null>(
    null,
  );
  const requestSeq = useRef(0);
  const abortRef = useRef<AbortController | null>(null);
  const cnpjInputRef = useRef<HTMLInputElement | null>(null);
  const pendingCaretRef = useRef<number | null>(null);
  // Ref do draft: o callback assíncrono sempre lê a versão mais recente.
  const draftRef = useRef(draft);
  useEffect(() => {
    draftRef.current = draft;
  }, [draft]);

  // Caret da máscara: após o render, reposiciona na fronteira de dígitos.
  useEffect(() => {
    if (pendingCaretRef.current == null) return;
    const pos = pendingCaretRef.current;
    pendingCaretRef.current = null;
    cnpjInputRef.current?.setSelectionRange(pos, pos);
  });

  // Resposta obsoleta nunca sobrescreve estado — abort + sequência.
  useEffect(
    () => () => {
      requestSeq.current += 1;
      abortRef.current?.abort();
    },
    [],
  );

  const cnpjDigits = normalizeCnpjDigits(cnpjInput);
  const cnpjValid = isCnpjFormatValid(cnpjInput);

  const resetPreview = () => {
    requestSeq.current += 1;
    abortRef.current?.abort();
    setPreview(null);
    setError(null);
    setActiveTaxId(null);
    setActivePersonType(null);
    onEntriesChange({});
  };

  const handleCnpjChange = (
    value: string,
    selectionStart: number | null,
  ) => {
    // Apresentação mascarada; a identidade continua sendo os 14 dígitos.
    const digits = digitsOnly(value, 14);
    const formatted = formatCnpjDigits(digits);
    if (selectionStart != null) {
      const before = Math.min(
        digitsBeforePos(value, selectionStart),
        digits.length,
      );
      pendingCaretRef.current = caretPosAfterDigits(formatted, before);
    }
    setCnpjInput(formatted);
    // Os 14 dígitos definem a identidade pesquisada: mudou → o preview
    // anterior (e qualquer requisição em andamento) é invalidado na hora.
    // Mudança só de máscara mantém o resultado.
    if (searchTaxIdChanged(value, activeTaxId)) {
      resetPreview();
    }
  };

  /**
   * Incorpora a identidade consultada ao draft — nunca silenciosamente.
   * Valor divergente em tax_id/person_type exige confirmação explícita;
   * cancelar preserva o draft e mantém as sugestões bloqueadas pela
   * incoerência de identidade (o painel reflete isso).
   */
  const confirmIdentity = (taxId: string, personType: string) => {
    if (!taxId) return;
    const check = identityChangeCheck(draftRef.current, taxId, personType);
    if (check.changedKeys.length > 0) {
      const message =
        check.filledFieldCount > 0
          ? C.identityReplaceConfirmWithFields
          : C.identityReplaceConfirm;
      if (!window.confirm(message)) return;
    }
    onApplyPatch({ tax_id: taxId, person_type: personType });
  };

  const selectMode = (next: CreationMode) => {
    if (next === mode) return;
    // Troca de modalidade descarta estado assistido — pede confirmação se
    // houver consulta em andamento, resultado ou CNPJ digitado. O draft
    // (valores já aplicados) sempre é preservado.
    const hasAssistedState = loading || preview !== null || cnpjDigits.length > 0;
    if (hasAssistedState && !window.confirm(C.modeSwitchConfirm)) return;
    abortRef.current?.abort();
    requestSeq.current += 1;
    setLoading(false);
    setPreview(null);
    setError(null);
    setActiveTaxId(null);
    setActivePersonType(null);
    setCnpjInput("");
    onEntriesChange({});
    setMode(next);
  };

  const consult = () => {
    if (!cnpjValid || loading) return;
    const seq = ++requestSeq.current;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError(null);
    // A resposta só é válida para este documento — a identidade ativa é
    // registrada no início para que qualquer mudança de dígitos a invalide.
    setActiveTaxId(cnpjDigits);
    createSupplierPreview(cnpjDigits, controller.signal)
      .then((result) => {
        if (seq !== requestSeq.current) return;
        setPreview(result);
        setActivePersonType(result.person_type || "J");
        onEntriesChange(buildSuggestionEntries(result));
        // Identidade: incorpora tax_id/person_type com confirmação quando
        // o draft já possui valor divergente — nunca sobrescreve em silêncio.
        confirmIdentity(cnpjDigits, result.person_type || "J");
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || seq !== requestSeq.current) return;
        setPreview(null);
        setActiveTaxId(null);
        setActivePersonType(null);
        onEntriesChange({});
        setError(mapCreationPreviewError(err));
      })
      .finally(() => {
        if (seq === requestSeq.current) setLoading(false);
      });
  };

  // Aplicação exige coerência completa (tax_id + person_type): sugestões
  // de outra identidade nunca entram no draft — guarda independente do
  // bloqueio visual do painel.
  const applyOne = (fieldKey: string, value: string) => {
    if (!isIdentityCoherent(draftRef.current, activeTaxId, activePersonType)) {
      return;
    }
    onApplyPatch({ [fieldKey]: value });
  };

  const applyAll = (list: readonly { field_key: string; suggested_value: string | null }[]) => {
    if (!isIdentityCoherent(draftRef.current, activeTaxId, activePersonType)) {
      return;
    }
    const patch: Partial<SupplierCreateDraft> = {};
    for (const e of list) {
      if (e.suggested_value) {
        (patch as Record<string, string>)[e.field_key] = e.suggested_value;
      }
    }
    onApplyPatch(patch);
  };

  return (
    <SuppliesSectionCard title={C.modeSelectorTitle}>
      <div className="sp-supplier-create__assist">
        <div
          className="sp-supplier-create__assist-modes"
          role="radiogroup"
          aria-label={C.modeSelectorTitle}
        >
          {MODES.map((option) => (
            <label
              key={option.id}
              className={`sp-supplier-create__assist-mode${mode === option.id ? " is-active" : ""}`}
            >
              <input
                type="radio"
                name="supplier-creation-mode"
                checked={mode === option.id}
                onChange={() => selectMode(option.id)}
                disabled={disabled}
              />
              <span className="sp-supplier-create__assist-mode-label">
                {option.label}
              </span>
              <span className="sp-supplier-create__assist-mode-hint">
                {option.hint}
              </span>
            </label>
          ))}
        </div>

        {mode === "name" ? (
          <SuppliesStateBanner variant="default">
            <strong>{C.modeNameUnavailableTitle}</strong>{" "}
            {C.modeNameUnavailableMessage}
          </SuppliesStateBanner>
        ) : null}

        {mode === "cnpj" ? (
          <div
            className="sp-supplier-create__assist-consult"
            aria-busy={loading}
          >
            <label className="sp-supplier-create__assist-cnpj">
              <span>{C.cnpjInputLabel}</span>
              <input
                ref={cnpjInputRef}
                type="text"
                inputMode="numeric"
                autoComplete="off"
                value={cnpjInput}
                placeholder={C.cnpjInputPlaceholder}
                onChange={(event) =>
                  handleCnpjChange(
                    event.target.value,
                    event.target.selectionStart,
                  )
                }
                disabled={disabled || loading}
                aria-invalid={cnpjInput.length > 0 && !cnpjValid}
              />
            </label>
            <div className="sp-supplier-create__assist-consult-actions">
              <SuppliesActionButton
                type="button"
                variant="primary"
                onClick={consult}
                disabled={disabled || loading || !cnpjValid}
              >
                {loading ? C.consultingAction : C.consultAction}
              </SuppliesActionButton>
              {preview || error ? (
                <SuppliesActionButton
                  type="button"
                  variant="ghost"
                  onClick={resetPreview}
                  disabled={disabled || loading}
                >
                  {C.newConsultAction}
                </SuppliesActionButton>
              ) : null}
            </div>
            {cnpjInput && !cnpjValid ? (
              <p className="sp-supplier-create__assist-error" role="alert">
                {C.cnpjInvalid}
              </p>
            ) : null}
          </div>
        ) : null}

        {error ? (
          <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner>
        ) : null}

        {preview?.duplicate_check.status === "CLEAR" ? (
          <SuppliesStateBanner variant="success">
            <strong>{C.duplicateClearTitle}</strong> {C.duplicateClearMessage}
          </SuppliesStateBanner>
        ) : null}
        {preview?.duplicate_check.status === "POSSIBLE_MATCH" ? (
          <SuppliesStateBanner variant="default">
            <strong>{C.duplicatePossibleTitle}</strong>{" "}
            {C.duplicatePossibleMessage}
            <CreationExistingSuppliersPanel
              key={activeTaxId ?? ""}
              basePath={basePath}
              taxId={activeTaxId ?? ""}
              initialMatches={preview.duplicate_check.matches}
              total={
                preview.duplicate_check.total ??
                preview.duplicate_check.matches.length
              }
              disabled={disabled}
            />
            <p className="sp-supplier-create__existing-footer">
              {C.duplicatePossibleFooter}
            </p>
          </SuppliesStateBanner>
        ) : null}
        {preview?.duplicate_check.status === "INCONCLUSIVE" ? (
          <SuppliesStateBanner variant="default">
            <strong>{C.duplicateInconclusiveTitle}</strong>{" "}
            {C.duplicateInconclusiveMessage}
          </SuppliesStateBanner>
        ) : null}

        {preview ? (
          <CreationSuggestionsPanel
            entries={entries}
            draft={draft}
            disabled={disabled}
            identityBlocked={
              !isIdentityCoherent(draft, activeTaxId, preview.person_type || "J")
            }
            onConfirmIdentity={() => {
              if (activeTaxId) {
                confirmIdentity(activeTaxId, preview.person_type || "J");
              }
            }}
            onApply={applyOne}
            onApplyAll={applyAll}
            confirmOverwrite={(label) =>
              window.confirm(`${label}: ${C.overwriteConfirm}`)
            }
          />
        ) : null}
      </div>
    </SuppliesSectionCard>
  );
}
