import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActionButton,
  EmptyState,
  SectionCard,
  StatusBadge,
} from "@delpi/plugin-ui/index";

import { useCommercialWorklistSync } from "../../app/CommercialRealtimeProvider";
import {
  completeTask,
  createTask,
  deferTask,
  deleteTask,
  getCompletedWorklist,
  getMyWorklist,
  updateTask,
  type CommercialTaskDto,
  type WorklistData,
  type WorklistScope,
} from "../../api/worklistApi";
import { uploadTaskAttachment } from "../../api/attachmentsApi";
import { CM_HELP } from "../../content/helpTooltips";
import { navigateCustomerDetail } from "../../app/pluginNavigation";
import { useCommercialConfirm } from "../../app/CommercialConfirmDialogProvider";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import {
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStatusBadgeClassNames,
  CommercialAttachmentFileList,
  CommercialFileDropzone,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialScopeChipBar,
  CommercialSelectField,
  CommercialTextAreaField,
  CommercialTextField,
  CommercialTitleWithHelp,
  CommercialViewTransition,
} from "../../app/commercialUi";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import {
  deferDueAtOneDay,
  dueDateInputToIsoEod,
  isoToLocalDateInput,
  localDateInputValue,
} from "./myDayDueDate";
import {
  TaskAttachmentPreviewModal,
  type TaskAttachmentPreviewTarget,
} from "./TaskAttachmentPreviewModal";
import { TaskAttachmentsBlock } from "./TaskAttachmentsBlock";
import { TaskDetailCard } from "./TaskDetailCard";

type MyDayPageProps = {
  basePath: string;
};

type BucketKey = "overdue" | "today" | "later" | "done";
type TypeFilter = "all" | string;
type TaskFormMode = "closed" | "create" | "edit";

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
  done: {
    label: "Concluídas",
    emptyHint: "Nenhuma tarefa concluída neste escopo ainda.",
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
    rawBucket === "overdue" ||
    rawBucket === "today" ||
    rawBucket === "later" ||
    rawBucket === "done"
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

function toneForBucket(bucket: BucketKey): "danger" | "warning" | "neutral" | "success" {
  if (bucket === "overdue") return "danger";
  if (bucket === "today") return "warning";
  if (bucket === "done") return "success";
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
  const { canManageFollowups, isAdmin, myPortfolio, currentUserId, sellers } =
    usePortfolioScope();
  const { notifyError, notifySuccess, notifyMissingRequired } = useCommercialFloatingNotice();
  const confirm = useCommercialConfirm();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<WorklistData | null>(null);
  const [doneItems, setDoneItems] = useState<CommercialTaskDto[]>([]);
  const [doneCount, setDoneCount] = useState(0);
  const [workScope, setWorkScope] = useState<WorklistScope>("mine");
  const [teamAssigneeFilter, setTeamAssigneeFilter] = useState("");
  const [bucket, setBucket] = useState<BucketKey>("overdue");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState(localDateInputValue);
  const [priority, setPriority] = useState("normal");
  const [taskType, setTaskType] = useState("follow_up");
  const [customerKey, setCustomerKey] = useState("");
  const [assigneeUserId, setAssigneeUserId] = useState("");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [creating, setCreating] = useState(false);
  const [savingEdit, setSavingEdit] = useState(false);
  const [pendingAttachments, setPendingAttachments] = useState<
    Array<{ id: string; file: File }>
  >([]);
  const [pendingPreview, setPendingPreview] = useState<TaskAttachmentPreviewTarget>(null);
  const [formMode, setFormMode] = useState<TaskFormMode>("closed");
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const taskFormRef = useRef<HTMLDivElement | null>(null);
  const deepLinkBucketRef = useRef<BucketKey | null>(null);

  const activeSellers = useMemo(
    () => sellers.filter((seller) => seller.active && seller.user_id.trim()),
    [sellers],
  );

  const directoryUserIds = useMemo(() => {
    const ids = activeSellers.map((seller) => seller.user_id);
    if (myPortfolio?.user_id) ids.push(myPortfolio.user_id);
    if (data) {
      for (const task of [...data.overdue, ...data.today, ...data.later]) {
        if (task.assignee_user_id) ids.push(task.assignee_user_id);
        if (task.created_by_user_id) ids.push(task.created_by_user_id);
      }
    }
    for (const task of doneItems) {
      if (task.assignee_user_id) ids.push(task.assignee_user_id);
      if (task.created_by_user_id) ids.push(task.created_by_user_id);
    }
    return ids;
  }, [activeSellers, data, doneItems, myPortfolio?.user_id]);
  const { labelFor: directoryLabelFor } = useDirectoryUserLabels(directoryUserIds);

  const sellerNameByUserId = useMemo(() => {
    const map = new Map<string, string>();
    for (const seller of activeSellers) {
      map.set(
        seller.user_id,
        directoryLabelFor(seller.user_id, seller.display_name),
      );
    }
    return map;
  }, [activeSellers, directoryLabelFor]);

  const sellerOptions = useMemo(
    () =>
      activeSellers.map((seller) => ({
        value: seller.user_id,
        label: directoryLabelFor(seller.user_id, seller.display_name),
      })),
    [activeSellers, directoryLabelFor],
  );

  const customerOptions = useMemo(() => {
    const portfolio =
      isAdmin && assigneeUserId
        ? activeSellers.find((seller) => seller.user_id === assigneeUserId) ?? myPortfolio
        : myPortfolio;
    const rows = portfolio?.customers ?? [];
    return rows.map((c) => ({
      value: `${c.customer_code}|${c.customer_store}`,
      label: `${c.customer_name?.trim() || "Cliente"} (${c.customer_code}/${c.customer_store})`,
    }));
  }, [activeSellers, assigneeUserId, isAdmin, myPortfolio]);

  const resetTaskFormFields = useCallback(() => {
    setTitle("");
    setDescription("");
    setPendingAttachments([]);
    setPendingPreview(null);
    setDueDate(localDateInputValue());
    setPriority("normal");
    setTaskType("follow_up");
    setCustomerKey("");
    setAssigneeUserId("");
    setEditingTaskId(null);
  }, []);

  const scrollToTaskForm = useCallback(() => {
    window.setTimeout(() => {
      taskFormRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 80);
  }, []);

  const openCreateForm = useCallback(() => {
    resetTaskFormFields();
    setFormMode("create");
    scrollToTaskForm();
  }, [resetTaskFormFields, scrollToTaskForm]);

  const openEditForm = useCallback(
    (task: CommercialTaskDto) => {
      const me = (currentUserId || myPortfolio?.user_id || "").trim();
      const createdBy = (task.created_by_user_id || "").trim();
      const assignee = (task.assignee_user_id || "").trim();
      const allowed =
        Boolean(me) && (createdBy === me || assignee === me || isAdmin);
      if (!allowed) {
        notifyError("Sem permissão para editar esta tarefa.");
        return;
      }
      setPendingAttachments([]);
      setPendingPreview(null);
      setEditingTaskId(task.id);
      setTitle(task.title ?? "");
      setDescription((task.description ?? "").trim());
      setDueDate(isoToLocalDateInput(task.due_at));
      setPriority(task.priority || "normal");
      setTaskType(task.task_type || "follow_up");
      setAssigneeUserId(task.assignee_user_id || "");
      setCustomerKey(
        task.customer_code && task.customer_store
          ? `${task.customer_code}|${task.customer_store}`
          : "",
      );
      setFormMode("edit");
      scrollToTaskForm();
    },
    [currentUserId, isAdmin, myPortfolio?.user_id, notifyError, scrollToTaskForm],
  );

  const closeTaskForm = useCallback(() => {
    setFormMode("closed");
    resetTaskFormFields();
  }, [resetTaskFormFields]);

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
      resetTaskFormFields();
      if (link.customerCode && link.customerStore) {
        setCustomerKey(`${link.customerCode}|${link.customerStore}`);
      }
      setFormMode("create");
      scrollToTaskForm();
    }
    clearCreateTaskQueryFromUrl();
    return undefined;
  }, [canManageFollowups, resetTaskFormFields, scrollToTaskForm]);

  const reload = useCallback(
    async (signal?: AbortSignal, options?: { preferBucket?: BucketKey | null }) => {
      setLoading(true);
      setError(null);
      const scope = isAdmin && workScope === "team" ? "team" : "mine";
      const assigneeUserId =
        isAdmin && workScope === "team" && teamAssigneeFilter
          ? teamAssigneeFilter
          : null;
      try {
        const [wl, done] = await Promise.all([
          getMyWorklist({ scope, assigneeUserId, signal }),
          getCompletedWorklist({ scope, assigneeUserId, signal }),
        ]);
        if (signal?.aborted) return;
        setData(wl);
        setDoneItems(done.items ?? []);
        setDoneCount(done.count ?? done.items?.length ?? 0);
        const pinned = options?.preferBucket ?? deepLinkBucketRef.current;
        if (pinned) {
          setBucket(pinned);
          deepLinkBucketRef.current = null;
        } else {
          setBucket((current) => {
            if (current === "done") return "done";
            if (wl.counts.overdue > 0) return "overdue";
            if (wl.counts.today > 0) return "today";
            if (wl.counts.later > 0) return "later";
            return current === "overdue" || current === "today" || current === "later"
              ? current
              : "later";
          });
        }
      } catch (err: unknown) {
        if (signal?.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar Meu dia.");
        setData(null);
        setDoneItems([]);
        setDoneCount(0);
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [isAdmin, teamAssigneeFilter, workScope],
  );

  useEffect(() => {
    if (!isAdmin && workScope === "team") {
      setWorkScope("mine");
      setTeamAssigneeFilter("");
    }
  }, [isAdmin, workScope]);

  useEffect(() => {
    const controller = new AbortController();
    void reload(controller.signal);
    return () => controller.abort();
  }, [reload]);

  useCommercialWorklistSync(() => {
    void reload();
  }, canManageFollowups);

  const counts = {
    overdue: data?.counts.overdue ?? 0,
    today: data?.counts.today ?? 0,
    later: data?.counts.later ?? 0,
    done: doneCount,
  };
  const openTotal = counts.overdue + counts.today + counts.later;
  const hero = heroCopy(counts);

  const items = useMemo(() => {
    if (bucket === "done") {
      if (typeFilter === "all") return doneItems;
      return doneItems.filter((task) => (task.task_type || "follow_up") === typeFilter);
    }
    if (!data) return [] as CommercialTaskDto[];
    const bucketItems = data[bucket] ?? [];
    if (typeFilter === "all") return bucketItems;
    return bucketItems.filter((task) => (task.task_type || "follow_up") === typeFilter);
  }, [bucket, data, doneItems, typeFilter]);

  const typeFilterChips = useMemo(() => {
    const source =
      bucket === "done"
        ? doneItems
        : data
          ? [...data.overdue, ...data.today, ...data.later]
          : [];
    const typeCounts = new Map<string, number>();
    for (const task of source) {
      const key = task.task_type || "follow_up";
      typeCounts.set(key, (typeCounts.get(key) ?? 0) + 1);
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
      const count = typeCounts.get(option.value) ?? 0;
      if (count === 0 && typeFilter !== option.value) continue;
      chips.push({
        id: option.value,
        label: `${option.label} (${count})`,
        active: typeFilter === option.value,
        onSelect: () => setTypeFilter(option.value),
      });
    }
    return chips;
  }, [bucket, data, doneItems, typeFilter]);

  const onComplete = async (taskId: string) => {
    if (!canManageFollowups) return;
    try {
      await completeTask(taskId);
      notifySuccess("Tarefa concluída.");
      await reload();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao concluir.");
    }
  };

  const onDelete = async (task: CommercialTaskDto) => {
    if (!canManageFollowups) return;
    const label = (task.title || "").trim() || "esta tarefa";
    const ok = await confirm({
      title: "Excluir tarefa",
      message: `Excluir «${label}»? Esta ação não pode ser desfeita.`,
      confirmLabel: "Excluir",
      cancelLabel: "Cancelar",
      variant: "danger",
    });
    if (!ok) return;
    try {
      await deleteTask(task.id);
      if (editingTaskId === task.id) closeTaskForm();
      notifySuccess("Tarefa excluída.");
      await reload();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao excluir.");
    }
  };

  const onDefer = async (task: CommercialTaskDto) => {
    if (!canManageFollowups) return;
    try {
      await deferTask(task.id, deferDueAtOneDay(task.due_at));
      notifySuccess("Prazo adiado em +1 dia.");
      await reload();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao adiar.");
    }
  };

  const onCreate = async () => {
    if (!canManageFollowups) return;
    const missing: string[] = [];
    if (!title.trim()) missing.push("Título");
    if (!dueDate) missing.push("Prazo");
    if (!notifyMissingRequired(missing)) return;
    setCreating(true);
    try {
      const customer = parseCustomerKey(customerKey);
      const note = description.trim();
      const created = await createTask({
        title: title.trim(),
        description: note || undefined,
        task_type: taskType || "follow_up",
        priority: priority || "normal",
        due_at: dueDateInputToIsoEod(dueDate),
        customer_code: customer?.code ?? null,
        customer_store: customer?.store ?? null,
        assignee_user_id: isAdmin && assigneeUserId ? assigneeUserId : undefined,
      });
      if (pendingAttachments.length > 0) {
        const failed: string[] = [];
        for (const item of pendingAttachments) {
          try {
            await uploadTaskAttachment(created.id, item.file);
          } catch {
            failed.push(item.file.name);
          }
        }
        if (failed.length > 0) {
          notifyError(
            `Tarefa criada, mas falhou o anexo: ${failed.join(", ")}.`,
          );
        }
      }
      const hadAttachment = pendingAttachments.length > 0;
      resetTaskFormFields();
      setFormMode("closed");
      notifySuccess(hadAttachment ? "Tarefa criada com anexo." : "Tarefa criada.");
      await reload();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao criar tarefa.");
    } finally {
      setCreating(false);
    }
  };

  const onSaveEdit = async () => {
    if (!canManageFollowups || !editingTaskId) return;
    const missing: string[] = [];
    if (!title.trim()) missing.push("Título");
    if (!dueDate) missing.push("Prazo");
    if (!notifyMissingRequired(missing)) return;
    setSavingEdit(true);
    try {
      const customer = parseCustomerKey(customerKey);
      const note = description.trim();
      await updateTask(editingTaskId, {
        title: title.trim(),
        description: note || null,
        task_type: taskType || "follow_up",
        priority: priority || "normal",
        due_at: dueDateInputToIsoEod(dueDate),
        customer_code: customer?.code ?? null,
        customer_store: customer?.store ?? null,
        assignee_user_id: isAdmin && assigneeUserId ? assigneeUserId : undefined,
      });
      closeTaskForm();
      notifySuccess("Tarefa atualizada.");
      await reload();
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao atualizar tarefa.");
    } finally {
      setSavingEdit(false);
    }
  };

  const scopeChips = [
    {
      id: "mine",
      label: "Minhas",
      active: workScope === "mine",
      onSelect: () => {
        setWorkScope("mine");
        setTeamAssigneeFilter("");
      },
    },
    {
      id: "team",
      label: "Equipe",
      active: workScope === "team",
      onSelect: () => setWorkScope("team"),
    },
  ];

  const bucketChips = (
    [
      ["overdue", counts.overdue] as const,
      ["today", counts.today] as const,
      ["later", counts.later] as const,
      ["done", counts.done] as const,
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
            ? workScope === "team"
              ? "Buscando follow-ups da equipe…"
              : "Buscando follow-ups e tarefas atribuídas a você."
            : workScope === "team"
              ? `${hero.description} Visão da equipe.`
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
        subtitle="Atrasadas → hoje → depois → concluídas."
        hint={CM_HELP.myDay.worklist}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
        actions={
          <div className="cm-my-day-queue-actions">
            {canManageFollowups ? (
              <ActionButton variant="primary" onClick={openCreateForm}>
                Nova tarefa
              </ActionButton>
            ) : null}
            <ActionButton variant="ghost" onClick={() => void reload()}>
              Atualizar
            </ActionButton>
          </div>
        }
      >
        <div className="cm-my-day-toolbar">
          {isAdmin ? (
            <CommercialScopeChipBar
              label={
                <CommercialTitleWithHelp
                  title="Escopo"
                  hint={
                    workScope === "team" ? CM_HELP.myDay.scopeTeam : CM_HELP.myDay.scopeMine
                  }
                />
              }
              aria-label="Escopo da worklist"
              chips={scopeChips}
            />
          ) : null}
          {isAdmin && workScope === "team" && sellerOptions.length > 0 ? (
            <div className="cm-my-day-toolbar__filter">
              <CommercialSelectField
                label="Responsável"
                hint={CM_HELP.myDay.teamAssigneeFilter}
                options={sellerOptions}
                value={teamAssigneeFilter}
                onChange={setTeamAssigneeFilter}
                allowEmpty
                emptyLabel="Toda a equipe"
                searchable={sellerOptions.length > 8}
              />
            </div>
          ) : null}
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

        {!loading && !error ? (
          <CommercialViewTransition
            transitionKey={`scope-${workScope}-${teamAssigneeFilter}-bucket-${bucket}-${typeFilter}`}
            tone="panel"
          >
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
                {canManageFollowups && bucket !== "done" ? (
                  <ActionButton variant="primary" onClick={openCreateForm}>
                    Nova tarefa
                  </ActionButton>
                ) : null}
              </EmptyState>
            ) : (
              <div className="cm-my-day-list" aria-label={`Tarefas: ${BUCKET_META[bucket].label}`}>
                {items.map((task) => {
                  const typeLabel = TYPE_LABELS[task.task_type] ?? task.task_type;
                  const priorityLabel =
                    PRIORITY_LABELS[task.priority] ?? task.priority;
                  const assigneeLabel =
                    workScope === "team"
                      ? sellerNameByUserId.get(task.assignee_user_id) ??
                        directoryLabelFor(task.assignee_user_id)
                      : null;
                  const createdBy = (task.created_by_user_id || "").trim();
                  const assignee = (task.assignee_user_id || "").trim();
                  const me = (currentUserId || myPortfolio?.user_id || "").trim();
                  const assignedByLabel =
                    createdBy && createdBy !== assignee
                      ? sellerNameByUserId.get(createdBy) ?? directoryLabelFor(createdBy)
                      : null;
                  const readOnly = bucket === "done";
                  const canEditTask =
                    !readOnly &&
                    canManageFollowups &&
                    Boolean(me) &&
                    (createdBy === me || assignee === me || isAdmin);
                  return (
                    <TaskDetailCard
                      key={task.id}
                      task={task}
                      tone={toneForBucket(bucket)}
                      typeLabel={typeLabel}
                      priorityLabel={priorityLabel}
                      assigneeLabel={assigneeLabel}
                      assignedByLabel={assignedByLabel}
                      canManage={canManageFollowups}
                      canEdit={canEditTask}
                      canDelete={canEditTask}
                      readOnly={readOnly}
                      formatDue={formatDue}
                      onEdit={() => openEditForm(task)}
                      onDelete={() => void onDelete(task)}
                      onComplete={() => void onComplete(task.id)}
                      onDefer={() => void onDefer(task)}
                      onOpenAccount={
                        task.customer_code && task.customer_store
                          ? () =>
                              navigateCustomerDetail(
                                task.customer_code!,
                                task.customer_store!,
                                { basePath },
                              )
                          : undefined
                      }
                      onAttachmentsChanged={() => void reload()}
                      notifyError={notifyError}
                      notifySuccess={notifySuccess}
                    />
                  );
                })}
              </div>
            )}
          </CommercialViewTransition>
        ) : null}
      </SectionCard>

      {canManageFollowups && formMode !== "closed" ? (
        <div ref={taskFormRef} className="cm-my-day-create">
          <SectionCard
            title={formMode === "edit" ? "Editar tarefa" : "Nova tarefa"}
            subtitle={
              formMode === "edit"
                ? isAdmin
                  ? "Altere campos, responsável e anexos; salve para gravar."
                  : "Altere campos e anexos; salve para gravar."
                : isAdmin
                  ? "Título, prazo, tipo, responsável, cliente, observação e anexos."
                  : "Título, prazo, tipo, cliente, observação e anexos — padrão HubSpot/Pipedrive."
            }
            hint={formMode === "edit" ? CM_HELP.myDay.editTask : CM_HELP.myDay.newTask}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
            collapsible
            open={formMode !== "closed"}
            onOpenChange={(next) => {
              if (!next) closeTaskForm();
            }}
            actions={
              <ActionButton variant="ghost" onClick={closeTaskForm}>
                Fechar
              </ActionButton>
            }
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
              {isAdmin && sellerOptions.length > 0 ? (
                <CommercialSelectField
                  label="Responsável"
                  hint={CM_HELP.myDay.taskAssignee}
                  options={sellerOptions}
                  value={assigneeUserId}
                  onChange={(value) => {
                    setAssigneeUserId(value);
                    setCustomerKey("");
                  }}
                  allowEmpty={formMode !== "edit"}
                  emptyLabel="Eu (padrão)"
                  searchable={sellerOptions.length > 8}
                />
              ) : null}
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
              {formMode === "create" ? (
                <div className="cm-my-day-form__title cm-my-day-attachments">
                  <CommercialFileDropzone
                    multiple
                    accept=".pdf,.png,.jpg,.jpeg,.webp,.gif,.txt,.doc,.docx,.xls,.xlsx,application/pdf,image/*,text/plain"
                    fieldLabel="Anexo (opcional)"
                    onFilesSelected={(files) => {
                      setPendingAttachments((current) => [
                        ...current,
                        ...files.map((file) => ({
                          id: `pending-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
                          file,
                        })),
                      ]);
                    }}
                    labels={{
                      title: "Arraste ou clique para anexar",
                      hint: "PDF, imagem, TXT, Word ou Excel · máx. 10 MB por arquivo",
                    }}
                  />
                  <CommercialAttachmentFileList
                    items={pendingAttachments.map((item) => ({
                      id: item.id,
                      fileName: item.file.name,
                      detail:
                        item.file.size < 1024
                          ? `${item.file.size} B`
                          : item.file.size < 1024 * 1024
                            ? `${(item.file.size / 1024).toFixed(1)} KB`
                            : `${(item.file.size / (1024 * 1024)).toFixed(1)} MB`,
                    }))}
                    emptyMessage="Nenhum arquivo na fila. Use a área acima para anexar."
                    labels={{ empty: "Nenhum arquivo na fila. Use a área acima para anexar." }}
                    onOpen={(item) => {
                      const found = pendingAttachments.find((row) => row.id === item.id);
                      if (found) setPendingPreview({ kind: "local", file: found.file });
                    }}
                    onRemove={(item) => {
                      setPendingAttachments((current) =>
                        current.filter((row) => row.id !== item.id),
                      );
                    }}
                    canRemove
                  />
                </div>
              ) : null}
              {formMode === "edit" && editingTaskId ? (
                <div className="cm-my-day-form__title">
                  <TaskAttachmentsBlock
                    taskId={editingTaskId}
                    mode="manage"
                    onChanged={() => void reload()}
                    notifyError={notifyError}
                    notifySuccess={notifySuccess}
                  />
                </div>
              ) : null}
              <div className="cm-my-day-form__actions">
                <ActionButton variant="ghost" onClick={closeTaskForm}>
                  Cancelar
                </ActionButton>
                {formMode === "edit" ? (
                  <ActionButton
                    variant="primary"
                    disabled={savingEdit}
                    onClick={() => void onSaveEdit()}
                  >
                    {savingEdit ? "Salvando…" : "Salvar alterações"}
                  </ActionButton>
                ) : (
                  <ActionButton
                    variant="primary"
                    disabled={creating}
                    onClick={() => void onCreate()}
                  >
                    {creating ? "Criando…" : "Criar tarefa"}
                  </ActionButton>
                )}
              </div>
            </div>
          </SectionCard>
        </div>
      ) : null}
      <TaskAttachmentPreviewModal
        target={pendingPreview}
        open={Boolean(pendingPreview)}
        onClose={() => setPendingPreview(null)}
      />
    </section>
  );
}
