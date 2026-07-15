import { Building2, CalendarClock, Clock3, Printer } from "lucide-react";

import {
  PRINT_GUIDE_LABEL,
  formatReadingTime,
} from "../content/catalog";
import type { GuideMeta } from "../types/guide";
import { printGuide } from "../utils/printGuide";

type GuideMetaBarProps = {
  meta: GuideMeta;
};

export function GuideMetaBar({ meta }: GuideMetaBarProps) {
  return (
    <div className="gp-meta">
      <ul className="gp-meta__list">
        <li>
          <Building2 size={16} strokeWidth={2} aria-hidden="true" />
          <span>
            <span className="gp-meta__label">Setor responsável</span>
            <strong>{meta.responsibleArea}</strong>
          </span>
        </li>
        <li>
          <CalendarClock size={16} strokeWidth={2} aria-hidden="true" />
          <span>
            <span className="gp-meta__label">Última atualização</span>
            <strong>{meta.updatedAtLabel}</strong>
          </span>
        </li>
        <li>
          <Clock3 size={16} strokeWidth={2} aria-hidden="true" />
          <span>
            <span className="gp-meta__label">Leitura</span>
            <strong>{formatReadingTime(meta.readingTimeMinutes)}</strong>
          </span>
        </li>
      </ul>
      <button
        type="button"
        className="gp-btn gp-btn--secondary gp-no-print-hide"
        onClick={printGuide}
      >
        <Printer size={16} strokeWidth={2} aria-hidden="true" />
        {PRINT_GUIDE_LABEL}
      </button>
    </div>
  );
}
