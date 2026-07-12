import {
  ArrowLeft,
  CalendarDays,
  ClipboardCheck,
  MapPin,
  Percent,
  UserRound,
  Users,
} from "lucide-react";

import type { AuditDetail } from "../api/audit5sApi";
import { auditStatusLabel, auditStatusVariant, shiftLabel } from "../constants/audit5s";
import { formatPersonName } from "../utils/formatPersonName";

type Props = {
  audit: AuditDetail;
  showBack?: boolean;
  onBack?: () => void;
};

function formatAuditDate(value: string): string {
  const [year, month, day] = value.split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}/${year}`;
}

export function AuditDetailHero({ audit, showBack, onBack }: Props) {
  const progressPct =
    audit.progress.total > 0
      ? Math.round((audit.progress.scored / audit.progress.total) * 100)
      : 0;
  const overallScore = audit.scores.overall_percentual ?? audit.overall_score_pct;
  const statusVariant = auditStatusVariant(audit.status);
  const auditorNames = audit.auditors
    .map((item) => formatPersonName(item.display_name))
    .filter(Boolean);
  const responsibleName =
    formatPersonName(audit.area_responsible) || audit.area_responsible;

  return (
    <header className="a5s-hero a5s-hero--audit-detail" aria-label="Resumo da auditoria">
      <div className="a5s-hero__glow a5s-hero__glow--primary" aria-hidden />
      <div className="a5s-hero__glow a5s-hero__glow--secondary" aria-hidden />

      <div className="a5s-hero__inner">
        <div className="a5s-hero__brand">
          <div className="a5s-hero__icon" aria-hidden>
            <ClipboardCheck size={28} strokeWidth={1.75} />
          </div>
          <div className="a5s-hero__copy">
            <p className="a5s-hero__eyebrow">
              {audit.audit_code} · Filial {audit.branch_code} · Qualidade
            </p>
            <h1 className="a5s-hero__title">{audit.area_name}</h1>
            <p className="a5s-hero__subtitle">
              <UserRound size={15} aria-hidden />
              Responsável: {responsibleName}
            </p>
          </div>
        </div>

        <div className="a5s-hero__actions">
          <span className={`a5s-status-badge a5s-status-badge--${statusVariant}`}>
            {auditStatusLabel(audit.status)}
          </span>
          {showBack && onBack ? (
            <button
              type="button"
              className="a5s-btn a5s-btn--ghost a5s-btn--header"
              onClick={onBack}
            >
              <ArrowLeft size={16} aria-hidden />
              Voltar
            </button>
          ) : null}
        </div>
      </div>

      <div className="a5s-hero-audit__meta">
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

      <div className="a5s-hero-audit__kpis">
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
            Geral
          </span>
          <strong className="a5s-kpi-card__value">
            {overallScore != null ? `${overallScore}%` : "—"}
          </strong>
          <span className="a5s-kpi-card__hint">média dos sensos</span>
        </article>
      </div>

      <div className="a5s-progress a5s-hero-audit__progress">
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
    </header>
  );
}
