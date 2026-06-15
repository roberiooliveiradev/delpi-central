import { AlertCircle, AlertTriangle, Info } from "lucide-react";

import type { AppointmentTimeFinding } from "../types/productionOeeDetail";

type AppointmentTimeFindingsProps = {
  findings: AppointmentTimeFinding[];
};

function FindingIcon({ severity }: { severity: AppointmentTimeFinding["severity"] }) {
  if (severity === "error") {
    return <AlertCircle size={16} aria-hidden />;
  }
  if (severity === "warning") {
    return <AlertTriangle size={16} aria-hidden />;
  }
  return <Info size={16} aria-hidden />;
}

export function AppointmentTimeFindings({ findings }: AppointmentTimeFindingsProps) {
  if (!findings.length) {
    return (
      <p className="ef-time-findings__ok" role="status">
        Nenhum alerta automático identificado na análise de tempos deste apontamento.
      </p>
    );
  }

  return (
    <ul className="ef-time-findings" aria-label="Alertas da análise de tempos">
      {findings.map((finding) => (
        <li
          key={finding.code}
          className={`ef-time-findings__item ef-time-findings__item--${finding.severity}`}
        >
          <FindingIcon severity={finding.severity} />
          <div>
            <strong>{finding.message}</strong>
            {finding.detail ? <p>{finding.detail}</p> : null}
          </div>
        </li>
      ))}
    </ul>
  );
}
