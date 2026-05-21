import {
  appendStrategicIndicatorsFiltersToPath,
  type StrategicIndicatorsFilterState,
} from "../shared/strategicIndicatorsFilterUrl";
import { navigateStrategicIndicators } from "../shared/strategicIndicatorsNavigation";
import "./StrategicIndicatorsBackLink.css";

type StrategicIndicatorsBackLinkProps = {
  href: string;
  label?: string;
  filterState?: StrategicIndicatorsFilterState;
};

export function StrategicIndicatorsBackLink({
  href,
  label = "Voltar",
  filterState,
}: StrategicIndicatorsBackLinkProps) {
  const target = appendStrategicIndicatorsFiltersToPath(href, filterState);

  return (
    <a
      href={target}
      className="si-back-link"
      onClick={(event) => {
        if (
          event.defaultPrevented ||
          event.button !== 0 ||
          event.metaKey ||
          event.ctrlKey ||
          event.shiftKey ||
          event.altKey
        ) {
          return;
        }

        event.preventDefault();
        navigateStrategicIndicators(href, filterState);
      }}
    >
      <span className="si-back-link__icon" aria-hidden>
        ←
      </span>
      {label}
    </a>
  );
}
