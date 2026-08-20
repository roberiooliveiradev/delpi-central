import { describe, expect, it, vi } from "vitest";

import {
  CREATE_TASK_MESSAGE_ACTION_ID,
  EDIT_MESSAGE_ACTION_ID,
  PIN_MESSAGE_ACTION_ID,
  UNPIN_MESSAGE_ACTION_ID,
  buildCreateTaskMessageAction,
  buildEditMessageAction,
  buildPinMessageAction,
  canCreateTaskFromMessage,
  canEditMessage,
  canPinMessage,
  resolveInteractionMessageActions,
} from "./messageThreadTaskAction";

describe("messageThreadTaskAction", () => {
  it("permite tarefa só em mensagens de texto ativas", () => {
    expect(canCreateTaskFromMessage({ kind: "text", deleted: false })).toBe(true);
    expect(canCreateTaskFromMessage({ kind: "system", deleted: false })).toBe(false);
    expect(canCreateTaskFromMessage({ kind: "task_ref", deleted: false })).toBe(false);
    expect(canCreateTaskFromMessage({ kind: "text", deleted: true })).toBe(false);
  });

  it("permite pin em texto e task_ref, não em system", () => {
    expect(canPinMessage({ kind: "text", deleted: false })).toBe(true);
    expect(canPinMessage({ kind: "task_ref", deleted: false })).toBe(true);
    expect(canPinMessage({ kind: "system", deleted: false })).toBe(false);
    expect(canPinMessage({ kind: "text", deleted: true })).toBe(false);
  });

  it("permite editar só texto próprio ativo", () => {
    expect(canEditMessage({ kind: "text", deleted: false, mine: true })).toBe(true);
    expect(canEditMessage({ kind: "text", deleted: false, mine: false })).toBe(false);
    expect(canEditMessage({ kind: "system", deleted: false, mine: true })).toBe(false);
    expect(canEditMessage({ kind: "text", deleted: true, mine: true })).toBe(false);
  });

  it("monta ação create-task sem botão local no kit", () => {
    const onCreateTask = vi.fn();
    const action = buildCreateTaskMessageAction({
      message: { id: "m1", kind: "text", deleted: false },
      onCreateTask,
    });
    expect(action?.id).toBe(CREATE_TASK_MESSAGE_ACTION_ID);
    expect(action?.icon).toBeTruthy();
    expect(action?.title).toBe(action?.label);
    action?.onClick();
    expect(onCreateTask).toHaveBeenCalledWith("m1");
  });

  it("monta ação editar para mensagem própria", () => {
    const onEdit = vi.fn();
    const action = buildEditMessageAction({
      message: { id: "m1", kind: "text", deleted: false, mine: true },
      onEdit,
    });
    expect(action?.id).toBe(EDIT_MESSAGE_ACTION_ID);
    expect(action?.icon).toBeTruthy();
    action?.onClick();
    expect(onEdit).toHaveBeenCalledWith("m1");
    expect(
      buildEditMessageAction({
        message: { id: "m1", kind: "text", deleted: false, mine: false },
        onEdit,
      }),
    ).toBeNull();
  });

  it("monta pin/unpin conforme estado", () => {
    const onTogglePin = vi.fn();
    const pin = buildPinMessageAction({
      message: { id: "m1", kind: "text", deleted: false },
      pinned: false,
      onTogglePin,
    });
    expect(pin?.id).toBe(PIN_MESSAGE_ACTION_ID);
    expect(pin?.icon).toBeTruthy();
    expect(pin?.title).toBe(pin?.label);
    pin?.onClick();
    expect(onTogglePin).toHaveBeenCalledWith("m1", true);

    const unpin = buildPinMessageAction({
      message: { id: "m1", kind: "text", deleted: false },
      pinned: true,
      onTogglePin,
    });
    expect(unpin?.id).toBe(UNPIN_MESSAGE_ACTION_ID);
  });

  it("resolveActions omite create-task enquanto busy; pin permanece se não busy", () => {
    const actions = resolveInteractionMessageActions({
      message: {
        id: "m1",
        kind: "text",
        bodyText: "x",
        createdAtLabel: "",
      },
      onCreateTask: () => undefined,
      creatingMessageId: "m1",
      pinnedMessageIds: new Set(),
      onTogglePin: () => undefined,
    });
    expect(actions.map((a) => a.id)).toEqual([PIN_MESSAGE_ACTION_ID]);
  });

  it("resolveActions inclui edit + create-task + pin para mine", () => {
    const actions = resolveInteractionMessageActions({
      message: {
        id: "m1",
        kind: "text",
        bodyText: "x",
        createdAtLabel: "",
        mine: true,
      },
      onCreateTask: () => undefined,
      pinnedMessageIds: new Set(),
      onTogglePin: () => undefined,
      onEditMessage: () => undefined,
    });
    expect(actions.map((a) => a.id)).toEqual([
      EDIT_MESSAGE_ACTION_ID,
      CREATE_TASK_MESSAGE_ACTION_ID,
      PIN_MESSAGE_ACTION_ID,
    ]);
  });

  it("resolveActions omite edit enquanto editing busy", () => {
    const actions = resolveInteractionMessageActions({
      message: {
        id: "m1",
        kind: "text",
        bodyText: "x",
        createdAtLabel: "",
        mine: true,
      },
      onCreateTask: () => undefined,
      onEditMessage: () => undefined,
      editingMessageId: "m1",
    });
    expect(actions.map((a) => a.id)).toEqual([CREATE_TASK_MESSAGE_ACTION_ID]);
  });

  it("resolveActions inclui create-task e pin juntos", () => {
    const actions = resolveInteractionMessageActions({
      message: {
        id: "m1",
        kind: "text",
        bodyText: "x",
        createdAtLabel: "",
      },
      onCreateTask: () => undefined,
      pinnedMessageIds: new Set(),
      onTogglePin: () => undefined,
    });
    expect(actions.map((a) => a.id)).toEqual([
      CREATE_TASK_MESSAGE_ACTION_ID,
      PIN_MESSAGE_ACTION_ID,
    ]);
  });
});
