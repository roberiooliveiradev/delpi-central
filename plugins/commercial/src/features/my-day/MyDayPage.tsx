import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActionButton,
  EmptyState,
  SectionCard,
  StatusBadge,
} from "@delpi/plugin-ui/index";

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
  cmStatusBadgeClassNames,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialScopeChipBar,
  CommercialSelectField,
  CommercialTextAreaField,
  CommercialTextField,
  CommercialTitleWithHelp,
  CommercialViewTransition,
  CommercialWorklistItem,
} from "../../app/commercialUi";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import { deferDueAtOneDay, dueDateInputToIsoEod, localDateInputValue } from "./myDayDueDate";

type MyDayPageProps = {
  basePath: string;
};

type BucketKey = "overdue" | "today" | "later";
type TypeFilter = "all" | string;

const PRIORITY_LABELS: Record<string, string> = {
  low: "Baixa",
  normal: "Normal",
  high: "Alta",
  critical: "Crítica",
};

const TASK_TYPE_OPTIONS = [
  { value: "follow_up", label: "Follow-up" },
  { value: "call", label: "Ligar" },
  { value: "email", label: "E-mail" },
  { value: "visit", label: "Visita" },
  { value: "todo", label: "To-do" },
] as const;

const TYPE_LABELS: Record<string, string> = Object.fromEntries(
  TASK_TYPE_OPTIONS.map((item) => [item.value, item.label]),
);

const PRIORITY_OPTIONS = [
  { value: "low", label: "Baixa" },
  { value: "normal", label: "Normal" },
  { value: "high", label: "Alta" },
] as const;

const BUCKET_META: Record<
  BucketKey,
  { label: string; emptyHint: string }
> = {
  overdue: {
    label: "Atrasadas",
    emptyHint: "Nenhuma atrasada — foque no hoje ou crie um follow-up.",
  },
  today: {
    label: "Hoje",
    emptyHint: "Nada com prazo hoje nesta fila.",
  },
  later: {
    label: "Depois",
    emptyHint: "Sem tarefas futuras — agende o próximo contato.",
  },
};

const cmEmptyCompactClassNames = {
  ...cmEmptyStateClassNames,
  root: `${cmEmptyStateClassNames.root} delpi-ui-state-box--compact cm-empty-compact`,
  withTitle: true,
};

function readCreateTaskDeepLink(): {
  createTask: boolean;
  customerCode: string;
  customerStore: string;
  bucket: BucketKey | null;
} {
  if (typeof window === "undefined") {
    return { createTask: false, customerCode: "", customerStore: "", bucket: null };
  }
  const params = new URLSearchParams(window.location.search);
  const rawBucket = (params.get("bucket") ?? "").trim().toLowerCase();
  const bucket: BucketKey | null =
    rawBucket === "overdue" || rawBucket === "today" || rawBucket === "later"
      ? rawBucket
      : null;
  return {
    createTask: params.get("createTask") === "1",
    customerCode: (params.get("customer_code") ?? "").trim(),
    customerStore: (params.get("customer_store") ?? "").trim(),
    bucket,
  };
}

function clearCreateTaskQueryFromUrl(): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  let changed = false;
  for (const key of ["createTask", "customer_code", "customer_store", "bucket"]) {
    if (url.searchParams.has(key)) {
      url.searchParams.delete(key);
      changed = true;
    }
  }
  if (!changed) return;
  window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
}

function truncateNote(text: string, max = 160): string {
  const normalized = text.replace(/\s+/g, " ").trim();
  if (normalized.length <= max) return normalized;
  return `${normalized.slice(0, max - 1).trimEnd()}…`;
}

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

function heroCopy(counts: { overdue: number; today: number; later: number }): {
  title: string;
  description: string;
} {
  if (counts.overdue > 0) {
    return {
      title: `${counts.overdue} atrasada${counts.overdue === 1 ? "" : "s"}`,
      description:
        "Priorize a fila atrasada antes do restante do dia. Conclua, adie ou abra a conta.",
    };
  }
  if (counts.today > 0) {
    return {
      title: `${counts.today} para hoje`,
      description: "Foque os follow-ups com prazo ainda hoje. Depois trate o que ficou para frente.",
    };
  }
  if (counts.later > 0) {
    return {
      title: "Fila em dia",
      description: "Nada atrasado nem para hoje — há tarefas futuras para acompanhar.",
    };
  }
  return {
    title: "Fila livre",
    description:
      "Nenhuma tarefa na worklist. Crie um follow-up com prazo para não perder o cliente.",
  };
}

export function MyDayPage({ basePath }: MyDayPageProps) {
  const { canManageFollowups, myPortfolio } = usePortfolioScope();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<WorklistData | null>(null);
  const [bucket, setBucket] = useState<BucketKey>("overdue");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState(localDateInputValue);
  const [priority, setPriority] = useState("normal");
  const [taskType, setTaskType] = useState("follow_up");
  const [customerKey, setCustomerKey] = useState("");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [creating, setCreating] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [highlightCreateForm, setHighlightCreateForm] = useState(false);
  const createFormRef = useRef<HTMLDivElement | null>(null);
  const deepLinkBucketRef = useRef<BucketKey | null>(null);

  const customerOptions = useMemo(() => {
    const rows = myPortfolio?.customers ?? [];
    return rows.map((c) => ({
      value: `${c.customer_code}|${c.customer_store}`,
      label: `${c.customer_name?.trim() || "Cliente"} (${c.customer_code}/${c.customer_store})`,
    }));
  }, [myPortfolio]);

  const focusCreateForm = useCallback(() => {
    setHighlightCreateForm(true);
    window.setTimeout(() => {
      createFormRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 80);
  }, []);

  useEffect(() => {
    if (!canManageFollowups) return;
    const link = readCreateTaskDeepLink();
    if (!link.createTask && !link.customerCode && !link.bucket) return;
    if (link.bucket) {
      deepLinkBucketRef.current = link.bucket;
      setBucket(link.bucket);
    }
    if (link.customerCode && link.customerStore) {
      setCustomerKey(`${link.customerCode}|${link.customerStore}`);
    }
    if (link.createTask || link.customerCode) {
      focusCreateForm();
    }
    clearCreateTaskQueryFromUrl();
    return undefined;
  }, [canManageFollowups, focusCreateForm]);

  const reload = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const wl = await getMyWorklist(signal);
      setData(wl);
      const pinned = deepLinkBucketRef.current;
      if (pinned) {
        setBucket(pinned);
        deepLinkBucketRef.current = null;
      } else if (wl.counts.overdue > 0) setBucket("overdue");
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

  const counts = {
    overdue: data?.counts.overdue ?? 0,
    today: data?.counts.today ?? 0,
    later: data?.counts.later ?? 0,
  };
  const openTotal = counts.overdue + counts.today + counts.later;
  const hero = heroCopy(counts);

  const items = useMemo(() => {
    if (!data) return [] as CommercialTaskDto[];
    const bucketItems = data[bucket] ?? [];
    if (typeFilter === "all") return bucketItems;
    return bucketItems.filter((task) => (task.task_type || "follow_up") === typeFilter);
  }, [bucket, data, typeFilter]);

  const typeFilterChips = useMemo(() => {
    const source = data ? [...data.overdue, ...data.today, ...data.later] : [];
    const counts = new Map<string, number>();
    for (const task of source) {
      const key = task.task_type || "follow_up";
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    const chips = [
      {
        id: "all",
        label: `Todos (${source.length})`,
        active: typeFilter === "all",
        onSelect: () => setTypeFilter("all"),
      },
    ];
    for (const option of TASK_TYPE_OPTIONS) {
      const count = counts.get(option.value) ?? 0;
      if (count === 0 && typeFilter !== option.value) continue;
      chips.push({
        id: option.value,
        label: `${option.label} (${count})`,
        active: typeFilter === option.value,
        onSelect: () => setTypeFilter(option.value),
      });
    }
    return chips;
  }, [data, typeFilter]);

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
      const note = description.trim();
      await createTask({
        title: trimmed,
        description: note || undefined,
        task_type: taskType || "follow_up",
        priority: priority || "normal",
        due_at: dueDateInputToIsoEod(dueDate),
        customer_code: customer?.code ?? null,
        customer_store: customer?.store ?? null,
      });
      setTitle("");
      setDescription("");
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

  const bucketChips = (
    [
      ["overdue", counts.overdue] as const,
      ["today", counts.today] as const,
      ["later", counts.later] as const,
    ] as const
  ).map(([id, count]) => ({
    id,
    label: `${BUCKET_META[id].label} (${count})`,
    active: bucket === id,
    onSelect: () => setBucket(id),
  }));

  return (
    <section className="cm-page-stack">
      <CommercialPageHero
        aria-label="Resumo do Meu dia"
        eyebrow="Meu dia"
        title={loading ? "Carregando fila…" : hero.title}
        description={
          loading
            ? "Buscando follow-ups e tarefas atribuídas a você."
            : hero.description
        }
        badge={
          !loading && counts.overdue > 0 ? (
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              label="Atrasadas"
              variant="danger"
            />
          ) : !loading && openTotal === 0 ? (
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              label="Em dia"
              variant="success"
            />
          ) : (
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              label={`${openTotal} aberta${openTotal === 1 ? "" : "s"}`}
              variant="info"
            />
          )
        }
        highlights={[
          {
            id: "overdue",
            label: "Atrasadas",
            value: loading ? "—" : counts.overdue.toLocaleString("pt-BR"),
          },
          {
            id: "today",
            label: "Hoje",
            value: loading ? "—" : counts.today.toLocaleString("pt-BR"),
          },
          {
            id: "later",
            label: "Depois",
            value: loading ? "—" : counts.later.toLocaleString("pt-BR"),
          },
        ]}
      />

      <SectionCard
        title="Fila"
        subtitle="Atrasadas → hoje → depois (padrão CRM)."
        hint={CM_HELP.myDay.worklist}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
        actions={
          <ActionButton variant="ghost" onClick={() => void reload()}>
            Atualizar
          </ActionButton>
        }
      >
        <div className="cm-my-day-toolbar">
          <CommercialScopeChipBar
            label="Fila"
            aria-label="Filas do Meu dia"
            chips={bucketChips}
          />
          {typeFilterChips.length > 1 ? (
            <CommercialScopeChipBar
              label={
                <CommercialTitleWithHelp
                  title="Tipo"
                  hint={CM_HELP.myDay.typeFilter}
                />
              }
              aria-label="Filtro por tipo de tarefa"
              chips={typeFilterChips}
            />
          ) : null}
        </div>

        {loading ? <CommercialLoadingCard title="Carregando worklist…" variant="panel" /> : null}
        {error ? (
          <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
        ) : null}
        {actionError ? (
          <EmptyState
            classNames={cmEmptyStateClassNames}
            defaultMessage={actionError}
            role="alert"
          />
        ) : null}

        {!loading && !error ? (
          <CommercialViewTransition transitionKey={`bucket-${bucket}-${typeFilter}`} tone="panel">
            {items.length === 0 ? (
              <EmptyState
                classNames={cmEmptyCompactClassNames}
                defaultTitle={
                  typeFilter === "all"
                    ? `Nenhuma em ${BUCKET_META[bucket].label.toLowerCase()}`
                    : `Nenhuma ${TYPE_LABELS[typeFilter] ?? typeFilter} em ${BUCKET_META[bucket].label.toLowerCase()}`
                }
                defaultMessage={
                  typeFilter === "all"
                    ? BUCKET_META[bucket].emptyHint
                    : "Tente outro tipo ou crie uma tarefa com este tipo."
                }
              >
                {canManageFollowups ? (
                  <ActionButton variant="primary" onClick={focusCreateForm}>
                    Criar follow-up
                  </ActionButton>
                ) : null}
              </EmptyState>
            ) : (
              <div className="cm-my-day-list" aria-label={`Tarefas: ${BUCKET_META[bucket].label}`}>
                {items.map((task) => {
                  const note = (task.description ?? "").trim();
                  const typeLabel = TYPE_LABELS[task.task_type] ?? task.task_type;
                  const priorityLabel =
                    PRIORITY_LABELS[task.priority] ?? task.priority;
                  return (
                  <CommercialWorklistItem
                    key={task.id}
                    title={task.title}
                    meta={`${formatDue(task.due_at)} · ${priorityLabel}${
                      typeLabel ? ` · ${typeLabel}` : ""
                    }${
                      task.customer_code
                        ? ` · ${task.customer_code}-${task.customer_store ?? ""}`
                        : ""
                    }`}
                    detail={note ? truncateNote(note) : undefined}
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
                  );
                })}
              </div>
            )}
          </CommercialViewTransition>
        ) : null}
      </SectionCard>

      {canManageFollowups ? (
        <div
          ref={createFormRef}
          className={
            highlightCreateForm ? "cm-my-day-create cm-my-day-create--focus" : "cm-my-day-create"
          }
        >
          <SectionCard
            title="Nova tarefa"
            subtitle={
              highlightCreateForm
                ? "Cliente ou ação pré-preenchidos — confirme prazo, título e observação."
                : "Título, prazo, tipo, cliente e observação — padrão HubSpot/Pipedrive."
            }
            hint={CM_HELP.myDay.newTask}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <div className="cm-my-day-form">
              <div className="cm-my-day-form__title">
                <CommercialTextField
                  label="Título"
                  hint={CM_HELP.myDay.taskTitle}
                  value={title}
                  onChange={setTitle}
                  placeholder="Ex.: Ligar para ACME sobre atraso"
                  required
                />
              </div>
              <div className="cm-my-day-form__title">
                <CommercialTextAreaField
                  label="Observação"
                  hint={CM_HELP.myDay.taskDescription}
                  value={description}
                  onChange={setDescription}
                  placeholder="Ex.: Cliente pediu retorno após emitir NF 12345"
                />
              </div>
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
              <div className="cm-my-day-form__actions">
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
