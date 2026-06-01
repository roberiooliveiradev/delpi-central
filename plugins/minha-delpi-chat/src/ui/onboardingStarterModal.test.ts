import { describe, expect, it } from "vitest";

import onboarding from "../../../../minha-delpi-ai-api/app/content/pt-BR/assistant/onboarding.json";
import {
  hasShortcutPlaceholders,
  normalizeShortcutTemplate,
  resolveStarterPromptOptions,
  starterRequiresShortcutModal,
} from "./chatShortcutPrompt";

type StarterCard = {
  id?: string;
  label?: string;
  query?: string;
};

const MODAL_STARTER_IDS = new Set([
  "product",
  "stock",
  "supplier",
  "structure",
  "sales",
  "purchases",
  "email",
  "correct",
  "text",
  "minutes",
]);

const DIRECT_STARTER_IDS = new Set([
  "capabilities",
  "attachment",
  "norms",
  "kpi",
  "summary",
  "chart",
]);

function profileCards(): Array<{ profileId: string; card: StarterCard }> {
  const rows: Array<{ profileId: string; card: StarterCard }> = [];

  for (const preset of onboarding.profilePresets ?? []) {
    const profileId = String(preset.id ?? "");

    for (const card of preset.cards ?? []) {
      rows.push({ profileId, card });
    }
  }

  return rows;
}

describe("onboarding starter modal routing", () => {
  it("cards operacionais por perfil abrem modal de contexto", () => {
    for (const { profileId, card } of profileCards()) {
      const query = String(card.query ?? "");
      const starterId = String(card.id ?? "");
      const normalized = normalizeShortcutTemplate(query);

      if (MODAL_STARTER_IDS.has(starterId)) {
        expect(starterRequiresShortcutModal(query, { starterId }), `${profileId}/${starterId}`).toBe(
          true,
        );
        expect(hasShortcutPlaceholders(normalized), `${profileId}/${starterId}`).toBe(true);
        continue;
      }

      if (DIRECT_STARTER_IDS.has(starterId)) {
        expect(starterRequiresShortcutModal(query, { starterId }), `${profileId}/${starterId}`).toBe(
          false,
        );
      }
    }
  });

  it("usa diálogo de produto para ids operacionais do onboarding", () => {
    for (const { profileId, card } of profileCards()) {
      const starterId = String(card.id ?? "");

      if (!MODAL_STARTER_IDS.has(starterId) || starterId === "email" || starterId === "minutes") {
        continue;
      }

      if (starterId === "correct" || starterId === "text") {
        continue;
      }

      const options = resolveStarterPromptOptions(String(card.query ?? ""), { starterId });

      expect(options.title, `${profileId}/${starterId}`).toBe("Consulta operacional");
    }
  });
});
