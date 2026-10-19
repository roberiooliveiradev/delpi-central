import { useMemo, useState } from "react";
import { NativeSelectField, formFieldShellBemClasses } from "@delpi/plugin-ui/index";

import { HostContainedDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import {
  PROCESS_ISSUE_DISCLAIMER,
  PROCESS_ISSUE_MATERIAL_CODE_MAX_LENGTH,
  PROCESS_ISSUE_NOTE_MAX_LENGTH,
  PROCESS_ISSUE_REASONS,
  PROCESS_ISSUE_REASON_REQUIRED,
  PROCESS_ISSUE_TOOL_CODE_MAX_LENGTH,
  isProcessIssueDraftValid,
  processIssueReason,
  type ProcessIssueDraft,
} from "../content/processIssue";
import type { MachineLoadOperation } from "../types";

const fieldClasses = formFieldShellBemClasses("ppc");

type Props = {
  open: boolean;
  operation: MachineLoadOperation | null;
  busy?: boolean;
  error?: string | null;
  onClose: () => void;
  onSubmit: (draft: ProcessIssueDraft) => void;
};

/** Modal compacto: motivo do catalogo process-issue + contexto somente leitura. */
export function ProcessIssueModal({
  open,
  operation,
  busy = false,
  error = null,
  onClose,
  onSubmit,
}: Props) {
  return (
    <HostContainedDialog
      open={open}
      title={copy.machineLoad.processIssue.modalTitle}
      onClose={onClose}
    >
      <ProcessIssueForm
        key={
          (operation?.production_order ?? "") +
          ":" +
          (operation?.operation_code ?? "") +
          ":" +
          (operation?.work_center ?? "")
        }
        operation={operation}
        busy={busy}
        error={error}
        onClose={onClose}
        onSubmit={onSubmit}
      />
    </HostContainedDialog>
  );
}

/** Remontado por key a cada operacao: o rascunho nunca vaza para a proxima. */
function ProcessIssueForm({
  operation,
  busy,
  error,
  onClose,
  onSubmit,
}: Omit<Props, "open">) {
  const [issueCode, setIssueCode] = useState("");
  const [auxiliary, setAuxiliary] = useState("");
  const [note, setNote] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const reason = useMemo(() => processIssueReason(issueCode), [issueCode]);
  const auxMaxLength =
    reason?.auxiliaryField === "materialCode"
      ? PROCESS_ISSUE_MATERIAL_CODE_MAX_LENGTH
      : PROCESS_ISSUE_TOOL_CODE_MAX_LENGTH;

  const reasonOptions = PROCESS_ISSUE_REASONS.map((item) => ({
    value: item.code,
    label: item.label,
  }));

  const handleSubmit = () => {
    const draft: ProcessIssueDraft = {
      issueCode,
      toolCode:
        reason?.auxiliaryField === "toolCode" ? auxiliary.trim() || null : null,
      materialCode:
        reason?.auxiliaryField === "materialCode"
          ? auxiliary.trim() || null
          : null,
      note: note.trim() || null,
    };
    if (!isProcessIssueDraftValid(draft)) {
      setValidationError(PROCESS_ISSUE_REASON_REQUIRED);
      return;
    }
    setValidationError(null);
    onSubmit(draft);
  };

  return (
    <div className="ppc-process-issue">
      <p className="ppc-process-issue__lead">
        {copy.machineLoad.processIssue.lead}
      </p>

      {operation ? (
        <dl className="ppc-process-issue__context">
          <div className="ppc-process-issue__context-row">
            <dt>{copy.machineLoad.processIssue.contextBranch}</dt>
            <dd>{operation.branch || "—"}</dd>
          </div>
          <div className="ppc-process-issue__context-row">
            <dt>{copy.machineLoad.processIssue.contextWorkCenter}</dt>
            <dd>
              {operation.work_center}
              {operation.work_center_name
                ? " — " + operation.work_center_name
                : ""}
            </dd>
          </div>
          <div className="ppc-process-issue__context-row">
            <dt>{copy.machineLoad.processIssue.contextOrder}</dt>
            <dd>
              {operation.production_order} · {operation.operation_code}
              {operation.operation_description
                ? " — " + operation.operation_description
                : ""}
            </dd>
          </div>
          {operation.product_code ? (
            <div className="ppc-process-issue__context-row">
              <dt>{copy.machineLoad.processIssue.contextProduct}</dt>
              <dd>
                {operation.product_code}
                {operation.product_description
                  ? " — " + operation.product_description
                  : ""}
              </dd>
            </div>
          ) : null}
          {operation.pa_product_code ? (
            <div className="ppc-process-issue__context-row">
              <dt>{copy.machineLoad.processIssue.contextPa}</dt>
              <dd>{operation.pa_product_code}</dd>
            </div>
          ) : null}
          {operation.tool ? (
            <div className="ppc-process-issue__context-row">
              <dt>{copy.machineLoad.processIssue.contextTool}</dt>
              <dd>{operation.tool}</dd>
            </div>
          ) : null}
        </dl>
      ) : null}

      <NativeSelectField
        id="ppc-process-issue-reason"
        label={copy.machineLoad.processIssue.reasonLabel}
        classNames={fieldClasses}
        value={issueCode}
        onChange={(value) => {
          setIssueCode(value);
          setAuxiliary("");
          setValidationError(null);
        }}
        options={reasonOptions}
        placeholderOption={copy.machineLoad.processIssue.reasonPlaceholder}
        disabled={busy}
        span
      />

      {reason?.auxiliaryField ? (
        <label
          className="ppc-process-issue__field"
          htmlFor="ppc-process-issue-auxiliary"
        >
          <span className="ppc-process-issue__field-label">
            {reason.auxiliaryLabel}
          </span>
          <input
            id="ppc-process-issue-auxiliary"
            className="ppc-process-issue__input"
            type="text"
            value={auxiliary}
            maxLength={auxMaxLength}
            placeholder={reason.auxiliaryPlaceholder ?? undefined}
            disabled={busy}
            onChange={(event) => setAuxiliary(event.target.value)}
          />
        </label>
      ) : null}

      <label className="ppc-process-issue__field" htmlFor="ppc-process-issue-note">
        <span className="ppc-process-issue__field-label">
          {copy.machineLoad.processIssue.noteLabel}
        </span>
        <textarea
          id="ppc-process-issue-note"
          className="ppc-process-issue__textarea"
          value={note}
          maxLength={PROCESS_ISSUE_NOTE_MAX_LENGTH}
          placeholder={copy.machineLoad.processIssue.notePlaceholder}
          disabled={busy}
          rows={3}
          onChange={(event) => setNote(event.target.value)}
        />
      </label>

      <p className="ppc-process-issue__disclaimer">{PROCESS_ISSUE_DISCLAIMER}</p>

      {validationError ? (
        <p className="ppc-process-issue__error" role="alert">
          {validationError}
        </p>
      ) : null}
      {error ? (
        <p className="ppc-process-issue__error" role="alert">
          {error}
        </p>
      ) : null}

      <div className="ppc-process-issue__actions">
        <button
          type="button"
          className="ppc-process-issue__cancel"
          onClick={onClose}
          disabled={busy}
        >
          {copy.machineLoad.processIssue.cancel}
        </button>
        <button
          type="button"
          className="ppc-process-issue__confirm"
          disabled={busy || !operation}
          onClick={handleSubmit}
        >
          {busy
            ? copy.machineLoad.processIssue.submitting
            : copy.machineLoad.processIssue.submit}
        </button>
      </div>
    </div>
  );
}
