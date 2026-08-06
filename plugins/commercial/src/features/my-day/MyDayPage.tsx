import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ActionButton, EmptyState, HelpTooltip, SectionCard } from "@delpi/plugin-ui/index";

import {
  completeTask,
  createTask,
  deferTask,
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
  CommercialSelectField,
  CommercialTextField,
  CommercialWorklistItem,
} from "../../app/commercialUi";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import { deferDueAtOneDay, dueDateInputToIsoEod, localDateInputValue } from "./myDayDueDate";

function readCreateTaskDeepLink(): {
  createTask: boolean;
  customerCode: string;
  customerStore: string;
} {
  if (typeof window === "undefined") {
    return { createTask: false, customerCode: "", customerStore: "" };
  }
  const params = new URLSearchParams(window.location.search);
  return {
    createTask: params.get("createTask") === "1",
    customerCode: (params.get("customer_code") ?? "").trim(),
    customerStore: (params.get("customer_store") ?? "").trim(),
  };
}

function clearCreateTaskQueryFromUrl(): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  if (!url.searchParams.has("createTask") && !url.searchParams.has("customer_code")) return;
  url.searchParams.delete("createTask");
  url.searchParams.delete("customer_code");
  url.searchParams.delete("customer_store");
  window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
}

type MyDayPageProps = {
  basePath: string;
};

type BucketKey = "overdue" | "today" | "later";

const PRIORITY_OPTIONS = [
  { value: "low", label: "Baixa" },
  { value: "normal", label: "Normal" },
  { value: "high", label: "Alta" },
] as const;

const TASK_TYPE_OPTIONS = [
  { value: "follow_up", label: "Follow-up" },
  { value: "call", label: "Ligar" },
  { value: "todo", label: "To-do" },
] as const;

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

function parseCustomerKey(key: string): { code: string; store: string } | null {
  const sep = key.indexOf("|");
  if (sep <= 0) return null;
  const code = key.slice(0, sep).trim();
  const store = key.slice(sep + 1).trim();
  if (!code || !store) return null;
  return { code, store };
}

export function MyDayPage({ basePath }: MyDayPageProps) {
  const { canManageFollowups, myPortfolio } = usePortfolioScope();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<WorklistData | null>(null);
  const [bucket, setBucket] = useState<BucketKey>("overdue");
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState(localDateInputValue);
  const [priority, setPriority] = useState("normal");
  const [taskType, setTaskType] = useState("follow_up");
  const [customerKey, setCustomerKey] = useState("");
  const [creating, setCreating] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [highlightCreateForm, setHighlightCreateForm] = useState(false);
  const createFormRef = useRef<HTMLDivElement | null>(null);

  const customerOptions = useMemo(() => {
    const rows = myPortfolio?.customers ?? [];
    return rows.map((c) => ({
      value: `${c.customer_code}|${c.customer_store}`,
      label: `${c.customer_name?.trim() || "Cliente"} (${c.customer_code}/${c.customer_store})`,
    }));
  }, [myPortfolio]);

  useEffect(() => {
    if (!canManageFollowups) return;
    const link = readCreateTaskDeepLink();
    if (!link.createTask && !link.customerCode) return;
    if (link.customerCode && link.customerStore) {
      setCustomerKey(`${link.customerCode}|${link.customerStore}`);
    }
    setHighlightCreateForm(true);
    clearCreateTaskQueryFromUrl();
    const timer = window.setTimeout(() => {
      createFormRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 120);
    return () => window.clearTimeout(timer);
  }, [canManageFollowups]);

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

  const onDefer = async (task: CommercialTaskDto) => {
    if (!canManageFollowups) return;
    setActionError(null);
    try {
      await deferTask(task.id, deferDueAtOneDay(task.due_at));
      await reload();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Falha ao adiar.");
    }
  };

  const onCreate = async () => {
    if (!canManageFollowups) return;
    const trimmed = title.trim();
    if (!trimmed || !dueDate) return;
    setCreating(true);
    setActionError(null);
    try {
      const customer = parseCustomerKey(customerKey);
      await createTask({
        title: trimmed,
        task_type: taskType || "follow_up",
        priority: priority || "normal",
        due_at: dueDateInputToIsoEod(dueDate),
        customer_code: customer?.code ?? null,
        customer_store: customer?.store ?? null,
      });
      setTitle("");
      setDueDate(localDateInputValue());
      setPriority("normal");
      setTaskType("follow_up");
      setCustomerKey("");
      setHighlightCreateForm(false);
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
        subtitle="Fila do dia: atrasadas → hoje → depois (padrão CRM)."
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
            defaultMessage="Crie um follow-up com prazo ou escolha outra fila."
          >
            {canManageFollowups ? (
              <p className="cm-muted">Use o formulário abaixo — prazo padrão é hoje.</p>
            ) : null}
          </EmptyState>
        ) : null}

        <div className="cm-page-stack" style={{ gap: 8 }}>
          {items.map((task) => (
            <CommercialWorklistItem
              key={task.id}
              title={task.title}
              meta={`${formatDue(task.due_at)} · ${task.priority}${
                task.task_type ? ` · ${task.task_type}` : ""
              }${
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
              tertiaryActionLabel={canManageFollowups ? "Adiar +1 dia" : undefined}
              onTertiaryAction={
                canManageFollowups ? () => void onDefer(task) : undefined
              }
            />
          ))}
        </div>
      </SectionCard>

      {canManageFollowups ? (
        <div ref={createFormRef}>
        <SectionCard
          title="Nova tarefa"
          subtitle={
            highlightCreateForm
              ? "Cliente pré-preenchido — confirme prazo e título para agendar o follow-up."
              : "Follow-up com prazo, prioridade e cliente da carteira."
          }
          hint={CM_HELP.myDay.newTask}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <div className="cm-form-grid">
            <CommercialTextField
              label="Título"
              hint={CM_HELP.myDay.taskTitle}
              value={title}
              onChange={setTitle}
              placeholder="Ex.: Ligar para ACME sobre atraso"
              required
            />
            <CommercialTextField
              label="Prazo"
              hint={CM_HELP.myDay.taskDue}
              type="date"
              value={dueDate}
              onChange={setDueDate}
              required
            />
            <CommercialSelectField
              label="Prioridade"
              hint={CM_HELP.myDay.taskPriority}
              options={[...PRIORITY_OPTIONS]}
              value={priority}
              onChange={setPriority}
              allowEmpty={false}
            />
            <CommercialSelectField
              label="Tipo"
              hint={CM_HELP.myDay.taskType}
              options={[...TASK_TYPE_OPTIONS]}
              value={taskType}
              onChange={setTaskType}
              allowEmpty={false}
            />
            <CommercialSelectField
              label="Cliente"
              hint={CM_HELP.myDay.taskCustomer}
              options={customerOptions}
              value={customerKey}
              onChange={setCustomerKey}
              allowEmpty
              emptyLabel="Sem vínculo (opcional)"
              searchable={customerOptions.length > 8}
            />
            <div className="cm-form-grid__actions">
              <ActionButton
                variant="primary"
                disabled={creating || !title.trim() || !dueDate}
                onClick={() => void onCreate()}
              >
                {creating ? "Criando…" : "Criar tarefa"}
              </ActionButton>
            </div>
          </div>
        </SectionCard>
        </div>
      ) : null}
    </section>
  );
}
