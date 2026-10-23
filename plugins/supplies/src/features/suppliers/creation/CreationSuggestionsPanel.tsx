import { SuppliesActionButton } from "../../../app/suppliesUi";
import { SUPPLIER_FIELD_REGISTRY } from "../types";
import type { SupplierCreateDraft } from "../types";
import {
  CREATION_CONTENT as C,
  formatRetrievedAt,
  providerDisplayName,
} from "./content";
import {
  pendingApplicableEntries,
  suggestionApplyDecision,
} from "./stateMachine";
import type { SuggestionEntry, SuggestionEntryMap } from "./types";

function suggestionFieldLabel(fieldKey: string): string {
  return (
    SUPPLIER_FIELD_REGISTRY.find((f) => f.key === fieldKey)?.label ??
    fieldKey
  );
}

const STATUS_LABEL: Record<SuggestionEntry["status"], string> = {
  SUGGESTED: C.statusSuggested,
  CONFIRMED: C.statusConfirmed,
  MANUALLY_CHANGED: C.statusChanged,
  UNAVAILABLE: C.statusUnavailable,
};

type SuggestionsPanelProps = {
  entries: SuggestionEntryMap;
  draft: SupplierCreateDraft;
  disabled: boolean;
  /**
   * Identidade do draft diverge do CNPJ consultado: sugestões ficam
   * visíveis, mas nenhuma ação de aplicação é oferecida.
   */
  identityBlocked: boolean;
  /** Confirma a substituição da identidade pelo CNPJ consultado. */
  onConfirmIdentity: () => void;
  /** Aplica o valor sugerido no draft — a page resolve confirmação. */
  onApply: (fieldKey: string, value: string) => void;
  /** Aplica todas as elegíveis de uma vez (campos vazios apenas). */
  onApplyAll: (entries: readonly SuggestionEntry[]) => void;
  /** Sobrescrever campo preenchido exige confirmação explícita. */
  confirmOverwrite: (fieldLabel: string) => boolean;
};

export function CreationSuggestionsPanel({
  entries,
  draft,
  disabled,
  identityBlocked,
  onConfirmIdentity,
  onApply,
  onApplyAll,
  confirmOverwrite,
}: SuggestionsPanelProps) {
  const list = Object.values(entries).filter(
    (e) => e.status !== "UNAVAILABLE",
  );
  const pending = pendingApplicableEntries(entries, draft);

  if (!list.length) {
    return (
      <div className="sp-supplier-create__assist-empty">
        <strong>{C.noSuggestionsTitle}</strong> {C.noSuggestionsMessage}
      </div>
    );
  }

  return (
    <div className="sp-supplier-create__assist-panel">
      <div className="sp-supplier-create__assist-head">
        <p className="sp-supplier-create__assist-desc">
          {C.suggestionsDescription}
        </p>
        {!identityBlocked && pending.length > 1 ? (
          <SuppliesActionButton
            type="button"
            variant="ghost"
            onClick={() => onApplyAll(pending)}
            disabled={disabled}
          >
            {C.applyAllAction} ({pending.length})
          </SuppliesActionButton>
        ) : null}
      </div>
      {identityBlocked ? (
        <div
          className="sp-supplier-create__assist-identity"
          role="alert"
        >
          <strong>{C.identityBlockedTitle}</strong>{" "}
          {C.identityBlockedMessage}{" "}
          <SuppliesActionButton
            type="button"
            variant="ghost"
            onClick={onConfirmIdentity}
            disabled={disabled}
          >
            {C.identityConfirmAction}
          </SuppliesActionButton>
        </div>
      ) : null}
      <ul className="sp-supplier-create__assist-list">
        {list.map((entry) => {
          const current = (
            draft[entry.field_key as keyof SupplierCreateDraft] ?? ""
          ).trim();
          const decision = suggestionApplyDecision(entry, current);
          const label = suggestionFieldLabel(entry.field_key);
          return (
            <li
              key={entry.field_key}
              className={`sp-supplier-create__assist-item sp-supplier-create__assist-item--${entry.status.toLowerCase()}`}
            >
              <div className="sp-supplier-create__assist-field">
                <span className="sp-supplier-create__assist-label">
                  {label}
                </span>
                <span
                  className={`sp-supplier-create__assist-badge sp-supplier-create__assist-badge--${entry.status.toLowerCase()}`}
                >
                  {STATUS_LABEL[entry.status]}
                </span>
              </div>
              <div className="sp-supplier-create__assist-value">
                {entry.suggested_value}
              </div>
              {current && current !== entry.suggested_value?.trim() ? (
                <div className="sp-supplier-create__assist-current">
                  {C.currentValueLabel}: {current}
                </div>
              ) : null}
              {entry.source ? (
                <div
                  className="sp-supplier-create__assist-source"
                  title={`${C.sourceLabel}: ${entry.source.provider_id}`}
                >
                  {C.sourceLabel}: {providerDisplayName(entry.source.provider_id)}{" "}
                  · {C.retrievedLabel}:{" "}
                  {formatRetrievedAt(entry.source.retrieved_at)}
                </div>
              ) : null}
              <div className="sp-supplier-create__assist-actions">
                {identityBlocked ? null : !entry.applicable ? (
                  <span className="sp-supplier-create__assist-note">
                    {C.reviewManually}
                  </span>
                ) : decision === "confirm_overwrite" ? (
                  <SuppliesActionButton
                    type="button"
                    variant="ghost"
                    onClick={() => {
                      if (
                        entry.suggested_value &&
                        confirmOverwrite(label)
                      ) {
                        onApply(entry.field_key, entry.suggested_value);
                      }
                    }}
                    disabled={disabled}
                  >
                    {C.applyOneAction}
                  </SuppliesActionButton>
                ) : decision === "apply" && entry.status !== "CONFIRMED" ? (
                  <SuppliesActionButton
                    type="button"
                    variant="ghost"
                    onClick={() =>
                      entry.suggested_value &&
                      onApply(entry.field_key, entry.suggested_value)
                    }
                    disabled={disabled}
                  >
                    {C.applyOneAction}
                  </SuppliesActionButton>
                ) : null}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
