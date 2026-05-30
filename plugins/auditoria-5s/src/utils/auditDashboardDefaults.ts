import { getTodayInputValue } from "./dates";

type AuditDateSource = {
  audit_date: string;
};

export function computeAuditDateRange(audits: AuditDateSource[]): {
  dateStart: string;
  dateEnd: string;
} {
  if (audits.length === 0) {
    const today = getTodayInputValue();
    return { dateStart: today, dateEnd: today };
  }

  let dateStart = audits[0].audit_date.slice(0, 10);
  let dateEnd = dateStart;

  for (let index = 1; index < audits.length; index += 1) {
    const day = audits[index].audit_date.slice(0, 10);
    if (day < dateStart) dateStart = day;
    if (day > dateEnd) dateEnd = day;
  }

  return { dateStart, dateEnd };
}
