import { Activity, FileText, Info } from "lucide-react";
import type { ReactNode } from "react";

export type ConversationContextPanelProps = {
  /** Host-authorized, read-only projections; omit until contract/data exist. */
  details?: ReactNode;
  evidence?: ReactNode;
  activities?: ReactNode;
};

/** Context chrome only; no evidence inference, tool invocation or authorization. */
export function ConversationContextPanel({
  details,
  evidence,
  activities,
}: ConversationContextPanelProps) {
  const sections = [
    { id: "details", title: "Detalhes", icon: Info, content: details, empty: "Nenhum detalhe adicional disponível." },
    { id: "evidence", title: "Evidências", icon: FileText, content: evidence, empty: "Nenhuma evidência adicional disponível nesta seleção." },
    { id: "activities", title: "Atividades", icon: Activity, content: activities, empty: "Nenhuma atividade adicional disponível nesta seleção." },
  ];
  return (
    <div className="delpi-ui-conversation-context-panel">
      {sections.map(({ id, title, icon: Icon, content, empty }) => (
        <section className="delpi-ui-conversation-context-panel__section" key={id} aria-label={title}>
          <h2 className="delpi-ui-conversation-context-panel__heading">
            <Icon size={17} aria-hidden="true" /><span>{title}</span>
          </h2>
          {content ?? <p className="delpi-ui-conversation-context-panel__empty">{empty}</p>}
        </section>
      ))}
    </div>
  );
}
