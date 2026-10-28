import { Lock } from "lucide-react";
import {
  useEffect,
  useId,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  FieldLabel,
  textFieldBemClasses,
} from "@delpi/plugin-ui/index";
import {
  UI_PREFIX,
  SuppliesSectionHintLabel,
  SuppliesSelectField,
  SuppliesTextField,
} from "../../app/suppliesUi";
import {
  SUPPLIERS_CONTENT as C,
  supplierFieldMaxLengthHint,
} from "./content";
import {
  fetchPostalCodeSuggestion,
  isCompletePostalCode,
  normalizePostalDigits,
  reconcileMunicipality,
  type MunicipalityReconciliation,
  type PostalAddressSuggestion,
} from "./postalAddress";
import {
  supplierFieldAnchorId,
  supplierFieldItemClass,
} from "./query";
import {
  catalogDisplayText,
  catalogLabelOf,
  isPreloadCatalog,
  useCatalogLabel,
  useCatalogOptions,
  useCatalogSearch,
  type SupplierCatalogOption,
} from "./supplierCatalogs";
import {
  caretPosAfterDigits,
  digitsBeforePos,
  digitsOnly,
  formatTaxIdForPerson,
} from "./taxIdMask";
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
  /** Tipo de pessoa do draft — máscara CNPJ (J) / CPF (F) / dígitos. */
  personType?: string;
};

const TAX_FIELD_CLASSES = textFieldBemClasses(UI_PREFIX);

/**
 * CNPJ/CPF mascarado na apresentação; o draft segue só dígitos (payload
 * canônico intacto). Mesmas classes BEM do TextField do kit — o kit não
 * tem variante mascarada, então replicamos o shell e controlamos o caret.
 */
function SupplierTaxIdField({
  spec,
  value,
  onChange,
  disabled,
  showRequiredMark,
  hint,
  personType,
}: SupplierFieldInputProps) {
  const fieldId = useId();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const pendingCaret = useRef<number | null>(null);
  const label =
    showRequiredMark && spec.required ? `${spec.label} *` : spec.label;
  const maxDigits = personType === "F" ? 11 : spec.maxLength;
  const display = formatTaxIdForPerson(value, personType);

  useEffect(() => {
    if (pendingCaret.current == null) return;
    const pos = pendingCaret.current;
    pendingCaret.current = null;
    inputRef.current?.setSelectionRange(pos, pos);
  });

  return (
    <div className={TAX_FIELD_CLASSES.root}>
      <label htmlFor={fieldId} className={TAX_FIELD_CLASSES.labelWrapper}>
        <FieldLabel label={label} hint={hint ?? spec.help} />
      </label>
      <input
        id={fieldId}
        ref={inputRef}
        type="text"
        inputMode="numeric"
        autoComplete="off"
        className={TAX_FIELD_CLASSES.control}
        value={display}
        disabled={disabled}
        onChange={(event) => {
          const digits = digitsOnly(event.target.value, maxDigits);
          const sel = event.target.selectionStart;
          if (sel != null) {
            pendingCaret.current = caretPosAfterDigits(
              formatTaxIdForPerson(digits, personType),
              Math.min(digitsBeforePos(event.target.value, sel), digits.length),
            );
          }
          onChange(digits);
        }}
      />
    </div>
  );
}

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
  personType,
}: SupplierFieldInputProps) {
  const label =
    showRequiredMark && spec.required ? `${spec.label} *` : spec.label;

  if (spec.key === "tax_id") {
    return (
      <SupplierTaxIdField
        spec={spec}
        value={value}
        onChange={onChange}
        disabled={disabled}
        showRequiredMark={showRequiredMark}
        hint={hint}
        personType={personType}
      />
    );
  }

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
  /** Marca "*" no label quando a inclusão exige o campo (R6-FE). */
  showRequiredMark?: boolean;
  /** Código atualmente selecionado (valor do draft). */
  value: string;
  /** Rótulo do valor atual quando ainda não resolvido pelo catálogo. */
  currentLabel?: string;
  /** Recebe (code, label, item) — o item permite preencher o par composto. */
  onPick: (
    code: string,
    label: string,
    option?: SupplierCatalogOption,
  ) => void;
  /** Valor do campo do qual o catálogo depende (ex.: UF → municípios). */
  dependsOnValue?: string;
  /**
   * Valor do campo indicado por `spec.catalogCodeParam` — filtro exato
   * `code=` do catálogo (ex.: lojas do cliente vinculado).
   */
  codeFilter?: string;
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
  codeFilter,
  disabled,
  hint,
  showRequiredMark,
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
        showRequiredMark={showRequiredMark}
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
      codeFilter={codeFilter}
      disabled={disabled}
      hint={hint}
      showRequiredMark={showRequiredMark}
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
  showRequiredMark,
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
      label={
        showRequiredMark && spec.required ? `${spec.label} *` : spec.label
      }
      hint={error ? C.catalogError : (hint ?? spec.help)}
      searchable
      value={trimmed}
      options={merged.map((o) => ({
        value: o.code,
        label: catalogDisplayText(o.code, o.label),
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

type ComboItem = {
  /** Valor gravado no campo (code ou store conforme catalogValueField). */
  value: string;
  label: string;
  option: SupplierCatalogOption;
};

function comboItems(
  spec: SupplierFieldSpec,
  options: SupplierCatalogOption[],
): ComboItem[] {
  const valueField = spec.catalogValueField ?? "code";
  const out: ComboItem[] = [];
  const seen = new Set<string>();
  for (const option of options) {
    const itemValue =
      valueField === "store" ? (option.store ?? "").trim() : option.code.trim();
    if (!itemValue || seen.has(itemValue)) continue;
    seen.add(itemValue);
    out.push({ value: itemValue, label: option.label, option });
  }
  return out;
}

function SupplierCatalogSearchCombo({
  spec,
  kind,
  value,
  currentLabel,
  onPick,
  dependsOnValue,
  codeFilter,
  disabled,
  hint,
  showRequiredMark,
}: SupplierCatalogFieldProps & { kind: NonNullable<SupplierFieldSpec["catalog"]> }) {
  const requiresDependency = Boolean(spec.catalogDependsOn);
  const dependencyReady = !requiresDependency || Boolean(dependsOnValue?.trim());
  const requiresCode = Boolean(spec.catalogCodeParam);
  const codeReady = !requiresCode || Boolean(codeFilter?.trim());
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const { options, hasMore, loading, error, search } = useCatalogSearch(kind, {
    state: dependsOnValue,
    code: spec.catalogCodeParam ? codeFilter : undefined,
    enabled: dependencyReady && codeReady && open && !disabled,
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
  const merged = comboItems(spec, options);
  if (trimmed && !merged.some((o) => o.value === trimmed)) {
    merged.unshift({
      value: trimmed,
      label: label || trimmed,
      option: { code: trimmed, label: label || trimmed, disabled: false },
    });
  }

  const pick = (item: ComboItem) => {
    onPick(item.value, item.label, item.option);
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
      pick(opt);
    }
  };

  const comboDisabled = disabled || !dependencyReady || !codeReady;
  return (
    <div
      ref={wrapperRef}
      className={`sp-supplier-combo${open ? " sp-supplier-combo--open" : ""}`}
      onKeyDown={onKeyDown}
    >
      <span className="sp-supplier-combo__label">
        {hint ?? spec.help ? (
          <SuppliesSectionHintLabel
            label={
              showRequiredMark && spec.required
                ? `${spec.label} *`
                : spec.label
            }
            hint={hint ?? spec.help ?? ""}
          />
        ) : showRequiredMark && spec.required ? (
          `${spec.label} *`
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
          {trimmed ? catalogDisplayText(trimmed, label) : C.catalogComboPlaceholder}
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
              merged.map((item, index) => (
                <li key={`${item.value}|${item.option.store ?? ""}`}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={item.value === trimmed}
                    className={`sp-supplier-combo__option${
                      index === activeIndex
                        ? " sp-supplier-combo__option--active"
                        : ""
                    }`}
                    disabled={item.option.disabled}
                    onClick={() => pick(item)}
                  >
                    {catalogDisplayText(item.value, item.label)}
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

/** Campos do draft que a proposta de CEP pode preencher (só com confirmação). */
export type SupplierPostalApplyPatch = {
  postal_code?: string;
  address?: string;
  district?: string;
  state?: string;
  city?: string;
  city_code?: string;
};

type SupplierPostalCodeAssistantProps = {
  spec: SupplierFieldSpec;
  value: string;
  onChange: (value: string) => void;
  /** Aplica a proposta confirmada — o parent atualiza o draft (diff-only). */
  onApply: (patch: SupplierPostalApplyPatch) => void;
  /** Valores atuais para evidenciar sobrescrita antes da confirmação. */
  current: { address: string; district: string; city: string; state: string };
  disabled?: boolean;
  showRequiredMark?: boolean;
  hint?: string;
};

/**
 * CEP com consulta assistida (F5-UX-R4): busca explícita, proposta visível,
 * conciliação do município com o catálogo Protheus (CC2) e aplicação somente
 * mediante confirmação. Respostas de CEP diferente do campo atual nunca são
 * aplicadas; a digitação manual permanece disponível em qualquer estado.
 */
export function SupplierPostalCodeAssistant({
  spec,
  value,
  onChange,
  onApply,
  current,
  disabled,
  showRequiredMark,
  hint,
}: SupplierPostalCodeAssistantProps) {
  const [phase, setPhase] = useState<
    "idle" | "invalid" | "loading" | "found" | "notfound" | "error"
  >("idle");
  const [suggestion, setSuggestion] =
    useState<PostalAddressSuggestion | null>(null);
  const [recon, setRecon] = useState<MunicipalityReconciliation | null>(null);
  const [picked, setPicked] = useState<SupplierCatalogOption | null>(null);
  const seqRef = useRef(0);
  const abortRef = useRef<AbortController | null>(null);

  const digits = normalizePostalDigits(value);
  const suggestionMatchesField =
    suggestion !== null && suggestion.postal_code === digits;

  const search = () => {
    const seq = ++seqRef.current;
    abortRef.current?.abort();
    setSuggestion(null);
    setRecon(null);
    setPicked(null);
    if (!isCompletePostalCode(value)) {
      setPhase("invalid");
      return;
    }
    const controller = new AbortController();
    abortRef.current = controller;
    setPhase("loading");
    fetchPostalCodeSuggestion(digits, controller.signal)
      .then(async (result) => {
        if (seq !== seqRef.current || controller.signal.aborted) return;
        if (!result || !result.found) {
          setPhase("notfound");
          return;
        }
        setSuggestion(result);
        let reconciliation: MunicipalityReconciliation = {
          status: "unmatched",
        };
        try {
          reconciliation = await reconcileMunicipality(
            result.state,
            result.ibge_city_code,
            result.city,
          );
        } catch {
          /* catálogo indisponível → município fica para seleção manual */
        }
        if (seq !== seqRef.current) return;
        setRecon(reconciliation);
        setPhase("found");
      })
      .catch(() => {
        if (seq !== seqRef.current) return;
        setPhase("error");
      });
  };

  const reset = () => {
    seqRef.current += 1;
    abortRef.current?.abort();
    setPhase("idle");
    setSuggestion(null);
    setRecon(null);
    setPicked(null);
  };

  const apply = () => {
    if (!suggestion || !suggestionMatchesField) return;
    const patch: SupplierPostalApplyPatch = {
      postal_code: suggestion.postal_code,
    };
    if (suggestion.street.trim()) patch.address = suggestion.street.trim();
    if (suggestion.district.trim()) {
      patch.district = suggestion.district.trim();
    }
    if (suggestion.state.trim()) {
      patch.state = suggestion.state.trim().toUpperCase();
    }
    const municipality =
      recon?.status === "matched"
        ? recon
        : picked
          ? { status: "matched" as const, code: picked.code, label: picked.label }
          : null;
    if (municipality) {
      patch.city = municipality.label;
      patch.city_code = municipality.code;
    }
    onApply(patch);
    reset();
  };

  const label =
    showRequiredMark && spec.required ? `${spec.label} *` : spec.label;
  const municipalityPending =
    phase === "found" &&
    suggestionMatchesField &&
    (recon?.status === "unmatched" ||
      (recon?.status === "multiple" && !picked));

  const rows: { label: string; proposed: string; current: string }[] =
    suggestion && suggestionMatchesField
      ? [
          {
            label: C.postalFieldAddress,
            proposed: suggestion.street.trim(),
            current: current.address,
          },
          {
            label: C.postalFieldDistrict,
            proposed: suggestion.district.trim(),
            current: current.district,
          },
          {
            label: C.postalFieldState,
            proposed: suggestion.state.trim().toUpperCase(),
            current: current.state,
          },
          ...(recon?.status === "matched"
            ? [
                {
                  label: C.postalFieldCity,
                  proposed: recon.label,
                  current: current.city,
                },
              ]
            : picked
              ? [
                  {
                    label: C.postalFieldCity,
                    proposed: picked.label,
                    current: current.city,
                  },
                ]
              : []),
        ].filter((row) => row.proposed)
      : [];

  return (
    <div className="sp-postal">
      <SuppliesTextField
        label={label}
        hint={hint ?? spec.help}
        value={value}
        onChange={(raw) => onChange(raw.replace(/\D/g, ""))}
        disabled={disabled}
      />
      <div className="sp-postal__actions">
        <button
          type="button"
          className="sp-postal__search"
          onClick={search}
          disabled={disabled || phase === "loading"}
        >
          {phase === "loading"
            ? C.postalLookupLoading
            : C.postalLookupButton}
        </button>
        {phase !== "idle" && phase !== "loading" ? (
          <button
            type="button"
            className="sp-postal__discard"
            onClick={reset}
            disabled={disabled}
          >
            {C.postalDiscard}
          </button>
        ) : null}
      </div>
      {phase === "invalid" ? (
        <p className="sp-postal__feedback">{C.postalInvalid}</p>
      ) : null}
      {phase === "notfound" ? (
        <p className="sp-postal__feedback">{C.postalNotFound}</p>
      ) : null}
      {phase === "error" ? (
        <p className="sp-postal__feedback">{C.postalError}</p>
      ) : null}
      {phase === "found" && suggestion && suggestionMatchesField ? (
        <div className="sp-postal__card" role="group" aria-label={C.postalFoundTitle}>
          <p className="sp-postal__card-title">{C.postalFoundTitle}</p>
          <dl className="sp-postal__rows">
            {rows.map((row) => (
              <div key={row.label} className="sp-postal__row">
                <dt>{row.label}</dt>
                <dd>
                  {row.current.trim() &&
                  row.current.trim().toUpperCase() !==
                    row.proposed.toUpperCase() ? (
                    <>
                      <span className="sp-postal__old">{row.current}</span>
                      {" → "}
                    </>
                  ) : null}
                  <strong>{row.proposed}</strong>
                </dd>
              </div>
            ))}
          </dl>
          {recon?.status === "matched" || picked ? (
            <p className="sp-postal__note">{C.postalMunicipalityMatched}</p>
          ) : null}
          {recon?.status === "multiple" && !picked ? (
            <>
              <p className="sp-postal__note">
                {C.postalMunicipalityMultiple}
              </p>
              <ul className="sp-postal__options">
                {recon.options.map((option) => (
                  <li key={option.code}>
                    <button
                      type="button"
                      className="sp-postal__option"
                      onClick={() => setPicked(option)}
                    >
                      {catalogDisplayText(option.code, option.label)}
                    </button>
                  </li>
                ))}
              </ul>
            </>
          ) : null}
          {recon?.status === "unmatched" ? (
            <p className="sp-postal__note">
              {C.postalMunicipalityUnmatched}
            </p>
          ) : null}
          <div className="sp-postal__card-actions">
            <button
              type="button"
              className="sp-postal__apply"
              onClick={apply}
              disabled={
                disabled || (recon?.status === "multiple" && !picked)
              }
            >
              {C.postalApply}
            </button>
            {municipalityPending && recon?.status === "unmatched" ? (
              <span className="sp-postal__hint">
                {C.postalMunicipalityUnmatched}
              </span>
            ) : null}
          </div>
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
  return <>{catalogDisplayText(trimmed, label || null)}</>;
}

/**
 * Grade lógica de 12 colunas compartilhada entre consulta, criação e edição.
 * Tablet colapsa para 2 colunas e mobile para 1 (CSS em index.css).
 */
const SUPPLIER_FIELD_CONTROL_SELECTOR =
  "input, select, textarea, button, [tabindex]:not([tabindex=\"-1\"])";

type SupplierFieldShellProps = {
  spec: SupplierFieldSpec;
  /** Erro vigente do campo (validação local ou 422 do backend) — R6-FE. */
  error?: string;
  /** Marca a11y de obrigatoriedade — mesmo critério do "*" do label. */
  requiredMark?: boolean;
  /** Destaque de campo alterado (edição). */
  changed?: boolean;
  children: ReactNode;
};

/**
 * Invólucro de campo do formulário de fornecedor: âncora estável para o
 * resumo de erros, classe de inválido, mensagem associada e wiring ARIA
 * imperativo sobre o primeiro controle focável — o kit federado não
 * encaminha `aria-*` aos controles nativos (X4.PROD-C1.R6-FE).
 */
export function SupplierFieldShell({
  spec,
  error,
  requiredMark = false,
  changed = false,
  children,
}: SupplierFieldShellProps) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const anchorId = supplierFieldAnchorId(spec.key);
  const errorId = `${anchorId}-error`;
  const invalid = Boolean(error);
  const required = requiredMark && Boolean(spec.required);

  useEffect(() => {
    const control = rootRef.current?.querySelector<HTMLElement>(
      SUPPLIER_FIELD_CONTROL_SELECTOR,
    );
    if (!control) return;
    if (required) control.setAttribute("aria-required", "true");
    else control.removeAttribute("aria-required");
    if (invalid) {
      control.setAttribute("aria-invalid", "true");
      control.setAttribute("aria-describedby", errorId);
    } else {
      control.removeAttribute("aria-invalid");
      if (control.getAttribute("aria-describedby") === errorId) {
        control.removeAttribute("aria-describedby");
      }
    }
  });

  return (
    <div
      ref={rootRef}
      id={anchorId}
      data-supplier-field={spec.key}
      className={supplierFieldItemClass(spec, { changed, invalid, highlightRequired: requiredMark })}
    >
      {children}
      {error ? (
        <p id={errorId} className="sp-supplier-field__error">
          {error}
        </p>
      ) : null}
    </div>
  );
}

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
