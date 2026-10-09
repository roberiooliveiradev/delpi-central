export type ComposerCharacterCounterProps = {
  value: string;
  /**
   * Real contracted limit (e.g. a backend-enforced input bound).
   * Never invent a number — omit the prop to hide the counter.
   */
  limit: number;
  className?: string;
};

/**
 * Compact `n/limit` indicator for the composer write area.
 *
 * Rendered only when a real, contracted limit is supplied — the
 * counter is informational; enforcement stays with the backend.
 */
export function ComposerCharacterCounter({
  value,
  limit,
  className,
}: ComposerCharacterCounterProps) {
  return (
    <span
      className={[
        "delpi-ui-message-composer__counter",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label={`${value.length} de ${limit} caracteres`}
    >
      {value.length}/{limit}
    </span>
  );
}
