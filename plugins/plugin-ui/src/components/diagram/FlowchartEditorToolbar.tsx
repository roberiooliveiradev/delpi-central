import { CircleHelp } from "lucide-react";
import { useMemo, useState } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import type { FlowchartEditorLabels } from "./types/flowchartEditorLabels";
import type { BpmnPaletteCategoryId } from "./types/bpmnNodeCatalog";
import type { FlowchartLane, FlowchartNodeType } from "./types/diagram";
import { DiagramEditorToolbarButton } from "./DiagramEditorToolbarButton";
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
};

function PaletteSubTabs<T extends string>({
  tabs,
  activeId,
  onChange,
  ariaLabel,
  compact,
}: {
  tabs: Array<{ id: T; label: string }>;
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
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={activeId === tab.id}
          className={
            activeId === tab.id
              ? "tm-diagram-editor__palette-subtab is-active"
              : "tm-diagram-editor__palette-subtab"
          }
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
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
}: Props) {
  const addLaneAction = diagramEditorAddLaneAction(labels);
  const layoutActions = useMemo(() => diagramEditorLayoutActions(labels), [labels]);
  const elementGroupTabs = useMemo(() => flowchartElementGroupTabs(labels), [labels]);
  const eventSubTabs = useMemo(() => flowchartEventSubTabs(labels), [labels]);
  const toolbarTabs = useMemo(
    () => [
      { id: "elements" as const, label: labels.toolbarElementsTab },
      { id: "models" as const, label: labels.toolbarModelsTab },
    ],
    [labels.toolbarElementsTab, labels.toolbarModelsTab]
  );

  const [elementGroup, setElementGroup] = useState<FlowchartElementGroupTab>("events");
  const [eventSubTab, setEventSubTab] = useState<BpmnPaletteCategoryId>("events_start");

  const activeCategory = resolvePaletteCategory(elementGroup, eventSubTab);
  const paletteItems = activeCategory ? paletteByCategory(activeCategory) : [];

  return (
    <div className="tm-diagram-editor__toolbar-overlay" role="toolbar" aria-label={labels.toolbarAriaLabel}>
      <div className="tm-diagram-editor__toolbar-head">
        <div className="tm-diagram-editor__toolbar-tabs" role="tablist" aria-label={labels.toolbarGroupsAriaLabel}>
          {toolbarTabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={toolbarTab === tab.id}
              className={
                toolbarTab === tab.id
                  ? "tm-diagram-editor__toolbar-tab is-active"
                  : "tm-diagram-editor__toolbar-tab"
              }
              onClick={() => onToolbarTabChange(tab.id)}
            >
              {tab.label}
            </button>
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
            <PaletteSubTabs
              tabs={elementGroupTabs}
              activeId={elementGroup}
              onChange={setElementGroup}
              ariaLabel={labels.paletteCategoriesAriaLabel}
            />

            {elementGroup === "events" ? (
              <PaletteSubTabs
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
