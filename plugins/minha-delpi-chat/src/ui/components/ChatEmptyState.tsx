import { Database, Network } from "lucide-react";

import type { ChatSkillCatalogItem } from "../../data/api/chatTypes";
import { getFirstDisplayName } from "../../utils/authDisplayName";
import {
  getSkillSuggestionPrompt,
  listStarterSkills,
} from "./chatSkillSuggestions";

import "./ChatEmptyState.css";

type ChatEmptyStateProps = {
  displayName?: string | null;
  skillCatalog?: ChatSkillCatalogItem[];
  onUseSuggestion?: (value: string) => void;
};

function SkillIcon({ skillKey }: { skillKey: string }) {
  if (skillKey === "sql") {
    return <Database size={17} aria-hidden="true" />;
  }

  return <Network size={17} aria-hidden="true" />;
}

export function ChatEmptyState({
  displayName,
  skillCatalog = [],
  onUseSuggestion,
}: ChatEmptyStateProps) {
  const firstName = getFirstDisplayName(displayName);

  const greeting = firstName
    ? `Ei, ${firstName}. Tudo pronto para começar?`
    : "Tudo pronto para começar?";

  const starterSkills = listStarterSkills(skillCatalog);

  return (
    <section className="mdc-chat-empty-state" aria-label="Início da conversa">
      <div className="mdc-chat-empty-state__hero">
        <h2>{greeting}</h2>
      </div>

      {starterSkills.length > 0 ? (
        <div className="mdc-chat-empty-state__skills" role="list">
          {starterSkills.map((skill) => (
            <button
              key={skill.skillKey}
              type="button"
              role="listitem"
              className="mdc-chat-empty-state__skill-pill"
              onClick={() =>
                onUseSuggestion?.(getSkillSuggestionPrompt(skill.skillKey, skill.label))
              }
            >
              <SkillIcon skillKey={skill.skillKey} />
              <span>{skill.label}</span>
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
