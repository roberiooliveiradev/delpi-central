import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { ApiError, formatDuplicateMessage } from "../../data/api/httpClient";
import * as api from "../../data/api/invoicePostingApi";
import {
  BRANCH_OPTIONS,
  normalizeDocumentInput,
  normalizeSeriesInput,
  parseAmountInput,
  sanitizeAmountTyping,
  sanitizeDocumentTyping,
} from "../../domain/fiscal";
import type { CreateRequestPayload, Supplier } from "../../domain/types";
import { branchLabel, type BranchCode } from "../../constants/branch";
import { LnfPageHeader } from "../components/LnfPageHeader";
import { SupplierSearch } from "../components/SupplierSearch";

type Props = {
  mode: "create" | "edit";
  requestId?: string;
  lockedBranch?: BranchCode;
  onCancel: () => void;
  onSuccess: (requestId: string) => void;
};

type FormState = {
  branch: string;
  document: string;
  series: string;
  issue_date: string;
  amount: string;
  received_at: string;
  observation: string;
};

function toLocalInputValue(iso: string | Date | null | undefined): string {
  if (!iso) return "";
  const d = iso instanceof Date ? iso : new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromLocalInputValue(local: string): string {
  const d = new Date(local);
  if (Number.isNaN(d.getTime())) return local;
  return d.toISOString();
}

function buildCreateForm(lockedBranch?: BranchCode): FormState {
  return {
    branch: lockedBranch ?? "01",
    document: "",
    series: "",
    issue_date: "",
    amount: "",
    received_at: toLocalInputValue(new Date()),
    observation: "",
  };
}

const FOCUSABLE_SELECTOR = [
  "input:not([disabled]):not([type='hidden']):not([type='submit'])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "button:not([disabled])",
].join(",");

/** Enter avança o foco como Tab (exceto textarea e botão submit). */
function handleEnterAsTab(e: KeyboardEvent<HTMLFormElement>) {
  if (e.key !== "Enter" || e.ctrlKey || e.metaKey || e.altKey) return;
  const target = e.target;
  if (!(target instanceof HTMLElement)) return;
  if (target.tagName === "TEXTAREA") return;
  if (
    target instanceof HTMLButtonElement &&
    (target.type === "submit" || target.dataset.testid === "btn-submit-request")
  ) {
    return;
  }
  e.preventDefault();
  const form = e.currentTarget;
  const focusables = Array.from(
    form.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
  ).filter((el) => {
    if (el.getAttribute("aria-hidden") === "true") return false;
    if (el.tabIndex < 0) return false;
    return true;
  });
  const idx = focusables.indexOf(target);
  if (idx < 0) return;
  const next = focusables[idx + 1];
  if (next) {
    next.focus();
    if (next instanceof HTMLInputElement && next.type === "text") {
      next.select();
    }
  }
}

export function RequestFormPage({
  mode,
  requestId,
  lockedBranch,
  onCancel,
  onSuccess,
}: Props) {
  const [form, setForm] = useState<FormState>(() => buildCreateForm(lockedBranch));
  const [supplier, setSupplier] = useState<Supplier | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(mode === "edit");

  const documentPreview = useMemo(
    () => normalizeDocumentInput(form.document),
    [form.document],
  );

  useEffect(() => {
    if (mode === "create") {
      setForm(buildCreateForm(lockedBranch));
      setSupplier(null);
      setFieldErrors({});
      setSubmitError(null);
      setLoading(false);
      return;
    }
    if (!requestId) return;
    let cancelled = false;
    setLoading(true);
    api
      .getRequest(requestId)
      .then((detail) => {
        if (cancelled) return;
        const r = detail.request;
        setForm({
          branch: lockedBranch ?? r.branch_code,
          document: r.document_number.replace(/^0+/, "") || r.document_number,
          series: r.series ?? "",
          issue_date: r.issue_date,
          amount: String(r.amount).replace(".", ","),
          received_at: toLocalInputValue(r.received_at),
          observation: r.observation ?? "",
        });
        setSupplier({
          supplier_code: r.supplier_code,
          supplier_store: r.supplier_store,
          supplier_name: r.supplier_name,
          supplier_short_name: r.supplier_short_name,
          tax_id: null,
          state: null,
          blocked: false,
        });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setSubmitError(err instanceof Error ? err.message : "Falha ao carregar.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [mode, requestId, lockedBranch]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitError(null);
    const errors: Record<string, string> = {};
    const doc = normalizeDocumentInput(form.document);
    const series = normalizeSeriesInput(form.series);
    if (!doc.digits) errors.document = "Informe o número da nota.";
    if (!(lockedBranch ?? form.branch)) errors.branch = "Selecione a filial.";
    if (!series) errors.series = "Informe a série (como no Protheus).";
    if (!supplier) errors.supplier = "Selecione o fornecedor.";
    if (!form.issue_date) errors.issue_date = "Informe a data de emissão.";
    const amountValue = parseAmountInput(form.amount);
    if (amountValue === null) errors.amount = "Informe o valor (use vírgula ou ponto).";
    if (!form.received_at) errors.received_at = "Informe o recebimento físico.";
    setFieldErrors(errors);
    if (
      Object.keys(errors).length > 0 ||
      !supplier ||
      !doc.digits ||
      !series ||
      amountValue === null
    ) {
      return;
    }

    const payload: CreateRequestPayload = {
      branch: lockedBranch ?? form.branch,
      document: doc.digits,
      series,
      supplier_code: supplier.supplier_code,
      supplier_store: supplier.supplier_store,
      issue_date: form.issue_date,
      amount: amountValue,
      received_at: fromLocalInputValue(form.received_at),
      observation: form.observation.trim() || undefined,
    };

    setBusy(true);
    try {
      if (mode === "create") {
        const created = await api.createRequest(payload);
        onSuccess(created.id);
      } else if (requestId) {
        const updated = await api.updateRequest(requestId, payload);
        onSuccess(updated.id);
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setSubmitError(formatDuplicateMessage(err));
      } else if (err instanceof ApiError && err.status === 403) {
        setSubmitError(err.message);
      } else {
        setSubmitError(err instanceof Error ? err.message : "Falha ao salvar.");
      }
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <p className="lnf-muted">Carregando formulário…</p>;
  }

  return (
    <div className="lnf-stack" data-testid="request-form-page">
      <LnfPageHeader
        title={mode === "create" ? "Nova solicitação" : "Corrigir solicitação"}
        subtitle="Informe os dados fiscais do recebimento físico da nota."
        actions={
          <button type="button" className="lnf-btn lnf-btn--ghost" onClick={onCancel}>
            Voltar
          </button>
        }
      />

      <form
        className="lnf-form-shell"
        onSubmit={handleSubmit}
        onKeyDown={handleEnterAsTab}
        noValidate
      >
        <section className="lnf-card lnf-form-section">
          <h2>Dados da nota</h2>
          <div className="lnf-form-grid">
            <label className="lnf-field">
              Filial
              {lockedBranch ? (
                <select
                  aria-label="Filial"
                  value={lockedBranch}
                  disabled
                  title="Filial definida pela rota do menu"
                >
                  <option value={lockedBranch}>{branchLabel(lockedBranch)}</option>
                </select>
              ) : (
                <select
                  aria-label="Filial"
                  value={form.branch}
                  onChange={(e) => setForm((f) => ({ ...f, branch: e.target.value }))}
                  aria-required
                >
                  {BRANCH_OPTIONS.map((b) => (
                    <option key={b.value} value={b.value}>
                      {b.label}
                    </option>
                  ))}
                </select>
              )}
              {fieldErrors.branch ? (
                <span className="lnf-error">{fieldErrors.branch}</span>
              ) : null}
            </label>

            <label className="lnf-field">
              Número da nota
              <input
                aria-label="Número da nota"
                inputMode="numeric"
                value={form.document}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    document: sanitizeDocumentTyping(e.target.value),
                  }))
                }
                aria-invalid={Boolean(fieldErrors.document)}
                aria-required
              />
              {documentPreview.digits ? (
                <span className="lnf-hint" data-testid="document-preview">
                  Apresentação: {documentPreview.display} · chave: {documentPreview.matchKey}
                </span>
              ) : null}
              {fieldErrors.document ? (
                <span className="lnf-error">{fieldErrors.document}</span>
              ) : null}
            </label>

            <label className="lnf-field">
              Série
              <input
                aria-label="Série"
                value={form.series}
                maxLength={3}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    series: normalizeSeriesInput(e.target.value),
                  }))
                }
                placeholder="Ex.: 1"
                aria-required
                aria-invalid={Boolean(fieldErrors.series)}
              />
              <span className="lnf-hint">Obrigatória — igual à série no Protheus.</span>
              {fieldErrors.series ? (
                <span className="lnf-error">{fieldErrors.series}</span>
              ) : null}
            </label>

            <label className="lnf-field">
              Data de emissão
              <input
                aria-label="Data de emissão"
                type="date"
                value={form.issue_date}
                onChange={(e) => setForm((f) => ({ ...f, issue_date: e.target.value }))}
                aria-required
              />
              {fieldErrors.issue_date ? (
                <span className="lnf-error">{fieldErrors.issue_date}</span>
              ) : null}
            </label>

            <label className="lnf-field">
              Valor
              <input
                aria-label="Valor"
                type="text"
                inputMode="decimal"
                placeholder="0,00"
                value={form.amount}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    amount: sanitizeAmountTyping(e.target.value),
                  }))
                }
                aria-required
              />
              {fieldErrors.amount ? (
                <span className="lnf-error">{fieldErrors.amount}</span>
              ) : null}
            </label>
          </div>
        </section>

        <section className="lnf-card lnf-form-section">
          <h2>Fornecedor</h2>
          <div className="lnf-form-grid">
            <div className="lnf-form-grid__full">
              <SupplierSearch
                selected={supplier}
                onSelect={setSupplier}
                error={fieldErrors.supplier}
              />
            </div>
          </div>
        </section>

        <section className="lnf-card lnf-form-section">
          <h2>Recebimento</h2>
          <div className="lnf-form-grid">
            <label className="lnf-field">
              Recebimento físico
              <input
                aria-label="Recebimento físico"
                type="datetime-local"
                value={form.received_at}
                onChange={(e) => setForm((f) => ({ ...f, received_at: e.target.value }))}
                aria-required
              />
              {fieldErrors.received_at ? (
                <span className="lnf-error">{fieldErrors.received_at}</span>
              ) : null}
            </label>

            <label className="lnf-field lnf-form-grid__full">
              Observação
              <textarea
                aria-label="Observação"
                rows={3}
                value={form.observation}
                onChange={(e) => setForm((f) => ({ ...f, observation: e.target.value }))}
              />
            </label>
          </div>
        </section>

        {submitError ? (
          <p className="lnf-error" role="alert" data-testid="form-submit-error">
            {submitError}
          </p>
        ) : null}

        <div className="lnf-form__actions lnf-form__actions--sticky">
          <button
            type="button"
            className="lnf-btn lnf-btn--ghost"
            onClick={onCancel}
            disabled={busy}
          >
            Cancelar
          </button>
          <button
            type="submit"
            className="lnf-btn lnf-btn--primary"
            disabled={busy}
            data-testid="btn-submit-request"
          >
            {busy ? "Salvando…" : mode === "create" ? "Cadastrar" : "Salvar correção"}
          </button>
        </div>
      </form>
    </div>
  );
}
