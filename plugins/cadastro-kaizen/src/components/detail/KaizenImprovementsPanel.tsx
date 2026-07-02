import { useCallback, useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronUp, PencilLine, Plus, Rocket } from "lucide-react";

import {
  createKaizenVersion,
  fetchKaizenSavingsTimeline,
  implementKaizenVersion,
  updateKaizenVersion,
} from "../../api/kaizenApi";
import type {
  KaizenFormValues,
  KaizenRecord,
  KaizenRevision,
  KaizenSavingsTimeline,
  KaizenVersionStatus,
} from "../../types/kaizen";
import { recordToFormValues } from "../../constants/kaizen";
import { formatCurrency, formatDate } from "../../utils/format";
import { StateAlert } from "../StateAlert";
import { HelpTooltip } from "../ui/HelpTooltip";
import { KAIZEN_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { KaizenEvidencePanel } from "./KaizenEvidencePanel";
import { KaizenVersionFormModal } from "./KaizenVersionFormModal";

const VERSION_STATUS_LABELS: Record<KaizenVersionStatus, string> = {
  em_andamento: "Em andamento",
  implantado: "Implantada",
  descontinuado: "Descontinuada",
  cancelado: "Cancelada",
  substituido: "Substituída",
};

const VERSION_STATUS_TONE: Record<KaizenVersionStatus, string> = {
  em_andamento: "warning",
  implantado: "success",
  descontinuado: "danger",
  cancelado: "muted",
  substituido: "muted",
};

const CURRENT_YEAR = new Date().getFullYear();
const TODAY = new Date().toISOString().slice(0, 10);

function versionStatus(revision: KaizenRevision): KaizenVersionStatus {
  return (revision.version_status as KaizenVersionStatus) ?? "implantado";
}

/** Constrói valores de formulário a partir do snapshot de uma versão (mescla no cabeçalho). */
function snapshotToFormValues(record: KaizenRecord, revision: KaizenRevision): KaizenFormValues {
  const snapshot = (revision.snapshot ?? {}) as Partial<KaizenRecord>;
  return recordToFormValues({ ...record, ...snapshot, id: record.id });
}

type Props = {
  record: KaizenRecord;
  revisions: KaizenRevision[];
  onLaunched: () => void;
};

type ModalState =
  | { kind: "create"; values: KaizenFormValues }
  | { kind: "edit"; revisionNumber: number; values: KaizenFormValues }
  | null;

export function KaizenImprovementsPanel({ record, revisions, onLaunched }: Props) {
  const [timeline, setTimeline] = useState<KaizenSavingsTimeline | null>(null);
  const [dateStart, setDateStart] = useState(`${CURRENT_YEAR}-01-01`);
  const [dateEnd, setDateEnd] = useState(`${CURRENT_YEAR}-12-31`);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [modal, setModal] = useState<ModalState>(null);
  const [implementDates, setImplementDates] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState(false);
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

  const orderedRevisions = useMemo(
    () => [...revisions].sort((a, b) => b.revision_number - a.revision_number),
    [revisions],
  );

  function openCreate() {
    // Clona a versão atual; nasce como rascunho (Em andamento).
    const cloned = { ...recordToFormValues(record), status: "em_andamento" as const };
    setModal({ kind: "create", values: cloned });
  }

  function openEdit(revision: KaizenRevision) {
    setModal({
      kind: "edit",
      revisionNumber: revision.revision_number,
      values: snapshotToFormValues(record, revision),
    });
  }

  async function handleModalSubmit(payload: Record<string, unknown>) {
    if (!modal) return;
    if (modal.kind === "create") {
      await createKaizenVersion(record.id, payload);
    } else {
      await updateKaizenVersion(record.id, modal.revisionNumber, payload);
    }
    setModal(null);
    onLaunched();
    await loadTimeline();
  }

  async function handleImplement(revisionNumber: number) {
    setBusy(true);
    setError(null);
    try {
      await implementKaizenVersion(record.id, revisionNumber, {
        effective_from: implementDates[revisionNumber] || TODAY,
      });
      onLaunched();
      await loadTimeline();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao implantar versão.");
    } finally {
      setBusy(false);
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
              versão v{timeline.current.revision_number} • válida até{" "}
              {formatDate(timeline.current.valid_until)}
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

      <div className="kz-improvements__toolbar">
        <button type="button" className="kz-primary-btn" onClick={openCreate} disabled={busy}>
          <Plus size={14} aria-hidden="true" />
          Criar nova versão
        </button>
        <HelpTooltip
          content={KAIZEN_HELP_TOOLTIPS.improvements.launch}
          ariaLabel="Ajuda: criar nova versão"
        />
      </div>

      <ol className="kz-improvements__list">
        {orderedRevisions.map((revision) => {
          const status = versionStatus(revision);
          const tone = VERSION_STATUS_TONE[status] ?? "muted";
          const isOpen = expanded === revision.id;
          const isDraft = status === "em_andamento";
          return (
            <li key={revision.id} className={`kz-improvement kz-improvement--${status}`}>
              <div className="kz-improvement__head">
                <div className="kz-improvement__title">
                  <span className="kz-timeline__version">v{revision.revision_number}</span>
                  <span className={`kz-badge kz-badge--${tone}`}>
                    {VERSION_STATUS_LABELS[status]}
                  </span>
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
                {status === "implantado" && revision.savings_valid_until
                  ? ` • aniversário ${formatDate(revision.savings_valid_until)}`
                  : ""}
              </p>

              {isDraft ? (
                <div className="kz-improvement__actions">
                  <button
                    type="button"
                    className="kz-ghost-btn"
                    onClick={() => openEdit(revision)}
                    disabled={busy}
                  >
                    <PencilLine size={14} aria-hidden="true" />
                    Editar versão
                  </button>
                  <div className="kz-improvement__implement">
                    <input
                      type="date"
                      value={implementDates[revision.revision_number] ?? TODAY}
                      onChange={(event) =>
                        setImplementDates((current) => ({
                          ...current,
                          [revision.revision_number]: event.target.value,
                        }))
                      }
                      aria-label="Data de implantação"
                    />
                    <button
                      type="button"
                      className="kz-primary-btn"
                      onClick={() => void handleImplement(revision.revision_number)}
                      disabled={busy}
                    >
                      <Rocket size={14} aria-hidden="true" />
                      Implantar
                    </button>
                    <HelpTooltip
                      content={KAIZEN_HELP_TOOLTIPS.improvements.implement}
                      ariaLabel="Ajuda: implantar versão"
                    />
                  </div>
                </div>
              ) : null}

              <button
                type="button"
                className="kz-ghost-btn kz-improvement__toggle"
                onClick={() => setExpanded(isOpen ? null : revision.id)}
                aria-expanded={isOpen}
              >
                {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                Evidências desta versão
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

      {modal ? (
        <KaizenVersionFormModal
          title={modal.kind === "create" ? "Nova versão do kaizen" : "Editar versão (rascunho)"}
          subtitle={
            modal.kind === "create"
              ? "Revise e ajuste todos os dados. A nova versão nasce Em andamento; a versão implantada atual segue contabilizando até você implantar esta."
              : "Ajustes ficam salvos no rascunho até a implantação."
          }
          initialValues={modal.values}
          submitLabel={modal.kind === "create" ? "Criar versão" : "Salvar rascunho"}
          onSubmit={handleModalSubmit}
          onClose={() => setModal(null)}
        />
      ) : null}
    </div>
  );
}
