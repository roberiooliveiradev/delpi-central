import { FilePreviewModal } from "@delpi/plugin-ui/index";
import { useMemo, useState, type FormEvent } from "react";
import { helpTooltips } from "../../content/helpTooltips";
import { fetchReceivedInvoicePreview, searchReceivedInvoices } from "../../data/api/invoicePostingApi";
import type { ReceivedInvoiceItem, ReceivedInvoiceSearch } from "../../domain/types";
import { LnfPageHeader } from "./LnfPageHeader";

type Props = {
  step: "choose" | "search";
  onManual: () => void;
  onSelectNfe: () => void;
  onCancel: () => void;
  onBackToChoice: () => void;
  onAdvance: (row: ReceivedInvoiceItem, searchedCnpj: string | null) => void;
};

function canUseDanfe(row: ReceivedInvoiceItem): boolean {
  return Boolean(row.danfeAvailable) && Boolean(row.documentId) && row.accessKey.length === 44;
}

export function ReceivedInvoicePicker({
  step,
  onManual,
  onSelectNfe,
  onCancel,
  onBackToChoice,
  onAdvance,
}: Props) {
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [supplierCnpj, setSupplierCnpj] = useState("");
  const [appliedCnpj, setAppliedCnpj] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [result, setResult] = useState<ReceivedInvoiceSearch | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<ReceivedInvoiceItem | null>(null);

  const previewSource = useMemo(() => {
    if (!preview) return null;
    const documentId = preview.documentId;
    const accessKey = preview.accessKey;
    return () => fetchReceivedInvoicePreview(documentId, accessKey);
  }, [preview]);

  async function runSearch(event: FormEvent | null, nextPage: number) {
    event?.preventDefault();
    const number = invoiceNumber.trim();
    const cnpj = supplierCnpj.trim();
    if (!number && !cnpj) {
      setError("Informe o número da nota ou o CNPJ do fornecedor.");
      return;
    }
    setLoading(true);
    setError(null);
    setAppliedCnpj(cnpj || null);
    setPage(nextPage);
    try {
      const data = await searchReceivedInvoices({
        invoiceNumber: number || undefined,
        supplierCnpj: cnpj || undefined,
        page: nextPage,
      });
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Não foi possível consultar as notas.");
    } finally {
      setLoading(false);
    }
  }

  if (step === "choose") {
    return (
      <div className="lnf-stack" data-testid="request-entry-choice">
        <LnfPageHeader
          title="Nova solicitação"
          subtitle={helpTooltips.newRequest}
          actions={
            <button type="button" className="lnf-btn lnf-btn--ghost" onClick={onCancel}>
              Voltar
            </button>
          }
        />
        <div className="lnf-choice-grid">
          <button type="button" className="lnf-card lnf-choice" onClick={onManual}>
            <strong>Inclusão manual</strong>
            <span>Preencher os dados fiscais do recebimento.</span>
          </button>
          <button type="button" className="lnf-card lnf-choice" data-testid="btn-select-nfe" onClick={onSelectNfe}>
            <strong>Selecionar NF-e</strong>
            <span>Buscar uma nota real e anexar o DANFE.</span>
          </button>
        </div>
      </div>
    );
  }

  const items = result?.items ?? [];

  return (
    <div className="lnf-stack" data-testid="received-invoice-search">
      <LnfPageHeader
        title="Selecionar NF-e"
        subtitle="A busca usa o número da nota ou o CNPJ. O DANFE abre nesta tela antes de avançar."
        actions={
          <button type="button" className="lnf-btn lnf-btn--ghost" onClick={onBackToChoice}>
            Voltar
          </button>
        }
      />
      <form className="lnf-card lnf-form-section" onSubmit={(event) => void runSearch(event, 1)}>
        <div className="lnf-form-grid">
          <label className="lnf-field">
            Número da NF
            <input
              aria-label="Número da NF"
              value={invoiceNumber}
              onChange={(event) => setInvoiceNumber(event.target.value)}
            />
          </label>
          <label className="lnf-field">
            CNPJ do fornecedor
            <input
              aria-label="CNPJ do fornecedor"
              value={supplierCnpj}
              onChange={(event) => setSupplierCnpj(event.target.value)}
            />
          </label>
        </div>
        <div className="lnf-form__actions">
          <button type="submit" className="lnf-btn lnf-btn--primary" disabled={loading}>
            {loading ? "Buscando…" : "Buscar"}
          </button>
        </div>
      </form>
      {error ? (
        <p className="lnf-error" role="alert">
          {error}
        </p>
      ) : null}
      {result && items.length === 0 ? <p className="lnf-muted">Nenhuma nota encontrada.</p> : null}
      {items.length > 0 ? (
        <div className="lnf-table-wrap">
          <table className="lnf-table">
            <thead>
              <tr>
                <th>NF</th>
                <th>Série</th>
                <th>Emissão</th>
                <th>Fornecedor</th>
                <th>Valor</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => {
                const usable = canUseDanfe(row);
                return (
                  <tr key={row.documentId || row.accessKey || row.invoiceNumber}>
                    <td>{row.invoiceNumber || "—"}</td>
                    <td>{row.series || "—"}</td>
                    <td>{row.emissionAt ? row.emissionAt.slice(0, 10) : "—"}</td>
                    <td>{row.issuerName || "—"}</td>
                    <td>{row.amountFormatted || row.amount || "—"}</td>
                    <td>
                      <div className="lnf-row-actions">
                        <button
                          type="button"
                          className="lnf-btn lnf-btn--ghost"
                          disabled={!usable}
                          onClick={() => {
                            if (usable) setPreview(row);
                          }}
                        >
                          Visualizar
                        </button>
                        <button
                          type="button"
                          className="lnf-btn lnf-btn--primary"
                          disabled={!usable}
                          onClick={() => {
                            if (usable) onAdvance(row, appliedCnpj);
                          }}
                        >
                          Avançar
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div className="lnf-form__actions">
            <button
              type="button"
              className="lnf-btn lnf-btn--ghost"
              disabled={!result?.pagination.hasPrevious || loading}
              onClick={() => void runSearch(null, page - 1)}
            >
              Anterior
            </button>
            <button
              type="button"
              className="lnf-btn lnf-btn--ghost"
              disabled={!result?.pagination.hasNext || loading}
              onClick={() => void runSearch(null, page + 1)}
            >
              Próxima
            </button>
          </div>
        </div>
      ) : null}
      <FilePreviewModal
        open={preview != null}
        title={preview ? `DANFE ${preview.invoiceNumber}` : "DANFE"}
        onClose={() => setPreview(null)}
        source={previewSource}
        mimeType="application/pdf"
        declaredType="pdf"
        fileName={preview ? `NFe-${preview.accessKey}.pdf` : null}
        portalScopeClassName="dashboard-lancamento-notas-fiscais"
        labels={{ loading: "Abrindo o DANFE…", loadFailed: "Não foi possível abrir o DANFE." }}
      />
    </div>
  );
}
