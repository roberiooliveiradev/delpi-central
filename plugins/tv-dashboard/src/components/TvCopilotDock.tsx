import { ChevronLeft, Sparkles, X } from "lucide-react";
import { FormatPaneShell } from "@delpi/plugin-ui/index";
import { useEffect, useLayoutEffect, useRef, type CSSProperties } from "react";

import type { BranchScope } from "../api/tvDashboardApi";
import { useOptionalTvCopilotDock } from "../context/tvCopilotDockContext";
import { useDeckSidePanelLayout } from "../hooks/useDeckSidePanelLayout";
import { TV_COPILOT_CONTENT as C } from "../content/tvCopilotContent";
import { TvCopilotSidePanelSuspense } from "./TvCopilotSidePanel";

type Props = {
  playlistId: string;
  slideId?: string | null;
  branchScope?: BranchScope | null;
};

/**
 * Slot do workspace: só monta a coluna quando o dock está visível
 * (evita `--with-copilot` com painel vazio).
 */
export function TvCopilotDockSlot(props: Props) {
  const dock = useOptionalTvCopilotDock();
  if (!dock?.visible) return null;
  return <TvCopilotDock {...props} />;
}

/**
 * Sidebar do Copiloto IA — colapsável (rail) ou fechável (sem rail).
 * Acesso pela aba «Copiloto» na top bar.
 */
export function TvCopilotDock({ playlistId, slideId = null, branchScope = null }: Props) {
  const dock = useOptionalTvCopilotDock();
  const { collapsed, setCollapsed, startResize, panelWidthPx, limits, width } =
    useDeckSidePanelLayout("copilot", { growDirection: "west" });
  const open = !collapsed;
  const asideRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!dock?.visible) return;
    if (dock.expandToken > 0) setCollapsed(false);
  }, [dock?.expandToken, dock?.visible, setCollapsed]);

  useLayoutEffect(() => {
    const slot = asideRef.current?.closest(".td-deck-copilot-slot");
    if (!(slot instanceof HTMLElement)) return;
    if (dock?.visible && open) {
      slot.style.setProperty("--td-copilot-panel-width", `${width}px`);
    } else {
      slot.style.removeProperty("--td-copilot-panel-width");
    }
  }, [dock?.visible, open, width]);

  if (!dock?.visible) return null;

  const panelStyle = {
    "--td-side-panel-width": `${open ? width : panelWidthPx}px`,
  } as CSSProperties;

  return (
    <aside
      ref={asideRef}
      className={[
        "td-deck-side-panel",
        "td-deck-side-panel--stage",
        "td-tv-copilot-dock",
        open ? "td-deck-side-panel--open" : "td-deck-side-panel--collapsed",
      ].join(" ")}
      style={panelStyle}
      aria-label={C.panelTitle}
      data-delpi-ui-density="compact"
    >
      {open ? (
        <>
          <div
            className="td-deck-panel-resize td-deck-panel-resize--west"
            role="separator"
            aria-orientation="vertical"
            aria-label="Redimensionar Copiloto IA"
            aria-valuenow={width}
            aria-valuemin={limits.minWidth}
            aria-valuemax={limits.maxWidth}
            onPointerDown={startResize}
          />
          <FormatPaneShell
            className="td-deck-side-panel__pane"
            title={C.panelTitle}
            closeLabel={C.collapseLabel}
            onClose={() => setCollapsed(true)}
            bodyClassName="td-deck-side-panel__pane-body td-tv-copilot-dock__body"
            density="compact"
          >
            <TvCopilotSidePanelSuspense
              playlistId={playlistId}
              slideId={slideId}
              branchScope={branchScope}
            />
          </FormatPaneShell>
        </>
      ) : (
        <div className="td-deck-side-panel__collapsed-rail">
          <button
            type="button"
            className="td-deck-side-panel__reopen"
            onClick={() => setCollapsed(false)}
            aria-label={C.expandLabel}
            title={C.expandLabel}
          >
            <ChevronLeft size={18} aria-hidden="true" />
          </button>
          <button
            type="button"
            className="td-deck-side-panel__rail-btn td-deck-side-panel__rail-btn--active"
            onClick={() => setCollapsed(false)}
            aria-label={C.panelTitle}
            title={C.panelTitle}
          >
            <Sparkles size={16} aria-hidden="true" />
          </button>
          <button
            type="button"
            className="td-deck-side-panel__rail-btn"
            onClick={() => dock.closeDock()}
            aria-label={C.closeLabel}
            title={C.closeLabel}
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>
      )}
    </aside>
  );
}
