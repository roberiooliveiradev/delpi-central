import { Bot, Folder, Plus, Sparkles, X } from "lucide-react";
import { useState } from "react";

import type { ChatAgent, ChatProject } from "../../data/api/chatTypes";

import "./ChatInput.css";

type ChatInputProps = {
  value: string;
  disabled?: boolean;
  isSending?: boolean;
  variant?: "dock" | "center";
  placeholder?: string;
  agents?: ChatAgent[];
  projects?: ChatProject[];
  selectedAgentKey?: string | null;
  selectedProjectId?: string | null;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onCancel?: () => void;
  onSelectAgent?: (agentKey: string | null) => void;
  onSelectProject?: (projectId: string | null) => void;
};

export function ChatInput({
  value,
  disabled,
  isSending,
  variant = "dock",
  placeholder = "Pergunte alguma coisa",
  agents = [],
  projects = [],
  selectedAgentKey,
  selectedProjectId,
  onChange,
  onSubmit,
  onCancel,
  onSelectAgent,
  onSelectProject,
}: ChatInputProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const selectedAgent = agents.find((agent) => agent.key === selectedAgentKey);
  const selectedProject = projects.find((project) => project.id === selectedProjectId);

  return (
    <form
      className={
        variant === "center"
          ? "mdc-chat-input mdc-chat-input--center"
          : "mdc-chat-input"
      }
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <div className="mdc-chat-input__box">
        <div className="mdc-chat-input__plus-wrap">
          <button
            type="button"
            className="mdc-chat-input__plus"
            onClick={() => setIsMenuOpen((current) => !current)}
            aria-label="Mais opções"
            aria-expanded={isMenuOpen}
          >
            <Plus size={20} aria-hidden="true" />
          </button>

          {isMenuOpen ? (
            <div className="mdc-chat-input__menu">
              <div className="mdc-chat-input__menu-section">
                <strong>Usar agente</strong>

                {selectedAgent ? (
                  <button
                    type="button"
                    onClick={() => {
                      onSelectAgent?.(null);
                      setIsMenuOpen(false);
                    }}
                  >
                    <X size={16} aria-hidden="true" />
                    <span>Sair do agente</span>
                  </button>
                ) : null}

                {agents.map((agent) => (
                  <button
                    key={agent.id}
                    type="button"
                    className={
                      agent.key === selectedAgentKey
                        ? "mdc-chat-input__menu-item--active"
                        : undefined
                    }
                    onClick={() => {
                      onSelectAgent?.(agent.key);
                      setIsMenuOpen(false);
                    }}
                  >
                    <Bot size={16} aria-hidden="true" />
                    <span>{agent.name}</span>
                  </button>
                ))}
              </div>

              <div className="mdc-chat-input__menu-section">
                <strong>Projeto</strong>

                {selectedProject ? (
                  <button
                    type="button"
                    onClick={() => {
                      onSelectProject?.(null);
                      setIsMenuOpen(false);
                    }}
                  >
                    <X size={16} aria-hidden="true" />
                    <span>Sair do projeto</span>
                  </button>
                ) : null}

                {projects.slice(0, 8).map((project) => (
                  <button
                    key={project.id}
                    type="button"
                    className={
                      project.id === selectedProjectId
                        ? "mdc-chat-input__menu-item--active"
                        : undefined
                    }
                    onClick={() => {
                      onSelectProject?.(project.id);
                      setIsMenuOpen(false);
                    }}
                  >
                    <Folder size={16} aria-hidden="true" />
                    <span>{project.name}</span>
                  </button>
                ))}
              </div>

              <div className="mdc-chat-input__menu-section">
                <strong>Em breve</strong>

                <button type="button" disabled>
                  <Sparkles size={16} aria-hidden="true" />
                  <span>Adicionar fonte</span>
                </button>

                <button type="button" disabled>
                  <Sparkles size={16} aria-hidden="true" />
                  <span>Escolher action</span>
                </button>
              </div>
            </div>
          ) : null}
        </div>

        <textarea
          value={value}
          disabled={disabled || isSending}
          placeholder={placeholder}
          rows={variant === "center" ? 1 : 3}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              onSubmit();
            }
          }}
        />
      </div>

      {isSending ? (
        <button type="button" onClick={onCancel}>
          Cancelar
        </button>
      ) : (
        <button type="submit" disabled={disabled || !value.trim()}>
          Enviar
        </button>
      )}

      <small>
        A resposta será exibida em tempo real e salva no histórico ao concluir.
      </small>
    </form>
  );
}
