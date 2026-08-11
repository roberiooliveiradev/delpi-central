import { useMemo, useRef, useState, type DragEvent, type KeyboardEvent } from "react";
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
  filterCollapsedSelectionRows,
  selectionTreeRowIsActive,
} from "../../utils/buildSelectionTreeRows";
import {
  membersOfGroup,
  renameGroupBlocks,
  resolveGroupDisplayName,
} from "../../utils/comunicadoGrouping";
import {
  attachListDragGhost,
  listDropHintClassName,
  resolveListDropEdge,
  type ListDropHint,
} from "../../utils/listReorderDrag";
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
    updateBlocksAtomically,
    toggleBlockHidden,
    setBlocksHidden,
    showAllBlocks,
    hideAllBlocks,
    bringForward,
    sendBackward,
  } = useComunicadoEditor();
  const [dragIds, setDragIds] = useState<string[] | null>(null);
  const [dropHint, setDropHint] = useState<ListDropHint | null>(null);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(() => new Set());
  const [renamingGroupId, setRenamingGroupId] = useState<string | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const renameInputRef = useRef<HTMLInputElement | null>(null);
  const isRibbon = layout === "ribbon";

  const treeRows = useMemo(() => buildSelectionTreeRows(blocks), [blocks]);

  const visibleRows = useMemo(
    () => filterCollapsedSelectionRows(treeRows, collapsedGroups),
    [collapsedGroups, treeRows],
  );

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

  function beginLayerDrag(event: DragEvent<HTMLElement>, ids: string[]) {
    setDragIds(ids);
    attachListDragGhost(event);
  }

  function updateLayerDropHint(event: DragEvent<HTMLElement>, targetId: string) {
    event.preventDefault();
    if (dragIds?.includes(targetId)) {
      setDropHint(null);
      return;
    }
    const edge = resolveListDropEdge(event.clientY, event.currentTarget.getBoundingClientRect());
    setDropHint((current) =>
      current?.id === targetId && current.edge === edge ? current : { id: targetId, edge },
    );
  }

  function onDrop(event: DragEvent<HTMLElement>, targetId: string) {
    event.preventDefault();
    const edge =
      dropHint?.id === targetId
        ? dropHint.edge
        : resolveListDropEdge(event.clientY, event.currentTarget.getBoundingClientRect());
    setDropHint(null);
    if (!dragIds || dragIds.length === 0 || dragIds.includes(targetId)) {
      setDragIds(null);
      return;
    }
    reorderBlockLayer(dragIds, targetId, edge);
    setDragIds(null);
  }

  function endLayerDrag() {
    setDragIds(null);
    setDropHint(null);
  }

  function applyBuildMap(map: Map<string, ComunicadoBlockAnimation[] | undefined>) {
    updateBlocksAtomically(
      [...map.entries()].map(([blockId, animations]) => ({
        blockId,
        patch: { animations },
      })),
    );
  }

  function toggleGroupCollapsed(groupId: string) {
    setCollapsedGroups((current) => {
      const next = new Set(current);
      if (next.has(groupId)) next.delete(groupId);
      else next.add(groupId);
      return next;
    });
  }

  function beginRenameGroup(groupId: string) {
    const members = membersOfGroup(blocks, groupId);
    setRenamingGroupId(groupId);
    setRenameDraft(resolveGroupDisplayName(members));
    requestAnimationFrame(() => renameInputRef.current?.select());
  }

  function commitRenameGroup() {
    if (!renamingGroupId) return;
    const groupId = renamingGroupId;
    const next = renameGroupBlocks(blocks, groupId, renameDraft);
    setRenamingGroupId(null);
    updateBlocksAtomically(
      membersOfGroup(next, groupId).map((member) => ({
        blockId: member.id,
        patch: { groupName: member.groupName },
      })),
    );
  }

  function onRenameKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault();
      commitRenameGroup();
    }
    if (event.key === "Escape") {
      event.preventDefault();
      setRenamingGroupId(null);
    }
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
              <span className="td-build-order__delay">
                {item.hasAnim ? `${item.delayMs} ms` : L.buildNoAnimation}
              </span>
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
        <ul
          className="td-layers-list td-layers-list--tree"
          onDragLeave={(event) => {
            const next = event.relatedTarget;
            if (next instanceof Node && event.currentTarget.contains(next)) return;
            setDropHint(null);
          }}
        >
          {visibleRows.map((row) => {
            if (row.kind === "group") {
              const active = selectionTreeRowIsActive(row, selectedIds);
              const members = membersOfGroup(blocks, row.groupId);
              const allHidden = members.length > 0 && members.every((m) => m.hidden === true);
              const collapsed = collapsedGroups.has(row.groupId);
              const displayName = resolveGroupDisplayName(members);
              const renaming = renamingGroupId === row.groupId;
              const dragging = Boolean(dragIds?.some((id) => row.memberIds.includes(id)));
              return (
                <li
                  key={`group:${row.groupId}`}
                  className={[
                    "td-layers-list__row",
                    "td-layers-list__row--group",
                    listDropHintClassName(dropHint, row.anchorId),
                    dragging ? "td-reorder--source" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  <button
                    type="button"
                    className="td-layers-list__twist"
                    aria-expanded={!collapsed}
                    aria-label={collapsed ? "Expandir grupo" : "Recolher grupo"}
                    title={collapsed ? "Expandir grupo" : "Recolher grupo"}
                    onClick={() => toggleGroupCollapsed(row.groupId)}
                  >
                    {collapsed ? (
                      <ChevronRight size={16} aria-hidden="true" />
                    ) : (
                      <ChevronDown size={16} aria-hidden="true" />
                    )}
                  </button>
                  <div
                    role="button"
                    tabIndex={0}
                    className={[
                      "td-layers-list__item",
                      "td-layers-list__item--group-node",
                      active ? "td-layers-list__item--active" : "",
                      dragging ? "td-layers-list__item--dragging" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    data-reorder-id={row.anchorId}
                    draggable={!renaming}
                    onDragStart={(event) => beginLayerDrag(event, row.memberIds)}
                    onDragOver={(event) => updateLayerDropHint(event, row.anchorId)}
                    onDrop={(event) => onDrop(event, row.anchorId)}
                    onDragEnd={endLayerDrag}
                    onClick={() => {
                      if (renaming) return;
                      selectBlocksByIds(row.memberIds, { keepPanelTab: true });
                    }}
                    onKeyDown={(event) => {
                      if (renaming) return;
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        selectBlocksByIds(row.memberIds, { keepPanelTab: true });
                      }
                      if (event.key === "F2") {
                        event.preventDefault();
                        beginRenameGroup(row.groupId);
                      }
                    }}
                    onDoubleClick={(event) => {
                      event.preventDefault();
                      event.stopPropagation();
                      beginRenameGroup(row.groupId);
                    }}
                    title="Selecionar grupo · duplo clique ou F2 para renomear"
                  >
                    <GripVertical size={16} className="td-layers-list__handle" aria-hidden="true" />
                    <FolderOpen size={14} className="td-layers-list__group-icon" aria-hidden="true" />
                    <span className="td-layers-list__meta">
                      {renaming ? (
                        <input
                          ref={renameInputRef}
                          className="td-layers-list__rename"
                          value={renameDraft}
                          aria-label="Renomear grupo"
                          onClick={(event) => event.stopPropagation()}
                          onChange={(event) => setRenameDraft(event.target.value)}
                          onBlur={commitRenameGroup}
                          onKeyDown={onRenameKeyDown}
                        />
                      ) : (
                        <span className="td-layers-list__type">{displayName}</span>
                      )}
                      <span className="td-layers-list__summary">
                        {row.memberIds.length} ·{" "}
                        {members.map((member) => comunicadoBlockTypeLabel(member.type)).join(" · ")}
                      </span>
                    </span>
                  </div>
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
            const dragging = Boolean(dragIds?.includes(block.id));
            return (
              <li
                key={block.id}
                className={[
                  "td-layers-list__row",
                  row.depth > 0 ? "td-layers-list__row--child" : "td-layers-list__row--root",
                  listDropHintClassName(dropHint, block.id),
                  dragging ? "td-reorder--source" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                {row.depth > 0 ? (
                  <span className="td-layers-list__tree-guide" aria-hidden="true" />
                ) : (
                  /* Reserva a mesma coluna do twist do grupo — alinhamento por nível. */
                  <span className="td-layers-list__twist-slot" aria-hidden="true" />
                )}
                <button
                  type="button"
                  className={[
                    "td-layers-list__item",
                    active ? "td-layers-list__item--active" : "",
                    row.depth > 0 ? "td-layers-list__item--child" : "",
                    userHidden ? "td-layers-list__item--user-hidden" : "",
                    dragging ? "td-layers-list__item--dragging" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  data-reorder-id={block.id}
                  draggable
                  onDragStart={(event) => beginLayerDrag(event, [block.id])}
                  onDragOver={(event) => updateLayerDropHint(event, block.id)}
                  onDrop={(event) => onDrop(event, block.id)}
                  onDragEnd={endLayerDrag}
                  onClick={(event) =>
                    selectBlock(block.id, {
                      additive: event.shiftKey,
                      expandGroup: false,
                      keepPanelTab: true,
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
        <button
          type="button"
          className="td-btn td-btn--sm"
          onClick={() => {
            const primaryId = selectedIds[selectedIds.length - 1];
            if (primaryId) selectBlocksByIds([primaryId], { keepPanelTab: true });
          }}
        >
          {L.focusPrimary}
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
