import { X } from "lucide-react";
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
import { branchAriaLabel, branchShortLabel } from "../../../domain/branchLabels";
import {
  myRequestsPath,
  navigateMyRequestsPath,
} from "../../../hooks/myRequestsNavigation";
import { useRequestsPermissions } from "../../../security/RequestsPermissionsContext";
import type { RequestTypeSummary } from "../../../types/requests";
import {
  DetailFields,
  MyRequestsAvatar,
  MyRequestsEmptyState,
  MyRequestsEntityDirectoryPicker,
  MyRequestsFormActions,
  MyRequestsJourneyProgressBar,
  MyRequestsProgressTracker,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  SegmentToggle,
  SelectField,
  TextField,
  type EntityDirectoryOption,
} from "../../../ui/mrUi";
import {
  carrierToOption,
  partyToOption,
} from "../domain/entityLookupMappers";
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
import { useInvoiceLookupSearch } from "./useInvoiceLookupSearch";

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
    (code) => ({
      value: code,
      label: branchShortLabel(code),
      ariaLabel: branchAriaLabel(code),
    }),
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
  const [party, setParty] = useState<Party | null>(null);
  const [invoiceType, setInvoiceType] = useState<InvoiceType>("sale");
  const [invoiceTypeOther, setInvoiceTypeOther] = useState("");
  const [pendingProducts, setPendingProducts] = useState<EntityDirectoryOption[]>([]);
  const [items, setItems] = useState<IssuanceItem[]>([]);
  const [freightMode, setFreightMode] = useState<FreightMode>("cif");
  const [carrier, setCarrier] = useState<Carrier | null>(null);
  const [weightKg, setWeightKg] = useState("1");
  const [volumeCount, setVolumeCount] = useState("1");
  const [observation, setObservation] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const headingRef = useRef<HTMLHeadingElement>(null);
  const lookups = useInvoiceLookupSearch(partyType);

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

  function selectParty(hit: Party) {
    lookups.rememberParty(hit);
    setParty(hit);
    if (!returnToReview) {
      setStepId("invoiceType");
    }
  }

  function onPartyPickerChange(options: EntityDirectoryOption[]) {
    setError(null);
    if (options.length === 0) {
      setParty(null);
      return;
    }
    const hit = lookups.resolveParty(options[0].id);
    if (!hit) {
      setError("Não foi possível aplicar o destinatário selecionado. Busque novamente.");
      return;
    }
    selectParty(hit);
  }

  function onCarrierPickerChange(options: EntityDirectoryOption[]) {
    setError(null);
    if (options.length === 0) {
      setCarrier(null);
      return;
    }
    const hit = lookups.resolveCarrier(options[0].id);
    if (!hit) {
      setError("Não foi possível aplicar a transportadora selecionada. Busque novamente.");
      return;
    }
    lookups.rememberCarrier(hit);
    setCarrier(hit);
  }

  function attachPendingProducts() {
    setError(null);
    if (pendingProducts.length === 0) return;
    const existing = new Set(items.map((item) => item.product_code));
    const toAdd: ProductHit[] = [];
    for (const option of pendingProducts) {
      if (existing.has(option.id)) continue;
      const hit = lookups.resolveProduct(option.id);
      if (!hit) {
        setError("Não foi possível anexar um dos produtos selecionados. Busque novamente.");
        return;
      }
      lookups.rememberProduct(hit);
      toAdd.push(hit);
      existing.add(hit.code);
    }
    if (toAdd.length > 0) {
      setItems((prev) =>
        applyDefaultStockWriteOff(
          [
            ...prev,
            ...toAdd.map((hit) => ({
              product_code: hit.code,
              product_description: hit.description,
              quantity: 1,
              unit_price: 0,
              stock_write_off: true,
            })),
          ],
          invoiceType,
        ),
      );
    }
    setPendingProducts([]);
  }

  function removeItem(index: number) {
    setItems((prev) => prev.filter((_, i) => i !== index));
  }

  function renderEntityChip(args: {
    entity: EntityDirectoryOption;
    label: string;
    disabled: boolean;
    onRemove: () => void;
    colorKey: string;
  }) {
    const { entity, label, disabled, onRemove, colorKey } = args;
    return (
      <span className="delpi-ui-tag-chip">
        <MyRequestsAvatar
          name={entity.label}
          colorKey={colorKey}
          size="sm"
          previewable={false}
        />
        <span>{label}</span>
        <button
          type="button"
          className="delpi-ui-tag-chip__remove"
          disabled={disabled || busy}
          aria-label={`Remover ${label}`}
          onClick={onRemove}
        >
          <X size={14} aria-hidden="true" />
        </button>
      </span>
    );
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
    showBranch && branch ? `Filial ${branchShortLabel(branch)}` : null,
    `Etapa ${currentIdx + 1} de ${WIZARD_STEPS.length}: ${stepMeta.label}`,
  ].filter(Boolean);

  function renderRecipientStep() {
    return (
      <div className="my-requests-form-stack">
        <SegmentToggle
          ariaLabel="Tipo de destinatário"
          value={partyType}
          onChange={(next) => {
            setPartyType(next);
            setParty(null);
          }}
          options={[
            { value: "customer", label: "Cliente" },
            { value: "supplier", label: "Fornecedor" },
          ]}
        />
        <MyRequestsEntityDirectoryPicker
          value={party ? [partyToOption(party)] : []}
          onChange={onPartyPickerChange}
          searchEntities={lookups.searchPartyEntities}
          maxSelected={1}
          disabled={busy}
          labels={{
            title: "Destinatário",
            hint: HELP.partySearch,
            placeholder: "Digite código, nome ou CNPJ",
            empty: "Nenhum destinatário encontrado.",
            selectedAriaLabel: "Destinatário selecionado",
          }}
          renderOptionLeading={(entity) => (
            <MyRequestsAvatar
              name={entity.label}
              colorKey={entity.id}
              size="sm"
              previewable={false}
            />
          )}
          renderSelectedChip={({ entity, label, disabled, onRemove }) =>
            renderEntityChip({
              entity,
              label,
              disabled,
              onRemove,
              colorKey: entity.id,
            })
          }
        />
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
    const attachedCodes = new Set(items.map((item) => item.product_code));
    return (
      <div className="my-requests-form-stack">
        <MyRequestsEntityDirectoryPicker
          value={pendingProducts}
          onChange={setPendingProducts}
          searchEntities={async (query, limit, signal) => {
            const hits = await lookups.searchProductEntities(query, limit, signal);
            return hits.filter((hit) => !attachedCodes.has(hit.id));
          }}
          maxSelected={20}
          disabled={busy}
          labels={{
            title: "Produtos",
            hint: HELP.productSearch,
            placeholder: "Digite código ou descrição",
            empty: "Nenhum produto encontrado.",
            emptySelected: "Nenhum resultado disponível — já selecionados ou anexados.",
            selectedAriaLabel: "Produtos pendentes de anexar",
          }}
          renderOptionLeading={(entity) => (
            <MyRequestsAvatar
              name={entity.label}
              colorKey={entity.id}
              size="sm"
              previewable={false}
            />
          )}
          renderSelectedChip={({ entity, label, disabled, onRemove }) =>
            renderEntityChip({
              entity,
              label,
              disabled,
              onRemove,
              colorKey: entity.id,
            })
          }
        />
        <MyRequestsFormActions>
          <ActionButton
            type="button"
            variant="primary"
            onClick={attachPendingProducts}
            disabled={busy || pendingProducts.length === 0}
          >
            Adicionar selecionados ({pendingProducts.length})
          </ActionButton>
        </MyRequestsFormActions>

        {items.length === 0 ? (
          <MyRequestsEmptyState
            title="Nenhum item adicionado"
            message="Busque produtos, selecione-os e use Adicionar selecionados para incluir na nota."
          />
        ) : (
          <ul className="my-requests-invoice-items">
            {items.map((item, index) => (
              <li key={`${item.product_code}-${index}`} className="my-requests-invoice-item">
                <div className="my-requests-invoice-item__title">
                  {item.product_code} — {item.product_description}
                </div>
                <div className="my-requests-invoice-item__row">
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
                        prev.map((row, i) =>
                          i === index ? { ...row, unit_price } : row,
                        ),
                      );
                    }}
                  />
                  <div className="my-requests-invoice-item__remove">
                    <ActionButton
                      type="button"
                      variant="ghost"
                      onClick={() => removeItem(index)}
                    >
                      Remover
                    </ActionButton>
                  </div>
                </div>
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
        <MyRequestsEntityDirectoryPicker
          value={carrier ? [carrierToOption(carrier)] : []}
          onChange={onCarrierPickerChange}
          searchEntities={lookups.searchCarrierEntities}
          maxSelected={1}
          disabled={busy}
          labels={{
            title: "Transportadora (opcional)",
            hint: HELP.carrierSearch,
            placeholder: "Digite código ou nome",
            empty: "Nenhuma transportadora encontrada.",
            selectedAriaLabel: "Transportadora selecionada",
          }}
          renderOptionLeading={(entity) => (
            <MyRequestsAvatar
              name={entity.label}
              colorKey={entity.id}
              size="sm"
              previewable={false}
            />
          )}
          renderSelectedChip={({ entity, label, disabled, onRemove }) =>
            renderEntityChip({
              entity,
              label,
              disabled,
              onRemove,
              colorKey: entity.id,
            })
          }
        />
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
      <div className="my-requests-wizard-stack" data-help="invoice-wizard">
        {showBranch ? (
          <div className="my-requests-wizard-branch">
            <FieldLabel label="Filial" hint={MY_REQUESTS_HELP_TOOLTIPS.new.branch} />
            <SegmentToggle
              ariaLabel="Filial"
              value={branchCode}
              onChange={setBranchCode}
              options={branchOptions}
              disabled={busy}
              widthMode="content"
              size="md"
            />
          </div>
        ) : null}

        <MyRequestsJourneyProgressBar
          value={percent}
          summary={`${completed} de ${WIZARD_STEPS.length} etapas concluídas`}
          ariaLabel={HELP.progress}
        />

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
