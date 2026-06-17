import type { ChatAgent } from "../../../data/api/chatTypes";
import { resolveAgentIcebreakersForDisplay } from "../../agentIcebreakers";

import { ChatAgentLanding } from "./ChatAgentLanding";

import "./ChatAgentHome.css";

type ChatAgentHomeProps = {
  agent: ChatAgent;
  onUseSuggestion: (value: string) => void;
  canManageAgent?: boolean;
  onManageAgent?: () => void;
  defaultIcebreakersHint?: string | null;
};

export function ChatAgentHome({
  agent,
  onUseSuggestion,
  canManageAgent = false,
  onManageAgent,
  defaultIcebreakersHint,
}: ChatAgentHomeProps) {
  return (
    <ChatAgentLanding
      className="mdc-chat-agent-home"
      name={agent.name}
      description={agent.description}
      icebreakers={resolveAgentIcebreakersForDisplay(agent.metadata)}
      onIcebreakerClick={onUseSuggestion}
      canManageAgent={canManageAgent}
      onManageAgent={onManageAgent}
      defaultIcebreakersHint={defaultIcebreakersHint}
    />
  );
}
