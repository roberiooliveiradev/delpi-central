import { CalendarDays, MapPin, Percent, UserRound, Users } from "lucide-react";

import type { AuditDetail } from "../api/audit5sApi";
import { auditStatusLabel, auditStatusVariant, shiftLabel } from "../constants/audit5s";
import { formatPersonName } from "../utils/formatPersonName";

type Props = {
  audit: AuditDetail;
};

function formatAuditDate(value: string): string {
  const [year, month, day] = value.split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}/${year}`;
}

export function AuditDetailHero({ audit }: Props) {
  const progressPct =
    audit.progress.total > 0
      ? Math.round((audit.progress.scored / audit.progress.total) * 100)
      : 0;
  const overallScore = audit.scores.overall_percentual ?? audit.overall_score_pct;
  const statusVariant = auditStatusVariant(audit.status);
  const auditorNames = audit.auditors
    .map((item) => formatPersonName(item.display_name))
    .filter(Boolean);

  return (
    <section className="a5s-audit-hero" aria-label="Resumo da auditoria">
      <div className="a5s-audit-hero__glow" aria-hidden />
      <div className="a5s-audit-hero__top">
        <div>
          <p className="a5s-audit-hero__code">{audit.audit_code}</p>
          <h2 className="a5s-audit-hero__area">{audit.area_name}</h2>
          <p className="a5s-audit-hero__responsible">
            <UserRound size={15} aria-hidden />
            Responsável: {formatPersonName(audit.area_responsible) || audit.area_responsible}
          </p>
        </div>
        <span className={`a5s-status-badge a5s-status-badge--${statusVariant}`}>
          {auditStatusLabel(audit.status)}
        </span>
      </div>

      <div className="a5s-audit-hero__meta">
        <span className="a5s-meta-chip">
          <CalendarDays size={15} aria-hidden />
          {formatAuditDate(audit.audit_date)}
        </span>
        <span className="a5s-meta-chip">
          <MapPin size={15} aria-hidden />
          Filial {audit.branch_code}
        </span>
        <span className="a5s-meta-chip">Turno {shiftLabel(audit.shift)}</span>
        {auditorNames.length > 0 ? (
          <span className="a5s-meta-chip">
            <Users size={15} aria-hidden />
            {auditorNames.join(", ")}
          </span>
        ) : null}
      </div>

      <div className="a5s-audit-hero__kpis">
        <article className="a5s-kpi-card">
          <span className="a5s-kpi-card__label">Progresso</span>
          <strong className="a5s-kpi-card__value">{progressPct}%</strong>
          <span className="a5s-kpi-card__hint">
            {audit.progress.scored} de {audit.progress.total} critérios
          </span>
        </article>
        <article className="a5s-kpi-card">
          <span className="a5s-kpi-card__label">Pendentes</span>
          <strong className="a5s-kpi-card__value">{audit.progress.pending}</strong>
          <span className="a5s-kpi-card__hint">aguardando nota</span>
        </article>
        <article className="a5s-kpi-card a5s-kpi-card--accent">
          <span className="a5s-kpi-card__label">
            <Percent size={14} aria-hidden />
            % Geral
          </span>
          <strong className="a5s-kpi-card__value">
            {overallScore != null ? `${overallScore}%` : "—"}
          </strong>
          <span className="a5s-kpi-card__hint">média dos sensos</span>
        </article>
      </div>

      <div className="a5s-progress">
        <div className="a5s-progress__track">
          <div
            className="a5s-progress__fill"
            style={{ width: `${progressPct}%` }}
            role="progressbar"
            aria-valuenow={progressPct}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Progresso da avaliação"
          />
        </div>
        <span className="a5s-progress__label">
          {audit.progress.scored}/{audit.progress.total} critérios avaliados
        </span>
      </div>
    </section>
  );
}
