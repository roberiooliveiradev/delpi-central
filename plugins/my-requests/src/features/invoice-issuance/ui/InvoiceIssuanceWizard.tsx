import { useMemo, useState } from "react";
import { ActionButton, FieldLabel, NativeTextAreaControl } from "@delpi/plugin-ui/index";

import { createRequest } from "../../../api/requestsApi";
import { AppShell } from "../../../components/AppShell";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import { useRequestsPermissions } from "../../../security/RequestsPermissionsContext";
import {
  MyRequestsFormActions,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  SegmentToggle,
  SelectField,
  TextField,
} from "../../../ui/mrUi";
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
    <AppShell
      title="Nova emissão de NF"
      subtitle={`Filial ${branch} · passo ${step + 1}/${WIZARD_STEPS.length}: ${stepMeta.label}`}
      canCreate
    >
      <MyRequestsSectionCard title="Wizard de emissão">
        <div data-help="invoice-wizard" title={MY_REQUESTS_HELP_TOOLTIPS.invoiceWizard.section}>
          <MyRequestsFormActions>
            {WIZARD_STEPS.map((item, index) => (
              <ActionButton
                key={item.id}
                type="button"
                variant={index === step ? "primary" : "ghost"}
                disabled={busy}
                onClick={() => setStep(index)}
              >
                {index + 1}. {item.label}
              </ActionButton>
            ))}
          </MyRequestsFormActions>

          {error ? (
            <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
          ) : null}

          {step === 0 ? (
            <div className="my-requests-form-stack">
              <SegmentToggle
                ariaLabel="Tipo de destinatário"
                value={partyType}
                onChange={setPartyType}
                options={[
                  { value: "customer", label: "Cliente" },
                  { value: "supplier", label: "Fornecedor" },
                ]}
              />
              <TextField
                label="Buscar destinatário"
                hint={MY_REQUESTS_HELP_TOOLTIPS.invoiceWizard.partySearch}
                value={partyQuery}
                onChange={setPartyQuery}
                placeholder="código, nome ou CNPJ"
              />
              <MyRequestsFormActions>
                <ActionButton type="button" variant="primary" onClick={runPartySearch}>
                  Buscar
                </ActionButton>
              </MyRequestsFormActions>
              <ul className="my-requests-domain-list">
                {partyHits.map((hit) => (
                  <li key={`${hit.party_code}-${hit.party_store}`}>
                    <ActionButton type="button" variant="link" onClick={() => setParty(hit)}>
                      {hit.party_code}/{hit.party_store} — {hit.party_name}
                    </ActionButton>
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
            <div className="my-requests-form-stack">
              <SelectField
                label="Tipo de NF"
                value={invoiceType}
                onChange={(value) => {
                  const next = value as InvoiceType;
                  setInvoiceType(next);
                  setItems((prev) => applyDefaultStockWriteOff(prev, next));
                }}
                options={Object.entries(INVOICE_TYPE_LABELS).map(([value, label]) => ({
                  value,
                  label,
                }))}
              />
              {invoiceType === "other" ? (
                <TextField
                  label="Descreva o tipo"
                  value={invoiceTypeOther}
                  onChange={setInvoiceTypeOther}
                />
              ) : null}
            </div>
          ) : null}

          {step === 2 ? (
            <div className="my-requests-form-stack">
              <TextField
                label="Buscar item"
                value={productQuery}
                onChange={setProductQuery}
              />
              <MyRequestsFormActions>
                <ActionButton type="button" variant="primary" onClick={runProductSearch}>
                  Buscar produtos
                </ActionButton>
              </MyRequestsFormActions>
              <ul className="my-requests-domain-list">
                {productHits.map((hit) => (
                  <li key={hit.code}>
                    <ActionButton type="button" variant="link" onClick={() => addProduct(hit)}>
                      {hit.code} — {hit.description}
                    </ActionButton>
                  </li>
                ))}
              </ul>
              <ul className="my-requests-domain-list">
                {items.map((item, index) => (
                  <li key={`${item.product_code}-${index}`}>
                    {item.product_code}
                    <TextField
                      label="Quantidade"
                      value={String(item.quantity)}
                      onChange={(value) => {
                        const quantity = Number(value);
                        setItems((prev) =>
                          prev.map((row, i) => (i === index ? { ...row, quantity } : row)),
                        );
                      }}
                    />
                    <TextField
                      label="Preço unitário"
                      value={String(item.unit_price)}
                      onChange={(value) => {
                        const unit_price = Number(value);
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
            <div className="my-requests-form-stack">
              <SegmentToggle
                ariaLabel="Modo de frete"
                value={freightMode}
                onChange={setFreightMode}
                options={[
                  { value: "cif", label: "CIF" },
                  { value: "fob", label: "FOB" },
                ]}
              />
              <TextField
                label="Transportadora (opcional)"
                value={carrierQuery}
                onChange={setCarrierQuery}
              />
              <MyRequestsFormActions>
                <ActionButton type="button" variant="primary" onClick={runCarrierSearch}>
                  Buscar transportadora
                </ActionButton>
              </MyRequestsFormActions>
              <ul className="my-requests-domain-list">
                {carrierHits.map((hit) => (
                  <li key={hit.carrier_code}>
                    <ActionButton type="button" variant="link" onClick={() => setCarrier(hit)}>
                      {hit.carrier_code} — {hit.carrier_name}
                    </ActionButton>
                  </li>
                ))}
              </ul>
              {carrier ? <p>Selecionada: {carrier.carrier_name}</p> : null}
            </div>
          ) : null}

          {step === 4 ? (
            <div className="my-requests-form-stack">
              <TextField label="Peso (kg)" value={weightKg} onChange={setWeightKg} />
              <TextField label="Volumes" value={volumeCount} onChange={setVolumeCount} />
              <div>
                <FieldLabel label="Observação" htmlFor="mr-nf-observation" />
                <NativeTextAreaControl
                  id="mr-nf-observation"
                  value={observation}
                  onChange={setObservation}
                  rows={3}
                />
              </div>
            </div>
          ) : null}

          {step === 5 ? (
            <div className="my-requests-form-stack">
              <ul className="my-requests-domain-list">
                {Object.entries(checklist).map(([key, ok]) => (
                  <li key={key}>
                    {ok ? "✓" : "○"} {key}
                  </li>
                ))}
              </ul>
              <MyRequestsFormActions>
                <ActionButton
                  type="button"
                  variant="primary"
                  disabled={busy || !Object.values(checklist).every(Boolean)}
                  onClick={submit}
                >
                  Enviar solicitação
                </ActionButton>
              </MyRequestsFormActions>
            </div>
          ) : null}

          <MyRequestsFormActions>
            {onCancel ? (
              <ActionButton type="button" variant="ghost" onClick={onCancel}>
                Voltar
              </ActionButton>
            ) : null}
            {step > 0 ? (
              <ActionButton
                type="button"
                variant="ghost"
                disabled={busy}
                onClick={() => setStep((s) => s - 1)}
              >
                Anterior
              </ActionButton>
            ) : null}
            {step < WIZARD_STEPS.length - 1 ? (
              <ActionButton
                type="button"
                variant="primary"
                disabled={busy}
                onClick={() => setStep((s) => s + 1)}
              >
                Próximo
              </ActionButton>
            ) : null}
          </MyRequestsFormActions>
        </div>
      </MyRequestsSectionCard>
    </AppShell>
  );
}
