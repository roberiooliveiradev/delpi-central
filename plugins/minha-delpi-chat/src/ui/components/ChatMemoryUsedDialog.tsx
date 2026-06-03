import { useId } from "react";

import { ModalPortal } from "./ModalPortal";
import "./ChatMemoryUsedDialog.css";

export type MemoryUsageView = {
  layers?: string[];
  topic?: string | null;
  task?: string | null;
  entities?: Record<string, string>;
  preferences?: string[];
  resolvedReferences?: string[];
  semanticHits?: Array<{ title?: string; snippet?: string }>;
  episodicCount?: number;
  episodicRecall?: string | null;
  writeGated?: boolean;
};

type ChatMemoryUsedDialogProps = {
  open: boolean;
  usage: MemoryUsageView | null;
  onClose: () => void;
};

export function ChatMemoryUsedDialog({ open, usage, onClose }: ChatMemoryUsedDialogProps) {
  const titleId = useId();

  if (!open || !usage) {
    return null;
  }

  const entities = usage.entities ?? {};
  const entityEntries = Object.entries(entities).filter(([, value]) => value);

  return (
    <ModalPortal>
      <div className="mdc-memory-used-dialog__backdrop" role="presentation" onClick={onClose}>
        <div
          className="mdc-memory-used-dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby={titleId}
          onClick={(event) => event.stopPropagation()}
        >
          <header className="mdc-memory-used-dialog__header">
            <h2 id={titleId} className="mdc-memory-used-dialog__title">
              Memória usada nesta conversa
            </h2>
            <button type="button" className="mdc-memory-used-dialog__close" onClick={onClose}>
              Fechar
            </button>
          </header>

          <div className="mdc-memory-used-dialog__body">
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

            {entityEntries.length > 0 ? (
              <section>
                <h3>Entidades</h3>
                <ul>
                  {entityEntries.map(([key, value]) => (
                    <li key={key}>
                      {key}: {value}
                    </li>
                  ))}
                </ul>
              </section>
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
              <p className="mdc-memory-used-dialog__note">
                Gravação de memória pausada neste turno (conteúdo sensível ou pedido do usuário).
              </p>
            ) : null}

            {!usage.topic &&
            !usage.task &&
            entityEntries.length === 0 &&
            !(usage.preferences?.length ?? 0) ? (
              <p>Nenhum contexto persistente além da mensagem atual.</p>
            ) : null}
          </div>
        </div>
      </div>
    </ModalPortal>
  );
}
