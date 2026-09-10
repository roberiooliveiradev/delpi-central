/**
 * Pure Admin Hub layer transitions — single source of exclusivity + URL policy.
 * Ephemeral DOM anchors stay outside this state (managed by the page/hook).
 */

import {
  INITIAL_ADMIN_HUB_UI,
  type AdminEntityRef,
  type AdminHubConfirmKind,
  type AdminHubModal,
  type AdminHubPanel,
  type AdminHubUiState,
} from "./adminHubUiState";

export type AdminHubUrlSlice = {
  entity: string | null;
  panel: AdminHubPanel | null;
  modal: AdminHubModal | null;
};

export type AdminHubTransitionResult = {
  state: AdminHubUiState;
  /** When true, caller should replace URL from `urlSlice`. */
  syncUrl: boolean;
  urlSlice: AdminHubUrlSlice;
  /** Clear ephemeral anchorEl / rebind after graph. */
  clearAnchor: boolean;
  /** Node id for resolveAnchor when opening summary/menu. */
  popoverNodeId: string | null;
};

export type AdminHubAction =
  | {
      type: "openSummary";
      entity: AdminEntityRef;
      popoverNodeId: string;
    }
  | {
      type: "openEntityMenu";
      entity: AdminEntityRef;
      popoverNodeId: string;
    }
  | { type: "closeTransient" }
  | { type: "closeSummary" }
  | { type: "closeEntityMenu" }
  | { type: "openPanel"; panel: AdminHubPanel }
  | { type: "closePanel" }
  | {
      type: "openModal";
      modal: AdminHubModal;
      entity?: AdminEntityRef | null;
      /** When true, keep previous panel in state for explicit restore. */
      preservePanel?: boolean;
    }
  | { type: "closeModal"; restorePanel?: boolean }
  | {
      type: "openConfirm";
      kind: AdminHubConfirmKind;
      id: string;
    }
  | { type: "closeConfirm" }
  | { type: "closeAll" }
  | {
      type: "hydrateFromUrl";
      entity: AdminEntityRef | null;
      panel: AdminHubPanel | null;
      modal: AdminHubModal | null;
    }
  | { type: "graphReloading" }
  | { type: "openInspector" }
  | { type: "setFilters"; filters: AdminHubUiState["filters"] };

function formatEntity(entity: AdminEntityRef | null): string | null {
  if (!entity) return null;
  return `${entity.type}:${entity.id}`;
}

function urlFromState(state: AdminHubUiState): AdminHubUrlSlice {
  const layer = state.openLayer;
  const shareEntity =
    layer === "summary" ||
    layer === "menu" ||
    layer === "modal" ||
    layer === "confirm" ||
    layer === "inspector" ||
    (layer === "panel" && state.selectedEntity != null);

  // Popovers are ephemeral: do not keep entity in URL for summary/menu alone.
  // Shareable deep-links: modal (+ entity when relevant), panel.
  let entity: string | null = null;
  if (layer === "modal" || layer === "confirm" || layer === "inspector") {
    entity = formatEntity(state.selectedEntity);
  } else if (layer === "panel") {
    entity = null;
  }
  // summary/menu: entity intentionally omitted from URL (H2)

  void shareEntity;

  return {
    entity,
    panel: layer === "panel" ? state.panel : layer === "modal" ? null : state.panel,
    modal: layer === "modal" ? state.modal : null,
  };
}

function result(
  state: AdminHubUiState,
  opts: {
    syncUrl?: boolean;
    clearAnchor?: boolean;
    popoverNodeId?: string | null;
    urlOverride?: AdminHubUrlSlice;
  } = {},
): AdminHubTransitionResult {
  const urlSlice = opts.urlOverride ?? urlFromState(state);
  return {
    state,
    syncUrl: opts.syncUrl ?? true,
    urlSlice,
    clearAnchor: opts.clearAnchor ?? false,
    popoverNodeId: opts.popoverNodeId ?? state.popoverAnchorId,
  };
}

/**
 * Apply exclusive layer transition.
 */
export function transitionAdminHub(
  current: AdminHubUiState,
  action: AdminHubAction,
): AdminHubTransitionResult {
  switch (action.type) {
    case "openSummary": {
      const state: AdminHubUiState = {
        ...current,
        selectedEntity: action.entity,
        openLayer: "summary",
        popoverAnchorId: action.popoverNodeId,
        panel: null,
        modal: null,
        confirm: null,
      };
      return result(state, {
        syncUrl: true,
        clearAnchor: false,
        popoverNodeId: action.popoverNodeId,
        urlOverride: { entity: null, panel: null, modal: null },
      });
    }
    case "openEntityMenu": {
      const state: AdminHubUiState = {
        ...current,
        selectedEntity: action.entity,
        openLayer: "menu",
        popoverAnchorId: action.popoverNodeId,
        modal: null,
        confirm: null,
        // keep panel? plan: exclusive — close conflicting modal; panel closed for canvas focus
        panel: null,
      };
      return result(state, {
        syncUrl: true,
        popoverNodeId: action.popoverNodeId,
        urlOverride: { entity: null, panel: null, modal: null },
      });
    }
    case "closeSummary":
    case "closeEntityMenu":
    case "closeTransient": {
      const state: AdminHubUiState = {
        ...current,
        openLayer: current.panel ? "panel" : "none",
        selectedEntity: current.panel ? current.selectedEntity : null,
        popoverAnchorId: null,
        confirm: null,
      };
      return result(state, {
        clearAnchor: true,
        popoverNodeId: null,
        urlOverride: {
          entity: null,
          panel: state.panel,
          modal: null,
        },
      });
    }
    case "openPanel": {
      const state: AdminHubUiState = {
        ...current,
        panel: action.panel,
        openLayer: "panel",
        modal: null,
        confirm: null,
        selectedEntity: null,
        popoverAnchorId: null,
      };
      return result(state, {
        clearAnchor: true,
        popoverNodeId: null,
        urlOverride: { entity: null, panel: action.panel, modal: null },
      });
    }
    case "closePanel": {
      const state: AdminHubUiState = {
        ...current,
        panel: null,
        openLayer: "none",
        popoverAnchorId: null,
      };
      return result(state, {
        clearAnchor: true,
        urlOverride: { entity: null, panel: null, modal: null },
      });
    }
    case "openModal": {
      const nextEntity =
        action.entity === undefined ? current.selectedEntity : action.entity;
      const state: AdminHubUiState = {
        ...current,
        modal: action.modal,
        openLayer: "modal",
        panel: action.preservePanel ? current.panel : null,
        confirm: null,
        selectedEntity: nextEntity,
        popoverAnchorId: null,
      };
      return result(state, {
        clearAnchor: true,
        popoverNodeId: null,
        urlOverride: {
          entity: formatEntity(nextEntity),
          panel: null,
          modal: action.modal,
        },
      });
    }
    case "closeModal": {
      const restore = Boolean(action.restorePanel && current.panel);
      const state: AdminHubUiState = {
        ...current,
        modal: null,
        openLayer: restore ? "panel" : "none",
        selectedEntity: restore ? current.selectedEntity : null,
        popoverAnchorId: null,
        confirm: null,
        panel: restore ? current.panel : null,
      };
      return result(state, {
        clearAnchor: true,
        urlOverride: {
          entity: null,
          panel: state.panel,
          modal: null,
        },
      });
    }
    case "openConfirm": {
      const state: AdminHubUiState = {
        ...current,
        confirm: { kind: action.kind, id: action.id },
        openLayer: "confirm",
        // keep modal/panel context in fields but layer is confirm
        popoverAnchorId: null,
      };
      return result(state, {
        clearAnchor: true,
        // confirm is ephemeral — do not put confirm in URL; keep modal if was open for restore
        syncUrl: true,
        urlOverride: {
          entity: formatEntity(current.selectedEntity),
          panel: null,
          modal: current.modal,
        },
      });
    }
    case "closeConfirm": {
      const backToModal = current.modal != null;
      const state: AdminHubUiState = {
        ...current,
        confirm: null,
        openLayer: backToModal ? "modal" : current.panel ? "panel" : "none",
      };
      return result(state, {
        urlOverride: {
          entity: backToModal ? formatEntity(current.selectedEntity) : null,
          panel: backToModal ? null : current.panel,
          modal: backToModal ? current.modal : null,
        },
      });
    }
    case "closeAll": {
      const state: AdminHubUiState = {
        ...INITIAL_ADMIN_HUB_UI,
        filters: current.filters,
      };
      return result(state, {
        clearAnchor: true,
        popoverNodeId: null,
        urlOverride: { entity: null, panel: null, modal: null },
      });
    }
    case "hydrateFromUrl": {
      // Never force summary from entity alone (H2). Persist only panel/modal.
      // Confirm is ephemeral and must survive URL projections that still carry modal=.
      if (current.openLayer === "confirm") {
        return result(current, { syncUrl: false, clearAnchor: false });
      }
      if (current.openLayer === "summary" || current.openLayer === "menu") {
        // URL hydrate must not reopen/clobber ephemeral popovers unless modal/panel arrived.
        if (!action.modal && !action.panel) {
          return result(current, { syncUrl: false, clearAnchor: false });
        }
      }
      let openLayer = current.openLayer;
      let selectedEntity = current.selectedEntity;
      let panel = current.panel;
      let modal = current.modal;
      let clearAnchor = false;

      if (action.modal) {
        openLayer = "modal";
        modal = action.modal;
        panel = null;
        selectedEntity = action.entity ?? selectedEntity;
        clearAnchor = true;
      } else if (action.panel) {
        openLayer = "panel";
        panel = action.panel;
        modal = null;
        selectedEntity = null;
        clearAnchor = true;
      } else if (
        current.openLayer !== "summary" &&
        current.openLayer !== "menu" &&
        current.openLayer !== "inspector"
      ) {
        openLayer = "none";
        modal = null;
        panel = null;
      }

      const state: AdminHubUiState = {
        ...current,
        selectedEntity,
        panel,
        modal,
        openLayer,
        popoverAnchorId: clearAnchor ? null : current.popoverAnchorId,
        // confirm already short-circuited above when openLayer was confirm
        confirm: null,
      };
      return result(state, { syncUrl: false, clearAnchor });
    }
    case "graphReloading": {
      // H1: drop dead DOM anchors while canvas unmounts; clear ephemeral layers.
      if (current.openLayer === "summary" || current.openLayer === "menu") {
        const state: AdminHubUiState = {
          ...current,
          openLayer: "none",
          selectedEntity: null,
          popoverAnchorId: null,
        };
        return result(state, {
          clearAnchor: true,
          syncUrl: true,
          urlOverride: {
            entity: null,
            panel: current.panel,
            modal: current.modal,
          },
        });
      }
      return result(current, { clearAnchor: true, syncUrl: false });
    }
    case "openInspector": {
      const state: AdminHubUiState = {
        ...current,
        openLayer: "inspector",
        modal: null,
        confirm: null,
        panel: null,
        popoverAnchorId: null,
      };
      return result(state, {
        clearAnchor: true,
        urlOverride: {
          entity: formatEntity(current.selectedEntity),
          panel: null,
          modal: null,
        },
      });
    }
    case "setFilters": {
      return result({ ...current, filters: action.filters }, { syncUrl: false });
    }
    default: {
      const _exhaustive: never = action;
      void _exhaustive;
      return result(current, { syncUrl: false });
    }
  }
}

/** Whether an operational error notice may alter layers — always false. */
export function noticeAffectsLayers(): boolean {
  return false;
}
