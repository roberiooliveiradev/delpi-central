import { ArrowLeft } from "lucide-react";

import type { ChatAgent } from "../../data/api/chatTypes";
import { ChatAgentsModal } from "../components/ChatAgentsModal";

import "./ChatAgentsPage.css";

type ChatAgentsPageProps = {
  agents: ChatAgent[];
  selectedAgentKey?: string | null;
  isLoading?: boolean;
  onBack: () => void;
  onSelectAgent?: (agentKey: string | null) => void;
  onCreateAgent?: Parameters<typeof ChatAgentsModal>[0]["onCreateAgent"];
  onUpdateAgent?: Parameters<typeof ChatAgentsModal>[0]["onUpdateAgent"];
  onDeleteAgent?: Parameters<typeof ChatAgentsModal>[0]["onDeleteAgent"];
  onShareAgent?: Parameters<typeof ChatAgentsModal>[0]["onShareAgent"];
};

export function ChatAgentsPage({
  agents,
  selectedAgentKey,
  isLoading,
  onBack,
  onSelectAgent,
  onCreateAgent,
  onUpdateAgent,
  onDeleteAgent,
  onShareAgent,
}: ChatAgentsPageProps) {
  return (
    <section className="mdc-chat-agents-page" aria-label="Gerenciamento de agentes">
      <header className="mdc-chat-agents-page__header">
        <button type="button" onClick={onBack}>
          <ArrowLeft size={17} aria-hidden="true" />
          <span>Voltar ao chat</span>
        </button>

        <div>
          <p className="mdc-chat-eyebrow">Especialistas</p>
          <h1>Agentes</h1>
          <p>
            Crie especialistas com instruções, comportamento e permissões próprias.
          </p>
        </div>
      </header>

      <ChatAgentsModal
        open
        agents={agents}
        selectedAgentKey={selectedAgentKey}
        isLoading={isLoading}
        onClose={onBack}
        onSelectAgent={onSelectAgent}
        onCreateAgent={onCreateAgent}
        onUpdateAgent={onUpdateAgent}
        onDeleteAgent={onDeleteAgent}
        onShareAgent={onShareAgent}
      />
    </section>
  );
}
