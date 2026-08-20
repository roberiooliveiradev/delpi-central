import { useEffect, useState } from "react";

import { copy } from "../content/copy";
import type { MachineLoadLocateJourney, MachineLoadLocatePayload, MachineLoadLocateStop } from "../types";
import { formatIsoDate } from "../utils/formatIsoDate";
import {
  locateJourneyProgress,
  locateJourneyTitle,
  locateStopStatusLabel,
  locateStopStatusTone,
  machineLoadLocateRowKey,
} from "../utils/machineLoadLocate";

type Props = {
  loading?: boolean;
  error?: string | null;
  result: MachineLoadLocatePayload | null;
  onGoToStop: (stop: MachineLoadLocateStop) => void;
};

/** Resultados de jornada compartilhados pelo painel de busca e pelo modal do menu de contexto. */
export function MachineLoadLocateResults({ loading, error, result, onGoToStop }: Props) {
  return (
    <div className="ppc-locate__results" aria-live="polite">
      {loading ? <p className="ppc-locate__state">{copy.machineLoad.locate.searching}</p> : null}
      {error ? (
        <p className="ppc-locate__state ppc-locate__state--error" role="alert">
          {error}
        </p>
      ) : null}
      {result?.message && !loading ? <p className="ppc-locate__state">{result.message}</p> : null}
      {result?.journeys.map((journey) => (
        <JourneyCard key={`${journey.kind}:${journey.key}`} journey={journey} onGoToStop={onGoToStop} />
      ))}
    </div>
  );
}

function JourneyCard({
  journey,
  onGoToStop,
}: {
  journey: MachineLoadLocateJourney;
  onGoToStop: (stop: MachineLoadLocateStop) => void;
}) {
  const progress = locateJourneyProgress(journey.stops);
  return (
    <article className="ppc-locate__journey">
      <header className="ppc-locate__journey-head">
        <div>
          <h3>{locateJourneyTitle(journey)}</h3>
          <p className="ppc-locate__journey-meta">
            <span>{copy.machineLoad.locate.stops(journey.stop_count)}</span>
            {journey.pa_due_date ? (
              <span>{copy.machineLoad.locate.due(formatIsoDate(journey.pa_due_date))}</span>
            ) : null}
            {journey.kind === "op" && journey.pa_product_code ? (
              <span>{copy.machineLoad.locate.journeyProduct(journey.pa_product_code)}</span>
            ) : null}
          </p>
        </div>
      </header>

      {progress.length > 0 ? (
        <ol className="ppc-locate__progress" aria-label={copy.machineLoad.locate.progressLabel}>
          {progress.map((step, index) => (
            <li
              key={`${journey.key}-${index}`}
              className={`ppc-locate__progress-step ppc-locate__progress-step--${step.tone}`}
            >
              <span className="ppc-locate__progress-dot" aria-hidden="true" />
              <span className="ppc-locate__progress-label">{step.label}</span>
            </li>
          ))}
        </ol>
      ) : null}

      <ol className="ppc-locate__stops">
        {journey.stops.map((stop, index) => (
          <StopCard
            key={machineLoadLocateRowKey(stop)}
            index={index + 1}
            stop={stop}
            onGoToStop={onGoToStop}
          />
        ))}
      </ol>
    </article>
  );
}

function StopCard({
  index,
  stop,
  onGoToStop,
}: {
  index: number;
  stop: MachineLoadLocateStop;
  onGoToStop: (stop: MachineLoadLocateStop) => void;
}) {
  const tone = locateStopStatusTone(stop.production_status, stop.is_in_production);
  const [flash, setFlash] = useState(false);

  useEffect(() => {
    if (!flash) return;
    const timer = window.setTimeout(() => setFlash(false), 400);
    return () => window.clearTimeout(timer);
  }, [flash]);

  return (
    <li className={`ppc-locate__stop ppc-locate__stop--${tone}${flash ? " ppc-locate__stop--flash" : ""}`}>
      <span className="ppc-locate__stop-index" aria-hidden="true">
        {index}
      </span>
      <div className="ppc-locate__stop-body">
        <div className="ppc-locate__stop-title">
          <strong className="ppc-locate__stop-ct">{stop.work_center}</strong>
          <span>{stop.work_center_name}</span>
        </div>
        <p className="ppc-locate__stop-line">
          OP {stop.production_order} · {stop.operation_code} {stop.operation_description}
        </p>
        <p className="ppc-locate__stop-meta">
          <span>
            {copy.machineLoad.locate.schedule} {formatIsoDate(stop.scheduled_date)}
            {stop.scheduled_start_time ? ` ${stop.scheduled_start_time}` : ""}
          </span>
          {stop.queue_position > 0 && stop.queue_size > 0 ? (
            <span>{copy.machineLoad.locate.position(stop.queue_position, stop.queue_size)}</span>
          ) : null}
          <span className={`ppc-locate__badge ppc-locate__badge--${tone}`}>
            {locateStopStatusLabel(stop.production_status, stop.is_in_production)}
          </span>
          {stop.is_withdrawn ? (
            <span className="ppc-locate__badge ppc-locate__badge--withdrawn">
              {copy.machineLoad.withdrawn.locateBadge}
            </span>
          ) : null}
          {stop.active_operator_name ? <span>{stop.active_operator_name}</span> : null}
        </p>
      </div>
      {stop.is_withdrawn ? null : (
        <button
          type="button"
          className="ppc-locate__go"
          onClick={() => {
            setFlash(true);
            onGoToStop(stop);
          }}
        >
          {copy.machineLoad.locate.goToQueue}
        </button>
      )}
    </li>
  );
}
