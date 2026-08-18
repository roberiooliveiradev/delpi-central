import { describe, expect, it, vi } from "vitest";

import {
  CREATE_TASK_MESSAGE_ACTION_ID,
  buildCreateTaskMessageAction,
  canCreateTaskFromMessage,
  resolveInteractionMessageActions,
} from "./messageThreadTaskAction";

describe("messageThreadTaskAction", () => {
  it("permite tarefa só em mensagens de texto ativas", () => {
    expect(canCreateTaskFromMessage({ kind: "text", deleted: false })).toBe(true);
    expect(canCreateTaskFromMessage({ kind: "system", deleted: false })).toBe(false);
    expect(canCreateTaskFromMessage({ kind: "task_ref", deleted: false })).toBe(false);
    expect(canCreateTaskFromMessage({ kind: "text", deleted: true })).toBe(false);
  });

  it("monta ação create-task sem botão local no kit", () => {
    const onCreateTask = vi.fn();
    const action = buildCreateTaskMessageAction({
      message: { id: "m1", kind: "text", deleted: false },
      onCreateTask,
    });
    expect(action?.id).toBe(CREATE_TASK_MESSAGE_ACTION_ID);
    action?.onClick();
    expect(onCreateTask).toHaveBeenCalledWith("m1");
  });

  it("resolveActions omite enquanto busy na mesma mensagem", () => {
    const actions = resolveInteractionMessageActions({
      message: {
        id: "m1",
        kind: "text",
        bodyText: "x",
        createdAtLabel: "",
      },
      onCreateTask: () => undefined,
      creatingMessageId: "m1",
    });
    expect(actions).toEqual([]);
  });
});
