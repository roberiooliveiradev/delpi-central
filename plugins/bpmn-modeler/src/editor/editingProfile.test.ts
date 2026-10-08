/**
 * G2A — contract tests da editing profile central.
 *
 * Prova: CREATE_EDIT allowed · PRESERVE_ONLY/out-of-profile denied ·
 * unclassified vendor option fail-closed (upgrade não amplia o produto).
 */
import { describe, it, expect } from "vitest";
import {
  isReplaceEntryAllowed,
  isReplaceHeaderAllowed,
  isPaletteEntryAllowed,
  isContextPadEntryAllowed,
  isPropertiesGroupAllowed,
  isPropertiesEntryAllowed,
  isClipboardElementAllowed,
  listSearchableCreateActions,
  type ClipboardElement,
} from "./editingProfile";

const allowedReplace = (id: string) => isReplaceEntryAllowed(`replace-with-${id}`);

describe("editingProfile — replace entries (create targets)", () => {
  it("permite activities CREATE_EDIT", () => {
    for (const id of [
      "task", "user-task", "service-task", "send-task", "receive-task",
      "manual-task", "rule-task", "script-task", "call-activity",
      "collapsed-subprocess", "expanded-subprocess",
    ]) expect(allowedReplace(id), id).toBe(true);
  });

  it("nega activities RENDER_PRESERVE_ONLY", () => {
    for (const id of [
      "transaction", "event-subprocess",
      "collapsed-ad-hoc-subprocess", "expanded-ad-hoc-subprocess",
    ]) expect(allowedReplace(id), id).toBe(false);
  });

  it("permite gateways CREATE_EDIT e nega complex", () => {
    for (const id of [
      "exclusive-gateway", "parallel-gateway",
      "inclusive-gateway", "event-based-gateway",
    ]) expect(allowedReplace(id), id).toBe(true);
    expect(allowedReplace("complex-gateway")).toBe(false);
  });

  it("permite defs de evento por posição conforme §6.2", () => {
    const allowed = [
      "none-start-event", "message-start", "timer-start", "signal-start",
      "message-intermediate-catch", "timer-intermediate-catch",
      "signal-intermediate-catch", "link-intermediate-catch",
      "none-intermediate-throwing", "message-intermediate-throw",
      "signal-intermediate-throw", "escalation-intermediate-throw",
      "link-intermediate-throw",
      "message-boundary", "timer-boundary", "error-boundary",
      "signal-boundary", "escalation-boundary",
      "non-interrupting-message-boundary", "non-interrupting-timer-boundary",
      "non-interrupting-signal-boundary", "non-interrupting-escalation-boundary",
      "none-end-event", "message-end", "error-end", "signal-end",
      "escalation-end", "terminate-end",
    ];
    for (const id of allowed) expect(allowedReplace(id), id).toBe(true);
  });

  it("nega defs preserve-only por posição", () => {
    const denied = [
      "conditional-start", "error-start", "escalation-start",
      "compensation-start",
      "non-interrupting-message-start", "non-interrupting-timer-start",
      "non-interrupting-conditional-start", "non-interrupting-signal-start",
      "non-interrupting-escalation-start",
      "conditional-intermediate-catch",
      "compensation-intermediate-throw",
      "none-boundary-event", // boundary CREATE_EDIT exige definição aprovada
      "conditional-boundary", "cancel-boundary", "compensation-boundary",
      "non-interrupting-conditional-boundary",
      "cancel-end", "compensation-end",
    ];
    for (const id of denied) expect(allowedReplace(id), id).toBe(false);
  });

  it("permite data/collaboration entries do profile", () => {
    for (const id of [
      "data-object-reference", "data-store-reference",
      "expanded-pool", "collapsed-pool",
    ]) expect(allowedReplace(id), id).toBe(true);
  });

  it("sequence-flow morphs (default/conditional) permitidos", () => {
    for (const key of [
      "replace-with-sequence-flow",
      "replace-with-default-flow",
      "replace-with-conditional-flow",
    ]) expect(isReplaceEntryAllowed(key), key).toBe(true);
  });

  it("FAIL-CLOSED — id não classificado não é exposto", () => {
    for (const key of [
      "replace-with-future-vendor-option",
      "replace-with-",
      "some-random-key",
      "",
    ]) expect(isReplaceEntryAllowed(key), key).toBe(false);
  });
});

describe("editingProfile — replace header toggles", () => {
  it("nega MultiInstance e loop toggles (fora do profile)", () => {
    for (const key of [
      "toggle-parallel-mi", "toggle-sequential-mi",
      "toggle-loop", "toggle-participant-multiplicity",
    ]) expect(isReplaceHeaderAllowed(key), key).toBe(false);
  });

  it("permite toggles normativos in-profile", () => {
    expect(isReplaceHeaderAllowed("toggle-non-interrupting")).toBe(true);
    expect(isReplaceHeaderAllowed("toggle-is-collection")).toBe(true);
  });

  it("FAIL-CLOSED — header desconhecido negado", () => {
    expect(isReplaceHeaderAllowed("toggle-future")).toBe(false);
  });
});

describe("editingProfile — palette", () => {
  it("permite create entries do profile + tools", () => {
    for (const key of [
      "create.start-event", "create.intermediate-event", "create.end-event",
      "create.exclusive-gateway", "create.task", "create.subprocess-expanded",
      "create.data-object", "create.data-store",
      "create.participant-expanded", "create.group",
      "lasso-tool", "hand-tool", "space-tool",
      "global-connect-tool", "tool-separator",
    ]) expect(isPaletteEntryAllowed(key), key).toBe(true);
  });

  it("FAIL-CLOSED — create entry nova do vendor negada", () => {
    for (const key of [
      "create.transaction", "create.complex-gateway",
      "create.ad-hoc-subprocess", "create.future-element",
    ]) expect(isPaletteEntryAllowed(key), key).toBe(false);
  });
});

describe("editingProfile — context pad", () => {
  it("permite appends/ops in-profile", () => {
    for (const key of [
      "append.end-event", "append.gateway", "append.append-task",
      "append.intermediate-event", "append.receive-task",
      "append.message-intermediate-event", "append.timer-intermediate-event",
      "append.signal-intermediate-event", "append.text-annotation",
      "connect", "delete", "replace",
      "lane-insert-above", "lane-insert-below",
      "lane-divide-two", "lane-divide-three",
    ]) expect(isContextPadEntryAllowed(key), key).toBe(true);
  });

  it("nega append fora do profile (conditional/compensation) e desconhecidos", () => {
    for (const key of [
      "append.condition-intermediate-event",
      "append.compensation-activity", // compensation modeling é preserve-only
      "append.compensation-end-event", "append.future-thing",
    ]) expect(isContextPadEntryAllowed(key), key).toBe(false);
  });
});

describe("editingProfile — properties panel", () => {
  it("permite grupos in-profile", () => {
    for (const id of [
      "general", "advanced", "documentation",
      "error", "link", "message", "signal", "escalation", "timer",
    ]) expect(isPropertiesGroupAllowed(id), id).toBe(true);
  });

  it("nega grupos fora do profile e desconhecidos (fail-closed)", () => {
    for (const id of [
      "multiInstance", "adHocCompletion", "compensation", "future-group",
    ]) expect(isPropertiesGroupAllowed(id), id).toBe(false);
  });

  it("permite entries aprovados do inventário real da surface vendor", () => {
    for (const id of [
      "name", "id", "processId", "processName",
      "documentation", "processDocumentation",
      "errorRef", "errorName", "errorCode",
      "linkName",
      "messageRef", "messageName",
      "signalRef", "signalName",
      "escalationRef", "escalationName", "escalationCode",
      "timerEventDefinitionType", "timerEventDefinitionValue",
    ]) expect(isPropertiesEntryAllowed(id), id).toBe(true);
  });

  it("nega isExecutable (normativo, edição intencionalmente oculta — C4)", () => {
    expect(isPropertiesEntryAllowed("isExecutable")).toBe(false);
  });

  it("FAIL-CLOSED — entry desconhecida/futura do vendor negada", () => {
    for (const id of [
      "future-vendor-field",
      "versionTag",
      "jobPriority",
      "candidateUsers",
      "calledElementType",
      "",
    ]) expect(isPropertiesEntryAllowed(id), id).toBe(false);
  });
});

describe("editingProfile — clipboard (copy/cut/paste/duplicate, G3)", () => {
  const el = (type: string, bo: object = {}): ClipboardElement => ({
    type,
    businessObject: { $type: type, ...bo },
  });

  it("permite tipos CREATE_EDIT (positive)", () => {
    for (const e of [
      el("bpmn:Task"),
      el("bpmn:UserTask"),
      el("bpmn:ServiceTask"),
      el("bpmn:SubProcess"),
      el("bpmn:CallActivity"),
      el("bpmn:ExclusiveGateway"),
      el("bpmn:ParallelGateway"),
      el("bpmn:InclusiveGateway"),
      el("bpmn:EventBasedGateway"),
      el("bpmn:StartEvent"),
      el("bpmn:IntermediateThrowEvent"),
      el("bpmn:EndEvent"),
      el("bpmn:DataObjectReference"),
      el("bpmn:DataStoreReference"),
      el("bpmn:Group"),
      el("bpmn:TextAnnotation"),
      el("bpmn:Participant"),
      el("bpmn:Lane"),
      el("bpmn:SequenceFlow"),
      el("bpmn:MessageFlow"),
      el("bpmn:Association"),
    ]) expect(isClipboardElementAllowed(e), e.type).toBe(true);
  });

  it("permite eventDefinitions dentro da posição CREATE_EDIT", () => {
    expect(
      isClipboardElementAllowed(
        el("bpmn:StartEvent", {
          eventDefinitions: [{ $type: "bpmn:TimerEventDefinition" }],
        }),
      ),
    ).toBe(true);
    expect(
      isClipboardElementAllowed(
        el("bpmn:BoundaryEvent", {
          eventDefinitions: [{ $type: "bpmn:ErrorEventDefinition" }],
        }),
      ),
    ).toBe(true);
    expect(
      isClipboardElementAllowed(
        el("bpmn:EndEvent", {
          eventDefinitions: [{ $type: "bpmn:TerminateEventDefinition" }],
        }),
      ),
    ).toBe(true);
  });

  it("nega tipos PRESERVE_ONLY importados (bypass paste)", () => {
    for (const type of [
      "bpmn:ComplexGateway",
      "bpmn:Transaction",
      "bpmn:AdHocSubProcess",
      "bpmn:ItemDefinition",
      "bpmn:FutureVendorType",
    ]) expect(isClipboardElementAllowed(el(type)), type).toBe(false);
  });

  it("nega markers preserve-only em tipos permitidos (sibling)", () => {
    expect(
      isClipboardElementAllowed(
        el("bpmn:Task", {
          loopCharacteristics: {
            $type: "bpmn:MultiInstanceLoopCharacteristics",
          },
        }),
      ),
    ).toBe(false);
    expect(
      isClipboardElementAllowed(el("bpmn:Task", { isForCompensation: true })),
    ).toBe(false);
    expect(
      isClipboardElementAllowed(
        el("bpmn:SubProcess", { triggeredByEvent: true }),
      ),
    ).toBe(false);
    expect(
      isClipboardElementAllowed(
        el("bpmn:SubProcess", { triggeredByEvent: false }),
      ),
    ).toBe(true);
  });

  it("nega eventDefinitions fora da posição / múltiplas / paralelo", () => {
    expect(
      isClipboardElementAllowed(
        el("bpmn:IntermediateCatchEvent", {
          eventDefinitions: [{ $type: "bpmn:ConditionalEventDefinition" }],
        }),
      ),
    ).toBe(false);
    expect(
      isClipboardElementAllowed(
        el("bpmn:StartEvent", {
          eventDefinitions: [
            { $type: "bpmn:MessageEventDefinition" },
            { $type: "bpmn:TimerEventDefinition" },
          ],
        }),
      ),
    ).toBe(false);
    expect(
      isClipboardElementAllowed(el("bpmn:StartEvent", { parallelMultiple: true })),
    ).toBe(false);
    expect(
      isClipboardElementAllowed(
        el("bpmn:StartEvent", { isInterrupting: false }),
      ),
    ).toBe(false);
    expect(isClipboardElementAllowed(el("bpmn:BoundaryEvent"))).toBe(false);
  });

  it("nega parent CREATE_EDIT que carrega descendant/attacher preserve-only", () => {
    // subprocess contendo EventSubProcess → conjunto negado (vendor não
    // filtra subárvore do clipboard)
    const sub = el("bpmn:SubProcess");
    sub.children = [
      el("bpmn:SubProcess", { triggeredByEvent: true }),
    ];
    expect(isClipboardElementAllowed(sub)).toBe(false);
    // mesmo subprocess com filho permitido → copiável
    sub.children = [el("bpmn:Task")];
    expect(isClipboardElementAllowed(sub)).toBe(true);
    // task com boundary preserve-only (cancel) → negada
    const task = el("bpmn:Task");
    task.attachers = [
      el("bpmn:BoundaryEvent", {
        eventDefinitions: [{ $type: "bpmn:CancelEventDefinition" }],
      }),
    ];
    expect(isClipboardElementAllowed(task)).toBe(false);
    // task com boundary permitido (timer) → copiável
    task.attachers = [
      el("bpmn:BoundaryEvent", {
        eventDefinitions: [{ $type: "bpmn:TimerEventDefinition" }],
      }),
    ];
    expect(isClipboardElementAllowed(task)).toBe(true);
  });

  it("FAIL-CLOSED — businessObject ausente/sem $type é negado; label segue owner", () => {
    expect(isClipboardElementAllowed({ type: "bpmn:Task" })).toBe(false);
    expect(
      isClipboardElementAllowed({ type: "bpmn:Task", businessObject: null }),
    ).toBe(false);
    expect(
      isClipboardElementAllowed({ type: "bpmn:Task", businessObject: {} }),
    ).toBe(false);
    expect(isClipboardElementAllowed({ type: "label" })).toBe(true);
  });
});

describe('editingProfile — searchable create actions (G3-PAL-1)', () => {
  const actions = listSearchableCreateActions();
  const byId = new Map(actions.map((a) => [a.id, a]));

  it('toda ação passa pelos predicados canônicos (fail-closed projection)', () => {
    expect(actions.length).toBeGreaterThan(0);
    for (const a of actions) {
      expect(isPaletteEntryAllowed(a.paletteEntryId), a.id).toBe(true);
      if (a.replaceEntryId) {
        expect(isReplaceEntryAllowed(a.replaceEntryId), a.id).toBe(true);
        expect(a.strategy).toBe('CREATE_THEN_REPLACE');
      } else {
        expect(a.strategy).toBe('DIRECT_PALETTE_CREATE');
      }
    }
  });

  it('tasks tipados rotam para replace entries corretos', () => {
    const typed: Array<[string, string]> = [
      ['user-task', 'replace-with-user-task'],
      ['service-task', 'replace-with-service-task'],
      ['manual-task', 'replace-with-manual-task'],
      ['rule-task', 'replace-with-rule-task'],
      ['script-task', 'replace-with-script-task'],
      ['send-task', 'replace-with-send-task'],
      ['receive-task', 'replace-with-receive-task'],
      ['call-activity', 'replace-with-call-activity'],
    ];
    for (const [id, rep] of typed) {
      expect(byId.get(id)?.replaceEntryId, id).toBe(rep);
      expect(byId.get(id)?.paletteEntryId).toBe('create.task');
    }
  });

  it('gateways tipados rotam via exclusive-gateway create', () => {
    for (const [id, rep] of [
      ['parallel-gateway', 'replace-with-parallel-gateway'],
      ['inclusive-gateway', 'replace-with-inclusive-gateway'],
      ['event-based-gateway', 'replace-with-event-based-gateway'],
    ] as const) {
      expect(byId.get(id)?.replaceEntryId, id).toBe(rep);
      expect(byId.get(id)?.paletteEntryId).toBe('create.exclusive-gateway');
    }
  });

  it('aliases específicos não existem em ação genérica (anti-misrouting)', () => {
    const task = byId.get('task')!;
    for (const term of ['usuario', 'usuário', 'servico', 'serviço', 'manual', 'regra']) {
      const hay = [task.label, task.id, ...task.aliases].map((s) => s.toLowerCase());
      expect(hay.some((h) => h.includes(term)), term).toBe(false);
    }
    const gw = byId.get('exclusive-gateway')!;
    for (const term of ['paralelo', 'inclusivo', 'eventos']) {
      const hay = [gw.label, gw.id, ...gw.aliases].map((s) => s.toLowerCase());
      expect(hay.some((h) => h.includes(term)), term).toBe(false);
    }
  });

  it('eventos tipados apontam para replace entries position-aware', () => {
    for (const [id, rep] of [
      ['timer-start', 'replace-with-timer-start'],
      ['message-start', 'replace-with-message-start'],
      ['timer-intermediate-catch', 'replace-with-timer-intermediate-catch'],
      ['message-intermediate-throw', 'replace-with-message-intermediate-throw'],
      ['terminate-end', 'replace-with-terminate-end'],
    ] as const) {
      expect(byId.get(id)?.replaceEntryId, id).toBe(rep);
    }
  });

  it('constructs contextuais e preserve-only não são pesquisáveis', () => {
    for (const a of actions) {
      expect(a.label.toLowerCase()).not.toMatch(/lane|raia|boundary|borda/);
    }
    expect(byId.has('lane')).toBe(false);
  });
});
