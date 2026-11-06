import { copy } from "../content/copy";
import type { LineFeederProgressLog } from "../hooks/useLineFeederMaterialsPreview";

type Props = {
  percent: number;
  logs: LineFeederProgressLog[];
};

export function LineFeederPreviewProgress({ percent, logs }: Props) {
  const texts = copy.lineFeeder.previewProgress;
  const clamped = Math.max(0, Math.min(100, Math.round(percent)));
  const recent = logs.slice(-8);
  const currentMessage =
    recent[recent.length - 1]?.message || texts.waitingMessage;

  return (
    <section
      className="ppc-feeder-progress"
      aria-busy="true"
      aria-live="polite"
      aria-label={texts.regionAria}
    >
      <header className="ppc-feeder-progress__head">
        <h2 className="ppc-feeder-progress__title">{texts.title}</h2>
        <p className="ppc-feeder-progress__hint">{texts.hint}</p>
      </header>

      <div className="ppc-feeder-progress__meter">
        <div
          className="ppc-feeder-progress__track"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={clamped}
          aria-valuetext={texts.percentAria(clamped)}
          aria-label={texts.barAria}
        >
          <div
            className="ppc-feeder-progress__fill"
            style={{ width: `${clamped}%` }}
          />
        </div>
        <span className="ppc-feeder-progress__percent" aria-hidden="true">
          {texts.percentLabel(clamped)}
        </span>
      </div>

      <p className="ppc-feeder-progress__current">{currentMessage}</p>

      {recent.length > 0 ? (
        <ol className="ppc-feeder-progress__logs" aria-label={texts.logsAria}>
          {recent.map((entry) => (
            <li key={entry.id} className="ppc-feeder-progress__log">
              <span className="ppc-feeder-progress__log-msg">{entry.message}</span>
            </li>
          ))}
        </ol>
      ) : null}
    </section>
  );
}
