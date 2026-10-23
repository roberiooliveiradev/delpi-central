import { useEffect, useMemo, useRef, useState } from "react";
import type { UIEvent as ReactUIEvent } from "react";

import { DELIA_ROOT_CLASS } from "./ui/deliaUi";
import { DeliaReception } from "./ui/DeliaReception";
import { DeliaComposer } from "./ui/DeliaComposer";
import { DeliaConversationPage } from "./ui/DeliaConversationPage";
import { DeliaTurnContextPanel } from "./ui/contextPanel";
import { ConversationTimeline } from "./ui/ConversationTimeline";
import type { ConversationDisplayTurn } from "./ui/ConversationTimeline";
import {
  DeliaInteractionError,
  INTERACTION_INPUT_CHAR_LIMIT,
  buildInteractionContext,
  submitInteractionTurn,
} from "./api/interactionClient";
import type {
  DeliaConfirmationRequest,
  DeliaTurnCommand,
  DeliaWorkspaceContext,
} from "./api/interactionClient";
import {
  ActivityViewer,
  UnifiedAvatar,
  ConversationError,
  ConversationHeader,
  ConversationStarterSuggestions,
  ConversationWorkspace,
  ConversationScrollNavigator,
  ConversationQueue,
  HelpTooltip,
  IconButton,
  isSegmentedPcmCaptureSupported,
} from "@delpi/plugin-ui/index";
import type {
  ConversationQueueItem,
  ConversationStarterSuggestion,
} from "@delpi/plugin-ui/index";
import { Undo2 } from "lucide-react";
import {
  DELIA_ACTIVITY_PENDING_VIEW,
  buildLiveActivityView,
} from "./activity/activityView";
import type { DeliaActivityEvent } from "./api/interactionClient";
import {
  DELIA_DEMO_BANNER,
  demoConfirmationAck,
  demoTurnOutcome,
  resolveDemoScenario,
} from "./demo/demoMode";
import { resolveAudioQaAdmission } from "./audio/audioCaptureQaAdmission";
import { resolveAudioCaptureLimits } from "./audio/audioCaptureTestAdmission";
import { resolveStarterSuggestions } from "./suggestions/starterSuggestions";
import { useDraftRecovery } from "./draft/draftRecovery";
import {
  demoMoveItem,
  demoRemoveItem,
  resolveQueueDemo,
} from "./demo/queueDemo";
import { useConversationQueue } from "./queue/conversationQueue";
import {
  endDictationSession,
  fetchDictationStatus,
  openDictationSession,
  streamDictationSegment,
  transcribeDictationAudio,
} from "./api/dictationClient";
import type { DeliaDictationStatus } from "./api/dictationClient";
import { useCurrentUserIdentity } from "./identity/currentUser";

/** Host props from Portal AppHost — presentation/transport only. */
export type AppProps = {
  getAccessToken?: () => string | undefined;
  basePath?: string;
  pathname?: string;
  search?: string;
  alternateEntry?: string;
  appRoutes?: Array<{ path: string; entry?: string; openInNewTab?: boolean }>;
  routeLabel?: string;
  /** Frontend presentation hint only — never backend authorization authority. */
  permissions?: string[];
  /** Frontend presentation hint only — never backend authorization authority. */
  isSuperadmin?: boolean;
  /** Bounded untrusted workspace hint getter (§6.130) — called per
   *  turn so the freshest published context is sent. Never authority. */
  getWorkspaceContext?: () => DeliaWorkspaceContext | null;
};

const TOKEN_UNAVAILABLE_MESSAGE =
  "Token de acesso indisponível. Recarregue pelo Portal.";

/** Autoscroll engagement threshold — only follow new turns when the
 *  reader is already near the end (doc 69 §10). */
const NEAR_BOTTOM_THRESHOLD_PX = 96;

/**
 * C3-INTERACTION-RUNTIME-01 + C3-INTERACTION-CONTINUITY-01 +
 * DELIA-UX-S2-RECEPTION-CONVERSATION-SHELL-01.
 *
 * Bounded transient multi-turn interaction: rendered turns are kept in
 * React memory only and resent as untrusted prior context on each new
 * turn. No browser storage and no backend persistence — a reload
 * resets the conversation. permissions / isSuperadmin remain host
 * presentation hints and are never sent as backend authority.
 *
 * The same component serves the full page and the global dock: a
 * single shell (reception → timeline → composer) adapts to the
 * container width — no parallel runtime, no fake capabilities.
 */
export default function App({
  getAccessToken,
  getWorkspaceContext,
  permissions: _permissions,
  isSuperadmin: _isSuperadmin,
}: AppProps) {
  void _permissions;
  void _isSuperadmin;

  // Demo mode is resolved once at mount — it is a dev/preview harness,
  // not a runtime state. Gated off in production builds.
  const [demoScenario] = useState(() =>
    resolveDemoScenario(window.location.search),
  );
  // Audio capture QA admission — dev/QA bundles only, explicit query
  // param required; production bundles never admit it. QA fixture
  // limits, not approved production media policy.
  const [audioQaAdmission] = useState(() =>
    resolveAudioQaAdmission(window.location.search),
  );
  // Doc 71 (F03-A): conversation queue surface. No backend queue
  // contract exists today, so production items stay EMPTY and the
  // component renders nothing. The `?delia-demo-queue=` QA fixture
  // (demo-gated bundle) is the only source of visible items.
  const [queueDemo, setQueueDemo] = useState(() =>
    resolveQueueDemo(window.location.search),
  );
  const [queueExpanded, setQueueExpanded] = useState(false);
  const userIdentity = useCurrentUserIdentity(getAccessToken);
  // VD-F03 dictation.transcription.v1 admission — read once per mount
  // from the backend status boundary. Unavailable (or transport-failed)
  // status keeps the honest local-only capture preview; it never
  // fabricates a transcribing state.
  const [dictationStt, setDictationStt] = useState<DeliaDictationStatus | null>(
    null,
  );
  useEffect(() => {
    if (!getAccessToken) return;
    const abort = new AbortController();
    fetchDictationStatus({
      getAccessToken: () => getAccessToken() ?? null,
      signal: abort.signal,
    })
      .then((status) => {
        if (!abort.signal.aborted) setDictationStt(status);
      })
      .catch(() => {
        // Admission transport failure is non-fatal: capture stays
        // local-only preview — honest, never a fabricated STT state.
      });
    return () => abort.abort();
  }, [getAccessToken]);
  const dictationSttAvailable = dictationStt?.available === true;
  // VD-F06: progressive dictation is admitted only when the contract
  // reports incremental.available AND this context can slice real PCM
  // (capability check owned by plugin-ui). Anything less keeps the
  // honest VD-F03 fallback — never a simulated live transcript.
  const incrementalDictationAdmitted =
    dictationStt?.incremental?.available === true &&
    getAccessToken != null &&
    isSegmentedPcmCaptureSupported();
  // Local audio capture — available to every legitimately admitted
  // DÉLIA user (delia.access enforced upstream by Portal/Core before
  // this MFE mounts). No dedicated audio permission, URL param or build
  // flag gates it (PM decision REMOVE-EXTRA-PERMISSION-AND-PRODUCTION-FIX-01).
  // Browser/secure-context support stays fail-closed inside
  // AudioRecorderControl. VD-F05: effective limits are
  // min(product 300 s decision, contract-published limits) — the
  // composer never admits a duration the backend does not accept.
  const audioAdmission =
    audioQaAdmission ?? resolveAudioCaptureLimits(dictationStt);
  const [input, setInput] = useState("");
  // F02-A-R1 — starter suggestions (doc 93 §16): the four default
  // questions are visible to every admitted user in production;
  // selecting one fills the controlled draft — never submits.
  const [starterItems] = useState<readonly ConversationStarterSuggestion[]>(
    () => resolveStarterSuggestions(),
  );
  const [suggestionNote, setSuggestionNote] = useState<string | null>(null);
  const [turns, setTurns] = useState<ConversationDisplayTurn[]>([]);
  // Latest-turns mirror: queued dispatch must build prior-turn context
  // from the state that already committed — never a stale closure
  // missing the just-finished response (doc 122 §11 dispatch gate).
  const turnsRef = useRef<ConversationDisplayTurn[]>([]);
  turnsRef.current = turns;
  const [loading, setLoading] = useState(false);
  // Doc 71/122 §11 (F03-B): ephemeral, memory-only conversation queue.
  // The fixture (`?delia-demo-queue=`) stays a pure VISUAL override —
  // while it is admitted the real queue affordance is not offered, so
  // QA states never mix with real pendings.
  const conversationQueue = useConversationQueue();
  const pendingQueueItems = conversationQueue.items;
  /**
   * PAUSED_AFTER_ERROR: any non-clean end of the in-flight turn
   * (error, timeout, abort, user stop) freezes automatic dispatch
   * until the user explicitly resumes — pendings are preserved,
   * never silently retried or dropped.
   */
  const [queuePaused, setQueuePaused] = useState(false);
  // Progressive activity (doc 70 §16): observed events for the
  // in-flight turn only — transient, request-scoped, never persisted.
  const [liveEvents, setLiveEvents] = useState<DeliaActivityEvent[]>([]);
  const liveActivityView = useMemo(
    () => buildLiveActivityView(liveEvents),
    [liveEvents],
  );
  const [respondingTurnId, setRespondingTurnId] = useState<string | null>(null);
  // Prompt 5: transient Context-panel message selection — ephemeral
  // conversation state only, never persisted. The panel's open state
  // is paired with the selection: "Ver contexto" selects + opens in
  // one action and closing the panel clears the highlight.
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(null);
  const [contextOpen, setContextOpen] = useState(false);
  const handleContextOpenChange = (open: boolean) => {
    setContextOpen(open);
    if (!open) setSelectedTurnId(null);
  };
  const handleSelectTurnContext = (turnId: string) => {
    if (selectedTurnId === turnId && contextOpen) {
      setContextOpen(false);
      setSelectedTurnId(null);
      return;
    }
    setSelectedTurnId(turnId);
    setContextOpen(true);
  };
  const selectedTurn = useMemo(
    () => turns.find((turn) => turn.id === selectedTurnId) ?? null,
    [turns, selectedTurnId],
  );
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  /** Guards late completions (including transports ignoring abort) after STOP. */
  const requestEpochRef = useRef(0);
  const activeStopEligibleRef = useRef(false);
  const [requestMode, setRequestMode] = useState<
    "idle" | "responding_cancelable" | "responding_not_cancelable" | "stopping"
  >("idle");
  const demoSeqRef = useRef(0);
  const scrollRegionRef = useRef<HTMLDivElement | null>(null);
  const turnsEndRef = useRef<HTMLDivElement | null>(null);
  const nearBottomRef = useRef(true);
  const [showScrollNavigator, setShowScrollNavigator] = useState(false);

  useEffect(() => {
    const end = turnsEndRef.current;
    const last = turns[turns.length - 1];
    // Follow the log only when the user just sent a turn or was
    // already reading near the end — never hijack scroll position.
    if (!end || !(nearBottomRef.current || last?.role === "user")) {
      return;
    }
    const viewport = scrollRegionRef.current;
    if (viewport) {
      viewport.scrollTop = viewport.scrollHeight;
      nearBottomRef.current = true;
      setShowScrollNavigator(false);
    }
  }, [turns, loading]);

  useEffect(
    () => () => {
      requestEpochRef.current += 1;
      abortRef.current?.abort();
    },
    [],
  );

  // Doc 102 — ConversationDraftRecovery: a single transient, in-memory
  // candidate born only from the explicit "Limpar rascunho" action.
  // Gates are evaluated lazily at undo time so a stale callback can
  // never restore into a different epoch/request state/draft.
  const {
    visible: draftRecoveryVisible,
    capture: captureDraftRecovery,
    undo: undoDraftRecovery,
    invalidate: invalidateDraftRecovery,
    pause: pauseDraftRecovery,
    resume: resumeDraftRecovery,
  } = useDraftRecovery({
    epoch: () => requestEpochRef.current,
    canRestore: () =>
      requestMode === "idle" && !loading && input === "",
    onRestore: (text) => {
      setInput(text);
      requestAnimationFrame(() => {
        const el = document.getElementById("delia-interaction-input");
        if (el instanceof HTMLTextAreaElement) {
          el.focus();
          el.setSelectionRange(text.length, text.length);
        }
      });
    },
  });

  // Any non-empty draft after a clear (typing, suggestion fill,
  // dictation merge) kills the candidate — undo must never overwrite
  // or merge new content.
  useEffect(() => {
    if (input !== "") invalidateDraftRecovery();
  }, [input, invalidateDraftRecovery]);

  // Sends, stops and any non-idle request state discard the candidate.
  useEffect(() => {
    if (loading || requestMode !== "idle") invalidateDraftRecovery();
  }, [loading, requestMode, invalidateDraftRecovery]);

  // A governed confirmation awaiting a human decision blocks queue
  // progression: admission never implies execution authority and the
  // queue must not auto-advance past an unresolved PREPARE/ACT gate.
  const hasPendingConfirmation = turns.some(
    (turn) =>
      turn.confirmationRequest != null && !turn.confirmationAnswered,
  );

  // READY_TO_DISPATCH → DISPATCHING: only a clean turn completion
  // (idle + not paused + no pending governed decision) releases the
  // head item through the existing sendTurn flow. takeNext consumes
  // the item atomically BEFORE the POST starts, so an effect re-run,
  // batched render or Strict Mode replay can never dispatch the same
  // pending twice. One turn in flight per conversation — always.
  const takeNextPending = conversationQueue.takeNext;
  useEffect(() => {
    if (loading || requestMode !== "idle") return;
    if (queuePaused) return;
    if (hasPendingConfirmation) return;
    const next = takeNextPending();
    if (!next) return;
    void sendTurn(next.text, undefined, { type: "MESSAGE" });
  }, [
    loading,
    requestMode,
    queuePaused,
    hasPendingConfirmation,
    pendingQueueItems,
    takeNextPending,
  ]);

  function handleTimelineScroll(event: ReactUIEvent<HTMLDivElement>) {
    const el = event.currentTarget;
    nearBottomRef.current =
      el.scrollHeight - el.scrollTop - el.clientHeight <
      NEAR_BOTTOM_THRESHOLD_PX;
    setShowScrollNavigator(turns.length > 0 && !nearBottomRef.current);
  }

  function handleGoToLatest() {
    const viewport = scrollRegionRef.current;
    if (!viewport) return;
    viewport.scrollTop = viewport.scrollHeight;
    nearBottomRef.current = true;
    setShowScrollNavigator(false);
  }

  async function sendTurn(
    value: string,
    confirmation?: {
      decision: "CONFIRM" | "REJECT";
      proposal_digest: string;
      preview_fingerprint: string;
      session_id: string;
    },
    command?: DeliaTurnCommand,
  ) {
    if (demoScenario) {
      setInput((current) => (current === value ? "" : current));
      void sendDemoTurn(value);
      return;
    }
    if (!getAccessToken || !getAccessToken()) {
      setError(TOKEN_UNAVAILABLE_MESSAGE);
      return;
    }
    // The sent text leaves the draft at admission — while the turn is
    // in flight the composer is free for the next question (F03-B).
    // Text the user typed afterwards is never touched; on failure the
    // message is restored only if the draft is still empty.
    setInput((current) => (current === value ? "" : current));

    const requestEpoch = ++requestEpochRef.current;
    const stopEligible = !confirmation && (!command || command.type === "MESSAGE");
    activeStopEligibleRef.current = stopEligible;
    setRequestMode(stopEligible ? "responding_cancelable" : "responding_not_cancelable");
    setRespondingTurnId(null);
    setLoading(true);
    setError(null);
    setLiveEvents([]);
    const controller = new AbortController();
    abortRef.current = controller;

    // Events observed during this request only — collected locally so
    // the final turn keeps the real step list even after the pending
    // viewer unmounts.
    const observed: DeliaActivityEvent[] = [];

    try {
      const result = await submitInteractionTurn(value, {
        getAccessToken,
        signal: controller.signal,
        context: buildInteractionContext(turnsRef.current),
        workspace: getWorkspaceContext?.() ?? undefined,
        confirmation,
        command,
        onActivityEvent: (event) => {
          if (requestEpoch !== requestEpochRef.current || controller.signal.aborted) return;
          observed.push(event);
          setLiveEvents([...observed]);
        },
      });
      if (requestEpoch !== requestEpochRef.current || controller.signal.aborted) return;
      setTurns((previous) => [
        // Only a response to a typed decision about THIS exact
        // proposal may close its card. Ordinary MESSAGE turns and
        // decisions about other proposals must preserve pending UI.
        ...previous.map((turn) => {
          const pending = turn.confirmationRequest;
          const decisionSent =
            confirmation &&
            (command?.type === "APPLY_PREPARED" ||
              command?.type === "REJECT_PREPARED");
          return decisionSent &&
            pending &&
            pending.proposal_digest === confirmation.proposal_digest &&
            pending.preview_fingerprint === confirmation.preview_fingerprint &&
            pending.session_id === confirmation.session_id
            ? { ...turn, confirmationAnswered: true }
            : turn;
        }),
        { id: result.user_turn_id, role: "user", content: value },
        {
          id: result.result_turn_id,
          role: "delia",
          content: result.content,
          epistemicClass: result.epistemic_class,
          limitations: result.limitations,
          groundingStatus: result.grounding_status,
          provenance: result.provenance,
          confirmationRequest: result.confirmation_request,
          presentation: result.presentation,
          presentationFault: result.presentationFault,
          contentFormat: result.contentFormat,
          markdownSource: result.markdownSource,
          authorizedLinks: [],
          // The authoritative result reconciles the observed steps —
          // the live view carries only events that actually arrived.
          activityView: buildLiveActivityView(observed) ?? undefined,
          // Prompt 5: retain the real observed events and the bounded
          // observability projection for the Context panel — request-
          // scoped, transient, never persisted.
          activityEvents: observed,
          observability: result.observability,
        },
      ]);
      setSelectedTurnId(result.result_turn_id);
      setRespondingTurnId(
        result.presentation?.messageKind && result.presentation.messageKind !== "RESULT"
          ? null
          : result.result_turn_id,
      );
      // Draft was already cleared at send admission; nothing to do here
      // — a queued completion never wipes text typed while in flight.
    } catch (submitError) {
      if (requestEpoch !== requestEpochRef.current || controller.signal.aborted) return;
      if (
        submitError instanceof Error &&
        submitError.name === "AbortError"
      ) {
        return;
      }
      // A failed send never loses what the user typed: the message is
      // restored to the draft only when it is still empty — text typed
      // after the send is never overwritten (doc 122 §11). A failed
      // turn also pauses the queue: pendings are preserved, never
      // auto-retried.
      setInput((current) => (current.trim() === "" ? value : current));
      setQueuePaused(true);
      setError(
        submitError instanceof DeliaInteractionError
          ? submitError.message
          : "Erro inesperado ao falar com a DÉLIA.",
      );
    } finally {
      if (requestEpoch === requestEpochRef.current) {
        abortRef.current = null;
        activeStopEligibleRef.current = false;
        setRequestMode("idle");
        setLoading(false);
        setLiveEvents([]);
      }
    }
  }

  /**
   * Demo-mode turn: appends the user turn and a clearly-marked
   * simulated response after a short honest delay. Never touches the
   * network, the backend, or any provider.
   */
  async function sendDemoTurn(value: string) {
    const seq = demoSeqRef.current++;
    const outcome = demoTurnOutcome(demoScenario!);
    setTurns((previous) => [
      ...previous,
      { id: `demo-user-${seq}`, role: "user", content: value },
    ]);
    setRespondingTurnId(null);
    setLoading(true);
    setError(null);
    await new Promise((resolve) => setTimeout(resolve, outcome.delayMs));
    setLoading(false);
    if (outcome.error) {
      // Same restore-if-still-empty rule as the real error path.
      setInput((current) => (current.trim() === "" ? value : current));
      setError(outcome.error);
      return;
    }
    setTurns((previous) => [
      ...previous,
      { id: `demo-delia-${seq}`, ...outcome.deliaTurn! },
    ]);
    setRespondingTurnId(
      outcome.deliaTurn?.presentation?.messageKind &&
      outcome.deliaTurn.presentation.messageKind !== "RESULT"
        ? null
        : `demo-delia-${seq}`,
    );
  }

  function handleStopResponse() {
    const controller = abortRef.current;
    if (!controller || controller.signal.aborted || !activeStopEligibleRef.current) return;
    activeStopEligibleRef.current = false;
    setRequestMode("stopping");
    // Invalidate the request synchronously before abort callbacks can fire.
    requestEpochRef.current += 1;
    controller.abort();
    abortRef.current = null;
    setLiveEvents([]);
    setRespondingTurnId(null);
    setLoading(false);
    setRequestMode("idle");
    // User-stopped turns never auto-continue the queue — pendings wait
    // for explicit resume. This is only a local transport stop;
    // backend completion is unknown.
    setQueuePaused(true);
  }

  /**
   * F03-B: admit the current draft into the ephemeral queue. Only a
   * successful local admission clears the draft — queued text is
   * frozen at enqueue time and never becomes backend authority.
   */
  function handleEnqueue() {
    const value = input.trim();
    if (!value) return;
    conversationQueue.enqueue(value);
    setInput("");
    setSuggestionNote(null);
  }

  function handleSubmit() {
    const value = input.trim();
    if (!value || loading || requestMode !== "idle") return;
    // A fresh question never jumps ahead of admitted pendings: with a
    // non-empty queue it joins the tail and the dispatcher keeps FIFO.
    if (pendingQueueItems.length > 0) {
      handleEnqueue();
      return;
    }
    void sendTurn(value, undefined, { type: "MESSAGE" });
  }

  /**
   * F02-A: a suggestion only edits the controlled draft — never
   * submits, never claims a capability. Fail-safe with a non-empty
   * draft (spec 93 §14): do not overwrite silently; show a light note
   * instead. Repeated clicks cannot duplicate text.
   */
  function handleStarterSelect(item: ConversationStarterSuggestion) {
    if (input.trim().length > 0) {
      setSuggestionNote(
        "Edite ou apague o texto atual antes de usar uma sugestão.",
      );
      return;
    }
    setSuggestionNote(null);
    const text = item.draftText.slice(0, INTERACTION_INPUT_CHAR_LIMIT);
    setInput(text);
    requestAnimationFrame(() => {
      const el = document.getElementById("delia-interaction-input");
      if (el instanceof HTMLTextAreaElement) {
        el.focus();
        el.setSelectionRange(text.length, text.length);
      }
    });
  }

  function handleComposerChange(value: string) {
    if (suggestionNote != null) setSuggestionNote(null);
    setInput(value);
  }

  /**
   * Doc 102: the explicit clear action snapshots the cleared text and
   * opens the transient undo notice — only for a non-empty draft and
   * only while the composer is in an allowed state.
   */
  function handleClearDraft(clearedValue: string) {
    if (clearedValue.length === 0) return;
    if (loading || requestMode !== "idle") return;
    captureDraftRecovery(clearedValue);
  }

  /**
   * Governed-write scope choice (§6.184): Executar/Cancelar send typed
   * decision commands bound to the exact pending proposal — the MFE
   * echoes the bounded digests back verbatim, never sees the raw owner
   * handle, and never makes any authorization decision. The shown text
   * is a display-only marker; no free text rides on the decision turn.
   */
  function handleConfirmation(
    request: DeliaConfirmationRequest,
    decision: "CONFIRM" | "REJECT",
  ) {
    if (loading) return;
    if (demoScenario) {
      // Visual-only: resolve the pending card and acknowledge locally.
      // No ACT, no confirmation echo, no backend call — the fixture
      // digests are non-authoritative demo values.
      const seq = demoSeqRef.current++;
      setTurns((previous) => [
        ...previous.map((turn) => {
          const pending = turn.confirmationRequest;
          return pending &&
            pending.proposal_digest === request.proposal_digest &&
            pending.preview_fingerprint === request.preview_fingerprint &&
            pending.session_id === request.session_id
            ? { ...turn, confirmationAnswered: true }
            : turn;
        }),
        { id: `demo-ack-${seq}`, ...demoConfirmationAck(decision) },
      ]);
      return;
    }
    const displayMarker =
      decision === "CONFIRM"
        ? "Decisão: executar a operação preparada."
        : "Decisão: cancelar a operação preparada.";
    void sendTurn(
      displayMarker,
      {
        decision,
        proposal_digest: request.proposal_digest,
        preview_fingerprint: request.preview_fingerprint,
        session_id: request.session_id,
      },
      {
        type:
          decision === "CONFIRM" ? "APPLY_PREPARED" : "REJECT_PREPARED",
      },
    );
  }

  // Real pendings → ConversationQueueItem view model. Every item in
  // the list is pending (the in-flight turn was already consumed), so
  // reorder/remove is always eligible; labels are the user's own text
  // — never model-derived titles.
  const queueViewItems: ConversationQueueItem[] = pendingQueueItems.map(
    (item, index) => ({
      id: item.id,
      label: item.text,
      ordinal: index + 1,
      status: "queued",
      canMoveUp: index > 0,
      canMoveDown: index < pendingQueueItems.length - 1,
      canRemove: true,
    }),
  );

  return (
    <div className={`${DELIA_ROOT_CLASS} dashboard-page dashboard-page--fill`}>
      <main className="delia-page-stack" aria-label="DÉLIA">
        <DeliaConversationPage
          context={<DeliaTurnContextPanel turn={selectedTurn} />}
          contextOpen={contextOpen}
          onContextOpenChange={handleContextOpenChange}
          conversation={(panelControls) => (
        <ConversationWorkspace
          className="delia-interaction"
          aria-label="Interação com a DÉLIA"
          bodyRef={scrollRegionRef}
          onBodyScroll={handleTimelineScroll}
          scrollNavigator={
            <ConversationScrollNavigator
              visible={turns.length > 0 && showScrollNavigator}
              onGoToLatest={handleGoToLatest}
            />
          }
          header={
            <ConversationHeader
              title="DÉLIA"
              subtitle="Inteligência operacional DELPI"
              leading={panelControls.leftToggle}
              actions={panelControls.rightToggle}
            />
          }
          banner={
            demoScenario || queueDemo ? (
              <div className="delia-demo-banner" role="note">
                {DELIA_DEMO_BANNER}
              </div>
            ) : null
          }
          footer={
            <>
              {error ? (
                <ConversationError
                  title={error}
                  description="Sua mensagem foi preservada."
                />
              ) : null}

              <ConversationQueue
                className="delia-conversation-queue"
                items={queueDemo?.items ?? queueViewItems}
                expanded={queueExpanded}
                loading={queueDemo?.loading}
                unavailable={queueDemo?.unavailable}
                error={queueDemo?.error ?? null}
                onExpandedChange={setQueueExpanded}
                onMoveUp={
                  queueDemo
                    ? (itemId) =>
                        setQueueDemo((d) =>
                          d
                            ? {
                                ...d,
                                items: demoMoveItem(d.items, itemId, "up"),
                              }
                            : d,
                        )
                    : (itemId) => conversationQueue.moveItem(itemId, "up")
                }
                onMoveDown={
                  queueDemo
                    ? (itemId) =>
                        setQueueDemo((d) =>
                          d
                            ? {
                                ...d,
                                items: demoMoveItem(d.items, itemId, "down"),
                              }
                            : d,
                        )
                    : (itemId) => conversationQueue.moveItem(itemId, "down")
                }
                onRemove={
                  queueDemo
                    ? (itemId) =>
                        setQueueDemo((d) =>
                          d
                            ? { ...d, items: demoRemoveItem(d.items, itemId) }
                            : d,
                        )
                    : (itemId) => conversationQueue.removeItem(itemId)
                }
              />

              {queuePaused &&
              pendingQueueItems.length > 0 &&
              !loading &&
              requestMode === "idle" &&
              !queueDemo ? (
                <div className="delia-queue-resume" role="status">
                  <span className="delia-queue-resume__text">
                    O envio das perguntas pendentes está pausado.
                  </span>
                  <button
                    type="button"
                    className="delia-queue-resume__action"
                    onClick={() => setQueuePaused(false)}
                  >
                    Retomar fila
                  </button>
                </div>
              ) : null}

              <DeliaComposer
                inputId="delia-interaction-input"
                value={input}
                onChange={handleComposerChange}
                onSubmit={handleSubmit}
                onEnqueue={queueDemo ? undefined : handleEnqueue}
                loading={loading}
                requestMode={requestMode}
                onStop={handleStopResponse}
                audioCaptureEnabled={audioAdmission != null}
                audioCaptureMaxDurationMs={audioAdmission?.maxDurationMs}
                audioCaptureMaxBytes={audioAdmission?.maxBytes}
                dictationTranscriber={
                  dictationSttAvailable && getAccessToken
                    ? (draft, signal) =>
                        transcribeDictationAudio(draft, {
                          getAccessToken: () => getAccessToken() ?? null,
                          signal,
                        })
                    : null
                }
                incrementalTransport={
                  incrementalDictationAdmitted
                    ? {
                        openSession: (signal) =>
                          openDictationSession({
                            getAccessToken: () => getAccessToken() ?? null,
                            signal,
                          }),
                        streamSegment: (input, signal) =>
                          streamDictationSegment(input, {
                            getAccessToken: () => getAccessToken() ?? null,
                            signal,
                          }),
                        endSession: (sessionId, signal) =>
                          endDictationSession(sessionId, {
                            getAccessToken: () => getAccessToken() ?? null,
                            signal,
                          }),
                      }
                    : null
                }
                incrementalMaxSessionMs={
                  dictationStt?.incremental?.maxSessionMs ?? null
                }
                incrementalMaxSegments={
                  dictationStt?.incremental?.maxSegments ?? null
                }
                onClearDraft={handleClearDraft}
                draftRecoveryAction={
                  draftRecoveryVisible ? (
                    <span
                      className="delia-draft-undo"
                      role="status"
                      onMouseEnter={pauseDraftRecovery}
                      onMouseLeave={resumeDraftRecovery}
                      onFocusCapture={pauseDraftRecovery}
                      onBlurCapture={resumeDraftRecovery}
                    >
                      <HelpTooltip wrap content="Desfazer limpeza do rascunho">
                        <IconButton
                          aria-label="Desfazer limpeza do rascunho"
                          onClick={undoDraftRecovery}
                        >
                          <Undo2 size={18} aria-hidden="true" />
                        </IconButton>
                      </HelpTooltip>
                    </span>
                  ) : undefined
                }
              />
            </>
          }
        >
          {turns.length > 0 ? (
            <ConversationTimeline
              turns={turns}
              loading={loading}
              respondingTurnId={respondingTurnId}
              onResponseMotionComplete={() => setRespondingTurnId(null)}
              selectedTurnId={selectedTurnId}
              onSelectTurn={handleSelectTurnContext}
              userIdentity={userIdentity}
              onConfirmation={handleConfirmation}
            />
          ) : (
            <>
              <DeliaReception userIdentity={userIdentity} />
              <ConversationStarterSuggestions
                items={starterItems}
                onSelect={handleStarterSelect}
                disabled={loading || requestMode !== "idle"}
                note={suggestionNote}
              />
            </>
          )}
          {loading ? (
            <div className="delia-interaction__pending-row">
              <span className="delia-interaction__pending-avatar" aria-hidden="true">
                <UnifiedAvatar kind="assistant" label="DÉLIA" size="sm" motionState="processing" />
              </span>
              <ActivityViewer
                {...(liveActivityView ?? DELIA_ACTIVITY_PENDING_VIEW)}
                className="delia-interaction__loading"
              />
            </div>
          ) : null}
          <div ref={turnsEndRef} aria-hidden="true" />
        </ConversationWorkspace>
        )} />
      </main>
    </div>
  );
}
