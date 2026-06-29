import { Save } from "lucide-react";
import { useMemo } from "react";

import { ScopeBadge, SeverityBadge, StatusBadge } from "./StatusBadge";
import { SelectField } from "./ui/SelectField";
import { TextAreaField } from "./ui/TextAreaField";
import { branchLabel, PLAN_STATUSES } from "../constants/actionPlans";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { PlanStatus } from "../types/actionPlan";

type PlanStatusSectionProps = {
  planStatus: PlanStatus;
  planBranchCode?: string | null;
  planScope?: string | null;
  planSeverity?: string | null;
  isTerminalPlan: boolean;
  statusValue: string;
  onStatusChange: (value: string) => void;
  reopenReason: string;
  onReopenReasonChange: (value: string) => void;
  reopenTargetStatus: string;
  onReopenTargetStatusChange: (value: string) => void;
  reopenStatusOptions: { value: string; label: string }[];
  saving: string | null;
  onSaveStatus: () => void;
  onReopen: () => void;
};

export function PlanStatusSection({
  planStatus,
  planBranchCode,
  planScope,
  planSeverity,
  isTerminalPlan,
  statusValue,
  onStatusChange,
  reopenReason,
  onReopenReasonChange,
  reopenTargetStatus,
  onReopenTargetStatusChange,
  reopenStatusOptions,
  saving,
  onSaveStatus,
  onReopen,
}: PlanStatusSectionProps) {
  const statusOptions = useMemo(
    () => PLAN_STATUSES.map((item) => ({ value: item.value, label: item.label })),
    [],
  );

  return (
    <div className="pac-plan-status-bar">
      <dl className="pac-dl pac-dl--compact">
        <div>
          <dt>Status atual</dt>
          <dd>
            <StatusBadge status={planStatus} />
          </dd>
        </div>
        <div>
          <dt>Filial</dt>
          <dd>{branchLabel(planBranchCode)}</dd>
        </div>
        <div>
          <dt>Escopo</dt>
          <dd>
            <ScopeBadge scope={planScope} />
          </dd>
        </div>
        <div>
          <dt>Severidade</dt>
          <dd>
            <SeverityBadge severity={planSeverity ?? "medium"} />
          </dd>
        </div>
      </dl>
      <div className="pac-inline-form pac-plan-status-bar__actions">
        {isTerminalPlan ? (
          <>
            <TextAreaField
              id="pac-reopen-reason"
              label="Motivo da reabertura"
              hint={PAC_HELP_TOOLTIPS.detail.reopenReason}
              value={reopenReason}
              onChange={onReopenReasonChange}
              placeholder="Descreva por que o plano precisa ser reaberto…"
              rows={3}
              fullWidth
            />
            <SelectField
              id="pac-plan-reopen-status"
              label="Retomar em"
              hint={PAC_HELP_TOOLTIPS.detail.reopenTargetStatus}
              options={reopenStatusOptions}
              value={reopenTargetStatus}
              onChange={onReopenTargetStatusChange}
              searchable={false}
            />
            <button
              type="button"
              className="pac-primary-btn"
              disabled={saving === "reopen" || reopenReason.trim().length < 5}
              onClick={onReopen}
            >
              <Save size={16} />
              {saving === "reopen" ? "Reabrindo…" : "Reabrir plano"}
            </button>
          </>
        ) : (
          <>
            <SelectField
              id="pac-plan-status"
              label="Atualizar status"
              hint={PAC_HELP_TOOLTIPS.detail.updateStatus}
              options={statusOptions}
              value={statusValue}
              onChange={onStatusChange}
              searchable
            />
            <button
              type="button"
              className="pac-primary-btn"
              disabled={saving === "status"}
              onClick={onSaveStatus}
            >
              <Save size={16} />
              {saving === "status" ? "Salvando…" : "Salvar status"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
