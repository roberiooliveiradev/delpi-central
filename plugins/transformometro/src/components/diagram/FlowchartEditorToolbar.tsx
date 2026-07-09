import { CircleHelp } from "lucide-react";

import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { HelpTooltip } from "@delpi/plugin-ui";
import { FLOWCHART_NODE_PALETTE, type FlowchartLane, type FlowchartNodeType } from "../../types/diagram";
import { DiagramEditorToolbarButton } from "./DiagramEditorToolbarButton";
import { FlowchartLaneToolbar } from "./FlowchartLaneToolbar";
import {
  DIAGRAM_EDITOR_ACTIONS,
  DIAGRAM_EDITOR_SELECTION_ACTIONS,
  FLOWCHART_NODE_ICONS,
  flowchartNodeHint,
} from "./flowchartEditorToolbar";

export type FlowchartEditorToolbarTab = "elements" | "layout" | "actions";

const TOOLBAR_TABS: { id: FlowchartEditorToolbarTab; label: string }[] = [
  { id: "elements", label: "Elementos" },
  { id: "layout", label: "Faixas & modelos" },
  { id: "actions", label: "Ações" },
];

type Props = {
  toolbarTab: FlowchartEditorToolbarTab;
  onToolbarTabChange: (tab: FlowchartEditorToolbarTab) => void;
  lanes: FlowchartLane[];
  activeLaneId?: string;
  onActiveLaneChange: (laneId: string) => void;
  onRemoveLane: () => void | Promise<void>;
  onAddNode: (type: FlowchartNodeType) => void;
  onEditorAction: (actionId: (typeof DIAGRAM_EDITOR_ACTIONS)[number]["id"]) => void;
  onSelectionAction: (actionId: (typeof DIAGRAM_EDITOR_SELECTION_ACTIONS)[number]["id"]) => void;
  isSelectionActionDisabled: (
    actionId: (typeof DIAGRAM_EDITOR_SELECTION_ACTIONS)[number]["id"]
  ) => boolean;
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
  onSelectionAction,
  isSelectionActionDisabled,
}: Props) {
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
          <div className="tm-diagram-editor__palette">
            {FLOWCHART_NODE_PALETTE.map((item) => {
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
        ) : null}

        {toolbarTab === "layout" ? (
          <div className="tm-diagram-editor__templates">
            {lanes.length ? (
              <FlowchartLaneToolbar
                lanes={lanes}
                activeLaneId={activeLaneId}
                onActiveLaneChange={onActiveLaneChange}
                onRemoveLane={onRemoveLane}
                disableRemove={!lanes.length}
              />
            ) : null}
            {DIAGRAM_EDITOR_ACTIONS.map((action) => (
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

        {toolbarTab === "actions" ? (
          <div className="tm-diagram-editor__actions">
            {DIAGRAM_EDITOR_SELECTION_ACTIONS.map((action) => (
              <DiagramEditorToolbarButton
                key={action.id}
                label={action.label}
                hint={action.hint}
                icon={action.icon}
                disabled={isSelectionActionDisabled(action.id)}
                active={
                  action.id === "delete"
                    ? !isSelectionActionDisabled("delete")
                    : action.id === "move" || action.id === "copy" || action.id === "duplicate"
                      ? !isSelectionActionDisabled(action.id)
                      : false
                }
                onClick={() => onSelectionAction(action.id)}
              />
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
