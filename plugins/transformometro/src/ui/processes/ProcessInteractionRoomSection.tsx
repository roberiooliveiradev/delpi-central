import { useCallback, useEffect, useState } from "react";
import { CalendarCheck, MessagesSquare } from "lucide-react";
import { EmptyState, emptyStateCardBemClasses } from "@delpi/plugin-ui/index";

import { SoftActionButton } from "../../components/SoftActionButton";
import { InlineErrorState } from "../../components/ErrorStateBox";
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
        <SoftActionButton
          icon={MessagesSquare}
          disabled={opening}
          aria-busy={opening || undefined}
          onClick={() => void openRoom()}
        >
          {opening ? "Abrindo sala…" : "Abrir Sala de interação"}
        </SoftActionButton>
        <SoftActionButton
          icon={CalendarCheck}
          onClick={() => onNavigate(buildProcessoSectionHref(processoId, "tarefas"))}
        >
          Ver tarefas relacionadas
        </SoftActionButton>
      </div>
    </section>
  );
}
