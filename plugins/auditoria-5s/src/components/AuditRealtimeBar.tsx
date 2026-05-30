import { Users, Wifi, WifiOff, X } from "lucide-react";

import type { AuditPresenceUser } from "../constants/realtime";
import { formatPersonName } from "../utils/formatPersonName";

type Props = {
  connected: boolean;
  presence: AuditPresenceUser[];
  notice: { message: string; tone: "info" | "warning" } | null;
  onDismissNotice: () => void;
};

export function AuditRealtimeBar({
  connected,
  presence,
  notice,
  onDismissNotice,
}: Props) {
  const others =
    presence.length > 0
      ? presence
          .map((user) => formatPersonName(user.display_name))
          .filter(Boolean)
          .join(", ")
      : null;

  return (
    <div className="a5s-realtime">
      <div className={`a5s-realtime__status ${connected ? "a5s-realtime__status--on" : ""}`}>
        {connected ? <Wifi size={14} aria-hidden /> : <WifiOff size={14} aria-hidden />}
        <span>{connected ? "Colaboração ativa" : "Reconectando…"}</span>
      </div>

      {others ? (
        <div className="a5s-realtime__presence">
          <Users size={14} aria-hidden />
          <span>{others}</span>
        </div>
      ) : null}

      {notice ? (
        <div className={`a5s-realtime__notice a5s-realtime__notice--${notice.tone}`}>
          <span>{notice.message}</span>
          <button type="button" className="a5s-realtime__dismiss" onClick={onDismissNotice} aria-label="Fechar aviso">
            <X size={14} />
          </button>
        </div>
      ) : null}
    </div>
  );
}
