import { useEffect, useMemo, useRef, useState } from "react";
import { FieldLabel, NativeCheckboxControl, NativeTextAreaControl } from "@delpi/plugin-ui/index";
import { CHECKLIST_ITEMS, II_HELP, WIZARD_STEPS, wizardStepIndex } from "../../content/helpTooltips";
import { useIssuancePermissions } from "../../application/useIssuancePermissions";
import { branchLabel, type BranchCode } from "../../constants/branch";
import type {
  Carrier,
  FreightMode,
  InvoiceType,
  IssuanceItem,
  IssuanceRequest,
  Party,
  PartyType,
} from "../../domain/types";
import { INVOICE_TYPE_LABELS } from "../../domain/status";
import * as api from "../../data/api/invoiceIssuanceApi";
import { ApiError } from "../../data/api/httpClient";
import { buildReviewChecklist } from "../../domain/reviewChecklist";
import { mergeIssuanceItems } from "../../domain/openSalesOrders";
import { applyDefaultStockWriteOff, defaultStockWriteOff } from "../../domain/stockWriteOff";
import { formatMoney, itemOriginLabel, itemTotal, roundQuantity, warehouse01BalanceHint } from "../format";
import { CarrierSearch } from "../components/CarrierSearch";
import { OpenSalesOrderPicker } from "../components/OpenSalesOrderPicker";
import { PartySearch } from "../components/PartySearch";
import { ProductSearch } from "../components/ProductSearch";
import { PageHeader } from "../components/PageHeader";
import { QuantityInput } from "../components/QuantityInput";
import { SegmentToggle, SelectField, TextField } from "../kit";

type Props = {
  mode: "create" | "edit";
  lockedBranch: BranchCode;
  requestId?: string;
  initial?: IssuanceRequest | null;
  onCancel: () => void;
  onSuccess: (id: string) => void;
};

type DraftItem = IssuanceItem & { stockHint?: string; quantity_open?: number };

const STEP_RECIPIENT = wizardStepIndex("recipient");
const STEP_INVOICE_TYPE = wizardStepIndex("invoiceType");
const STEP_ITEMS = wizardStepIndex("items");
const STEP_FREIGHT = wizardStepIndex("freight");
const STEP_EXTRAS = wizardStepIndex("extras");
const STEP_REVIEW = wizardStepIndex("review");

function clampDraftQuantity(item: DraftItem, raw: number): number {
  if (!Number.isFinite(raw)) return raw;
  const rounded = roundQuantity(raw);
  if (item.quantity_open != null && item.quantity_open > 0) {
    return Math.min(rounded, item.quantity_open);
  }
  return rounded;
}

function requestToDraft(request: IssuanceRequest) {
  return {
    partyType: request.party_type,
    party: {
      party_type: request.party_type,
      party_code: request.party_code,
      party_store: request.party_store,
      party_name: request.party_name,
      tax_id: request.tax_id,
      blocked: false,
    } as Party,
    items: request.items,
    invoiceType: request.invoice_type,
    invoiceTypeOther: request.invoice_type_other ?? "",
    freightMode: request.freight_mode,
    carrier: seedCarrier(request),
    weightKg: String(request.weight_kg),
    volumeCount: String(request.volume_count),
    observation: request.observation ?? "",
  };
}

function seedCarrier(request: IssuanceRequest): Carrier | null {
  const code = (request.carrier_code || "").trim();
  const name = (request.carrier_name || "").trim();
  if (!code && !name) return null;
  return {
    carrier_code: code,
    carrier_name: name,
    legal_name: request.carrier_legal_name || null,
    tax_id: request.carrier_tax_id || null,
    address: request.carrier_address || null,
    phone: request.carrier_phone || null,
    blocked: false,
  };
}

export function IssuanceWizardPage({
  mode,
  lockedBranch,
  requestId,
  initial,
  onCancel,
  onSuccess,
}: Props) {
  const perms = useIssuancePermissions();
  const seeded = initial ? requestToDraft(initial) : null;
  const [step, setStep] = useState(0);
  const [partyType, setPartyType] = useState<PartyType>(seeded?.partyType ?? "customer");
  const [party, setParty] = useState<Party | null>(seeded?.party ?? null);
  const [items, setItems] = useState<DraftItem[]>(seeded?.items ?? []);
  const [itemSource, setItemSource] = useState<"sales_order" | "manual">(
    seeded?.partyType === "supplier" ? "manual" : "sales_order",
  );
  const [invoiceType, setInvoiceType] = useState<InvoiceType>(seeded?.invoiceType ?? "sale");
  const [invoiceTypeOther, setInvoiceTypeOther] = useState(seeded?.invoiceTypeOther ?? "");
  const [freightMode, setFreightMode] = useState<FreightMode>(seeded?.freightMode ?? "cif");
  const [carrier, setCarrier] = useState<Carrier | null>(seeded?.carrier ?? null);
  const [weightKg, setWeightKg] = useState(seeded?.weightKg ?? "");
  const [volumeCount, setVolumeCount] = useState(seeded?.volumeCount ?? "");
  const [observation, setObservation] = useState(seeded?.observation ?? "");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const partyKey = party
    ? `${party.party_type}:${party.party_code}:${party.party_store}`
    : "";
  const prevPartyKey = useRef<string | null>(null);

  useEffect(() => {
    if (prevPartyKey.current === null) {
      prevPartyKey.current = partyKey;
      setItemSource(party?.party_type === "customer" ? "sales_order" : "manual");
      return;
    }
    if (prevPartyKey.current === partyKey) return;
    prevPartyKey.current = partyKey;
    setItems([]);
    setItemSource(party?.party_type === "customer" ? "sales_order" : "manual");
  }, [partyKey, party]);

  useEffect(() => {
    if (step !== STEP_ITEMS) return;
    const pending = items
      .map((item, index) => ({ item, index }))
      .filter(({ item }) => item.stock_write_off && !item.stockHint);
    if (pending.length === 0) return;
    const controller = new AbortController();
    void Promise.all(
      pending.map(async ({ item, index }) => {
        try {
          const balance = await api.getWarehouse01Balance(
            item.product_code,
            lockedBranch,
            controller.signal,
          );
          return { index, stockHint: warehouse01BalanceHint(balance.quantity) };
        } catch (err: unknown) {
          if ((err as { name?: string }).name === "AbortError") return null;
          return { index, stockHint: "—" };
        }
      }),
    ).then((updates) => {
      if (controller.signal.aborted) return;
      setItems((current) => {
        const next = [...current];
        for (const update of updates) {
          if (!update || !next[update.index]) continue;
          next[update.index] = { ...next[update.index], stockHint: update.stockHint };
        }
        return next;
      });
    });
    return () => controller.abort();
  }, [step, items, lockedBranch]);

  const reviewChecklist = useMemo(
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

  const canContinue = useMemo(() => {
    if (step === STEP_RECIPIENT) return Boolean(party);
    if (step === STEP_INVOICE_TYPE) {
      return invoiceType !== "other" || invoiceTypeOther.trim().length > 0;
    }
    if (step === STEP_ITEMS) {
      return (
        items.length > 0 &&
        items.every((item) => item.product_code && item.quantity > 0 && item.unit_price >= 0)
      );
    }
    if (step === STEP_FREIGHT) {
      return Boolean(freightMode) && Number(weightKg) > 0 && Number(volumeCount) > 0;
    }
    if (step === STEP_REVIEW) return Object.values(reviewChecklist).every(Boolean);
    return true;
  }, [
    step,
    party,
    items,
    invoiceType,
    invoiceTypeOther,
    freightMode,
    weightKg,
    volumeCount,
    reviewChecklist,
  ]);

  function payload() {
    if (!party) throw new Error("Destinatário obrigatório.");
    return {
      branch_code: lockedBranch,
      party_type: party.party_type,
      party_code: party.party_code,
      party_store: party.party_store,
      invoice_type: invoiceType,
      invoice_type_other: invoiceType === "other" ? invoiceTypeOther : null,
      freight_mode: freightMode,
      carrier_code: carrier?.carrier_code?.trim() || null,
      carrier_name: carrier?.carrier_name?.trim() || null,
      weight_kg: Number(weightKg),
      volume_count: Number(volumeCount),
      observation: observation.trim() || null,
      items: items.map((item) => ({
        product_code: item.product_code,
        product_description: item.product_description,
        quantity: Number(item.quantity),
        unit_price: Number(item.unit_price),
        stock_write_off: Boolean(item.stock_write_off),
        sales_order: item.sales_order || null,
        sales_order_item: item.sales_order_item || null,
        customer_order_number: item.customer_order_number || null,
      })),
    };
  }

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      let saved: IssuanceRequest;
      if (mode === "edit" && requestId) {
        saved = await api.updateReturnedRequest(requestId, payload());
        saved = await api.resubmitRequest(saved.id);
      } else {
        saved = await api.createRequest(payload());
      }
      onSuccess(saved.id);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Não foi possível enviar a solicitação.");
    } finally {
      setBusy(false);
    }
  }

  function onToggleStock(index: number, checked: boolean) {
    setItems((current) => {
      const next = [...current];
      next[index] = { ...next[index], stock_write_off: checked, stockHint: undefined };
      return next;
    });
  }

  return (
    <div className="ii-stack" data-testid="wizard-page">
      <PageHeader
        title={mode === "edit" ? "Corrigir solicitação" : "Nova solicitação de emissão"}
        subtitle={branchLabel(lockedBranch)}
        actions={
          <button type="button" className="ii-btn ii-btn--ghost" onClick={onCancel}>
            Voltar à fila
          </button>
        }
      />

      <ol className="ii-wizard" aria-label="Etapas da solicitação">
        {WIZARD_STEPS.map((item, index) => (
          <li
            key={item.id}
            className={
              index === step
                ? "ii-wizard__step ii-wizard__step--current"
                : index < step
                  ? "ii-wizard__step ii-wizard__step--done"
                  : "ii-wizard__step"
            }
          >
            <span>{index + 1}</span>
            {item.label}
          </li>
        ))}
      </ol>

      {error ? (
        <div className="ii-alert ii-error" role="alert">
          {error}
        </div>
      ) : null}

      <section className="ii-card">
        {step === STEP_RECIPIENT ? (
          <PartySearch
            partyType={partyType}
            selected={party}
            onPartyTypeChange={setPartyType}
            onSelect={setParty}
            disabled={!perms.canCreate && mode !== "edit"}
          />
        ) : null}

        {step === STEP_INVOICE_TYPE ? (
          <div className="ii-stack">
            <SelectField
              label="Tipo de nota fiscal"
              value={invoiceType}
              onChange={(value: string) => {
                const next = value as InvoiceType;
                setInvoiceType(next);
                setItems((current) => applyDefaultStockWriteOff(current, next));
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
                required
                fullWidth
              />
            ) : null}
          </div>
        ) : null}

        {step === STEP_ITEMS ? (
          <div className="ii-stack">
            {party?.party_type === "customer" ? (
              <div data-testid="item-source-toggle">
                <SegmentToggle
                  ariaLabel="Origem dos itens"
                  value={itemSource}
                  onChange={(value: string) =>
                    setItemSource(value === "manual" ? "manual" : "sales_order")
                  }
                  options={[
                    { value: "sales_order", label: "Do pedido de venda" },
                    { value: "manual", label: "Informar itens" },
                  ]}
                />
              </div>
            ) : null}

            {party?.party_type === "customer" && itemSource === "sales_order" ? (
              <OpenSalesOrderPicker
                branch={lockedBranch}
                partyCode={party.party_code}
                partyStore={party.party_store}
                stockWriteOff={defaultStockWriteOff(invoiceType)}
                onApply={(picked) =>
                  setItems((current) => mergeIssuanceItems(current, picked))
                }
              />
            ) : (
              <ProductSearch
                onPick={(product) =>
                  setItems((current) => [
                    ...current,
                    {
                      product_code: product.code,
                      product_description: product.description,
                      quantity: 1,
                      unit_price: 0,
                      stock_write_off: defaultStockWriteOff(invoiceType),
                    },
                  ])
                }
              />
            )}
            {party?.party_type === "customer" && itemSource === "sales_order" ? (
              <>
                <p className="ii-muted">Ou informe um item avulso:</p>
                <ProductSearch
                  onPick={(product) =>
                    setItems((current) => [
                      ...current,
                      {
                        product_code: product.code,
                        product_description: product.description,
                        quantity: 1,
                        unit_price: 0,
                        stock_write_off: defaultStockWriteOff(invoiceType),
                      },
                    ])
                  }
                />
              </>
            ) : null}
            {items.length === 0 ? (
              <p className="ii-muted">Inclua ao menos um item.</p>
            ) : (
              <table className="ii-table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Descrição</th>
                    <th>Origem</th>
                    <th>Qtd</th>
                    <th>Valor unit.</th>
                    <th>Baixa estoque</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {items.map((item, index) => (
                    <tr key={`${item.product_code}-${item.sales_order || "avulso"}-${index}`}>
                      <td>{item.product_code}</td>
                      <td>{item.product_description}</td>
                      <td>{itemOriginLabel(item)}</td>
                      <td>
                        <QuantityInput
                          ariaLabel={`Quantidade ${item.product_code}`}
                          value={item.quantity}
                          max={item.quantity_open}
                          min={0}
                          onChange={(next) => {
                            const copy = [...items];
                            copy[index] = {
                              ...item,
                              quantity: clampDraftQuantity(item, next),
                            };
                            setItems(copy);
                          }}
                        />
                      </td>
                      <td>
                        <input
                          aria-label={`Valor unitário ${item.product_code}`}
                          type="number"
                          min={0}
                          step="0.01"
                          value={item.unit_price}
                          onChange={(event) => {
                            const next = [...items];
                            next[index] = {
                              ...item,
                              unit_price: Number(event.target.value),
                            };
                            setItems(next);
                          }}
                        />
                      </td>
                      <td>
                        <NativeCheckboxControl
                          checked={item.stock_write_off}
                          onChange={(checked: boolean) => void onToggleStock(index, checked)}
                          label="Baixa"
                        />
                        {item.stock_write_off && item.stockHint ? (
                          <p className="ii-muted">{item.stockHint}</p>
                        ) : null}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="ii-btn ii-btn--ghost ii-btn--sm"
                          onClick={() => setItems(items.filter((_, i) => i !== index))}
                        >
                          Remover
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        ) : null}

        {step === STEP_FREIGHT ? (
          <div className="ii-stack">
            <SelectField
              label="Modalidade de transporte"
              value={freightMode}
              onChange={(value: string) => setFreightMode(value as FreightMode)}
              options={[
                { value: "cif", label: "CIF" },
                { value: "fob", label: "FOB" },
              ]}
            />
            <CarrierSearch selected={carrier} onSelect={setCarrier} />
            <TextField
              label="Peso (kg)"
              value={weightKg}
              onChange={setWeightKg}
              required
            />
            <TextField
              label="Volumes"
              value={volumeCount}
              onChange={setVolumeCount}
              required
            />
          </div>
        ) : null}

        {step === STEP_EXTRAS ? (
          <div className="ii-stack">
            <div className="ii-field">
              <FieldLabel label="Observação" htmlFor="ii-observation" hint={II_HELP.observation} />
              <NativeTextAreaControl
                id="ii-observation"
                value={observation}
                onChange={setObservation}
                rows={4}
              />
            </div>
          </div>
        ) : null}

        {step === STEP_REVIEW ? (
          <div className="ii-stack" data-testid="wizard-review">
            <p>
              {party?.party_name} · {items.length} item(ns) · {INVOICE_TYPE_LABELS[invoiceType]} ·{" "}
              {freightMode.toUpperCase()}
              {carrier?.carrier_name ? ` · ${carrier.carrier_name}` : " · sem transportadora"} ·{" "}
              {formatMoney(
                items.reduce((sum, item) => sum + itemTotal(item.quantity, item.unit_price), 0),
              )}
            </p>
            {observation.trim() ? <p className="ii-muted">{observation.trim()}</p> : null}
            {CHECKLIST_ITEMS.map((item) => (
              <NativeCheckboxControl
                key={item.key}
                checked={reviewChecklist[item.key]}
                disabled
                onChange={() => undefined}
                label={item.label}
              />
            ))}
            <p className="ii-muted">{II_HELP.checklistFooter}</p>
          </div>
        ) : null}

        <div className="ii-wizard__actions">
          <button
            type="button"
            className="ii-btn ii-btn--ghost"
            disabled={step === STEP_RECIPIENT || busy}
            onClick={() => setStep((current) => Math.max(0, current - 1))}
          >
            Voltar
          </button>
          {step < WIZARD_STEPS.length - 1 ? (
            <button
              type="button"
              className="ii-btn ii-btn--primary"
              disabled={!canContinue || busy}
              onClick={() => setStep((current) => current + 1)}
            >
              Continuar
            </button>
          ) : (
            <button
              type="button"
              className="ii-btn ii-btn--primary"
              disabled={!canContinue || busy}
              onClick={() => void submit()}
            >
              {busy ? "Enviando…" : "Enviar solicitação"}
            </button>
          )}
        </div>
      </section>
    </div>
  );
}
