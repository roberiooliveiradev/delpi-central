import { FilePreviewModal } from "@delpi/plugin-ui/index";
import { useMemo, useState, type FormEvent } from "react";
import { helpTooltips } from "../../content/helpTooltips";
import {
  downloadReceivedNfseXml,
  fetchReceivedCteDacte,
  fetchReceivedInvoicePreview,
  fetchReceivedNfseDetail,
  searchReceivedInvoices,
} from "../../data/api/invoicePostingApi";
import { displayDocumentNumber } from "../../domain/fiscal";
import type { NfseDetail, ReceivedDocumentType, ReceivedInvoiceItem, ReceivedInvoiceSearch } from "../../domain/types";
import { LnfPageHeader } from "./LnfPageHeader";
import { NfseDataModal } from "./NfseDataModal";

type Props = {
  step: "choose" | "search";
  onManual: () => void;
  onSelectNfe: () => void;
  onCancel: () => void;
  onBackToChoice: () => void;
  onAdvance: (row: ReceivedInvoiceItem, searchedCnpj: string | null) => void;
  selectionError?: string | null;
};

type DocumentFilter = "all" | ReceivedDocumentType;

function rowType(row: ReceivedInvoiceItem): ReceivedDocumentType {
  if (row.documentType === "nfse" || row.documentType === "cte") return row.documentType;
  return "nfe";
}

function canAdvance(row: ReceivedInvoiceItem): boolean {
  const kind = rowType(row);
  if (kind === "nfse") return Boolean(row.documentId);
  if (kind === "cte") {
    return Boolean(row.documentId) && Boolean(row.providerFileId) && row.accessKey.length === 44;
  }
  return Boolean(row.danfeAvailable) && Boolean(row.documentId) && row.accessKey.length === 44;
}

function canPreview(row: ReceivedInvoiceItem): boolean {
  if (rowType(row) === "cte") {
    return Boolean(row.printableAvailable) && Boolean(row.providerFileId) && row.accessKey.length === 44;
  }
  return canAdvance(row);
}

function typeLabel(row: ReceivedInvoiceItem): string {
  const kind = rowType(row);
  if (kind === "nfse") return "NFS-e";
  if (kind === "cte") return "CT-e";
  return "NF-e";
}

function primaryNumber(row: ReceivedInvoiceItem): string {
  if (rowType(row) === "nfe") return row.invoiceNumber || "—";
  return displayDocumentNumber(row.documentNumber || row.invoiceNumber) || "—";
}

export function ReceivedInvoicePicker({
  step,
  onManual,
  onSelectNfe,
  onCancel,
  onBackToChoice,
  onAdvance,
  selectionError = null,
}: Props) {
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [supplierCnpj, setSupplierCnpj] = useState("");
  const [documentType, setDocumentType] = useState<DocumentFilter>("all");
  const [appliedCnpj, setAppliedCnpj] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [result, setResult] = useState<ReceivedInvoiceSearch | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<ReceivedInvoiceItem | null>(null);
  const [nfseRow, setNfseRow] = useState<ReceivedInvoiceItem | null>(null);
  const [nfseDetail, setNfseDetail] = useState<NfseDetail | null>(null);
  const [nfseLoading, setNfseLoading] = useState(false);
  const [nfseError, setNfseError] = useState<string | null>(null);

  const previewSource = useMemo(() => {
    if (!preview) return null;
    const documentId = preview.documentId;
    const accessKey = preview.accessKey;
    const branch = preview.branchCode;
    if (rowType(preview) === "cte" && preview.providerFileId) {
      const fileId = preview.providerFileId;
      return () => fetchReceivedCteDacte(documentId, fileId, accessKey, branch);
    }
    return () => fetchReceivedInvoicePreview(documentId, accessKey, branch);
  }, [preview]);

  async function runSearch(event: FormEvent | null, nextPage: number, nextType = documentType) {
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
        documentType: nextType,
      });
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Não foi possível consultar as notas.");
    } finally {
      setLoading(false);
    }
  }

  async function openNfse(row: ReceivedInvoiceItem) {
    setNfseRow(row);
    setNfseDetail(null);
    setNfseError(null);
    setNfseLoading(true);
    try {
      const detail = await fetchReceivedNfseDetail(row.documentId, row.branchCode);
      setNfseDetail(detail);
    } catch (err) {
      setNfseError(err instanceof Error ? err.message : "Não foi possível carregar os dados da NFS-e.");
    } finally {
      setNfseLoading(false);
    }
  }

  async function downloadXml(variant: "original" | "standard") {
    if (!nfseRow) return;
    const blob = await downloadReceivedNfseXml(nfseRow.documentId, variant, nfseRow.branchCode);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = variant === "original" ? "nfse-original.xml" : "nfse-padronizado.xml";
    anchor.click();
    URL.revokeObjectURL(url);
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
            <strong>Selecionar documento fiscal</strong>
            <span>Buscar NF-e, NFS-e ou CT-e e trazer os dados para a solicitação.</span>
          </button>
        </div>
      </div>
    );
  }

  const items = result?.items ?? [];

  return (
    <div className="lnf-stack" data-testid="received-invoice-search">
      <LnfPageHeader
        title="Selecionar documento fiscal"
        subtitle="A busca usa o número ou o CNPJ. NF-e abre o DANFE. NFS-e mostra os dados da nota. CT-e abre o DACTE."
        actions={
          <button type="button" className="lnf-btn lnf-btn--ghost" onClick={onBackToChoice}>
            Voltar
          </button>
        }
      />
      <form className="lnf-card lnf-form-section" onSubmit={(event) => void runSearch(event, 1)}>
        <div className="lnf-tabs" role="tablist" aria-label="Tipo de documento">
          {(
            [
              ["all", "Todos"],
              ["nfe", "NF-e"],
              ["nfse", "NFS-e"],
              ["cte", "CT-e"],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              type="button"
              role="tab"
              aria-selected={documentType === value}
              className={documentType === value ? "lnf-tabs__tab lnf-tabs__tab--active" : "lnf-tabs__tab"}
              onClick={() => {
                setDocumentType(value);
                if (result) void runSearch(null, 1, value);
              }}
            >
              {label}
            </button>
          ))}
        </div>
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
      {selectionError ? (
        <p className="lnf-error" role="alert">
          {selectionError}
        </p>
      ) : null}
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
                <th>Tipo</th>
                <th>Número</th>
                <th>Série</th>
                <th>Emissão</th>
                <th>Fornecedor/Prestador</th>
                <th>Valor</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => {
                const usable = canAdvance(row);
                const viewable = canPreview(row);
                const original = row.providerDocumentNumber;
                const showOriginal =
                  rowType(row) === "nfse" && original && original !== (row.documentNumber || row.invoiceNumber);
                return (
                  <tr key={`${rowType(row)}-${row.documentId || row.accessKey || row.invoiceNumber}`}>
                    <td>
                      <span className="lnf-doc-badge" data-testid={`doc-type-${rowType(row)}`}>
                        {typeLabel(row)}
                      </span>
                    </td>
                    <td>
                      <div>{primaryNumber(row)}</div>
                      {showOriginal ? <div className="lnf-muted">Original Questor: {original}</div> : null}
                    </td>
                    <td>{row.series || "—"}</td>
                    <td>{row.emissionAt ? row.emissionAt.slice(0, 10) : "—"}</td>
                    <td>{row.issuerName || "—"}</td>
                    <td>{row.amountFormatted || row.amount || "—"}</td>
                    <td>
                      <div className="lnf-row-actions">
                        <button
                          type="button"
                          className="lnf-btn lnf-btn--ghost"
                          disabled={!viewable}
                          onClick={() => {
                            if (!viewable) return;
                            if (rowType(row) === "nfse") {
                              void openNfse(row);
                              return;
                            }
                            setPreview(row);
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
        title={
          preview
            ? rowType(preview) === "cte"
              ? `DACTE ${primaryNumber(preview)}`
              : `DANFE ${preview.invoiceNumber}`
            : "DANFE"
        }
        onClose={() => setPreview(null)}
        source={previewSource}
        mimeType="application/pdf"
        declaredType="pdf"
        fileName={
          preview
            ? rowType(preview) === "cte"
              ? `CTe-${preview.accessKey}.pdf`
              : `NFe-${preview.accessKey}.pdf`
            : null
        }
        portalScopeClassName="dashboard-lancamento-notas-fiscais"
        labels={
          preview && rowType(preview) === "cte"
            ? { loading: "Abrindo o DACTE…", loadFailed: "Não foi possível abrir o DACTE." }
            : { loading: "Abrindo o DANFE…", loadFailed: "Não foi possível abrir o DANFE." }
        }
      />
      {nfseRow ? (
        <NfseDataModal
          row={nfseRow}
          detail={nfseDetail}
          loading={nfseLoading}
          error={nfseError}
          onClose={() => setNfseRow(null)}
          onDownload={(variant) => void downloadXml(variant)}
        />
      ) : null}
    </div>
  );
}
