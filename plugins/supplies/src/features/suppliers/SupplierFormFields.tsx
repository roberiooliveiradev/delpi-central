import { Lock } from "lucide-react";
import type { ReactNode } from "react";

import {
  SuppliesSectionHintLabel,
  SuppliesSelectField,
  SuppliesTextField,
} from "../../app/suppliesUi";
import {
  SUPPLIERS_CONTENT as C,
  supplierFieldMaxLengthHint,
} from "./content";
import type {
  SupplierDetailSectionKey,
  SupplierFieldSpec,
} from "./types";

type SupplierFieldInputProps = {
  spec: SupplierFieldSpec;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  /** Marca "*" no label quando a inclusão exige o campo. */
  showRequiredMark?: boolean;
  /** Hint customizado (ex.: ajuda de edição). */
  hint?: string;
};

/**
 * Input de um campo do SUPPLIER_FIELD_REGISTRY — usado por criação e edição.
 * Aplica digitsOnly/uppercase/maxLength declarados no spec.
 */
export function SupplierFieldInput({
  spec,
  value,
  onChange,
  disabled,
  showRequiredMark,
  hint,
}: SupplierFieldInputProps) {
  const label =
    showRequiredMark && spec.required ? `${spec.label} *` : spec.label;

  if (spec.options) {
    return (
      <SuppliesSelectField
        label={label}
        hint={hint ?? spec.help}
        value={value}
        options={spec.options}
        allowEmpty
        emptyLabel={C.fieldEmptyOption}
        onChange={onChange}
        disabled={disabled}
      />
    );
  }

  return (
    <SuppliesTextField
      label={label}
      hint={
        hint ??
        [spec.help, supplierFieldMaxLengthHint(spec.maxLength)]
          .filter(Boolean)
          .join(" ")
      }
      value={value}
      onChange={(raw) => {
        let next = raw;
        if (spec.digitsOnly) next = next.replace(/\D/g, "");
        if (spec.uppercase) next = next.toUpperCase();
        onChange(next.slice(0, spec.maxLength));
      }}
      disabled={disabled}
    />
  );
}

/**
 * Grade lógica de 12 colunas compartilhada entre consulta, criação e edição.
 * Tablet colapsa para 2 colunas e mobile para 1 (CSS em index.css).
 */
export function SupplierFieldGrid({ children }: { children: ReactNode }) {
  return <div className="sp-supplier-fields">{children}</div>;
}

type SupplierDisplayFieldProps = {
  label: string;
  value: string;
  hint?: string;
  /** Texto para valor vazio (ex.: "Não informado"); padrão "—". */
  emptyLabel?: string;
  /** Valor indisponível na consulta (campo ausente no GET) — estilo atenuado. */
  unavailable?: boolean;
};

/** Exibição somente leitura de um campo cadastral — nunca um input desabilitado. */
export function SupplierDisplayField({
  label,
  value,
  hint,
  emptyLabel = "—",
  unavailable,
}: SupplierDisplayFieldProps) {
  const display = value.trim();
  return (
    <div className="sp-supplier-display">
      <span className="sp-supplier-display__label">
        {hint ? (
          <SuppliesSectionHintLabel label={label} hint={hint} />
        ) : (
          label
        )}
      </span>
      <span
        className={`sp-supplier-display__value${display ? "" : " sp-supplier-display__value--empty"}${unavailable ? " sp-supplier-display__value--unavailable" : ""}`}
      >
        {display || (unavailable ? C.fieldUnavailable : emptyLabel)}
      </span>
    </div>
  );
}

type SupplierProtectedFieldProps = SupplierDisplayFieldProps & {
  /** Campo de identidade/documento — sinalização de proteção discreta. */
  protected?: boolean;
};

/**
 * Campo imutável na edição (código, loja, documento) ou pendente de contrato
 * (readonly). Renderizado como informação protegida, nunca como input.
 */
export function SupplierProtectedField({
  label,
  value,
  hint,
  emptyLabel = "—",
  unavailable,
  protected: isProtected,
}: SupplierProtectedFieldProps) {
  const display = value.trim();
  return (
    <div
      className={`sp-supplier-display${isProtected ? " sp-supplier-display--protected" : ""}`}
    >
      <span className="sp-supplier-display__label">
        {isProtected ? (
          <Lock size={12} aria-hidden="true" className="sp-supplier-display__lock" />
        ) : null}
        {hint ? (
          <SuppliesSectionHintLabel label={label} hint={hint} />
        ) : (
          label
        )}
      </span>
      <span
        className={`sp-supplier-display__value${display ? "" : " sp-supplier-display__value--empty"}${unavailable ? " sp-supplier-display__value--unavailable" : ""}`}
      >
        {display || (unavailable ? C.fieldUnavailable : emptyLabel)}
      </span>
    </div>
  );
}

type SupplierFormActionsProps = {
  /** Texto do contador à esquerda (ex.: "3 alterações pendentes"); oculto se vazio. */
  counter?: string;
  children: ReactNode;
};

/** Barra de ações consistente: contador à esquerda, botões à direita. */
export function SupplierFormActions({
  counter,
  children,
}: SupplierFormActionsProps) {
  return (
    <div className="sp-supplier-actions">
      <span className="sp-supplier-actions__counter" aria-live="polite">
        {counter ?? ""}
      </span>
      <div className="sp-supplier-actions__buttons">{children}</div>
    </div>
  );
}

export type SupplierReviewRow = {
  label: string;
  /** Valor anterior; `undefined` no CREATE (não existe valor atual). */
  before?: string;
  after: string;
  /** Ajuda contextual do campo (tooltip oficial na label da linha). */
  help?: string;
};

export type SupplierReviewGroup = {
  section: SupplierDetailSectionKey;
  title: string;
  rows: SupplierReviewRow[];
};

/**
 * Tabela de revisão agrupada por seção — diff (valor atual × novo) no EDIT,
 * lista de campos a enviar no CREATE (sem coluna de valor atual).
 */
export function SupplierReviewTable({
  groups,
  showBefore,
}: {
  groups: SupplierReviewGroup[];
  showBefore: boolean;
}) {
  return (
    <div className="sp-supplier-review">
      {groups.map((group) => (
        <section key={group.section} className="sp-supplier-review__section">
          <h4 className="sp-supplier-review__title">{group.title}</h4>
          <table className="sp-supplier-diff">
            <thead>
              <tr>
                <th>Campo</th>
                {showBefore ? <th>Valor atual</th> : null}
                <th>{showBefore ? "Novo valor" : "Valor"}</th>
              </tr>
            </thead>
            <tbody>
              {group.rows.map((row) => (
                <tr key={row.label}>
                  <td>
                    {row.help ? (
                      <SuppliesSectionHintLabel
                        label={row.label}
                        hint={row.help}
                      />
                    ) : (
                      row.label
                    )}
                  </td>
                  {showBefore ? <td>{row.before?.trim() || "—"}</td> : null}
                  <td>{row.after.trim() || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
    </div>
  );
}
