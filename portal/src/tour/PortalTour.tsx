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
  resolveShouldShowPortalTour,
  shouldSkipPortalTourSyncOnOpen,
  syncPortalTourCompleted,
  syncPortalTourQuestCompleted,
  syncPortalTourStarted,
  shouldAutoOpenPortalTourPanel,
  canReopenPortalTourPanel,
} from "./portalTourPersistence";
import {
  getPortalTourQuests,
  groupQuestsByCategory,
  isQuestAvailable,
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
import { setPortalTourSidebarPanel } from "./portalTourSidebar";
import { clearPortalTourTimers, schedulePortalTourTimer } from "./portalTourTimers";
import { closeAppLauncher } from "../utils/appLauncher";
import { usePortalTourHighlights } from "./usePortalTourHighlights";
import { PortalTourCompletionModal } from "./PortalTourCompletionModal";
import {
  PortalTourLevelUpOverlay,
  type PortalTourLevelUpOverlayState,
} from "./PortalTourLevelUpOverlay";
import { subscribePortalTourSyncStatus } from "./portalTourSyncStatus";
import {
  runPortalTourConfetti,
  runPortalTourLevelUpCelebration,
} from "./portalTourCelebration";
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
  const [levelCelebrating, setLevelCelebrating] = useState(false);
  const [levelUpOverlay, setLevelUpOverlay] =
    useState<PortalTourLevelUpOverlayState | null>(null);
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
    active && panelOpen,
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
    document.documentElement.dataset.portalTourCompanion = "false";
    setActive(false);
    setPanelOpen(false);
    setExpanded(true);
    setToast(null);
    setHintQuestId(null);
    setSuccessFlashQuestId(null);
    setJustCompletedQuestId(null);
    setXpBarBump(false);
    setLevelCelebrating(false);
    setLevelUpOverlay(null);
    setBanner(null);
    setShowCompletionModal(false);
    confettiCleanupRef.current?.();
    confettiCleanupRef.current = null;
    publishPortalTourSession({
      sessionActive: false,
      panelOpen: false,
      completed: true,
      requiredDone,
      requiredTotal,
      progressPercent: 100,
      explorerLevel: explorerLevel.label,
    });
  }, [user?.id, coreApi, requiredDone, requiredTotal, explorerLevel.label]);

  const hidePanel = useCallback(() => {
    setPanelOpen(false);
    setExpanded(false);
    setShowCompletionModal(false);
    confettiCleanupRef.current?.();
    confettiCleanupRef.current = null;
    document.documentElement.dataset.portalTourActive = "false";
    document.documentElement.dataset.portalTourCompanion = "false";
    clearTourPulseTargets();
  }, []);

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
      const previousLevel = resolveExplorerLevel(previousPercent);

      if (levelUp && !reachingFullCompletion) {
        if (shouldPlayPortalTourAnimations()) {
          confettiCleanupRef.current?.();
          confettiCleanupRef.current = runPortalTourLevelUpCelebration();
          setLevelCelebrating(true);
          schedulePortalTourTimer(() => setLevelCelebrating(false), 1400);
        }

        const overlayId = `level-up-${levelUp.minPercent}-${questId}`;
        setLevelUpOverlay({
          id: overlayId,
          questTitle: quest.title,
          xp: resolveQuestXp(quest),
          categoryLabel: PORTAL_TOUR_CATEGORY_LABELS[quest.category],
          previousLevelLabel: previousLevel.label,
          levelLabel: levelUp.label,
          message: levelUpMessage(levelUp),
          progressPercent: nextPercent,
          categoryCompleteLabel: categoryLabel ?? undefined,
        });
        schedulePortalTourTimer(() => {
          setLevelUpOverlay((current) =>
            current?.id === overlayId ? null : current,
          );
        }, 6200);
      } else {
        setToast({
          id: questId,
          title: quest.title,
          xp: resolveQuestXp(quest),
          categoryLabel: PORTAL_TOUR_CATEGORY_LABELS[quest.category],
        });
        schedulePortalTourTimer(() => {
          setToast((current) => (current?.id === questId ? null : current));
        }, 2800);

        if (categoryLabel) {
          const bannerId = `category-${quest.category}`;
          setBanner({
            id: bannerId,
            message: `Área «${categoryLabel}» concluída!`,
          });
          schedulePortalTourTimer(() => {
            setBanner((current) => (current?.id === bannerId ? null : current));
          }, 3400);
        }
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
    if (canReopenPortalTourPanel(remote)) {
      setCompletedIds(hydratePortalTourSessionFromRemote(remote));
    }

    if (!resolveShouldShowPortalTour(user.id, remote)) return;

    const timer = window.setTimeout(() => {
      setActive(true);
      setPanelOpen(shouldAutoOpenPortalTourPanel(remote));
    }, 900);
    return () => window.clearTimeout(timer);
  }, [remoteReady, coreLoaded, user?.id]);

  useEffect(() => {
    if (!active) return;
    if (shouldSkipPortalTourSyncOnOpen(remoteProgressRef.current)) return;
    syncPortalTourStarted(coreApi, Array.from(completedRef.current));
  }, [active, coreApi]);

  useEffect(() => {
    const tourUiActive = active && panelOpen && !showCompletionModal;
    document.documentElement.dataset.portalTourActive = tourUiActive
      ? "true"
      : "false";
    document.documentElement.dataset.portalTourCompanion = tourUiActive
      ? "true"
      : "false";
    return () => {
      document.documentElement.dataset.portalTourActive = "false";
      document.documentElement.dataset.portalTourCompanion = "false";
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
      setLevelUpOverlay(null);
      setShowCompletionModal(false);
      confettiCleanupRef.current?.();
      confettiCleanupRef.current = null;
      setExpanded(true);
      setActive(true);
      setPanelOpen(true);
    };
    const reopenPortalTourFromRemote = () => {
      if (completedRef.current.size > 0) return;
      const hydrated = hydratePortalTourSessionFromRemote(remoteProgressRef.current);
      completedRef.current = hydrated;
      setCompletedIds(hydrated);
    };
    const onOpenPanel = () => {
      if (!active) {
        reopenPortalTourFromRemote();
        setActive(true);
      }
      showPanel();
    };
    const onResume = () => {
      autoStartCheckedRef.current = true;
      reopenPortalTourFromRemote();
      setActive(true);
      showPanel();
    };
    window.addEventListener(DELPI_PORTAL_TOUR_START_EVENT, onStart);
    window.addEventListener(DELPI_PORTAL_TOUR_OPEN_PANEL_EVENT, onOpenPanel);
    window.addEventListener(DELPI_PORTAL_TOUR_RESUME_EVENT, onResume);
    return () => {
      window.removeEventListener(DELPI_PORTAL_TOUR_START_EVENT, onStart);
      window.removeEventListener(DELPI_PORTAL_TOUR_OPEN_PANEL_EVENT, onOpenPanel);
      window.removeEventListener(DELPI_PORTAL_TOUR_RESUME_EVENT, onResume);
    };
  }, [active, showPanel, catalog]);

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
        hidePanel();
      }
    };

    window.addEventListener("keydown", onKeyDown, true);
    return () => window.removeEventListener("keydown", onKeyDown, true);
  }, [active, panelOpen, hidePanel, showCompletionModal, closeCompletionCelebration]);

  if (!active) return null;

  const hasTransientFeedback = Boolean(
    toast ||
      banner ||
      levelUpOverlay ||
      showCompletionModal ||
      levelCelebrating,
  );
  const shouldRenderRoot = panelOpen || hasTransientFeedback;
  if (!shouldRenderRoot) return null;

  const dismissLevelUpOverlay = () => setLevelUpOverlay(null);

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

      {levelUpOverlay ? (
        <PortalTourLevelUpOverlay
          celebration={levelUpOverlay}
          onClose={dismissLevelUpOverlay}
        />
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
        className={`portal-tour-quest-panel${expanded ? " is-expanded" : " is-collapsed"}${levelCelebrating ? " is-level-up" : ""}`}
      >
        <div className="portal-tour-quest-toggle-row">
          <button
            type="button"
            className="portal-tour-quest-toggle"
            onClick={() => setExpanded((current) => !current)}
            aria-expanded={expanded}
          >
            <span className="portal-tour-quest-toggle-main">
              <Trophy size={18} aria-hidden />
              <span className="portal-tour-quest-toggle-label">
                Descubra o portal
              </span>
              <span className="portal-tour-quest-badge" aria-hidden>
                {requiredDone}/{requiredTotal}
              </span>
              <span
                className={`portal-tour-level-badge${levelCelebrating ? " is-celebrating" : ""}`}
              >
                {explorerLevel.label}
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
            aria-label="Fechar painel de descobertas"
          >
            <X size={18} aria-hidden />
          </button>
        </div>

        {expanded ? (
          <div className="portal-tour-quest-body">
            <p className="portal-tour-quest-intro">
              Explore a Minha DELPI no seu ritmo — ordem livre, por área do
              portal. Siga o destaque azul ou toque em <strong>Dica</strong> em
              cada desafio.
              {contextLabel ? (
                <span className="portal-tour-quest-context">{contextLabel}</span>
              ) : null}
            </p>

            <div
              className="portal-tour-xp-bar"
              role="progressbar"
              aria-valuenow={progressPercent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Progresso: ${requiredDone} de ${requiredTotal} desafios — ${earnedXp} XP`}
            >
              <div
                className={`portal-tour-xp-bar-fill${xpBarBump ? " is-bump" : ""}`}
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <p className="portal-tour-xp-summary" aria-hidden>
              {earnedXp} XP · {progressPercent}%
            </p>

            <ul className="portal-tour-quest-list">
              {PORTAL_TOUR_CATEGORY_ORDER.map((category) => {
                const categoryQuests = questsByCategory.get(category);
                if (!categoryQuests?.length) return null;

                return (
                  <li key={category} className="portal-tour-quest-group">
                    <p className="portal-tour-quest-group-title">
                      {PORTAL_TOUR_CATEGORY_LABELS[category]}
                    </p>
                    <ul className="portal-tour-quest-group-list">
                      {categoryQuests.map((quest) => {
                        const done = completedIds.has(quest.id);
                        const available = isQuestAvailable(quest);
                        const guide = resolveQuestGuide(quest, done);
                        const hintOpen = hintQuestId === quest.id;

                        return (
                          <li
                            key={quest.id}
                            className={`portal-tour-quest-item${done ? " is-done" : ""}${!done && available ? " is-available" : ""}${!available && !done ? " is-unavailable" : ""}${hintOpen ? " is-hint-open" : ""}${justCompletedQuestId === quest.id ? " is-just-done" : ""}`}
                          >
                            <span className="portal-tour-quest-check" aria-hidden>
                              {done ? <Check size={14} strokeWidth={3} /> : null}
                            </span>
                            <div className="portal-tour-quest-copy">
                              <span className="portal-tour-quest-title">
                                {quest.title}
                                {isQuestMarkedNew(catalog, quest.id) ? (
                                  <span className="portal-tour-quest-new">
                                    novidade
                                  </span>
                                ) : null}
                                {quest.optional ? (
                                  <span className="portal-tour-quest-optional">
                                    opcional
                                  </span>
                                ) : null}
                              </span>
                              <span className="portal-tour-quest-hint">
                                {done
                                  ? "Concluído — parabéns!"
                                  : available
                                    ? quest.hint
                                    : guide?.steps[0] ?? "Disponível em breve."}
                              </span>
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
                                    {hintOpen ? "Ocultar dica" : "Dica"}
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
