import { ArrowRight, Clock3 } from "lucide-react";

import { OPEN_GUIDE_LABEL, formatReadingTime } from "../content/catalog";
import type { GuideSummary } from "../types/guide";
import { navigateGuiasProcedimentos } from "../utils/navigation";
import { GUIAS_PROCEDIMENTOS_ROUTES } from "../utils/route";

type GuideCardProps = {
  guide: GuideSummary;
  /** Em resultados de busca global, exibe o departamento. */
  showDepartment?: boolean;
};

export function GuideCard({ guide, showDepartment = false }: GuideCardProps) {
  const href = GUIAS_PROCEDIMENTOS_ROUTES.guide(guide.slug);

  return (
    <a
      className="gp-card"
      href={href}
      onClick={(event) => {
        event.preventDefault();
        navigateGuiasProcedimentos(href);
      }}
    >
      {showDepartment ? (
        <span className="gp-card__category">{guide.departmentName}</span>
      ) : null}
      <h3 className="gp-card__title">{guide.title}</h3>
      <p className="gp-card__summary">{guide.summary}</p>
      <div className="gp-card__footer">
        <span className="gp-card__meta">
          <Clock3 size={15} strokeWidth={2} aria-hidden="true" />
          {formatReadingTime(guide.readingTimeMinutes)}
        </span>
        <span className="gp-card__action">
          {OPEN_GUIDE_LABEL}
          <ArrowRight size={16} strokeWidth={2} aria-hidden="true" />
        </span>
      </div>
    </a>
  );
}
