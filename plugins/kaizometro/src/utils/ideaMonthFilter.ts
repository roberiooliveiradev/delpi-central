export type KaizenDateFilterValues = {
  dateFields: string[];
  dateStart: string;
  dateEnd: string;
};

const MONTH_RE = /^([1-9]\d{3})-(0[1-9]|1[0-2])$/;

/** Convert a selected month to the date fields already supported by the Kaizen API. */
export function buildIdeaMonthFilter(month: string): KaizenDateFilterValues {
  const match = MONTH_RE.exec(month);
  if (!match) {
    return { dateFields: [], dateStart: "", dateEnd: "" };
  }

  const lastDay = new Date(Number(match[1]), Number(match[2]), 0).getDate();
  return {
    dateFields: ["recebimento"],
    dateStart: `${month}-01`,
    dateEnd: `${month}-${String(lastDay).padStart(2, "0")}`,
  };
}

/** Keep the month input in sync with edits to the existing date filters. */
export function detectIdeaMonthFilter(filters: KaizenDateFilterValues): string {
  const month = filters.dateStart.slice(0, 7);
  const expected = buildIdeaMonthFilter(month);
  return filters.dateFields.length === 1 &&
    filters.dateFields[0] === "recebimento" &&
    filters.dateStart === expected.dateStart &&
    filters.dateEnd === expected.dateEnd
    ? month
    : "";
}
