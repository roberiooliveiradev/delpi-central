import type { ReactNode } from "react";
import { ConversationThreeRegionLayout } from "@delpi/plugin-ui/index";

/**
 * Single product-level page composition. Shared layout primitives live in
 * plugin-ui; DÉLIA supplies its existing, stateful conversation workspace.
 * History/search/context APIs are deliberately not simulated.
 */
export type DeliaConversationPageProps = {
  conversation: ReactNode;
};

export function DeliaConversationPage({ conversation }: DeliaConversationPageProps) {
  return (
    <ConversationThreeRegionLayout
      left={
        <p className="delia-visually-muted">
          O histórico ficará disponível quando a persistência de conversas for integrada.
        </p>
      }
      right={
        <p className="delia-visually-muted">
          Detalhes adicionais aparecerão aqui quando houver contexto autorizado.
        </p>
      }
      center={conversation}
    />
  );
}
