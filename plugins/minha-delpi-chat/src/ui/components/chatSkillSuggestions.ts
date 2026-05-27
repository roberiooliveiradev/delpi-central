import type { ChatSkillCatalogItem } from "../../data/api/chatTypes";

/** Skills exibidas como atalhos na tela inicial do chat (sem agente). */
export const CHAT_STARTER_SKILL_KEYS = ["company-knowledge", "sql"] as const;

export const CHAT_SKILL_SUGGESTION_PROMPTS: Record<string, string> = {
  "company-knowledge":
    "Consulte o conhecimento da empresa (base global de políticas, diretrizes e manuais) para responder. Cite as fontes documentais quando usar esse material.",
  sql: "Elabore uma consulta SQL (SELECT) para responder à minha necessidade, em um bloco ```sql```, com breve explicação.",
};

function isStarterSkillKey(skillKey: string): skillKey is (typeof CHAT_STARTER_SKILL_KEYS)[number] {
  return (CHAT_STARTER_SKILL_KEYS as readonly string[]).includes(skillKey);
}

export function listStarterSkills(catalog: ChatSkillCatalogItem[]): ChatSkillCatalogItem[] {
  const order = new Map<string, number>(
    CHAT_STARTER_SKILL_KEYS.map((key, index) => [key, index]),
  );

  return catalog
    .filter((item) => isStarterSkillKey(item.skillKey))
    .sort(
      (left, right) =>
        (order.get(left.skillKey) ?? 99) - (order.get(right.skillKey) ?? 99),
    );
}

export function getSkillSuggestionPrompt(skillKey: string, label: string): string {
  return (
    CHAT_SKILL_SUGGESTION_PROMPTS[skillKey] ??
    `Use a skill ${label} para orientar sua resposta.`
  );
}
