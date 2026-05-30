import { useState } from "react";
import { CheckCircle2, Clock3 } from "lucide-react";

import type { AuditDetail } from "../api/audit5sApi";
import { formatRelativeUpdate, type NcTreatmentStats } from "../utils/auditNc";
import { AuditNcPanel } from "./AuditNcPanel";
import { AuditNcSidebar } from "./AuditNcSidebar";
import { AuditNcSummary } from "./AuditNcSummary";

type Props = {
  audit: AuditDetail;
  onAuditUpdated: (audit: AuditDetail) => void;
  onClosed: () => void;
  onRequestClose?: () => void;
};

export function AuditNcView({ audit, onAuditUpdated, onClosed, onRequestClose }: Props) {
  const [stats, setStats] = useState<NcTreatmentStats>({
    total: 0,
    registered: 0,
    inTreatment: 0,
    finalized: 0,
    pending: 0,
    progressPct: 0,
  });
  const [lastSavedAt, setLastSavedAt] = useState<number | null>(null);
  const [closeSignal, setCloseSignal] = useState(0);

  const canFinish = audit.status !== "closed" && stats.total > 0 && stats.finalized === stats.total;

  const handleFinish = () => {
    if (onRequestClose) {
      onRequestClose();
      return;
    }
    setCloseSignal((value) => value + 1);
  };

  return (
    <section className="a5s-nc-treatment">
      <div className="a5s-nc-treatment__intro">
        <p className="a5s-nc-treatment__subtitle">
          Registre ações corretivas para os critérios com nota baixa desta auditoria. Os campos são salvos
          automaticamente ao sair de cada campo.
        </p>
        {audit.status !== "closed" ? (
          <button
            type="button"
            className="a5s-btn a5s-btn--header"
            disabled={!canFinish}
            onClick={handleFinish}
          >
            <CheckCircle2 size={16} aria-hidden />
            Concluir tratamento
          </button>
        ) : null}
      </div>

      <AuditNcSummary audit={audit} stats={stats} />

      <div className="a5s-nc-treatment__layout">
        <AuditNcPanel
          audit={audit}
          onAuditUpdated={onAuditUpdated}
          onClosed={onClosed}
          onStatsChange={setStats}
          onLastSavedChange={setLastSavedAt}
          closeSignal={closeSignal}
        />
        <AuditNcSidebar />
      </div>

      <footer className="a5s-nc-treatment__footer">
        <span className="a5s-nc-treatment__updated">
          <Clock3 size={15} aria-hidden />
          {formatRelativeUpdate(lastSavedAt)}
        </span>
        {audit.status !== "closed" ? (
          <button
            type="button"
            className="a5s-btn"
            disabled={!canFinish}
            onClick={handleFinish}
          >
            <CheckCircle2 size={16} aria-hidden />
            Concluir tratamento
          </button>
        ) : null}
      </footer>
    </section>
  );
}
