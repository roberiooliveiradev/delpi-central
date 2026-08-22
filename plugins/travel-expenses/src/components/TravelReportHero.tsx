import { useState } from "react";
import { ActionButton, BackLink, DelpiLogoMark } from "@delpi/plugin-ui/index";
import { FileText, Pencil } from "lucide-react";

import type { ReportDetail } from "../api/travelExpensesApi";
import { STATUS_LABELS, formatBrl, formatDate, UNIT_LABELS } from "../constants/labels";
import { helpTooltips } from "../content/helpTooltips";
import { navigateTravel } from "../hooks/useTravelRouterPath";
import { TravelBrandBar } from "./TravelBrandBar";
import {
  TravelFormActions,
  TravelFormGrid,
  TravelStatusBadge,
} from "../ui/travelUi";

type HeaderDraft = {
  destination: string;
  purpose: string;
  periodStart: string;
  periodEnd: string;
  costCenterCode: string;
  costCenterLabel: string;
};

type Props = {
  report: ReportDetail;
  header: HeaderDraft;
  editable: boolean;
  saving: boolean;
  onHeaderChange: (next: HeaderDraft) => void;
  onSaveHeader: () => void | Promise<void>;
  onCancelHeader: () => void;
};

function statusVariant(status: string) {
  if (status === "draft") return "info" as const;
  if (status === "returned") return "warning" as const;
  if (status === "approved" || status === "closed") return "success" as const;
  return "neutral" as const;
}

function displayValue(value: string | null | undefined, fallback = "—") {
  const text = String(value || "").trim();
  return text || fallback;
}

export function TravelReportHero({
  report,
  header,
  editable,
  saving,
  onHeaderChange,
  onSaveHeader,
  onCancelHeader,
}: Props) {
  const [editing, setEditing] = useState(false);

  function cancelEdit() {
    onCancelHeader();
    setEditing(false);
  }

  async function saveEdit() {
    try {
      await onSaveHeader();
      setEditing(false);
    } catch {
      // erro exibido pelo WorkspacePage
    }
  }

  const periodLabel =
    header.periodStart || header.periodEnd
      ? `${formatDate(header.periodStart)} – ${formatDate(header.periodEnd)}`
      : "—";
  const costCenterLabel = [header.costCenterCode, header.costCenterLabel]
    .filter(Boolean)
    .join(" — ");

  return (
    <header className="te-report-hero">
      <div className="te-report-hero__inner">
        <div className="te-report-hero__toolbar">
          <BackLink onClick={() => navigateTravel("/apps/travel-expenses/reports")}>Lista</BackLink>
          <div className="te-report-hero__toolbar-actions">
            <ActionButton
              variant="ghost"
              onClick={() => navigateTravel(`/apps/travel-expenses/reports/${report.id}/report`)}
            >
              <FileText size={16} /> Ver relatório
            </ActionButton>
          </div>
        </div>

        <div className="te-report-hero__identity">
          <span className="te-report-hero__logo" aria-hidden="true">
            <DelpiLogoMark className="te-report-hero__logo-mark" title="DELPI" />
          </span>
          <div className="te-report-hero__identity-text">
            <p className="te-report-hero__eyebrow">Despesas de Viagem</p>
            <div className="te-report-hero__title-row">
              <h1 className="te-report-hero__title">{report.number}</h1>
              <TravelStatusBadge
                label={STATUS_LABELS[report.status] || report.status}
                variant={statusVariant(report.status)}
              />
            </div>
            <p className="te-report-hero__unit">
              {UNIT_LABELS[report.unitCode] || report.unitCode}
            </p>
          </div>
        </div>

        {!editing ? (
          <div className="te-report-hero__summary">
            <h2 className="te-report-hero__destination">
              {displayValue(header.destination, "Sem destino")}
            </h2>
            {header.purpose ? (
              <p className="te-report-hero__purpose">{header.purpose}</p>
            ) : (
              <p className="te-report-hero__purpose te-muted">Motivo não informado</p>
            )}
            <div className="te-report-hero__meta">
              <div className="te-report-hero__meta-item">
                <span>Período</span>
                <strong>{periodLabel}</strong>
              </div>
              <div className="te-report-hero__meta-item">
                <span>Centro de custo</span>
                <strong>{displayValue(costCenterLabel)}</strong>
              </div>
              <div className="te-report-hero__meta-item te-report-hero__meta-item--total">
                <span>Total lançado</span>
                <strong>{formatBrl(report.totalAmountBrl)}</strong>
              </div>
            </div>
            {editable ? (
              <button
                type="button"
                className="te-report-hero__edit-btn"
                onClick={() => setEditing(true)}
              >
                <Pencil size={14} aria-hidden /> Editar cabeçalho
              </button>
            ) : null}
          </div>
        ) : (
          <div className="te-report-hero__edit">
            <TravelFormGrid>
              <label className="te-field te-field--hero">
                Destino
                <input
                  value={header.destination}
                  onChange={(event) =>
                    onHeaderChange({ ...header, destination: event.target.value })
                  }
                />
              </label>
              <label className="te-field te-field--hero">
                Motivo
                <input
                  value={header.purpose}
                  onChange={(event) => onHeaderChange({ ...header, purpose: event.target.value })}
                />
              </label>
              <label className="te-field te-field--hero">
                Início
                <input
                  type="date"
                  value={header.periodStart}
                  onChange={(event) =>
                    onHeaderChange({ ...header, periodStart: event.target.value })
                  }
                />
              </label>
              <label className="te-field te-field--hero">
                Fim
                <input
                  type="date"
                  value={header.periodEnd}
                  onChange={(event) =>
                    onHeaderChange({ ...header, periodEnd: event.target.value })
                  }
                />
              </label>
              <label className="te-field te-field--hero">
                Centro de custo (código)
                <input
                  value={header.costCenterCode}
                  onChange={(event) =>
                    onHeaderChange({ ...header, costCenterCode: event.target.value })
                  }
                  placeholder={helpTooltips.costCenter}
                />
              </label>
              <label className="te-field te-field--hero">
                Centro de custo (nome)
                <input
                  value={header.costCenterLabel}
                  onChange={(event) =>
                    onHeaderChange({ ...header, costCenterLabel: event.target.value })
                  }
                />
              </label>
            </TravelFormGrid>
            <TravelFormActions>
              <ActionButton variant="ghost" onClick={cancelEdit} disabled={saving}>
                Cancelar
              </ActionButton>
              <ActionButton variant="primary" onClick={() => void saveEdit()} disabled={saving}>
                Salvar cabeçalho
              </ActionButton>
            </TravelFormActions>
          </div>
        )}
      </div>
      <TravelBrandBar className="te-report-hero__brand-bar" />
    </header>
  );
}
