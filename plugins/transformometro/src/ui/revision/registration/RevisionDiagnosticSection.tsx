/**
 * Revision → Diagnóstico — canonical Portal surface for Diagnostic.
 *
 * Composition only: canonical GET list/detail, governed PREPARE → explicit
 * confirmation → COMMIT → verified read-back, realtime invalidation via the
 * existing `revisao:{id}` room. No domain rules, no client ids, no generic
 * edit/remove — only the 13 canonical material actions.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  ActionButton,
  EmptyState,
  NativeTextAreaControl,
  emptyStateCardBemClasses,
} from "@delpi/plugin-ui/index";

import type { AppProps } from "../../../App";
import { LoadingActivityCard } from "../../../components/LoadingActivityCard";
import { StateBox } from "../../../components/StateBox";
import {
  TmDetailFieldGrid,
  TmFormFieldShell,
  TmStatusBadge,
} from "../../../components/tmChromeUi";
import {
  commitGovernedProposal,
  fetchDiagnostic,
  listRevisionDiagnostics,
  prepareCreateDiagnostic,
  type DiagnosticListResult,
  type DiagnosticManageAction,
  type DiagnosticProposal,
  type DiagnosticReadContext,
} from "../../../data/api/transformometroDiagnosticApi";
import { fetchRevisaoEvidencias } from "../../../data/api/transformometroEvidenceApi";
import type { Revisao } from "../../../data/api/transformometroApi";
import { useTransformometroEntityWatch } from "../../../hooks/useTransformometroEntityWatch";
import type { RevisaoEvidence } from "../../../types/revisaoEvidence";
import { getTransformometroClientId } from "../../../utils/clientId";
import { DiagnosticActionPanel } from "../diagnostic/DiagnosticActionPanel";
import { DiagnosticContent } from "../diagnostic/DiagnosticContent";
import { resolveDiagnosticEventIntent } from "../diagnostic/diagnosticRealtime";
import { useRevisaoDiagnosticId } from "../../processes/ProcessWorkspaceShell";
import { buildRevisaoDiagnosticHref } from "../../processes/processWorkspaceNav";

const STALE_PROPOSAL_MESSAGE =
  "Este diagnóstico foi alterado desde a preparação da mudança. " +
  "Recarregue e revise antes de confirmar novamente.";

const OUTCOME_FAILED_MESSAGE =
  "A mudança foi enviada, mas a leitura canônica não confirmou o resultado " +
  "esperado (OUTCOME_VERIFICATION_FAILED). Recarregue e revise o estado atual.";

type ListState = "loading" | "ready" | "error" | "forbidden";
type DetailState =
  | "idle"
  | "loading"
  | "ready"
  | "error"
  | "not_found"
  | "forbidden"
  | "mismatch";

type CreateStage = "idle" | "form" | "review";

type ActiveAction = {
  action: DiagnosticManageAction;
  targetId: string | null;
  targetLabel: string | null;
} | null;

type Props = Pick<AppProps, "getAccessToken"> & {
  revisao: Revisao;
  onError: (message: string | null) => void;
  onNavigate?: (path: string) => void;
};

function httpStatus(err: unknown): number | null {
  return err && typeof err === "object" && typeof (err as { status?: unknown }).status === "number"
    ? (err as { status: number }).status
    : null;
}

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

export function RevisionDiagnosticSection({
  revisao,
  getAccessToken,
  onNavigate,
}: Props) {
  const processoId = revisao.processo_id;
  const instanciaId = revisao.instancia_id ?? "";
  const revisaoId = revisao.revisao_id;
  const clientIdRef = useRef(getTransformometroClientId());

  const hashDiagnosticId = useRevisaoDiagnosticId();

  const [list, setList] = useState<DiagnosticListResult | null>(null);
  const [listState, setListState] = useState<ListState>("loading");
  const [listError, setListError] = useState<string | null>(null);

  const [detail, setDetail] = useState<DiagnosticReadContext | null>(null);
  const [detailState, setDetailState] = useState<DetailState>("idle");
  const [detailError, setDetailError] = useState<string | null>(null);

  const [evidences, setEvidences] = useState<RevisaoEvidence[] | null>(null);
  const [evidencesLoading, setEvidencesLoading] = useState(false);

  const [createStage, setCreateStage] = useState<CreateStage>("idle");
  const [createStatement, setCreateStatement] = useState("");
  const [createProposal, setCreateProposal] = useState<DiagnosticProposal | null>(null);
  const [createBusy, setCreateBusy] = useState<"prepare" | "commit" | "verify" | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createStale, setCreateStale] = useState(false);

  const [activeAction, setActiveAction] = useState<ActiveAction>(null);
  const [remoteConflict, setRemoteConflict] = useState(false);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);
  const successRef = useRef<HTMLDivElement>(null);
  const createReviewRef = useRef<HTMLHeadingElement>(null);

  const listSeq = useRef(0);
  const detailSeq = useRef(0);

  const navigateToDiagnostic = useCallback(
    (diagnosticId?: string | null) => {
      onNavigate?.(buildRevisaoDiagnosticHref(processoId, instanciaId, revisaoId, diagnosticId));
    },
    [instanciaId, onNavigate, processoId, revisaoId],
  );

  const loadList = useCallback(async () => {
    const seq = ++listSeq.current;
    setListState("loading");
    try {
      const result = await listRevisionDiagnostics(revisaoId, getAccessToken);
      if (seq !== listSeq.current) return null;
      setList(result);
      setListState("ready");
      setListError(null);
      return result;
    } catch (err) {
      if (seq !== listSeq.current) return null;
      setListState(httpStatus(err) === 403 || httpStatus(err) === 401 ? "forbidden" : "error");
      setListError(errorMessage(err, "Não foi possível carregar os diagnósticos."));
      return null;
    }
  }, [getAccessToken, revisaoId]);

  const loadDetail = useCallback(
    async (diagnosticId: string) => {
      const seq = ++detailSeq.current;
      setDetailState("loading");
      try {
        const ctx = await fetchDiagnostic(diagnosticId, getAccessToken);
        if (seq !== detailSeq.current) return null;
        if (ctx.diagnostic.revision_id !== revisaoId) {
          setDetail(null);
          setDetailState("mismatch");
          return null;
        }
        setDetail(ctx);
        setDetailState("ready");
        setDetailError(null);
        return ctx;
      } catch (err) {
        if (seq !== detailSeq.current) return null;
        const status = httpStatus(err);
        setDetail(null);
        if (status === 404) setDetailState("not_found");
        else if (status === 403 || status === 401) setDetailState("forbidden");
        else setDetailState("error");
        setDetailError(errorMessage(err, "Não foi possível carregar o diagnóstico."));
        return null;
      }
    },
    [getAccessToken, revisaoId],
  );

  // Selected id: explicit deep-link, or the single Diagnostic of the Revision
  // (auto-open is presentation-only — never labeled as a chosen one).
  const selectedId = useMemo(() => {
    if (hashDiagnosticId) return hashDiagnosticId;
    if (listState === "ready" && list?.items.length === 1) {
      return list.items[0].diagnostic_id;
    }
    return null;
  }, [hashDiagnosticId, list, listState]);

  useEffect(() => {
    void loadList();
  }, [loadList]);

  useEffect(() => {
    if (selectedId) void loadDetail(selectedId);
    else {
      setDetail(null);
      setDetailState("idle");
    }
  }, [loadDetail, selectedId]);

  useEffect(() => {
    if (successNotice && successRef.current) successRef.current.focus();
  }, [successNotice]);

  const loadEvidences = useCallback(async () => {
    if (evidences || evidencesLoading) return;
    setEvidencesLoading(true);
    try {
      setEvidences(await fetchRevisaoEvidencias(revisaoId, getAccessToken));
    } catch {
      setEvidences([]);
    } finally {
      setEvidencesLoading(false);
    }
  }, [evidences, evidencesLoading, getAccessToken, revisaoId]);

  const startAction = useCallback(
    (action: DiagnosticManageAction, targetId?: string | null, targetLabel?: string | null) => {
      setSuccessNotice(null);
      setActiveAction({ action, targetId: targetId ?? null, targetLabel: targetLabel ?? null });
      if (action === "add_evidence_link") void loadEvidences();
    },
    [loadEvidences],
  );

  const hasLocalMaterialState = createStage !== "idle" || activeAction != null;

  // Realtime: diagnostic events fan out to the canonical revisao:{id} room.
  const handleRemoteEvent = useCallback(
    (event: Parameters<typeof resolveDiagnosticEventIntent>[0]) => {
      const intent = resolveDiagnosticEventIntent(event, {
        selectedId,
        hasLocalMaterialState,
        clientId: clientIdRef.current,
      });
      switch (intent.type) {
        case "ignore":
          return;
        case "refresh-list":
          void loadList();
          return;
        case "refresh-list-and-detail":
          void loadList();
          if (selectedId) void loadDetail(selectedId);
          return;
        case "local-conflict":
          void loadList();
          setRemoteConflict(true);
          return;
      }
    },
    [hasLocalMaterialState, loadDetail, loadList, selectedId],
  );

  useTransformometroEntityWatch({
    entities: [{ entityType: "revisao", entityId: revisaoId }],
    getAccessToken,
    enabled: Boolean(revisaoId),
    onEntityUpdated: (event) => {
      handleRemoteEvent(event);
    },
  });

  // -------------------------------------------------------------- create flow

  const handleCreatePrepare = useCallback(async () => {
    setCreateBusy("prepare");
    setCreateError(null);
    setCreateStale(false);
    try {
      const proposal = await prepareCreateDiagnostic(
        revisaoId,
        createStatement.trim(),
        getAccessToken,
      );
      setCreateProposal(proposal);
      setCreateStage("review");
    } catch (err) {
      setCreateError(errorMessage(err, "Falha ao preparar o diagnóstico."));
    } finally {
      setCreateBusy(null);
    }
  }, [createStatement, getAccessToken, revisaoId]);

  const handleCreateConfirm = useCallback(async () => {
    if (!createProposal) return;
    const newId = String(createProposal.exact_change?.diagnostic_id ?? "");
    setCreateBusy("commit");
    setCreateError(null);
    try {
      await commitGovernedProposal(createProposal.proposal_handle, getAccessToken);
    } catch (err) {
      setCreateBusy(null);
      if (httpStatus(err) === 409) {
        setCreateStale(true);
        return;
      }
      setCreateError(errorMessage(err, "Falha ao confirmar o diagnóstico."));
      return;
    }
    // COMMIT 2xx ≠ success — verify via canonical list + detail read-back.
    setCreateBusy("verify");
    try {
      const result = await loadList();
      const confirmed = result?.items.some((item) => item.diagnostic_id === newId);
      if (!result || !confirmed) {
        setCreateError(OUTCOME_FAILED_MESSAGE);
        setCreateProposal(null);
        setCreateStage("form");
        return;
      }
      setCreateStage("idle");
      setCreateProposal(null);
      setCreateStatement("");
      setCreateStale(false);
      setSuccessNotice("Diagnóstico registrado e confirmado nesta revisão.");
      navigateToDiagnostic(newId);
    } catch {
      setCreateError(OUTCOME_FAILED_MESSAGE);
      setCreateProposal(null);
      setCreateStage("form");
    } finally {
      setCreateBusy(null);
    }
  }, [createProposal, getAccessToken, loadList, navigateToDiagnostic]);

  useEffect(() => {
    if (createStage === "review" && createReviewRef.current) {
      createReviewRef.current.focus();
    }
  }, [createStage]);

  // ------------------------------------------------------------- manage flow

  const handleActionApplied = useCallback(() => {
    setActiveAction(null);
    setRemoteConflict(false);
    setSuccessNotice("Alteração confirmada e verificada.");
    void loadList();
    if (selectedId) void loadDetail(selectedId);
  }, [loadDetail, loadList, selectedId]);

  const handleReloadAfterConflict = useCallback(() => {
    setRemoteConflict(false);
    setActiveAction(null);
    void loadList();
    if (selectedId) void loadDetail(selectedId);
  }, [loadDetail, loadList, selectedId]);

  // ------------------------------------------------------------------ render

  const emptyClasses = emptyStateCardBemClasses("ds");

  return (
    <section className="tm-diagnostic-section" aria-labelledby="tm-diagnostic-title">
      <div className="tm-diagnostic-section__head">
        <h2 id="tm-diagnostic-title" className="tm-diagnostic-section__title">
          Diagnóstico
        </h2>
        {listState === "ready" && (list?.items.length ?? 0) > 0 ? (
          <ActionButton
            variant="ghost"
            onClick={() => {
              setSuccessNotice(null);
              setCreateError(null);
              setCreateStale(false);
              setCreateProposal(null);
              setCreateStage("form");
            }}
          >
            Iniciar diagnóstico
          </ActionButton>
        ) : null}
      </div>
      <p className="ds-hint">
        Registre o problema, os achados, hipóteses, relações causais e a conclusão
        desta revisão. Toda mudança passa por preparação, revisão e confirmação.
      </p>

      {remoteConflict ? (
        <StateBox variant="warning">
          Este diagnóstico foi atualizado em outro local. Revise o estado atual
          antes de preparar ou confirmar novamente.
          <ActionButton onClick={handleReloadAfterConflict}>
            Recarregar diagnóstico
          </ActionButton>
        </StateBox>
      ) : null}

      {successNotice ? (
        <div ref={successRef} tabIndex={-1}>
          <StateBox variant="success">{successNotice}</StateBox>
        </div>
      ) : null}

      {listState === "loading" ? (
        <LoadingActivityCard
          title="Carregando diagnósticos"
          description="Lendo os diagnósticos desta revisão."
        />
      ) : null}

      {listState === "forbidden" ? (
        <StateBox variant="error">
          {listError || "Você não tem permissão para ver os diagnósticos desta revisão."}
        </StateBox>
      ) : null}

      {listState === "error" ? (
        <StateBox variant="error">
          {listError}
          <ActionButton onClick={() => void loadList()}>
            Tentar novamente
          </ActionButton>
        </StateBox>
      ) : null}

      {listState === "ready" && (list?.items.length ?? 0) === 0 && createStage === "idle" ? (
        <EmptyState
          classNames={emptyClasses}
          defaultTitle="Nenhum diagnóstico registrado nesta revisão."
          defaultMessage="Registre o problema, os achados, hipóteses, relações causais e a conclusão desta revisão."
        >
          <ActionButton
            onClick={() => setCreateStage("form")}
          >
            Iniciar diagnóstico
          </ActionButton>
        </EmptyState>
      ) : null}

      {/* Selector — explicit choice when the Revision has multiple Diagnostics. */}
      {listState === "ready" && (list?.items.length ?? 0) > 1 ? (
        <nav aria-label="Diagnósticos da revisão" className="tm-diagnostic-selector">
          <ul className="tm-diagnostic-selector__list">
            {list?.items.map((item) => (
              <li key={item.diagnostic_id}>
                <button
                  type="button"
                  className={[
                    "tm-diagnostic-selector__item",
                    item.diagnostic_id === selectedId
                      ? "tm-diagnostic-selector__item--selected"
                      : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  aria-pressed={item.diagnostic_id === selectedId}
                  onClick={() => navigateToDiagnostic(item.diagnostic_id)}
                >
                  <span className="tm-diagnostic-selector__statement">
                    {item.problem_statement}
                  </span>
                  <span className="tm-diagnostic-selector__meta ds-hint">
                    {item.findings_count} achados · {item.hypotheses_count} hipóteses ·{" "}
                    {item.conclusions_count} conclusões
                  </span>
                  {item.revalidation_attention_required ? (
                    <TmStatusBadge label="Requer revalidação" variant="warning" />
                  ) : null}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      ) : null}

      {createStage === "form" ? (
        <div className="tm-diagnostic-create">
          <TmFormFieldShell
            id="tm-diagnostic-create-statement"
            label="Problema investigado"
            span
          >
            <NativeTextAreaControl
              id="tm-diagnostic-create-statement"
              className="tm-diagnostic-textarea"
              value={createStatement}
              onChange={setCreateStatement}
              rows={3}
              placeholder="Descreva o problema que este diagnóstico investiga."
            />
          </TmFormFieldShell>
          {createError ? (
            <StateBox variant="error">{createError}</StateBox>
          ) : null}
          <div className="tm-diagnostic-action__actions">
            <ActionButton
              disabled={createBusy != null || !createStatement.trim()}
              onClick={() => void handleCreatePrepare()}
            >
              {createBusy === "prepare" ? "Preparando…" : "Preparar diagnóstico"}
            </ActionButton>
            <ActionButton
              variant="ghost"
              disabled={createBusy != null}
              onClick={() => {
                setCreateStage("idle");
                setCreateError(null);
              }}
            >
              Cancelar
            </ActionButton>
          </div>
        </div>
      ) : null}

      {createStage === "review" && createProposal ? (
        <div className="tm-diagnostic-create tm-diagnostic-action__review">
          <h3 ref={createReviewRef} tabIndex={-1} className="tm-diagnostic-action__review-title">
            Revise a alteração preparada
          </h3>
          <p className="ds-hint">
            Confirme a alteração preparada abaixo. O diagnóstico só é criado após a
            confirmação explícita e a verificação da leitura canônica.
          </p>
          <TmDetailFieldGrid
            fields={[
              { label: "Ação", value: "Criar diagnóstico" },
              {
                label: "Problema investigado",
                value: String(createProposal.exact_change?.problem_statement ?? ""),
              },
            ]}
          />
          {createStale ? (
            <StateBox variant="warning">{STALE_PROPOSAL_MESSAGE}</StateBox>
          ) : null}
          {createError ? (
            <StateBox variant="error">{createError}</StateBox>
          ) : null}
          <div className="tm-diagnostic-action__actions">
            <ActionButton
              variant="primary"
              disabled={createBusy != null || createStale}
              onClick={() => void handleCreateConfirm()}
            >
              {createBusy === "commit"
                ? "Confirmando…"
                : createBusy === "verify"
                  ? "Verificando…"
                  : "Confirmar diagnóstico"}
            </ActionButton>
            <ActionButton
              variant="ghost"
              disabled={createBusy != null}
              onClick={() => {
                setCreateStage("form");
                setCreateProposal(null);
                setCreateStale(false);
              }}
            >
              Voltar e editar
            </ActionButton>
          </div>
        </div>
      ) : null}

      {detailState === "loading" ? (
        <LoadingActivityCard
          title="Abrindo diagnóstico"
          description="Lendo o diagnóstico selecionado."
        />
      ) : null}

      {detailState === "not_found" || detailState === "mismatch" ? (
        <StateBox variant="error">
          Diagnóstico não encontrado nesta revisão.
        </StateBox>
      ) : null}

      {detailState === "forbidden" ? (
        <StateBox variant="error">
          {detailError || "Você não tem permissão para ver este diagnóstico."}
        </StateBox>
      ) : null}

      {detailState === "error" ? (
        <StateBox variant="error">
          {detailError}
          <ActionButton
            onClick={() => selectedId && void loadDetail(selectedId)}
          >
            Tentar novamente
          </ActionButton>
        </StateBox>
      ) : null}

      {detailState === "ready" && detail ? (
        <DiagnosticContent
          detail={detail}
          onStartAction={startAction}
          activeAction={activeAction?.action ?? null}
          actionSlot={
            activeAction ? (
              <DiagnosticActionPanel
                diagnosticId={detail.diagnostic.diagnostic_id}
                action={activeAction.action}
                targetId={activeAction.targetId}
                targetLabel={activeAction.targetLabel}
                detail={detail}
                evidences={evidences}
                evidencesLoading={evidencesLoading}
                remoteStale={remoteConflict}
                getAccessToken={getAccessToken}
                onCancel={() => setActiveAction(null)}
                onApplied={handleActionApplied}
              />
            ) : null
          }
        />
      ) : null}
    </section>
  );
}
