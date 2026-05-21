import {
  appendStrategicIndicatorsFiltersToPath,
  type StrategicIndicatorsFilterState,
} from "../shared/strategicIndicatorsFilterUrl";
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
  return (
    <a
      href={appendStrategicIndicatorsFiltersToPath(href, filterState)}
      className="si-back-link"
    >
      <span className="si-back-link__icon" aria-hidden>
        ←
      </span>
      {label}
    </a>
  );
}
