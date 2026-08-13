import { useEffect, useMemo, useState } from "react";

import {
  CommercialActionButton,
  CommercialHostDialog,
  CommercialMultiSelectField,
  CommercialSelectField,
  CommercialStateBanner,
  CommercialTextAreaField,
  CommercialTextField,
} from "../../app/commercialUi";
import { CM_HELP } from "../../content/helpTooltips";
import { PORTFOLIO_BULK_TRANSFER_CONTENT as C } from "../../content/portfolioBulkTransferContent";
import { customerKey } from "../../shared/format";
import type { SellerPortfolio } from "../../types/portfolio";

type WizardStep = "source" | "customers" | "target" | "confirm";

const STEPS: WizardStep[] = ["source", "customers", "target", "confirm"];

type SellerPortfolioBulkTransferWizardProps = {
  open: boolean;
  busy: boolean;
  error: string | null;
  portfolios: SellerPortfolio[];
  /** Quando informado, pula a etapa de origem (ex.: detalhe da carteira). */
  initialSourceId?: string | null;
  onClose: () => void;
  onTransfer: (input: {
    sourceId: string;
    targetId: string;
    customerKeys: string[];
    reason: string;
  }) => void;
};

function stepIndex(step: WizardStep): number {
  return STEPS.indexOf(step);
}

export function SellerPortfolioBulkTransferWizard({
  open,
  busy,
  error,
  portfolios,
  initialSourceId = null,
  onClose,
  onTransfer,
}: SellerPortfolioBulkTransferWizardProps) {
  const lockedSource = Boolean(initialSourceId);
  const [step, setStep] = useState<WizardStep>(lockedSource ? "customers" : "source");
  const [sourceId, setSourceId] = useState(initialSourceId ?? "");
  const [targetId, setTargetId] = useState("");
  const [customerKeys, setCustomerKeys] = useState<string[]>([]);
  const [reason, setReason] = useState("");

  const source = useMemo(
    () => portfolios.find((item) => item.id === sourceId) ?? null,
    [portfolios, sourceId],
  );

  const target = useMemo(
    () => portfolios.find((item) => item.id === targetId) ?? null,
    [portfolios, targetId],
  );

  const sourceOptions = useMemo(
    () =>
      portfolios
        .filter((item) => item.active)
        .map((item) => ({
          value: item.id,
          label: `${item.display_name} (${item.customer_count ?? item.customers?.length ?? 0})`,
        })),
    [portfolios],
  );

  const targetOptions = useMemo(
    () =>
      portfolios
        .filter((item) => item.active && item.id !== sourceId)
        .map((item) => ({ value: item.id, label: item.display_name })),
    [portfolios, sourceId],
  );

  const customerOptions = useMemo(
    () =>
      (source?.customers ?? []).map((customer) => ({
        value: customerKey(customer.customer_code, customer.customer_store),
        label: `${customer.customer_code}/${customer.customer_store} · ${customer.customer_name?.trim() || "—"}`,
      })),
    [source],
  );

  useEffect(() => {
    if (!open) return;
    const nextSource = initialSourceId ?? "";
    setSourceId(nextSource);
    setTargetId("");
    setReason("");
    setStep(nextSource ? "customers" : "source");
    const locked = portfolios.find((item) => item.id === nextSource);
    setCustomerKeys(
      locked
        ? locked.customers.map((customer) =>
            customerKey(customer.customer_code, customer.customer_store),
          )
        : [],
    );
  }, [open, initialSourceId, portfolios]);

  useEffect(() => {
    if (!source) return;
    if (step !== "customers" && step !== "source") return;
    setCustomerKeys((current) => {
      const valid = new Set(
        source.customers.map((customer) =>
          customerKey(customer.customer_code, customer.customer_store),
        ),
      );
      const kept = current.filter((key) => valid.has(key));
      if (kept.length > 0) return kept;
      return [...valid];
    });
  }, [source, step]);

  function handleClose() {
    if (busy) return;
    onClose();
  }

  function canGoNext(): boolean {
    if (step === "source") return Boolean(sourceId);
    if (step === "customers") return customerKeys.length > 0;
    if (step === "target") return Boolean(targetId);
    return Boolean(reason.trim());
  }

  function goNext() {
    if (!canGoNext()) return;
    const index = stepIndex(step);
    if (index < STEPS.length - 1) setStep(STEPS[index + 1]);
  }

  function goBack() {
    if (busy) return;
    const index = stepIndex(step);
    if (index <= 0) return;
    if (lockedSource && STEPS[index - 1] === "source") return;
    setStep(STEPS[index - 1]);
  }

  function handleSubmit() {
    if (!sourceId || !targetId || customerKeys.length === 0 || !reason.trim()) return;
    onTransfer({
      sourceId,
      targetId,
      customerKeys,
      reason: reason.trim(),
    });
  }

  const stepLabel =
    step === "source"
      ? C.stepSource
      : step === "customers"
        ? C.stepCustomers
        : step === "target"
          ? C.stepTarget
          : C.stepConfirm;

  return (
    <CommercialHostDialog
      open={open}
      title={C.title}
      description={`${CM_HELP.sellerPortfolios.bulkTransferWizard} · Etapa: ${stepLabel}`}
      onClose={handleClose}
      footer={
        <div className="cm-portfolios-form__actions">
          <CommercialActionButton variant="ghost" onClick={handleClose} disabled={busy}>
            {C.cancel}
          </CommercialActionButton>
          {stepIndex(step) > (lockedSource ? 1 : 0) ? (
            <CommercialActionButton variant="ghost" onClick={goBack} disabled={busy}>
              {C.back}
            </CommercialActionButton>
          ) : null}
          {step !== "confirm" ? (
            <CommercialActionButton
              variant="primary"
              onClick={goNext}
              disabled={busy || !canGoNext()}
            >
              {C.next}
            </CommercialActionButton>
          ) : (
            <CommercialActionButton
              variant="primary"
              onClick={handleSubmit}
              disabled={busy || !canGoNext()}
            >
              {busy ? C.submitting : C.submit}
            </CommercialActionButton>
          )}
        </div>
      }
    >
      <div className="cm-portfolios-form">
        {error ? <CommercialStateBanner variant="error">{error}</CommercialStateBanner> : null}

        <ol className="cm-portfolios-wizard-steps" aria-label="Etapas da transferência">
          {STEPS.filter((item) => !(lockedSource && item === "source")).map((item) => (
            <li
              key={item}
              className={
                item === step
                  ? "cm-portfolios-wizard-steps__item cm-portfolios-wizard-steps__item--current"
                  : stepIndex(item) < stepIndex(step)
                    ? "cm-portfolios-wizard-steps__item cm-portfolios-wizard-steps__item--done"
                    : "cm-portfolios-wizard-steps__item"
              }
            >
              {item === "source"
                ? C.stepSource
                : item === "customers"
                  ? C.stepCustomers
                  : item === "target"
                    ? C.stepTarget
                    : C.stepConfirm}
            </li>
          ))}
        </ol>

        {step === "source" ? (
          <CommercialSelectField
            label={C.sourceLabel}
            hint={C.sourceHint}
            value={sourceId}
            onChange={(value) => {
              setSourceId(value);
              setTargetId("");
              setCustomerKeys([]);
            }}
            options={sourceOptions}
            allowEmpty
            emptyLabel={C.sourceEmpty}
            searchable
          />
        ) : null}

        {step === "customers" ? (
          customerOptions.length === 0 ? (
            <CommercialStateBanner>{C.customersEmpty}</CommercialStateBanner>
          ) : (
            <div className="cm-portfolios-form__user">
              {lockedSource || source ? (
                <CommercialTextField
                  label={C.confirmFrom}
                  hint={CM_HELP.sellerPortfolios.bulkTransferConfirmFrom}
                  value={source?.display_name ?? "—"}
                  onChange={() => undefined}
                  disabled
                />
              ) : null}
              <CommercialMultiSelectField
                label={C.customersLabel}
                hint={C.customersHint}
                options={customerOptions}
                selectedValues={customerKeys}
                onChange={setCustomerKeys}
                searchable
                showSelectedTags
              />
            </div>
          )
        ) : null}

        {step === "target" ? (
          <CommercialSelectField
            label={C.targetLabel}
            hint={C.targetHint}
            value={targetId}
            onChange={setTargetId}
            options={targetOptions}
            allowEmpty
            emptyLabel={C.targetEmpty}
            searchable
          />
        ) : null}

        {step === "confirm" ? (
          <div className="cm-portfolios-form__user">
            <p className="cm-portfolios-wizard-summary" aria-label={C.confirmSummary}>
              <strong>{C.confirmFrom}:</strong> {source?.display_name ?? "—"}
              <br />
              <strong>{C.confirmTo}:</strong> {target?.display_name ?? "—"}
              <br />
              <strong>{C.confirmCount}:</strong> {customerKeys.length.toLocaleString("pt-BR")}
            </p>
            <CommercialTextAreaField
              label={C.reasonLabel}
              hint={C.reasonHint}
              value={reason}
              onChange={setReason}
              placeholder={C.reasonPlaceholder}
              required
            />
          </div>
        ) : null}
      </div>
    </CommercialHostDialog>
  );
}
