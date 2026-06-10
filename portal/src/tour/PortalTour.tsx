import { useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useLocation } from "react-router-dom";
import { Check, ChevronDown, ChevronUp, Lightbulb, Sparkles, Trophy } from "lucide-react";
import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { CoreApi } from "../data/coreApi";
import "./PortalTour.css";
import {
  clearTourPulseTargets,
  watchTourQuests,
} from "./portalTourInteraction";
import {
  hydrateCompletedQuestIds,
  loadPortalTourProgress,
  markPortalTourCompletedEverywhere,
  resolveShouldShowPortalTour,
  syncPortalTourFinished,
  syncPortalTourQuestCompleted,
  syncPortalTourStarted,
} from "./portalTourPersistence";
import {
  countCompletedRequired,
  countRequiredQuests,
  getPortalTourQuests,
  groupQuestsByCategory,
  isQuestAvailable,
  PORTAL_TOUR_CATEGORY_LABELS,
  PORTAL_TOUR_CATEGORY_ORDER,
} from "./portalTourQuests";
import {
  getTourContextLabel,
  resolveQuestGuide,
} from "./portalTourQuestGuide";
import { setPortalTourSidebarPanel } from "./portalTourSidebar";
import { clearPortalTourTimers, schedulePortalTourTimer } from "./portalTourTimers";
import { closeAppLauncher } from "../utils/appLauncher";
import { usePortalTourHighlights } from "./usePortalTourHighlights";

export const DELPI_PORTAL_TOUR_START_EVENT = "DELPI_PORTAL_TOUR_START";

export function startPortalTour() {
  window.dispatchEvent(new CustomEvent(DELPI_PORTAL_TOUR_START_EVENT));
}

type QuestToast = {
  id: string;
  title: string;
};

export function PortalTour() {
  const { user, coreLoaded, getAccessToken, refreshToken } = useContext(AuthContext);
  const location = useLocation();
  const [active, setActive] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [completedIds, setCompletedIds] = useState<Set<string>>(() => new Set());
  const [toast, setToast] = useState<QuestToast | null>(null);
  const [remoteReady, setRemoteReady] = useState(false);
  const [hintQuestId, setHintQuestId] = useState<string | null>(null);
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

  const quests = useMemo(
    () => getPortalTourQuests({ canAccessAdmin }),
    [canAccessAdmin],
  );

  const questsByCategory = useMemo(
    () => groupQuestsByCategory(quests),
    [quests],
  );

  const requiredTotal = useMemo(() => countRequiredQuests(quests), [quests]);
  const requiredDone = useMemo(
    () => countCompletedRequired(quests, completedIds),
    [quests, completedIds],
  );
  const progressPercent =
    requiredTotal > 0 ? Math.round((requiredDone / requiredTotal) * 100) : 0;
  const allRequiredDone = requiredDone >= requiredTotal;

  const highlights = usePortalTourHighlights(active, quests, completedIds);

  const contextLabel = useMemo(
    () => (active ? getTourContextLabel() : ""),
    [active, location.pathname, highlights],
  );

  useEffect(() => {
    completedRef.current = completedIds;
  }, [completedIds]);

  const finish = useCallback(
    (completed: boolean) => {
      if (user?.id) {
        if (completed) {
          markPortalTourCompletedEverywhere(user.id);
        }
        syncPortalTourFinished(coreApi, completed, Array.from(completedRef.current));
      }
      clearTourPulseTargets();
      clearPortalTourTimers();
      closeAppLauncher();
      setPortalTourSidebarPanel("none");
      document.documentElement.dataset.portalTourActive = "false";
      document.documentElement.dataset.portalTourCompanion = "false";
      setActive(false);
      setExpanded(true);
      setCompletedIds(new Set());
      setToast(null);
      setHintQuestId(null);
    },
    [user?.id, coreApi],
  );

  const toggleQuestHint = useCallback((questId: string) => {
    setHintQuestId((current) => (current === questId ? null : questId));
  }, []);

  const completeQuest = useCallback(
    (questId: string) => {
      if (completedRef.current.has(questId)) return;

      const quest = quests.find((item) => item.id === questId);
      if (!quest) return;

      setCompletedIds((current) => {
        if (current.has(questId)) return current;
        const next = new Set(current);
        next.add(questId);
        syncPortalTourQuestCompleted(coreApi, Array.from(next), questId);
        return next;
      });

      setToast({ id: questId, title: quest.title });
      schedulePortalTourTimer(() => {
        setToast((current) => (current?.id === questId ? null : current));
      }, 2600);
    },
    [quests, coreApi],
  );

  useEffect(() => {
    if (!coreLoaded || !user?.id) return;

    let cancelled = false;
    void loadPortalTourProgress(coreApi).then((remote) => {
      if (cancelled) return;
      remoteProgressRef.current = remote;
      setRemoteReady(true);
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
    if (remote?.status === "exploring" && remote.completedQuestIds.length > 0) {
      setCompletedIds(hydrateCompletedQuestIds(remote));
    }

    if (!resolveShouldShowPortalTour(user.id, remote)) return;

    const timer = window.setTimeout(() => setActive(true), 900);
    return () => window.clearTimeout(timer);
  }, [remoteReady, coreLoaded, user?.id]);

  useEffect(() => {
    if (!active) return;
    syncPortalTourStarted(coreApi, Array.from(completedRef.current));
  }, [active, coreApi]);

  useEffect(() => {
    document.documentElement.dataset.portalTourActive = active ? "true" : "false";
    document.documentElement.dataset.portalTourCompanion = active ? "true" : "false";
    return () => {
      document.documentElement.dataset.portalTourActive = "false";
      document.documentElement.dataset.portalTourCompanion = "false";
    };
  }, [active]);

  useEffect(() => {
    const onStart = () => {
      clearPortalTourTimers();
      autoStartCheckedRef.current = true;
      setCompletedIds(new Set());
      setToast(null);
      setHintQuestId(null);
      setExpanded(true);
      setActive(true);
    };
    window.addEventListener(DELPI_PORTAL_TOUR_START_EVENT, onStart);
    return () =>
      window.removeEventListener(DELPI_PORTAL_TOUR_START_EVENT, onStart);
  }, []);

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
    if (!active) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        finish(false);
      }
    };

    window.addEventListener("keydown", onKeyDown, true);
    return () => window.removeEventListener("keydown", onKeyDown, true);
  }, [active, finish]);

  if (!active) return null;

  return createPortal(
    <div
      className="portal-tour-root portal-tour-root--gamified"
      role="region"
      aria-label="Tour de descobertas do portal"
    >
      {highlights.map((rect) => (
        <div
          key={rect.questId}
          className="portal-tour-highlight-ring"
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
          <span>
            <strong>{toast.title}</strong> concluído!
          </span>
        </div>
      ) : null}

      <div
        className={`portal-tour-quest-panel${expanded ? " is-expanded" : " is-collapsed"}`}
      >
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
          </span>
          {expanded ? (
            <ChevronDown size={18} aria-hidden />
          ) : (
            <ChevronUp size={18} aria-hidden />
          )}
        </button>

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
              aria-label={`Progresso: ${requiredDone} de ${requiredTotal} desafios`}
            >
              <div
                className="portal-tour-xp-bar-fill"
                style={{ width: `${progressPercent}%` }}
              />
            </div>

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
                            className={`portal-tour-quest-item${done ? " is-done" : ""}${!done && available ? " is-available" : ""}${!available && !done ? " is-unavailable" : ""}${hintOpen ? " is-hint-open" : ""}`}
                          >
                            <span className="portal-tour-quest-check" aria-hidden>
                              {done ? <Check size={14} strokeWidth={3} /> : null}
                            </span>
                            <div className="portal-tour-quest-copy">
                              <span className="portal-tour-quest-title">
                                {quest.title}
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

            <div className="portal-tour-quest-footer">
              <button
                type="button"
                className="portal-tour-btn portal-tour-btn--ghost"
                onClick={() => finish(false)}
              >
                Pular
              </button>
              <button
                type="button"
                className="portal-tour-btn portal-tour-btn--primary"
                onClick={() => finish(true)}
              >
                {allRequiredDone ? (
                  <>
                    <Sparkles size={16} aria-hidden />
                    Concluir
                  </>
                ) : (
                  `Concluir (${requiredDone}/${requiredTotal})`
                )}
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>,
    document.body,
  );
}
