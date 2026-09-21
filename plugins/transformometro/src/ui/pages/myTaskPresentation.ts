import type { TaskItemPresentation } from "@delpi/plugin-ui/index";

import type { MyTaskItemDto } from "../../data/api/transformometroTasksApi";

export function toTaskItemPresentation(
  item: MyTaskItemDto,
  assigneeLabel?: string | null,
): TaskItemPresentation {
  return {
    id: item.id,
    title: item.title,
    description: item.description,
    sourceLabel: item.source_label,
    statusLabel: item.status_label,
    statusTone: item.status === "completed" ? "success" : item.overdue ? "danger" : "info",
    assigneeLabel: assigneeLabel ?? null,
    dueDateLabel: item.due_date_label,
    contextLabel: item.context_label,
    overdue: item.overdue,
    route: item.route,
    actions: {
      canOpen: item.actions?.can_open,
      canEdit: item.actions?.can_edit,
      canComplete: item.actions?.can_complete,
      canCancel: item.actions?.can_cancel,
    },
  };
}
