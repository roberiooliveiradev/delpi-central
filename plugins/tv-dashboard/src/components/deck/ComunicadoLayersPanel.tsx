import { useMemo, useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Eye,
  EyeOff,
  FolderOpen,
  GripVertical,
} from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";
import {
  assignStaggeredEntranceDelays,
  clearEntranceAnimations,
  resolveBlockStageHideReason,
  resolveEntranceAnimation,
  sortBlocksByZIndex,
  syncEntranceDelaysSameInstant,
  type ComunicadoBlockAnimation,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  buildSelectionTreeRows,
  selectionTreeRowIsActive,
  type SelectionTreeRow,
} from "../../utils/buildSelectionTreeRows";
import { membersOfGroup } from "../../utils/comunicadoGrouping";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { comunicadoBlockSummary, comunicadoBlockTypeLabel } from "../../utils/comunicadoBlockLabels";
import { DeckPropertySection } from "./DeckPropertySection";

const L = TV_DASHBOARD_HELP_TOOLTIPS.layers;

type Props = {
  pane?: boolean;
  /** ribbon = grade full-width na top bar; pane = painel lateral. */
  layout?: "ribbon" | "pane";
};

export function ComunicadoLayersPanel({ pane = true, layout = "pane" }: Props) {
  const {
    blocks,
    selectedIds,
    selectBlock,
    selectBlocksByIds,
    reorderBlockLayer,
    updateBlock,
    toggleBlockHidden,
    setBlocksHidden,
    showAllBlocks,
    hideAllBlocks,
    bringForward,
    sendBackward,
  } = useComunicadoEditor();
  const [dragId, setDragId] = useState<string | null>(null);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(() => new Set());
  const isRibbon = layout === "ribbon";

  const treeRows = useMemo(() => buildSelectionTreeRows(blocks), [blocks]);

  const visibleRows = useMemo(() => {
    const rows: SelectionTreeRow[] = [];
    for (const row of treeRows) {
      if (row.kind === "block" && row.groupId && collapsedGroups.has(row.groupId)) {
        continue;
      }
      rows.push(row);
    }
    return rows;
  }, [collapsedGroups, treeRows]);

  const buildOrder = useMemo(
    () =>
      sortBlocksByZIndex(blocks).map((block) => ({
        id: block.id,
        label: comunicadoBlockSummary(block),
        type: comunicadoBlockTypeLabel(block.type),
        delayMs: resolveEntranceAnimation(block.animations)?.delayMs ?? 0,
        hasAnim: Boolean(resolveEntranceAnimation(block.animations)),
      })),
    [blocks],
  );

  function onDrop(targetId: string) {
    if (!dragId || dragId === targetId) return;
    const sorted = sortBlocksByZIndex(blocks);
    const targetIndex = sorted.findIndex((block) => block.id === targetId);
    if (targetIndex < 0) return;
    reorderBlockLayer(dragId, targetIndex);
    setDragId(null);
  }

  function applyBuildMap(map: Map<string, ComunicadoBlockAnimation[] | undefined>) {
    for (const [id, animations] of map.entries()) {
      updateBlock(id, { animations });
    }
  }

  function toggleGroupCollapsed(groupId: string) {
    setCollapsedGroups((current) => {
      const next = new Set(current);
      if (next.has(groupId)) next.delete(groupId);
      else next.add(groupId);
      return next;
    });
  }

  function toggleGroupHidden(groupId: string) {
    const members = membersOfGroup(blocks, groupId);
    if (members.length === 0) return;
    const allHidden = members.every((member) => member.hidden === true);
    setBlocksHidden(
      members.map((member) => member.id),
      !allHidden,
    );
  }

  const buildOrderSection = (
    <>
      {buildOrder.length === 0 ? (
        <p className="td-subtitle">Nenhum elemento no slide.</p>
      ) : (
        <ol className="td-build-order">
          {buildOrder.map((item, index) => (
            <li key={item.id} className="td-build-order__item">
              <span className="td-build-order__index">{index + 1}</span>
              <span className="td-build-order__meta">
                <span className="td-build-order__type">{item.type}</span>
                <span className="td-build-order__summary">{item.label}</span>
              </span>
              <span className="td-build-order__delay">{item.hasAnim ? `${item.delayMs} ms` : "—"}</span>
            </li>
          ))}
        </ol>
      )}
      <div className="td-build-order__actions">
        <HintAction hint={L.buildSequenciar} ariaLabel="Ajuda: Sequenciar">
          <button
            type="button"
            className="td-btn td-btn--sm"
            onClick={() =>
              applyBuildMap(
                assignStaggeredEntranceDelays(sortBlocksByZIndex(blocks), {
                  stepMs: 300,
                  preset: "fade",
                }),
              )
            }
          >
            Sequenciar
          </button>
        </HintAction>
        <HintAction hint={L.buildSameInstant} ariaLabel="Ajuda: Mesmo instante">
          <button
            type="button"
            className="td-btn td-btn--sm"
            onClick={() => applyBuildMap(syncEntranceDelaysSameInstant(sortBlocksByZIndex(blocks), 0))}
          >
            Mesmo instante
          </button>
        </HintAction>
        <HintAction hint={L.buildClear} ariaLabel="Ajuda: Limpar">
          <button
            type="button"
            className="td-btn td-btn--sm"
            onClick={() => applyBuildMap(clearEntranceAnimations(blocks))}
          >
            Limpar
          </button>
        </HintAction>
      </div>
    </>
  );

  const selectionToolbar = (
    <div className="td-layers-list__toolbar">
      <HintAction hint={L.showAll} ariaLabel="Ajuda: Mostrar tudo">
        <button type="button" className="td-btn td-btn--sm" onClick={showAllBlocks}>
          Mostrar tudo
        </button>
      </HintAction>
      <HintAction hint={L.hideAll} ariaLabel="Ajuda: Ocultar tudo">
        <button type="button" className="td-btn td-btn--sm" onClick={hideAllBlocks}>
          Ocultar tudo
        </button>
      </HintAction>
      <div className="td-layers-list__reorder">
        <HintAction hint={L.moveUp} ariaLabel="Ajuda: Avançar camada">
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--icon"
            disabled={selectedIds.length === 0}
            onClick={bringForward}
            aria-label="Avançar"
          >
            <ChevronUp size={16} aria-hidden="true" />
          </button>
        </HintAction>
        <HintAction hint={L.moveDown} ariaLabel="Ajuda: Recuar camada">
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--icon"
            disabled={selectedIds.length === 0}
            onClick={sendBackward}
            aria-label="Recuar"
          >
            <ChevronDown size={16} aria-hidden="true" />
          </button>
        </HintAction>
      </div>
    </div>
  );

  const layersSection = (
    <>
      {selectionToolbar}
      {visibleRows.length === 0 ? (
        <p className="td-subtitle">Nenhum elemento no slide.</p>
      ) : (
        <ul className="td-layers-list td-layers-list--tree">
          {visibleRows.map((row) => {
            if (row.kind === "group") {
              const active = selectionTreeRowIsActive(row, selectedIds);
              const members = membersOfGroup(blocks, row.groupId);
              const allHidden = members.length > 0 && members.every((m) => m.hidden === true);
              const collapsed = collapsedGroups.has(row.groupId);
              return (
                <li
                  key={`group:${row.groupId}`}
                  className="td-layers-list__row td-layers-list__row--group"
                >
                  <button
                    type="button"
                    className="td-layers-list__twist"
                    aria-label={collapsed ? "Expandir grupo" : "Recolher grupo"}
                    onClick={() => toggleGroupCollapsed(row.groupId)}
                  >
                    {collapsed ? (
                      <ChevronRight size={14} aria-hidden="true" />
                    ) : (
                      <ChevronDown size={14} aria-hidden="true" />
                    )}
                  </button>
                  <button
                    type="button"
                    className={[
                      "td-layers-list__item",
                      "td-layers-list__item--group-node",
                      active ? "td-layers-list__item--active" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    draggable
                    onDragStart={() => setDragId(row.anchorId)}
                    onDragOver={(event) => event.preventDefault()}
                    onDrop={() => onDrop(row.anchorId)}
                    onClick={() => selectBlocksByIds(row.memberIds)}
                    title="Selecionar grupo inteiro"
                  >
                    <GripVertical size={16} className="td-layers-list__handle" aria-hidden="true" />
                    <FolderOpen size={14} className="td-layers-list__group-icon" aria-hidden="true" />
                    <span className="td-layers-list__meta">
                      <span className="td-layers-list__type">Grupo · {row.memberIds.length}</span>
                      <span className="td-layers-list__summary">
                        {members.map((member) => comunicadoBlockTypeLabel(member.type)).join(" · ")}
                      </span>
                    </span>
                  </button>
                  <HintAction hint={L.toggleVisibility} ariaLabel="Ajuda: Visibilidade do grupo">
                    <button
                      type="button"
                      className="td-layers-list__eye"
                      aria-label={allHidden ? "Mostrar grupo" : "Ocultar grupo"}
                      onClick={(event) => {
                        event.stopPropagation();
                        toggleGroupHidden(row.groupId);
                      }}
                    >
                      {allHidden ? (
                        <EyeOff size={16} aria-hidden="true" />
                      ) : (
                        <Eye size={16} aria-hidden="true" />
                      )}
                    </button>
                  </HintAction>
                </li>
              );
            }

            const block = row.block;
            const active = selectedIds.includes(block.id);
            const hideReason = resolveBlockStageHideReason(block, blocks);
            const hiddenOnStage = hideReason != null;
            const userHidden = block.hidden === true;
            return (
              <li
                key={block.id}
                className={[
                  "td-layers-list__row",
                  row.depth > 0 ? "td-layers-list__row--child" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                style={row.depth > 0 ? { paddingLeft: 18 } : undefined}
              >
                {row.depth > 0 ? (
                  <span className="td-layers-list__tree-guide" aria-hidden="true" />
                ) : null}
                <button
                  type="button"
                  className={[
                    "td-layers-list__item",
                    active ? "td-layers-list__item--active" : "",
                    row.depth > 0 ? "td-layers-list__item--child" : "",
                    userHidden ? "td-layers-list__item--user-hidden" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  draggable
                  onDragStart={() => setDragId(block.id)}
                  onDragOver={(event) => event.preventDefault()}
                  onDrop={() => onDrop(block.id)}
                  onClick={(event) =>
                    selectBlock(block.id, {
                      additive: event.shiftKey,
                      expandGroup: false,
                    })
                  }
                  title={
                    hideReason === "linked_data_source"
                      ? "Oculta no palco (fonte vinculada) — seleção vai para o visual ligado"
                      : userHidden
                        ? "Oculto pelo usuário"
                        : row.depth > 0
                          ? "Membro do grupo — clique seleciona só este; Shift adiciona"
                          : undefined
                  }
                >
                  <GripVertical size={16} className="td-layers-list__handle" aria-hidden="true" />
                  <span className="td-layers-list__meta">
                    <span className="td-layers-list__type">
                      {comunicadoBlockTypeLabel(block.type)}
                      {hiddenOnStage ? " · oculto" : ""}
                    </span>
                    <span className="td-layers-list__summary">{comunicadoBlockSummary(block)}</span>
                  </span>
                </button>
                <HintAction hint={L.toggleVisibility} ariaLabel="Ajuda: Visibilidade">
                  <button
                    type="button"
                    className="td-layers-list__eye"
                    aria-label={userHidden ? "Mostrar elemento" : "Ocultar elemento"}
                    disabled={hideReason === "linked_data_source" && !userHidden}
                    onClick={(event) => {
                      event.stopPropagation();
                      toggleBlockHidden(block.id);
                    }}
                  >
                    {userHidden || hiddenOnStage ? (
                      <EyeOff size={16} strokeWidth={2.25} aria-hidden="true" />
                    ) : (
                      <Eye size={16} strokeWidth={2.25} aria-hidden="true" />
                    )}
                  </button>
                </HintAction>
              </li>
            );
          })}
        </ul>
      )}
      {selectedIds.length > 1 ? (
        <button type="button" className="td-btn td-btn--sm" onClick={() => selectBlocksByIds([selectedIds[0]!])}>
          Focar primeiro selecionado
        </button>
      ) : null}
    </>
  );

  if (isRibbon) {
    return (
      <div className="td-deck-ribbon__panel td-deck-ribbon__panel--layers">
        <div className="td-deck-ribbon__panel-zone">
          <h4 className="td-deck-ribbon__panel-zone-title">Ordem de construção</h4>
          {buildOrderSection}
        </div>
        <div className="td-deck-ribbon__panel-zone">
          <h4 className="td-deck-ribbon__panel-zone-title">{L.panelTitle}</h4>
          {layersSection}
        </div>
      </div>
    );
  }

  return (
    <>
      <DeckPropertySection pane={pane} title="Ordem de construção" hint={L.buildOrder} defaultOpen>
        {buildOrderSection}
      </DeckPropertySection>

      <DeckPropertySection pane={pane} title={L.panelTitle} hint={L.list} defaultOpen>
        {layersSection}
      </DeckPropertySection>
    </>
  );
}
