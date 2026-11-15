import { useEffect, useState } from "react";

import {
  entryAuditDownloadUrl,
  getEntryAuditAnalysis,
  getEntryAuditOccurrence,
  setEntryAuditOccurrenceStatus,
  type EntryAuditOccurrence,
} from "../../api/entryAuditApi";
import {
  CfActionButton,
  CfDetailCard,
  CfPageHero,
  CfPagePath,
  CfResolutionStatusCell,
  CfStateBanner,
  CfTimeline,
  CfTitleWithHelp,
} from "../../app/controllershipFinanceUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { CF_HELP } from "../../content/helpTooltips";
import { EntryAuditLoadingState } from "./EntryAuditLoadingState";
import { EntryAuditSeverityBadge } from "./EntryAuditSeverityBadge";
import {
  ENTRY_AUDIT_ACTION_ICONS,
  displayValue,
  entryAuditOccurrenceClaraPrompt,
  entryAuditFieldLabel,
  formatDifference,
  formatOccurrenceValue,
  formatNoteSeries,
  formatPeriodLabel,
  formatTheme,
} from "./entryAuditPresentation";

export function EntryAuditOccurrencePage({
  basePath,
  analysisId,
  occurrenceKey,
}: {
  basePath: string;
  analysisId: string;
  occurrenceKey: string;
}) {
  const [occurrence, setOccurrence] = useState<EntryAuditOccurrence | null>(null);
  const [period, setPeriod] = useState<{ from: string; to: string } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [copiedHint, setCopiedHint] = useState("");
  const [confirmAction, setConfirmAction] = useState<"resolve" | "reopen" | null>(
    null,
  );

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      getEntryAuditOccurrence(analysisId, occurrenceKey, controller.signal),
      getEntryAuditAnalysis(analysisId, controller.signal),
    ])
      .then(([item, analysis]) => {
        setOccurrence(item);
        setPeriod({ from: analysis.date_from, to: analysis.date_to });
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            reason instanceof Error
              ? reason.message
              : "Falha ao carregar a ocorrência.",
          );
        }
      });
    return () => controller.abort();
  }, [analysisId, occurrenceKey]);

  const back = () => {
    const search = typeof window === "undefined" ? "" : window.location.search;
    navigatePluginPath(
      `${basePath}/entry-audit/analyses/${encodeURIComponent(analysisId)}${search}`,
    );
  };

  const goHome = () => navigatePluginPath(basePath);
  const goEntry = () => navigatePluginPath(`${basePath}/entry-audit`);

  const toggleStatus = async () => {
    if (!occurrence) return;
    setBusy(true);
    setError("");
    try {
      const action = occurrence.status === "resolved" ? "reopen" : "resolve";
      await setEntryAuditOccurrenceStatus(occurrence.stable_key, action);
      setOccurrence(await getEntryAuditOccurrence(analysisId, occurrenceKey));
      setConfirmAction(null);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Falha ao atualizar ocorrência.",
      );
    } finally {
      setBusy(false);
    }
  };

  const copyForClara = async () => {
    if (!occurrence || !period) return;
    const text = entryAuditOccurrenceClaraPrompt(
      occurrence.stable_key,
      period.from,
      period.to,
    );
    try {
      await navigator.clipboard.writeText(text);
      setCopiedHint("Copiado");
      window.setTimeout(() => setCopiedHint(""), 2000);
    } catch {
      setCopiedHint("Não foi possível copiar");
      window.setTimeout(() => setCopiedHint(""), 2000);
    }
  };

  if (error && !occurrence) {
    return (
      <CfStateBanner variant="error">
        {error}
        <CfActionButton variant="ghost" onClick={back}>
          Voltar para a análise
        </CfActionButton>
      </CfStateBanner>
    );
  }

  if (!occurrence || !period) {
    return (
      <EntryAuditLoadingState
        back={{ label: "Início", href: basePath, onNavigate: goHome }}
        pathItems={[
          {
            id: "entry",
            label: "Auditoria de Entradas",
            href: `${basePath}/entry-audit`,
            onNavigate: goEntry,
          },
          {
            id: "analysis",
            label: "Análise",
            href: `${basePath}/entry-audit/analyses/${encodeURIComponent(analysisId)}`,
            onNavigate: back,
          },
        ]}
        current="Ocorrência"
        title="Ocorrência"
        hint={CF_HELP.entryAudit.detail}
      />
    );
  }

  const xmlHref = occurrence.links?.xml
    ? entryAuditDownloadUrl(occurrence.links.xml)
    : null;
  const periodLabel = formatPeriodLabel(period.from, period.to);
  const isResolved = occurrence.status === "resolved";

  return (
    <section className="cf-page-stack" aria-label="Detalhe da ocorrência">
      <CfPagePath
        ariaLabel="Caminho da página"
        size="sm"
        back={{
          label: "Início",
          href: basePath,
          onNavigate: (event: { preventDefault: () => void }) => {
            event.preventDefault();
            goHome();
          },
        }}
        items={[
          {
            id: "notas",
            label: "Notas fiscais",
            href: basePath,
            onNavigate: (event: { preventDefault: () => void }) => {
              event.preventDefault();
              goHome();
            },
          },
          {
            id: "entry",
            label: "Auditoria de Entradas",
            href: `${basePath}/entry-audit`,
            onNavigate: (event: { preventDefault: () => void }) => {
              event.preventDefault();
              goEntry();
            },
          },
          {
            id: "analysis",
            label: `Análise ${periodLabel}`,
            href: `${basePath}/entry-audit/analyses/${encodeURIComponent(analysisId)}`,
            onNavigate: (event: { preventDefault: () => void }) => {
              event.preventDefault();
              back();
            },
          },
        ]}
        current="Ocorrência"
      />

      <CfPageHero
        eyebrow="Notas fiscais"
        title={
          <CfTitleWithHelp
            title={occurrence.title || "Ocorrência"}
            hint={CF_HELP.entryAudit.detail}
          />
        }
        description={`Documento ${formatNoteSeries(occurrence.document_number, occurrence.series)} · ${displayValue(occurrence.supplier_name)}`}
        badge={<EntryAuditSeverityBadge severity={occurrence.severity} />}
        actions={
          <>
            <CfActionButton variant="ghost" onClick={copyForClara}>
              Copiar pergunta para a CLARA
            </CfActionButton>
            <CfActionButton variant="ghost" onClick={back}>
              Voltar para a análise
            </CfActionButton>
          </>
        }
      />
      <p aria-live="polite">{copiedHint}</p>

      {error ? <CfStateBanner variant="error">{error}</CfStateBanner> : null}

      {confirmAction ? (
        <CfStateBanner variant="default">
          {confirmAction === "resolve"
            ? "Confirmar marcar como resolvida?"
            : "Confirmar reabrir a ocorrência?"}
          <CfActionButton
            variant="primary"
            disabled={busy}
            softDisabled
            onClick={toggleStatus}
          >
            Confirmar
          </CfActionButton>
          <CfActionButton
            variant="ghost"
            onClick={() => setConfirmAction(null)}
          >
            Cancelar
          </CfActionButton>
        </CfStateBanner>
      ) : null}

      <CfDetailCard
        title="Tratamento"
        headerActions={
          <CfResolutionStatusCell
            variant="full"
            status={isResolved ? "resolved" : "open"}
            pending={busy}
            onResolve={
              isResolved
                ? undefined
                : () => setConfirmAction("resolve")
            }
            onReopen={
              isResolved ? () => setConfirmAction("reopen") : undefined
            }
          />
        }
      >
        <dl>
          <dt>Severidade</dt>
          <dd>
            <EntryAuditSeverityBadge severity={occurrence.severity} />
          </dd>
          <dt>Tema</dt>
          <dd>{formatTheme(occurrence.theme)}</dd>
          <dt>Regra</dt>
          <dd>{displayValue(occurrence.rule_name ?? occurrence.title)}</dd>
          <dt>Por que ocorreu</dt>
          <dd>{displayValue(occurrence.why)}</dd>
          <dt>O que fazer</dt>
          <dd>{displayValue(occurrence.action)}</dd>
          {occurrence.clara_suggestion ? (
            <>
              <dt>Sugestão da CLARA</dt>
              <dd>{occurrence.clara_suggestion}</dd>
            </>
          ) : null}
        </dl>
      </CfDetailCard>

      <CfDetailCard
        title="Comparação"
        hint={CF_HELP.entryAudit.fieldValues}
      >
        <dl>
          <dt>Nota/Série</dt>
          <dd>
            {formatNoteSeries(occurrence.document_number, occurrence.series)}
          </dd>
          <dt>Fornecedor</dt>
          <dd>{displayValue(occurrence.supplier_name)}</dd>
          <dt>TES</dt>
          <dd>{displayValue(occurrence.tes)}</dd>
          <dt>Campo</dt>
          <dd>{entryAuditFieldLabel(occurrence)}</dd>
          <dt>Protheus</dt>
          <dd>{formatOccurrenceValue(occurrence.protheus_value, occurrence)}</dd>
          <dt>XML</dt>
          <dd>{formatOccurrenceValue(occurrence.xml_value, occurrence)}</dd>
          <dt>Diferença</dt>
          <dd>{formatDifference(occurrence.difference, occurrence.field)}</dd>
        </dl>
        {xmlHref ? (
          <CfActionButton href={xmlHref} title="Baixar XML desta ocorrência">
            <span className="cf-action-with-icon">
              {ENTRY_AUDIT_ACTION_ICONS.xml}
              Baixar XML
            </span>
          </CfActionButton>
        ) : (
          <p>XML não disponível para esta ocorrência.</p>
        )}
      </CfDetailCard>

      <CfDetailCard title="Histórico">
        {occurrence.history?.length ? (
          <CfTimeline
            items={occurrence.history.map((event, index) => ({
              id: `${event.event}-${event.at ?? index}`,
              title: displayValue(event.event),
              occurredAt: event.at,
              timeLabel: event.at
                ? new Date(event.at).toLocaleString("pt-BR")
                : undefined,
              meta: event.actor || undefined,
            }))}
          />
        ) : (
          <p>Sem eventos registrados.</p>
        )}
      </CfDetailCard>
    </section>
  );
}
