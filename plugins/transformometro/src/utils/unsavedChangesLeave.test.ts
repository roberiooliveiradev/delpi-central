import { describe, expect, it, vi } from "vitest";

import { resolveUnsavedLeave } from "./unsavedChangesLeave";

describe("resolveUnsavedLeave", () => {
  it("descarta sem perguntar quando edição limpa", async () => {
    const discard = vi.fn();
    const ok = await resolveUnsavedLeave(
      [
        {
          isEditing: () => true,
          isDirty: () => false,
          save: async () => undefined,
          discard,
        },
      ],
      async () => "cancel",
    );
    expect(ok).toBe(true);
    expect(discard).toHaveBeenCalledTimes(1);
  });

  it("salva dirty e libera edição", async () => {
    let editing = true;
    const save = vi.fn(async () => {
      editing = false;
    });
    const discard = vi.fn(() => {
      editing = false;
    });
    const ok = await resolveUnsavedLeave(
      [
        {
          isEditing: () => editing,
          isDirty: () => true,
          save,
          discard,
        },
      ],
      async () => "secondary",
    );
    expect(ok).toBe(true);
    expect(save).toHaveBeenCalledTimes(1);
  });

  it("permanece na tela ao cancelar o diálogo", async () => {
    const discard = vi.fn();
    const ok = await resolveUnsavedLeave(
      [
        {
          isEditing: () => true,
          isDirty: () => true,
          save: async () => undefined,
          discard,
        },
      ],
      async () => "cancel",
    );
    expect(ok).toBe(false);
    expect(discard).not.toHaveBeenCalled();
  });
});
