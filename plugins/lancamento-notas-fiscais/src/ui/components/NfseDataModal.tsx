import type { NfseDetail, ReceivedInvoiceItem } from "../../domain/types";
import { displayDocumentNumber } from "../../domain/fiscal";

type Props = {
  row: ReceivedInvoiceItem;
  detail: NfseDetail | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onDownload: (variant: "original" | "standard") => void;
};

export function NfseDataModal({ row, detail, loading, error, onClose, onDownload }: Props) {
  const operational = displayDocumentNumber(row.documentNumber || row.invoiceNumber);
  const original = row.providerDocumentNumber || "";
  const service = detail?.services?.[0];
  const taxes = [
    ["ISS", detail?.iss],
    ["PIS", detail?.pis],
    ["COFINS", detail?.cofins],
    ["CSLL", detail?.csll],
    ["IR", detail?.ir],
    ["INSS", detail?.inss],
  ].filter((entry) => entry[1]);

  return (
    <div className="lnf-nfse-modal" role="dialog" aria-modal="true" aria-labelledby="nfse-data-title">
      <button type="button" className="lnf-nfse-modal__backdrop" aria-label="Fechar painel" onClick={onClose} />
      <div className="lnf-card lnf-nfse-modal__panel">
        <header className="lnf-nfse-modal__header">
          <div>
            <h2 id="nfse-data-title">Dados da NFS-e</h2>
            <p className="lnf-muted">Leitura dos dados recebidos. Isto não é um DANFSE oficial.</p>
          </div>
          <button type="button" className="lnf-btn lnf-btn--ghost" onClick={onClose}>
            Fechar
          </button>
        </header>
        <dl className="lnf-nfse-facts">
          <div>
            <dt>Número operacional</dt>
            <dd>NFS-e {operational || "—"}</dd>
          </div>
          <div>
            <dt>Número original no Questor</dt>
            <dd>{original || "—"}</dd>
          </div>
          <div>
            <dt>Série</dt>
            <dd>{detail?.series || row.series || "—"}</dd>
          </div>
          <div>
            <dt>Data de emissão</dt>
            <dd>{(detail?.emissionDate || row.emissionAt || "").slice(0, 10) || "—"}</dd>
          </div>
          <div>
            <dt>Prestador</dt>
            <dd>{detail?.providerName || row.issuerName || "—"}</dd>
          </div>
          <div>
            <dt>CNPJ prestador</dt>
            <dd>{detail?.providerCnpj || row.issuerCnpj || "—"}</dd>
          </div>
          <div>
            <dt>Tomador</dt>
            <dd>{detail?.takerName || row.receiverName || "—"}</dd>
          </div>
          <div>
            <dt>CNPJ tomador</dt>
            <dd>{detail?.takerCnpj || row.receiverCnpj || "—"}</dd>
          </div>
          <div>
            <dt>Município/prefeitura</dt>
            <dd>{detail?.cityHall || row.cityHall || "—"}</dd>
          </div>
          <div>
            <dt>Valor</dt>
            <dd>{detail?.netAmount || row.amountFormatted || row.amount || "—"}</dd>
          </div>
        </dl>
        {loading ? <p className="lnf-muted">Carregando dados complementares…</p> : null}
        {error ? (
          <p className="lnf-error" role="alert">
            {error}
          </p>
        ) : null}
        {service ? (
          <section>
            <h3>Serviço</h3>
            <p>{service.description || "—"}</p>
            <p className="lnf-muted">Código {service.serviceCode || detail?.serviceCode || "—"}</p>
            {service.nbs ? <p className="lnf-muted">NBS {service.nbs}</p> : null}
          </section>
        ) : null}
        {taxes.length > 0 ? (
          <ul className="lnf-nfse-taxes">
            {taxes.map(([label, value]) => (
              <li key={label}>
                {label}: {value}
              </li>
            ))}
          </ul>
        ) : null}
        {service?.ibsCbs && Object.keys(service.ibsCbs).length > 0 ? (
          <ul className="lnf-nfse-taxes">
            {Object.entries(service.ibsCbs).map(([label, value]) => (
              <li key={label}>
                {label}: {value}
              </li>
            ))}
          </ul>
        ) : null}
        <div className="lnf-form__actions">
          <button type="button" className="lnf-btn lnf-btn--ghost" onClick={() => onDownload("original")}>
            Baixar XML original
          </button>
          <button type="button" className="lnf-btn lnf-btn--ghost" onClick={() => onDownload("standard")}>
            Baixar XML padronizado
          </button>
        </div>
      </div>
    </div>
  );
}
