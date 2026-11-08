import { EngineeringInitialsAvatar } from "../../../ui/engineeringUi";
import { prcPersonLabel } from "../prcCopy";

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Célula de identidade — avatar por iniciais + nome resolvido,
 * fallback honesto (nunca UUID cru como nome). Usada na fila,
 * cards, kanban e detalhe. */
export function PrcPersonCell({
  subject,
  displayName,
  emptyLabel,
}: {
  subject: string | null | undefined;
  displayName?: string | null;
  emptyLabel?: string;
}) {
  const name = (displayName || "").trim();
  const label = name || prcPersonLabel(subject, displayName);
  const resolved = Boolean(name);
  const isUuid = subject ? UUID_RE.test(subject.trim()) : false;
  const initialsSource = resolved ? name : "";
  return (
    <span className="engineering-prc__person">
      <EngineeringInitialsAvatar
        name={initialsSource || "—"}
        size="sm"
      />
      <span
        className={
          resolved || !isUuid ? "" : "engineering-prc__muted"
        }
      >
        {emptyLabel && !subject ? emptyLabel : label}
      </span>
    </span>
  );
}
