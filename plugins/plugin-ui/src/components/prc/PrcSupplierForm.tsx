/** PRC-REF-023-UX-PARITY-FIX-02 — controles compartilhados do
 * formulário PRC, fonte única para Portal Engenharia e Minhas
 * Solicitações: justificativas contextuais (toggle/editor ≤250),
 * lookup SA2 com debounce/cancelamento e tabela de vínculos
 * (Busca | Código | Loja | Razão social | Nome fantasia | Part Number |
 * Catálogo | Ações). Classes neutras `delpi-prc__` (styles/delpi-prc.css).
 * A busca é injetada — cada MFE passa seu client da Engineering API. */

import { Fragment, useEffect, useRef, useState } from "react";
import { Search, Trash2, Undo2, X } from "lucide-react";
import { ActionButton } from "../actions/ActionButton";
import { IconButton } from "../actions/IconButton";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import {
  duplicateDraftRowIds,
  findRowWithOfficialKey,
  linkKeyOf,
  supplierHitMain,
  supplierHitSecondary,
  type SupplierRow,
} from "../../utils/prcProductRegistration";

export const PRC_REASON_MAX = 250;

/** Textos canônicos da busca e validação de fornecedores SA2. */
export const PRC_SUPPLIER_TEXT = {
  placeholder: "Buscar por código, razão social ou nome fantasia",
  partNumberHint:
    "Código de peça do produto no catálogo do fornecedor — obrigatório para vincular.",
  catalogHint:
    "Referência de catálogo informada pelo fornecedor, quando disponível.",
  partNumberRequired:
    "Part Number é obrigatório para vincular o fornecedor.",
  duplicateExisting:
    "Este fornecedor já está vinculado ao produto. Para alterar o Part Number ou Catálogo, edite a linha existente.",
  discardDraftOnly:
    "Descartar remove somente esta linha candidata — o vínculo oficial permanece intacto.",
  emptyResult: "Nenhum fornecedor encontrado para o termo pesquisado.",
  selectRequired:
    "Escolha um fornecedor na lista de resultados para confirmar o código e a loja.",
} as const;

/* ---------------- justificativas contextuais ---------------- */

export function PrcReasonToggle({
  id,
  value,
  open,
  onToggle,
  disabled,
  label = "Justificar",
}: {
  id: string;
  value: string;
  open: boolean;
  onToggle: () => void;
  disabled?: boolean;
  label?: string;
}) {
  const len = value.trim().length;
  return (
    <ActionButton
      variant="link"
      className="delpi-prc__reason-toggle"
      disabled={disabled}
      aria-expanded={open}
      aria-label={
        len
          ? `Editar justificativa (${len}/${PRC_REASON_MAX} caracteres)`
          : "Adicionar justificativa opcional"
      }
      title="Adicionar justificativa opcional"
      onClick={onToggle}
    >
      <span id={id}>{len ? "Editar justificativa" : label}</span>
      {len ? (
        <span className="delpi-prc__reason-filled">
          {len}/{PRC_REASON_MAX}
        </span>
      ) : null}
    </ActionButton>
  );
}

export function PrcReasonEditor({
  id,
  value,
  onChange,
  onCollapse,
  disabled,
  label = "Justificativa (opcional)",
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  onCollapse: () => void;
  disabled?: boolean;
  label?: string;
}) {
  const len = value.length;
  return (
    <div className="delpi-prc__reason" id={`${id}-editor`}>
      <label className="delpi-prc__reason-label" htmlFor={`${id}-text`}>
        {label}
      </label>
      <textarea
        id={`${id}-text`}
        className="delpi-prc__reason-input"
        rows={3}
        maxLength={PRC_REASON_MAX}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
      />
      <div className="delpi-prc__reason-footer">
        <span
          className={
            len >= PRC_REASON_MAX
              ? "delpi-prc__reason-count delpi-prc__reason-count--full"
              : "delpi-prc__reason-count"
          }
          aria-live="polite"
        >
          {len}/{PRC_REASON_MAX} caracteres
        </span>
        <span className="delpi-prc__reason-actions">
          <ActionButton
            variant="link"
            disabled={disabled}
            onClick={onCollapse}
          >
            Recolher
          </ActionButton>
          {value ? (
            <ActionButton
              variant="link"
              disabled={disabled}
              onClick={() => {
                onChange("");
                onCollapse();
              }}
            >
              Remover justificativa
            </ActionButton>
          ) : null}
        </span>
      </div>
    </div>
  );
}

/** Justificativa individual opcional, colapsada por padrão. */
export function PrcReasonField({
  id,
  value,
  onChange,
  disabled,
  label = "Justificar",
}: {
  id: string;
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
  label?: string;
}) {
  const [open, setOpen] = useState(Boolean(value));

  if (!open) {
    return (
      <PrcReasonToggle
        id={id}
        value={value}
        open={false}
        disabled={disabled}
        label={label}
        onToggle={() => setOpen(true)}
      />
    );
  }
  return (
    <PrcReasonEditor
      id={id}
      value={value}
      onChange={onChange}
      disabled={disabled}
      onCollapse={() => setOpen(false)}
    />
  );
}

/* ---------------- lookup SA2 ---------------- */

export type PrcSupplierHitLike = {
  supplier_code?: string;
  supplier_store?: string;
  supplier_name?: string;
  supplier_short_name?: string;
  [key: string]: unknown;
};

export type PrcSupplierSearchFn = (
  query: string,
  signal?: AbortSignal,
) => Promise<PrcSupplierHitLike[]>;

type LookupState = "idle" | "loading" | "error";

/** Busca SA2 oficial — debounce, cancelamento e descarte de resposta
 * obsoleta. `fetcher` resolve os hits via Engineering API do MFE. */
export function useSupplierSearch(
  query: string,
  fetcher: PrcSupplierSearchFn,
) {
  const [items, setItems] = useState<PrcSupplierHitLike[]>([]);
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<LookupState>("idle");
  const seq = useRef(0);
  const aborter = useRef<AbortController | null>(null);
  const fetcherRef = useRef(fetcher);
  useEffect(() => {
    fetcherRef.current = fetcher;
  });

  useEffect(() => {
    const q = query.trim();
    aborter.current?.abort();
    if (q.length < 2) {
      setItems([]);
      setOpen(false);
      setState("idle");
      return undefined;
    }
    const current = ++seq.current;
    setState("loading");
    const controller = new AbortController();
    aborter.current = controller;
    const timer = window.setTimeout(async () => {
      try {
        const items = await fetcherRef.current(q, controller.signal);
        if (current !== seq.current) return;
        setItems(items || []);
        setOpen(true);
        setState("idle");
      } catch {
        if (current !== seq.current) return;
        setState("error");
        setOpen(false);
      }
    }, 300);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  return { items, open, state, setOpen, setItems };
}

const MAX_VISIBLE = 8;

function SupplierSuggestPanel({
  open,
  anchorRef,
  panelRef,
  listId,
  items,
  activeIndex,
  emptyText,
  showEmpty,
  portalScopeClassName,
  onChoose,
  onDismiss,
}: {
  open: boolean;
  anchorRef: React.RefObject<HTMLDivElement | null>;
  panelRef: React.RefObject<HTMLDivElement | null>;
  listId: string;
  items: PrcSupplierHitLike[];
  activeIndex: number;
  emptyText: string;
  showEmpty: boolean;
  portalScopeClassName?: string;
  onChoose: (hit: PrcSupplierHitLike) => void;
  onDismiss: () => void;
}) {
  return (
    <AnchoredPanelPortal
      open={open}
      anchorRef={anchorRef}
      panelRef={panelRef}
      variant="bare"
      matchAnchorWidth
      allowFlip
      portalScopeClassName={portalScopeClassName}
      exclusive={false}
      onDismiss={onDismiss}
      role="presentation"
      className="delpi-prc__lookup-panel"
    >
      <ul
        id={listId}
        className="delpi-prc__lookup-list"
        role="listbox"
        aria-label="Fornecedores sugeridos"
      >
        {items.map((hit, i) => (
          <li
            key={`${hit.supplier_code}.${hit.supplier_store}.${i}`}
            id={`${listId}-opt-${i}`}
            role="option"
            aria-selected={i === activeIndex}
            className={
              i === activeIndex
                ? "delpi-prc__lookup-item delpi-prc__lookup-item--active"
                : "delpi-prc__lookup-item"
            }
          >
            <button
              type="button"
              className="delpi-prc__lookup-option"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => onChoose(hit)}
            >
              <span className="delpi-prc__lookup-legal">
                {supplierHitMain(hit)}
              </span>
              <span className="delpi-prc__lookup-meta">
                {supplierHitSecondary(hit)}
              </span>
            </button>
          </li>
        ))}
        {showEmpty ? (
          <li className="delpi-prc__lookup-empty">{emptyText}</li>
        ) : null}
      </ul>
    </AnchoredPanelPortal>
  );
}

/** Lookup SA2 na linha auxiliar da tabela de fornecedores. Seleção
 * oficial preenche código+loja+razão+fantasia; Escape ou clique externo
 * recolhe sem apagar a seleção. */
export function PrcSupplierCellLookup({
  id,
  query,
  disabled,
  searchSuppliers,
  portalScopeClassName,
  onQueryChange,
  onSelect,
  onClose,
}: {
  id: string;
  query: string;
  disabled?: boolean;
  searchSuppliers: PrcSupplierSearchFn;
  portalScopeClassName?: string;
  onQueryChange: (v: string) => void;
  onSelect: (hit: PrcSupplierHitLike) => void;
  onClose: () => void;
}) {
  const { items, open, state, setOpen } = useSupplierSearch(
    query,
    searchSuppliers,
  );
  const [activeIndex, setActiveIndex] = useState(-1);
  const anchorRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  });
  const listId = `${id}-list`;
  const visible = items.slice(0, MAX_VISIBLE);

  useEffect(() => {
    setActiveIndex(visible.length ? 0 : -1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    const onDocMouseDown = (e: MouseEvent) => {
      const t = e.target as Node;
      if (
        anchorRef.current?.contains(t) ||
        panelRef.current?.contains(t)
      ) {
        return;
      }
      if (
        t instanceof Element &&
        (t.closest(".delpi-prc__supplier-aux") ||
          t.closest(".delpi-prc__search-toggle"))
      ) {
        return;
      }
      onCloseRef.current();
    };
    document.addEventListener("mousedown", onDocMouseDown);
    return () =>
      document.removeEventListener("mousedown", onDocMouseDown);
  }, []);

  const choose = (hit: PrcSupplierHitLike) => {
    onSelect(hit);
    setOpen(false);
  };
  const lookupKeys = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!open) setOpen(true);
      else setActiveIndex((i) => Math.min(i + 1, visible.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (
      e.key === "Enter" &&
      open &&
      activeIndex >= 0 &&
      visible[activeIndex]
    ) {
      e.preventDefault();
      choose(visible[activeIndex]);
    }
  };
  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      onCloseRef.current();
      return;
    }
    lookupKeys(e);
  };

  return (
    <div
      ref={anchorRef}
      className="delpi-prc__lookup"
      role="combobox"
      aria-expanded={open}
      aria-haspopup="listbox"
      aria-owns={listId}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) setOpen(false);
      }}
    >
      <input
        ref={inputRef}
        id={id}
        type="text"
        className="delpi-prc__lookup-input"
        placeholder={PRC_SUPPLIER_TEXT.placeholder}
        value={query}
        disabled={disabled}
        aria-label="Buscar fornecedor por código, razão social ou nome fantasia"
        aria-autocomplete="list"
        aria-controls={listId}
        aria-activedescendant={
          activeIndex >= 0 ? `${listId}-opt-${activeIndex}` : undefined
        }
        autoComplete="off"
        onChange={(e) => onQueryChange(e.target.value)}
        onKeyDown={onKeyDown}
        onFocus={() => {
          if (visible.length) setOpen(true);
        }}
      />
      {state === "loading" ? (
        <span className="delpi-prc__muted">Buscando…</span>
      ) : null}
      {state === "error" ? (
        <span className="delpi-prc__field-error" role="alert">
          Busca indisponível — tente novamente.
        </span>
      ) : null}
      <SupplierSuggestPanel
        open={open && state !== "loading"}
        anchorRef={anchorRef}
        panelRef={panelRef}
        listId={listId}
        items={visible}
        activeIndex={activeIndex}
        emptyText={PRC_SUPPLIER_TEXT.emptyResult}
        showEmpty={open && !visible.length && state === "idle"}
        portalScopeClassName={portalScopeClassName}
        onChoose={choose}
        onDismiss={() => setOpen(false)}
      />
    </div>
  );
}

/* ---------------- tabela de vínculos ---------------- */

export type PrcBaselineLink = {
  supplierCode: string;
  store: string;
  supplierName?: string | null;
  partNumber?: string | null;
  catalogNumber?: string | null;
};

export type PrcSupplierTableProps = {
  suppliers: SupplierRow[];
  removeMarks: Set<string>;
  baselineLinks: PrcBaselineLink[];
  requestType: "create" | "update";
  busy?: boolean;
  errorsVisible?: boolean;
  partNumberLabel: string;
  catalogLabel: string;
  searchSuppliers: PrcSupplierSearchFn;
  portalScopeClassName?: string;
  onPatchRow: (rowId: string, patch: Partial<SupplierRow>) => void;
  onToggleSearch: (rowId: string) => void;
  onCloseSearch: (rowId: string) => void;
  onToggleReason: (
    rowId: string,
    flag: "pnReasonOpen" | "catReasonOpen" | "opReasonOpen",
  ) => void;
  onSetReason: (
    rowId: string,
    flag: "pnReason" | "catReason" | "opReason",
    value: string,
  ) => void;
  onDiscardDraft: (rowId: string) => void;
  onMarkRemove: (rowId: string) => void;
  onUndoRemove: (rowId: string) => void;
};

/** Tabela oficial de vínculos SA2/SA5 — linha principal com colunas
 * Busca/Código/Loja/Razão social/Nome fantasia/PN/Catálogo/Ações e linha
 * auxiliar expansível (lookup + editores de justificativa). A origem da
 * linha (`origin`) determina vínculo oficial vs candidata — descarte
 * local nunca gera remoção SA5. */
export function PrcSupplierTable({
  suppliers,
  removeMarks,
  baselineLinks,
  requestType,
  busy,
  errorsVisible,
  partNumberLabel,
  catalogLabel,
  searchSuppliers,
  portalScopeClassName,
  onPatchRow,
  onToggleSearch,
  onCloseSearch,
  onToggleReason,
  onSetReason,
  onDiscardDraft,
  onMarkRemove,
  onUndoRemove,
}: PrcSupplierTableProps) {
  return (
    <div className="delpi-prc__supplier-table-wrap">
      <table className="delpi-prc__supplier-table">
        <caption className="delpi-prc__sr-only">
          Vínculos de fornecedores do produto
        </caption>
        <thead>
          <tr>
            <th scope="col">Busca</th>
            <th scope="col">Código</th>
            <th scope="col">Loja</th>
            <th scope="col">Razão social</th>
            <th scope="col">Nome fantasia</th>
            <th scope="col">{partNumberLabel}</th>
            <th scope="col">{catalogLabel}</th>
            <th scope="col">Ações</th>
          </tr>
        </thead>
        <tbody>
          {suppliers.map((row, index) => {
            const missing =
              !row.supplierCode.trim() ||
              !row.store.trim() ||
              !row.supplierName.trim();
            const dup = duplicateDraftRowIds(suppliers).has(row.rowId);
            const key = linkKeyOf(row.supplierCode, row.store);
            const isOfficial = row.origin === "official";
            const markedRemove =
              isOfficial && removeMarks.has(row.rowId);
            const baselineLink = isOfficial
              ? baselineLinks.find(
                  (l) =>
                    linkKeyOf(l.supplierCode, l.store) === key,
                )
              : undefined;
            const pnChanged = isOfficial
              ? row.partNumber.trim() !==
                (baselineLink?.partNumber || "").trim()
              : row.partNumber.trim() !== "";
            const catChanged = isOfficial
              ? row.catalogNumber.trim() !==
                (baselineLink?.catalogNumber || "").trim()
              : row.catalogNumber.trim() !== "";
            const identityLocked = isOfficial;
            const searchId = `prc-sup-search-${row.rowId}`;
            const auxOpen = Boolean(
              row.searchOpen ||
                row.pnReasonOpen ||
                row.catReasonOpen ||
                row.opReasonOpen,
            );
            const rowClass = markedRemove
              ? "delpi-prc__supplier-tr--remove"
              : isOfficial && requestType === "update"
                ? ""
                : "delpi-prc__supplier-tr--added";
            return (
              <Fragment key={row.rowId}>
                <tr
                  className={
                    missing || dup || row.selectionError
                      ? "delpi-prc__supplier-tr--error"
                      : rowClass
                  }
                  data-row-id={row.rowId}
                  data-origin={row.origin}
                >
                  <td
                    data-label="Busca"
                    className="delpi-prc__supplier-td--search"
                  >
                    <span
                      title={
                        identityLocked
                          ? "Identidade oficial do vínculo — para trocar o fornecedor, solicite a remoção e adicione um novo vínculo."
                          : "Buscar por código, razão social ou nome fantasia"
                      }
                    >
                      <IconButton
                        className="delpi-prc__search-toggle"
                        aria-label={
                          row.supplierCode
                            ? `Alterar fornecedor da linha ${index + 1}`
                            : `Buscar fornecedor da linha ${index + 1}`
                        }
                        aria-expanded={Boolean(row.searchOpen)}
                        aria-controls={searchId}
                        aria-haspopup="listbox"
                        disabled={busy || identityLocked || markedRemove}
                        onClick={() => onToggleSearch(row.rowId)}
                      >
                        <Search size={15} aria-hidden />
                      </IconButton>
                    </span>
                  </td>
                  <td data-label="Código">{row.supplierCode || "—"}</td>
                  <td data-label="Loja">{row.store || "—"}</td>
                  <td data-label="Razão social">
                    {row.supplierName || "—"}
                    {row.selectionError ? (
                      <span
                        className="delpi-prc__cell-error"
                        role="alert"
                      >
                        {row.selectionError}
                      </span>
                    ) : missing ? (
                      <span
                        className="delpi-prc__cell-error"
                        role="alert"
                      >
                        Selecione um fornecedor oficial.
                      </span>
                    ) : null}
                    {dup && !missing && !row.selectionError ? (
                      <span
                        className="delpi-prc__cell-error"
                        role="alert"
                      >
                        {PRC_SUPPLIER_TEXT.duplicateExisting}
                      </span>
                    ) : null}
                  </td>
                  <td data-label="Nome fantasia">
                    {row.supplierShortName || "—"}
                  </td>
                  <td data-label={partNumberLabel}>
                    <input
                      id={`prc-new-sup-pn-${row.rowId}`}
                      type="text"
                      className="delpi-prc__cell-input"
                      aria-label={partNumberLabel}
                      aria-required="true"
                      required
                      title={PRC_SUPPLIER_TEXT.partNumberHint}
                      value={row.partNumber}
                      disabled={busy || markedRemove}
                      onChange={(e) =>
                        onPatchRow(row.rowId, {
                          partNumber: e.target.value,
                        })
                      }
                    />
                    {errorsVisible && !row.partNumber.trim() ? (
                      <span
                        className="delpi-prc__cell-error"
                        role="alert"
                      >
                        {PRC_SUPPLIER_TEXT.partNumberRequired}
                      </span>
                    ) : null}
                    {isOfficial && pnChanged ? (
                      <p className="delpi-prc__cell-diff">
                        <span className="delpi-prc__diff-tag">
                          Alterado
                        </span>
                        <span className="delpi-prc__muted">
                          Anterior:{" "}
                          <strong>
                            {(baselineLink?.partNumber || "").trim() ||
                              "vazio"}
                          </strong>
                        </span>
                      </p>
                    ) : null}
                    {pnChanged ? (
                      <PrcReasonToggle
                        id={`prc-sup-pn-reason-${row.rowId}`}
                        value={row.pnReason || ""}
                        open={Boolean(row.pnReasonOpen)}
                        disabled={busy}
                        onToggle={() =>
                          onToggleReason(row.rowId, "pnReasonOpen")
                        }
                      />
                    ) : null}
                  </td>
                  <td data-label={catalogLabel}>
                    <input
                      id={`prc-new-sup-cat-${row.rowId}`}
                      type="text"
                      className="delpi-prc__cell-input"
                      aria-label={catalogLabel}
                      title={PRC_SUPPLIER_TEXT.catalogHint}
                      value={row.catalogNumber}
                      disabled={busy || markedRemove}
                      onChange={(e) =>
                        onPatchRow(row.rowId, {
                          catalogNumber: e.target.value,
                        })
                      }
                    />
                    {isOfficial && catChanged ? (
                      <p className="delpi-prc__cell-diff">
                        <span className="delpi-prc__diff-tag">
                          Alterado
                        </span>
                        <span className="delpi-prc__muted">
                          Anterior:{" "}
                          <strong>
                            {(baselineLink?.catalogNumber || "").trim() ||
                              "vazio"}
                          </strong>
                        </span>
                      </p>
                    ) : null}
                    {catChanged ? (
                      <PrcReasonToggle
                        id={`prc-sup-cat-reason-${row.rowId}`}
                        value={row.catReason || ""}
                        open={Boolean(row.catReasonOpen)}
                        disabled={busy}
                        onToggle={() =>
                          onToggleReason(row.rowId, "catReasonOpen")
                        }
                      />
                    ) : null}
                  </td>
                  <td
                    data-label="Ações"
                    className="delpi-prc__supplier-td--actions"
                  >
                    {requestType === "update" && isOfficial ? (
                      markedRemove ? (
                        <span title="Desfazer remoção">
                          <IconButton
                            aria-label={`Desfazer remoção do vínculo ${row.supplierCode}/${row.store}`}
                            disabled={busy}
                            onClick={() => onUndoRemove(row.rowId)}
                          >
                            <Undo2 size={15} aria-hidden />
                          </IconButton>
                        </span>
                      ) : (
                        <span title="Solicitar remoção">
                          <IconButton
                            tone="danger"
                            aria-label={`Solicitar remoção do vínculo ${row.supplierCode}/${row.store}`}
                            disabled={busy}
                            onClick={() => onMarkRemove(row.rowId)}
                          >
                            <Trash2 size={15} aria-hidden />
                          </IconButton>
                        </span>
                      )
                    ) : (
                      <span
                        title={
                          dup
                            ? PRC_SUPPLIER_TEXT.discardDraftOnly
                            : "Descartar linha candidata"
                        }
                      >
                        <IconButton
                          tone="danger"
                          aria-label={`Descartar fornecedor da linha ${index + 1}`}
                          disabled={busy}
                          onClick={() => onDiscardDraft(row.rowId)}
                        >
                          <Trash2 size={15} aria-hidden />
                        </IconButton>
                      </span>
                    )}
                    {markedRemove ? (
                      <>
                        <p className="delpi-prc__remove-tag">
                          Remoção solicitada — será proposta ao TOTVS.
                        </p>
                        <PrcReasonToggle
                          id={`prc-sup-rm-reason-${row.rowId}`}
                          value={row.opReason || ""}
                          open={Boolean(row.opReasonOpen)}
                          disabled={busy}
                          onToggle={() =>
                            onToggleReason(row.rowId, "opReasonOpen")
                          }
                        />
                      </>
                    ) : null}
                    {!isOfficial && !missing && !dup ? (
                      <>
                        {requestType === "update" ? (
                          <p className="delpi-prc__add-tag">Adicionado</p>
                        ) : null}
                        <PrcReasonToggle
                          id={`prc-sup-add-reason-${row.rowId}`}
                          value={row.opReason || ""}
                          open={Boolean(row.opReasonOpen)}
                          disabled={busy}
                          label="Justificar inclusão"
                          onToggle={() =>
                            onToggleReason(row.rowId, "opReasonOpen")
                          }
                        />
                      </>
                    ) : null}
                    {dup ? (
                      <p className="delpi-prc__muted">
                        {PRC_SUPPLIER_TEXT.discardDraftOnly}
                      </p>
                    ) : null}
                  </td>
                </tr>
                {auxOpen ? (
                  <tr className="delpi-prc__supplier-aux">
                    <td colSpan={8}>
                      {row.searchOpen ? (
                        <div
                          id={searchId}
                          className="delpi-prc__supplier-search"
                          role="group"
                          aria-label={`Busca de fornecedor da linha ${index + 1}`}
                        >
                          <div className="delpi-prc__supplier-search-head">
                            <span className="delpi-prc__supplier-search-title">
                              {row.supplierCode
                                ? "Alterar seleção do fornecedor"
                                : "Pesquisar fornecedor"}
                            </span>
                            <IconButton
                              aria-label="Fechar busca"
                              onClick={() => onCloseSearch(row.rowId)}
                            >
                              <X size={14} aria-hidden />
                            </IconButton>
                          </div>
                          <PrcSupplierCellLookup
                            id={`prc-new-sup-${row.rowId}`}
                            query={row.query}
                            disabled={busy}
                            searchSuppliers={searchSuppliers}
                            portalScopeClassName={portalScopeClassName}
                            onQueryChange={(v) =>
                              onPatchRow(row.rowId, {
                                query: v,
                                selectionError: undefined,
                              })
                            }
                            onSelect={(hit) => {
                              const code = String(hit.supplier_code ?? "");
                              const store = String(
                                hit.supplier_store ?? "",
                              );
                              const conflict = findRowWithOfficialKey(
                                suppliers,
                                code,
                                store,
                                row.rowId,
                              );
                              if (conflict) {
                                onPatchRow(row.rowId, {
                                  selectionError:
                                    PRC_SUPPLIER_TEXT.duplicateExisting,
                                  searchOpen: true,
                                });
                                return;
                              }
                              onPatchRow(row.rowId, {
                                supplierCode: code,
                                store,
                                supplierName: String(
                                  hit.supplier_name ?? "",
                                ),
                                supplierShortName: String(
                                  hit.supplier_short_name ?? "",
                                ),
                                query: "",
                                searchOpen: false,
                                selectionError: undefined,
                              });
                              window.requestAnimationFrame(() => {
                                document
                                  .getElementById(
                                    `prc-new-sup-pn-${row.rowId}`,
                                  )
                                  ?.focus();
                              });
                            }}
                            onClose={() => onCloseSearch(row.rowId)}
                          />
                          {row.selectionError ? (
                            <p
                              className="delpi-prc__field-error"
                              role="alert"
                            >
                              {row.selectionError}
                            </p>
                          ) : (
                            <p className="delpi-prc__muted">
                              Ao escolher um resultado, código, loja e
                              razão social são preenchidos
                              automaticamente.
                            </p>
                          )}
                        </div>
                      ) : null}
                      {pnChanged && row.pnReasonOpen ? (
                        <PrcReasonEditor
                          id={`prc-sup-pn-reason-${row.rowId}`}
                          label={`Justificativa de ${partNumberLabel} (opcional)`}
                          value={row.pnReason || ""}
                          onChange={(v) =>
                            onSetReason(row.rowId, "pnReason", v)
                          }
                          disabled={busy}
                          onCollapse={() =>
                            onToggleReason(row.rowId, "pnReasonOpen")
                          }
                        />
                      ) : null}
                      {catChanged && row.catReasonOpen ? (
                        <PrcReasonEditor
                          id={`prc-sup-cat-reason-${row.rowId}`}
                          label={`Justificativa de ${catalogLabel} (opcional)`}
                          value={row.catReason || ""}
                          onChange={(v) =>
                            onSetReason(row.rowId, "catReason", v)
                          }
                          disabled={busy}
                          onCollapse={() =>
                            onToggleReason(row.rowId, "catReasonOpen")
                          }
                        />
                      ) : null}
                      {row.opReasonOpen ? (
                        <PrcReasonEditor
                          id={`prc-sup-op-reason-${row.rowId}`}
                          label="Justificativa da operação (opcional)"
                          value={row.opReason || ""}
                          onChange={(v) =>
                            onSetReason(row.rowId, "opReason", v)
                          }
                          disabled={busy}
                          onCollapse={() =>
                            onToggleReason(row.rowId, "opReasonOpen")
                          }
                        />
                      ) : null}
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
