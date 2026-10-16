import { Activity, FileText, Info } from "lucide-react";
import type { ReactNode } from "react";

export type ConversationContextPanelProps = {
  details?: ReactNode;
  evidence?: ReactNode;
  activities?: ReactNode;
};

/** Pure visual projection: never infers evidence, authorization or business outcome. */
export function ConversationContextPanel({ details, evidence, activities }: ConversationContextPanelProps) {
  const sections = [
    { id: "details", title: "Detalhes", icon: Info, content: details },
    { id: "evidence", title: "Evidências", icon: FileText, content: evidence },
    { id: "activities", title: "Atividades", icon: Activity, content: activities },
  ];
  const hasContent = sections.some((item) => item.content != null);
  return (
    <div className="delpi-ui-conversation-context-panel">
      {sections.map(({ id, title, icon: Icon, content }) => (
        <section key={id} className="delpi-ui-conversation-context-panel__section" aria-label={title}>
          <h2 className="delpi-ui-conversation-context-panel__heading">
            <Icon size={17} aria-hidden="true" /><span>{title}</span>
          </h2>
          {content != null ? <div className="delpi-ui-conversation-context-panel__body">{content}</div> : null}
        </section>
      ))}
      {!hasContent ? (
        <p className="delpi-ui-conversation-context-panel__empty">
          Selecione uma mensagem para ver mais informações.
        </p>
      ) : null}
    </div>
  );
}
