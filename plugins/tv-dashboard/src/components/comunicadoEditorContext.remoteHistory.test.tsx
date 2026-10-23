import { act, cleanup, render } from "@testing-library/react";
import { useEffect } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ComunicadoEditorProvider } from "./comunicadoEditorContext";
import {
  useComunicadoEditor,
  type ComunicadoEditorContextValue,
} from "./comunicadoEditorContextCore";

vi.mock("../api/tvDashboardApi", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("../api/tvDashboardApi")>();
  return {
    ...actual,
    applyPresentationMutations: vi.fn(),
  };
});

function makeValue(notes?: string): Record<string, unknown> {
  return {
    version: 2,
    blocks: [],
    ...(notes ? { speakerNotes: notes } : {}),
  };
}

let capturedApi: ComunicadoEditorContextValue | null = null;
function Probe() {
  const api = useComunicadoEditor();
  useEffect(() => {
    capturedApi = api;
  });
  return null;
}

const onChangeSpy = vi.fn();

function Harness({
  value,
  remoteRevision = 0,
  foreignRemoteRevision = 0,
}: {
  value: Record<string, unknown>;
  remoteRevision?: number;
  foreignRemoteRevision?: number;
}) {
  return (
    <ComunicadoEditorProvider
      playlistId="pl-1"
      slideId="s1"
      value={value}
      remoteRevision={remoteRevision}
      foreignRemoteRevision={foreignRemoteRevision}
      onChange={(next) => onChangeSpy(next)}
    >
      <Probe />
    </ComunicadoEditorProvider>
  );
}

function api(): ComunicadoEditorContextValue {
  if (!capturedApi) throw new Error("context unavailable");
  return capturedApi;
}

afterEach(() => {
  cleanup();
  capturedApi = null;
  onChangeSpy.mockReset();
});

describe("undo/redo local diante de baseline externa (VISTA-TV-023)", () => {
  it("atualização remota estrangeira invalida a pilha — undo não reverte o remoto", () => {
    const initial = render(<Harness value={makeValue()} />);

    // Edição local confirmada → entra na pilha de undo.
    act(() => api().setSpeakerNotes("nota local"));
    const localEmit = onChangeSpy.mock.calls.at(-1)?.[0] as Record<string, unknown>;
    initial.rerender(<Harness value={localEmit} />);
    expect(api().canUndo).toBe(true);

    // Baseline estrangeira (outro editor/copiloto): remoteRevision + foreignRemoteRevision.
    initial.rerender(
      <Harness
        value={makeValue("nota do peer")}
        remoteRevision={1}
        foreignRemoteRevision={1}
      />,
    );

    expect(api().canUndo).toBe(false);
    act(() => api().undo());
    // Undo virou no-op — a alteração remota permanece como estado vigente.
    expect(api().config.speakerNotes).toBe("nota do peer");
    initial.unmount();
  });

  it("ack da própria escrita (sem foreignRemoteRevision) preserva a pilha", () => {
    const initial = render(<Harness value={makeValue()} />);

    act(() => api().setSpeakerNotes("nota local"));
    const localEmit = onChangeSpy.mock.calls.at(-1)?.[0] as Record<string, unknown>;
    initial.rerender(<Harness value={localEmit} />);
    expect(api().canUndo).toBe(true);

    // Read-back do servidor pode normalizar o config — ainda assim é ack próprio:
    // remoteRevision sobe, foreignRemoteRevision não.
    initial.rerender(
      <Harness value={makeValue("nota local normalizada")} remoteRevision={1} />,
    );

    expect(api().canUndo).toBe(true);
    act(() => api().undo());
    expect(api().config.speakerNotes).toBeUndefined();
    initial.unmount();
  });

  it("redo também é invalidado — futuro não sobrescreve baseline remota", () => {
    const initial = render(<Harness value={makeValue()} />);

    act(() => api().setSpeakerNotes("nota local"));
    const localEmit = onChangeSpy.mock.calls.at(-1)?.[0] as Record<string, unknown>;
    initial.rerender(<Harness value={localEmit} />);
    act(() => api().undo());
    const undoEmit = onChangeSpy.mock.calls.at(-1)?.[0] as Record<string, unknown>;
    initial.rerender(<Harness value={undoEmit} />);
    expect(api().canRedo).toBe(true);

    initial.rerender(
      <Harness
        value={makeValue("nota do peer")}
        remoteRevision={1}
        foreignRemoteRevision={1}
      />,
    );

    expect(api().canRedo).toBe(false);
    act(() => api().redo());
    expect(api().config.speakerNotes).toBe("nota do peer");
    initial.unmount();
  });

  it("edição local após baseline remota volta a empilhar normalmente", () => {
    const initial = render(<Harness value={makeValue()} />);
    initial.rerender(
      <Harness
        value={makeValue("baseline remota")}
        remoteRevision={1}
        foreignRemoteRevision={1}
      />,
    );
    expect(api().canUndo).toBe(false);

    act(() => api().setSpeakerNotes("minha edição pós-remota"));
    const emit = onChangeSpy.mock.calls.at(-1)?.[0] as Record<string, unknown>;
    initial.rerender(<Harness value={emit} remoteRevision={1} foreignRemoteRevision={1} />);
    expect(api().canUndo).toBe(true);

    act(() => api().undo());
    expect(api().config.speakerNotes).toBe("baseline remota");
    initial.unmount();
  });
});
