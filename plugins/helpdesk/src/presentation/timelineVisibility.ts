/** Client-side timeline visibility — only kinds the BFF actually publishes. */

export type TimelineVisibilityKind =
  | "description"
  | "followups"
  | "tasks"
  | "documents"
  | "approvals"
  | "solutions";

export type TimelineVisibilityState = Record<TimelineVisibilityKind, boolean>;

export const DEFAULT_TIMELINE_VISIBILITY: TimelineVisibilityState = {
  description: true,
  followups: true,
  tasks: true,
  documents: true,
  approvals: true,
  solutions: true,
};

export const TIMELINE_VISIBILITY_OPTIONS: {
  id: TimelineVisibilityKind;
  label: string;
  variant: string;
}[] = [
  { id: "description", label: "Descrição", variant: "description" },
  { id: "followups", label: "Acompanhamentos", variant: "reply" },
  { id: "tasks", label: "Tarefas", variant: "task" },
  { id: "documents", label: "Documentos", variant: "attachment" },
  { id: "approvals", label: "Aprovações", variant: "approval" },
  { id: "solutions", label: "Soluções", variant: "solution" },
];

export function conversationMessageVisible(
  kind: "opening" | "followup" | "solution" | "task",
  visibility: TimelineVisibilityState,
): boolean {
  if (kind === "opening") return visibility.description;
  if (kind === "followup") return visibility.followups;
  if (kind === "task") return visibility.tasks;
  if (kind === "solution") return visibility.solutions;
  return true;
}

export function ticketTasksFromTimeline(
  timeline: readonly { id: number; kind: string; content: string; created_at: string; author_display_name: string }[],
): { id: number; content: string; created_at: string; author: string }[] {
  return timeline
    .filter((entry) => entry.kind === "task")
    .map((entry) => ({
      id: entry.id,
      content: entry.content,
      created_at: entry.created_at,
      author: entry.author_display_name,
    }));
}
