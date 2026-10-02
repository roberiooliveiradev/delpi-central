import { describe, expect, it } from "vitest";

import { propertiesPanelModule } from "./propertiesPanelModule";
import { translate } from "./i18n/translate";

/* eslint-disable @typescript-eslint/no-explicit-any */

const AdvancedIdProvider = propertiesPanelModule.advancedIdProvider[1] as any;
const PopupTitlePtBr = propertiesPanelModule.popupTitlePtBr[1] as any;

function fakePanel() {
  const registered: { priority: number; provider: any }[] = [];
  return {
    registered,
    registerProvider(priority: number, provider: any) {
      registered.push({ priority, provider });
    },
  };
}

function makeProvider() {
  const panel = fakePanel();
  const provider = new AdvancedIdProvider(panel, translate);
  return { panel, provider };
}

function groupsFixture() {
  return [
    {
      id: "general",
      label: "Geral",
      entries: [
        { id: "name", component: "TextField" },
        { id: "id", component: "TextField" },
        { id: "isExecutable", component: "Checkbox" },
      ],
    },
    { id: "documentation", label: "Documentação", entries: [{ id: "documentation" }] },
  ];
}

describe("AdvancedIdProvider", () => {
  it("se registra com prioridade abaixo dos providers vendor", () => {
    const { panel, provider } = makeProvider();
    const rec = panel.registered.find((r) => r.provider === provider);
    expect(rec?.priority).toBeLessThan(500);
  });

  it("move o entry `id` para o grupo avançado, preservando os demais", () => {
    const { provider } = makeProvider();
    const groups = provider.getGroups()(groupsFixture());

    const general = groups.find((g: any) => g.id === "general");
    expect(general.entries.map((e: any) => e.id)).toEqual(["name", "isExecutable"]);

    const advanced = groups.find((g: any) => g.id === "advanced");
    expect(advanced.label).toBe("Configurações avançadas");
    expect(advanced.entries.map((e: any) => e.id)).toEqual(["id"]);
    // entry vendor preservado — mesmo objeto, mesmo binding/command stack
    expect(advanced.entries[0].component).toBe("TextField");
  });

  it("move também `processId` (ID do processo no painel do participant)", () => {
    const { provider } = makeProvider();
    const groups = provider.getGroups()([
      {
        id: "general",
        entries: [
          { id: "name" },
          { id: "id", component: "TextField" },
          { id: "processId", component: "TextField" },
        ],
      },
    ]);
    const advanced = groups.find((g: any) => g.id === "advanced");
    expect(advanced.entries.map((e: any) => e.id)).toEqual(["id", "processId"]);
  });

  it("o grupo avançado vai para o fim da lista", () => {
    const { provider } = makeProvider();
    const groups = provider.getGroups()(groupsFixture());
    expect(groups.at(-1).id).toBe("advanced");
  });

  it("descarta o grupo de origem quando ele fica vazio", () => {
    const { provider } = makeProvider();
    const groups = provider.getGroups()([
      { id: "general", entries: [{ id: "id", component: "TextField" }] },
    ]);
    expect(groups.map((g: any) => g.id)).toEqual(["advanced"]);
  });

  it("anexa ao grupo `advanced` já existente em vez de duplicar", () => {
    const { provider } = makeProvider();
    const groups = provider.getGroups()([
      { id: "general", entries: [{ id: "id" }, { id: "name" }] },
      { id: "advanced", label: "Advanced", entries: [{ id: "other" }] },
    ]);
    expect(groups.filter((g: any) => g.id === "advanced")).toHaveLength(1);
    expect(
      groups.find((g: any) => g.id === "advanced").entries.map((e: any) => e.id),
    ).toEqual(["other", "id"]);
  });

  it("é neutro quando não há entry `id`", () => {
    const { provider } = makeProvider();
    const input = [{ id: "general", entries: [{ id: "name" }] }];
    const groups = provider.getGroups()(input);
    expect(groups).toEqual(input);
  });

  it("tolera grupos sem `entries` (list groups)", () => {
    const { provider } = makeProvider();
    const input = [
      { id: "general", entries: [{ id: "id" }, { id: "name" }] },
      { id: "listeners" },
    ];
    const groups = provider.getGroups()(input);
    expect(groups.find((g: any) => g.id === "listeners")).toBeTruthy();
  });
});

describe("PopupTitlePtBr", () => {
  function makeBus() {
    const listeners: { event: string; priority: number; fn: (e: any) => void }[] = [];
    return {
      listeners,
      on(event: string, priority: number, fn: (e: any) => void) {
        listeners.push({ event, priority, fn });
      },
    };
  }

  it("troca o type cru por label PT-BR no clone, sem mutar o elemento real", () => {
    const bus = makeBus();
    new PopupTitlePtBr(bus);
    const listener = bus.listeners.find(
      (l) => l.event === "propertiesPanel.openPopup",
    );
    expect(listener).toBeTruthy();
    expect(listener!.priority).toBeGreaterThan(1000);

    const element = { type: "bpmn:Process", label: "Nome" };
    const event: any = { element };
    listener!.fn(event);

    expect(event.element.type).toBe("Processo");
    expect(event.element.label).toBe("Nome");
    expect(element.type).toBe("bpmn:Process");
  });

  it("ignora eventos sem element/type", () => {
    const bus = makeBus();
    new PopupTitlePtBr(bus);
    const listener = bus.listeners[0];
    expect(() => listener.fn({})).not.toThrow();
    expect(() => listener.fn({ element: {} })).not.toThrow();
  });
});
