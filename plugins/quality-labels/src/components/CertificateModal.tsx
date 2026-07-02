import { useEffect, useRef, useState } from "react";
import {
  CheckCircle2,
  Eraser,
  FileText,
  ListChecks,
  Loader2,
  Plus,
  Save,
  Search,
  Trash2,
  X,
} from "lucide-react";

import {
  fetchCertificatePdfBlob,
  getCertificate,
  saveCertificate,
  searchCustomers,
} from "../api/qualityLabelsApi";
import type {
  Certificate,
  CertificateItem,
  CertificateItemStatus,
  CertificateSampleType,
  CustomerHit,
  QualityLabel,
} from "../types/qualityLabels";

type Props = {
  label: QualityLabel;
  onClose: () => void;
  onSaved?: (message: string) => void;
};

const SAMPLE_OPTIONS: { value: CertificateSampleType; label: string }[] = [
  { value: "amostra", label: "Amostra" },
  { value: "lote_piloto", label: "Lote Piloto" },
  { value: "fornecimento", label: "Fornecimento" },
];

const STATUS_OPTIONS: {
  value: CertificateItemStatus;
  label: string;
  title: string;
  modifier: string;
}[] = [
  { value: "A", label: "A", title: "Aprovado", modifier: "approved" },
  { value: "R", label: "R", title: "Reprovado", modifier: "rejected" },
  { value: "NA", label: "N/A", title: "Não aplicável", modifier: "na" },
];

type FormState = {
  sampleType: CertificateSampleType;
  quantity: string;
  sampleQuantity: string;
  customerName: string;
  customerCode: string;
  customerStore: string;
  customerItem: string;
  customerItemRev: string;
  customerSource: "totvs" | "manual";
  delpiNotes: string;
  customerNotes: string;
  items: CertificateItem[];
};

function toForm(cert: Certificate): FormState {
  return {
    sampleType: cert.sampleType ?? "fornecimento",
    quantity: cert.quantity ?? "",
    sampleQuantity: cert.sampleQuantity ?? "",
    customerName: cert.customerName ?? "",
    customerCode: cert.customerCode ?? "",
    customerStore: cert.customerStore ?? "",
    customerItem: cert.customerItem ?? "",
    customerItemRev: cert.customerItemRev ?? "",
    customerSource: cert.customerSource ?? "manual",
    delpiNotes: cert.delpiNotes ?? "",
    customerNotes: cert.customerNotes ?? "",
    items: cert.items ?? [],
  };
}

export function CertificateModal({ label, onClose, onSaved }: Props) {
  const [certificate, setCertificate] = useState<Certificate | null>(null);
  const [form, setForm] = useState<FormState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<null | "draft" | "issue">(null);
  const [error, setError] = useState<string | null>(null);

  const [customerHits, setCustomerHits] = useState<CustomerHit[]>([]);
  const [showCustomerHits, setShowCustomerHits] = useState(false);
  const [searchingCustomers, setSearchingCustomers] = useState(false);
  const customerFieldRef = useRef<HTMLDivElement>(null);
  const skipNextCustomerSearch = useRef(false);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    getCertificate(label.id, controller.signal)
      .then((cert) => {
        setCertificate(cert);
        skipNextCustomerSearch.current = true;
        setForm(toForm(cert));
      })
      .catch((err) => {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          setError(err instanceof Error ? err.message : "Erro ao carregar o certificado.");
        }
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [label.id]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  // Busca de clientes TOTVS (SA1) por proximidade durante a digitação.
  const customerName = form?.customerName ?? "";
  useEffect(() => {
    if (skipNextCustomerSearch.current) {
      skipNextCustomerSearch.current = false;
      return;
    }
    const term = customerName.trim();
    if (term.length < 2) {
      setCustomerHits([]);
      setShowCustomerHits(false);
      return;
    }
    const controller = new AbortController();
    setSearchingCustomers(true);
    const handle = window.setTimeout(async () => {
      try {
        const hits = await searchCustomers(term, controller.signal);
        setCustomerHits(hits);
        setShowCustomerHits(hits.length > 0);
      } catch (err) {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          setCustomerHits([]);
        }
      } finally {
        setSearchingCustomers(false);
      }
    }, 350);
    return () => {
      controller.abort();
      window.clearTimeout(handle);
    };
  }, [customerName]);

  useEffect(() => {
    if (!showCustomerHits) return;
    function onClickOutside(event: MouseEvent) {
      if (
        customerFieldRef.current &&
        !customerFieldRef.current.contains(event.target as Node)
      ) {
        setShowCustomerHits(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [showCustomerHits]);

  function patch(partial: Partial<FormState>) {
    setForm((prev) => (prev ? { ...prev, ...partial } : prev));
  }

  function handleSelectCustomer(hit: CustomerHit) {
    skipNextCustomerSearch.current = true;
    patch({
      customerName: hit.name,
      customerCode: hit.code,
      customerStore: hit.store,
      customerSource: "manual",
    });
    setShowCustomerHits(false);
    setCustomerHits([]);
  }

  function setItemStatus(index: number, status: CertificateItemStatus) {
    setForm((prev) => {
      if (!prev) return prev;
      const items = prev.items.map((item, i) =>
        i === index ? { ...item, status } : item,
      );
      return { ...prev, items };
    });
  }

  function setItemDescription(index: number, description: string) {
    setForm((prev) => {
      if (!prev) return prev;
      const items = prev.items.map((item, i) =>
        i === index ? { ...item, description } : item,
      );
      return { ...prev, items };
    });
  }

  function removeItem(index: number) {
    setForm((prev) => {
      if (!prev) return prev;
      const items = prev.items
        .filter((_, i) => i !== index)
        .map((item, i) => ({ ...item, position: i + 1 }));
      return { ...prev, items };
    });
  }

  function addItem() {
    setForm((prev) => {
      if (!prev) return prev;
      const nextPosition = prev.items.length + 1;
      const item: CertificateItem = {
        position: nextPosition,
        description: "",
        status: "A",
        isCustom: true,
      };
      return { ...prev, items: [...prev.items, item] };
    });
  }

  function setAllStatus(status: CertificateItemStatus) {
    setForm((prev) =>
      prev ? { ...prev, items: prev.items.map((item) => ({ ...item, status })) } : prev,
    );
  }

  async function handleSave(issue: boolean) {
    if (!form) return;
    setSaving(issue ? "issue" : "draft");
    setError(null);
    try {
      const cert = await saveCertificate(label.id, {
        sampleType: form.sampleType,
        quantity: form.quantity.trim() || null,
        sampleQuantity: form.sampleQuantity.trim() || null,
        customerCode: form.customerCode.trim() || null,
        customerStore: form.customerStore.trim() || null,
        customerName: form.customerName.trim() || null,
        customerItem: form.customerItem.trim() || null,
        customerItemRev: form.customerItemRev.trim() || null,
        customerSource: form.customerSource,
        delpiNotes: form.delpiNotes.trim() || null,
        customerNotes: form.customerNotes.trim() || null,
        items: form.items
          .filter((item) => item.description.trim().length > 0)
          .map((item, index) => ({
            position: index + 1,
            description: item.description.trim(),
            status: item.status,
            isCustom: item.isCustom,
          })),
        issue,
      });
      setCertificate(cert);
      skipNextCustomerSearch.current = true;
      setForm(toForm(cert));
      if (issue) {
        await openPdf();
        onSaved?.("Certificado emitido com sucesso.");
      } else {
        onSaved?.("Certificado salvo como rascunho.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar o certificado.");
    } finally {
      setSaving(null);
    }
  }

  async function openPdf() {
    try {
      const blob = await fetchCertificatePdfBlob(label.id);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      window.setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao abrir o PDF.");
    }
  }

  return (
    <div className="ql-modal-overlay" onMouseDown={onClose}>
      <div
        className="ql-modal ql-modal--wide"
        role="dialog"
        aria-modal="true"
        aria-label="Certificado de qualidade"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <header className="ql-modal__header">
          <div className="ql-modal__title">
            <FileText className="ql-icon" />
            <div>
              <h2>Certificado de Qualidade</h2>
              <p>
                OP {label.productionOrder} · {label.productCode}
                {certificate?.docRef ? ` · ${certificate.docRef}` : ""}
              </p>
            </div>
          </div>
          <button type="button" className="ql-icon-btn" title="Fechar" onClick={onClose}>
            <X className="ql-icon" />
          </button>
        </header>

        <div className="ql-modal__body">
          {loading || !form ? (
            <div className="ql-state">
              <p>
                <Loader2 className="ql-icon ql-spin" /> Carregando certificado...
              </p>
            </div>
          ) : (
            <>
              {error && (
                <div className="ql-state ql-state--error">
                  <p>{error}</p>
                </div>
              )}

              <section className="ql-cert-section">
                <span className="ql-cert-section__title">Tipo de fornecimento</span>
                <div className="ql-segmented">
                  {SAMPLE_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      className={`ql-segmented__btn ${
                        form.sampleType === opt.value ? "ql-segmented__btn--active" : ""
                      }`}
                      aria-pressed={form.sampleType === opt.value}
                      onClick={() => patch({ sampleType: opt.value })}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </section>

              <section className="ql-cert-section">
                <span className="ql-cert-section__title">
                  Cliente
                  {form.customerSource === "totvs" ? (
                    <span className="ql-badge ql-badge--info ql-cert-source">via TOTVS</span>
                  ) : (
                    <span className="ql-badge ql-cert-source">manual</span>
                  )}
                </span>
                <div className="ql-cert-grid">
                  <label className="ql-field ql-field--wide">
                    <span className="ql-label-text">Nome do cliente</span>
                    <div className="ql-op-search" ref={customerFieldRef}>
                      <input
                        className="ql-input"
                        value={form.customerName}
                        onChange={(e) => patch({ customerName: e.target.value })}
                        onFocus={() => {
                          if (customerHits.length > 0) setShowCustomerHits(true);
                        }}
                        placeholder="Pesquisar cliente (SA1)…"
                        autoComplete="off"
                      />
                      {searchingCustomers ? (
                        <Loader2 className="ql-icon ql-spin ql-op-search__spin" />
                      ) : (
                        <Search className="ql-icon ql-op-search__spin" />
                      )}
                      {showCustomerHits && customerHits.length > 0 && (
                        <ul className="ql-suggestions">
                          {customerHits.map((hit) => (
                            <li key={`${hit.code}-${hit.store}`}>
                              <button
                                type="button"
                                className="ql-suggestion"
                                onClick={() => handleSelectCustomer(hit)}
                              >
                                <span className="ql-suggestion__op">{hit.name}</span>
                                <span className="ql-suggestion__unit">
                                  Cód. {hit.code}
                                  {hit.store ? ` · Loja ${hit.store}` : ""}
                                </span>
                              </button>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </label>
                  <label className="ql-field">
                    <span className="ql-label-text">Item do cliente</span>
                    <input
                      className="ql-input"
                      value={form.customerItem}
                      onChange={(e) => patch({ customerItem: e.target.value })}
                      placeholder="Ex.: 2229-07/1"
                    />
                  </label>
                  <label className="ql-field">
                    <span className="ql-label-text">Revisão</span>
                    <input
                      className="ql-input"
                      value={form.customerItemRev}
                      onChange={(e) => patch({ customerItemRev: e.target.value })}
                      placeholder="Ex.: 00"
                    />
                  </label>
                  <label className="ql-field">
                    <span className="ql-label-text">Quantidade</span>
                    <input
                      className="ql-input"
                      value={form.quantity}
                      onChange={(e) => patch({ quantity: e.target.value })}
                      placeholder="Ex.: 10 peças"
                    />
                  </label>
                  <label className="ql-field">
                    <span className="ql-label-text">Quantidade amostral</span>
                    <input
                      className="ql-input"
                      value={form.sampleQuantity}
                      onChange={(e) => patch({ sampleQuantity: e.target.value })}
                      placeholder="Ex.: 10 peças"
                    />
                  </label>
                  <div className="ql-field">
                    <span className="ql-label-text">Item Delpi / OP</span>
                    <div className="ql-cert-readonly">
                      {label.productCode} · OP {label.productionOrder}
                    </div>
                  </div>
                </div>
              </section>

              <section className="ql-cert-section">
                <div className="ql-cert-checklist-head">
                  <span className="ql-cert-section__title">
                    <ListChecks className="ql-icon" /> Checklist de inspeção
                  </span>
                  <div className="ql-cert-bulk">
                    <button
                      type="button"
                      className="ql-btn ql-btn--ghost ql-btn--sm"
                      onClick={() => setAllStatus("A")}
                    >
                      <CheckCircle2 className="ql-icon" /> Tudo Aprovado
                    </button>
                    <button
                      type="button"
                      className="ql-btn ql-btn--ghost ql-btn--sm"
                      onClick={() => setAllStatus("NA")}
                    >
                      <Eraser className="ql-icon" /> Marcar N/A
                    </button>
                  </div>
                </div>

                <ul className="ql-checklist">
                  {form.items.map((item, index) => (
                    <li key={index} className="ql-checklist__row">
                      <span className="ql-checklist__num">{index + 1}</span>
                      {item.isCustom ? (
                        <input
                          className="ql-input ql-checklist__input"
                          value={item.description}
                          onChange={(e) => setItemDescription(index, e.target.value)}
                          placeholder="Descreva o item de inspeção"
                        />
                      ) : (
                        <span className="ql-checklist__desc">{item.description}</span>
                      )}
                      <div className="ql-segmented ql-segmented--status">
                        {STATUS_OPTIONS.map((opt) => (
                          <button
                            key={opt.value}
                            type="button"
                            title={opt.title}
                            aria-pressed={item.status === opt.value}
                            className={`ql-status-btn ql-status-btn--${opt.modifier} ${
                              item.status === opt.value ? "ql-status-btn--active" : ""
                            }`}
                            onClick={() => setItemStatus(index, opt.value)}
                          >
                            {opt.label}
                          </button>
                        ))}
                      </div>
                      {item.isCustom ? (
                        <button
                          type="button"
                          className="ql-icon-btn ql-icon-btn--danger"
                          title="Remover linha"
                          onClick={() => removeItem(index)}
                        >
                          <Trash2 className="ql-icon" />
                        </button>
                      ) : (
                        <span className="ql-checklist__spacer" />
                      )}
                    </li>
                  ))}
                </ul>

                <button type="button" className="ql-btn ql-btn--ghost ql-btn--sm" onClick={addItem}>
                  <Plus className="ql-icon" /> Adicionar linha
                </button>
              </section>

              <section className="ql-cert-section">
                <div className="ql-cert-grid">
                  <label className="ql-field ql-field--wide">
                    <span className="ql-label-text">Observações Delpi</span>
                    <textarea
                      className="ql-input ql-textarea"
                      rows={2}
                      value={form.delpiNotes}
                      onChange={(e) => patch({ delpiNotes: e.target.value })}
                      placeholder="Observações da Delpi"
                    />
                  </label>
                  <label className="ql-field ql-field--wide">
                    <span className="ql-label-text">Observações do Cliente</span>
                    <textarea
                      className="ql-input ql-textarea"
                      rows={2}
                      value={form.customerNotes}
                      onChange={(e) => patch({ customerNotes: e.target.value })}
                      placeholder="Validação do projeto pelo cliente"
                    />
                  </label>
                </div>
              </section>
            </>
          )}
        </div>

        <footer className="ql-modal__footer">
          {certificate?.hasPdf && (
            <button type="button" className="ql-btn ql-btn--ghost" onClick={() => void openPdf()}>
              <FileText className="ql-icon" /> Ver PDF
            </button>
          )}
          <button
            type="button"
            className="ql-btn ql-btn--ghost"
            onClick={() => void handleSave(false)}
            disabled={saving !== null || loading}
          >
            {saving === "draft" ? <Loader2 className="ql-icon ql-spin" /> : <Save className="ql-icon" />}
            Salvar rascunho
          </button>
          <button
            type="button"
            className="ql-btn ql-btn--primary"
            onClick={() => void handleSave(true)}
            disabled={saving !== null || loading}
          >
            {saving === "issue" ? <Loader2 className="ql-icon ql-spin" /> : <FileText className="ql-icon" />}
            Emitir e gerar PDF
          </button>
        </footer>
      </div>
    </div>
  );
}
