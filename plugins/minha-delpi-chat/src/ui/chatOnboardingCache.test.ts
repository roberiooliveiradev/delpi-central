import { beforeEach, describe, expect, it, vi } from "vitest";

import type { AssistantOnboardingPayload } from "../data/api/chatTypes";
import {
  readHomeCatalogCache,
  writeHomeCatalogCache,
} from "./chatOnboardingCache";

const storage = new Map<string, string>();

beforeEach(() => {
  storage.clear();
  vi.stubGlobal("sessionStorage", {
    getItem: (key: string) => storage.get(key) ?? null,
    setItem: (key: string, value: string) => {
      storage.set(key, value);
    },
    removeItem: (key: string) => {
      storage.delete(key);
    },
  });
});

const sampleOnboarding: AssistantOnboardingPayload = {
  welcome: {
    title: "Olá! Posso ajudar com consultas operacionais, textos, documentos.",
    subtitle: "Escolha uma opção para começar ou escreva do seu jeito.",
  },
  starterCards: [],
  profiles: [],
  selectedProfileId: null,
  tourSteps: [],
};

describe("chatOnboardingCache", () => {
  it("persiste e restaura catálogo por perfil", () => {
    writeHomeCatalogCache("engenharia", {
      onboarding: sampleOnboarding,
      highlights: [],
    });

    expect(readHomeCatalogCache("engenharia")).toEqual({
      onboarding: sampleOnboarding,
      highlights: [],
    });
  });

  it("mantém caches separados por perfil", () => {
    writeHomeCatalogCache("engenharia", {
      onboarding: sampleOnboarding,
      highlights: [],
    });

    writeHomeCatalogCache("compras", {
      onboarding: {
        ...sampleOnboarding,
        welcome: { title: "Compras", subtitle: "Suprimentos" },
      },
      highlights: [],
    });

    expect(readHomeCatalogCache("engenharia")?.onboarding?.welcome?.title).toContain(
      "consultas operacionais",
    );
    expect(readHomeCatalogCache("compras")?.onboarding?.welcome?.title).toBe("Compras");
  });
});
