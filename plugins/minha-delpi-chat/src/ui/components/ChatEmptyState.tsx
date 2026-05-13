import {
  Bot,
  Database,
  FileSearch,
  MessageSquarePlus,
  Route,
  Sparkles,
} from "lucide-react";

import type { ChatAgent } from "../../data/api/chatTypes";

import "./ChatEmptyState.css";

type ChatEmptyStateProps = {
  agent?: ChatAgent | null;
  onUseSuggestion: (value: string) => void;
};

const defaultSuggestions = [
  {
    icon: Database,
    title: "Consultar produto",
    prompt: "Busque as informações do produto 10080022 usando a API DELPI",
  },
  {
    icon: Route,
    title: "Ver meus acessos",
    prompt: "Quais aplicativos e rotas eu tenho acesso?",
  },
  {
    icon: FileSearch,
    title: "Buscar conhecimento",
    prompt: "O que é a Minha DELPI?",
  },
  {
    icon: MessageSquarePlus,
    title: "Consultar LMP",
    prompt: "Liste as LMPs recentes disponíveis para mim",
  },
];

function getAgentIcebreakers(agent?: ChatAgent | null): string[] {
  const value = agent?.metadata?.icebreakers;

  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 8);
}

function createIcebreakerTitle(prompt: string): string {
  const normalized = prompt.trim();

  if (normalized.length <= 42) {
    return normalized;
  }

  return `${normalized.slice(0, 39)}...`;
}

export function ChatEmptyState({ agent, onUseSuggestion }: ChatEmptyStateProps) {
  const agentIcebreakers = getAgentIcebreakers(agent);
  const isAgentMode = Boolean(agent);

  const suggestions = isAgentMode
    ? agentIcebreakers.map((prompt) => ({
        icon: Sparkles,
        title: createIcebreakerTitle(prompt),
        prompt,
      }))
    : defaultSuggestions;

  return (
    <section
      className={
        isAgentMode
          ? "mdc-chat-empty-state mdc-chat-empty-state--agent"
          : "mdc-chat-empty-state"
      }
      aria-label={isAgentMode ? `Início do agente ${agent?.name}` : "Início da conversa"}
    >
      <div className="mdc-chat-empty-state__hero">
        {isAgentMode ? (
          <span className="mdc-chat-empty-state__agent-icon">
            <Bot size={24} aria-hidden="true" />
          </span>
        ) : null}

        <p className="mdc-chat-eyebrow">
          {isAgentMode ? "Agente selecionado" : "Como posso ajudar?"}
        </p>

        <h2>
          {isAgentMode
            ? agent?.name || "Agente"
            : "Comece fazendo uma pergunta"}
        </h2>

        <p>
          {isAgentMode
            ? agent?.description ||
              "Este especialista usa instruções próprias para responder neste chat."
            : "Consulte conhecimento da plataforma ou dados operacionais autorizados por APIs conectadas."}
        </p>

        {isAgentMode ? (
          <div className="mdc-chat-empty-state__agent-meta">
            <span>{agent?.visibility === "public" ? "Público interno" : "Privado"}</span>
            {agent?.category ? <span>{agent.category}</span> : null}
            {agent?.response_style ? <span>{agent.response_style}</span> : null}
          </div>
        ) : null}
      </div>

      {suggestions.length > 0 ? (
        <div className="mdc-chat-empty-state__grid">
          {suggestions.map((suggestion) => {
            const Icon = suggestion.icon;

            return (
              <button
                key={`${suggestion.title}-${suggestion.prompt}`}
                type="button"
                onClick={() => onUseSuggestion(suggestion.prompt)}
              >
                <Icon size={18} aria-hidden="true" />
                <span>{suggestion.title}</span>
                <small>{suggestion.prompt}</small>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="mdc-chat-empty-state__no-icebreakers">
          <Sparkles size={18} aria-hidden="true" />
          <span>Este agente ainda não possui quebra-gelos configurados.</span>
        </div>
      )}
    </section>
  );
}
