/** Processos > Balanceamento de Linha — workspace independente da
 * Ficha do Produto (plano V3, M5 Yamazumi como primeiro método
 * interativo). Consulta o roteiro oficial pelo contrato
 * `GET /v1/products/{code}/routing` e executa a análise determinística
 * M1 via `POST /v1/products/{code}/line-balance` — sem chamadas diretas
 * à API-DELPI e sem recalcular o domínio no frontend.
 *
 * Separação de proveniência preservada: roteiro OBSERVED, parâmetros
 * PROVIDED, métricas CALCULATED, organização de postos DRAFT_LOCAL e
 * distribuições SIMULATION — hipóteses nunca são apresentadas como
 * dimensionamento aprovado nem gravadas no roteiro oficial. */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { TableExportPayload } from "@delpi/plugin-ui/index";

import { getCurrentAccessToken, HomeApiError } from "../../../api/httpClient";
import { getSubjectFromAccessToken } from "../../../app/authDisplayName";
import {
  EngineeringActionButton,
  EngineeringChartCard,
  EngineeringDetailCard,
  EngineeringEmptyState,
  EngineeringFilterSelect,
  EngineeringFormActions,
  EngineeringKpiCard,
  EngineeringLoadingActivityCard,
  EngineeringScopeChipBar,
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
import { resolveChartTimeUnit, type ChartTimeUnit } from "../../products/routing/chartUnits";
import { RoutingSeriesChart } from "../../products/routing/RoutingSeriesChart";
import { PostConfigurator } from "../../products/routing/PostConfigurator";
import { BalanceResultsSection } from "../../products/routing/BalanceResultsSection";
import {
  formatHours,
  formatMinutes,
  groupRoutingRows,
  stageLabel,
  type RoutingOperationView,
} from "../../products/routing/routingGrouping";
import {
  validateStudyInputs,
  SAVE_STATUS_LABEL,
} from "../../products/routing/studyInputs";
import {
  useRoutingStudyDraft,
  type BalanceRunParams,
} from "../../products/routing/useRoutingStudyDraft";
import {
  BALANCING_METHODS,
  METHOD_STATUS_BADGE_VARIANT,
  type MethodId,
} from "./methodCatalog";
import {
  AGGREGATE_TIME_CATEGORY,
  assignOperationToPost,
  buildYamazumiChartSpec,
  buildYamazumiExportRows,
  computePostLoads,
  unassignedOperations,
} from "./yamazumi";

/** Namespace de rascunho isolado da Ficha do Produto — mesmo schema V2,
 * chave própria por identidade/produto/filial/estágio (contrato de
 * sessão). */
const LINE_BALANCE_STORAGE_PREFIX = "engineering:processes:line-balance";

type RoutingData = ProductRoutingResult & { truncated?: boolean };

function isForbidden(error: unknown): boolean {
  return error instanceof HomeApiError && error.status === 403;
}

function isNotFound(error: unknown): boolean {
  return error instanceof HomeApiError && error.status === 404;
}

const OP_COLUMNS: DataTableColumn<RoutingOperationView>[] = [
  {
    key: "op",
    header: "Operação",
    render: (op) => op.operation_code || "—",
  },
  {
    key: "desc",
    header: "Descrição",
    render: (op) => op.operation_description ?? "—",
  },
  {
    key: "ct",
    header: "CT",
    render: (op) => op.work_center ?? "—",
  },
  {
    key: "resource",
    header: "Recurso",
    render: (op) => op.resource_code ?? "—",
  },
  {
    key: "time",
    header: "Tempo padrão (min/peça)",
    align: "right",
    render: (op) =>
      op.time_minutes_piece != null
        ? formatMinutes(op.time_minutes_piece)
        : "UNKNOWN",
  },
  {
    key: "setup",
    header: "Setup (h)",
    align: "right",
    render: (op) => (op.setup_hours != null ? formatHours(op.setup_hours) : "—"),
  },
];

export function LineBalancingPage({ basePath }: { basePath?: string }) {
  const [productCode, setProductCode] = useState("");
  const [queriedCode, setQueriedCode] = useState("");
  const [branch, setBranch] = useState("");
  const [branches, setBranches] = useState<string[]>([]);
  const [routing, setRouting] = useState<RoutingData | null>(null);
  const [routingError, setRoutingError] = useState<unknown>(null);
  const [routingLoading, setRoutingLoading] = useState(false);
  const [stageKey, setStageKey] = useState<string | null>(null);
  const [balanceRunning, setBalanceRunning] = useState(false);
  const [balanceError, setBalanceError] = useState<unknown>(null);
  const [clearOpen, setClearOpen] = useState(false);
  const [clearedNotice, setClearedNotice] = useState(false);
  const [methodId, setMethodId] = useState<MethodId>("m5");
  const balanceAbort = useRef<AbortController | null>(null);

  const identity = useMemo(
    () => getSubjectFromAccessToken(getCurrentAccessToken()),
    [],
  );

  /* Consulta oficial — só após "Buscar roteiro"; reconsulta quando a
   * filial muda (contrato filtra server-side). */
  useEffect(() => {
    if (!queriedCode) return undefined;
    const controller = new AbortController();
    setRoutingLoading(true);
    setRoutingError(null);
    fetchProductRouting(
      queriedCode,
      { branch: branch || undefined },
      controller.signal,
    )
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

  const grouped = useMemo(
    () => groupRoutingRows(routing?.items ?? []),
    [routing],
  );
  useEffect(() => {
    if (
      grouped.stages.length &&
      !grouped.stages.some((s) => s.key === stageKey)
    ) {
      setStageKey(null);
    }
  }, [grouped, stageKey]);
  /* Contexto exigido: o estágio só é assumido após seleção explícita
   * do usuário — nunca automaticamente (contrato V3). */
  const stage =
    grouped.stages.find((s) => s.key === stageKey) ?? null;

  const study = useRoutingStudyDraft({
    identity,
    productCode: queriedCode,
    branch,
    stage,
    storagePrefix: LINE_BALANCE_STORAGE_PREFIX,
  });
  const active = study.active;

  const validation = useMemo(
    () =>
      validateStudyInputs(
        active?.inputs ?? {
          demand: "",
          shiftMinutes: "",
          breakMinutes: "",
          batchSize: "",
          numStations: "",
        },
        branch,
      ),
    [active?.inputs, branch],
  );

  const runBalance = useCallback(
    (params: BalanceRunParams) => {
      if (!study.activeScenarioId || !queriedCode) return;
      const scenarioId = study.activeScenarioId;
      balanceAbort.current?.abort();
      const controller = new AbortController();
      balanceAbort.current = controller;
      setBalanceRunning(true);
      setBalanceError(null);
      postProductLineBalance(queriedCode, params, controller.signal)
        .then((result) => {
          if (controller.signal.aborted) return;
          study.attachResult(scenarioId, params, result);
        })
        .catch((err) => {
          if (!controller.signal.aborted) setBalanceError(err);
        })
        .finally(() => {
          if (!controller.signal.aborted) setBalanceRunning(false);
        });
    },
    [queriedCode, study],
  );

  const confirmClear = useCallback(() => {
    const removed = study.clearStudy();
    setClearOpen(false);
    if (removed) setClearedNotice(true);
  }, [study]);

  /* --- Yamazumi (M5) --------------------------------------------------- */

  const posts = active?.posts ?? [];
  const operations = stage?.operations ?? [];
  const loads = useMemo(
    () => computePostLoads(posts, operations),
    [posts, operations],
  );
  const unassigned = useMemo(
    () => unassignedOperations(posts, operations),
    [posts, operations],
  );

  const stageResult = useMemo(() => {
    if (!active?.computed || !stage) return null;
    return (
      active.computed.result.stages.find(
        (st) => `${st.product_code}#${st.bom_level}` === stage.key,
      ) ?? null
    );
  }, [active?.computed, stage]);

  /* Takt: CALCULATED do domínio quando há resultado; prévia aritmética
   * dos inputs (providencial, não oficial) só como referência visual. */
  const taktMinutes =
    stageResult?.takt_minutes ?? validation.taktPreview;
  const taktProvenance =
    stageResult?.takt_minutes != null
      ? "CALCULATED"
      : taktMinutes != null
        ? "PROVIDED (prévia)"
        : null;

  const autoUnit = useMemo(
    () =>
      resolveChartTimeUnit([
        ...loads.map((l) => l.loadMinutes ?? 0),
        ...(taktMinutes != null ? [taktMinutes] : []),
      ]),
    [loads, taktMinutes],
  );

  const chartSpec = useMemo(
    () => buildYamazumiChartSpec(loads, taktMinutes),
    [loads, taktMinutes],
  );

  const overTaktPosts = loads.filter(
    (l) =>
      l.loadMinutes != null &&
      taktMinutes != null &&
      l.loadMinutes > taktMinutes,
  );
  const unknownTimePosts = loads.filter((l) => l.unknownOps.length > 0);
  const emptyPosts = loads.filter((l) => l.empty);

  const searchRouting = useCallback(() => {
    const code = productCode.trim();
    if (!code) return;
    setQueriedCode(code);
    setBranch("");
    setBranches([]);
    setStageKey(null);
    setBalanceError(null);
    setClearedNotice(false);
  }, [productCode]);

  const assignToPost = useCallback(
    (opKey: string, targetPostId: string) => {
      if (!targetPostId) return;
      for (const u of assignOperationToPost(posts, opKey, targetPostId)) {
        study.patchPost(u.postId, u.patch);
      }
    },
    [posts, study],
  );

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
      ...grouped.stages.map((s) => ({
        value: s.key,
        label: stageLabel(s),
      })),
    ],
    [grouped],
  );

  const methodOptions = BALANCING_METHODS.map((m) => ({
    value: m.id,
    label: `${m.label} — ${m.name}`,
  }));
  const method = BALANCING_METHODS.find((m) => m.id === methodId)!;

  const exportContext = (unit: ChartTimeUnit) => ({
    produto: queriedCode,
    filial: branch || "—",
    estagio: stage ? stageLabel(stage) : "—",
    cenario: active ? `Cenário ${active.label}` : "—",
    unidade: unit.unit,
  });

  const buildYamazumiExportPayload = (
    unit: ChartTimeUnit,
  ): TableExportPayload => {
    const ctx = exportContext(unit);
    const rows = buildYamazumiExportRows(loads, unassigned);
    return {
      title: `Yamazumi — ${ctx.produto} (${ctx.unidade}) — SIMULATION`,
      columns: [
        { key: "produto", label: "Produto" },
        { key: "filial", label: "Filial" },
        { key: "estagio", label: "Estágio" },
        { key: "cenario", label: "Cenário" },
        { key: "metodo", label: "Método" },
        { key: "demanda", label: "Demanda (peças)" },
        { key: "tempo_produtivo", label: "Tempo produtivo (min)" },
        { key: "lote", label: "Lote (peças)" },
        { key: "posto", label: "Posto" },
        { key: "ordem", label: "Ordem" },
        { key: "operacao", label: "Operação" },
        { key: "descricao", label: "Descrição" },
        { key: "ct", label: "Centro de trabalho" },
        { key: "recurso", label: "Recurso" },
        { key: "tempo", label: `Tempo por peça (${ctx.unidade})` },
        { key: "takt", label: `Takt (${ctx.unidade})` },
        { key: "proveniencia", label: "Proveniência" },
        { key: "limitacao", label: "Limitação" },
      ],
      rows: rows.map((r) => ({
        ...ctx,
        metodo: "M5 Yamazumi",
        demanda: validation.params?.demand ?? "—",
        tempo_produtivo: validation.params?.available_minutes ?? "—",
        lote: validation.params?.batch_size ?? "—",
        posto: r.post,
        ordem: r.order,
        operacao: r.operation_code,
        descricao: r.operation_description,
        ct: r.work_center || "—",
        recurso: r.resource || "—",
        tempo:
          typeof r.time_minutes_piece === "number"
            ? (r.time_minutes_piece * unit.factor).toLocaleString("pt-BR", {
                maximumFractionDigits: unit.decimalPlaces,
              })
            : "UNKNOWN",
        takt:
          taktMinutes != null
            ? (taktMinutes * unit.factor).toLocaleString("pt-BR", {
                maximumFractionDigits: unit.decimalPlaces,
              })
            : "—",
        proveniencia: r.provenance,
        limitacao:
          "Hipótese local — não é roteiro aprovado nem dimensionamento validado; sem precedência, simultaneidade ou viabilidade de recursos.",
      })),
    };
  };

  return (
    <>
      <EngineeringSectionCard
        title="Balanceamento de Linha"
        subtitle="Consulte o roteiro de fabricação e construa estudos de balanceamento com diferentes métodos de Engenharia Industrial."
      >
        <div
          className="engineering-processes__lookup"
          role="group"
          aria-label="Consulta do roteiro oficial"
        >
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
        </div>
      </EngineeringSectionCard>

      {!queriedCode ? (
        <EngineeringEmptyState message="Informe o código do produto e acione Buscar roteiro para consultar a fonte oficial." />
      ) : routingLoading ? (
        <EngineeringLoadingActivityCard description="Consultando o roteiro oficial…" />
      ) : routingError ? (
        isForbidden(routingError) ? (
          <EngineeringEmptyState message="Acesso negado pela fonte oficial — você não tem autorização para consultar o roteiro." />
        ) : isNotFound(routingError) ? (
          <EngineeringEmptyState message="Produto não encontrado ou sem roteiro na fonte oficial." />
        ) : (
          <EngineeringStateBanner variant="error">
            {routingError instanceof HomeApiError
              ? routingError.message
              : "Fonte oficial de roteiro indisponível."}
          </EngineeringStateBanner>
        )
      ) : !grouped.stages.length ? (
        <EngineeringEmptyState message="Roteiro oficial vazio para este contexto — nenhuma operação retornada." />
      ) : !stage ? (
        <EngineeringEmptyState message="Selecione a filial e o estágio produtivo para visualizar as operações oficiais e iniciar o estudo." />
      ) : (
        <>
          <EngineeringSectionCard
            title="Operações oficiais do roteiro"
            subtitle={`${queriedCode} · ${operations.length} operação(ões) deduplicada(s) por identidade de operação${routing?.truncated ? " · resultado truncado pela fonte" : ""}`}
          >
            {routing?.truncated ? (
              <EngineeringStateBanner variant="default">
                A fonte retornou resultado paginado incompleto — o estudo
                considera somente as operações efetivamente recebidas.
              </EngineeringStateBanner>
            ) : null}
            <DataTable
              columns={OP_COLUMNS}
              rows={operations}
              rowKey={(op) => op.key}
              layout="embedded"
              compact
              emptyMessage="Nenhuma operação neste estágio."
            />
          </EngineeringSectionCard>

          <EngineeringSectionCard
            title="Estudo de balanceamento"
            subtitle="Parâmetros PROVIDED + hipóteses SIMULATION de organização da linha — cálculo sempre pelo domínio oficial."
            actions={
              study.status !== "idle" ? (
                <EngineeringStatusBadge
                  label={SAVE_STATUS_LABEL[study.status] ?? study.status}
                  variant={
                    study.status === "saved"
                      ? "success"
                      : study.status === "save_error" ||
                          study.status === "storage_unavailable"
                        ? "warning"
                        : "neutral"
                  }
                />
              ) : undefined
            }
          >
            {study.notice === "stale_reference" ? (
              <EngineeringStateBanner variant="default">
                O roteiro oficial mudou desde o último estudo salvo —
                operações referenciadas que não existem mais foram
                desvinculadas (STALE).
              </EngineeringStateBanner>
            ) : null}
            {clearedNotice ? (
              <EngineeringStateBanner variant="default">
                Rascunho local deste contexto limpo — nenhum dado oficial
                foi alterado.
              </EngineeringStateBanner>
            ) : null}

            {study.scenarios.length ? (
              <EngineeringScopeChipBar
                chips={study.scenarios.map((s) => ({
                  id: s.clientId,
                  label: `Cenário ${s.label}`,
                  active: s.clientId === study.activeScenarioId,
                  onSelect: () => study.selectScenario(s.clientId),
                }))}
              />
            ) : null}

            <div className="engineering-routing__balance-grid">
              <EngineeringDetailCard
                title="Condições de produção"
                titleHint="Parâmetros PROVIDED pelo usuário — o tempo produtivo é derivado de turno − pausas e enviado como available_minutes ao domínio EVA."
              >
                <div
                  className="engineering-routing__form-grid"
                  role="group"
                  aria-label="Condições de produção"
                >
                  <EngineeringTextField
                    id="lb-demand"
                    label="Demanda por período (peças)"
                    value={active?.inputs.demand ?? ""}
                    onChange={(v) => study.updateInputs({ demand: v })}
                    required
                    hint="Peças a produzir no período analisado."
                    disabled={balanceRunning}
                  />
                  <EngineeringTextField
                    id="lb-shift"
                    label="Duração do turno (min)"
                    value={active?.inputs.shiftMinutes ?? ""}
                    onChange={(v) => study.updateInputs({ shiftMinutes: v })}
                    required
                    hint="Minutos totais do período, antes das pausas."
                    disabled={balanceRunning}
                  />
                  <EngineeringTextField
                    id="lb-break"
                    label="Pausas (min)"
                    value={active?.inputs.breakMinutes ?? ""}
                    onChange={(v) => study.updateInputs({ breakMinutes: v })}
                    hint="Minutos não produtivos do turno — subtraídos do tempo disponível."
                    disabled={balanceRunning}
                  />
                  <EngineeringTextField
                    id="lb-batch"
                    label="Tamanho do lote (peças)"
                    value={active?.inputs.batchSize ?? ""}
                    onChange={(v) => study.updateInputs({ batchSize: v })}
                    hint="Opcional — só com lote explícito o setup é amortizado por peça."
                    disabled={balanceRunning}
                  />
                  <EngineeringTextField
                    id="lb-stations"
                    label="Número de postos"
                    value={active?.inputs.numStations ?? ""}
                    onChange={(v) => study.updateInputs({ numStations: v })}
                    hint="Opcional — verificação de viabilidade FFD do domínio."
                    disabled={balanceRunning}
                  />
                </div>
                <EngineeringKpiCard
                  title="Prévia do takt"
                  titleHint="Prévia aritmética de interface (disponível ÷ demanda) — o resultado oficial vem do domínio."
                  value={
                    validation.taktPreview !== null
                      ? `${formatMinutes(validation.taktPreview)} / peça`
                      : "—"
                  }
                />
              </EngineeringDetailCard>

              <EngineeringDetailCard
                title="Método de balanceamento"
                titleHint="Catálogo V3 — métodos sem suporte exibem requisitos, nunca um cálculo inerte."
              >
                <div className="engineering-routing__form-grid">
                  <EngineeringFilterSelect
                    label="Método"
                    options={methodOptions}
                    value={methodId}
                    onChange={(v) => setMethodId(v as MethodId)}
                  />
                </div>
                <div className="engineering-processes__method-list">
                  {BALANCING_METHODS.map((m) => (
                    <div
                      key={m.id}
                      className="engineering-processes__method-item"
                    >
                      <span className="engineering-processes__method-head">
                        <strong>
                          {m.label} · {m.name}
                        </strong>
                        <EngineeringStatusBadge
                          label={m.statusLabel}
                          variant={METHOD_STATUS_BADGE_VARIANT[m.status]}
                        />
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
                {validation.errors.length ? (
                  <ul className="engineering-routing__limitations" role="alert">
                    {validation.errors.map((e, i) => (
                      <li key={i}>{e}</li>
                    ))}
                  </ul>
                ) : null}
              </EngineeringDetailCard>
            </div>

            <EngineeringFormActions>
              <EngineeringActionButton
                variant="ghost"
                disabled={
                  balanceRunning ||
                  study.scenarios.length >= study.maxScenarios
                }
                onClick={study.addScenario}
              >
                Novo cenário
              </EngineeringActionButton>
              <EngineeringActionButton
                variant="default"
                disabled={balanceRunning}
                onClick={() => setClearOpen(true)}
              >
                Limpar estudo
              </EngineeringActionButton>
              {methodId === "m1" || methodId === "m2" ? (
                <EngineeringActionButton
                  variant="primary"
                  disabled={validation.params === null || balanceRunning}
                  onClick={() =>
                    validation.params && runBalance(validation.params)
                  }
                >
                  {balanceRunning ? "Calculando…" : "Calcular análise rápida"}
                </EngineeringActionButton>
              ) : null}
            </EngineeringFormActions>

            {balanceError ? (
              <EngineeringStateBanner variant="error">
                {balanceError instanceof HomeApiError
                  ? balanceError.message
                  : "Não foi possível executar o cálculo do domínio."}
              </EngineeringStateBanner>
            ) : null}
          </EngineeringSectionCard>

          {methodId === "m5" ? (
            <EngineeringSectionCard
              title="Yamazumi — organização hipotética da linha"
              subtitle={`Configure postos DRAFT_LOCAL atribuindo operações oficiais e compare a carga ao takt. ${AGGREGATE_TIME_CATEGORY}.`}
            >
              <div className="engineering-processes__yamazumi-grid">
                <div className="engineering-processes__yamazumi-posts">
                  <PostConfigurator
                    posts={posts}
                    operations={operations}
                    maxPosts={study.maxPosts}
                    disabled={!study.ready || balanceRunning}
                    onAdd={study.addPost}
                    onPatch={study.patchPost}
                    onMove={study.movePost}
                    onRemove={study.removePost}
                  />
                  {unassigned.length ? (
                    <EngineeringDetailCard
                      title={`Operações não atribuídas (${unassigned.length})`}
                      titleHint="Operações oficiais fora de qualquer posto hipotético — a carga não é contabilizada até a atribuição."
                    >
                      <ul className="engineering-processes__unassigned">
                        {unassigned.map((op) => (
                          <li
                            key={op.key}
                            className="engineering-processes__unassigned-item"
                          >
                            <span>
                              {op.operation_code || "—"} —{" "}
                              {op.operation_description ?? "—"}
                              {op.time_minutes_piece == null
                                ? " · tempo UNKNOWN"
                                : ` · ${formatMinutes(op.time_minutes_piece)}`}
                            </span>
                            <EngineeringFilterSelect
                              label="Atribuir a"
                              options={[
                                { value: "", label: "Selecionar posto…" },
                                ...posts.map((p, i) => ({
                                  value: p.clientId,
                                  label:
                                    p.name ||
                                    `Posto ${String(i + 1).padStart(2, "0")}`,
                                })),
                              ]}
                              value=""
                              onChange={(v) => assignToPost(op.key, v)}
                              disabled={!posts.length}
                            />
                          </li>
                        ))}
                      </ul>
                      {!posts.length ? (
                        <p className="engineering-routing__muted">
                          Adicione um posto para atribuir operações.
                        </p>
                      ) : null}
                    </EngineeringDetailCard>
                  ) : null}
                </div>

                <div className="engineering-processes__yamazumi-chart">
                  <EngineeringChartCard
                    title="Carga × takt por posto"
                    titleHint={`Cada segmento é uma operação OBSERVED atribuída ao posto (DRAFT_LOCAL); a linha é o takt ${taktProvenance ?? "—"}. Soma simples dos tempos por peça — sem precedência, simultaneidade ou viabilidade.`}
                  >
                    <div className="engineering-processes__yamazumi-legend">
                      {taktProvenance ? (
                        <EngineeringStatusBadge
                          label={`Takt ${formatMinutes(taktMinutes ?? 0)} · ${taktProvenance}`}
                          variant={overTaktPosts.length ? "warning" : "success"}
                        />
                      ) : (
                        <EngineeringStatusBadge
                          label="Takt não disponível — informe demanda e turno"
                          variant="neutral"
                        />
                      )}
                      {overTaktPosts.length ? (
                        <EngineeringStatusBadge
                          label={`Acima do takt: ${overTaktPosts.map((p) => p.postName).join(", ")}`}
                          variant="warning"
                        />
                      ) : null}
                      {unknownTimePosts.length ? (
                        <EngineeringStatusBadge
                          label={`Tempos UNKNOWN em: ${unknownTimePosts.map((p) => p.postName).join(", ")}`}
                          variant="neutral"
                        />
                      ) : null}
                      {emptyPosts.length ? (
                        <EngineeringStatusBadge
                          label={`Postos vazios: ${emptyPosts.map((p) => p.postName).join(", ")}`}
                          variant="neutral"
                        />
                      ) : null}
                      {unassigned.length ? (
                        <EngineeringStatusBadge
                          label={`${unassigned.length} operação(ões) não atribuída(s)`}
                          variant="neutral"
                        />
                      ) : null}
                    </div>
                    {loads.length ? (
                      <RoutingSeriesChart
                        storageKey={`engineering:processes:line-balance:${queriedCode}:yamazumi`}
                        idPrefix="en-lb-yamazumi"
                        data={chartSpec.rows}
                        series={chartSpec.series}
                        autoUnit={autoUnit}
                        allowedChartTypes={["stacked_bar", "bar"]}
                        defaultChartType="stacked_bar"
                        buildExportPayload={buildYamazumiExportPayload}
                        emptyMessage="Atribua operações com tempo oficial para compor o Yamazumi."
                      />
                    ) : (
                      <EngineeringEmptyState message="Adicione postos para compor o Yamazumi." />
                    )}
                    <p className="engineering-routing__muted">
                      Instrumento analítico — a distribuição é hipótese local,
                      não prova viabilidade física nem aprova o processo.
                    </p>
                  </EngineeringChartCard>
                </div>
              </div>
            </EngineeringSectionCard>
          ) : methodId === "m1" || methodId === "m2" ? (
            <BalanceResultsSection
              scenarios={study.scenarios}
              stage={stage}
              branch={branch}
              active={active}
            />
          ) : (
            <EngineeringSectionCard
              title={`${method.label} · ${method.name}`}
              subtitle={method.statusLabel}
            >
              <EngineeringEmptyState
                message={`Método em planejamento — ${method.summary}`}
              />
              {method.requirements?.length ? (
                <ul className="engineering-routing__limitations">
                  {method.requirements.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              ) : null}
            </EngineeringSectionCard>
          )}

          {methodId === "m5" && study.scenarios.some((s) => s.computed) ? (
            <BalanceResultsSection
              scenarios={study.scenarios}
              stage={stage}
              branch={branch}
              active={active}
            />
          ) : null}
        </>
      )}

      <EngineeringConfirmDialog
        open={clearOpen}
        title="Limpar estudo"
        message={
          <>
            Remove apenas o rascunho local deste contexto (produto{" "}
            {queriedCode}, filial {branch || "todas"}, estágio{" "}
            {stage ? stageLabel(stage) : "—"}). Nenhum dado oficial ou
            rascunho da Ficha do Produto é alterado.
          </>
        }
        confirmLabel="Limpar rascunho"
        variant="danger"
        onConfirm={confirmClear}
        onCancel={() => setClearOpen(false)}
      />
    </>
  );
}
