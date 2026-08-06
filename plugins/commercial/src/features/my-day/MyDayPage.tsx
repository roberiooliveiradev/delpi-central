import { useCallback, useEffect, useMemo, useState } from "react";
import { ActionButton, EmptyState, HelpTooltip, SectionCard } from "@delpi/plugin-ui/index";

import {
  completeTask,
  createTask,
  getMyWorklist,
  type CommercialTaskDto,
  type WorklistData,
} from "../../api/worklistApi";
import { CM_HELP } from "../../content/helpTooltips";
import { navigateCustomerDetail } from "../../app/pluginNavigation";
import {
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialLoadingCard,
  CommercialTextField,
  CommercialWorklistItem,
} from "../../app/commercialUi";
import { usePortfolioScope } from "../../app/usePortfolioScope";

type MyDayPageProps = {
  basePath: string;
};

type BucketKey = "overdue" | "today" | "later";

function formatDue(dueAt?: string | null): string {
  if (!dueAt) return "Sem prazo";
  try {
    return new Date(dueAt).toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dueAt;
  }
}

function toneForBucket(bucket: BucketKey): "danger" | "warning" | "neutral" {
  if (bucket === "overdue") return "danger";
  if (bucket === "today") return "warning";
  return "neutral";
}

export function MyDayPage({ basePath }: MyDayPageProps) {
  const { canManageFollowups } = usePortfolioScope();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<WorklistData | null>(null);
  const [bucket, setBucket] = useState<BucketKey>("overdue");
  const [title, setTitle] = useState("");
  const [creating, setCreating] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const reload = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const wl = await getMyWorklist(signal);
      setData(wl);
      if (wl.counts.overdue > 0) setBucket("overdue");
      else if (wl.counts.today > 0) setBucket("today");
      else setBucket("later");
    } catch (err: unknown) {
      if (signal?.aborted) return;
      setError(err instanceof Error ? err.message : "Erro ao carregar Meu dia.");
      setData(null);
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void reload(controller.signal);
    return () => controller.abort();
  }, [reload]);

  const items = useMemo(() => {
    if (!data) return [] as CommercialTaskDto[];
    return data[bucket] ?? [];
  }, [bucket, data]);

  const onComplete = async (taskId: string) => {
    if (!canManageFollowups) return;
    setActionError(null);
    try {
      await completeTask(taskId);
      await reload();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Falha ao concluir.");
    }
  };

  const onCreate = async () => {
    if (!canManageFollowups) return;
    const trimmed = title.trim();
    if (!trimmed) return;
    setCreating(true);
    setActionError(null);
    try {
      await createTask({ title: trimmed, task_type: "follow_up", priority: "normal" });
      setTitle("");
      await reload();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Falha ao criar tarefa.");
    } finally {
      setCreating(false);
    }
  };

  return (
    <section className="cm-page-stack">
      <SectionCard
        title="Meu dia"
        subtitle="Fila priorizada: atrasadas → hoje → depois."
        hint={CM_HELP.myDay.worklist}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <div className="cm-nav-row" role="tablist" aria-label="Filas do Meu dia">
          {(
            [
              ["overdue", "Atrasadas", data?.counts.overdue ?? 0, CM_HELP.myDay.bucketOverdue],
              ["today", "Hoje", data?.counts.today ?? 0, CM_HELP.myDay.bucketToday],
              ["later", "Depois", data?.counts.later ?? 0, CM_HELP.myDay.bucketLater],
            ] as const
          ).map(([id, label, count, help]) => (
            <span key={id} style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
              <ActionButton
                variant={bucket === id ? "primary" : "ghost"}
                aria-selected={bucket === id}
                onClick={() => setBucket(id)}
              >
                {label} ({count})
              </ActionButton>
              <HelpTooltip content={help} ariaLabel={`Ajuda: ${label}`} />
            </span>
          ))}
          <ActionButton variant="ghost" onClick={() => void reload()}>
            Atualizar
          </ActionButton>
        </div>

        {loading ? <CommercialLoadingCard title="Carregando worklist…" variant="panel" /> : null}
        {error ? (
          <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
        ) : null}
        {actionError ? (
          <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={actionError} role="alert" />
        ) : null}

        {!loading && !error && items.length === 0 ? (
          <EmptyState
            classNames={{ ...cmEmptyStateClassNames, withTitle: true }}
            defaultTitle="Nenhuma tarefa nesta fila"
            defaultMessage="Crie um follow-up ou escolha outra fila."
          >
            {canManageFollowups ? (
              <p className="cm-muted">Use o formulário abaixo para a primeira tarefa.</p>
            ) : null}
          </EmptyState>
        ) : null}

        <div className="cm-page-stack" style={{ gap: 8 }}>
          {items.map((task) => (
            <CommercialWorklistItem
              key={task.id}
              title={task.title}
              meta={`${formatDue(task.due_at)} · ${task.priority}${
                task.customer_code
                  ? ` · ${task.customer_code}-${task.customer_store ?? ""}`
                  : ""
              }`}
              tone={toneForBucket(bucket)}
              primaryActionLabel={canManageFollowups ? "Concluir" : undefined}
              onPrimaryAction={
                canManageFollowups ? () => void onComplete(task.id) : undefined
              }
              secondaryActionLabel={
                task.customer_code && task.customer_store ? "Abrir conta" : undefined
              }
              onSecondaryAction={
                task.customer_code && task.customer_store
                  ? () =>
                      navigateCustomerDetail(task.customer_code!, task.customer_store!, {
                        basePath,
                      })
                  : undefined
              }
            />
          ))}
        </div>
      </SectionCard>

      {canManageFollowups ? (
        <SectionCard
          title="Nova tarefa"
          subtitle="Follow-up atribuído a você."
          hint={CM_HELP.myDay.newTask}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <div className="cm-nav-row" style={{ alignItems: "flex-end" }}>
            <div style={{ flex: "1 1 240px", minWidth: 0 }}>
              <CommercialTextField
                label="Título"
                hint={CM_HELP.myDay.taskTitle}
                value={title}
                onChange={setTitle}
                placeholder="Ex.: Ligar para ACME sobre atraso"
              />
            </div>
            <ActionButton variant="primary" disabled={creating || !title.trim()} onClick={() => void onCreate()}>
              {creating ? "Criando…" : "Criar tarefa"}
            </ActionButton>
          </div>
        </SectionCard>
      ) : null}
    </section>
  );
}
