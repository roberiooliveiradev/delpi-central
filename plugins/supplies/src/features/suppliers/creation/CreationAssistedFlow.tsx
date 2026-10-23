import { useEffect, useRef, useState } from "react";

import {
  navigatePluginPath,
} from "../../../app/pluginNavigation";
import { buildSupplierDetailPath } from "../../../app/pluginRoutes";
import {
  SuppliesActionButton,
  SuppliesSectionCard,
  SuppliesStateBanner,
} from "../../../app/suppliesUi";
import type { SupplierCreateDraft } from "../types";
import { createSupplierPreview } from "./api";
import { CREATION_CONTENT as C, mapCreationPreviewError } from "./content";
import { CreationSuggestionsPanel } from "./CreationSuggestionsPanel";
import {
  buildSuggestionEntries,
  isCnpjFormatValid,
  normalizeCnpjDigits,
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
  const requestSeq = useRef(0);
  const abortRef = useRef<AbortController | null>(null);

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
    onEntriesChange({});
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
    createSupplierPreview(cnpjDigits, controller.signal)
      .then((result) => {
        if (seq !== requestSeq.current) return;
        setPreview(result);
        onEntriesChange(buildSuggestionEntries(result));
        // tax_id/person_type vêm da entrada do usuário — não são dados externos.
        onApplyPatch({
          tax_id: cnpjDigits,
          person_type: result.person_type || "J",
        });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || seq !== requestSeq.current) return;
        setPreview(null);
        onEntriesChange({});
        setError(mapCreationPreviewError(err));
      })
      .finally(() => {
        if (seq === requestSeq.current) setLoading(false);
      });
  };

  const applyOne = (fieldKey: string, value: string) => {
    onApplyPatch({ [fieldKey]: value });
  };

  const applyAll = (list: readonly { field_key: string; suggested_value: string | null }[]) => {
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
                type="text"
                inputMode="numeric"
                autoComplete="off"
                value={cnpjInput}
                placeholder={C.cnpjInputPlaceholder}
                onChange={(event) => setCnpjInput(event.target.value)}
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
          <SuppliesStateBanner variant="error">
            <strong>{C.duplicatePossibleTitle}</strong>{" "}
            {C.duplicatePossibleMessage}
            {preview.duplicate_check.matches.length ? (
              <ul className="sp-supplier-create__assist-matches">
                {preview.duplicate_check.matches.map((match) => (
                  <li key={`${match.supplier_code}-${match.supplier_store}`}>
                    <a
                      href={buildSupplierDetailPath(
                        match.supplier_code ?? "",
                        match.supplier_store ?? "",
                        basePath,
                      )}
                      onClick={(event) => {
                        event.preventDefault();
                        navigatePluginPath(
                          buildSupplierDetailPath(
                            match.supplier_code ?? "",
                            match.supplier_store ?? "",
                            basePath,
                          ),
                        );
                      }}
                    >
                      {match.supplier_name || match.supplier_code}
                      {match.supplier_code
                        ? ` · ${match.supplier_code}/${match.supplier_store}`
                        : ""}
                      {match.state ? ` · ${match.state}` : ""}
                      {match.blocked ? ` · ${C.duplicateMatchBlocked}` : ""}
                    </a>
                  </li>
                ))}
              </ul>
            ) : null}
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
