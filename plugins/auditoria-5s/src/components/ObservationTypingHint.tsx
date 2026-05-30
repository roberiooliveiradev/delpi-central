import type { AuditTypingUser } from "../constants/realtime";
import { formatObservationTypingLabel } from "../utils/observationTypingLabel";

type Props = {
  users: AuditTypingUser[];
  selfClientId: string;
};

export function ObservationTypingHint({ users, selfClientId }: Props) {
  const label = formatObservationTypingLabel(users, selfClientId);
  if (!label) return null;

  return (
    <p className="a5s-criterion__typing" role="status" aria-live="polite">
      <span className="a5s-criterion__typing-dot" aria-hidden />
      {label}
    </p>
  );
}
