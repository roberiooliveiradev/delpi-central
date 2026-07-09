import { CircleHelp } from "lucide-react";

import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { HelpTooltip } from "@delpi/plugin-ui";
import type { FlowchartLane, FlowchartNodeType } from "../../types/diagram";
import { DiagramEditorToolbarButton } from "./DiagramEditorToolbarButton";
import { FlowchartLaneToolbar } from "./FlowchartLaneToolbar";
import {
  BPMN_PALETTE_CATEGORIES,
  DIAGRAM_EDITOR_ADD_LANE_ACTION,
  DIAGRAM_EDITOR_LAYOUT_ACTIONS,
  FLOWCHART_NODE_ICONS,
  flowchartNodeHint,
  paletteByCategory,
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
            <div className="tm-diagram-editor__palette-groups">
              {BPMN_PALETTE_CATEGORIES.map((category) => {
                const items = paletteByCategory(category.id);
                if (!items.length) return null;
                return (
                  <section key={category.id} className="tm-diagram-editor__palette-group">
                    <h4 className="tm-diagram-editor__palette-group-title">{category.label}</h4>
                    <div className="tm-diagram-editor__palette">
                      {items.map((item) => {
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
                  </section>
                );
              })}
            </div>
            <div className="tm-diagram-editor__elements-lanes">
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
