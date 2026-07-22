import {
  AnchoredPanelPortal,
  resolveOverflowRibbonTabIds,
  TabHintCell,
  measureElementWidth,
} from "@delpi/plugin-ui/index";
import { ChevronDown, MoreHorizontal } from "lucide-react";
import {
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";
import {
  isContextualDeckRibbonTab,
  type DeckRibbonTabId,
  type DeckRibbonTabMeta,
} from "./deckRibbonTabMeta";

export type DeckChromeTabsRowProps = {
  tabs: DeckRibbonTabMeta[];
  activeTab: DeckRibbonTabId;
  onSelect: (tab: DeckRibbonTabId) => void;
  isTabDisabled?: (tab: DeckRibbonTabMeta) => boolean;
  /** Ex.: DeckKeyTip em volta da célula. */
  wrapTab?: (tab: DeckRibbonTabMeta, cell: ReactNode) => ReactNode;
  className?: string;
  portalScopeClassName?: string;
  overflowEnabled?: boolean;
};

export function deckChromeTabClassNames(
  tab: DeckRibbonTabMeta,
  tabs: DeckRibbonTabMeta[],
  index: number,
): {
  cellClassName: string;
  tabClassName: string;
  tabActiveClassName: string;
} {
  const contextual = isContextualDeckRibbonTab(tab);
  const firstContextual =
    contextual && tabs.slice(0, index).every((prev) => !isContextualDeckRibbonTab(prev));
  return {
    cellClassName: [
      "td-deck-chrome__tab-cell",
      contextual ? "td-deck-chrome__tab-cell--contextual" : "",
      firstContextual ? "td-deck-chrome__tab-cell--contextual-start" : "",
    ]
      .filter(Boolean)
      .join(" "),
    tabClassName: [
      "td-deck-chrome__tab",
      contextual ? "td-deck-chrome__tab--contextual" : "",
    ]
      .filter(Boolean)
      .join(" "),
    tabActiveClassName: [
      "td-deck-chrome__tab--active",
      contextual ? "td-deck-chrome__tab--contextual-active" : "",
    ]
      .filter(Boolean)
      .join(" "),
  };
}

/**
 * Faixa de abas do chrome com overflow «Mais…» (direita → esquerda; ativa sempre visível).
 */
export function DeckChromeTabsRow({
  tabs,
  activeTab,
  onSelect,
  isTabDisabled,
  wrapTab,
  className,
  portalScopeClassName = TV_DASHBOARD_ROOT_CLASS,
  overflowEnabled = true,
}: DeckChromeTabsRowProps) {
  const rowRef = useRef<HTMLDivElement>(null);
  const measureRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const moreMeasureRef = useRef<HTMLDivElement>(null);
  const moreAnchorRef = useRef<HTMLDivElement>(null);
  const morePanelRef = useRef<HTMLDivElement>(null);
  const [availableWidth, setAvailableWidth] = useState(0);
  const [widthsVersion, setWidthsVersion] = useState(0);
  const [moreOpen, setMoreOpen] = useState(false);

  useLayoutEffect(() => {
    const node = rowRef.current;
    if (!node || typeof ResizeObserver === "undefined") return;
    const update = () => setAvailableWidth(node.clientWidth);
    update();
    const observer = new ResizeObserver(update);
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  useLayoutEffect(() => {
    setWidthsVersion((v) => v + 1);
  }, [tabs, availableWidth]);

  const tabWidths = useMemo(() => {
    return tabs.map((tab, order) => ({
      id: tab.id,
      width: measureElementWidth(measureRefs.current.get(tab.id) ?? null),
      order,
    }));
    // eslint-disable-next-line react-hooks/exhaustive-deps -- widthsVersion após layout das medidas
  }, [tabs, availableWidth, widthsVersion]);

  const overflowControlWidth = Math.max(
    40,
    measureElementWidth(moreMeasureRef.current),
  );

  const overflowIdsPrev = useRef<Set<string>>(new Set());
  const overflowIds = useMemo(() => {
    if (!overflowEnabled || availableWidth <= 0) {
      if (overflowIdsPrev.current.size === 0) return overflowIdsPrev.current;
      overflowIdsPrev.current = new Set();
      return overflowIdsPrev.current;
    }
    const next = resolveOverflowRibbonTabIds(tabWidths, availableWidth, {
      overflowControlWidth,
      activeId: activeTab,
      gap: 0,
    });
    const prev = overflowIdsPrev.current;
    if (prev.size === next.size && [...next].every((id) => prev.has(id))) {
      return prev;
    }
    overflowIdsPrev.current = next;
    return next;
  }, [activeTab, availableWidth, overflowControlWidth, overflowEnabled, tabWidths]);

  useLayoutEffect(() => {
    if (overflowIds.size === 0) setMoreOpen(false);
  }, [overflowIds]);

  const overflowTabs = tabs.filter((tab) => overflowIds.has(tab.id));
  const visibleTabs = tabs.filter((tab) => !overflowIds.has(tab.id));
  const activeInOverflow = overflowIds.has(activeTab);

  function renderTabCell(tab: DeckRibbonTabMeta, indexInFullList: number) {
    const classes = deckChromeTabClassNames(tab, tabs, indexInFullList);
    const cell = (
      <TabHintCell
        label={tab.label}
        hint={tab.hint}
        icon={tab.icon}
        active={activeTab === tab.id}
        disabled={isTabDisabled?.(tab) ?? false}
        onSelect={() => onSelect(tab.id)}
        cellClassName={classes.cellClassName}
        tabClassName={classes.tabClassName}
        tabActiveClassName={classes.tabActiveClassName}
      />
    );
    return wrapTab ? wrapTab(tab, cell) : cell;
  }

  return (
    <div
      ref={rowRef}
      className={["td-deck-chrome__tabs", className].filter(Boolean).join(" ")}
      role="tablist"
      aria-label="Faixas do editor"
      data-tabs-overflow={overflowEnabled ? "on" : "off"}
    >
      <div className="td-deck-chrome__tabs-measure" aria-hidden="true">
        {tabs.map((tab, index) => {
          const classes = deckChromeTabClassNames(tab, tabs, index);
          return (
            <div
              key={`m-${tab.id}`}
              ref={(node) => {
                if (node) measureRefs.current.set(tab.id, node);
                else measureRefs.current.delete(tab.id);
              }}
              className={classes.cellClassName}
            >
              <span className={classes.tabClassName}>
                {tab.icon ? <tab.icon size={15} aria-hidden="true" /> : null}
                {tab.label}
              </span>
            </div>
          );
        })}
        <div ref={moreMeasureRef} className="td-deck-chrome__tab-cell td-deck-chrome__tab-cell--more">
          <span className="td-deck-chrome__tab td-deck-chrome__tab--more">
            <MoreHorizontal size={15} aria-hidden="true" />
            Mais
            <ChevronDown size={12} aria-hidden="true" />
          </span>
        </div>
      </div>

      <div className="td-deck-chrome__tabs-visible">
        {visibleTabs.map((tab) => {
          const index = tabs.findIndex((t) => t.id === tab.id);
          return <div key={tab.id}>{renderTabCell(tab, index)}</div>;
        })}

        {overflowTabs.length > 0 ? (
          <div ref={moreAnchorRef} className="td-deck-chrome__tab-cell td-deck-chrome__tab-cell--more">
            <button
              type="button"
              className={[
                "td-deck-chrome__tab",
                "td-deck-chrome__tab--more",
                moreOpen ? "td-deck-chrome__tab--more-open" : "",
                activeInOverflow ? "td-deck-chrome__tab--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              aria-haspopup="menu"
              aria-expanded={moreOpen}
              aria-label="Mais faixas"
              onClick={() => setMoreOpen((open) => !open)}
            >
              <MoreHorizontal size={15} aria-hidden="true" />
              Mais
              <ChevronDown size={12} aria-hidden="true" />
            </button>
            {moreOpen ? (
              <AnchoredPanelPortal
                open={moreOpen}
                anchorRef={moreAnchorRef}
                panelRef={morePanelRef}
                variant="bare"
                portalScopeClassName={portalScopeClassName}
                className="td-deck-chrome__tabs-more-portal"
                role="menu"
                aria-label="Faixas ocultas"
                onDismiss={() => setMoreOpen(false)}
              >
                <ul className="td-deck-chrome__tabs-more-list">
                  {overflowTabs.map((tab) => {
                    const Icon = tab.icon;
                    const disabled = isTabDisabled?.(tab) ?? false;
                    const selected = activeTab === tab.id;
                    return (
                      <li key={tab.id} role="none">
                        <button
                          type="button"
                          role="menuitem"
                          className={[
                            "td-deck-chrome__tabs-more-item",
                            selected ? "td-deck-chrome__tabs-more-item--active" : "",
                          ]
                            .filter(Boolean)
                            .join(" ")}
                          disabled={disabled}
                          onClick={() => {
                            onSelect(tab.id);
                            setMoreOpen(false);
                          }}
                        >
                          {Icon ? <Icon size={15} aria-hidden="true" /> : null}
                          <span>{tab.label}</span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </AnchoredPanelPortal>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
