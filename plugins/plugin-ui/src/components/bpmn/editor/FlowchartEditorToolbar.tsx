import {
  ArrowLeft,
  Boxes,
  CircleHelp,
  Code2,
  LayoutTemplate,
  Pencil,
  type LucideIcon,
} from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";

import { HelpTooltip } from "../../help/HelpTooltip";
import { TabHintCell } from "../../help/TabHintCell";
import { EditorChrome } from "../../layout/EditorChrome";
import {
  EditorRibbonSection,
  EditorRibbonSections,
} from "../../ribbon/EditorRibbonSection";
import { RibbonTile, RibbonTiles } from "../../ribbon/RibbonTile";
import type { FlowchartEditorLabels } from "../model/flowchartEditorLabels";
import type { BpmnPaletteCategoryId } from "../model/bpmnNodeCatalog";
import type { FlowchartLane, FlowchartNodeType } from "../model/diagram";
import { FlowchartEditorHistoryActions } from "./FlowchartEditorHistoryActions";
import { FlowchartComponentSearch } from "./FlowchartComponentSearch";
import { FlowchartLaneToolbar } from "../nodes/FlowchartLaneToolbar";
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

export type FlowchartEditorChromeLeading = {
  onBack?: () => void;
  backLabel?: string;
  title?: string;
};

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
  chromeLeading?: FlowchartEditorChromeLeading;
  /** Avisos na faixa do chrome (entre head e ribbon). */
  chromeNotices?: ReactNode;
  portalScopeClassName?: string;
  showPreviewTab?: boolean;
  activeViewTab?: "canvas" | "mermaid";
  onViewTabChange?: (tab: "canvas" | "mermaid") => void;
  children: ReactNode;
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
        "delpi-ui-bpmn-editor__palette-subtabs",
        compact ? "delpi-ui-bpmn-editor__palette-subtabs--compact" : "",
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
            cellClassName="delpi-ui-bpmn-editor__palette-subtab-cell"
            tabClassName={
              activeId === tab.id
                ? "delpi-ui-bpmn-editor__palette-subtab is-active"
                : "delpi-ui-bpmn-editor__palette-subtab"
            }
            tabActiveClassName="is-active"
            hintPlacement="bottom"
          />
        );
      })}
    </div>
  );
}

/**
 * Chrome 2-tier do editor BPMN (head + ribbon com seções colapsáveis) + corpo.
 */
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
  chromeLeading,
  chromeNotices,
  portalScopeClassName,
  showPreviewTab = false,
  activeViewTab = "canvas",
  onViewTabChange,
  children,
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

  const [eventSubTab, setEventSubTab] = useState<BpmnPaletteCategoryId>("events_start");

  const backLabel = chromeLeading?.backLabel ?? "Voltar";

  const leading = (
    <>
      {chromeLeading?.onBack ? (
        <button
          type="button"
          className="delpi-ui-bpmn-editor__chrome-back"
          onClick={chromeLeading.onBack}
        >
          <ArrowLeft size={16} aria-hidden />
          {backLabel}
        </button>
      ) : null}
      {onUndo && onRedo ? (
        <FlowchartEditorHistoryActions
          labels={labels}
          canUndo={canUndo}
          canRedo={canRedo}
          onUndo={onUndo}
          onRedo={onRedo}
        />
      ) : null}
    </>
  );

  const tabs = (
    <div className="delpi-ui-bpmn-editor__toolbar-tabs" role="tablist" aria-label={labels.toolbarGroupsAriaLabel}>
      {toolbarTabs.map((tab) => (
        <TabHintCell
          key={tab.id}
          label={tab.label}
          hint={tab.hint}
          icon={tab.icon}
          active={toolbarTab === tab.id}
          onSelect={() => onToolbarTabChange(tab.id)}
          cellClassName="delpi-ui-bpmn-editor__toolbar-tab-cell"
          tabClassName="delpi-ui-bpmn-editor__toolbar-tab"
          tabActiveClassName="is-active"
          hintPlacement="bottom"
        />
      ))}
    </div>
  );

  const trailing = (
    <>
      <FlowchartComponentSearch
        labels={labels}
        onAddNode={onAddNode}
        onEditorAction={onEditorAction}
        portalScopeClassName={portalScopeClassName}
      />
      <HelpTooltip
        content={labels.usoGeral}
        ariaLabel={labels.toolbarHowToUseAriaLabel}
        wrap
        placement="bottom"
        className="delpi-ui-bpmn-editor__hint-wrap"
      >
        <button type="button" className="delpi-ui-bpmn-editor__hint-link delpi-ui-bpmn-editor__toolbar-help">
          <CircleHelp size={14} aria-hidden="true" />
          <span>{labels.toolbarHowToUse}</span>
        </button>
      </HelpTooltip>
      {showPreviewTab && onViewTabChange ? (
        <div className="delpi-ui-bpmn-editor__view-tabs delpi-ui-bpmn-editor__view-tabs--chrome" role="tablist">
          <TabHintCell
            label={labels.canvasTabLabel}
            hint={labels.canvasTab}
            icon={Pencil}
            active={activeViewTab === "canvas"}
            onSelect={() => onViewTabChange("canvas")}
            cellClassName="delpi-ui-bpmn-editor__tab-wrap"
            tabClassName="delpi-ui-bpmn-editor__tab"
            tabActiveClassName="is-active"
          />
          <TabHintCell
            label={labels.mermaidTabLabel}
            hint={labels.mermaidTab}
            icon={Code2}
            active={activeViewTab === "mermaid"}
            onSelect={() => onViewTabChange("mermaid")}
            cellClassName="delpi-ui-bpmn-editor__tab-wrap"
            tabClassName="delpi-ui-bpmn-editor__tab"
            tabActiveClassName="is-active"
          />
        </div>
      ) : null}
    </>
  );

  const ribbon =
    toolbarTab === "elements" ? (
      <EditorRibbonSections portalScopeClassName={portalScopeClassName}>
        {elementGroupTabs.map((group, index) => {
          const Icon = group.icon;
          if (group.id === "lanes") {
            return (
              <EditorRibbonSection
                key={group.id}
                groupId={`bpmn-${group.id}`}
                label={group.label}
                hint={group.hint}
                collapseIcon={Icon}
                order={(index + 1) * 10}
              >
                <RibbonTiles compact aria-label={group.label}>
                  <RibbonTile
                    icon={addLaneAction.icon}
                    label={addLaneAction.label}
                    hint={addLaneAction.hint}
                    onClick={() => onEditorAction("addLane")}
                  />
                </RibbonTiles>
                {lanes.length ? (
                  <FlowchartLaneToolbar
                    labels={labels}
                    lanes={lanes}
                    activeLaneId={activeLaneId}
                    onActiveLaneChange={onActiveLaneChange}
                  />
                ) : null}
              </EditorRibbonSection>
            );
          }

          const category = resolvePaletteCategory(group.id as FlowchartElementGroupTab, eventSubTab);
          const paletteItems = category ? paletteByCategory(category) : [];

          return (
            <EditorRibbonSection
              key={group.id}
              groupId={`bpmn-${group.id}`}
              label={group.label}
              hint={group.hint}
              collapseIcon={Icon}
              order={(index + 1) * 10}
            >
              {group.id === "events" ? (
                <PaletteSubTabs<BpmnPaletteCategoryId>
                  tabs={eventSubTabs}
                  activeId={eventSubTab}
                  onChange={setEventSubTab}
                  ariaLabel={labels.paletteEventsAriaLabel}
                  compact
                />
              ) : null}
              <RibbonTiles compact aria-label={group.label}>
                {paletteItems.map((item) => {
                  const NodeIcon = FLOWCHART_NODE_ICONS[item.type];
                  return (
                    <RibbonTile
                      key={item.type}
                      icon={NodeIcon}
                      label={item.label}
                      hint={flowchartNodeHint(item.type, labels)}
                      onClick={() => onAddNode(item.type)}
                    />
                  );
                })}
              </RibbonTiles>
            </EditorRibbonSection>
          );
        })}
      </EditorRibbonSections>
    ) : (
      <EditorRibbonSections portalScopeClassName={portalScopeClassName}>
        <EditorRibbonSection
          groupId="bpmn-templates"
          label={labels.toolbarModelsTab}
          hint={labels.toolbarModelsTabHint}
          collapseIcon={LayoutTemplate}
          order={10}
        >
          <RibbonTiles compact aria-label={labels.toolbarModelsTab}>
            {layoutActions.map((action) => (
              <RibbonTile
                key={action.id}
                icon={action.icon}
                label={action.label}
                hint={action.hint}
                onClick={() => onEditorAction(action.id)}
              />
            ))}
          </RibbonTiles>
        </EditorRibbonSection>
      </EditorRibbonSections>
    );

  return (
    <EditorChrome
      density="compact"
      aria-label={labels.toolbarAriaLabel}
      leading={leading}
      tabs={tabs}
      trailing={trailing}
      trail={chromeLeading?.title ? <span title={chromeLeading.title}>{chromeLeading.title}</span> : null}
      notices={chromeNotices}
      ribbon={ribbon}
      className="delpi-ui-bpmn-editor__chrome"
    >
      {children}
    </EditorChrome>
  );
}
