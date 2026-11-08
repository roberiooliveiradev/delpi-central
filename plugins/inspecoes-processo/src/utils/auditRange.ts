/** Filter contract: inclusive production dates, up to 31 calendar days. */
export const MAX_AUDIT_RANGE_DAYS = 31;

function parseDate(value: string): number | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const millis = Date.UTC(year, month - 1, day);
  const parsed = new Date(millis);
  if (parsed.getUTCFullYear() !== year || parsed.getUTCMonth() + 1 !== month ||
      parsed.getUTCDate() !== day) return null;
  return millis;
}

export function validateAuditRange(startDate: string, endDate: string): string | null {
  const start = parseDate(startDate);
  const end = parseDate(endDate);
  if (start === null || end === null) return "Informe datas válidas.";
  if (start > end) return "A data inicial não pode superar a data final.";
  const duration = Math.round((end - start) / 86_400_000) + 1;
  if (duration > MAX_AUDIT_RANGE_DAYS) {
    return "Selecione no máximo 31 dias de produção.";
  }
  return null;
}
