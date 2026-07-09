import { CircleHelp } from "lucide-react";
import { useState } from "react";

import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { HelpTooltip } from "@delpi/plugin-ui";
import type { BpmnPaletteCategoryId } from "../../types/bpmnNodeCatalog";
import type { FlowchartLane, FlowchartNodeType } from "../../types/diagram";
import { DiagramEditorToolbarButton } from "./DiagramEditorToolbarButton";
import { FlowchartLaneToolbar } from "./FlowchartLaneToolbar";
import {
  DIAGRAM_EDITOR_ADD_LANE_ACTION,
  DIAGRAM_EDITOR_LAYOUT_ACTIONS,
  FLOWCHART_ELEMENT_GROUP_TABS,
  FLOWCHART_EVENT_SUB_TABS,
  FLOWCHART_NODE_ICONS,
  flowchartNodeHint,
  paletteByCategory,
  resolvePaletteCategory,
  type FlowchartElementGroupTab,
} from "./flowchartEditorToolbar";

export type FlowchartEditorToolbarTab = "elements" | "models";

const TOOLBAR_TABS: { id: FlowchartEditorToolbarTab; label: string }[] = [
  { id: "elements", label: "Elementos" },
  { id: "models", label: "Modelos" },
];

type Props = {
  toolbarTab: FlowchartEditorToolbarTab;
  onToolbarTabChange: (tab: FlowchartEditorToolbarTab) => void;
  lanes: FlowchartLane[];
  activeLaneId?: string;
  onActiveLaneChange: (laneId: string) => void;
  onRemoveLane: () => void | Promise<void>;
  onAddNode: (type: FlowchartNodeType) => void;
  onEditorAction: (actionId: (typeof DIAGRAM_EDITOR_LAYOUT_ACTIONS)[number]["id"] | "addLane") => void;
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
  toolbarTab,
  onToolbarTabChange,
  lanes,
  activeLaneId,
  onActiveLaneChange,
  onRemoveLane,
  onAddNode,
  onEditorAction,
}: Props) {
  const addLaneAction = DIAGRAM_EDITOR_ADD_LANE_ACTION;
  const [elementGroup, setElementGroup] = useState<FlowchartElementGroupTab>("events");
  const [eventSubTab, setEventSubTab] = useState<BpmnPaletteCategoryId>("events_start");

  const activeCategory = resolvePaletteCategory(elementGroup, eventSubTab);
  const paletteItems = activeCategory ? paletteByCategory(activeCategory) : [];

  return (
    <div className="tm-diagram-editor__toolbar-overlay" role="toolbar" aria-label="Ferramentas do diagrama">
      <div className="tm-diagram-editor__toolbar-head">
        <div className="tm-diagram-editor__toolbar-tabs" role="tablist" aria-label="Grupos de ferramentas">
          {TOOLBAR_TABS.map((tab) => (
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
          content={TM_HELP_TOOLTIPS.diagramEditor.usoGeral}
          ariaLabel="Como usar o editor de diagrama"
          wrap
          placement="bottom"
          className="tm-diagram-editor__hint-wrap"
        >
          <button type="button" className="tm-diagram-editor__hint-link tm-diagram-editor__toolbar-help">
            <CircleHelp size={14} aria-hidden="true" />
            <span>Como usar</span>
          </button>
        </HelpTooltip>
      </div>

      <div className="tm-diagram-editor__toolbar-panel" role="tabpanel">
        {toolbarTab === "elements" ? (
          <div className="tm-diagram-editor__elements">
            <PaletteSubTabs
              tabs={FLOWCHART_ELEMENT_GROUP_TABS}
              activeId={elementGroup}
              onChange={setElementGroup}
              ariaLabel="Categorias de elementos BPMN"
            />

            {elementGroup === "events" ? (
              <PaletteSubTabs
                tabs={FLOWCHART_EVENT_SUB_TABS}
                activeId={eventSubTab}
                onChange={setEventSubTab}
                ariaLabel="Tipos de evento"
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
                    lanes={lanes}
                    activeLaneId={activeLaneId}
                    onActiveLaneChange={onActiveLaneChange}
                    onRemoveLane={onRemoveLane}
                    disableRemove={!lanes.length}
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
                      hint={flowchartNodeHint(item.type)}
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
            {DIAGRAM_EDITOR_LAYOUT_ACTIONS.map((action) => (
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
