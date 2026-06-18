import { useId } from "react";
import { X } from "lucide-react";

import { ChatModal } from "./ChatModal";
import "./ChatMemoryUsedDialog.css";

export type MemoryUsageView = {
  layers?: string[];
  topic?: string | null;
  task?: string | null;
  operationalFocus?: Record<string, string>;
  preferences?: string[];
  resolvedReferences?: string[];
  semanticHits?: Array<{ title?: string; snippet?: string }>;
  episodicCount?: number;
  episodicRecall?: string | null;
  writeGated?: boolean;
  userContextItems?: string[];
};

type ChatMemoryUsedDialogProps = {
  open: boolean;
  usage: MemoryUsageView | null;
  onClose: () => void;
};

export function ChatMemoryUsedDialog({ open, usage, onClose }: ChatMemoryUsedDialogProps) {
  const titleId = useId();

  if (!usage) {
    return null;
  }

  const hasRichContent =
    Boolean(usage.topic || usage.task) ||
    (usage.preferences?.length ?? 0) > 0 ||
    (usage.resolvedReferences?.length ?? 0) > 0 ||
    (usage.semanticHits?.length ?? 0) > 0 ||
    (usage.userContextItems?.length ?? 0) > 0 ||
    (usage.episodicCount ?? 0) > 0 ||
    Boolean(usage.episodicRecall) ||
    Boolean(usage.writeGated);

  return (
    <ChatModal
      open={open}
      onClose={onClose}
      size="md"
      ariaLabelledBy={titleId}
      panelClassName="mdc-chat-memory-used"
    >
      <header className="mdc-chat-memory-used__header">
        <h2 id={titleId} className="mdc-chat-memory-used__title">
          Memória usada nesta conversa
        </h2>
        <button
          type="button"
          className="mdc-chat-modal-icon-btn mdc-chat-modal-icon-btn--outlined mdc-chat-modal-icon-btn--sm"
          onClick={onClose}
          aria-label="Fechar"
        >
          <X aria-hidden="true" />
        </button>
      </header>

      <div className="mdc-chat-memory-used__body">
        {usage.topic ? (
          <p>
            <strong>Assunto:</strong> {usage.topic}
          </p>
        ) : null}
        {usage.task ? (
          <p>
            <strong>Tarefa:</strong> {usage.task}
          </p>
        ) : null}

        {(usage.preferences?.length ?? 0) > 0 ? (
          <section>
            <h3>Preferências</h3>
            <ul>
              {usage.preferences?.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {(usage.resolvedReferences?.length ?? 0) > 0 ? (
          <section>
            <h3>Referências</h3>
            <ul>
              {usage.resolvedReferences?.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {(usage.semanticHits?.length ?? 0) > 0 ? (
          <section>
            <h3>Documentação / playbooks</h3>
            <ul>
              {usage.semanticHits?.map((hit) => (
                <li key={hit.title}>
                  <strong>{hit.title}</strong>
                  {hit.snippet ? ` — ${hit.snippet}` : null}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {(usage.userContextItems?.length ?? 0) > 0 ? (
          <section>
            <h3>Contexto desta conversa</h3>
            <ul>
              {usage.userContextItems?.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ) : null}

        {(usage.episodicCount ?? 0) > 0 || usage.episodicRecall ? (
          <section>
            <h3>Episódios</h3>
            {usage.episodicRecall ? <p>{usage.episodicRecall}</p> : null}
            {(usage.episodicCount ?? 0) > 0 ? (
              <p>{usage.episodicCount} episódio(s) guardado(s) nesta sessão.</p>
            ) : null}
          </section>
        ) : null}

        {usage.writeGated ? (
          <p className="mdc-chat-memory-used__note">
            Gravação de memória pausada neste turno (conteúdo sensível ou pedido do usuário).
          </p>
        ) : null}

        {!hasRichContent ? (
          <p className="mdc-chat-memory-used__empty">
            Nenhum contexto persistente além da mensagem atual. Use «+» na barra de contexto
            para fixar produto, filial ou texto livre.
          </p>
        ) : null}
      </div>
    </ChatModal>
  );
}
