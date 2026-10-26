/**
 * Visão geral V0.2 do Fechamento mensal (Plano 113 §12, doc 112 §35).
 *
 * Composição render-only aprovada pelo PO: estado do fechamento, três
 * indicadores clicáveis, «O que precisa de atenção» como bloco dominante,
 * três cartões independentes (Estoque/Documentos/Pacote DRE), atividade
 * recente real e os blocos separados de Conclusão e Envio ao final.
 *
 * Honestidade de dados:
 * - Códigos técnicos de `blocking_reasons` são traduzidos por um mapa
 *   auditável; o código original aparece apenas como detalhe secundário.
 * - Divergências só exibem número quando fontes/cálculo existem; fonte
 *   indisponível nunca vira zero.
 * - Atividade recente mostra apenas eventos reais retornados pelo owner
 *   de auditoria P3 — nenhum registro sintético.
 * - Conclusão é derivada pelo backend (`derive_closing_state`); a aba
 *   não inventa ação de concluir nem de enviar — apresenta elegibilidade
 *   e navega para as superfícies reais (pacotes/pendências/checklist).
 */
import { useEffect, useRef, useState } from "react";

import type { ClosingCompetence } from "../../api/competencesApi";
import { listP3Events, type P3AuditEvent } from "../../api/p3Api";
import type { Cockpit } from "../../api/packagesApi";
import { ApiError } from "../../api/httpClient";
import {
  CfActionButton,
  CfEventsSection,
  CfInteractiveDataCard,
  CfSectionCard,
  CfStatusBadge,
} from "../../app/controllershipFinanceUi";
import { CF_HELP } from "../../content/helpTooltips";
import { countOpenPendencies } from "./CockpitSummaryPanel";

const ZERO_DIVERGENCE_PATTERN = /^-?0+([.,]0+)?$/;

const CLOSING_LABELS: Record<string, string> = {
  PENDING: "Em andamento",
  MONTHLY_CLOSING_COMPLETED: "Concluído",
  TERMINALLY_REJECTED: "Rejeitado (terminal)",
};

const CLOSING_VARIANTS: Record<
  string,
  "warning" | "info" | "success" | "neutral" | "danger"
> = {
  PENDING: "warning",
  MONTHLY_CLOSING_COMPLETED: "success",
  TERMINALLY_REJECTED: "danger",
};

/** Nomes de domínio P3 → linguagem simples (relatórios reais do processo). */
const DOMAIN_LABELS: Record<string, string> = {
  ENTRADAS_SAIDAS: "entradas e saídas",
  P7: "o relatório P7",
  H02: "o relatório H02",
};

const EVENT_LABELS: Record<string, string> = {
  CUTOFF_CONFIRMED: "Conferência do mês finalizada",
  P3_REVALIDATED: "Conferências refeitas",
  RECONCILIATION_UPDATED: "Conferência atualizada",
  COMPETENCE_OPENED: "Fechamento aberto",
};

const dateTimeFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const dateFormatter = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

function countDivergences(cockpit: Cockpit): number {
  return cockpit.p3.domains.filter(
    (d) =>
      d.divergence !== null && !ZERO_DIVERGENCE_PATTERN.test(d.divergence),
  ).length;
}

function hasUnavailableSource(cockpit: Cockpit): boolean {
  return cockpit.p3.domains.some((d) => d.source_state === "UNAVAILABLE");
}

function humanizeToken(token: string): string {
  return token.replace(/[_-]+/g, " ").trim();
}

function domainLabel(domain: string | undefined): string {
  if (!domain) return "o relatório";
  return DOMAIN_LABELS[domain] ?? humanizeToken(domain).toLowerCase();
}

type AttentionItem = {
  id: string;
  title: string;
  description: string;
  tone: "danger" | "warning" | "info" | "neutral";
  actionLabel: string;
  onAction: () => void;
};

/**
 * Tradutor auditável de códigos `blocking_reasons` (contrato P5/P3) para
 * mensagens em PT-BR simples (V0.3). Códigos desconhecidos nunca aparecem
 * na interface — recebem uma mensagem genérica e ficam restritos aos
 * meios de diagnóstico autorizados.
 */
function describeBlocking(code: string): string {
  const [head, ...params] = code.split(":");
  const table: Record<string, (p: string[]) => string> = {
    terminal_rejection_active: () =>
      "Este fechamento foi rejeitado e não pode ser concluído",
    no_applicable_packages: () =>
      "Não há um conjunto de documentos para envio definido neste mês",
    package_not_submitted: (p) =>
      `Documentos para ${humanizeToken(p[0]).toLowerCase()} ainda não enviados para revisão`,
    no_required_areas: (p) =>
      `Documentos para ${humanizeToken(p[0]).toLowerCase()} sem área revisora definida`,
    area_not_reviewed: (p) =>
      `Documentos para ${humanizeToken(p[0]).toLowerCase()} aguardando revisão de ${humanizeToken(p[1] ?? "").toLowerCase()}`,
    area_not_accepted: (p) =>
      `Documentos para ${humanizeToken(p[0]).toLowerCase()} não aceitos por ${humanizeToken(p[1] ?? "").toLowerCase()}`,
    open_clarification: (p) =>
      `Pendência de esclarecimento nos documentos para ${humanizeToken(p[0]).toLowerCase()}`,
    p3_cutoff_not_confirmed: () =>
      "Conferência do mês ainda não finalizada",
    p3_revalidation_required: () =>
      "As conferências precisam ser refeitas após alterações nas entradas",
    p3_source_unavailable: (p) =>
      `Não foi possível consultar ${domainLabel(p[0])}`,
    p3_divergence: (p) =>
      `Divergência identificada em ${domainLabel(p[0])}`,
    p3_reconciliation_missing: (p) =>
      `Conferência de ${domainLabel(p[0])} ainda não registrada`,
    p3_declared_only: (p) =>
      `Conferência de ${domainLabel(p[0])} aguardando comprovação oficial`,
  };
  const render = table[head];
  return render
    ? render(params)
    : "Existe uma situação pendente que precisa ser verificada";
}

function blockingTarget(code: string): "reports" | "packages" {
  return code.startsWith("p3_") ? "reports" : "packages";
}

function eventLabel(eventType: string): string {
  return (
    EVENT_LABELS[eventType] ?? humanizeToken(eventType).toLowerCase()
  );
}

type EventsResult =
  | { key: string; kind: "ready"; data: P3AuditEvent[] }
  | { key: string; kind: "error"; message: string };

export function MonthlyOverviewPanel({
  cockpit,
  competence,
  period,
  onSelectTab,
  onGoTo,
}: {
  cockpit: Cockpit;
  competence: ClosingCompetence | null;
  period: string;
  onSelectTab: (tab: "documents" | "reports") => void;
  onGoTo: (relativePath: string) => void;
}) {
  const [eventsResult, setEventsResult] = useState<EventsResult | null>(
    null,
  );
  const eventsRequestId = useRef(0);
  const eventsKey = `events:${period}`;

  // Atividade recente — fonte real de auditoria P3, keyed por período;
  // falha nesta fonte nunca apaga os demais blocos.
  useEffect(() => {
    if (!period) return;
    const id = ++eventsRequestId.current;
    const controller = new AbortController();
    listP3Events(period, controller.signal)
      .then((data) => {
        if (controller.signal.aborted || eventsRequestId.current !== id)
          return;
        setEventsResult({ key: eventsKey, kind: "ready", data });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || eventsRequestId.current !== id)
          return;
        setEventsResult({
          key: eventsKey,
          kind: "error",
          message:
            err instanceof ApiError
              ? err.message
              : "Falha ao consultar a atividade recente.",
        });
      });
    return () => controller.abort();
  }, [period, eventsKey]);

  const events =
    eventsResult?.key === eventsKey && eventsResult.kind === "ready"
      ? eventsResult.data
      : null;
  const eventsError =
    eventsResult?.key === eventsKey && eventsResult.kind === "error"
      ? eventsResult.message
      : null;
  const eventsLoading = eventsResult?.key !== eventsKey;

  const blockingCount = cockpit.closing.blocking_reasons.length;
  const divergenceCount = countDivergences(cockpit);
  const unavailableSources = hasUnavailableSource(cockpit);
  const openPendencies = countOpenPendencies(cockpit);
  const expectedDocs = cockpit.checklist["EXPECTED"] ?? 0;
  const checklistTotal = Object.values(cockpit.checklist).reduce(
    (sum, n) => sum + n,
    0,
  );
  // «Documentos a tratar» sem contrato P2 de contagem — «—» honesto.
  const documentsCount: number | null = null;
  const divergenceValue = unavailableSources
    ? null
    : divergenceCount;

  const scrollToAttention = () => {
    const node = document.getElementById("cf-monthly-attention");
    if (node) {
      node.scrollIntoView?.({ behavior: "smooth", block: "start" });
      node.focus({ preventScroll: true });
    }
  };

  // ── Atenção (bloco dominante) ────────────────────────────────────
  // Expansão na própria Visão geral — nunca enviar o usuário para uma
  // listagem parcial com rótulo de «todas as pendências».
  const [showAllAttention, setShowAllAttention] = useState(false);
  const attentionItems: AttentionItem[] = [];
  for (const code of cockpit.closing.blocking_reasons) {
    const head = code.split(":")[0];
    const isBlockingSource =
      head === "p3_source_unavailable" ||
      head === "terminal_rejection_active";
    const target = blockingTarget(code);
    attentionItems.push({
      id: `blocking:${code}`,
      title: describeBlocking(code),
      description:
        target === "reports"
          ? "Conferência do estoque"
          : "Envio à Contabilidade",
      tone: isBlockingSource ? "danger" : "warning",
      actionLabel:
        target === "reports" ? "Ver divergências" : "Ver envio",
      onAction:
        target === "reports"
          ? () => onSelectTab("reports")
          : () => onGoTo(`closing/packages/${period}`),
    });
  }
  if (openPendencies > 0) {
    attentionItems.push({
      id: "pendencies",
      title: `${openPendencies} pendência(s) aguardando tratamento`,
      description: "Pendências",
      tone: "warning",
      actionLabel: "Ver pendências",
      onAction: () => onGoTo("closing/pendencies"),
    });
  }
  if (expectedDocs > 0) {
    attentionItems.push({
      id: "expected-docs",
      title: `${expectedDocs} documento(s) aguardando evidência`,
      description: "Documentos exigidos",
      tone: "warning",
      actionLabel: "Ver documentos",
      onAction: () => onSelectTab("documents"),
    });
  }
  const attention = showAllAttention
    ? attentionItems
    : attentionItems.slice(0, 4);
  const attentionOverflow = attentionItems.length - attention.length;

  // ── Eixo: Conferência do estoque ──────────────────────────────────
  const stockDomains = cockpit.p3.domains;
  const stockUnavailable = stockDomains.filter(
    (d) => d.source_state === "UNAVAILABLE",
  ).length;
  const stockDeclared = stockDomains.filter(
    (d) => d.provenance_kind === "DECLARED",
  ).length;
  const stockSituation = !cockpit.p3.cutoff_confirmed
    ? "A conferência do mês ainda não foi finalizada."
    : stockUnavailable === stockDomains.length && stockDomains.length > 0
      ? `Não foi possível consultar nenhum dos ${stockDomains.length} relatórios necessários.`
      : stockUnavailable > 0
        ? `Não foi possível consultar ${stockUnavailable} de ${stockDomains.length} relatórios necessários.`
        : divergenceCount > 0
          ? `${divergenceCount} divergência(s) identificada(s) na conferência.`
          : stockDeclared > 0
            ? "Conferência realizada — aguardando comprovação oficial."
            : "Conferência do estoque em dia.";
  const stockNextStep = !cockpit.p3.cutoff_confirmed
    ? "Próximo passo: finalizar a conferência do mês."
    : stockUnavailable > 0
      ? "Próximo passo: verificar os relatórios que não puderam ser consultados."
      : divergenceCount > 0
        ? "Próximo passo: analisar as divergências em Relatórios e divergências."
        : stockDeclared > 0
          ? "Próximo passo: anexar a comprovação oficial."
          : null;

  // ── Eixo: Documentos do mês ───────────────────────────────────────
  const acceptedDocs = cockpit.checklist["ACCEPTED"] ?? 0;

  // ── Eixo: Documentos para a Contabilidade ─────────────────────────
  const packages = cockpit.closing.packages;
  const packagesReady = packages.filter(
    (p) => p.state === "PACKAGE_FINALIZED",
  ).length;
  const packagesInReview = packages.filter(
    (p) => p.state === "PACKAGE_SUBMITTED_FOR_REVIEW",
  ).length;

  // ── Conclusão / Envio ─────────────────────────────────────────────
  const closingState = cockpit.closing.state;
  const conclusionBlockers = blockingCount;

  const eventItems = (events ?? []).slice(0, 5).map((event) => ({
    id: String(event.event_id),
    title: eventLabel(event.event_type),
    description: `${dateTimeFormatter.format(new Date(event.created_at))} · ${event.actor_subject}`,
    tone: "neutral" as const,
  }));

  return (
    <>
      <div
        className="cf-monthly-status"
        aria-label="Estado do fechamento"
      >
        <CfStatusBadge
          variant={CLOSING_VARIANTS[closingState] ?? "neutral"}
          label={
            CLOSING_LABELS[closingState] ??
            humanizeToken(closingState)
          }
        />
        {competence ? (
          <span className="cf-monthly-status-meta">
            Aberto em{" "}
            {dateFormatter.format(new Date(competence.opened_at))}
            {competence.template_version_id === null
              ? " · sem lista de documentos definida"
              : ""}
          </span>
        ) : null}
      </div>

      <div
        className="cf-monthly-indicators"
        aria-label="Indicadores de atenção"
      >
        <CfInteractiveDataCard
          ariaLabel={`O que falta resolver: ${blockingCount}`}
          fields={[
            {
              id: "value",
              label: "O que falta resolver",
              value: String(blockingCount),
              valueTone: "value",
              present: true,
              hint: "situações que impedem a conclusão",
            },
          ]}
          openHint="Ver na lista abaixo"
          onActivate={scrollToAttention}
        />
        <CfInteractiveDataCard
          ariaLabel={`Divergências: ${divergenceValue === null ? "—" : divergenceValue}`}
          fields={[
            {
              id: "value",
              label: "Divergências",
              value:
                divergenceValue === null ? "—" : String(divergenceValue),
              valueTone: "value",
              present: true,
              hint:
                divergenceValue === null
                  ? "não foi possível consultar os relatórios"
                  : "diferenças encontradas nas conferências",
            },
          ]}
          openHint="Ver em Relatórios e divergências"
          onActivate={() => onSelectTab("reports")}
        />
        <CfInteractiveDataCard
          ariaLabel={`Documentos a tratar: ${documentsCount === null ? "—" : documentsCount}`}
          fields={[
            {
              id: "value",
              label: "Documentos a tratar",
              value: documentsCount === null ? "—" : String(documentsCount),
              valueTone: "value",
              present: true,
              hint: "contagem ainda não disponível",
            },
          ]}
          openHint="Ver em Documentos e interações"
          onActivate={() => onSelectTab("documents")}
        />
      </div>

      <section
        id="cf-monthly-attention"
        tabIndex={-1}
        aria-label="O que precisa de atenção"
      >
        <CfEventsSection
          title="O que precisa de atenção"
          subtitle={
            attentionOverflow > 0
              ? `Mostrando ${attention.length} de ${attentionItems.length} situações`
              : "Situações reais deste fechamento"
          }
          hint={CF_HELP.monthlyClosing.attention}
          items={attention}
          omitWhenEmpty={false}
          emptyMessage="Nada pendente neste fechamento."
          listAriaLabel="O que precisa de atenção"
        />
        {attentionOverflow > 0 ? (
          <div className="cf-settlements-actions">
            <CfActionButton
              variant="ghost"
              onClick={() => setShowAllAttention(true)}
            >
              Mostrar todas as {attentionItems.length} situações
            </CfActionButton>
          </div>
        ) : null}
        {showAllAttention && attentionItems.length > 4 ? (
          <div className="cf-settlements-actions">
            <CfActionButton
              variant="ghost"
              onClick={() => setShowAllAttention(false)}
            >
              Mostrar menos
            </CfActionButton>
          </div>
        ) : null}
      </section>

      <div className="cf-monthly-axes" aria-label="Acompanhamento por eixo">
        <CfSectionCard
          title="Conferência do estoque"
          hint={CF_HELP.monthlyClosing.stockAxis}
        >
          <ul className="cf-axis-facts">
            <li>{stockSituation}</li>
            {stockNextStep ? (
              <li className="cf-axis-next">{stockNextStep}</li>
            ) : null}
          </ul>
        </CfSectionCard>

        <CfSectionCard
          title="Documentos do mês"
          hint={CF_HELP.monthlyClosing.docsAxis}
        >
          {checklistTotal === 0 ? (
            <p>Nenhum documento exigido para este fechamento.</p>
          ) : (
            <ul className="cf-axis-facts">
              <li>
                {checklistTotal} documento(s) exigido(s) neste mês —{" "}
                {expectedDocs} aguardando evidência, {acceptedDocs}{" "}
                aceito(s).
              </li>
              {expectedDocs > 0 ? (
                <li className="cf-axis-next">
                  Próximo passo: revisar em Documentos e interações.
                </li>
              ) : null}
            </ul>
          )}
        </CfSectionCard>

        <CfSectionCard
          title="Documentos para a Contabilidade"
          hint={CF_HELP.monthlyClosing.packageAxis}
        >
          {packages.length === 0 ? (
            <p>
              Não há um conjunto de documentos para envio definido neste
              mês.
            </p>
          ) : (
            <ul className="cf-axis-facts">
              <li>
                {packagesReady} conjunto(s) pronto(s) para envio
                {packagesInReview > 0
                  ? ` · ${packagesInReview} já enviado(s) para revisão`
                  : ""}
                .
              </li>
            </ul>
          )}
          <div className="cf-settlements-actions">
            <CfActionButton
              variant="ghost"
              onClick={() => onGoTo(`closing/packages/${period}`)}
            >
              Ver detalhes
            </CfActionButton>
          </div>
        </CfSectionCard>
      </div>

      <CfEventsSection
        title="Atividades recentes"
        subtitle="Registros reais das conferências deste mês"
        hint={CF_HELP.monthlyClosing.recentActivity}
        items={eventItems}
        omitWhenEmpty={false}
        emptyMessage={
          eventsLoading
            ? "Carregando atividades…"
            : eventsError
              ? eventsError
              : "Ainda não há atividades registradas nesta conferência."
        }
        listAriaLabel="Atividades recentes do fechamento"
      />

      <div className="cf-monthly-outcomes" aria-label="Conclusão e envio">
        <CfSectionCard
          title="Concluir fechamento"
          hint={CF_HELP.monthlyClosing.conclusion}
        >
          <p>
            <CfStatusBadge
              variant={CLOSING_VARIANTS[closingState] ?? "neutral"}
              label={CLOSING_LABELS[closingState] ?? closingState}
            />
          </p>
          {closingState === "MONTHLY_CLOSING_COMPLETED" ? (
            <p>Este fechamento está concluído.</p>
          ) : (
            <p>
              O fechamento será concluído quando todas as condições forem
              atendidas
              {conclusionBlockers > 0
                ? ` — ${conclusionBlockers} situação(ões) ainda impedem a conclusão`
                : ""}
              .
            </p>
          )}
          {conclusionBlockers > 0 ? (
            <div className="cf-settlements-actions">
              <CfActionButton variant="ghost" onClick={scrollToAttention}>
                Ver o que falta resolver
              </CfActionButton>
            </div>
          ) : null}
        </CfSectionCard>

        <CfSectionCard
          title="Enviar documentos à Contabilidade"
          hint={CF_HELP.monthlyClosing.sendPackage}
        >
          {packages.length === 0 ? (
            <p>
              Não há um conjunto de documentos para envio definido neste
              mês.
            </p>
          ) : (
            <p>
              {packagesReady} conjunto(s) pronto(s) para envio
              {packagesInReview > 0
                ? ` · ${packagesInReview} já enviado(s) para revisão`
                : ""}
              . O envio é uma operação separada da conclusão e exige
              confirmação.
            </p>
          )}
          <div className="cf-settlements-actions">
            <CfActionButton
              variant="ghost"
              onClick={() => onGoTo(`closing/packages/${period}`)}
            >
              Gerenciar envio
            </CfActionButton>
          </div>
        </CfSectionCard>
      </div>
    </>
  );
}
