import { ActionButton, StatusBadge } from "@delpi/plugin-ui/index";

import type { CommercialTaskDto } from "../../api/worklistApi";
import { CM_HELP } from "../../content/helpTooltips";
import {
  cmStatusBadgeClassNames,
  CommercialDetailCard,
  CommercialDetailFieldGrid,
} from "../../app/commercialUi";
import { TaskAttachmentsBlock } from "./TaskAttachmentsBlock";

type TaskDetailCardProps = {
  task: CommercialTaskDto;
  tone: "danger" | "warning" | "neutral" | "success";
  typeLabel: string;
  priorityLabel: string;
  assigneeLabel?: string | null;
  /** Quem criou/atribuiu — exibido quando diferente do responsável. */
  assignedByLabel?: string | null;
  canManage: boolean;
  /** Criador, responsável ou gestor — edita conteúdo/anexos. */
  canEdit: boolean;
  /** Mesmo critério de edição (apenas tarefas abertas). */
  canDelete?: boolean;
  /** Concluídas: só leitura (sem Editar / Adiar / Concluir). */
  readOnly?: boolean;
  onEdit: () => void;
  onDelete?: () => void;
  onComplete: () => void;
  onDefer: () => void;
  onOpenAccount?: () => void;
  onAttachmentsChanged: () => void;
  notifyError: (message: string) => void;
  notifySuccess: (message: string) => void;
  formatDue: (dueAt?: string | null) => string;
  formatCompleted?: (completedAt?: string | null) => string;
};

function toneBadge(tone: TaskDetailCardProps["tone"]): {
  label: string;
  variant: "danger" | "warning" | "info" | "success";
} {
  if (tone === "danger") return { label: "Atrasada", variant: "danger" };
  if (tone === "warning") return { label: "Hoje", variant: "warning" };
  if (tone === "success") return { label: "Concluída", variant: "success" };
  return { label: "Depois", variant: "info" };
}

export function TaskDetailCard({
  task,
  tone,
  typeLabel,
  priorityLabel,
  assigneeLabel,
  assignedByLabel,
  canManage,
  canEdit,
  canDelete = false,
  readOnly = false,
  onEdit,
  onDelete,
  onComplete,
  onDefer,
  onOpenAccount,
  onAttachmentsChanged,
  notifyError,
  notifySuccess,
  formatDue,
  formatCompleted,
}: TaskDetailCardProps) {
  const note = (task.description ?? "").trim();
  const badge = toneBadge(tone);
  const attachmentCount = task.attachment_count ?? 0;
  const completedLabel =
    formatCompleted?.(task.completed_at) ??
    (task.completed_at ? formatDue(task.completed_at) : "—");

  const fields = [
    ...(readOnly
      ? [
          {
            label: "Concluída em",
            value: completedLabel,
            hint: CM_HELP.myDay.taskCompletedAt,
          },
        ]
      : []),
    { label: "Prazo", value: formatDue(task.due_at), hint: CM_HELP.myDay.taskDue },
    { label: "Prioridade", value: priorityLabel, hint: CM_HELP.myDay.taskPriority },
    { label: "Tipo", value: typeLabel, hint: CM_HELP.myDay.taskType },
    ...(assigneeLabel
      ? [{ label: "Responsável", value: assigneeLabel, hint: CM_HELP.myDay.taskAssignee }]
      : []),
    ...(assignedByLabel
      ? [
          {
            label: "Atribuído por",
            value: assignedByLabel,
            hint: CM_HELP.myDay.taskAssignedBy,
          },
        ]
      : []),
    ...(task.customer_code
      ? [
          {
            label: "Cliente",
            value: `${task.customer_code}/${task.customer_store ?? ""}`,
            hint: CM_HELP.myDay.taskCustomer,
          },
        ]
      : []),
    {
      label: "Observação",
      value: note || "Sem observação",
      hint: CM_HELP.myDay.taskDescription,
      wide: true as const,
    },
  ];

  const hintParts = [
    readOnly ? `Concluída ${completedLabel}` : formatDue(task.due_at),
    priorityLabel,
    typeLabel,
  ];
  if (attachmentCount > 0) {
    hintParts.push(
      `${attachmentCount} anexo${attachmentCount === 1 ? "" : "s"}`,
    );
  }

  return (
    <CommercialDetailCard
      title={task.title}
      hint={hintParts.join(" · ")}
      titleHint={CM_HELP.myDay.worklist}
      className={`cm-task-detail-card cm-task-detail-card--${tone}`}
      icon={
        <StatusBadge
          classNames={cmStatusBadgeClassNames}
          label={badge.label}
          variant={badge.variant}
        />
      }
      headerActions={
        <div className="cm-task-detail-card__actions">
          {!readOnly && canEdit ? (
            <ActionButton variant="ghost" onClick={onEdit}>
              Editar
            </ActionButton>
          ) : null}
          {!readOnly && canDelete && onDelete ? (
            <ActionButton variant="ghost" onClick={onDelete}>
              Excluir
            </ActionButton>
          ) : null}
          {!readOnly && canManage ? (
            <ActionButton variant="ghost" onClick={onDefer}>
              Adiar +1 dia
            </ActionButton>
          ) : null}
          {onOpenAccount ? (
            <ActionButton variant="ghost" onClick={onOpenAccount}>
              Abrir conta
            </ActionButton>
          ) : null}
          {!readOnly && canManage ? (
            <ActionButton variant="primary" onClick={onComplete}>
              Concluir
            </ActionButton>
          ) : null}
        </div>
      }
    >
      <div className="cm-task-detail-card__body">
        <CommercialDetailFieldGrid fields={fields} valueFallback="—" wrapLabels />
        <TaskAttachmentsBlock
          taskId={task.id}
          initialCount={attachmentCount}
          mode="preview"
          embedded
          onChanged={onAttachmentsChanged}
          notifyError={notifyError}
          notifySuccess={notifySuccess}
        />
      </div>
    </CommercialDetailCard>
  );
}
