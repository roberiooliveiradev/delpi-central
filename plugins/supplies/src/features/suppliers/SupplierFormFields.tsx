import { Lock } from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";

import {
  SuppliesSectionHintLabel,
  SuppliesSelectField,
  SuppliesTextField,
} from "../../app/suppliesUi";
import {
  SUPPLIERS_CONTENT as C,
  supplierFieldMaxLengthHint,
} from "./content";
import {
  catalogLabelOf,
  isPreloadCatalog,
  useCatalogLabel,
  useCatalogOptions,
  useCatalogSearch,
} from "./supplierCatalogs";
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

type SupplierCatalogFieldProps = {
  spec: SupplierFieldSpec;
  /** Código atualmente selecionado (valor do draft). */
  value: string;
  /** Rótulo do valor atual quando ainda não resolvido pelo catálogo. */
  currentLabel?: string;
  /** Recebe (code, label) — necessário quando a seleção preenche outro campo. */
  onPick: (code: string, label: string) => void;
  /** Valor do campo do qual o catálogo depende (ex.: UF → municípios). */
  dependsOnValue?: string;
  disabled?: boolean;
  hint?: string;
};

/**
 * Campo alimentado por catálogo TOTVS (BFF `/suppliers/catalogs/<kind>`).
 * Catálogos pequenos usam `SuppliesSelectField` pesquisável (lista completa
 * cacheada); catálogos grandes/dependentes usam pesquisa remota limitada.
 * O formulário guarda sempre o código contratado — a descrição é só exibição.
 */
export function SupplierCatalogField({
  spec,
  value,
  currentLabel,
  onPick,
  dependsOnValue,
  disabled,
  hint,
}: SupplierCatalogFieldProps) {
  const kind = spec.catalog;
  if (!kind) return null;

  if (isPreloadCatalog(kind)) {
    return (
      <SupplierCatalogPreloadSelect
        spec={spec}
        kind={kind}
        value={value}
        currentLabel={currentLabel}
        onPick={onPick}
        disabled={disabled}
        hint={hint}
      />
    );
  }
  return (
    <SupplierCatalogSearchCombo
      spec={spec}
      kind={kind}
      value={value}
      currentLabel={currentLabel}
      onPick={onPick}
      dependsOnValue={dependsOnValue}
      disabled={disabled}
      hint={hint}
    />
  );
}

function SupplierCatalogPreloadSelect({
  spec,
  kind,
  value,
  currentLabel,
  onPick,
  disabled,
  hint,
}: SupplierCatalogFieldProps & { kind: NonNullable<SupplierFieldSpec["catalog"]> }) {
  const { options, loading, error } = useCatalogOptions(kind);
  const merged = [...options];
  const trimmed = value.trim();
  if (trimmed && !merged.some((o) => o.code === trimmed)) {
    // Preserva valor atual fora da lista (ex.: código legado desativado).
    merged.unshift({
      code: trimmed,
      label: currentLabel?.trim() || trimmed,
      disabled: false,
    });
  }
  return (
    <SuppliesSelectField
      label={spec.label}
      hint={error ? C.catalogError : (hint ?? spec.help)}
      searchable
      value={trimmed}
      options={merged.map((o) => ({
        value: o.code,
        label: `${o.label} · ${o.code}`,
      }))}
      allowEmpty
      emptyLabel={C.fieldEmptyOption}
      onChange={(code) => {
        const opt = merged.find((o) => o.code === code);
        onPick(code, opt?.label ?? "");
      }}
      disabled={disabled || loading}
    />
  );
}

function SupplierCatalogSearchCombo({
  spec,
  kind,
  value,
  currentLabel,
  onPick,
  dependsOnValue,
  disabled,
  hint,
}: SupplierCatalogFieldProps & { kind: NonNullable<SupplierFieldSpec["catalog"]> }) {
  const requiresDependency = Boolean(spec.catalogDependsOn);
  const dependencyReady = !requiresDependency || Boolean(dependsOnValue?.trim());
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const { options, hasMore, loading, error, search } = useCatalogSearch(kind, {
    state: dependsOnValue,
    enabled: dependencyReady && open && !disabled,
  });

  useEffect(() => {
    if (!open) return;
    const onMouseDown = (event: MouseEvent) => {
      if (!wrapperRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onMouseDown);
    return () => document.removeEventListener("mousedown", onMouseDown);
  }, [open]);

  const trimmed = value.trim();
  const label =
    catalogLabelOf(kind, trimmed) ?? currentLabel?.trim() ?? "";
  const merged = [...options];
  if (trimmed && !merged.some((o) => o.code === trimmed)) {
    merged.unshift({
      code: trimmed,
      label: label || trimmed,
      disabled: false,
    });
  }

  const pick = (code: string, optionLabel: string) => {
    onPick(code, optionLabel);
    setOpen(false);
    setActiveIndex(-1);
  };

  const onKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (!open) {
      if (event.key === "ArrowDown" || event.key === "Enter") {
        event.preventDefault();
        setOpen(true);
      }
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      setOpen(false);
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, merged.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      const opt = merged[activeIndex];
      pick(opt.code, opt.label);
    }
  };

  const comboDisabled = disabled || !dependencyReady;
  return (
    <div
      ref={wrapperRef}
      className={`sp-supplier-combo${open ? " sp-supplier-combo--open" : ""}`}
      onKeyDown={onKeyDown}
    >
      <span className="sp-supplier-combo__label">
        {hint ?? spec.help ? (
          <SuppliesSectionHintLabel
            label={spec.label}
            hint={hint ?? spec.help ?? ""}
          />
        ) : (
          spec.label
        )}
      </span>
      <button
        type="button"
        className="sp-supplier-combo__trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        disabled={comboDisabled}
        onClick={() => setOpen((current) => !current)}
      >
        <span className="sp-supplier-combo__trigger-text">
          {trimmed ? `${label || trimmed} · ${trimmed}` : C.catalogComboPlaceholder}
        </span>
      </button>
      {open ? (
        <div className="sp-supplier-combo__panel" role="presentation">
          <input
            type="search"
            className="sp-supplier-combo__search"
            placeholder={C.catalogSearchPlaceholder}
            aria-label={`${C.catalogSearchAriaLabel}: ${spec.label}`}
            onChange={(event) => {
              setActiveIndex(-1);
              search(event.target.value);
            }}
          />
          <ul className="sp-supplier-combo__list" role="listbox">
            {merged.length === 0 ? (
              <li className="sp-supplier-combo__empty">
                {error
                  ? C.catalogError
                  : loading
                    ? C.catalogLoading
                    : C.catalogEmpty}
              </li>
            ) : (
              merged.map((option, index) => (
                <li key={option.code}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={option.code === trimmed}
                    className={`sp-supplier-combo__option${
                      index === activeIndex
                        ? " sp-supplier-combo__option--active"
                        : ""
                    }`}
                    disabled={option.disabled}
                    onClick={() => pick(option.code, option.label)}
                  >
                    {option.label} · {option.code}
                  </button>
                </li>
              ))
            )}
          </ul>
          {hasMore ? (
            <p className="sp-supplier-combo__more">{C.catalogMoreHint}</p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

/**
 * Valor de consulta de um campo com catálogo — exibe "descrição · código"
 * quando o rótulo resolve; mantém o código original caso o catálogo esteja
 * indisponível ou o valor não conste na lista.
 */
export function SupplierCatalogViewValue({
  spec,
  value,
  dependsOnValue,
}: {
  spec: SupplierFieldSpec;
  value: string;
  dependsOnValue?: string;
}) {
  const trimmed = value.trim();
  const label = useCatalogLabel(
    spec.catalog ?? "states",
    trimmed,
    { state: dependsOnValue },
  );
  if (!spec.catalog || !trimmed) return <>{value}</>;
  return <>{label ? `${label} · ${trimmed}` : value}</>;
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
