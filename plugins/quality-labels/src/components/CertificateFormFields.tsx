import { useEffect, useRef, useState } from "react";
import {
  CheckCircle2,
  Eraser,
  ListChecks,
  Loader2,
  Plus,
  Search,
  Trash2,
} from "lucide-react";

import { searchCustomers } from "../api/qualityLabelsApi";
import type {
  CertificateFormState,
  CertificateItemStatus,
  CustomerHit,
} from "../types/qualityLabels";
import { SAMPLE_OPTIONS } from "../utils/certificateFormUtils";

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

type Props = {
  form: CertificateFormState;
  onChange: (partial: Partial<CertificateFormState>) => void;
  productionOrder?: string;
  productCode?: string;
  docRef?: string;
  disabled?: boolean;
};

export function CertificateFormFields({
  form,
  onChange,
  productionOrder,
  productCode,
  docRef,
  disabled = false,
}: Props) {
  const [customerHits, setCustomerHits] = useState<CustomerHit[]>([]);
  const [showCustomerHits, setShowCustomerHits] = useState(false);
  const [searchingCustomers, setSearchingCustomers] = useState(false);
  const customerFieldRef = useRef<HTMLDivElement>(null);
  const skipNextCustomerSearch = useRef(false);

  useEffect(() => {
    if (skipNextCustomerSearch.current) {
      skipNextCustomerSearch.current = false;
      return;
    }
    const term = form.customerName.trim();
    if (term.length < 2 || disabled) {
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
  }, [form.customerName, disabled]);

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

  function patch(partial: Partial<CertificateFormState>) {
    onChange(partial);
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
    const items = form.items.map((item, i) =>
      i === index ? { ...item, status } : item,
    );
    patch({ items });
  }

  function setItemDescription(index: number, description: string) {
    const items = form.items.map((item, i) =>
      i === index ? { ...item, description } : item,
    );
    patch({ items });
  }

  function removeItem(index: number) {
    const items = form.items
      .filter((_, i) => i !== index)
      .map((item, i) => ({ ...item, position: i + 1 }));
    patch({ items });
  }

  function addItem() {
    patch({
      items: [
        ...form.items,
        {
          position: form.items.length + 1,
          description: "",
          status: "A",
          isCustom: true,
        },
      ],
    });
  }

  function setAllStatus(status: CertificateItemStatus) {
    patch({ items: form.items.map((item) => ({ ...item, status })) });
  }

  return (
    <div className="ql-cert-fields">
      {docRef && (
        <p className="ql-cert-fields__ref">Referência: {docRef}</p>
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
              disabled={disabled}
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
                disabled={disabled}
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
              disabled={disabled}
            />
          </label>
          <label className="ql-field">
            <span className="ql-label-text">Revisão</span>
            <input
              className="ql-input"
              value={form.customerItemRev}
              onChange={(e) => patch({ customerItemRev: e.target.value })}
              placeholder="Ex.: 00"
              disabled={disabled}
            />
          </label>
          <label className="ql-field">
            <span className="ql-label-text">Quantidade</span>
            <input
              className="ql-input"
              value={form.quantity}
              onChange={(e) => patch({ quantity: e.target.value })}
              placeholder="Ex.: 10 peças"
              disabled={disabled}
            />
          </label>
          <label className="ql-field">
            <span className="ql-label-text">Quantidade amostral</span>
            <input
              className="ql-input"
              value={form.sampleQuantity}
              onChange={(e) => patch({ sampleQuantity: e.target.value })}
              placeholder="Ex.: 10 peças"
              disabled={disabled}
            />
          </label>
          {(productCode || productionOrder) && (
            <div className="ql-field">
              <span className="ql-label-text">Item Delpi / OP</span>
              <div className="ql-cert-readonly">
                {productCode ?? "—"}
                {productionOrder ? ` · OP ${productionOrder}` : ""}
              </div>
            </div>
          )}
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
              disabled={disabled}
              onClick={() => setAllStatus("A")}
            >
              <CheckCircle2 className="ql-icon" /> Tudo Aprovado
            </button>
            <button
              type="button"
              className="ql-btn ql-btn--ghost ql-btn--sm"
              disabled={disabled}
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
                  disabled={disabled}
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
                    disabled={disabled}
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
                  disabled={disabled}
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

        <button
          type="button"
          className="ql-btn ql-btn--ghost ql-btn--sm"
          disabled={disabled}
          onClick={addItem}
        >
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
              disabled={disabled}
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
              disabled={disabled}
            />
          </label>
        </div>
      </section>
    </div>
  );
}
