import { Info } from "lucide-react";

import type { PreviousCriterionNonconformity } from "../api/audit5sApi";

type Props = {
  nc: PreviousCriterionNonconformity;
  onViewDetails: (nc: PreviousCriterionNonconformity) => void;
};

export function PreviousCriterionNcBanner({ nc, onViewDetails }: Props) {
  return (
    <div
      className="a5s-previous-nc-banner"
      role="status"
      aria-live="polite"
    >
      <Info className="a5s-previous-nc-banner__icon" size={18} aria-hidden />
      <p className="a5s-previous-nc-banner__text">
        Na auditoria anterior, foi identificada uma não conformidade neste critério.
      </p>
      <button
        type="button"
        className="a5s-previous-nc-banner__action"
        onClick={() => onViewDetails(nc)}
      >
        Visualizar detalhes
      </button>
    </div>
  );
}
