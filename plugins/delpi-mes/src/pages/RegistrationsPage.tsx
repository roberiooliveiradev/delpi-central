import { ArrowRight } from "lucide-react";

import { DELPI_MES_COPY } from "../content/copy";
import { buildRegistrationHref } from "../hooks/useDelpiMesRoute";

export function RegistrationsPage({ onOpenDowntimeReasons }: { onOpenDowntimeReasons: () => void }) {
  const copy = DELPI_MES_COPY.registrations;
  return (
    <section className="delpi-mes-page" aria-labelledby="delpi-mes-page-title">
      <div className="delpi-mes-page__heading">
        <p className="delpi-mes-eyebrow">{copy.globalScope}</p>
        <h2 id="delpi-mes-page-title">{copy.title}</h2>
        <p>{copy.description}</p>
      </div>
      <p className="delpi-mes-global-scope" role="note">
        <strong>{copy.globalScope}</strong>
        <span>{copy.globalScopeHint}</span>
      </p>
      <ul className="delpi-mes-registration-grid">
        <li>
          <a
            className="delpi-mes-registration-card"
            href={buildRegistrationHref("downtime-reasons")}
            onClick={(event) => {
              event.preventDefault();
              onOpenDowntimeReasons();
            }}
          >
            <strong>{copy.downtimeReasons.title}</strong>
            <span>{copy.downtimeReasons.description}</span>
            <span className="delpi-mes-registration-card__action">
              {copy.downtimeReasons.action}
              <ArrowRight aria-hidden="true" />
            </span>
          </a>
        </li>
      </ul>
    </section>
  );
}
