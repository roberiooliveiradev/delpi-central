import { useCallback, useEffect, useState } from "react";

import { fetchKaizenSavingsTimeline } from "../../api/kaizenApi";
import type { KaizenRecord, KaizenRevision, KaizenSavingsTimeline } from "../../types/kaizen";
import { formatCurrency, formatDate } from "../../utils/format";
import { HelpTooltip } from "../ui/HelpTooltip";
import { KAIZEN_HELP_TOOLTIPS } from "../../content/helpTooltips";

const CURRENT_YEAR = new Date().getFullYear();

type Props = {
  record: KaizenRecord;
  /** Usado apenas como gatilho de recarga quando as versões mudam. */
  revisions: KaizenRevision[];
};

/**
 * Painel analítico (somente leitura) de ganhos: economia ativa hoje e ganho por período.
 * A gestão de versões (criar/editar/implantar) fica no seletor de versões do topo.
 */
export function KaizenImprovementsPanel({ record, revisions }: Props) {
  const [timeline, setTimeline] = useState<KaizenSavingsTimeline | null>(null);
  const [dateStart, setDateStart] = useState(`${CURRENT_YEAR}-01-01`);
  const [dateEnd, setDateEnd] = useState(`${CURRENT_YEAR}-12-31`);

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

  return (
    <div className="kz-improvements">
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
    </div>
  );
}
