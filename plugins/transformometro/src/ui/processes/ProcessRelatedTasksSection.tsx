import { useCallback, useEffect, useState } from "react";
import { EmptyState, emptyStateCardBemClasses } from "@delpi/plugin-ui/index";

import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { InlineErrorState } from "../../components/ErrorStateBox";
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import {
  listProcessoRelatedTasks,
  type TransformometroTask,
} from "../../data/api/transformometroTasksApi";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";

type Props = {
  processoId: string;
  getAccessToken?: () => string | undefined;
  onNavigate: (path: string) => void;
  active: boolean;
};

const EMPTY = emptyStateCardBemClasses("ds");

function statusLabel(status: TransformometroTask["status"]): string {
  if (status === "completed") return "Concluída";
  if (status === "cancelled") return "Cancelada";
  return "Pendente";
}

export function ProcessRelatedTasksSection({
  processoId,
  getAccessToken,
  onNavigate,
  active,
}: Props) {
  const [items, setItems] = useState<TransformometroTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadedOnce, setLoadedOnce] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listProcessoRelatedTasks(processoId, getAccessToken);
      setItems(data.items);
      setLoadedOnce(true);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Não foi possível carregar as tarefas relacionadas."
      );
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, processoId]);

  useEffect(() => {
    if (!active) return;
    if (loadedOnce && !error) return;
    void load();
  }, [active, error, load, loadedOnce]);

  return (
    <section className="ds-card tm-processo-workspace-panel" aria-labelledby="tm-process-tarefas-title">
      <h2 id="tm-process-tarefas-title" className="ds-section-title">
        Tarefas relacionadas
      </h2>
      <p className="ds-hint">
        Tarefas criadas a partir de mensagens da Sala de interação deste processo. Tarefas manuais sem
        vínculo com a sala não aparecem aqui — use Minhas tarefas para a fila pessoal.
      </p>

      {loading && items.length === 0 ? (
        <LoadingActivityCard
          title="Carregando tarefas"
          description="Buscando tarefas vinculadas à sala deste processo."
        />
      ) : null}

      {error ? (
        <InlineErrorState
          title="Falha ao carregar tarefas relacionadas"
          message={error}
          onAction={() => void load()}
        />
      ) : null}

      {!loading && !error && items.length === 0 ? (
        <EmptyState
          classNames={EMPTY}
          title="Sem tarefas relacionadas"
          defaultMessage="Ainda não há tarefas originadas de mensagens da sala deste processo."
        />
      ) : null}

      {items.length > 0 ? (
        <ul className="tm-processo-related-tasks">
          {items.map((task) => (
            <li key={task.id} className="tm-processo-related-tasks__item">
              <div>
                <strong>{task.title}</strong>
                <p className="ds-hint">
                  {statusLabel(task.status)}
                  {task.due_date ? ` · prazo ${task.due_date}` : ""}
                </p>
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      <div className="tm-processo-workspace-overview__actions">
        <button
          type="button"
          className={DS_GHOST_BTN}
          disabled={loading}
          onClick={() => void load()}
        >
          {loading ? "Atualizando…" : "Atualizar"}
        </button>
        <button
          type="button"
          className={DS_GHOST_BTN}
          onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.myTasks)}
        >
          Abrir Minhas tarefas
        </button>
      </div>
    </section>
  );
}
