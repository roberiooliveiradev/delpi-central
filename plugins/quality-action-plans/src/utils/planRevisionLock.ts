export function withExpectedPlanRevision<T extends Record<string, unknown>>(
  payload: T,
  revisionNumber?: number | null,
): T & { expected_revision_number?: number } {
  if (revisionNumber == null || revisionNumber <= 0) {
    return payload;
  }
  return { ...payload, expected_revision_number: revisionNumber };
}

export function expectedPlanRevisionQuery(revisionNumber?: number | null): string {
  if (revisionNumber == null || revisionNumber <= 0) {
    return "";
  }
  return `?expected_revision_number=${encodeURIComponent(String(revisionNumber))}`;
}
