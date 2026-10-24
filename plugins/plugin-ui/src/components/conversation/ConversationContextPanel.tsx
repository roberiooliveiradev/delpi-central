import { Activity, FileText, Info } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export type ConversationContextPanelSection = {
  id: string;
  title: string;
  icon?: LucideIcon;
  content?: ReactNode;
};

export type ConversationContextPanelProps = {
  details?: ReactNode;
  evidence?: ReactNode;
  activities?: ReactNode;
  /** Custom sections override the default message-scoped trio —
   *  pass only sections with legitimate content (empty panels show
   *  `emptyState`, never fabricated rows). */
  sections?: readonly ConversationContextPanelSection[];
  /** Copy shown when no section carries content. */
  emptyState?: ReactNode;
};

const DEFAULT_EMPTY =
  "Selecione uma mensagem para ver mais informações.";

/** Pure visual projection: never infers evidence, authorization or business outcome. */
export function ConversationContextPanel({
  details,
  evidence,
  activities,
  sections,
  emptyState = DEFAULT_EMPTY,
}: ConversationContextPanelProps) {
  const effective = sections ?? [
    { id: "details", title: "Detalhes", icon: Info, content: details },
    { id: "evidence", title: "Evidências", icon: FileText, content: evidence },
    { id: "activities", title: "Atividades", icon: Activity, content: activities },
  ];
  const hasContent = effective.some((item) => item.content != null);
  return (
    <div className="delpi-ui-conversation-context-panel">
      {effective.map(({ id, title, icon: Icon = Info, content }) => (
        <section key={id} className="delpi-ui-conversation-context-panel__section" aria-label={title}>
          <h2 className="delpi-ui-conversation-context-panel__heading">
            <Icon size={17} aria-hidden="true" /><span>{title}</span>
          </h2>
          {content != null ? <div className="delpi-ui-conversation-context-panel__body">{content}</div> : null}
        </section>
      ))}
      {!hasContent ? (
        <p className="delpi-ui-conversation-context-panel__empty">
          {emptyState}
        </p>
      ) : null}
    </div>
  );
}
