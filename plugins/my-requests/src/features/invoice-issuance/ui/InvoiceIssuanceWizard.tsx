import { useMemo, useState } from "react";

import { createRequest } from "../../../api/requestsApi";
import { AppShell } from "../../../components/AppShell";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import { useRequestsPermissions } from "../../../security/RequestsPermissionsContext";
import { buildReviewChecklist } from "../domain/reviewChecklist";
import { applyDefaultStockWriteOff } from "../domain/stockWriteOff";
import { INVOICE_TYPE_LABELS } from "../domain/status";
import type {
  Carrier,
  FreightMode,
  InvoiceType,
  IssuanceItem,
  Party,
  PartyType,
  ProductHit,
} from "../domain/types";
import { searchCarriers, searchParties, searchProducts } from "../lookupsApi";

export const WIZARD_STEPS = [
  { id: "recipient", label: "Destinatário" },
  { id: "invoiceType", label: "Tipo de NF" },
  { id: "items", label: "Itens" },
  { id: "freight", label: "Transporte" },
  { id: "extras", label: "Adicionais" },
  { id: "review", label: "Conferência" },
] as const;

type InvoiceIssuanceWizardProps = {
  lockedBranch?: string;
  onCancel?: () => void;
};

export function InvoiceIssuanceWizard({
  lockedBranch,
  onCancel,
}: InvoiceIssuanceWizardProps) {
  const access = useRequestsPermissions();
  const branch = lockedBranch || access.branches[0] || "01";
  const [step, setStep] = useState(0);
  const [partyType, setPartyType] = useState<PartyType>("customer");
  const [partyQuery, setPartyQuery] = useState("");
  const [partyHits, setPartyHits] = useState<Party[]>([]);
  const [party, setParty] = useState<Party | null>(null);
  const [invoiceType, setInvoiceType] = useState<InvoiceType>("sale");
  const [invoiceTypeOther, setInvoiceTypeOther] = useState("");
  const [productQuery, setProductQuery] = useState("");
  const [productHits, setProductHits] = useState<ProductHit[]>([]);
  const [items, setItems] = useState<IssuanceItem[]>([]);
  const [freightMode, setFreightMode] = useState<FreightMode>("cif");
  const [carrierQuery, setCarrierQuery] = useState("");
  const [carrierHits, setCarrierHits] = useState<Carrier[]>([]);
  const [carrier, setCarrier] = useState<Carrier | null>(null);
  const [weightKg, setWeightKg] = useState("1");
  const [volumeCount, setVolumeCount] = useState("1");
  const [observation, setObservation] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const checklist = useMemo(
    () =>
      buildReviewChecklist({
        party,
        items,
        invoiceType,
        invoiceTypeOther,
        freightMode,
        weightKg,
        volumeCount,
      }),
    [party, items, invoiceType, invoiceTypeOther, freightMode, weightKg, volumeCount],
  );

  async function runPartySearch() {
    setError(null);
    try {
      setPartyHits(await searchParties(partyType, partyQuery.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no lookup");
    }
  }

  async function runProductSearch() {
    setError(null);
    try {
      setProductHits(await searchProducts(productQuery.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no lookup");
    }
  }

  async function runCarrierSearch() {
    setError(null);
    try {
      setCarrierHits(await searchCarriers(carrierQuery.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no lookup");
    }
  }

  function addProduct(hit: ProductHit) {
    const next: IssuanceItem = {
      product_code: hit.code,
      product_description: hit.description,
      quantity: 1,
      unit_price: 0,
      stock_write_off: true,
    };
    setItems(applyDefaultStockWriteOff([...items, next], invoiceType));
  }

  async function submit() {
    if (!party) {
      setError("Selecione o destinatário.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const created = await createRequest({
        typeCode: "invoice-issuance",
        branchCode: branch,
        idempotencyKey: crypto.randomUUID(),
        payload: {
          party_type: party.party_type,
          party_code: party.party_code,
          party_store: party.party_store,
          party_name: party.party_name,
          tax_id: party.tax_id,
          invoice_type: invoiceType,
          invoice_type_other: invoiceType === "other" ? invoiceTypeOther : null,
          freight_mode: freightMode,
          carrier_code: carrier?.carrier_code || null,
          carrier_name: carrier?.carrier_name || null,
          weight_kg: Number(weightKg),
          volume_count: Number(volumeCount),
          observation: observation || null,
          items: items.map((item) => ({
            product_code: item.product_code,
            product_description: item.product_description,
            quantity: item.quantity,
            unit_price: item.unit_price,
            stock_write_off: item.stock_write_off,
            sales_order: item.sales_order || null,
            sales_order_item: item.sales_order_item || null,
          })),
        },
      });
      window.location.assign(`/apps/my-requests/requests/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar");
      setBusy(false);
    }
  }

  const stepMeta = WIZARD_STEPS[step];

  return (
    <AppShell title="Nova emissão de NF" canCreate>
      <section
        className="dashboard-my-requests__panel"
        data-help="invoice-wizard"
        title={MY_REQUESTS_HELP_TOOLTIPS.invoiceWizard.section}
      >
        <p className="dashboard-my-requests__muted">
          Filial {branch} · passo {step + 1}/{WIZARD_STEPS.length}: {stepMeta.label}
        </p>
        <ol className="dashboard-my-requests__nav" aria-label="Etapas do wizard">
          {WIZARD_STEPS.map((item, index) => (
            <li key={item.id}>
              <button
                type="button"
                className="dashboard-my-requests__btn"
                disabled={busy}
                onClick={() => setStep(index)}
              >
                {index + 1}. {item.label}
              </button>
            </li>
          ))}
        </ol>
        {error ? <p className="dashboard-my-requests__error">{error}</p> : null}

        {step === 0 ? (
          <div className="dashboard-my-requests__form">
            <label>
              Tipo de destinatário
              <select
                value={partyType}
                onChange={(e) => setPartyType(e.target.value as PartyType)}
              >
                <option value="customer">Cliente</option>
                <option value="supplier">Fornecedor</option>
              </select>
            </label>
            <label title={MY_REQUESTS_HELP_TOOLTIPS.invoiceWizard.partySearch}>
              Buscar destinatário
              <input
                value={partyQuery}
                onChange={(e) => setPartyQuery(e.target.value)}
                placeholder="código, nome ou CNPJ"
              />
            </label>
            <button type="button" className="dashboard-my-requests__btn" onClick={runPartySearch}>
              Buscar
            </button>
            <ul className="dashboard-my-requests__list">
              {partyHits.map((hit) => (
                <li key={`${hit.party_code}-${hit.party_store}`}>
                  <button type="button" onClick={() => setParty(hit)}>
                    {hit.party_code}/{hit.party_store} — {hit.party_name}
                  </button>
                </li>
              ))}
            </ul>
            {party ? (
              <p>
                Selecionado: <strong>{party.party_name}</strong> ({party.party_code}/
                {party.party_store})
              </p>
            ) : null}
          </div>
        ) : null}

        {step === 1 ? (
          <div className="dashboard-my-requests__form">
            <label>
              Tipo de NF
              <select
                value={invoiceType}
                onChange={(e) => {
                  const next = e.target.value as InvoiceType;
                  setInvoiceType(next);
                  setItems((prev) => applyDefaultStockWriteOff(prev, next));
                }}
              >
                {Object.entries(INVOICE_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            {invoiceType === "other" ? (
              <label>
                Descreva o tipo
                <input
                  value={invoiceTypeOther}
                  onChange={(e) => setInvoiceTypeOther(e.target.value)}
                />
              </label>
            ) : null}
          </div>
        ) : null}

        {step === 2 ? (
          <div className="dashboard-my-requests__form">
            <label>
              Buscar item
              <input
                value={productQuery}
                onChange={(e) => setProductQuery(e.target.value)}
              />
            </label>
            <button type="button" className="dashboard-my-requests__btn" onClick={runProductSearch}>
              Buscar produtos
            </button>
            <ul className="dashboard-my-requests__list">
              {productHits.map((hit) => (
                <li key={hit.code}>
                  <button type="button" onClick={() => addProduct(hit)}>
                    {hit.code} — {hit.description}
                  </button>
                </li>
              ))}
            </ul>
            <ul className="dashboard-my-requests__list">
              {items.map((item, index) => (
                <li key={`${item.product_code}-${index}`}>
                  {item.product_code} qtd{" "}
                  <input
                    type="number"
                    min={0.001}
                    step="any"
                    value={item.quantity}
                    onChange={(e) => {
                      const quantity = Number(e.target.value);
                      setItems((prev) =>
                        prev.map((row, i) => (i === index ? { ...row, quantity } : row)),
                      );
                    }}
                  />{" "}
                  preço{" "}
                  <input
                    type="number"
                    min={0}
                    step="any"
                    value={item.unit_price}
                    onChange={(e) => {
                      const unit_price = Number(e.target.value);
                      setItems((prev) =>
                        prev.map((row, i) => (i === index ? { ...row, unit_price } : row)),
                      );
                    }}
                  />
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {step === 3 ? (
          <div className="dashboard-my-requests__form">
            <label>
              Frete
              <select
                value={freightMode}
                onChange={(e) => setFreightMode(e.target.value as FreightMode)}
              >
                <option value="cif">CIF</option>
                <option value="fob">FOB</option>
              </select>
            </label>
            <label>
              Transportadora (opcional)
              <input
                value={carrierQuery}
                onChange={(e) => setCarrierQuery(e.target.value)}
              />
            </label>
            <button type="button" className="dashboard-my-requests__btn" onClick={runCarrierSearch}>
              Buscar transportadora
            </button>
            <ul className="dashboard-my-requests__list">
              {carrierHits.map((hit) => (
                <li key={hit.carrier_code}>
                  <button type="button" onClick={() => setCarrier(hit)}>
                    {hit.carrier_code} — {hit.carrier_name}
                  </button>
                </li>
              ))}
            </ul>
            {carrier ? <p>Selecionada: {carrier.carrier_name}</p> : null}
          </div>
        ) : null}

        {step === 4 ? (
          <div className="dashboard-my-requests__form">
            <label>
              Peso (kg)
              <input value={weightKg} onChange={(e) => setWeightKg(e.target.value)} />
            </label>
            <label>
              Volumes
              <input value={volumeCount} onChange={(e) => setVolumeCount(e.target.value)} />
            </label>
            <label>
              Observação
              <textarea
                rows={3}
                value={observation}
                onChange={(e) => setObservation(e.target.value)}
              />
            </label>
          </div>
        ) : null}

        {step === 5 ? (
          <div>
            <ul className="dashboard-my-requests__list">
              {Object.entries(checklist).map(([key, ok]) => (
                <li key={key}>
                  {ok ? "✓" : "○"} {key}
                </li>
              ))}
            </ul>
            <button
              type="button"
              className="dashboard-my-requests__btn"
              disabled={busy || !Object.values(checklist).every(Boolean)}
              onClick={submit}
            >
              Enviar solicitação
            </button>
          </div>
        ) : null}

        <div className="dashboard-my-requests__action-bar">
          {onCancel ? (
            <button type="button" className="dashboard-my-requests__btn" onClick={onCancel}>
              Voltar
            </button>
          ) : null}
          {step > 0 ? (
            <button
              type="button"
              className="dashboard-my-requests__btn"
              disabled={busy}
              onClick={() => setStep((s) => s - 1)}
            >
              Anterior
            </button>
          ) : null}
          {step < WIZARD_STEPS.length - 1 ? (
            <button
              type="button"
              className="dashboard-my-requests__btn"
              disabled={busy}
              onClick={() => setStep((s) => s + 1)}
            >
              Próximo
            </button>
          ) : null}
        </div>
      </section>
    </AppShell>
  );
}
