import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  ScopeChipBar,
  TaskEditorFrame,
  TaskEmptyState,
  TaskItemsTable,
  TaskSearchField,
  TaskWorkspacePage,
  UserDirectoryPicker,
  buildTaskWorkspaceHighlights,
  scopeChipBarBemClasses,
  type DirectoryUserOption,
  type TaskItemPresentation,
} from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import { TmNativeTextAreaField, TmNativeTextField } from "../../components/ui/tmNativeFormFields";
import { PORTAL_PAGE_COPY } from "../../constants/portalExperience";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import { fetchMeProfile } from "../../data/api/meApi";
import { searchDirectoryUsers } from "../../data/api/transformometroMeetingMinutesApi";
import {
  cancelTask,
  completeTask,
  createTask,
  getTask,
  listMyTaskItems,
  updateTask,
  type MyTaskItemDto,
  type MyTaskItemsResponse,
} from "../../data/api/transformometroTasksApi";
import { toTaskItemPresentation } from "./myTaskPresentation";

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
};

type FilterId = "pending" | "completed" | "all";
type FormMode = "closed" | "create" | "edit";

const CHIPS = scopeChipBarBemClasses("ds");

export function MyTasksPage({ getAccessToken, pathname, onNavigate }: Props) {
  const confirm = useConfirm();
  const [payload, setPayload] = useState<MyTaskItemsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reloadNonce, setReloadNonce] = useState(0);
  const [filter, setFilter] = useState<FilterId>("pending");
  const [formMode, setFormMode] = useState<FormMode>("closed");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [assignee, setAssignee] = useState<DirectoryUserOption[]>([]);
  const [me, setMe] = useState<DirectoryUserOption | null>(null);
  const [saving, setSaving] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    void fetchMeProfile(getAccessToken)
      .then((profile) => {
        if (!profile.id) return;
        const self = { id: profile.id, name: profile.name || "Eu", email: "" };
        setMe(self);
        setAssignee((current) => (current.length ? current : [self]));
      })
      .catch(() => undefined);
  }, [getAccessToken]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const next = await listMyTaskItems(getAccessToken, filter);
      setPayload(next);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível carregar suas tarefas.");
    } finally {
      setLoading(false);
    }
  }, [filter, getAccessToken]);

  useEffect(() => {
    void load();
  }, [load, reloadNonce]);

  const refreshing = Boolean(payload) && loading;
  const items = payload?.items ?? [];
  const rows = useMemo(() => {
    const mapped = items.map((item) =>
      toTaskItemPresentation(
        item,
        item.assignee_user_id && me?.id === item.assignee_user_id ? me.name : null,
      ),
    );
    const needle = query.trim().toLowerCase();
    if (!needle) return mapped;
    return mapped.filter((row) =>
      [row.title, row.description, row.sourceLabel, row.contextLabel]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle)),
    );
  }, [items, me, query]);
  const highlights = buildTaskWorkspaceHighlights(payload?.summary ?? { pending: 0 }, {
    loading: refreshing || (loading && !payload),
    includeDueBuckets: true,
  });

  function openCreate() {
    setFormMode("create");
    setEditingId(null);
    setTitle("");
    setDescription("");
    setDueDate("");
    setAssignee(me ? [me] : []);
  }

  function openEdit(item: TaskItemPresentation) {
    const source = items.find((row) => row.id === item.id);
    if (!source || source.type !== "manual_task") return;
    setFormMode("edit");
    setEditingId(source.source_id);
    setTitle(source.title);
    setDescription(source.description ?? "");
    setDueDate(source.due_date ?? "");
    setAssignee(
      source.assignee_user_id
        ? [{ id: source.assignee_user_id, name: me?.name || "Responsável", email: "" }]
        : me
          ? [me]
          : [],
    );
  }

  function closeForm() {
    setFormMode("closed");
    setEditingId(null);
  }

  const reviewRows = [
    { label: "Título", value: title.trim() || "—" },
    { label: "Responsável", value: assignee[0]?.name || "—" },
    { label: "Prazo", value: dueDate || "Sem prazo" },
    { label: "Descrição", value: description.trim() || "—" },
  ];

  async function submit() {
    if (!title.trim()) return;
    const assigneeId = assignee[0]?.id || me?.id || "";
    const confirmed = await confirm({
      title: formMode === "edit" ? "Salvar tarefa?" : "Criar tarefa?",
      message: `${title.trim()} · ${assignee[0]?.name || "você"} · ${dueDate || "sem prazo"}`,
      confirmLabel: formMode === "edit" ? "Salvar" : "Criar tarefa",
    });
    if (!confirmed) return;
    setSaving(true);
    try {
      const payloadWrite = {
        title: title.trim(),
        description: description.trim() || null,
        assignee_user_id: assigneeId || null,
        due_date: dueDate || null,
      };
      const saved =
        formMode === "edit" && editingId
          ? await updateTask(editingId, payloadWrite, getAccessToken)
          : await createTask(payloadWrite, getAccessToken);
      const readBack = await getTask(saved.id, getAccessToken);
      if (readBack.title !== payloadWrite.title || readBack.assignee_user_id !== (assigneeId || readBack.assignee_user_id)) {
        throw new Error("A gravação não confirmou o estado esperado.");
      }
      closeForm();
      setReloadNonce((nonce) => nonce + 1);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível gravar a tarefa.");
    } finally {
      setSaving(false);
    }
  }

  async function onComplete(item: TaskItemPresentation) {
    const source = items.find((row) => row.id === item.id);
    if (!source || source.type !== "manual_task") return;
    const confirmed = await confirm({
      title: "Concluir tarefa?",
      message: source.title,
      confirmLabel: "Concluir",
    });
    if (!confirmed) return;
    try {
      const done = await completeTask(source.source_id, getAccessToken);
      if (done.status !== "completed") throw new Error("A conclusão não foi confirmada.");
      setReloadNonce((nonce) => nonce + 1);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível concluir a tarefa.");
    }
  }

  async function onCancel(item: TaskItemPresentation) {
    const source = items.find((row) => row.id === item.id);
    if (!source || source.type !== "manual_task") return;
    const confirmed = await confirm({
      title: "Cancelar tarefa?",
      message: source.title,
      confirmLabel: "Cancelar tarefa",
    });
    if (!confirmed) return;
    try {
      const cancelled = await cancelTask(source.source_id, getAccessToken);
      if (cancelled.status !== "cancelled") throw new Error("O cancelamento não foi confirmado.");
      setReloadNonce((nonce) => nonce + 1);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível cancelar a tarefa.");
    }
  }

  function onOpen(item: TaskItemPresentation) {
    if (item.route) onNavigate(item.route);
  }

  const hero = (
    <PageHeader
      eyebrow={PORTAL_PAGE_COPY.myTasks.eyebrow}
      title={PORTAL_PAGE_COPY.myTasks.title}
      subtitle={PORTAL_PAGE_COPY.myTasks.description}
      currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.myTasks}
      onNavigate={onNavigate}
      refreshing={refreshing}
      highlights={highlights}
    >
      <ScopeChipBar
        classNames={CHIPS}
        aria-label="Filtro de tarefas"
        chips={[
          { id: "pending", label: "Pendentes", active: filter === "pending", onSelect: () => setFilter("pending") },
          { id: "completed", label: "Concluídas", active: filter === "completed", onSelect: () => setFilter("completed") },
          { id: "all", label: "Todas", active: filter === "all", onSelect: () => setFilter("all") },
        ]}
      />
    </PageHeader>
  );

  return (
    <TransformometroShell>
      <TaskWorkspacePage
        hero={hero}
        initialLoading={
          loading && !payload ? (
            <LoadingActivityCard
              title="Carregando suas tarefas"
              description="Buscando tarefas do portal e assinaturas pendentes."
            />
          ) : undefined
        }
        refreshing={refreshing}
        partialError={payload?.partial_error ? <p>{payload.partial_error}</p> : null}
        error={
          error ? (
            <p>
              {error}{" "}
              <button type="button" onClick={() => setReloadNonce((nonce) => nonce + 1)}>
                Tentar de novo
              </button>
            </p>
          ) : null
        }
        worklist={{
          title: "Fila",
          subtitle: "Pendentes, concluídas e assinaturas de ata.",
          actions: (
            <>
              <ActionButton variant="primary" onClick={openCreate}>
                Nova tarefa
              </ActionButton>
              <ActionButton variant="ghost" onClick={() => setReloadNonce((nonce) => nonce + 1)}>
                {refreshing ? "Atualizando…" : "Atualizar"}
              </ActionButton>
            </>
          ),
          search: (
            <TaskSearchField
              id="tm-task-search"
              value={query}
              onChange={setQuery}
              placeholder="Buscar tarefas..."
              aria-label="Buscar tarefas"
            />
          ),
        }}
        editor={
          formMode !== "closed" ? (
            <TaskEditorFrame
              title={formMode === "edit" ? "Editar tarefa" : "Nova tarefa"}
              subtitle="A tarefa fica no Portal Transforma+. Assinatura de ata continua na própria ata."
              reviewRows={reviewRows}
              onClose={closeForm}
              primaryLabel={formMode === "edit" ? "Salvar alterações" : "Criar tarefa"}
              onPrimary={() => void submit()}
              primaryBusy={saving}
              primaryDisabled={!title.trim()}
            >
              <TmNativeTextField id="tm-task-title" label="Título" value={title} onChange={setTitle} required span />
              <TmNativeTextAreaField
                id="tm-task-description"
                label="Descrição"
                value={description}
                onChange={setDescription}
                span
              />
              <TmNativeTextField id="tm-task-due" label="Prazo" type="date" value={dueDate} onChange={setDueDate} />
              <UserDirectoryPicker
                value={assignee}
                onChange={setAssignee}
                searchUsers={(query, limit, signal) => searchDirectoryUsers(query, limit, signal, getAccessToken)}
                maxSelected={1}
                labels={{ title: "Responsável", placeholder: "Atribuir a mim ou buscar…" }}
              />
            </TaskEditorFrame>
          ) : null
        }
      >
        {rows.length === 0 && !error ? (
          <TaskEmptyState
            title={
              query.trim()
                ? "Nenhuma tarefa corresponde à busca"
                : filter === "completed"
                  ? "Nenhuma tarefa concluída"
                  : filter === "all"
                    ? "Nenhuma tarefa nesta lista"
                    : "Nenhuma tarefa pendente"
            }
            message={
              query.trim()
                ? "Ajuste o texto ou limpe a busca para ver o restante da fila."
                : filter === "completed"
                  ? "Nenhuma tarefa concluída."
                  : filter === "all"
                    ? "Nenhuma tarefa nesta lista."
                    : "Nenhuma tarefa pendente no momento."
            }
          >
            {!query.trim() ? (
              <ActionButton variant="primary" onClick={openCreate}>
                Nova tarefa
              </ActionButton>
            ) : null}
          </TaskEmptyState>
        ) : (
          <TaskItemsTable
            items={rows}
            refreshing={refreshing}
            onOpen={onOpen}
            onEdit={openEdit}
            onComplete={(item) => void onComplete(item)}
            onCancel={(item) => void onCancel(item)}
          />
        )}
      </TaskWorkspacePage>
    </TransformometroShell>
  );
}

export type { MyTaskItemDto };
