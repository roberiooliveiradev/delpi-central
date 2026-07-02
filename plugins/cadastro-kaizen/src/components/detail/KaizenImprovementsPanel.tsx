import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronUp, Plus, Sparkles } from "lucide-react";

import { fetchKaizenSavingsTimeline, updateKaizenRecord } from "../../api/kaizenApi";
import type {
  KaizenRecord,
  KaizenRevision,
  KaizenRevisionChangeType,
  KaizenSavingsTimeline,
  SavingsType,
} from "../../types/kaizen";
import { SAVINGS_TYPES } from "../../constants/kaizen";
import { formatCurrency, formatDate } from "../../utils/format";
import { savingsTypeLabel } from "../../utils/labels";
import { StateAlert } from "../StateAlert";
import { HelpTooltip } from "../ui/HelpTooltip";
import { KAIZEN_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { KaizenEvidencePanel } from "./KaizenEvidencePanel";

const CHANGE_TYPE_LABELS: Record<KaizenRevisionChangeType, string> = {
  baseline: "Baseline",
  implantacao: "Implantação",
  melhoria: "Melhoria",
  correcao: "Correção",
  descontinuacao: "Descontinuação",
  restauracao: "Restauração",
};

const CHANGE_TYPE_TONE: Record<KaizenRevisionChangeType, string> = {
  baseline: "muted",
  implantacao: "success",
  melhoria: "info",
  correcao: "warning",
  descontinuacao: "danger",
  restauracao: "info",
};

type ImprovementStatus =
  | { kind: "vigente"; until: string | null }
  | { kind: "expirada"; until: string | null }
  | { kind: "superada"; on: string };

function resolveStatus(revision: KaizenRevision): ImprovementStatus {
  if (revision.effective_until) {
    return { kind: "superada", on: revision.effective_until };
  }
  const validUntil = revision.savings_valid_until;
  if (validUntil) {
    const today = new Date();
    const limit = new Date(`${validUntil}T23:59:59`);
    if (today > limit) return { kind: "expirada", until: validUntil };
  }
  return { kind: "vigente", until: validUntil };
}

function statusBadge(status: ImprovementStatus) {
  if (status.kind === "vigente") {
    return (
      <span className="kz-badge kz-badge--current">
        Vigente{status.until ? ` até ${formatDate(status.until)}` : ""}
      </span>
    );
  }
  if (status.kind === "expirada") {
    return <span className="kz-badge kz-badge--muted">Encerrada em {formatDate(status.until)}</span>;
  }
  return <span className="kz-badge kz-badge--muted">Superada em {formatDate(status.on)}</span>;
}

const CURRENT_YEAR = new Date().getFullYear();

type LaunchForm = {
  effective_from: string;
  savings_type: SavingsType | "";
  seconds_per_occurrence: string;
  occurrences_per_day: string;
  hourly_cost: string;
  quantity_saved_per_day: string;
  unit_material_cost: string;
  fixed_daily_savings: string;
  realized_daily_savings: string;
  improvement_description: string;
  change_reason: string;
};

const EMPTY_LAUNCH: LaunchForm = {
  effective_from: new Date().toISOString().slice(0, 10),
  savings_type: "",
  seconds_per_occurrence: "",
  occurrences_per_day: "",
  hourly_cost: "",
  quantity_saved_per_day: "",
  unit_material_cost: "",
  fixed_daily_savings: "",
  realized_daily_savings: "",
  improvement_description: "",
  change_reason: "",
};

function num(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Number(trimmed.replace(",", "."));
  return Number.isFinite(parsed) ? parsed : null;
}

type Props = {
  record: KaizenRecord;
  revisions: KaizenRevision[];
  onLaunched: () => void;
};

export function KaizenImprovementsPanel({ record, revisions, onLaunched }: Props) {
  const [timeline, setTimeline] = useState<KaizenSavingsTimeline | null>(null);
  const [dateStart, setDateStart] = useState(`${CURRENT_YEAR}-01-01`);
  const [dateEnd, setDateEnd] = useState(`${CURRENT_YEAR}-12-31`);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [showLaunch, setShowLaunch] = useState(false);
  const [launch, setLaunch] = useState<LaunchForm>(EMPTY_LAUNCH);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTimeline = useCallback(async () => {
    try {
      setTimeline(await fetchKaizenSavingsTimeline(record.id, { dateStart, dateEnd }));
    } catch {
      setTimeline(null);
    }
  }, [record.id, dateStart, dateEnd]);

  useEffect(() => {
    void loadTimeline();
  }, [loadTimeline, revisions]);

  const isImplemented = record.status === "implantado";

  const orderedRevisions = useMemo(
    () => [...revisions].sort((a, b) => b.revision_number - a.revision_number),
    [revisions],
  );

  function updateLaunch<K extends keyof LaunchForm>(key: K, value: LaunchForm[K]) {
    setLaunch((current) => ({ ...current, [key]: value }));
  }

  async function submitLaunch() {
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        effective_from: launch.effective_from || undefined,
        date_implemented: launch.effective_from || undefined,
        savings_type: launch.savings_type || undefined,
        seconds_per_occurrence: num(launch.seconds_per_occurrence),
        occurrences_per_day: num(launch.occurrences_per_day),
        hourly_cost: num(launch.hourly_cost),
        quantity_saved_per_day: num(launch.quantity_saved_per_day),
        unit_material_cost: num(launch.unit_material_cost),
        fixed_daily_savings: num(launch.fixed_daily_savings),
        realized_daily_savings: num(launch.realized_daily_savings),
        improvement_description: launch.improvement_description.trim() || undefined,
        change_reason:
          launch.change_reason.trim() || `Nova melhoria vigente em ${launch.effective_from}`,
      };
      await updateKaizenRecord(record.id, payload);
      setShowLaunch(false);
      setLaunch(EMPTY_LAUNCH);
      onLaunched();
      await loadTimeline();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao lançar melhoria.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="kz-improvements">
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}

      <div className="kz-improvements__summary">
        <div className="kz-improvements__metric">
          <span className="kz-improvements__metric-label">
            Economia vigente hoje
            <HelpTooltip
              content={KAIZEN_HELP_TOOLTIPS.improvements.currentSavings}
              ariaLabel="Ajuda: economia vigente"
            />
          </span>
          <strong className="kz-improvements__metric-value">
            {timeline?.current.active
              ? `${formatCurrency(timeline.current.annual_savings)} / ano`
              : "Sem ganho ativo"}
          </strong>
          {timeline?.current.active && timeline.current.valid_until ? (
            <span className="kz-improvements__metric-sub">
              válida até {formatDate(timeline.current.valid_until)}
            </span>
          ) : null}
        </div>

        <div className="kz-improvements__metric">
          <span className="kz-improvements__metric-label">
            Ganho no período
            <HelpTooltip
              content={KAIZEN_HELP_TOOLTIPS.improvements.periodGain}
              ariaLabel="Ajuda: ganho no período"
            />
          </span>
          <strong className="kz-improvements__metric-value">
            {formatCurrency(timeline?.period_savings ?? null)}
          </strong>
          <div className="kz-improvements__period">
            <input
              type="date"
              value={dateStart}
              onChange={(event) => setDateStart(event.target.value)}
            />
            <span>→</span>
            <input
              type="date"
              value={dateEnd}
              onChange={(event) => setDateEnd(event.target.value)}
            />
          </div>
        </div>
      </div>

      <ol className="kz-improvements__list">
        {orderedRevisions.map((revision) => {
          const status = resolveStatus(revision);
          const tone = CHANGE_TYPE_TONE[revision.change_type] ?? "muted";
          const isOpen = expanded === revision.id;
          return (
            <li key={revision.id} className="kz-improvement">
              <div className="kz-improvement__head">
                <div className="kz-improvement__title">
                  <span className="kz-timeline__version">v{revision.revision_number}</span>
                  <span className={`kz-badge kz-badge--${tone}`}>
                    {CHANGE_TYPE_LABELS[revision.change_type] ?? revision.change_type}
                  </span>
                  {statusBadge(status)}
                </div>
                <div className="kz-improvement__savings">
                  <span>{formatCurrency(revision.daily_savings)} / dia</span>
                  <span>{formatCurrency(revision.annual_savings)} / ano</span>
                </div>
              </div>

              {revision.change_summary ? (
                <p className="kz-improvement__summary">{revision.change_summary}</p>
              ) : null}
              {revision.change_reason ? (
                <p className="kz-improvement__reason">{revision.change_reason}</p>
              ) : null}

              <p className="kz-improvement__meta">
                Vigência: {formatDate(revision.effective_from)}
                {" → "}
                {revision.effective_until ? formatDate(revision.effective_until) : "atual"}
                {revision.savings_valid_until
                  ? ` • aniversário ${formatDate(revision.savings_valid_until)}`
                  : ""}
              </p>

              <button
                type="button"
                className="kz-ghost-btn kz-improvement__toggle"
                onClick={() => setExpanded(isOpen ? null : revision.id)}
                aria-expanded={isOpen}
              >
                {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                Evidências desta melhoria
              </button>

              {isOpen ? (
                <div className="kz-improvement__evidences">
                  <KaizenEvidencePanel
                    kaizenId={record.id}
                    readOnly={false}
                    revisionId={revision.id}
                    compact
                  />
                </div>
              ) : null}
            </li>
          );
        })}
      </ol>

      {showLaunch ? (
        <div className="kz-improvement-launch">
          <h3 className="kz-improvement-launch__title">
            Lançar nova melhoria
            <HelpTooltip
              content={KAIZEN_HELP_TOOLTIPS.improvements.launch}
              ariaLabel="Ajuda: lançar melhoria"
            />
          </h3>
          <div className="kz-form-grid">
            <div className="kz-field">
              <label htmlFor="kz-imp-eff">Vigente a partir de *</label>
              <input
                id="kz-imp-eff"
                type="date"
                value={launch.effective_from}
                onChange={(event) => updateLaunch("effective_from", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-imp-type">Tipo de economia</label>
              <select
                id="kz-imp-type"
                value={launch.savings_type}
                onChange={(event) =>
                  updateLaunch("savings_type", event.target.value as SavingsType | "")
                }
              >
                <option value="">Inferir automaticamente</option>
                {SAVINGS_TYPES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="kz-field">
              <label htmlFor="kz-imp-seconds">Segundos por ocorrência</label>
              <input
                id="kz-imp-seconds"
                value={launch.seconds_per_occurrence}
                onChange={(event) => updateLaunch("seconds_per_occurrence", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-imp-occ">Ocorrências por dia</label>
              <input
                id="kz-imp-occ"
                value={launch.occurrences_per_day}
                onChange={(event) => updateLaunch("occurrences_per_day", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-imp-hourly">Custo hora (R$)</label>
              <input
                id="kz-imp-hourly"
                value={launch.hourly_cost}
                onChange={(event) => updateLaunch("hourly_cost", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-imp-qty">Quantidade economizada/dia</label>
              <input
                id="kz-imp-qty"
                value={launch.quantity_saved_per_day}
                onChange={(event) => updateLaunch("quantity_saved_per_day", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-imp-unit">Custo unitário material (R$)</label>
              <input
                id="kz-imp-unit"
                value={launch.unit_material_cost}
                onChange={(event) => updateLaunch("unit_material_cost", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-imp-fixed">Economia fixa/dia (R$)</label>
              <input
                id="kz-imp-fixed"
                value={launch.fixed_daily_savings}
                onChange={(event) => updateLaunch("fixed_daily_savings", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-imp-realized">Economia realizada/dia (R$)</label>
              <input
                id="kz-imp-realized"
                value={launch.realized_daily_savings}
                onChange={(event) => updateLaunch("realized_daily_savings", event.target.value)}
              />
            </div>
            <div className="kz-field kz-span-2">
              <label htmlFor="kz-imp-desc">O que mudou nesta melhoria</label>
              <textarea
                id="kz-imp-desc"
                value={launch.improvement_description}
                onChange={(event) => updateLaunch("improvement_description", event.target.value)}
              />
            </div>
            <div className="kz-field kz-span-2">
              <label htmlFor="kz-imp-reason">Motivo (registra na revisão)</label>
              <input
                id="kz-imp-reason"
                value={launch.change_reason}
                onChange={(event) => updateLaunch("change_reason", event.target.value)}
              />
            </div>
          </div>
          <div className="kz-improvement-launch__actions">
            <button
              type="button"
              className="kz-ghost-btn"
              onClick={() => {
                setShowLaunch(false);
                setLaunch(EMPTY_LAUNCH);
              }}
              disabled={saving}
            >
              Cancelar
            </button>
            <button
              type="button"
              className="kz-primary-btn"
              onClick={() => void submitLaunch()}
              disabled={saving}
            >
              <Sparkles size={14} aria-hidden="true" />
              {saving ? "Lançando…" : "Lançar melhoria"}
            </button>
          </div>
          <p className="kz-improvement-launch__hint">
            Tipo atual do kaizen: {savingsTypeLabel(record.savings_type)}. Após lançar, expanda a
            melhoria criada para anexar suas evidências (Antes/Depois).
          </p>
        </div>
      ) : (
        <button
          type="button"
          className="kz-primary-btn kz-improvements__launch-toggle"
          onClick={() => setShowLaunch(true)}
          disabled={!isImplemented}
          title={
            isImplemented
              ? undefined
              : "Disponível para kaizens implantados — mude o estágio para Implantado primeiro."
          }
        >
          <Plus size={14} aria-hidden="true" />
          Lançar nova melhoria
        </button>
      )}
    </div>
  );
}
