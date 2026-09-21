import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState, ActionButton, emptyStateCardBemClasses } from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { DataTableSection, type DataTableColumn } from "../../components/DataTableSection";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { PORTAL_PAGE_COPY } from "../../constants/portalExperience";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import { pendingAtas } from "../../data/api/transformometroMeetingMinutesApi";
import { ataStatusLabel } from "../meeting-minutes/meetingMinuteStatusUi";
import { projectPendingSignatureTasks, type MyTaskProjection } from "./myTaskProjection";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
};

const EMPTY = emptyStateCardBemClasses("ds");

export function MyTasksPage({ getAccessToken, pathname, onNavigate }: Props) {
  const [tasks, setTasks] = useState<MyTaskProjection[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reloadNonce, setReloadNonce] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await pendingAtas(getAccessToken);
      setTasks(projectPendingSignatureTasks(response.items ?? []));
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível carregar suas tarefas.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken]);

  useEffect(() => {
    void load();
  }, [load, reloadNonce]);

  const refreshing = Boolean(tasks) && loading;
  const columns = useMemo<DataTableColumn<MyTaskProjection>[]>(
    () => [
      { key: "title", header: "Tarefa", render: (row) => row.title },
      { key: "source", header: "Origem", render: () => "Ata" },
      { key: "status", header: "Status", render: (row) => ataStatusLabel(row.status) },
      {
        key: "context",
        header: "Contexto",
        render: (row) => row.contextLabel ?? "—",
      },
      {
        key: "action",
        header: "Ação",
        interactive: true,
        render: (row) => (
          <ActionButton variant="link" onClick={() => onNavigate(row.route)}>
            Abrir
          </ActionButton>
        ),
      },
    ],
    [onNavigate],
  );

  if (loading && !tasks) {
    return (
      <TransformometroShell>
        <PageHeader
          eyebrow={PORTAL_PAGE_COPY.myTasks.eyebrow}
          title={PORTAL_PAGE_COPY.myTasks.title}
          subtitle={PORTAL_PAGE_COPY.myTasks.description}
          currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.myTasks}
          onNavigate={onNavigate}
        />
        <LoadingActivityCard
          title="Carregando suas tarefas"
          description="Buscando assinaturas de ata que ainda exigem a sua ação."
        />
      </TransformometroShell>
    );
  }

  const rows = tasks ?? [];

  return (
    <TransformometroShell>
      <PageHeader
        eyebrow={PORTAL_PAGE_COPY.myTasks.eyebrow}
        title={PORTAL_PAGE_COPY.myTasks.title}
        subtitle={PORTAL_PAGE_COPY.myTasks.description}
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.myTasks}
        onNavigate={onNavigate}
        onRefresh={() => setReloadNonce((nonce) => nonce + 1)}
        refreshing={refreshing}
        highlights={[
          {
            id: "pending",
            label: "Pendentes",
            value: String(rows.length),
            loading: refreshing,
          },
        ]}
      />
      {error ? (
        <p role="alert">
          {error}{" "}
          <button type="button" onClick={() => setReloadNonce((nonce) => nonce + 1)}>
            Tentar de novo
          </button>
        </p>
      ) : null}
      {rows.length === 0 && !error ? (
        <EmptyState
          classNames={EMPTY}
          title="Nenhuma tarefa pendente"
          defaultMessage="Nenhuma tarefa pendente no momento."
        />
      ) : (
        <section aria-busy={refreshing || undefined}>
          <DataTableSection
            columnPreferencesKey="transformometro:MyTasksPage:pending-signatures:v1"
            title="Pendências"
            hint="Assinaturas de ata atribuídas a você. Abrir leva ao registro."
            columns={columns}
            rows={rows}
            rowKey={(row) => row.id}
            loading={false}
            refreshing={refreshing}
            emptyMessage="Nenhuma tarefa pendente no momento."
          />
        </section>
      )}
    </TransformometroShell>
  );
}
