import { useCallback, useEffect, useState } from "react";
import { MessagesSquare } from "lucide-react";

import { InlineErrorState } from "../../components/ErrorStateBox";
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { openInteractionRoom } from "../../data/api/transformometroInteractionApi";
import { buildInteractionRoomPath } from "../../constants/routes";
import { buildProcessoSectionHref } from "./processWorkspaceNav";

type Props = {
  processoId: string;
  getAccessToken?: () => string | undefined;
  onNavigate: (path: string) => void;
  active: boolean;
};

export function ProcessInteractionRoomSection({
  processoId,
  getAccessToken,
  onNavigate,
  active,
}: Props) {
  const [opening, setOpening] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const openRoom = useCallback(async () => {
    setOpening(true);
    setError(null);
    try {
      const room = await openInteractionRoom(processoId, getAccessToken);
      onNavigate(buildInteractionRoomPath(room.id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível abrir a sala.");
    } finally {
      setOpening(false);
    }
  }, [getAccessToken, onNavigate, processoId]);

  useEffect(() => {
    if (!active) setError(null);
  }, [active]);

  return (
    <section className="ds-card tm-processo-workspace-panel" aria-labelledby="tm-process-sala-title">
      <h2 id="tm-process-sala-title" className="ds-section-title">
        Sala de interação
      </h2>
      <p className="ds-hint">
        Cada processo tem uma sala de conversa. Abrir a sala não duplica mensagens — você segue
        para o contexto canônico da interação.
      </p>
      {error ? (
        <InlineErrorState
          title="Não foi possível abrir a sala"
          message={error}
          onAction={() => void openRoom()}
        />
      ) : null}
      <div className="tm-processo-workspace-overview__actions">
        <button
          type="button"
          className={DS_GHOST_BTN}
          disabled={opening}
          aria-busy={opening || undefined}
          onClick={() => void openRoom()}
        >
          <MessagesSquare size={16} aria-hidden="true" />
          {opening ? "Abrindo sala…" : "Abrir Sala de interação"}
        </button>
        <button
          type="button"
          className="ds-link"
          onClick={() => onNavigate(buildProcessoSectionHref(processoId, "tarefas"))}
        >
          Ver tarefas relacionadas
        </button>
      </div>
    </section>
  );
}
