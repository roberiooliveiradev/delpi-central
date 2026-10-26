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

const ITEM_STATE_LABELS: Record<string, string> = {
  EXPECTED: "aguardando evidência",
  ACCEPTED: "aceitos",
  NOT_APPLICABLE: "não aplicáveis",
  CANCELLED: "cancelados",
};

const EVENT_LABELS: Record<string, string> = {
  CUTOFF_CONFIRMED: "Cutoff confirmado",
  P3_REVALIDATED: "Conciliações revalidadas",
  RECONCILIATION_UPDATED: "Conciliação atualizada",
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
 * mensagens em PT-BR. Código técnico permanece visível como detalhe —
 * nunca como mensagem principal.
 */
function describeBlocking(code: string): string {
  const [head, ...params] = code.split(":");
  const table: Record<string, (p: string[]) => string> = {
    terminal_rejection_active: () =>
      "Rejeição terminal ativa — a competência não pode concluir",
    no_applicable_packages: () =>
      "Nenhum pacote aplicável configurado neste mês",
    package_not_submitted: (p) =>
      `Pacote de ${humanizeToken(p[0])} ainda não enviado para revisão`,
    no_required_areas: (p) =>
      `Pacote de ${humanizeToken(p[0])} sem áreas revisoras definidas`,
    area_not_reviewed: (p) =>
      `Pacote de ${humanizeToken(p[0])} aguardando revisão de ${humanizeToken(p[1] ?? "")}`,
    area_not_accepted: (p) =>
      `Pacote de ${humanizeToken(p[0])} não aceito por ${humanizeToken(p[1] ?? "")}`,
    open_clarification: (p) =>
      `Esclarecimento em aberto no pacote de ${humanizeToken(p[0])}`,
    p3_cutoff_not_confirmed: () => "Cutoff do mês ainda não confirmado",
    p3_revalidation_required: () =>
      "Entradas alteradas — as conciliações precisam de nova revalidação",
    p3_source_unavailable: (p) =>
      `Fonte ${p[0]} indisponível — não foi possível verificar a conciliação`,
    p3_divergence: (p) =>
      `Divergência monetária identificada em ${p[0]}`,
    p3_reconciliation_missing: (p) =>
      `Conciliação de ${p[0]} ainda não registrada`,
    p3_declared_only: (p) =>
      `Conciliação de ${p[0]} apenas declarada — aguardando resultado oficial`,
  };
  const render = table[head];
  return render
    ? render(params)
    : `Pendência identificada pelo fechamento (${code})`;
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
          ? "Conciliação P3 — condição impeditiva de conclusão"
          : "Pacotes e revisão — condição impeditiva de conclusão",
      tone: isBlockingSource ? "danger" : "warning",
      actionLabel: target === "reports" ? "Ver relatórios" : "Ver pacotes",
      onAction:
        target === "reports"
          ? () => onSelectTab("reports")
          : () => onGoTo(`closing/packages/${period}`),
    });
  }
  if (openPendencies > 0) {
    attentionItems.push({
      id: "pendencies",
      title: `${openPendencies} pendência(s) em aberto`,
      description:
        "Registros P4 aguardando tratamento — não impedem a consulta.",
      tone: "warning",
      actionLabel: "Ver pendências",
      onAction: () => onGoTo("closing/pendencies"),
    });
  }
  if (expectedDocs > 0) {
    attentionItems.push({
      id: "expected-docs",
      title: `${expectedDocs} item(ns) do checklist aguardando evidência`,
      description:
        "Itens previstos na abertura deste fechamento sem evidência entregue.",
      tone: "warning",
      actionLabel: "Ver documentos",
      onAction: () => onSelectTab("documents"),
    });
  }
  const attention = attentionItems.slice(0, 4);
  const attentionOverflow = attentionItems.length - attention.length;

  // ── Eixo Estoque ──────────────────────────────────────────────────
  const stockDomains = cockpit.p3.domains;
  const stockUnavailable = stockDomains.filter(
    (d) => d.source_state === "UNAVAILABLE",
  ).length;
  const stockDeclared = stockDomains.filter(
    (d) => d.provenance_kind === "DECLARED",
  ).length;
  const stockNextStep = !cockpit.p3.cutoff_confirmed
    ? "Próximo passo: confirmar o cutoff do mês."
    : stockUnavailable > 0
      ? "Próximo passo: verificar as fontes indisponíveis."
      : divergenceCount > 0
        ? "Próximo passo: tratar as divergências identificadas."
        : stockDeclared > 0
          ? "Próximo passo: comprovar o resultado oficial."
          : "Conciliação oficial em dia.";

  // ── Eixo Documentos ───────────────────────────────────────────────
  const docStates = Object.entries(cockpit.checklist).filter(
    ([, n]) => n > 0,
  );

  // ── Eixo Pacote DRE ───────────────────────────────────────────────
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
              ? " · sem checklist publicado"
              : ""}
          </span>
        ) : null}
      </div>

      <div
        className="cf-monthly-indicators"
        aria-label="Indicadores de atenção"
      >
        <CfInteractiveDataCard
          ariaLabel={`Bloqueios: ${blockingCount}`}
          fields={[
            {
              id: "value",
              label: "Bloqueios",
              value: String(blockingCount),
              valueTone: "value",
              present: true,
              hint: "condições que impedem a conclusão",
            },
          ]}
          openHint="Ver na seção de atenção"
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
                  ? "não foi possível verificar — fonte indisponível"
                  : "domínios P3 com divergência",
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
              hint: "contagem aguardando contrato do owner P2",
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
              : "Situações reais identificadas neste fechamento"
          }
          hint={CF_HELP.monthlyClosing.attention}
          items={attention}
          omitWhenEmpty={false}
          emptyMessage="Nenhuma pendência identificada neste fechamento."
          listAriaLabel="O que precisa de atenção"
        />
        {attentionOverflow > 0 ? (
          <div className="cf-settlements-actions">
            <CfActionButton
              variant="ghost"
              onClick={() => onGoTo("closing/pendencies")}
            >
              Ver todas as pendências
            </CfActionButton>
          </div>
        ) : null}
      </section>

      <div className="cf-monthly-axes" aria-label="Acompanhamento por eixo">
        <CfSectionCard
          title="Estoque"
          hint={CF_HELP.monthlyClosing.stockAxis}
        >
          <ul className="cf-axis-facts">
            <li>
              Cutoff:{" "}
              {cockpit.p3.cutoff_confirmed
                ? "confirmado"
                : "não confirmado"}
            </li>
            <li>
              Fontes: {stockDomains.length - stockUnavailable} de{" "}
              {stockDomains.length} disponíveis
              {stockUnavailable > 0
                ? ` (${stockUnavailable} indisponível(is))`
                : ""}
            </li>
            <li className="cf-axis-next">{stockNextStep}</li>
          </ul>
        </CfSectionCard>

        <CfSectionCard
          title="Documentos"
          hint={CF_HELP.monthlyClosing.docsAxis}
        >
          {checklistTotal === 0 ? (
            <p>
              Sem exigências cadastradas — o fechamento foi aberto sem
              checklist publicado.
            </p>
          ) : (
            <ul className="cf-axis-facts">
              {docStates.map(([state, n]) => (
                <li key={state}>
                  {n} {ITEM_STATE_LABELS[state] ?? humanizeToken(state)}
                </li>
              ))}
            </ul>
          )}
        </CfSectionCard>

        <CfSectionCard
          title="Pacote DRE"
          hint={CF_HELP.monthlyClosing.packageAxis}
        >
          {packages.length === 0 ? (
            <p>Nenhum pacote aplicável neste mês.</p>
          ) : (
            <ul className="cf-axis-facts">
              <li>
                {packages.length} pacote(s) — {packagesReady} preparado(s),{" "}
                {packagesInReview} em revisão
              </li>
            </ul>
          )}
          <div className="cf-settlements-actions">
            <CfActionButton
              variant="ghost"
              onClick={() => onGoTo(`closing/packages/${period}`)}
            >
              Ver pacotes
            </CfActionButton>
          </div>
        </CfSectionCard>
      </div>

      <CfEventsSection
        title="Atividade recente"
        subtitle="Eventos registrados nesta competência (auditoria P3)"
        hint={CF_HELP.monthlyClosing.recentActivity}
        items={eventItems}
        omitWhenEmpty={false}
        emptyMessage={
          eventsLoading
            ? "Carregando atividade…"
            : eventsError
              ? eventsError
              : "Nenhuma atividade registrada para esta competência."
        }
        listAriaLabel="Atividade recente do fechamento"
      />

      <div className="cf-monthly-outcomes" aria-label="Conclusão e envio">
        <CfSectionCard
          title="Conclusão da etapa da Controladoria"
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
              A conclusão é derivada pelo sistema quando todas as condições
              são atendidas — {conclusionBlockers} condição(ões) impeditiva(s)
              no momento.
            </p>
          )}
          {conclusionBlockers > 0 ? (
            <div className="cf-settlements-actions">
              <CfActionButton variant="ghost" onClick={scrollToAttention}>
                Ver condições impeditivas
              </CfActionButton>
            </div>
          ) : null}
        </CfSectionCard>

        <CfSectionCard
          title="Envio do pacote documental"
          hint={CF_HELP.monthlyClosing.sendPackage}
        >
          {packages.length === 0 ? (
            <p>
              Sem pacote aplicável neste mês — o envio fica indisponível
              até existir um pacote preparado.
            </p>
          ) : (
            <p>
              {packagesReady} de {packages.length} pacote(s) preparado(s)
              para envio; {packagesInReview} já em revisão. O envio é uma
              operação separada da conclusão e exige confirmação humana.
            </p>
          )}
          <div className="cf-settlements-actions">
            <CfActionButton
              variant="ghost"
              onClick={() => onGoTo(`closing/packages/${period}`)}
            >
              Gerenciar pacotes
            </CfActionButton>
          </div>
        </CfSectionCard>
      </div>
    </>
  );
}
