import { Database, FileSearch, MessageSquarePlus, Route } from "lucide-react";

import "./ChatEmptyState.css";

type ChatEmptyStateProps = {
  onUseSuggestion: (value: string) => void;
};

const suggestions = [
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

export function ChatEmptyState({ onUseSuggestion }: ChatEmptyStateProps) {
  return (
    <section className="mdc-chat-empty-state" aria-label="Início da conversa">
      <div>
        <p className="mdc-chat-eyebrow">Como posso ajudar?</p>
        <h2>Comece fazendo uma pergunta</h2>
        <p>
          Consulte conhecimento da plataforma ou dados operacionais autorizados
          por APIs conectadas.
        </p>
      </div>

      <div className="mdc-chat-empty-state__grid">
        {suggestions.map((suggestion) => {
          const Icon = suggestion.icon;

          return (
            <button
              key={suggestion.title}
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
    </section>
  );
}
