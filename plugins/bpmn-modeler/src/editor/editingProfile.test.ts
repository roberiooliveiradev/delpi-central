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
