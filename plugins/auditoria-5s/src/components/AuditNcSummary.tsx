import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  Clock3,
  MapPin,
  UserRound,
  Users,
} from "lucide-react";

import type { AuditDetail } from "../api/audit5sApi";
import { auditStatusLabel, auditStatusVariant, shiftLabel } from "../constants/audit5s";
import type { NcTreatmentStats } from "../utils/auditNc";

type Props = {
  audit: AuditDetail;
  stats: NcTreatmentStats;
};

function formatAuditDate(value: string): string {
  const [year, month, day] = value.split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}/${year}`;
}

export function AuditNcSummary({ audit, stats }: Props) {
  const statusVariant = auditStatusVariant(audit.status);
  const auditorNames = audit.auditors.map((item) => item.display_name).filter(Boolean);

  return (
    <section className="a5s-nc-summary" aria-label="Resumo da auditoria para tratamento de NC">
      <div className="a5s-nc-summary__head">
        <div>
          <p className="a5s-nc-summary__code">{audit.audit_code}</p>
          <h3 className="a5s-nc-summary__area">{audit.area_name}</h3>
        </div>
        <span className={`a5s-status-badge a5s-status-badge--${statusVariant}`}>
          {auditStatusLabel(audit.status)}
        </span>
      </div>

      <div className="a5s-nc-summary__meta">
        <span className="a5s-meta-chip">
          <UserRound size={14} aria-hidden />
          {audit.area_responsible}
        </span>
        <span className="a5s-meta-chip">
          <CalendarDays size={14} aria-hidden />
          {formatAuditDate(audit.audit_date)}
        </span>
        <span className="a5s-meta-chip">
          <MapPin size={14} aria-hidden />
          Filial {audit.branch_code}
        </span>
        <span className="a5s-meta-chip">Turno {shiftLabel(audit.shift)}</span>
        {auditorNames.length > 0 ? (
          <span className="a5s-meta-chip">
            <Users size={14} aria-hidden />
            {auditorNames.join(", ")}
          </span>
        ) : null}
      </div>

      <div className="a5s-nc-summary__stats">
        <article className="a5s-nc-stat">
          <span className="a5s-nc-stat__icon a5s-nc-stat__icon--warning" aria-hidden>
            <AlertTriangle size={16} />
          </span>
          <div>
            <span className="a5s-nc-stat__label">Critérios com NC</span>
            <strong className="a5s-nc-stat__value">{stats.total} critérios</strong>
          </div>
        </article>
        <article className="a5s-nc-stat">
          <span className="a5s-nc-stat__icon a5s-nc-stat__icon--success" aria-hidden>
            <CheckCircle2 size={16} />
          </span>
          <div>
            <span className="a5s-nc-stat__label">Ações finalizadas</span>
            <strong className="a5s-nc-stat__value">{stats.finalized} critérios</strong>
          </div>
        </article>
        <article className="a5s-nc-stat">
          <span className="a5s-nc-stat__icon a5s-nc-stat__icon--pending" aria-hidden>
            <Clock3 size={16} />
          </span>
          <div>
            <span className="a5s-nc-stat__label">Em tratamento</span>
            <strong className="a5s-nc-stat__value">{stats.inTreatment} critério{stats.inTreatment === 1 ? "" : "s"}</strong>
          </div>
        </article>
        <div className="a5s-nc-summary__progress">
          <div className="a5s-nc-summary__progress-head">
            <span>{stats.finalized} de {stats.total} ações finalizadas</span>
            <strong>{stats.progressPct}%</strong>
          </div>
          <div className="a5s-progress__track">
            <div
              className="a5s-progress__fill"
              style={{ width: `${stats.progressPct}%` }}
              role="progressbar"
              aria-valuenow={stats.progressPct}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Progresso do tratamento de NC"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
