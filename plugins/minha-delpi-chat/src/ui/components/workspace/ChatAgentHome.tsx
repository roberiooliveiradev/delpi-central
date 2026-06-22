import type { ChatAgent } from "../../../data/api/chatTypes";
import {
  resolveAgentIcebreakerEntries,
  type AgentIcebreakerEntry,
} from "../../agentIcebreakers";

import { ChatAgentLanding } from "./ChatAgentLanding";

import "./ChatAgentHome.css";

type ChatAgentHomeProps = {
  agent: ChatAgent;
  onUseSuggestion: (entry: AgentIcebreakerEntry) => void;
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
      icon={agent.icon}
      description={agent.description}
      icebreakerEntries={resolveAgentIcebreakerEntries(agent.metadata)}
      onIcebreakerClick={onUseSuggestion}
      canManageAgent={canManageAgent}
      onManageAgent={onManageAgent}
      defaultIcebreakersHint={defaultIcebreakersHint}
    />
  );
}
