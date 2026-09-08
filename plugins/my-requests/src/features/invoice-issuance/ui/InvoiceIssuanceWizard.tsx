import { useEffect, useMemo, useRef, useState } from "react";
import { ActionButton, FieldLabel, NativeTextAreaControl } from "@delpi/plugin-ui/index";

import { createRequest } from "../../../api/requestsApi";
import { AppShell } from "../../../components/AppShell";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import {
  branchCodeForCreate,
  requiresBranchField,
  showsBranchField,
} from "../../../domain/branchScope";
import {
  myRequestsPath,
  navigateMyRequestsPath,
} from "../../../hooks/myRequestsNavigation";
import { useRequestsPermissions } from "../../../security/RequestsPermissionsContext";
import type { RequestTypeSummary } from "../../../types/requests";
import {
  DetailFields,
  MyRequestsEmptyState,
  MyRequestsFormActions,
  MyRequestsJourneyProgressBar,
  MyRequestsProgressTracker,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  SegmentToggle,
  SelectField,
  TextField,
} from "../../../ui/mrUi";
import { buildReviewChecklist } from "../domain/reviewChecklist";
import {
  buildStepCompletionMap,
  canOpenStep,
  completedStepCount,
  computeStepStates,
  isStepComplete,
  progressPercent,
  resolveNextStepAfterEdit,
  type WizardStepId,
} from "../domain/stepCompletion";
import { applyDefaultStockWriteOff } from "../domain/stockWriteOff";
import {
  FREIGHT_MODE_LABELS,
  INVOICE_TYPE_LABELS,
  freightModeLabel,
  invoiceTypeLabel,
  partyTypeLabel,
} from "../domain/status";
import type {
  Carrier,
  FreightMode,
  InvoiceType,
  IssuanceItem,
  Party,
  PartyType,
  ProductHit,
} from "../domain/types";
import { WIZARD_STEPS } from "../domain/wizardSteps";
import { searchCarriers, searchParties, searchProducts } from "../lookupsApi";

export { WIZARD_STEPS } from "../domain/wizardSteps";

const HELP = MY_REQUESTS_HELP_TOOLTIPS.invoiceWizard;

const STEP_HELP: Record<WizardStepId, string> = {
  recipient: HELP.recipient,
  invoiceType: HELP.invoiceType,
  items: HELP.items,
  freight: HELP.freight,
  extras: HELP.extras,
  review: HELP.review,
};

type InvoiceIssuanceWizardProps = {
  requestType: RequestTypeSummary;
  /** @deprecated Prefer branch selection inside the wizard via branch_scope */
  lockedBranch?: string;
  onCancel?: () => void;
};

function stepIndex(stepId: WizardStepId): number {
  return WIZARD_STEPS.findIndex((step) => step.id === stepId);
}

function formatMoney(value: number): string {
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

export function InvoiceIssuanceWizard({
  requestType,
  lockedBranch,
  onCancel,
}: InvoiceIssuanceWizardProps) {
  const access = useRequestsPermissions();
  const branchOptions = (access.branches.length ? access.branches : ["01", "02"]).map(
    (code) => ({ value: code, label: code }),
  );
  const showBranch = showsBranchField(requestType.branch_scope);
  const [branchCode, setBranchCode] = useState(
    lockedBranch || branchOptions[0]?.value || "",
  );
  const branch = showBranch
    ? branchCode || branchOptions[0]?.value || ""
    : "";

  const [stepId, setStepId] = useState<WizardStepId>("recipient");
  const [returnToReview, setReturnToReview] = useState(false);
  const [compactDensity, setCompactDensity] = useState(
    () => typeof window !== "undefined" && window.innerWidth < 768,
  );

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

  const headingRef = useRef<HTMLHeadingElement>(null);

  const draft = useMemo(
    () => ({
      party,
      invoiceType,
      invoiceTypeOther,
      items,
      freightMode,
      weightKg,
      volumeCount,
    }),
    [party, invoiceType, invoiceTypeOther, items, freightMode, weightKg, volumeCount],
  );

  const completion = useMemo(() => buildStepCompletionMap(draft), [draft]);
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

  const stepStates = useMemo(
    () =>
      computeStepStates({
        currentStepId: stepId,
        completion,
      }),
    [stepId, completion],
  );

  const completed = completedStepCount(completion);
  const percent = progressPercent(completion);
  const currentComplete = isStepComplete(stepId, draft);
  const reviewReady = Object.values(checklist).every(Boolean);
  const stepMeta = WIZARD_STEPS.find((step) => step.id === stepId) ?? WIZARD_STEPS[0];
  const currentIdx = stepIndex(stepId);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 768px)");
    const sync = () => setCompactDensity(media.matches);
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  useEffect(() => {
    headingRef.current?.focus();
  }, [stepId]);

  async function runPartySearch() {
    setError(null);
    try {
      setPartyHits(await searchParties(partyType, partyQuery.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na busca de destinatário");
    }
  }

  async function runProductSearch() {
    setError(null);
    try {
      setProductHits(await searchProducts(productQuery.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na busca de produtos");
    }
  }

  async function runCarrierSearch() {
    setError(null);
    try {
      setCarrierHits(await searchCarriers(carrierQuery.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na busca de transportadora");
    }
  }

  function selectParty(hit: Party) {
    setParty(hit);
    if (!returnToReview) {
      setStepId("invoiceType");
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

  function removeItem(index: number) {
    setItems((prev) => prev.filter((_, i) => i !== index));
  }

  function goToStep(nextId: WizardStepId) {
    if (!canOpenStep(nextId, completion)) return;
    setStepId(nextId);
  }

  function openForEdit(target: WizardStepId) {
    setReturnToReview(true);
    setStepId(target);
  }

  function goBack() {
    if (currentIdx <= 0) {
      onCancel?.();
      return;
    }
    setStepId(WIZARD_STEPS[currentIdx - 1].id);
  }

  function goForward() {
    if (!currentComplete) return;
    if (returnToReview) {
      const next = resolveNextStepAfterEdit({
        editedStepId: stepId,
        completion,
        returnToReview: true,
      });
      setStepId(next);
      if (next === "review") {
        setReturnToReview(false);
      }
      return;
    }
    if (currentIdx < WIZARD_STEPS.length - 1) {
      setStepId(WIZARD_STEPS[currentIdx + 1].id);
    }
  }

  async function submit() {
    if (!party) {
      setError("Selecione o destinatário.");
      return;
    }
    if (requiresBranchField(requestType.branch_scope) && !branch.trim()) {
      setError("Selecione a filial.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const created = await createRequest({
        typeCode: "invoice-issuance",
        branchCode: branchCodeForCreate(requestType.branch_scope, branch),
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
      navigateMyRequestsPath(myRequestsPath({ requestId: created.id }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível criar a solicitação.");
      setBusy(false);
    }
  }

  const subtitleParts = [
    showBranch && branch ? `Filial ${branch}` : null,
    `Etapa ${currentIdx + 1} de ${WIZARD_STEPS.length}: ${stepMeta.label}`,
  ].filter(Boolean);

  function renderRecipientStep() {
    return (
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
          hint={HELP.partySearch}
          value={partyQuery}
          onChange={setPartyQuery}
          placeholder="código, nome ou CNPJ"
        />
        <MyRequestsFormActions>
          <ActionButton type="button" variant="primary" onClick={runPartySearch} disabled={busy}>
            Buscar
          </ActionButton>
        </MyRequestsFormActions>
        {partyHits.length > 0 ? (
          <ul className="my-requests-domain-list">
            {partyHits.map((hit) => (
              <li key={`${hit.party_code}-${hit.party_store}`}>
                <ActionButton type="button" variant="link" onClick={() => selectParty(hit)}>
                  {hit.party_code}/{hit.party_store} — {hit.party_name}
                </ActionButton>
              </li>
            ))}
          </ul>
        ) : null}
        {party ? (
          <DetailFields
            fields={[
              { label: "Nome", value: party.party_name },
              { label: "Tipo", value: partyTypeLabel(party.party_type) },
              { label: "Código", value: party.party_code },
              { label: "Loja", value: party.party_store },
              { label: "CNPJ/CPF", value: party.tax_id || "—" },
            ]}
          />
        ) : null}
      </div>
    );
  }

  function renderInvoiceTypeStep() {
    return (
      <div className="my-requests-form-stack">
        <SelectField
          label="Tipo de NF"
          hint={HELP.invoiceType}
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
    );
  }

  function renderItemsStep() {
    return (
      <div className="my-requests-form-stack">
        <TextField
          label="Buscar produto"
          hint={HELP.productSearch}
          value={productQuery}
          onChange={setProductQuery}
          placeholder="código ou descrição"
        />
        <MyRequestsFormActions>
          <ActionButton type="button" variant="primary" onClick={runProductSearch} disabled={busy}>
            Buscar
          </ActionButton>
        </MyRequestsFormActions>
        {productHits.length > 0 ? (
          <ul className="my-requests-domain-list">
            {productHits.map((hit) => (
              <li key={hit.code}>
                <ActionButton type="button" variant="link" onClick={() => addProduct(hit)}>
                  {hit.code} — {hit.description}
                </ActionButton>
              </li>
            ))}
          </ul>
        ) : null}

        {items.length === 0 ? (
          <MyRequestsEmptyState
            title="Nenhum item adicionado"
            message="Busque um produto e selecione-o para incluir na nota."
          />
        ) : (
          <ul className="my-requests-domain-list">
            {items.map((item, index) => (
              <li key={`${item.product_code}-${index}`}>
                <strong>
                  {item.product_code} — {item.product_description}
                </strong>
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
                <ActionButton type="button" variant="ghost" onClick={() => removeItem(index)}>
                  Remover
                </ActionButton>
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  function renderFreightStep() {
    return (
      <div className="my-requests-form-stack">
        <SegmentToggle
          ariaLabel="Modo de frete"
          value={freightMode}
          onChange={setFreightMode}
          options={[
            { value: "cif", label: FREIGHT_MODE_LABELS.cif },
            { value: "fob", label: FREIGHT_MODE_LABELS.fob },
          ]}
        />
        <FieldLabel label="Frete" hint={HELP.freight} />
        <TextField
          label="Transportadora (opcional)"
          hint={HELP.carrierSearch}
          value={carrierQuery}
          onChange={setCarrierQuery}
          placeholder="código ou nome"
        />
        <MyRequestsFormActions>
          <ActionButton type="button" variant="primary" onClick={runCarrierSearch} disabled={busy}>
            Buscar
          </ActionButton>
        </MyRequestsFormActions>
        {carrierHits.length > 0 ? (
          <ul className="my-requests-domain-list">
            {carrierHits.map((hit) => (
              <li key={hit.carrier_code}>
                <ActionButton type="button" variant="link" onClick={() => setCarrier(hit)}>
                  {hit.carrier_code} — {hit.carrier_name}
                </ActionButton>
              </li>
            ))}
          </ul>
        ) : null}
        {carrier ? (
          <DetailFields
            fields={[
              { label: "Código", value: carrier.carrier_code },
              { label: "Nome", value: carrier.carrier_name },
              { label: "CNPJ/CPF", value: carrier.tax_id || "—" },
            ]}
          />
        ) : null}
      </div>
    );
  }

  function renderExtrasStep() {
    return (
      <div className="my-requests-form-stack">
        <TextField label="Peso (kg)" value={weightKg} onChange={setWeightKg} />
        <TextField label="Volumes" value={volumeCount} onChange={setVolumeCount} />
        <div>
          <FieldLabel label="Observação (opcional)" htmlFor="mr-nf-observation" />
          <NativeTextAreaControl
            id="mr-nf-observation"
            value={observation}
            onChange={setObservation}
            rows={3}
          />
        </div>
      </div>
    );
  }

  function renderReviewStep() {
    const totalQty = items.reduce((sum, item) => sum + Number(item.quantity || 0), 0);
    return (
      <div className="my-requests-form-stack">
        <MyRequestsSectionCard
          title="Destinatário"
          actions={
            <ActionButton type="button" variant="ghost" onClick={() => openForEdit("recipient")}>
              Alterar
            </ActionButton>
          }
        >
          <DetailFields
            fields={[
              { label: "Nome", value: party?.party_name || "—" },
              {
                label: "Tipo",
                value: party ? partyTypeLabel(party.party_type) : "—",
              },
              {
                label: "Código / Loja",
                value: party ? `${party.party_code} / ${party.party_store}` : "—",
              },
              { label: "CNPJ/CPF", value: party?.tax_id || "—" },
            ]}
          />
        </MyRequestsSectionCard>

        <MyRequestsSectionCard
          title="Tipo de nota fiscal"
          actions={
            <ActionButton type="button" variant="ghost" onClick={() => openForEdit("invoiceType")}>
              Alterar
            </ActionButton>
          }
        >
          <DetailFields
            fields={[
              {
                label: "Tipo",
                value:
                  invoiceType === "other"
                    ? `${invoiceTypeLabel(invoiceType)} — ${invoiceTypeOther || "—"}`
                    : invoiceTypeLabel(invoiceType),
              },
            ]}
          />
        </MyRequestsSectionCard>

        <MyRequestsSectionCard
          title="Itens"
          actions={
            <ActionButton type="button" variant="ghost" onClick={() => openForEdit("items")}>
              Alterar
            </ActionButton>
          }
        >
          <DetailFields
            fields={[
              {
                label: "Resumo",
                value: `${items.length} ${items.length === 1 ? "item" : "itens"} · quantidade total ${totalQty}`,
                wide: true,
              },
            ]}
          />
          {items.length > 0 ? (
            <ul className="my-requests-domain-list">
              {items.map((item, index) => (
                <li key={`${item.product_code}-${index}`}>
                  {item.product_code} · {item.product_description} · {item.quantity} ·{" "}
                  {formatMoney(Number(item.unit_price))}
                </li>
              ))}
            </ul>
          ) : null}
        </MyRequestsSectionCard>

        <MyRequestsSectionCard
          title="Transporte"
          actions={
            <ActionButton type="button" variant="ghost" onClick={() => openForEdit("freight")}>
              Alterar
            </ActionButton>
          }
        >
          <DetailFields
            fields={[
              { label: "Frete", value: freightModeLabel(freightMode) },
              {
                label: "Transportadora",
                value: carrier
                  ? `${carrier.carrier_code} — ${carrier.carrier_name}`
                  : "Não informada",
              },
            ]}
          />
        </MyRequestsSectionCard>

        <MyRequestsSectionCard
          title="Informações adicionais"
          actions={
            <ActionButton type="button" variant="ghost" onClick={() => openForEdit("extras")}>
              Alterar
            </ActionButton>
          }
        >
          <DetailFields
            fields={[
              { label: "Peso (kg)", value: weightKg },
              { label: "Volumes", value: volumeCount },
              { label: "Observação", value: observation || "—", wide: true },
            ]}
          />
        </MyRequestsSectionCard>
      </div>
    );
  }

  function renderStepBody() {
    switch (stepId) {
      case "recipient":
        return renderRecipientStep();
      case "invoiceType":
        return renderInvoiceTypeStep();
      case "items":
        return renderItemsStep();
      case "freight":
        return renderFreightStep();
      case "extras":
        return renderExtrasStep();
      case "review":
        return renderReviewStep();
      default:
        return null;
    }
  }

  const showNext = stepId !== "review" && !returnToReview;
  const showContinue = stepId !== "review" && returnToReview;
  const showSubmit = stepId === "review";

  return (
    <AppShell title="Nova emissão de NF" subtitle={subtitleParts.join(" · ")} canCreate>
      <div className="my-requests-form-stack" data-help="invoice-wizard" title={HELP.section}>
        {showBranch ? (
          <SelectField
            label="Filial"
            hint={MY_REQUESTS_HELP_TOOLTIPS.new.branch}
            value={branchCode}
            onChange={setBranchCode}
            options={branchOptions}
            disabled={busy}
          />
        ) : null}

        <div title={HELP.progress}>
          <MyRequestsJourneyProgressBar
            value={percent}
            summary={`${completed} de ${WIZARD_STEPS.length} etapas concluídas`}
          />
        </div>

        <MyRequestsProgressTracker
          steps={stepStates}
          currentStepId={stepId}
          interactive
          density={compactDensity ? "compact" : "default"}
          ariaLabel="Etapas da emissão de nota fiscal"
          compactSummary={`Etapa atual: ${stepMeta.label}. ${completed} de ${WIZARD_STEPS.length} concluídas.`}
          onStepChange={(id) => goToStep(id as WizardStepId)}
        />

        {error ? <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner> : null}

        <MyRequestsSectionCard title={stepMeta.label} hint={STEP_HELP[stepId]}>
          <h2
            ref={headingRef}
            tabIndex={-1}
            style={{
              position: "absolute",
              width: 1,
              height: 1,
              padding: 0,
              margin: -1,
              overflow: "hidden",
              clip: "rect(0, 0, 0, 0)",
              whiteSpace: "nowrap",
              border: 0,
            }}
          >
            {stepMeta.label}
          </h2>

          {renderStepBody()}

          <MyRequestsFormActions align="end">
            <ActionButton type="button" variant="ghost" disabled={busy} onClick={goBack}>
              Voltar
            </ActionButton>
            {showNext ? (
              <ActionButton
                type="button"
                variant="primary"
                disabled={busy || !currentComplete}
                onClick={goForward}
              >
                Próximo
              </ActionButton>
            ) : null}
            {showContinue ? (
              <ActionButton
                type="button"
                variant="primary"
                disabled={busy || !currentComplete}
                onClick={goForward}
              >
                Continuar
              </ActionButton>
            ) : null}
            {showSubmit ? (
              <ActionButton
                type="button"
                variant="primary"
                disabled={busy || !reviewReady}
                onClick={submit}
              >
                Enviar
              </ActionButton>
            ) : null}
          </MyRequestsFormActions>
        </MyRequestsSectionCard>
      </div>
    </AppShell>
  );
}
