/** Processos > Balanceamento de Linha — host do DELPI Line Balance
 * Studio (`plugins/delpi-line-balance-studio`) na rota governada
 * `/apps/engineering/processes/line-balancing`. O host mantém SSO,
 * RBAC, client HTTP, filial, estágio, cancelamento, estados de erro e
 * o contrato oficial M1 (`POST /v1/products/{code}/line-balance`). O
 * Studio compõe o estudo (postos, cenários, condições, Yamazumi) como
 * DRAFT_LOCAL — nunca escreve no roteiro oficial.
 *
 * Proveniência: roteiro OBSERVED, parâmetros PROVIDED, métricas M1
 * CALCULATED, organização de postos e cenários SIMULATION/DRAFT_LOCAL —
 * hipóteses nunca são apresentadas como dimensionamento aprovado. */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { exportTableFormat } from "@delpi/plugin-ui/index";
import type { StudioStudyInput } from "@delpi/line-balance-studio";
import type {
  StudioAnalysisState,
  StudioDraftSaveState,
  StudioOfficialOperation,
  StudioRoutingState,
} from "@delpi/line-balance-studio/ui";

import { getCurrentAccessToken, HomeApiError } from "../../../api/httpClient";
import { getSubjectFromAccessToken } from "../../../app/authDisplayName";
import { EngineeringStateBanner } from "../../../ui/engineeringUi";
import { EngineeringConfirmDialog } from "../../../ui/EngineeringConfirmDialog";
import {
  fetchProductRouting,
  postProductLineBalance,
} from "../../products/api/productApi";
import type {
  ProductLineBalanceResult,
  ProductRoutingResult,
} from "../../products/types";
import {
  groupRoutingRows,
  stageLabel,
} from "../../products/routing/routingGrouping";
import type { BalanceRunParams } from "../../products/routing/useRoutingStudyDraft";
import { LineBalanceStudioMount } from "./LineBalanceStudio";
import {
  buildManualStudyInput,
  buildObservedStudyInput,
  buildStudioExportPayload,
  clearStudioDraft,
  deriveBalanceParams,
  loadStudioDraft,
  migrateLegacyDraft,
  saveStudioDraft,
  studioDraftContext,
  studioDraftKey,
  type StudioDraftContext,
  type StudioDraftSave,
} from "./studioAdapter";
import { buildStorageKey, parseDraft } from "../../products/routing/routingStudyDraft";

const LEGACY_DRAFT_PREFIX = "engineering:processes:line-balance";
const MANUAL_CONTEXT: StudioDraftContext = {
  productCode: "manual",
  branch: "",
  stageKey: "manual",
  sourceFingerprint: "manual",
};

const SAVE_LABEL: Record<StudioDraftSave, string> = {
  saved: "Rascunho salvo",
  unavailable: "Armazenamento indisponível",
  quota: "Armazenamento cheio — rascunho não salvo",
  error: "Falha ao salvar rascunho",
};

type RoutingData = ProductRoutingResult & { truncated?: boolean };

function isForbidden(error: unknown): boolean {
  return error instanceof HomeApiError && error.status === 403;
}

function isNotFound(error: unknown): boolean {
  return error instanceof HomeApiError && error.status === 404;
}

export function LineBalancingPage() {
  const [queriedCode, setQueriedCode] = useState("");
  const [branch, setBranch] = useState("");
  const [branches, setBranches] = useState<string[]>([]);
  const [routing, setRouting] = useState<RoutingData | null>(null);
  const [routingError, setRoutingError] = useState<unknown>(null);
  const [routingLoading, setRoutingLoading] = useState(false);
  const [stageKey, setStageKey] = useState<string | null>(null);
  const [studySeed, setStudySeed] = useState<StudioStudyInput | undefined>();
  const [liveStudy, setLiveStudy] = useState<StudioStudyInput | undefined>();
  const [staleNotice, setStaleNotice] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<StudioDraftSave | "idle">("idle");
  const [balanceRunning, setBalanceRunning] = useState(false);
  const [balanceError, setBalanceError] = useState<unknown>(null);
  const [balanceResult, setBalanceResult] = useState<{
    params: BalanceRunParams;
    result: ProductLineBalanceResult;
  } | null>(null);
  const [clearOpen, setClearOpen] = useState(false);
  const [clearedNotice, setClearedNotice] = useState(false);
  const balanceAbort = useRef<AbortController | null>(null);
  const liveStudyRef = useRef<StudioStudyInput | undefined>(undefined);

  const identity = useMemo(() => getSubjectFromAccessToken(getCurrentAccessToken()), []);

  /* Consulta oficial — só após "Buscar roteiro"; reconsulta quando a
   * filial muda (contrato filtra server-side). Resposta atrasada ou
   * negada nunca expõe dados de outro produto: o estado é por produto
   * consultado e o abort descarta retornos fora de ordem. */
  useEffect(() => {
    if (!queriedCode) return undefined;
    const controller = new AbortController();
    setRoutingLoading(true);
    setRoutingError(null);
    fetchProductRouting(queriedCode, { branch: branch || undefined }, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        setRouting(result);
        setBranches((prev) => {
          const next = new Set(prev);
          for (const item of result.items ?? []) {
            if (item.branch) next.add(String(item.branch));
          }
          return [...next].sort();
        });
      })
      .catch((err) => {
        if (!controller.signal.aborted) setRoutingError(err);
      })
      .finally(() => {
        if (!controller.signal.aborted) setRoutingLoading(false);
      });
    return () => controller.abort();
  }, [queriedCode, branch]);

  const grouped = useMemo(() => groupRoutingRows(routing?.items ?? []), [routing]);
  useEffect(() => {
    if (grouped.stages.length && !grouped.stages.some((s) => s.key === stageKey)) {
      setStageKey(null);
    }
  }, [grouped, stageKey]);
  /* Estágio só é assumido após seleção explícita — nunca automático. */
  const stage = grouped.stages.find((s) => s.key === stageKey) ?? null;

  /* Seed do Studio: rascunho do mesmo contexto/fingerprint → seed
   * OBSERVED do estágio; legado migrado; `stale` descarta e avisa. */
  useEffect(() => {
    if (!stage) {
      setStudySeed(undefined);
      setLiveStudy(undefined);
      liveStudyRef.current = undefined;
      return;
    }
    const ctx = studioDraftContext({ productCode: queriedCode, branch, stage });
    const key = studioDraftKey(identity, ctx);
    const loaded = loadStudioDraft(key, ctx);
    if (loaded.status === "ok") {
      setStudySeed(loaded.study);
      setLiveStudy(loaded.study);
      liveStudyRef.current = loaded.study;
      setStaleNotice(null);
      return;
    }
    if (loaded.status === "stale") {
      setStaleNotice("O roteiro oficial mudou desde o rascunho salvo — as hipóteses antigas foram descartadas.");
    }
    /* Migração compatível: rascunho no formato anterior (postos) é
     * convertido para o DTO do Studio preservando postos/atribuições
     * que ainda existem no roteiro atual. */
    const legacyKey = buildStorageKey(identity, ctx, LEGACY_DRAFT_PREFIX);
    let migrated: StudioStudyInput | undefined;
    const legacyParsed = parseDraft(safeRead(legacyKey), ctx);
    if (legacyParsed.ok) {
      migrated = migrateLegacyDraft(
        legacyParsed.draft,
        buildObservedStudyInput({ stage, productCode: queriedCode, branch }),
      );
      saveStudioDraft(key, ctx, migrated);
    }
    const seed = migrated ?? buildObservedStudyInput({
      stage,
      productCode: queriedCode,
      branch,
      stageName: stageLabel(stage),
      truncated: routing?.truncated,
    });
    setStudySeed(seed);
    setLiveStudy(seed);
    liveStudyRef.current = seed;
    if (loaded.status !== "stale") setStaleNotice(null);
  }, [stage, queriedCode, branch, identity, routing?.truncated]);

  const draftContext = useMemo<StudioDraftContext | null>(() => {
    if (studySeed?.source === "OBSERVED_ROUTING" && stage) {
      return studioDraftContext({ productCode: queriedCode, branch, stage });
    }
    if (studySeed && studySeed.source !== "OBSERVED_ROUTING") return MANUAL_CONTEXT;
    return null;
  }, [studySeed, stage, queriedCode, branch]);

  const onStudyChange = useCallback(
    (study: StudioStudyInput) => {
      liveStudyRef.current = study;
      setLiveStudy(study);
      if (!draftContext) return;
      const outcome = saveStudioDraft(studioDraftKey(identity, draftContext), draftContext, study);
      setSaveStatus(outcome);
    },
    [draftContext, identity],
  );

  /* Estudo manual — mesmo fluxo de rascunho, contexto neutro; o nome
   * informado na entrada do Studio aplica-se apenas a rascunho novo. */
  const startManualStudy = useCallback((name?: string) => {
    const restored = loadStudioDraft(studioDraftKey(identity, MANUAL_CONTEXT), MANUAL_CONTEXT);
    const seed = restored.status === "ok"
      ? restored.study
      : { ...buildManualStudyInput(), ...(name ? { name } : {}) };
    setStudySeed(seed);
    setLiveStudy(seed);
    liveStudyRef.current = seed;
    setStaleNotice(null);
    setBalanceResult(null);
    setBalanceError(null);
  }, [identity]);

  const searchRouting = useCallback((code: string) => {
    if (!code) return;
    setQueriedCode(code);
    setBranch("");
    setBranches([]);
    setStageKey(null);
    setBalanceError(null);
    setBalanceResult(null);
    setClearedNotice(false);
    setStaleNotice(null);
  }, []);

  /* Troca de origem — encerra a sessão; o rascunho local salvo do
   * contexto permanece em storage e é restaurado ao retornar. */
  const resetOrigin = useCallback(() => {
    setQueriedCode("");
    setBranch("");
    setBranches([]);
    setStageKey(null);
    setStudySeed(undefined);
    setLiveStudy(undefined);
    liveStudyRef.current = undefined;
    setBalanceError(null);
    setBalanceResult(null);
    setClearedNotice(false);
    setStaleNotice(null);
  }, []);

  const onRoutingContext = useCallback(({ branch: nextBranch, stage: nextStage }: { branch: string; stage: string }) => {
    if (nextBranch !== branch) setBranch(nextBranch);
    setStageKey(nextStage || null);
  }, [branch]);

  const confirmClear = useCallback(() => {
    let removed = false;
    if (draftContext) {
      removed = clearStudioDraft(studioDraftKey(identity, draftContext));
    }
    setClearOpen(false);
    const fresh = stage && studySeed?.source === "OBSERVED_ROUTING"
      ? buildObservedStudyInput({ stage, productCode: queriedCode, branch, stageName: stageLabel(stage), truncated: routing?.truncated })
      : buildManualStudyInput();
    setStudySeed(fresh);
    setLiveStudy(fresh);
    liveStudyRef.current = fresh;
    setBalanceResult(null);
    if (removed) setClearedNotice(true);
  }, [draftContext, identity, stage, queriedCode, branch, routing?.truncated]);

  /* M1 — parâmetros derivados das condições do estudo; cálculo sempre
   * pelo contrato oficial do domínio, nunca recalculado no host. */
  const balanceParams = useMemo(
    () => deriveBalanceParams(liveStudy ?? studySeed, branch),
    [liveStudy, studySeed, branch],
  );

  const runBalance = useCallback(() => {
    if (!queriedCode || !balanceParams.ok) return;
    const params = balanceParams.params;
    balanceAbort.current?.abort();
    const controller = new AbortController();
    balanceAbort.current = controller;
    setBalanceRunning(true);
    setBalanceError(null);
    postProductLineBalance(queriedCode, params, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setBalanceResult({ params, result });
      })
      .catch((err) => {
        if (!controller.signal.aborted) setBalanceError(err);
      })
      .finally(() => {
        if (!controller.signal.aborted) setBalanceRunning(false);
      });
  }, [queriedCode, balanceParams]);

  const stageBalance = useMemo(() => {
    if (!balanceResult || !stage) return null;
    return (
      balanceResult.result.stages.find(
        (st) => `${st.product_code}#${st.bom_level}` === stage.key,
      ) ?? null
    );
  }, [balanceResult, stage]);

  const branchOptions = useMemo(
    () => [
      { value: "", label: "Todas as filiais" },
      ...branches.map((b) => ({ value: b, label: `Filial ${b}` })),
    ],
    [branches],
  );

  const stageOptions = useMemo(
    () => [
      { value: "", label: "Selecionar estágio…" },
      ...grouped.stages.map((s) => ({ value: s.key, label: stageLabel(s) })),
    ],
    [grouped],
  );

  /* Estado da consulta oficial apresentado pelo Studio — a mesma
   * informação que antes dirigia os estados do host, agora serializada
   * no contrato público do elemento. */
  const studioRoutingState: StudioRoutingState = useMemo(() => {
    if (!queriedCode) return { phase: "idle" };
    if (routingLoading) return { phase: "searching", productCode: queriedCode };
    if (routingError) {
      return {
        phase: "error",
        productCode: queriedCode,
        message: isForbidden(routingError)
          ? "Acesso negado pela fonte oficial — você não tem autorização para consultar o roteiro."
          : isNotFound(routingError)
            ? "Produto não encontrado ou sem roteiro na fonte oficial."
            : routingError instanceof HomeApiError
              ? routingError.message
              : "Fonte oficial de roteiro indisponível.",
      };
    }
    if (!grouped.stages.length) {
      return {
        phase: "error",
        productCode: queriedCode,
        message: "Roteiro oficial vazio para este contexto — nenhuma operação retornada.",
      };
    }
    return {
      phase: "awaiting-stage",
      productCode: queriedCode,
      branch,
      branchOptions,
      stage: stage?.key ?? "",
      stageOptions,
      message: stage
        ? undefined
        : "Selecione a filial e o estágio produtivo para visualizar as operações oficiais e iniciar o estudo.",
    };
  }, [queriedCode, routingLoading, routingError, grouped.stages.length, branch, branchOptions, stage, stageOptions]);

  const exportStudy = useCallback(
    (format: "csv" | "xlsx" | "pdf") => {
      const study = liveStudyRef.current ?? studySeed;
      if (!study) return;
      exportTableFormat(
        buildStudioExportPayload({
          productCode: queriedCode,
          branch,
          stageLabel: stage ? stageLabel(stage) : study.source === "OBSERVED_ROUTING" ? study.routing.stageId : "Estudo manual",
          study,
        }),
        format,
      );
    },
    [queriedCode, branch, stage, studySeed],
  );

  /* Análise oficial M1 — execução permanece aqui (BFF/domínio); o Studio
   * recebe o estado serializado para apresentá-la na bancada do método. */
  const studioAnalysisState: StudioAnalysisState | undefined = useMemo(() => {
    if (!queriedCode || !stage || studySeed?.source !== "OBSERVED_ROUTING") return undefined;
    if (balanceRunning) return { phase: "running" };
    if (balanceError) {
      return {
        phase: "error",
        message: isForbidden(balanceError)
          ? "Acesso negado pela análise oficial — autorização insuficiente."
          : isNotFound(balanceError)
            ? "Produto ou estágio não encontrado pela análise oficial."
            : balanceError instanceof HomeApiError
              ? balanceError.message
              : "Serviço de análise oficial indisponível.",
      };
    }
    if (balanceResult) {
      return {
        phase: "result",
        result: {
          taktMinutes: stageBalance?.takt_minutes ?? null,
          workContentMinutes: stageBalance?.work_content_minutes ?? null,
          theoreticalMinStations: stageBalance?.theoretical_min_stations ?? null,
          bottleneckOperation: stageBalance?.bottleneck_candidate?.operation_code ?? null,
          operationsMissingTime: stageBalance?.operations_missing_time?.length ?? 0,
          stageCovered: Boolean(stageBalance),
        },
      };
    }
    return { phase: "idle", issues: balanceParams.ok ? [] : balanceParams.issues };
  }, [queriedCode, stage, studySeed, balanceRunning, balanceError, balanceResult, stageBalance, balanceParams]);

  /* Metadados oficiais do roteiro — detalhe técnico sob demanda dentro da
   * bancada (sem segunda tabela concorrente fora do Studio). */
  const officialOperations: StudioOfficialOperation[] | undefined = useMemo(() => {
    if (!stage || studySeed?.source !== "OBSERVED_ROUTING") return undefined;
    return stage.operations.map((op) => ({
      key: op.key,
      code: op.operation_code,
      description: op.operation_description,
      workCenter: op.work_center,
      resource: op.resource_code,
      timeMinutesPiece: op.time_minutes_piece,
      setupHours: op.setup_hours,
    }));
  }, [stage, studySeed]);

  const draftSave: StudioDraftSaveState | undefined = useMemo(
    () => saveStatus === "idle"
      ? undefined
      : { label: SAVE_LABEL[saveStatus] ?? saveStatus, tone: saveStatus === "saved" ? "success" : "warning" },
    [saveStatus],
  );

  return (
    <>
      {staleNotice ? <EngineeringStateBanner variant="default">{staleNotice}</EngineeringStateBanner> : null}
      {clearedNotice ? (
        <EngineeringStateBanner variant="default">Rascunho local do contexto atual limpo — o roteiro oficial permanece intacto.</EngineeringStateBanner>
      ) : null}

      <LineBalanceStudioMount
        study={studySeed}
        routingState={studioRoutingState}
        analysisState={studioAnalysisState}
        officialOperations={officialOperations}
        draftSave={draftSave}
        onStudyChange={onStudyChange}
        onRoutingSearch={searchRouting}
        onRoutingContext={onRoutingContext}
        onManualStudy={startManualStudy}
        onOriginReset={resetOrigin}
        onAnalysisRun={runBalance}
        onExport={exportStudy}
        onClearStudy={() => setClearOpen(true)}
      />

      <EngineeringConfirmDialog
        open={clearOpen}
        title="Limpar estudo"
        message="Remove o rascunho local (postos, cenários e condições) do contexto atual. O roteiro oficial consultado permanece intacto. Continuar?"
        confirmLabel="Limpar"
        onCancel={() => setClearOpen(false)}
        onConfirm={confirmClear}
      />
    </>
  );
}

function safeRead(key: string): string | null {
  try {
    return globalThis.sessionStorage?.getItem(key) ?? null;
  } catch {
    return null;
  }
}
