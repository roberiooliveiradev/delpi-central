import { useState } from "react";
import { Info, Lock } from "lucide-react";

import { HostContainedDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";

type Props = {
  open: boolean;
  busy?: boolean;
  error?: string | null;
  onClose: () => void;
  onConfirm: (groupByTool: boolean) => void;
};

/** Modal de critérios da otimização: data de entrega sempre ativa, ferramenta opcional. */
export function MachineLoadOptimizationModal({
  open,
  busy = false,
  error = null,
  onClose,
  onConfirm,
}: Props) {
  return (
    <HostContainedDialog
      open={open}
      title={copy.machineLoad.optimization.modalTitle}
      onClose={onClose}
    >
      {/* Remonta a cada abertura: a ferramenta sempre começa desmarcada. */}
      {open ? (
        <OptimizationForm busy={busy} error={error} onClose={onClose} onConfirm={onConfirm} />
      ) : null}
    </HostContainedDialog>
  );
}

function OptimizationForm({
  busy,
  error,
  onClose,
  onConfirm,
}: Omit<Props, "open">) {
  const [groupByTool, setGroupByTool] = useState(false);
  const texts = copy.machineLoad.optimization;

  return (
    <div className="ppc-optimization">
      <p className="ppc-optimization__lead">{texts.lead}</p>

      <fieldset className="ppc-optimization__group">
        <legend className="ppc-optimization__legend">{texts.priorityLegend}</legend>
        <label className="ppc-optimization__option ppc-optimization__option--locked">
          <input type="checkbox" checked disabled aria-readonly="true" />
          <span className="ppc-optimization__option-body">
            <span className="ppc-optimization__option-title">
              {texts.deliveryDateLabel}
              <span className="ppc-optimization__badge">
                <Lock size={11} strokeWidth={2} aria-hidden />
                {texts.requiredBadge}
              </span>
            </span>
            <span className="ppc-optimization__option-hint">{texts.deliveryDateHint}</span>
          </span>
        </label>
      </fieldset>

      <fieldset className="ppc-optimization__group">
        <legend className="ppc-optimization__legend">{texts.groupingLegend}</legend>
        <label className="ppc-optimization__option">
          <input
            type="checkbox"
            checked={groupByTool}
            onChange={(event) => setGroupByTool(event.target.checked)}
            disabled={busy}
          />
          <span className="ppc-optimization__option-body">
            <span className="ppc-optimization__option-title">{texts.toolLabel}</span>
            <span className="ppc-optimization__option-hint">{texts.toolHint}</span>
            <span className="ppc-optimization__option-hint">{texts.toolFootnote}</span>
          </span>
        </label>
      </fieldset>

      <p className="ppc-optimization__note">
        <Info size={13} strokeWidth={1.9} aria-hidden />
        {texts.noToolNote}
      </p>
      <p className="ppc-optimization__note">
        <Info size={13} strokeWidth={1.9} aria-hidden />
        {texts.missingDueNote}
      </p>
      <p className="ppc-optimization__note">
        <Info size={13} strokeWidth={1.9} aria-hidden />
        {texts.startedNote} {texts.scopeNote}
      </p>

      {error ? (
        <p className="ppc-optimization__error" role="alert">
          {error}
        </p>
      ) : null}

      <div className="ppc-optimization__actions">
        <button
          type="button"
          className="ppc-optimization__cancel"
          onClick={onClose}
          disabled={busy}
        >
          {texts.cancel}
        </button>
        <button
          type="button"
          className="ppc-optimization__confirm"
          disabled={busy}
          aria-busy={busy}
          onClick={() => onConfirm(groupByTool)}
        >
          {busy ? texts.busy : texts.confirm}
        </button>
      </div>
    </div>
  );
}
