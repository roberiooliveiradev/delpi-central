import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  StatusBadge,
  UserDirectoryPicker,
  type DirectoryUserOption,
} from "@delpi/plugin-ui/index";
import { X } from "lucide-react";

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
import { listCommercialGroups, type CommercialGroupDto } from "../../api/commercialGroupsApi";
import { uploadTaskAttachment } from "../../api/attachmentsApi";
import { searchDirectoryUsers } from "../../api/commercialPortfolioApi";
import { CM_HELP } from "../../content/helpTooltips";
import { navigateCustomerDetail, navigateUserProfile, buildUserProfileHref, buildCustomerDetailHref } from "../../app/pluginNavigation";
import { currentReturnNav } from "../../app/commercialNavigationReturn";
import { accountLinkTitle, profileLinkTitle } from "../../content/entityLinkHints";
import { useCommercialConfirm } from "../../app/CommercialConfirmDialogProvider";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { useDirectoryUserLabels } from "../../app/useDirectoryUserLabels";
import {
  cmStatusBadgeClassNames,
  CommercialActionButton,
  CommercialAttachmentPreviewStrip,
  CommercialEmptyState,
  CommercialFileDropzone,
  CommercialLoadingCard,
  CommercialMultiSelectField,
  CommercialPageHero,
  CommercialScopeChipBar,
  CommercialSectionCard,
  CommercialSelectField,
  CommercialSegmentToggle,
  CommercialStatusBadge,
  CommercialTextAreaField,
  CommercialTextField,
  CommercialTitleWithHelp,
  CommercialViewTransition,
} from "../../app/commercialUi";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import { CustomerAvatar } from "../customers/components/CustomerAvatar";
import {
  CustomerSearchPicker,
  type CustomerSearchSelection,
} from "../customers/components/CustomerSearchPicker";
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
import { TaskEntityLinkChips } from "./TaskEntityLinkChips";
import { TaskUserChipAvatar } from "./TaskUserChipAvatar";
import { TaskUserLinkChip } from "./TaskUserLinkChip";

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

function readCreateTaskDeepLink(): {
  createTask: boolean;
  customerCode: string;
  customerStore: string;
  assigneeUserId: string;
  bucket: BucketKey | null;
} {
  if (typeof window === "undefined") {
    return {
      createTask: false,
      customerCode: "",
      customerStore: "",
      assigneeUserId: "",
      bucket: null,
    };
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
    assigneeUserId: (params.get("assignee_user_id") ?? "").trim(),
    bucket,
  };
}

function clearCreateTaskQueryFromUrl(): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  let changed = false;
  for (const key of [
    "createTask",
    "customer_code",
    "customer_store",
    "assignee_user_id",
    "bucket",
  ]) {
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

function directoryOptionFromId(
  userId: string,
  labelFor: (id: string, fallback?: string | null) => string,
): DirectoryUserOption {
  const id = userId.trim();
  return {
    id,
    name: labelFor(id, id),
    email: "",
  };
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
  const {
    canManageFollowups,
    isAdmin,
    canViewWorklistTeam,
    canManagePortfolios,
    myPortfolio,
    currentUserId,
    sellers,
  } = usePortfolioScope();
  const canTeamWorklist = canViewWorklistTeam || isAdmin;
  const canAssignGroups = canManagePortfolios || isAdmin;
  const { notifyError, notifySuccess, notifyMissingRequired } = useCommercialFloatingNotice();
  const confirm = useCommercialConfirm();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<WorklistData | null>(null);
  const [doneItems, setDoneItems] = useState<CommercialTaskDto[]>([]);
  const [doneCount, setDoneCount] = useState(0);
  const [workScope, setWorkScope] = useState<WorklistScope>("mine");
  const [teamAssigneeFilter, setTeamAssigneeFilter] = useState("");
  const [teamAssigneePicker, setTeamAssigneePicker] = useState<DirectoryUserOption[]>([]);
  const [bucket, setBucket] = useState<BucketKey>("overdue");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState(localDateInputValue);
  const [priority, setPriority] = useState("normal");
  const [taskType, setTaskType] = useState("follow_up");
  const [customerSelection, setCustomerSelection] = useState<CustomerSearchSelection[]>(
    [],
  );
  const [assigneePicker, setAssigneePicker] = useState<DirectoryUserOption[]>([]);
  const [assigneeGroupIds, setAssigneeGroupIds] = useState<string[]>([]);
  const [assigneeMode, setAssigneeMode] = useState<"users" | "groups">("users");
  const [groupOptions, setGroupOptions] = useState<CommercialGroupDto[]>([]);
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [creating, setCreating] = useState(false);
  const [savingEdit, setSavingEdit] = useState(false);
  const [pendingAttachments, setPendingAttachments] = useState<
    Array<{ id: string; file: File }>
  >([]);
  const [pendingThumbUrls, setPendingThumbUrls] = useState<Record<string, string>>({});
  const [pendingPreview, setPendingPreview] = useState<TaskAttachmentPreviewTarget>(null);
  const [formMode, setFormMode] = useState<TaskFormMode>("closed");
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const taskFormRef = useRef<HTMLDivElement | null>(null);
  const deepLinkBucketRef = useRef<BucketKey | null>(null);

  useEffect(() => {
    const next: Record<string, string> = {};
    for (const item of pendingAttachments) {
      const mime = (item.file.type || "").toLowerCase();
      const isImage =
        mime.startsWith("image/") ||
        /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(item.file.name || "");
      if (isImage) next[item.id] = URL.createObjectURL(item.file);
    }
    setPendingThumbUrls(next);
    return () => {
      for (const url of Object.values(next)) URL.revokeObjectURL(url);
    };
  }, [pendingAttachments]);

  const assigneeUserIds = useMemo(
    () =>
      assigneePicker
        .map((item) => item.id.trim())
        .filter(Boolean),
    [assigneePicker],
  );

  const activeSellers = useMemo(
    () =>
      sellers.filter(
        (seller) => seller.active && Boolean((seller.user_id ?? "").trim()),
      ),
    [sellers],
  );

  const directoryUserIds = useMemo(() => {
    const ids = activeSellers.map((seller) => seller.user_id);
    if (myPortfolio?.user_id) ids.push(myPortfolio.user_id);
    ids.push(...assigneeUserIds);
    if (teamAssigneeFilter) ids.push(teamAssigneeFilter);
    if (data) {
      for (const uid of data.team_user_ids ?? []) {
        if (uid) ids.push(uid);
      }
      for (const task of [...data.overdue, ...data.today, ...data.later]) {
        for (const uid of task.assignee_user_ids?.length
          ? task.assignee_user_ids
          : task.assignee_user_id
            ? [task.assignee_user_id]
            : []) {
          if (uid) ids.push(uid);
        }
        if (task.created_by_user_id) ids.push(task.created_by_user_id);
        if (task.completed_by_user_id) ids.push(task.completed_by_user_id);
      }
    }
    for (const task of doneItems) {
      for (const uid of task.assignee_user_ids?.length
        ? task.assignee_user_ids
        : task.assignee_user_id
          ? [task.assignee_user_id]
          : []) {
        if (uid) ids.push(uid);
      }
      if (task.created_by_user_id) ids.push(task.created_by_user_id);
      if (task.completed_by_user_id) ids.push(task.completed_by_user_id);
    }
    return ids;
  }, [
    activeSellers,
    assigneeUserIds,
    data,
    doneItems,
    myPortfolio?.user_id,
    teamAssigneeFilter,
  ]);
  const { labelFor: directoryLabelFor } = useDirectoryUserLabels(directoryUserIds);

  const sellerNameByUserId = useMemo(() => {
    const map = new Map<string, string>();
    for (const seller of activeSellers) {
      const uid = (seller.user_id ?? "").trim();
      if (!uid) continue;
      map.set(uid, directoryLabelFor(uid, seller.display_name));
    }
    return map;
  }, [activeSellers, directoryLabelFor]);

  const resetTaskFormFields = useCallback(() => {
    setTitle("");
    setDescription("");
    setPendingAttachments([]);
    setPendingPreview(null);
    setDueDate(localDateInputValue());
    setPriority("normal");
    setTaskType("follow_up");
    setCustomerSelection([]);
    setAssigneePicker([]);
    setAssigneeGroupIds([]);
    setAssigneeMode("users");
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
      if (!me || createdBy !== me) {
        notifyError("Só quem criou a tarefa pode editá-la.");
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
      const nextUserIds =
        task.assignee_user_ids?.length
          ? task.assignee_user_ids
          : task.assignee_user_id
            ? [task.assignee_user_id]
            : [];
      const nextGroupIds = task.assignee_group_ids?.length
        ? [...task.assignee_group_ids]
        : (task.assignee_groups ?? []).map((group) => group.id).filter(Boolean);
      const preferGroups = canAssignGroups && nextGroupIds.length > 0;
      setAssigneeMode(preferGroups ? "groups" : "users");
      setAssigneePicker(
        preferGroups
          ? []
          : nextUserIds.map((uid) => directoryOptionFromId(uid, directoryLabelFor)),
      );
      setAssigneeGroupIds(preferGroups ? nextGroupIds : []);
      const customers =
        task.customers?.length
          ? task.customers.map((item) => ({
              code: item.customer_code,
              store: item.customer_store,
              name: (item.customer_name || "").trim(),
            }))
          : task.customer_code && task.customer_store
            ? [
                {
                  code: task.customer_code,
                  store: task.customer_store,
                  name: (task.customer_name || "").trim(),
                },
              ]
            : [];
      setCustomerSelection(customers);
      setFormMode("edit");
      scrollToTaskForm();
    },
    [canAssignGroups, currentUserId, directoryLabelFor, myPortfolio?.user_id, notifyError, scrollToTaskForm],
  );

  const closeTaskForm = useCallback(() => {
    setFormMode("closed");
    resetTaskFormFields();
  }, [resetTaskFormFields]);

  useEffect(() => {
    if (!canManageFollowups) return;
    const link = readCreateTaskDeepLink();
    if (
      !link.createTask &&
      !link.customerCode &&
      !link.assigneeUserId &&
      !link.bucket
    ) {
      return;
    }
    if (link.bucket) {
      deepLinkBucketRef.current = link.bucket;
      setBucket(link.bucket);
    }
    if (link.createTask || link.customerCode || link.assigneeUserId) {
      resetTaskFormFields();
      if (link.customerCode && link.customerStore) {
        setCustomerSelection([
          {
            code: link.customerCode,
            store: link.customerStore,
            name: "",
          },
        ]);
      }
      if (link.assigneeUserId) {
        setAssigneeMode("users");
        setAssigneePicker([
          directoryOptionFromId(link.assigneeUserId, directoryLabelFor),
        ]);
      }
      setFormMode("create");
      scrollToTaskForm();
    }
    clearCreateTaskQueryFromUrl();
    return undefined;
  }, [
    canManageFollowups,
    directoryLabelFor,
    resetTaskFormFields,
    scrollToTaskForm,
  ]);

  const reload = useCallback(
    async (signal?: AbortSignal, options?: { preferBucket?: BucketKey | null }) => {
      setLoading(true);
      setError(null);
      const scope = canTeamWorklist && workScope === "team" ? "team" : "mine";
      const assigneeUserId =
        canTeamWorklist && workScope === "team" && teamAssigneeFilter
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
    [canTeamWorklist, teamAssigneeFilter, workScope],
  );

  useEffect(() => {
    if (!canTeamWorklist && workScope === "team") {
      setWorkScope("mine");
      setTeamAssigneeFilter("");
    }
  }, [canTeamWorklist, workScope]);

  useEffect(() => {
    if (!canAssignGroups) {
      setGroupOptions([]);
      return;
    }
    const controller = new AbortController();
    void listCommercialGroups({ activeOnly: true, signal: controller.signal })
      .then((items) => {
        if (!controller.signal.aborted) {
          setGroupOptions(items);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) setGroupOptions([]);
      });
    return () => controller.abort();
  }, [canAssignGroups]);

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
      const customers = customerSelection
        .filter((item) => item.code.trim() && item.store.trim())
        .map((item) => ({
          code: item.code.trim(),
          store: item.store.trim(),
          name: item.name.trim() || null,
        }));
      const note = description.trim();
      const created = await createTask({
        title: title.trim(),
        description: note || undefined,
        task_type: taskType || "follow_up",
        priority: priority || "normal",
        due_at: dueDateInputToIsoEod(dueDate),
        customers: customers.length > 0 ? customers : undefined,
        assignee_user_ids:
          canTeamWorklist &&
          assigneeMode === "users" &&
          assigneeUserIds.length > 0
            ? assigneeUserIds
            : undefined,
        assignee_group_ids:
          canAssignGroups &&
          assigneeMode === "groups" &&
          assigneeGroupIds.length > 0
            ? assigneeGroupIds
            : undefined,
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
      const customers = customerSelection
        .filter((item) => item.code.trim() && item.store.trim())
        .map((item) => ({
          code: item.code.trim(),
          store: item.store.trim(),
          name: item.name.trim() || null,
        }));
      const note = description.trim();
      await updateTask(editingTaskId, {
        title: title.trim(),
        description: note || null,
        task_type: taskType || "follow_up",
        priority: priority || "normal",
        due_at: dueDateInputToIsoEod(dueDate),
        customers,
        assignee_user_ids:
          canTeamWorklist &&
          assigneeMode === "users" &&
          assigneeUserIds.length > 0
            ? assigneeUserIds
            : canTeamWorklist && assigneeMode === "users"
              ? []
              : undefined,
        assignee_group_ids:
          canAssignGroups && assigneeMode === "groups"
            ? assigneeGroupIds
            : canAssignGroups && assigneeMode === "users"
              ? []
              : undefined,
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
        setTeamAssigneePicker([]);
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
      >
        <div className="cm-my-day-toolbar">
          {canTeamWorklist ? (
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
          {canTeamWorklist && workScope === "team" ? (
            <div className="cm-my-day-toolbar__filter">
              <UserDirectoryPicker
                value={teamAssigneePicker}
                onChange={(users) => {
                  setTeamAssigneePicker(users);
                  setTeamAssigneeFilter(users[0]?.id?.trim() ?? "");
                }}
                searchUsers={searchDirectoryUsers}
                maxSelected={1}
                showEmail
                renderOptionLeading={(user) => (
                  <TaskUserChipAvatar
                    userId={user.id}
                    name={(user.name || "").trim() || user.email}
                  />
                )}
                renderSelectedChip={({ user, label, disabled, onRemove }) => (
                  <span className="delpi-ui-tag-chip">
                    <TaskUserChipAvatar
                      userId={user.id}
                      name={(user.name || "").trim() || user.email}
                    />
                    <span>{label}</span>
                    <button
                      type="button"
                      className="delpi-ui-tag-chip__remove"
                      disabled={disabled}
                      aria-label={`Remover ${label}`}
                      onClick={onRemove}
                    >
                      <X size={14} aria-hidden="true" />
                    </button>
                  </span>
                )}
                labels={{
                  title: "Responsável",
                  hint: CM_HELP.myDay.teamAssigneeFilter,
                  placeholder: "Buscar usuário… (vazio = toda a equipe)",
                }}
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
      </CommercialPageHero>

      <CommercialSectionCard
        title="Fila"
        subtitle="Atrasadas → hoje → depois → concluídas."
        hint={CM_HELP.myDay.worklist}
        actions={
          <div className="cm-my-day-queue-actions">
            {canManageFollowups ? (
              <CommercialActionButton variant="primary" onClick={openCreateForm}>
                Nova tarefa
              </CommercialActionButton>
            ) : null}
            <CommercialActionButton variant="ghost" onClick={() => void reload()}>
              Atualizar
            </CommercialActionButton>
          </div>
        }
      >
        {loading ? <CommercialLoadingCard title="Carregando worklist…" variant="panel" /> : null}
        {error ? (
          <CommercialEmptyState message={error} role="alert" />
        ) : null}

        {!loading && !error ? (
          <CommercialViewTransition
            transitionKey={`scope-${workScope}-${teamAssigneeFilter}-bucket-${bucket}-${typeFilter}`}
            tone="panel"
          >
            {items.length === 0 ? (
              <CommercialEmptyState
                title={
                  typeFilter === "all"
                    ? `Nenhuma em ${BUCKET_META[bucket].label.toLowerCase()}`
                    : `Nenhuma ${TYPE_LABELS[typeFilter] ?? typeFilter} em ${BUCKET_META[bucket].label.toLowerCase()}`
                }
                message={
                  typeFilter === "all"
                    ? BUCKET_META[bucket].emptyHint
                    : "Tente outro tipo ou crie uma tarefa com este tipo."
                }
              >
                {canManageFollowups && bucket !== "done" ? (
                  <CommercialActionButton variant="primary" onClick={openCreateForm}>
                    Nova tarefa
                  </CommercialActionButton>
                ) : null}
              </CommercialEmptyState>
            ) : (
              <div className="cm-my-day-list" aria-label={`Tarefas: ${BUCKET_META[bucket].label}`}>
                {items.map((task) => {
                  const typeLabel = TYPE_LABELS[task.task_type] ?? task.task_type;
                  const priorityLabel =
                    PRIORITY_LABELS[task.priority] ?? task.priority;
                  const assigneeIds =
                    task.assignee_user_ids?.length
                      ? task.assignee_user_ids
                      : task.assignee_user_id
                        ? [task.assignee_user_id]
                        : [];
                  const assigneeValue =
                    assigneeIds.length > 0 ? (
                      <div
                        className="cm-task-link-chips"
                        role="group"
                        aria-label="Responsáveis da tarefa"
                      >
                        {assigneeIds.map((uid) => {
                          const fallback =
                            sellerNameByUserId.get(uid) ?? directoryLabelFor(uid);
                          return (
                            <TaskUserLinkChip
                              key={uid}
                              userId={uid}
                              fallbackLabel={fallback}
                              href={
                                buildUserProfileHref(uid, {
                                  basePath,
                                  returnNav: currentReturnNav("Minhas tarefas"),
                                }) ?? `${basePath}/users/${encodeURIComponent(uid)}`
                              }
                              title={profileLinkTitle(fallback)}
                              onNavigate={() =>
                                navigateUserProfile(uid, {
                                  basePath,
                                  returnNav: currentReturnNav("Minhas tarefas"),
                                })
                              }
                            />
                          );
                        })}
                      </div>
                    ) : null;
                  const taskGroups =
                    task.assignee_groups?.length
                      ? task.assignee_groups
                      : (task.assignee_group_ids ?? []).map((id) => ({
                          id,
                          kind: "",
                          name: "",
                        }));
                  const groupsValue =
                    taskGroups.length > 0 ? (
                      <div
                        className="cm-task-link-chips"
                        role="group"
                        aria-label="Grupos da tarefa"
                      >
                        {taskGroups.map((group) => (
                          <CommercialStatusBadge
                            key={group.id}
                            label={group.name || group.kind || "Grupo"}
                            variant="info"
                          />
                        ))}
                      </div>
                    ) : null;
                  const completedBy = (task.completed_by_user_id || "").trim();
                  const completedByValue =
                    completedBy ? (
                      <div
                        className="cm-task-link-chips"
                        role="group"
                        aria-label="Concluída por"
                      >
                        <TaskUserLinkChip
                          userId={completedBy}
                          fallbackLabel={
                            sellerNameByUserId.get(completedBy) ??
                            directoryLabelFor(completedBy)
                          }
                          href={
                            buildUserProfileHref(completedBy, {
                              basePath,
                              returnNav: currentReturnNav("Minhas tarefas"),
                            }) ?? `${basePath}/users/${encodeURIComponent(completedBy)}`
                          }
                          title={profileLinkTitle(
                            sellerNameByUserId.get(completedBy) ??
                              directoryLabelFor(completedBy),
                          )}
                          onNavigate={() =>
                            navigateUserProfile(completedBy, {
                              basePath,
                              returnNav: currentReturnNav("Minhas tarefas"),
                            })
                          }
                        />
                      </div>
                    ) : null;
                  const createdBy = (task.created_by_user_id || "").trim();
                  const primaryAssignee = (assigneeIds[0] || "").trim();
                  const me = (currentUserId || myPortfolio?.user_id || "").trim();
                  const assignedByFallback = createdBy
                    ? sellerNameByUserId.get(createdBy) ??
                      directoryLabelFor(createdBy)
                    : "";
                  const assignedByValue =
                    createdBy && createdBy !== primaryAssignee ? (
                      <div
                        className="cm-task-link-chips"
                        role="group"
                        aria-label="Atribuído por"
                      >
                        <TaskUserLinkChip
                          userId={createdBy}
                          fallbackLabel={assignedByFallback}
                          href={
                            buildUserProfileHref(createdBy, {
                              basePath,
                              returnNav: currentReturnNav("Minhas tarefas"),
                            }) ?? `${basePath}/users/${encodeURIComponent(createdBy)}`
                          }
                          title={profileLinkTitle(assignedByFallback)}
                          onNavigate={() =>
                            navigateUserProfile(createdBy, {
                              basePath,
                              returnNav: currentReturnNav("Minhas tarefas"),
                            })
                          }
                        />
                      </div>
                    ) : null;
                  const taskCustomers =
                    task.customers?.length
                      ? task.customers
                      : task.customer_code && task.customer_store
                        ? [
                            {
                              customer_code: task.customer_code,
                              customer_store: task.customer_store,
                              customer_name: task.customer_name,
                            },
                          ]
                        : [];
                  const customerValue =
                    taskCustomers.length > 0 ? (
                      <TaskEntityLinkChips
                        ariaLabel="Clientes da tarefa"
                        items={taskCustomers.map((item) => {
                          const name = (item.customer_name || "").trim();
                          const codeStore = `${item.customer_code}/${item.customer_store}`;
                          const accountHref =
                            buildCustomerDetailHref(
                              item.customer_code,
                              item.customer_store,
                              {
                                basePath,
                                section: "contatos",
                                search: "",
                                returnNav: currentReturnNav("Minhas tarefas"),
                              },
                            ) ?? "";
                          return {
                            key: `${item.customer_code}:${item.customer_store}`,
                            label: name || codeStore,
                            subtitle: name ? codeStore : undefined,
                            avatar: (
                              <CustomerAvatar
                                code={item.customer_code}
                                store={item.customer_store}
                                name={name || codeStore}
                                size="sm"
                                previewable={false}
                              />
                            ),
                            href: accountHref,
                            title: accountLinkTitle(name || codeStore),
                            onNavigate: () =>
                              navigateCustomerDetail(
                                item.customer_code,
                                item.customer_store,
                                {
                                  basePath,
                                  section: "contatos",
                                  search: "",
                                  returnNav: currentReturnNav("Minhas tarefas"),
                                },
                              ),
                          };
                        })}
                      />
                    ) : null;
                  const readOnly = bucket === "done";
                  const isCreator = Boolean(me) && createdBy === me;
                  const canEditTask = !readOnly && canManageFollowups && isCreator;
                  const primaryCustomer = taskCustomers[0];
                  return (
                    <TaskDetailCard
                      key={task.id}
                      task={task}
                      tone={toneForBucket(bucket)}
                      typeLabel={typeLabel}
                      priorityLabel={priorityLabel}
                      assigneeValue={assigneeValue}
                      assignedByValue={assignedByValue}
                      completedByValue={completedByValue}
                      groupsValue={groupsValue}
                      customerValue={customerValue}
                      canManage={canManageFollowups}
                      canEdit={canEditTask}
                      canDelete={canEditTask}
                      canDefer={canEditTask}
                      readOnly={readOnly}
                      formatDue={formatDue}
                      onEdit={() => openEditForm(task)}
                      onDelete={() => void onDelete(task)}
                      onComplete={() => void onComplete(task.id)}
                      onDefer={() => void onDefer(task)}
                      onOpenAccount={
                        primaryCustomer
                          ? () =>
                              navigateCustomerDetail(
                                primaryCustomer.customer_code,
                                primaryCustomer.customer_store,
                                { basePath, section: "contatos", search: "" },
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
      </CommercialSectionCard>

      {canManageFollowups && formMode !== "closed" ? (
        <div ref={taskFormRef} className="cm-my-day-create">
          <CommercialSectionCard
            title={formMode === "edit" ? "Editar tarefa" : "Nova tarefa"}
            subtitle={
              formMode === "edit"
                ? canTeamWorklist
                  ? "Altere campos, responsável e anexos; salve para gravar."
                  : "Altere campos e anexos; salve para gravar."
                : canTeamWorklist
                  ? "Título, prazo, tipo, responsável, cliente, observação e anexos."
                  : "Título, prazo, tipo, cliente, observação e anexos — padrão HubSpot/Pipedrive."
            }
            hint={formMode === "edit" ? CM_HELP.myDay.editTask : CM_HELP.myDay.newTask}
            
            
            collapsible
            open
            onOpenChange={(next) => {
              if (!next) closeTaskForm();
            }}
            actions={
              <CommercialActionButton variant="ghost" onClick={closeTaskForm}>
                Fechar
              </CommercialActionButton>
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
              {canTeamWorklist || canAssignGroups ? (
                <div className="cm-my-day-form__assignee-xor">
                  {canTeamWorklist && canAssignGroups ? (
                    <CommercialSegmentToggle
                      size="sm"
                      ariaLabel={CM_HELP.myDay.taskAssigneeXor}
                      idPrefix="my-day-assignee-mode"
                      value={assigneeMode}
                      onChange={(next) => {
                        const mode = next === "groups" ? "groups" : "users";
                        setAssigneeMode(mode);
                        if (mode === "users") setAssigneeGroupIds([]);
                        else setAssigneePicker([]);
                      }}
                      options={[
                        { value: "users", label: "Usuários" },
                        { value: "groups", label: "Grupos" },
                      ]}
                    />
                  ) : null}
                  {canTeamWorklist && assigneeMode === "users" ? (
                    <UserDirectoryPicker
                      value={assigneePicker}
                      onChange={setAssigneePicker}
                      searchUsers={searchDirectoryUsers}
                      maxSelected={20}
                      showEmail
                      renderOptionLeading={(user) => (
                        <TaskUserChipAvatar
                          userId={user.id}
                          name={(user.name || "").trim() || user.email}
                        />
                      )}
                      renderSelectedChip={({ user, label, disabled, onRemove }) => (
                        <span className="delpi-ui-tag-chip">
                          <TaskUserChipAvatar
                            userId={user.id}
                            name={(user.name || "").trim() || user.email}
                          />
                          <span>{label}</span>
                          <button
                            type="button"
                            className="delpi-ui-tag-chip__remove"
                            disabled={disabled}
                            aria-label={`Remover ${label}`}
                            onClick={onRemove}
                          >
                            <X size={14} aria-hidden="true" />
                          </button>
                        </span>
                      )}
                      labels={{
                        title: "Responsáveis",
                        hint: CM_HELP.myDay.taskAssignee,
                        placeholder:
                          formMode === "edit"
                            ? "Buscar usuários…"
                            : "Buscar usuários… (vazio = eu)",
                      }}
                    />
                  ) : null}
                  {canAssignGroups && assigneeMode === "groups" ? (
                    <CommercialMultiSelectField
                      id="my-day-task-groups"
                      label="Grupos"
                      hint={CM_HELP.myDay.taskGroups}
                      selectedValues={assigneeGroupIds}
                      onChange={setAssigneeGroupIds}
                      options={groupOptions.map((group) => ({
                        value: group.id,
                        label: group.name || group.kind || group.id,
                      }))}
                      searchable
                    />
                  ) : null}
                </div>
              ) : null}
              <CustomerSearchPicker
                value={customerSelection}
                onChange={setCustomerSelection}
                maxSelected={20}
                renderOptionLeading={(hit) => (
                  <CustomerAvatar
                    code={hit.code}
                    store={hit.store}
                    name={(hit.name || "").trim() || hit.code}
                    size="sm"
                  />
                )}
                renderSelectedChip={({ item, label, disabled, onRemove }) => (
                  <span className="delpi-ui-tag-chip">
                    <CustomerAvatar
                      code={item.code}
                      store={item.store}
                      name={(item.name || "").trim() || item.code}
                      size="sm"
                    />
                    <span>{label}</span>
                    <button
                      type="button"
                      className="delpi-ui-tag-chip__remove"
                      disabled={disabled}
                      aria-label={`Remover ${label}`}
                      onClick={onRemove}
                    >
                      <X size={14} aria-hidden="true" />
                    </button>
                  </span>
                )}
                labels={{
                  title: "Clientes",
                  hint: CM_HELP.myDay.taskCustomer,
                  placeholder: "Código ou nome (opcional)",
                }}
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
                  <CommercialAttachmentPreviewStrip
                    mode="manage"
                    items={pendingAttachments.map((item) => ({
                      id: item.id,
                      fileName: item.file.name,
                      contentType: item.file.type,
                      detail:
                        item.file.size < 1024
                          ? `${item.file.size} B`
                          : item.file.size < 1024 * 1024
                            ? `${(item.file.size / 1024).toFixed(1)} KB`
                            : `${(item.file.size / (1024 * 1024)).toFixed(1)} MB`,
                      previewUrl: pendingThumbUrls[item.id] ?? null,
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
                <CommercialActionButton variant="ghost" onClick={closeTaskForm}>
                  Cancelar
                </CommercialActionButton>
                {formMode === "edit" ? (
                  <CommercialActionButton
                    variant="primary"
                    disabled={savingEdit}
                    onClick={() => void onSaveEdit()}
                  >
                    {savingEdit ? "Salvando…" : "Salvar alterações"}
                  </CommercialActionButton>
                ) : (
                  <CommercialActionButton
                    variant="primary"
                    disabled={creating}
                    onClick={() => void onCreate()}
                  >
                    {creating ? "Criando…" : "Criar tarefa"}
                  </CommercialActionButton>
                )}
              </div>
            </div>
          </CommercialSectionCard>
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
