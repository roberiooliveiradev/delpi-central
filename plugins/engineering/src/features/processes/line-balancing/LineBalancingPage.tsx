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
import {
  exportTableFormat,
  TabularExportButtons,
} from "@delpi/plugin-ui/index";
import type { StudioStudyInput } from "@delpi/line-balance-studio";

import { getCurrentAccessToken, HomeApiError } from "../../../api/httpClient";
import { getSubjectFromAccessToken } from "../../../app/authDisplayName";
import {
  EngineeringActionButton,
  EngineeringEmptyState,
  EngineeringFilterSelect,
  EngineeringFormActions,
  EngineeringKpiCard,
  EngineeringLoadingActivityCard,
  EngineeringSectionCard,
  EngineeringStateBanner,
  EngineeringStatusBadge,
  EngineeringTextField,
} from "../../../ui/engineeringUi";
import { EngineeringConfirmDialog } from "../../../ui/EngineeringConfirmDialog";
import { DataTable, type DataTableColumn } from "../../products/components/dataTableUi";
import {
  fetchProductRouting,
  postProductLineBalance,
} from "../../products/api/productApi";
import type {
  ProductLineBalanceResult,
  ProductRoutingResult,
} from "../../products/types";
import {
  formatHours,
  formatMinutes,
  groupRoutingRows,
  stageLabel,
  type RoutingOperationView,
} from "../../products/routing/routingGrouping";
import type { BalanceRunParams } from "../../products/routing/useRoutingStudyDraft";
import { BALANCING_METHODS, METHOD_STATUS_BADGE_VARIANT } from "./methodCatalog";
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

const OP_COLUMNS: DataTableColumn<RoutingOperationView>[] = [
  { key: "op", header: "Operação", render: (op) => op.operation_code || "—" },
  { key: "desc", header: "Descrição", render: (op) => op.operation_description ?? "—" },
  { key: "ct", header: "CT", render: (op) => op.work_center ?? "—" },
  { key: "resource", header: "Recurso", render: (op) => op.resource_code ?? "—" },
  {
    key: "time",
    header: "Tempo padrão (min/peça)",
    align: "right",
    render: (op) => (op.time_minutes_piece != null ? formatMinutes(op.time_minutes_piece) : "UNKNOWN"),
  },
  {
    key: "setup",
    header: "Setup (h)",
    align: "right",
    render: (op) => (op.setup_hours != null ? formatHours(op.setup_hours) : "—"),
  },
];

export function LineBalancingPage() {
  const [productCode, setProductCode] = useState("");
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

  /* Estudo manual — mesmo fluxo de rascunho, contexto neutro. */
  const startManualStudy = useCallback(() => {
    const restored = loadStudioDraft(studioDraftKey(identity, MANUAL_CONTEXT), MANUAL_CONTEXT);
    const seed = restored.status === "ok" ? restored.study : buildManualStudyInput();
    setStudySeed(seed);
    setLiveStudy(seed);
    liveStudyRef.current = seed;
    setStaleNotice(null);
    setBalanceResult(null);
    setBalanceError(null);
  }, [identity]);

  const showStudio = Boolean(studySeed) && (Boolean(stage) || Boolean(studySeed));

  const searchRouting = useCallback(() => {
    const code = productCode.trim();
    if (!code) return;
    setQueriedCode(code);
    setBranch("");
    setBranches([]);
    setStageKey(null);
    setBalanceError(null);
    setBalanceResult(null);
    setClearedNotice(false);
    setStaleNotice(null);
  }, [productCode]);

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

  return (
    <>
      <EngineeringSectionCard
        title="Balanceamento de Linha"
        subtitle="Consulte o roteiro oficial de fabricação e construa estudos de balanceamento no Line Balance Studio — hipóteses locais nunca alteram o roteiro oficial."
      >
        <div className="engineering-processes__lookup" role="group" aria-label="Consulta do roteiro oficial">
          <EngineeringTextField
            id="lb-product-code"
            label="Código do produto"
            value={productCode}
            onChange={setProductCode}
            hint="Código oficial do produto na fonte autorizada."
          />
          <EngineeringActionButton
            variant="primary"
            disabled={!productCode.trim() || routingLoading}
            onClick={searchRouting}
          >
            {routingLoading ? "Consultando…" : "Buscar roteiro"}
          </EngineeringActionButton>
          {queriedCode ? (
            <>
              <EngineeringFilterSelect
                label="Filial"
                options={branchOptions}
                value={branch}
                onChange={setBranch}
              />
              <EngineeringFilterSelect
                label="Estágio produtivo"
                options={stageOptions}
                value={stage?.key ?? ""}
                onChange={(v) => setStageKey(v || null)}
                disabled={!grouped.stages.length}
              />
            </>
          ) : null}
          <EngineeringActionButton variant="default" onClick={startManualStudy}>
            Novo estudo manual
          </EngineeringActionButton>
        </div>
      </EngineeringSectionCard>

      {staleNotice ? <EngineeringStateBanner variant="default">{staleNotice}</EngineeringStateBanner> : null}
      {clearedNotice ? (
        <EngineeringStateBanner variant="default">Rascunho local do contexto atual limpo — o roteiro oficial permanece intacto.</EngineeringStateBanner>
      ) : null}

      {!queriedCode && !studySeed ? (
        <EngineeringEmptyState message="Informe o código do produto e acione Buscar roteiro para consultar a fonte oficial — ou inicie um estudo manual." />
      ) : queriedCode && routingLoading ? (
        <EngineeringLoadingActivityCard title="Consultando" description="Consultando o roteiro oficial…" />
      ) : queriedCode && routingError ? (
        isForbidden(routingError) ? (
          <EngineeringEmptyState message="Acesso negado pela fonte oficial — você não tem autorização para consultar o roteiro." />
        ) : isNotFound(routingError) ? (
          <EngineeringEmptyState message="Produto não encontrado ou sem roteiro na fonte oficial." />
        ) : (
          <EngineeringStateBanner variant="error">
            {routingError instanceof HomeApiError ? routingError.message : "Fonte oficial de roteiro indisponível."}
          </EngineeringStateBanner>
        )
      ) : queriedCode && !grouped.stages.length ? (
        <EngineeringEmptyState message="Roteiro oficial vazio para este contexto — nenhuma operação retornada." />
      ) : null}

      {queriedCode && !routingLoading && !routingError && grouped.stages.length > 0 && !stage && !studySeed ? (
        <EngineeringEmptyState message="Selecione a filial e o estágio produtivo para visualizar as operações oficiais e iniciar o estudo." />
      ) : null}

      {stage && studySeed?.source === "OBSERVED_ROUTING" ? (
        <>
          <EngineeringSectionCard
            title="Operações oficiais do roteiro"
            subtitle={`${queriedCode} · ${stage.operations.length} operação(ões) deduplicada(s) por identidade de operação${routing?.truncated ? " · resultado truncado pela fonte" : ""}`}
          >
            {routing?.truncated ? (
              <EngineeringStateBanner variant="default">
                A fonte retornou resultado paginado incompleto — o estudo considera somente as operações efetivamente recebidas.
              </EngineeringStateBanner>
            ) : null}
            <DataTable
              columns={OP_COLUMNS}
              rows={stage.operations}
              rowKey={(op) => op.key}
              layout="embedded"
              compact
              emptyMessage="Nenhuma operação neste estágio."
            />
          </EngineeringSectionCard>
        </>
      ) : null}

      {showStudio ? (
        <EngineeringSectionCard
          title="Estudo de balanceamento"
          subtitle="Line Balance Studio — organização DRAFT_LOCAL de postos e cenários SIMULATION sobre a fonte oficial ou entradas manuais."
          actions={
            saveStatus !== "idle" ? (
              <EngineeringStatusBadge
                label={SAVE_LABEL[saveStatus] ?? saveStatus}
                variant={saveStatus === "saved" ? "success" : "warning"}
              />
            ) : undefined
          }
        >
          <LineBalanceStudioMount study={studySeed} onStudyChange={onStudyChange} />
          <EngineeringFormActions>
            <EngineeringActionButton variant="default" onClick={() => setClearOpen(true)}>
              Limpar estudo
            </EngineeringActionButton>
            <TabularExportButtons onExport={exportStudy} />
          </EngineeringFormActions>
        </EngineeringSectionCard>
      ) : null}

      {queriedCode && stage && studySeed?.source === "OBSERVED_ROUTING" ? (
        <EngineeringSectionCard
          title="Análise oficial M1 — capacidade e takt"
          subtitle="Métricas CALCULATED do domínio EVA sobre o roteiro OBSERVED com os parâmetros PROVIDED das condições do estudo."
        >
          {!balanceParams.ok ? (
            <ul className="engineering-routing__limitations" role="alert">
              {balanceParams.issues.map((issue, i) => (
                <li key={i}>{issue}</li>
              ))}
            </ul>
          ) : null}
          <EngineeringFormActions>
            <EngineeringActionButton
              variant="primary"
              disabled={!balanceParams.ok || balanceRunning}
              onClick={runBalance}
            >
              {balanceRunning ? "Calculando…" : "Executar análise oficial"}
            </EngineeringActionButton>
          </EngineeringFormActions>
          {balanceError ? (
            <EngineeringStateBanner variant="error">
              {isForbidden(balanceError)
                ? "Acesso negado pela análise oficial — autorização insuficiente."
                : isNotFound(balanceError)
                  ? "Produto ou estágio não encontrado pela análise oficial."
                  : balanceError instanceof HomeApiError
                    ? balanceError.message
                    : "Serviço de análise oficial indisponível."}
            </EngineeringStateBanner>
          ) : null}
          {stageBalance ? (
            <div className="engineering-routing__balance-grid">
              <EngineeringKpiCard title="Takt" value={formatMinutes(stageBalance.takt_minutes)} subtitle="min/peça — CALCULATED" />
              <EngineeringKpiCard
                title="Conteúdo de trabalho"
                value={formatMinutes(stageBalance.work_content_minutes)}
                subtitle="min — CALCULATED"
              />
              <EngineeringKpiCard
                title="Mínimo teórico de postos"
                value={stageBalance.theoretical_min_stations != null ? String(stageBalance.theoretical_min_stations) : "—"}
                subtitle="CALCULATED"
              />
              <EngineeringKpiCard
                title="Gargalo candidato"
                value={stageBalance.bottleneck_candidate?.operation_code ?? "—"}
                subtitle="CALCULATED"
              />
            </div>
          ) : balanceResult ? (
            <EngineeringEmptyState message="O resultado oficial não inclui o estágio selecionado." />
          ) : null}
          {stageBalance?.operations_missing_time?.length ? (
            <EngineeringStateBanner variant="default">
              {stageBalance.operations_missing_time.length} operação(ões) sem tempo oficial — UNKNOWN, nunca assumidas como zero.
            </EngineeringStateBanner>
          ) : null}
        </EngineeringSectionCard>
      ) : null}

      <EngineeringSectionCard
        title="Métodos de balanceamento"
        subtitle="Catálogo M1–M6 — somente capacidades reais; métodos planejados mostram requisitos em vez de cálculo inerte."
      >
        <div className="engineering-processes__method-list">
          {BALANCING_METHODS.map((m) => (
            <div key={m.id} className="engineering-processes__method-item">
              <span className="engineering-processes__method-head">
                <strong>
                  {m.label} — {m.name}
                </strong>
                <EngineeringStatusBadge label={m.statusLabel} variant={METHOD_STATUS_BADGE_VARIANT[m.status] ?? "neutral"} />
              </span>
              <p className="engineering-routing__muted">{m.summary}</p>
              {m.requirements?.length ? (
                <ul className="engineering-routing__limitations">
                  {m.requirements.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ))}
        </div>
      </EngineeringSectionCard>

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
