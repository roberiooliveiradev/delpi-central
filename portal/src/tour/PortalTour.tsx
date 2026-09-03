import { useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useLocation } from "react-router-dom";
import {
  Check,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  Star,
  Sparkles,
  Trophy,
  X,
} from "lucide-react";
import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { CoreApi, type PortalTourAchievementItem, type PortalTourCatalogResponse } from "../data/coreApi";
import "./PortalTour.css";
import {
  clearTourPulseTargets,
  watchTourQuests,
} from "./portalTourInteraction";
import {
  hydratePortalTourSessionFromRemote,
  loadPortalTourProgress,
  markPortalTourCompletedEverywhere,
  repairLocalCompletedWhenRemoteIncomplete,
  resolveShouldShowPortalTour,
  shouldSkipPortalTourSyncOnOpen,
  syncPortalTourCompleted,
  syncPortalTourQuestCompleted,
  syncPortalTourStarted,
  syncPortalTourDismissed,
  shouldAutoOpenPortalTourPanel,
  shouldActivatePortalTourSession,
  canReopenPortalTourPanel,
} from "./portalTourPersistence";
import {
  getPortalTourQuests,
  groupQuestsByCategory,
  PORTAL_TOUR_CATEGORY_LABELS,
  PORTAL_TOUR_CATEGORY_ORDER,
} from "./portalTourQuests";
import {
  alignQuestsWithCatalog,
  isQuestMarkedNew,
  resolveCompletedRequiredCount,
  resolveNewQuestsBannerMessage,
  resolveProgressPercentFromCatalog,
  resolveRequiredQuestTotal,
} from "./portalTourCatalogSync";
import {
  getTourContextLabel,
  resolveQuestGuide,
} from "./portalTourQuestGuide";
import {
  orderCategoriesPendingFirst,
  questListVisualClassName,
  resolveQuestListHint,
  resolveQuestListVisualState,
  sortQuestsForCompanionList,
} from "./portalTourQuestListVisual";
import { setPortalTourSidebarPanel } from "./portalTourSidebar";
import { clearPortalTourTimers, schedulePortalTourTimer } from "./portalTourTimers";
import { closeAppLauncher } from "../utils/appLauncher";
import { usePortalTourHighlights } from "./usePortalTourHighlights";
import { PortalTourCompletionModal } from "./PortalTourCompletionModal";
import { subscribePortalTourSyncStatus } from "./portalTourSyncStatus";
import { runPortalTourConfetti } from "./portalTourCelebration";
import {
  formatExplorationDuration,
  resolveExplorationDurationSeconds,
} from "./portalTourInsights";
import { shouldPlayPortalTourAnimations } from "./portalTourPreferences";
import {
  computeEarnedXp,
  levelUpMessage,
  resolveCategoryJustCompleted,
  resolveExplorerLevel,
  resolveExplorerLevelUp,
  resolveQuestXp,
  type QuestCelebrationToast,
} from "./portalTourGamification";

import {
  DELPI_PORTAL_TOUR_DISMISS_EVENT,
  DELPI_PORTAL_TOUR_OPEN_PANEL_EVENT,
  DELPI_PORTAL_TOUR_RESUME_EVENT,
  publishPortalTourSession,
  resetPortalTourSessionSnapshot,
} from "./portalTourSession";

export const DELPI_PORTAL_TOUR_START_EVENT = "DELPI_PORTAL_TOUR_START";

export function startPortalTour() {
  window.dispatchEvent(new CustomEvent(DELPI_PORTAL_TOUR_START_EVENT));
}

type QuestBanner = {
  id: string;
  message: string;
  kind?: "default" | "level-up";
  levelLabel?: string;
};

export function PortalTour() {
  const { user, coreLoaded, getAccessToken, refreshToken } = useContext(AuthContext);
  const location = useLocation();
  const [active, setActive] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [completedIds, setCompletedIds] = useState<Set<string>>(() => new Set());
  const [toast, setToast] = useState<QuestCelebrationToast | null>(null);
  const [remoteReady, setRemoteReady] = useState(false);
  const [hintQuestId, setHintQuestId] = useState<string | null>(null);
  const [successFlashQuestId, setSuccessFlashQuestId] = useState<string | null>(
    null,
  );
  const [justCompletedQuestId, setJustCompletedQuestId] = useState<string | null>(
    null,
  );
  const [xpBarBump, setXpBarBump] = useState(false);
  const [banner, setBanner] = useState<QuestBanner | null>(null);
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [explorationDurationLabel, setExplorationDurationLabel] = useState<
    string | null
  >(null);
  const [completionAchievements, setCompletionAchievements] = useState<
    PortalTourAchievementItem[]
  >([]);
  const [syncFailed, setSyncFailed] = useState(false);
  const [catalog, setCatalog] = useState<PortalTourCatalogResponse | null>(null);
  const confettiCleanupRef = useRef<(() => void) | null>(null);
  const completedRef = useRef(completedIds);
  const remoteProgressRef = useRef<Awaited<ReturnType<typeof loadPortalTourProgress>>>(null);
  const autoStartCheckedRef = useRef(false);

  const coreApi = useMemo(
    () =>
      new CoreApi(
        new ApiClient("", getAccessToken, {
          refreshToken: async () => {
            await refreshToken();
            return Boolean(getAccessToken());
          },
        }),
      ),
    [getAccessToken, refreshToken],
  );

  const canAccessAdmin = useMemo(
    () =>
      Boolean(
        user?.is_superadmin || user?.permissions?.includes("rbac.manage"),
      ),
    [user?.is_superadmin, user?.permissions],
  );

  const localQuests = useMemo(
    () => getPortalTourQuests({ canAccessAdmin }),
    [canAccessAdmin],
  );

  const quests = useMemo(
    () => alignQuestsWithCatalog(localQuests, catalog),
    [localQuests, catalog],
  );

  const questsByCategory = useMemo(
    () => groupQuestsByCategory(quests),
    [quests],
  );

  const requiredTotal = useMemo(
    () => resolveRequiredQuestTotal(catalog, quests),
    [catalog, quests],
  );
  const requiredDone = useMemo(
    () => resolveCompletedRequiredCount(catalog, quests, completedIds),
    [catalog, quests, completedIds],
  );
  const progressPercent = useMemo(
    () => resolveProgressPercentFromCatalog(catalog, quests, completedIds),
    [catalog, quests, completedIds],
  );
  const explorerLevel = useMemo(
    () => resolveExplorerLevel(progressPercent),
    [progressPercent],
  );
  const earnedXp = useMemo(
    () => computeEarnedXp(quests, completedIds),
    [quests, completedIds],
  );

  const highlights = usePortalTourHighlights(
    panelOpen,
    hintQuestId,
    quests,
    completedIds,
  );

  const contextLabel = useMemo(
    () => (active ? getTourContextLabel() : ""),
    [active, location.pathname, highlights],
  );

  useEffect(() => {
    completedRef.current = completedIds;
  }, [completedIds]);

  useEffect(() => {
    return subscribePortalTourSyncStatus(({ failed }) => {
      setSyncFailed(failed);
    });
  }, []);

  useEffect(() => {
    publishPortalTourSession({
      sessionActive: active,
      panelOpen,
      completed: false,
      dismissed: false,
      requiredDone,
      requiredTotal,
      progressPercent,
      explorerLevel: explorerLevel.label,
    });
  }, [
    active,
    panelOpen,
    requiredDone,
    requiredTotal,
    progressPercent,
    explorerLevel.label,
  ]);

  const completeSession = useCallback(() => {
    if (user?.id) {
      markPortalTourCompletedEverywhere(user.id);
      syncPortalTourCompleted(coreApi, Array.from(completedRef.current));
    }
    clearTourPulseTargets();
    clearPortalTourTimers();
    closeAppLauncher();
    setPortalTourSidebarPanel("none");
    document.documentElement.dataset.portalTourActive = "false";
    setActive(false);
    setPanelOpen(false);
    setExpanded(true);
    setToast(null);
    setHintQuestId(null);
    setSuccessFlashQuestId(null);
    setJustCompletedQuestId(null);
    setXpBarBump(false);
    setBanner(null);
    setShowCompletionModal(false);
    confettiCleanupRef.current?.();
    confettiCleanupRef.current = null;
    publishPortalTourSession({
      sessionActive: false,
      panelOpen: false,
      completed: true,
      dismissed: false,
      requiredDone,
      requiredTotal,
      progressPercent: 100,
      explorerLevel: explorerLevel.label,
    });
  }, [user?.id, coreApi, requiredDone, requiredTotal, explorerLevel.label]);

  const hidePanel = useCallback(() => {
    setPanelOpen(false);
    setExpanded(true);
    setHintQuestId(null);
    setShowCompletionModal(false);
    confettiCleanupRef.current?.();
    confettiCleanupRef.current = null;
    document.documentElement.dataset.portalTourActive = "false";
    clearTourPulseTargets();
  }, []);

  const dismissSession = useCallback(() => {
    syncPortalTourDismissed(coreApi, Array.from(completedRef.current));
    if (remoteProgressRef.current) {
      remoteProgressRef.current = {
        ...remoteProgressRef.current,
        status: "dismissed",
        completedQuestIds: Array.from(completedRef.current),
      };
    }
    clearTourPulseTargets();
    clearPortalTourTimers();
    closeAppLauncher();
    setPortalTourSidebarPanel("none");
    document.documentElement.dataset.portalTourActive = "false";
    setActive(false);
    setPanelOpen(false);
    setExpanded(true);
    setToast(null);
    setHintQuestId(null);
    setSuccessFlashQuestId(null);
    setJustCompletedQuestId(null);
    setXpBarBump(false);
    setBanner(null);
    setShowCompletionModal(false);
    confettiCleanupRef.current?.();
    confettiCleanupRef.current = null;
    publishPortalTourSession({
      sessionActive: false,
      panelOpen: false,
      completed: false,
      dismissed: true,
      requiredDone,
      requiredTotal,
      progressPercent,
      explorerLevel: explorerLevel.label,
    });
  }, [coreApi, requiredDone, requiredTotal, progressPercent, explorerLevel.label]);

  const showPanel = useCallback(() => {
    setPanelOpen(true);
    setExpanded(true);
  }, []);

  const openCompletionCelebration = useCallback(() => {
    const remote = remoteProgressRef.current;
    const durationSeconds = resolveExplorationDurationSeconds(
      remote?.startedAt,
      remote?.insights?.explorationDurationSeconds,
    );
    setExplorationDurationLabel(formatExplorationDuration(durationSeconds));
    setShowCompletionModal(true);
    confettiCleanupRef.current?.();
    confettiCleanupRef.current = runPortalTourConfetti();
    void coreApi
      .getPortalTourAchievements()
      .then((response) => {
        setCompletionAchievements(
          response.items.filter((item) => item.unlocked),
        );
      })
      .catch(() => {
        setCompletionAchievements([]);
      });
  }, [coreApi]);

  const closeCompletionCelebration = useCallback(() => {
    confettiCleanupRef.current?.();
    confettiCleanupRef.current = null;
    setShowCompletionModal(false);
    completeSession();
  }, [completeSession]);

  const toggleQuestHint = useCallback((questId: string) => {
    setHintQuestId((current) => (current === questId ? null : questId));
  }, []);

  const completeQuest = useCallback(
    (questId: string) => {
      if (completedRef.current.has(questId)) return;

      const quest = quests.find((item) => item.id === questId);
      if (!quest) return;

      const beforeIds = completedRef.current;
      const previousPercent = resolveProgressPercentFromCatalog(
        catalog,
        quests,
        beforeIds,
      );
      const nextIds = new Set(beforeIds);
      nextIds.add(questId);
      const nextPercent = resolveProgressPercentFromCatalog(
        catalog,
        quests,
        nextIds,
      );
      const nextRequiredDone = resolveCompletedRequiredCount(
        catalog,
        quests,
        nextIds,
      );

      setCompletedIds(nextIds);
      completedRef.current = nextIds;
      if (remoteProgressRef.current) {
        remoteProgressRef.current = {
          ...remoteProgressRef.current,
          status: "exploring",
          completedQuestIds: Array.from(nextIds),
        };
      }
      syncPortalTourQuestCompleted(coreApi, Array.from(nextIds), questId);

      const categoryLabel = resolveCategoryJustCompleted(
        quests,
        beforeIds,
        nextIds,
        quest.category,
      );

      const levelUp = resolveExplorerLevelUp(previousPercent, nextPercent);
      const reachingFullCompletion = nextRequiredDone >= requiredTotal;

      setToast({
        id: questId,
        title: quest.title,
        xp: resolveQuestXp(quest),
        categoryLabel: PORTAL_TOUR_CATEGORY_LABELS[quest.category],
      });
      schedulePortalTourTimer(() => {
        setToast((current) => (current?.id === questId ? null : current));
      }, 2000);

      if (levelUp && !reachingFullCompletion) {
        const levelBannerId = `level-up-${levelUp.minPercent}-${questId}`;
        setBanner({
          id: levelBannerId,
          message: levelUpMessage(levelUp),
          kind: "level-up",
          levelLabel: levelUp.label,
        });
        schedulePortalTourTimer(() => {
          setBanner((current) =>
            current?.id === levelBannerId ? null : current,
          );
        }, 2800);
      } else if (categoryLabel) {
        const bannerId = `category-${quest.category}`;
        setBanner({
          id: bannerId,
          message: `Área «${categoryLabel}» concluída!`,
        });
        schedulePortalTourTimer(() => {
          setBanner((current) => (current?.id === bannerId ? null : current));
        }, 2800);
      }

      setSuccessFlashQuestId(questId);
      schedulePortalTourTimer(() => {
        setSuccessFlashQuestId((current) => (current === questId ? null : current));
      }, 480);

      setJustCompletedQuestId(questId);
      schedulePortalTourTimer(() => {
        setJustCompletedQuestId((current) => (current === questId ? null : current));
      }, 720);

      if (shouldPlayPortalTourAnimations()) {
        setXpBarBump(true);
        schedulePortalTourTimer(() => setXpBarBump(false), 420);
      }

      if (nextRequiredDone >= requiredTotal) {
        schedulePortalTourTimer(() => openCompletionCelebration(), 900);
      }
    },
    [quests, coreApi, requiredTotal, openCompletionCelebration, catalog],
  );

  useEffect(() => {
    if (!coreLoaded || !user?.id) return;

    let cancelled = false;
    void Promise.all([
      loadPortalTourProgress(coreApi, user.id),
      coreApi.getPortalTourCatalog().catch(() => null),
    ]).then(([remote, remoteCatalog]) => {
      if (cancelled) return;
      repairLocalCompletedWhenRemoteIncomplete(user.id, remote, remoteCatalog);
      remoteProgressRef.current = remote;
      if (remoteCatalog) setCatalog(remoteCatalog);
      setRemoteReady(true);

      const streakMessage = remote?.insights?.returnStreakMessage;
      const newQuestsMessage = resolveNewQuestsBannerMessage(remoteCatalog);
      const bannerMessage = streakMessage ?? newQuestsMessage;
      if (bannerMessage) {
        const bannerId = streakMessage ? "return-streak" : "new-quests";
        setBanner({ id: bannerId, message: bannerMessage });
        schedulePortalTourTimer(() => {
          setBanner((current) => (current?.id === bannerId ? null : current));
        }, 4500);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [coreLoaded, user?.id, coreApi]);

  useEffect(() => {
    if (!remoteReady || !coreLoaded || !user?.id) return;
    if (autoStartCheckedRef.current) return;
    autoStartCheckedRef.current = true;

    const remote = remoteProgressRef.current;
    const currentCatalog = catalog;
    if (canReopenPortalTourPanel(remote, currentCatalog)) {
      setCompletedIds(hydratePortalTourSessionFromRemote(remote, currentCatalog));
    }

    // Opt-in: só ativa watch em background se já estiver exploring.
    // Nunca abre o painel sozinho (shouldAutoOpen sempre false).
    if (!shouldActivatePortalTourSession(remote, currentCatalog)) return;
    if (!resolveShouldShowPortalTour(user.id, remote, currentCatalog)) return;

    const timer = window.setTimeout(() => {
      setActive(true);
      setPanelOpen(shouldAutoOpenPortalTourPanel(remote, currentCatalog));
    }, 900);
    return () => window.clearTimeout(timer);
  }, [remoteReady, coreLoaded, user?.id, catalog]);

  useEffect(() => {
    const tourUiActive = active && panelOpen && !showCompletionModal;
    document.documentElement.dataset.portalTourActive = tourUiActive
      ? "true"
      : "false";
    return () => {
      document.documentElement.dataset.portalTourActive = "false";
    };
  }, [active, panelOpen, showCompletionModal]);

  useEffect(() => {
    const onStart = () => {
      clearPortalTourTimers();
      autoStartCheckedRef.current = true;
      remoteProgressRef.current = null;
      resetPortalTourSessionSnapshot();
      setCompletedIds(new Set());
      setToast(null);
      setHintQuestId(null);
      setBanner(null);
      setShowCompletionModal(false);
      confettiCleanupRef.current?.();
      confettiCleanupRef.current = null;
      setExpanded(true);
      setActive(true);
      setPanelOpen(true);
      syncPortalTourStarted(coreApi, []);
    };
    const reopenPortalTourFromRemote = () => {
      const hydrated = hydratePortalTourSessionFromRemote(
        remoteProgressRef.current,
        catalog,
      );
      completedRef.current = hydrated;
      setCompletedIds(hydrated);
    };
    const onOpenPanel = () => {
      if (!active) {
        reopenPortalTourFromRemote();
        setActive(true);
      }
      showPanel();
      if (shouldSkipPortalTourSyncOnOpen(remoteProgressRef.current, catalog)) {
        return;
      }
      syncPortalTourStarted(coreApi, Array.from(completedRef.current));
    };
    const onResume = () => {
      autoStartCheckedRef.current = true;
      reopenPortalTourFromRemote();
      if (remoteProgressRef.current) {
        remoteProgressRef.current = {
          ...remoteProgressRef.current,
          status: "exploring",
        };
      }
      setActive(true);
      showPanel();
      syncPortalTourStarted(coreApi, Array.from(completedRef.current));
      publishPortalTourSession({
        sessionActive: true,
        panelOpen: true,
        dismissed: false,
        completed: false,
      });
    };
    const onDismiss = () => {
      autoStartCheckedRef.current = true;
      dismissSession();
    };
    window.addEventListener(DELPI_PORTAL_TOUR_START_EVENT, onStart);
    window.addEventListener(DELPI_PORTAL_TOUR_OPEN_PANEL_EVENT, onOpenPanel);
    window.addEventListener(DELPI_PORTAL_TOUR_RESUME_EVENT, onResume);
    window.addEventListener(DELPI_PORTAL_TOUR_DISMISS_EVENT, onDismiss);
    return () => {
      window.removeEventListener(DELPI_PORTAL_TOUR_START_EVENT, onStart);
      window.removeEventListener(DELPI_PORTAL_TOUR_OPEN_PANEL_EVENT, onOpenPanel);
      window.removeEventListener(DELPI_PORTAL_TOUR_RESUME_EVENT, onResume);
      window.removeEventListener(DELPI_PORTAL_TOUR_DISMISS_EVENT, onDismiss);
    };
  }, [active, showPanel, catalog, coreApi, dismissSession]);

  useEffect(() => {
    if (!active) return;

    const stopWatch = watchTourQuests(
      quests,
      (questId) => completedRef.current.has(questId),
      completeQuest,
    );

    return stopWatch;
  }, [active, quests, completeQuest]);

  useEffect(() => {
    if (!active || !panelOpen) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        if (showCompletionModal) {
          closeCompletionCelebration();
          return;
        }
        if (hintQuestId) {
          setHintQuestId(null);
          return;
        }
        hidePanel();
      }
    };

    window.addEventListener("keydown", onKeyDown, true);
    return () => window.removeEventListener("keydown", onKeyDown, true);
  }, [
    active,
    panelOpen,
    hidePanel,
    showCompletionModal,
    closeCompletionCelebration,
    hintQuestId,
  ]);

  if (!active) return null;

  const hasTransientFeedback = Boolean(toast || banner || showCompletionModal);
  const shouldRenderRoot = panelOpen || hasTransientFeedback;
  if (!shouldRenderRoot) return null;

  return createPortal(
    <div
      className={[
        "portal-tour-root",
        "portal-tour-root--gamified",
        !panelOpen ? "portal-tour-root--feedback-only" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      role="region"
      aria-label="Tour de descobertas do portal"
    >
      {highlights.map((rect) => (
        <div
          key={rect.questId}
          className={`portal-tour-highlight-ring${successFlashQuestId === rect.questId ? " is-success" : ""}`}
          style={{
            top: rect.top,
            left: rect.left,
            width: rect.width,
            height: rect.height,
          }}
          aria-hidden
        />
      ))}

      {toast ? (
        <div className="portal-tour-toast" role="status" aria-live="polite">
          <Check size={16} aria-hidden />
          <span className="portal-tour-toast-copy">
            <strong>{toast.title}</strong>
            <span className="portal-tour-toast-meta">
              +{toast.xp} XP · {toast.categoryLabel}
            </span>
          </span>
        </div>
      ) : null}

      {banner ? (
        <div
          className={`portal-tour-banner${banner.kind === "level-up" ? " is-level-up" : ""}`}
          role="status"
          aria-live="polite"
        >
          {banner.kind === "level-up" ? (
            <Sparkles size={16} aria-hidden />
          ) : (
            <Star size={15} aria-hidden />
          )}
          <span>{banner.message}</span>
          {banner.kind === "level-up" && banner.levelLabel ? (
            <span className="portal-tour-level-up-chip">{banner.levelLabel}</span>
          ) : null}
        </div>
      ) : null}

      {syncFailed && active ? (
        <div className="portal-tour-sync-warning" role="status" aria-live="polite">
          Não foi possível salvar o progresso no servidor. Suas conquistas locais
          serão reenviadas na próxima ação.
        </div>
      ) : null}

      {showCompletionModal ? (
        <PortalTourCompletionModal
          explorerLevel={explorerLevel}
          earnedXp={earnedXp}
          requiredDone={requiredDone}
          requiredTotal={requiredTotal}
          explorationDurationLabel={explorationDurationLabel}
          achievements={completionAchievements}
          onClose={() => closeCompletionCelebration()}
        />
      ) : null}

      {panelOpen ? (
      <div
        className={`portal-tour-quest-panel${expanded ? " is-expanded" : " is-collapsed"}`}
      >
        <div className="portal-tour-quest-toggle-row">
          <button
            type="button"
            className="portal-tour-quest-toggle"
            onClick={() => setExpanded((current) => !current)}
            aria-expanded={expanded}
          >
            <span className="portal-tour-quest-toggle-main">
              <span className="portal-tour-quest-toggle-icon" aria-hidden>
                <Trophy size={16} />
              </span>
              <span className="portal-tour-quest-toggle-copy">
                <span className="portal-tour-quest-toggle-label">
                  Descubra o portal
                </span>
                <span className="portal-tour-quest-toggle-meta">
                  {requiredDone} de {requiredTotal}
                  {contextLabel ? ` · ${contextLabel}` : ""}
                </span>
              </span>
            </span>
            {expanded ? (
              <ChevronDown size={18} aria-hidden />
            ) : (
              <ChevronUp size={18} aria-hidden />
            )}
          </button>
          <button
            type="button"
            className="portal-tour-quest-close"
            onClick={hidePanel}
            aria-label="Fechar lista de descobertas"
          >
            <X size={18} aria-hidden />
          </button>
        </div>

        {expanded ? (
          <div className="portal-tour-quest-body">
            <div
              className="portal-tour-xp-bar"
              role="progressbar"
              aria-valuenow={progressPercent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Progresso: ${requiredDone} de ${requiredTotal} desafios`}
            >
              <div
                className={`portal-tour-xp-bar-fill${xpBarBump ? " is-bump" : ""}`}
                style={{ width: `${progressPercent}%` }}
              />
            </div>

            <ul className="portal-tour-quest-list">
              {orderCategoriesPendingFirst(
                PORTAL_TOUR_CATEGORY_ORDER,
                questsByCategory,
                completedIds,
              ).map((category) => {
                const categoryQuests = questsByCategory.get(category);
                if (!categoryQuests?.length) return null;
                void location.pathname;
                const sortedQuests = sortQuestsForCompanionList(
                  categoryQuests,
                  completedIds,
                );
                const pendingInCategory = sortedQuests.filter(
                  (quest) => !completedIds.has(quest.id),
                );
                const doneInCategory = sortedQuests.filter((quest) =>
                  completedIds.has(quest.id),
                );
                const visibleQuests =
                  pendingInCategory.length > 0
                    ? [...pendingInCategory, ...doneInCategory.slice(0, 2)]
                    : doneInCategory;
                const hiddenDone =
                  pendingInCategory.length > 0
                    ? Math.max(0, doneInCategory.length - 2)
                    : 0;

                return (
                  <li key={category} className="portal-tour-quest-group">
                    <p className="portal-tour-quest-group-title">
                      {PORTAL_TOUR_CATEGORY_LABELS[category]}
                    </p>
                    <ul className="portal-tour-quest-group-list">
                      {visibleQuests.map((quest) => {
                        const done = completedIds.has(quest.id);
                        const visualState = resolveQuestListVisualState(
                          quest,
                          done,
                        );
                        const guide = resolveQuestGuide(quest, done);
                        const hintOpen = hintQuestId === quest.id;
                        const visualClass = questListVisualClassName(visualState);
                        const hintText = resolveQuestListHint(
                          quest,
                          visualState,
                          guide?.steps[0] ?? null,
                        );

                        return (
                          <li
                            key={quest.id}
                            className={[
                              "portal-tour-quest-item",
                              visualClass,
                              hintOpen ? "is-hint-open" : "",
                              justCompletedQuestId === quest.id
                                ? "is-just-done"
                                : "",
                            ]
                              .filter(Boolean)
                              .join(" ")}
                          >
                            <span className="portal-tour-quest-check" aria-hidden>
                              {done ? <Check size={12} strokeWidth={3} /> : null}
                            </span>
                            <div className="portal-tour-quest-copy">
                              <span className="portal-tour-quest-title">
                                {quest.title}
                                {visualState === "near" ? (
                                  <span className="portal-tour-quest-near-badge">
                                    Perto
                                  </span>
                                ) : null}
                                {!done && isQuestMarkedNew(catalog, quest.id) ? (
                                  <span className="portal-tour-quest-new">
                                    Novo
                                  </span>
                                ) : null}
                                {!done && quest.optional ? (
                                  <span className="portal-tour-quest-optional">
                                    Opcional
                                  </span>
                                ) : null}
                              </span>
                              {hintText ? (
                                <span className="portal-tour-quest-hint">
                                  {hintText}
                                </span>
                              ) : null}
                              {!done && guide ? (
                                <>
                                  <button
                                    type="button"
                                    className="portal-tour-quest-hint-btn"
                                    onClick={() => toggleQuestHint(quest.id)}
                                    aria-expanded={hintOpen}
                                    aria-controls={`portal-tour-hint-${quest.id}`}
                                  >
                                    <Lightbulb size={13} aria-hidden />
                                    {hintOpen ? "Ocultar" : "Dica"}
                                  </button>
                                  {hintOpen ? (
                                    <>
                                      {guide.kind === "unlock" ? (
                                        <p className="portal-tour-quest-unlock-label">
                                          Como desbloquear
                                        </p>
                                      ) : null}
                                      <ol
                                        id={`portal-tour-hint-${quest.id}`}
                                        className="portal-tour-quest-steps"
                                      >
                                        {guide.steps.map((step) => (
                                          <li key={step}>{step}</li>
                                        ))}
                                      </ol>
                                    </>
                                  ) : null}
                                </>
                              ) : null}
                            </div>
                          </li>
                        );
                      })}
                      {hiddenDone > 0 ? (
                        <li className="portal-tour-quest-more-done">
                          +{hiddenDone} concluído{hiddenDone === 1 ? "" : "s"}
                        </li>
                      ) : null}
                    </ul>
                  </li>
                );
              })}
            </ul>
          </div>
        ) : null}
      </div>
      ) : null}
    </div>,
    document.body,
  );
}
