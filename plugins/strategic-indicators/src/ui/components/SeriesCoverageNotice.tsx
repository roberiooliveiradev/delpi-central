import { seriesCoverageCopy } from "../../content/seriesCoverage";
import type { TrendsDashboardViewData } from "../../data/types/trends";
import { InfoState } from "./InfoState";

type SeriesCoverageNoticeProps = {
  trends: Pick<
    TrendsDashboardViewData,
    | "monthsRequested"
    | "competencesReturned"
    | "missingCompetences"
    | "igdSeries"
  >;
  onRefresh?: () => void;
};

export function SeriesCoverageNotice({
  trends,
  onRefresh,
}: SeriesCoverageNoticeProps) {
  const monthsRequested = trends.monthsRequested;
  if (monthsRequested == null || monthsRequested <= 0) {
    return null;
  }

  const monthsReturned =
    trends.competencesReturned.length > 0
      ? trends.competencesReturned.length
      : trends.igdSeries.length;
  const missing = trends.missingCompetences;
  const incomplete =
    missing.length > 0 || monthsReturned < monthsRequested;

  if (!incomplete) {
    return null;
  }

  return (
    <InfoState
      title={seriesCoverageCopy.incompleteTitle}
      description={seriesCoverageCopy.incompleteDescription({
        monthsRequested,
        monthsReturned,
        missingCompetences: missing,
      })}
      actionLabel={onRefresh ? "Atualizar" : undefined}
      onAction={onRefresh}
    />
  );
}
