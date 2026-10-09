import { describe, expect, it } from "vitest";

import { propertiesPanelModule } from "./propertiesPanelModule";
import { translate } from "./i18n/translate";

/* eslint-disable @typescript-eslint/no-explicit-any */

const AdvancedIdProvider = propertiesPanelModule.advancedIdProvider[1] as any;
const PopupTitlePtBr = propertiesPanelModule.popupTitlePtBr[1] as any;
const BpmnCorePropsProvider = propertiesPanelModule
  .bpmnCorePropsProvider[1] as any;

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

describe("TextPopupProvider", () => {
  const TextPopupProvider = propertiesPanelModule.textPopupProvider[1] as any;

  it("registra componente para o tipo `text` com translate injetado", () => {
    const registrations: { type: string; component: any }[] = [];
    const feelPopup = {
      registerProvider(type: string, component: any) {
        registrations.push({ type, component });
      },
    };
    new TextPopupProvider(feelPopup, translate);
    expect(registrations).toHaveLength(1);
    expect(registrations[0].type).toBe("text");
    const vnode = registrations[0].component({ title: "T", value: "" });
    expect(vnode).toBeTruthy();
    // o tooltip hardcoded do vendor sai traduzido via prop do provider
    const title = vnode.props.children[0];
    expect(title.props.closeButtonTooltip).toBe("Salvar e fechar");
  });
});

describe("PanelChromePtBr", () => {
  const PanelChromePtBr = propertiesPanelModule.panelChromePtBr[1] as any;

  function makeBus() {
    const listeners: { event: string; fn: (...a: any[]) => void }[] = [];
    return {
      listeners,
      on(event: string, pOrFn: unknown, fn?: (...a: any[]) => void) {
        listeners.push({ event, fn: (fn ?? pOrFn) as (...a: any[]) => void });
      },
    };
  }

  function fakeEl(title: string) {
    const attrs = new Map([["title", title]]);
    return {
      getAttribute: (k: string) => attrs.get(k) ?? null,
      setAttribute: (k: string, v: string) => void attrs.set(k, v),
      textContent: "x",
    };
  }

  function fakePanel(container: unknown) {
    return { _container: container };
  }

  it("traduz tooltips EN conhecidas dentro do container do painel", () => {
    const bus = makeBus();
    const inside = fakeEl("Open pop-up editor");
    const container = { querySelectorAll: () => [inside] };
    new PanelChromePtBr(bus, fakePanel(container));

    const rendered = bus.listeners.find(
      (l) => l.event === "propertiesPanel.rendered",
    );
    expect(rendered).toBeTruthy();
    rendered!.fn();
    expect(inside.getAttribute("title")).toBe("Abrir editor ampliado");
  });

  it("usa o domNode do evento feelPopup.opened (popup fora do container)", async () => {
    const bus = makeBus();
    new PanelChromePtBr(bus, fakePanel(null));
    const listener = bus.listeners.find((l) => l.event === "feelPopup.opened");
    expect(listener).toBeTruthy();

    const close = fakeEl("Save and close");
    listener!.fn({ domNode: { querySelectorAll: () => [close] } });
    // domNode do popup já está commitado quando opened dispara — fix síncrono
    expect(close.getAttribute("title")).toBe("Salvar e fechar");
  });

  it("feelPopup.opened também normaliza o placeholder in-panel", async () => {
    const bus = makeBus();
    const inside = fakeEl("Open pop-up editor");
    new PanelChromePtBr(bus, fakePanel({ querySelectorAll: () => [inside] }));
    bus.listeners
      .find((l) => l.event === "feelPopup.opened")!
      .fn({ domNode: null });
    await Promise.resolve();
    expect(inside.getAttribute("title")).toBe("Abrir editor ampliado");
  });

  it("defer de updated agenda microtask, não polling", async () => {
    const bus = makeBus();
    const inside = fakeEl("Open pop-up editor");
    new PanelChromePtBr(bus, fakePanel({ querySelectorAll: () => [inside] }));
    bus.listeners
      .find((l) => l.event === "propertiesPanel.updated")!
      .fn();
    // ainda não aplicado (microtask pendente)
    expect(inside.getAttribute("title")).toBe("Open pop-up editor");
    await Promise.resolve();
    expect(inside.getAttribute("title")).toBe("Abrir editor ampliado");
  });
});

// ---------------------------------------------------------------------------
// BpmnCorePropsProvider — Wave E: calledElement / conditionExpression / default
// ---------------------------------------------------------------------------

/** businessObject fake com o contrato moddle mínimo usado pelos utils
    vendor (`$instanceOf`, `get`). */
function fakeBo(
  type: string,
  props: Record<string, any> = {},
  superTypes: string[] = [],
): any {
  return {
    $type: type,
    $instanceOf(t: string) {
      return t === this.$type || superTypes.includes(t);
    },
    get(p: string) {
      return this[p];
    },
    ...props,
  };
}

function fakeEl(bo: any, source?: any): any {
  const element: any = { businessObject: bo };
  if (source) element.source = source;
  return element;
}

function groupsFor(provider: any, element: any) {
  return provider.getGroups(element)([{ id: "general", entries: [] }]);
}

describe("BpmnCorePropsProvider (Wave E)", () => {
  it("expõe calledElement apenas para bpmn:CallActivity", () => {
    const provider = new BpmnCorePropsProvider(fakePanel());
    const call = groupsFor(provider, fakeEl(fakeBo("bpmn:CallActivity")));
    const group = call.find((g: any) => g.id === "callActivity");
    expect(group).toBeTruthy();
    expect(group.entries.map((e: any) => e.id)).toEqual(["calledElement"]);

    const task = groupsFor(provider, fakeEl(fakeBo("bpmn:Task")));
    expect(task.find((g: any) => g.id === "callActivity")).toBeUndefined();
  });

  it("expõe condition+default em SequenceFlow com source elegível", () => {
    const provider = new BpmnCorePropsProvider(fakePanel());
    for (const srcType of [
      "bpmn:Task",
      "bpmn:ExclusiveGateway",
      "bpmn:InclusiveGateway",
    ]) {
      const flow = fakeEl(
        fakeBo("bpmn:SequenceFlow"),
        fakeEl(
          fakeBo(
            srcType,
            {},
            srcType === "bpmn:Task" ? ["bpmn:Activity"] : [],
          ),
        ),
      );
      const flowGroup = groupsFor(provider, flow).find(
        (g: any) => g.id === "flow",
      );
      expect(flowGroup, srcType).toBeTruthy();
      expect(flowGroup.entries.map((e: any) => e.id).sort()).toEqual([
        "conditionExpression",
        "defaultFlow",
      ]);
    }
  });

  it("não expõe flow group em contexto inválido (events, parallel, event-based, complex)", () => {
    const provider = new BpmnCorePropsProvider(fakePanel());
    for (const srcType of [
      "bpmn:StartEvent",
      "bpmn:ParallelGateway",
      "bpmn:EventBasedGateway",
      "bpmn:EndEvent",
      "bpmn:ComplexGateway",
    ]) {
      const flow = fakeEl(
        fakeBo("bpmn:SequenceFlow"),
        fakeEl(fakeBo(srcType)),
      );
      expect(
        groupsFor(provider, flow).find((g: any) => g.id === "flow"),
        srcType,
      ).toBeUndefined();
    }
    const task = groupsFor(provider, fakeEl(fakeBo("bpmn:Task")));
    expect(task.find((g: any) => g.id === "flow")).toBeUndefined();
  });

  it("exclusão mútua: default flow não mostra condition; flow com condition não mostra default", () => {
    const provider = new BpmnCorePropsProvider(fakePanel());
    const sourceBo = fakeBo("bpmn:ExclusiveGateway");
    const flowBo = fakeBo("bpmn:SequenceFlow");
    sourceBo.default = flowBo;
    const defFlow = fakeEl(flowBo, fakeEl(sourceBo));
    expect(
      groupsFor(provider, defFlow)
        .find((g: any) => g.id === "flow")
        .entries.map((e: any) => e.id),
    ).toEqual(["defaultFlow"]);

    const condFlowBo = fakeBo("bpmn:SequenceFlow", {
      conditionExpression: fakeBo("bpmn:FormalExpression", {
        body: "x > 1",
      }),
    });
    const condFlow = fakeEl(
      condFlowBo,
      fakeEl(fakeBo("bpmn:Task", {}, ["bpmn:Activity"])),
    );
    expect(
      groupsFor(provider, condFlow)
        .find((g: any) => g.id === "flow")
        .entries.map((e: any) => e.id),
    ).toEqual(["conditionExpression"]);
  });
});
