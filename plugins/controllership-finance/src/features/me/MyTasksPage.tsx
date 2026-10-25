/**
 * Minhas tarefas — projeção self-only `/me/tasks` (F5).
 *
 * Somente trabalho pendente atribuído ao próprio usuário: responsável
 * de pendência P4, revisor de área obrigatória P5 e remetente de
 * pacote com esclarecimento aberto. Não é uma TaskEntity genérica —
 * cada item aponta para a página dona do recurso. Não há SLA
 * inventado: `pendingSince` é dado factual.
 */
import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiError } from "../../api/httpClient";
import {
  listMyTasks,
  type MyTask,
  type MyTasksProjection,
} from "../../api/meApi";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  CfEmptyState,
  CfMetricStrip,
  CfStatusBadge,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  DataTableSection,
  type DataTableColumn,
} from "../../app/cfDataTableUi";
import {
  FilterInputField,
  FiltersRow,
} from "../../app/cfFiltersUi";
import { ClosingHero } from "../../app/ClosingHero";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";

type PanelError = { status: number; code: string | null; message: string };

const PERIOD_PATTERN = /^\d{4}-(0[1-9]|1[0-2])$/;

const ERROR_MESSAGES: Record<string, string> = {
  unauthorized: "Sessão expirada — autentique-se novamente.",
  forbidden: "Você não tem acesso a esta área.",
};

const ACTION_LABELS: Record<string, string> = {
  PENDENCY_ACTION_REQUIRED: "Pendência sob sua responsabilidade",
  PACKAGE_REVIEW_REQUIRED: "Revisão de pacote pendente",
  PACKAGE_CLARIFICATION_REQUIRED: "Esclarecimento aguardando resposta",
};

const ACTION_VARIANTS: Record<
  string,
  "warning" | "info" | "success" | "neutral" | "danger"
> = {
  PENDENCY_ACTION_REQUIRED: "warning",
  PACKAGE_REVIEW_REQUIRED: "info",
  PACKAGE_CLARIFICATION_REQUIRED: "warning",
};

function mapError(error: unknown): PanelError {
  if (error instanceof ApiError) {
    return {
      status: error.status,
      code: error.code ?? null,
      message: ERROR_MESSAGES[error.code ?? ""] ?? error.message,
    };
  }
  return {
    status: 0,
    code: null,
    message: "Falha de comunicação com a API.",
  };
}

export function MyTasksPage() {
  const [period, setPeriod] = useState("");
  const [projection, setProjection] =
    useState<MyTasksProjection | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<PanelError | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  const periodValid = period === "" || PERIOD_PATTERN.test(period);

  const reload = useCallback(async () => {
    if (!periodValid) return;
    setLoading(true);
    setError(null);
    try {
      const result = await listMyTasks({
        period: period.trim() || undefined,
      });
      setProjection(result);
      setUpdatedAt(new Date());
    } catch (err) {
      setError(mapError(err));
    } finally {
      setLoading(false);
    }
  }, [period, periodValid]);

  useEffect(() => {
    void reload();
    // Carrega uma vez; novas consultas via «Atualizar»/limpar filtros.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const tasks = useMemo(
    () => projection?.items ?? [],
    [projection],
  );
  const counts = useMemo(() => {
    const byAction = new Map<string, number>();
    for (const task of tasks) {
      byAction.set(
        task.actionKind,
        (byAction.get(task.actionKind) ?? 0) + 1,
      );
    }
    return byAction;
  }, [tasks]);

  const columns = useMemo<DataTableColumn<MyTask>[]>(
    () => [
      {
        key: "action",
        header: "Tipo",
        render: (task) => (
          <CfStatusBadge
            label={ACTION_LABELS[task.actionKind] ?? task.actionKind}
            variant={ACTION_VARIANTS[task.actionKind] ?? "neutral"}
          />
        ),
      },
      {
        key: "title",
        header: "Tarefa",
        render: (task) => (
          <>
            <div>{task.title}</div>
            <div className="cf-cell-secondary">
              {task.context.contextLabel}
            </div>
          </>
        ),
      },
      {
        key: "status",
        header: "Estado",
        render: (task) => (
          <CfStatusBadge label={task.statusLabel} variant="neutral" />
        ),
      },
      {
        key: "since",
        header: "Pendente desde",
        render: (task) =>
          task.pendingSince ? formatDateTime(task.pendingSince) : "—",
      },
      {
        key: "link",
        header: "Ação",
        render: (task) => (
          <a
            className="cf-link"
            href={task.deepLink}
            aria-label={`Abrir: ${task.title}`}
          >
            Abrir
          </a>
        ),
      },
    ],
    [],
  );

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Minhas tarefas"
    >
      <ClosingHero
        title="Minhas tarefas"
        subtitle="Trabalho pendente atribuído a você — pendências, revisões de pacote e esclarecimentos."
        filters={
          <form
            className="cf-settlements-filters"
            onSubmit={(event) => event.preventDefault()}
          >
            <FiltersRow>
              <FilterInputField
                id="cf-tasks-period"
                label="Competência"
                type="month"
                value={period}
                onChange={setPeriod}
              />
            </FiltersRow>
          </form>
        }
        updatedAt={updatedAt}
        onRefresh={() => void reload()}
        refreshing={loading}
        onClearFilters={() => {
          setPeriod("");
        }}
        notice={
          !periodValid ? (
            <CfFeedbackMessage
              intent="warning"
              title="Competência inválida"
            >
              Use o formato AAAA-MM.
            </CfFeedbackMessage>
          ) : undefined
        }
      />

      <div className="cf-page-stack" aria-busy={loading}>
        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="suas tarefas"
            onRetry={() => void reload()}
          />
        ) : null}

        {projection && tasks.length > 0 ? (
          <CfMetricStrip
            aria-label="Resumo das suas tarefas"
            items={[
              {
                id: "total",
                label: "Tarefas pendentes",
                value: String(projection.total),
              },
              {
                id: "reviews",
                label: "Revisões de pacote",
                value: String(
                  counts.get("PACKAGE_REVIEW_REQUIRED") ?? 0,
                ),
              },
              {
                id: "pendencies",
                label: "Pendências",
                value: String(
                  counts.get("PENDENCY_ACTION_REQUIRED") ?? 0,
                ),
              },
              {
                id: "clarifications",
                label: "Esclarecimentos",
                value: String(
                  counts.get("PACKAGE_CLARIFICATION_REQUIRED") ?? 0,
                ),
              },
            ]}
          />
        ) : null}

        {projection && tasks.length === 0 && !loading && !error ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage={
              period
                ? "Nenhuma pendência, revisão ou esclarecimento atribuído a você nesta competência."
                : "Nenhuma pendência, revisão ou esclarecimento atribuído a você."
            }
          />
        ) : null}

        <DataTableSection<MyTask>
          title="Trabalho atribuído a você"
          titleHint={CF_HELP.myTasks.queue}
          columns={columns}
          rows={tasks}
          rowKey={(task) => task.id}
          loading={loading}
          hideSearch
          emptyMessage="Nenhuma tarefa encontrada."
          columnPreferencesKey="cf:my-tasks:v1"
        />
      </div>
    </section>
  );
}
