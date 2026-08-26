import {
  ActionButton,
  StatusBadge,
  attachmentIdsInMarkdown,
  type MentionTextItem,
} from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { downloadAttachmentBlob } from "../../api/attachmentsApi";
import type {
  CommercialTaskDto,
  TaskSourceMessageMentionDto,
} from "../../api/worklistApi";
import { CM_HELP } from "../../content/helpTooltips";
import {
  cmStatusBadgeClassNames,
  CommercialDetailCard,
  CommercialDetailFieldGrid,
  CommercialMessageBodyReadonly,
} from "../../app/commercialUi";
import { TaskAttachmentsBlock } from "./TaskAttachmentsBlock";
import {
  TaskAttachmentPreviewModal,
  type TaskAttachmentPreviewTarget,
} from "./TaskAttachmentPreviewModal";

type TaskDetailCardProps = {
  task: CommercialTaskDto;
  tone: "danger" | "warning" | "neutral" | "success";
  typeLabel: string;
  priorityLabel: string;
  /** Texto legado ou chips com link (ReactNode). */
  assigneeValue?: ReactNode;
  /** Quem criou/atribuiu — chips com avatar quando diferente do responsável. */
  assignedByValue?: ReactNode;
  /** Quem concluiu — chip com avatar quando disponível. */
  completedByValue?: ReactNode;
  /** Grupos responsáveis (badges). */
  groupsValue?: ReactNode;
  /** Texto legado ou chips com link (ReactNode). */
  customerValue?: ReactNode;
  canManage: boolean;
  /** Só o criador edita conteúdo/anexos. */
  canEdit: boolean;
  /** Só o criador exclui. */
  canDelete?: boolean;
  /** Só o criador adia prazo. */
  canDefer?: boolean;
  /** Concluídas: só leitura (sem Editar / Adiar / Concluir). */
  readOnly?: boolean;
  onEdit: () => void;
  onDelete?: () => void;
  onComplete: () => void;
  onDefer: () => void;
  onOpenAccount?: () => void;
  onAttachmentsChanged: () => void;
  notifyError: (
    message: string,
    options?: { title?: string; id?: string; autoDismissMs?: number | null },
  ) => void;
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

function taskMentionsToKitItems(
  mentions: TaskSourceMessageMentionDto[] | undefined,
): MentionTextItem[] {
  return (mentions ?? []).map((mention) => ({
    kind: mention.mention_kind,
    label: mention.label,
    ref: mention.ref ?? undefined,
    id: mention.id,
  }));
}

export function TaskDetailCard({
  task,
  tone,
  typeLabel,
  priorityLabel,
  assigneeValue,
  assignedByValue,
  completedByValue,
  groupsValue,
  customerValue,
  canManage,
  canEdit,
  canDelete = false,
  canDefer = false,
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
  const mentionItems = useMemo(
    () => taskMentionsToKitItems(task.source_message_mentions),
    [task.source_message_mentions],
  );
  const inlineAttachmentIds = useMemo(
    () => attachmentIdsInMarkdown(note),
    [note],
  );
  const [inlineThumbUrls, setInlineThumbUrls] = useState<Record<string, string>>({});
  const [inlinePreview, setInlinePreview] = useState<TaskAttachmentPreviewTarget | null>(
    null,
  );

  useEffect(() => {
    if (inlineAttachmentIds.length === 0) {
      setInlineThumbUrls({});
      return undefined;
    }
    let cancelled = false;
    const created: string[] = [];
    void (async () => {
      const next: Record<string, string> = {};
      for (const attachmentId of inlineAttachmentIds) {
        try {
          const blob = await downloadAttachmentBlob(attachmentId);
          if (cancelled) return;
          const url = URL.createObjectURL(blob);
          created.push(url);
          next[attachmentId] = url;
        } catch {
          // preview inline opcional — anexos no rodapé permanecem
        }
      }
      if (!cancelled) setInlineThumbUrls(next);
    })();
    return () => {
      cancelled = true;
      for (const url of created) URL.revokeObjectURL(url);
    };
  }, [inlineAttachmentIds.join("|"), task.id]);

  const fields = [
    ...(readOnly
      ? [
          {
            label: "Concluída em",
            value: completedLabel,
            hint: CM_HELP.myDay.taskCompletedAt,
          },
          ...(completedByValue
            ? [
                {
                  label: "Concluída por",
                  value: completedByValue,
                  hint: CM_HELP.myDay.taskCompletedBy,
                },
              ]
            : []),
        ]
      : []),
    { label: "Prazo", value: formatDue(task.due_at), hint: CM_HELP.myDay.taskDue },
    { label: "Prioridade", value: priorityLabel, hint: CM_HELP.myDay.taskPriority },
    { label: "Tipo", value: typeLabel, hint: CM_HELP.myDay.taskType },
    ...(assigneeValue
      ? [{ label: "Responsável", value: assigneeValue, hint: CM_HELP.myDay.taskAssignee }]
      : []),
    ...(groupsValue
      ? [{ label: "Grupos", value: groupsValue, hint: CM_HELP.myDay.taskGroups }]
      : []),
    ...(assignedByValue
      ? [
          {
            label: "Atribuído por",
            value: assignedByValue,
            hint: CM_HELP.myDay.taskAssignedBy,
          },
        ]
      : []),
    ...(customerValue
      ? [
          {
            label: "Cliente",
            value: customerValue,
            hint: CM_HELP.myDay.taskCustomer,
          },
        ]
      : []),
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
    <>
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
            {!readOnly && canDefer ? (
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
          {note ? (
            <div className="cm-task-detail-card__prose">
              <CommercialMessageBodyReadonly
                markdown={note}
                mentions={mentionItems}
                resolveAttachmentImageSrc={(attachmentId) =>
                  inlineThumbUrls[attachmentId] ?? null
                }
                onAttachmentImageClick={(attachmentId) => {
                  setInlinePreview({
                    kind: "remote",
                    id: attachmentId,
                    fileName: attachmentId,
                    contentType: "image/*",
                    byteSize: 0,
                  });
                }}
              />
            </div>
          ) : null}
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
      {inlinePreview ? (
        <TaskAttachmentPreviewModal
          target={inlinePreview}
          open
          onClose={() => setInlinePreview(null)}
        />
      ) : null}
    </>
  );
}
