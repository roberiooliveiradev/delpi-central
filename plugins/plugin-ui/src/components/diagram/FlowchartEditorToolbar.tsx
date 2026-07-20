import { Boxes, CircleHelp, LayoutTemplate, type LucideIcon } from "lucide-react";
import { useMemo, useState } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { TabHintCell } from "../help/TabHintCell";
import type { FlowchartEditorLabels } from "./types/flowchartEditorLabels";
import type { BpmnPaletteCategoryId } from "./types/bpmnNodeCatalog";
import type { FlowchartLane, FlowchartNodeType } from "./types/diagram";
import { DiagramEditorToolbarButton } from "./DiagramEditorToolbarButton";
import { FlowchartEditorHistoryActions } from "./FlowchartEditorHistoryActions";
import { FlowchartLaneToolbar } from "./FlowchartLaneToolbar";
import {
  diagramEditorAddLaneAction,
  diagramEditorLayoutActions,
  FLOWCHART_NODE_ICONS,
  flowchartElementGroupTabs,
  flowchartEventSubTabs,
  flowchartNodeHint,
  paletteByCategory,
  resolvePaletteCategory,
  type DiagramEditorAction,
  type FlowchartElementGroupTab,
} from "./flowchartEditorToolbar";

export type FlowchartEditorToolbarTab = "elements" | "models";

type Props = {
  labels: FlowchartEditorLabels;
  toolbarTab: FlowchartEditorToolbarTab;
  onToolbarTabChange: (tab: FlowchartEditorToolbarTab) => void;
  lanes: FlowchartLane[];
  activeLaneId?: string;
  onActiveLaneChange: (laneId: string) => void;
  onAddNode: (type: FlowchartNodeType) => void;
  onEditorAction: (actionId: DiagramEditorAction["id"]) => void;
  canUndo?: boolean;
  canRedo?: boolean;
  onUndo?: () => void;
  onRedo?: () => void;
};

function PaletteSubTabs<T extends string>({
  tabs,
  activeId,
  onChange,
  ariaLabel,
  compact,
}: {
  tabs: Array<{ id: T; label: string; hint?: string; icon?: LucideIcon }>;
  activeId: T;
  onChange: (id: T) => void;
  ariaLabel: string;
  compact?: boolean;
}) {
  return (
    <div
      className={[
        "tm-diagram-editor__palette-subtabs",
        compact ? "tm-diagram-editor__palette-subtabs--compact" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="tablist"
      aria-label={ariaLabel}
    >
      {tabs.map((tab) => {
        const Icon = tab.icon;
        return (
          <TabHintCell
            key={tab.id}
            label={tab.label}
            hint={tab.hint ?? tab.label}
            icon={Icon}
            active={activeId === tab.id}
            onSelect={() => onChange(tab.id)}
            cellClassName="tm-diagram-editor__palette-subtab-cell"
            tabClassName={
              activeId === tab.id
                ? "tm-diagram-editor__palette-subtab is-active"
                : "tm-diagram-editor__palette-subtab"
            }
            tabActiveClassName="is-active"
            hintPlacement="bottom"
          />
        );
      })}
    </div>
  );
}

export function FlowchartEditorToolbar({
  labels,
  toolbarTab,
  onToolbarTabChange,
  lanes,
  activeLaneId,
  onActiveLaneChange,
  onAddNode,
  onEditorAction,
  canUndo = false,
  canRedo = false,
  onUndo,
  onRedo,
}: Props) {
  const addLaneAction = diagramEditorAddLaneAction(labels);
  const layoutActions = useMemo(() => diagramEditorLayoutActions(labels), [labels]);
  const elementGroupTabs = useMemo(() => flowchartElementGroupTabs(labels), [labels]);
  const eventSubTabs = useMemo(() => flowchartEventSubTabs(labels), [labels]);
  const toolbarTabs = useMemo(
    () => [
      {
        id: "elements" as const,
        label: labels.toolbarElementsTab,
        hint: labels.toolbarElementsTabHint,
        icon: Boxes,
      },
      {
        id: "models" as const,
        label: labels.toolbarModelsTab,
        hint: labels.toolbarModelsTabHint,
        icon: LayoutTemplate,
      },
    ],
    [labels],
  );

  const [elementGroup, setElementGroup] = useState<FlowchartElementGroupTab>("events");
  const [eventSubTab, setEventSubTab] = useState<BpmnPaletteCategoryId>("events_start");

  const activeCategory = resolvePaletteCategory(elementGroup, eventSubTab);
  const paletteItems = activeCategory ? paletteByCategory(activeCategory) : [];

  return (
    <div className="tm-diagram-editor__toolbar-overlay" role="toolbar" aria-label={labels.toolbarAriaLabel}>
      <div className="tm-diagram-editor__toolbar-head">
        {onUndo && onRedo ? (
          <FlowchartEditorHistoryActions
            labels={labels}
            canUndo={canUndo}
            canRedo={canRedo}
            onUndo={onUndo}
            onRedo={onRedo}
          />
        ) : null}
        <div className="tm-diagram-editor__toolbar-tabs" role="tablist" aria-label={labels.toolbarGroupsAriaLabel}>
          {toolbarTabs.map((tab) => (
            <TabHintCell
              key={tab.id}
              label={tab.label}
              hint={tab.hint}
              icon={tab.icon}
              active={toolbarTab === tab.id}
              onSelect={() => onToolbarTabChange(tab.id)}
              cellClassName="tm-diagram-editor__toolbar-tab-cell"
              tabClassName="tm-diagram-editor__toolbar-tab"
              tabActiveClassName="is-active"
              hintPlacement="bottom"
            />
          ))}
        </div>
        <HelpTooltip
          content={labels.usoGeral}
          ariaLabel={labels.toolbarHowToUseAriaLabel}
          wrap
          placement="bottom"
          className="tm-diagram-editor__hint-wrap"
        >
          <button type="button" className="tm-diagram-editor__hint-link tm-diagram-editor__toolbar-help">
            <CircleHelp size={14} aria-hidden="true" />
            <span>{labels.toolbarHowToUse}</span>
          </button>
        </HelpTooltip>
      </div>

      <div className="tm-diagram-editor__toolbar-panel" role="tabpanel">
        {toolbarTab === "elements" ? (
          <div className="tm-diagram-editor__elements">
            <PaletteSubTabs<FlowchartElementGroupTab>
              tabs={elementGroupTabs}
              activeId={elementGroup}
              onChange={setElementGroup}
              ariaLabel={labels.paletteCategoriesAriaLabel}
            />

            {elementGroup === "events" ? (
              <PaletteSubTabs<BpmnPaletteCategoryId>
                tabs={eventSubTabs}
                activeId={eventSubTab}
                onChange={setEventSubTab}
                ariaLabel={labels.paletteEventsAriaLabel}
                compact
              />
            ) : null}

            {elementGroup === "lanes" ? (
              <div className="tm-diagram-editor__elements-lanes tm-diagram-editor__elements-lanes--panel">
                <DiagramEditorToolbarButton
                  label={addLaneAction.label}
                  hint={addLaneAction.hint}
                  icon={addLaneAction.icon}
                  onClick={() => onEditorAction("addLane")}
                />
                {lanes.length ? (
                  <FlowchartLaneToolbar
                    labels={labels}
                    lanes={lanes}
                    activeLaneId={activeLaneId}
                    onActiveLaneChange={onActiveLaneChange}
                  />
                ) : null}
              </div>
            ) : (
              <div className="tm-diagram-editor__palette">
                {paletteItems.map((item) => {
                  const Icon = FLOWCHART_NODE_ICONS[item.type];
                  return (
                    <DiagramEditorToolbarButton
                      key={item.type}
                      label={item.label}
                      hint={flowchartNodeHint(item.type, labels)}
                      icon={Icon}
                      onClick={() => onAddNode(item.type)}
                    />
                  );
                })}
              </div>
            )}
          </div>
        ) : null}

        {toolbarTab === "models" ? (
          <div className="tm-diagram-editor__templates">
            {layoutActions.map((action) => (
              <DiagramEditorToolbarButton
                key={action.id}
                label={action.label}
                hint={action.hint}
                icon={action.icon}
                onClick={() => onEditorAction(action.id)}
              />
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
