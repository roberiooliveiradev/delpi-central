import { useEffect, useState, type ReactNode } from "react";
import { TabHintCell } from "@delpi/plugin-ui/index";

import type { BranchScope, NativeScreenCatalogItem, Playlist, Slide } from "../api/tvDashboardApi";
import { ComunicadoRibbonContent } from "./ComunicadoRibbonContent";
import { DeckSettingsPanel } from "./DeckSettingsPanel";
import { SlideDeckRibbon } from "./SlideDeckRibbon";
import {
  DeckRibbonShell,
  type DeckRibbonTabId,
  resolveDeckRibbonTabs,
} from "./deck";

type SlideDeckProps = {
  slides: Slide[];
  selectedSlide: Slide | null;
  onAdd: () => void;
  onSelect: (slideId: string) => void;
  onDuplicate: (slide: Slide) => void;
  onToggleActive: (slide: Slide) => void;
  onRemove: (slide: Slide) => void;
};

type Props = {
  playlist: Playlist;
  slide: Slide | null;
  catalog: NativeScreenCatalogItem[];
  branchScope: BranchScope | null;
  isCustomSlide: boolean;
  adminLabels?: Record<string, string>;
  slideTabExtra?: ReactNode;
  headerActions?: ReactNode;
  slideDeck: SlideDeckProps;
  onSavePlaylistSettings: (field: string, value: string | number) => void;
  onSaveSlide: (
    slide: Slide,
    payload: {
      title: string;
      durationSec: number;
      nativeConfig?: Record<string, unknown>;
      externalUrl?: string;
      transitionStyle?: string | null;
    },
  ) => void;
};

function isRibbonTab(tab: DeckRibbonTabId): tab is "home" | "insert" | "format" {
  return tab === "home" || tab === "insert" || tab === "format";
}

function isSettingsTab(tab: DeckRibbonTabId): tab is "slide" | "playlist" {
  return tab === "slide" || tab === "playlist";
}

/** Chrome do editor: abas estilo PowerPoint + ribbon contextual + painel de configuração. */
export function DeckEditorChrome({
  playlist,
  slide,
  catalog,
  branchScope,
  isCustomSlide,
  adminLabels = {},
  slideTabExtra,
  headerActions,
  slideDeck,
  onSavePlaylistSettings,
  onSaveSlide,
}: Props) {
  const tabs = resolveDeckRibbonTabs(isCustomSlide);
  const [activeTab, setActiveTab] = useState<DeckRibbonTabId>("home");

  useEffect(() => {
    if (!tabs.some((tab) => tab.id === activeTab)) {
      setActiveTab("home");
    }
  }, [activeTab, tabs]);

  useEffect(() => {
    if (activeTab === "slide" && !slide) {
      setActiveTab("home");
    }
  }, [activeTab, slide]);

  return (
    <section className="td-deck-chrome" aria-label="Editor da programação">
      <div className="td-deck-chrome__head">
        <div className="td-deck-chrome__tabs" role="tablist" aria-label="Faixas do editor">
          {tabs.map((tab) => (
            <TabHintCell
              key={tab.id}
              label={tab.label}
              hint={tab.hint}
              active={activeTab === tab.id}
              disabled={tab.disabledWhenNoSlide ? !slide : false}
              onSelect={() => setActiveTab(tab.id)}
              cellClassName="td-deck-chrome__tab-cell"
              tabClassName="td-deck-chrome__tab"
              tabActiveClassName="td-deck-chrome__tab--active"
            />
          ))}
        </div>
        {headerActions}
      </div>

      {isRibbonTab(activeTab) ? (
        <div className="td-deck-chrome__ribbon">
          <DeckRibbonShell>
            {activeTab === "home" ? <SlideDeckRibbon {...slideDeck} /> : null}
            {isCustomSlide && (activeTab === "insert" || activeTab === "format") ? (
              <ComunicadoRibbonContent activeTab={activeTab} labels={adminLabels} />
            ) : null}
          </DeckRibbonShell>
        </div>
      ) : null}

      {isSettingsTab(activeTab) ? (
        <div className="td-deck-chrome__panel" role="tabpanel">
          <DeckSettingsPanel
            activeTab={activeTab}
            playlist={playlist}
            slide={slide}
            catalog={catalog}
            branchScope={branchScope}
            slideTabExtra={slideTabExtra}
            onSavePlaylistSettings={onSavePlaylistSettings}
            onSaveSlide={onSaveSlide}
          />
        </div>
      ) : null}
    </section>
  );
}
