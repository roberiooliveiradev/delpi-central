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
  CfResolutionStatusCell,
  CfStateBanner,
  CfTitleWithHelp,
} from "../../app/controllershipFinanceUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { CF_HELP } from "../../content/helpTooltips";
import {
  displayValue,
  entryAuditOccurrenceClaraPrompt,
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

  const toggleStatus = async () => {
    if (!occurrence) return;
    setBusy(true);
    setError("");
    try {
      const action = occurrence.status === "resolved" ? "reopen" : "resolve";
      await setEntryAuditOccurrenceStatus(occurrence.stable_key, action);
      setOccurrence(await getEntryAuditOccurrence(analysisId, occurrenceKey));
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
    return <CfStateBanner variant="error">{error}</CfStateBanner>;
  }
  if (!occurrence) return <p aria-live="polite">Carregando ocorrência…</p>;

  const xmlHref = occurrence.links?.xml
    ? entryAuditDownloadUrl(occurrence.links.xml)
    : null;

  return (
    <section className="cf-page-stack" aria-label="Detalhe da ocorrência">
      <CfPageHero
        eyebrow="Auditoria de Entradas"
        title={
          <CfTitleWithHelp
            title={occurrence.title || "Ocorrência"}
            hint={CF_HELP.entryAudit.detail}
          />
        }
        description={`Documento ${displayValue(occurrence.document_number)} · ${displayValue(occurrence.supplier_name)}`}
        actions={
          <>
            <CfActionButton variant="ghost" onClick={copyForClara}>
              Copiar pergunta para a CLARA
            </CfActionButton>
            <CfActionButton onClick={back}>Voltar para a análise</CfActionButton>
          </>
        }
      />
      <p aria-live="polite">{copiedHint}</p>

      {error ? <CfStateBanner variant="error">{error}</CfStateBanner> : null}

      <CfDetailCard
        title="Tratamento"
        headerActions={
          <CfResolutionStatusCell
            variant="full"
            status={occurrence.status === "resolved" ? "resolved" : "open"}
            pending={busy}
            onResolve={occurrence.status === "resolved" ? undefined : toggleStatus}
            onReopen={occurrence.status === "resolved" ? toggleStatus : undefined}
          />
        }
      >
        <dl>
          <dt>Severidade</dt>
          <dd>{displayValue(occurrence.severity)}</dd>
          <dt>Tema</dt>
          <dd>{displayValue(occurrence.theme)}</dd>
          <dt>Por que ocorreu</dt>
          <dd>{displayValue(occurrence.why)}</dd>
          <dt>Ação sugerida</dt>
          <dd>{displayValue(occurrence.action)}</dd>
          {occurrence.clara_suggestion ? (
            <>
              <dt>Sugestão da CLARA</dt>
              <dd>{occurrence.clara_suggestion}</dd>
            </>
          ) : null}
        </dl>
      </CfDetailCard>

      <CfDetailCard title="Comparação">
        <dl>
          <dt>Campo</dt>
          <dd>{displayValue(occurrence.field_label ?? occurrence.field)}</dd>
          <dt>Protheus</dt>
          <dd>{displayValue(occurrence.protheus_value)}</dd>
          <dt>XML</dt>
          <dd>{displayValue(occurrence.xml_value)}</dd>
          <dt>Diferença</dt>
          <dd>{displayValue(occurrence.difference)}</dd>
          <dt>TES</dt>
          <dd>{displayValue(occurrence.tes)}</dd>
        </dl>
        {xmlHref ? (
          <a href={xmlHref} download>
            Baixar XML
          </a>
        ) : (
          <p>XML não disponível para esta ocorrência.</p>
        )}
      </CfDetailCard>

      <CfDetailCard title="Histórico">
        {occurrence.history?.length ? (
          <ol>
            {occurrence.history.map((event, index) => (
              <li key={`${event.event}-${event.at ?? index}`}>
                <strong>{displayValue(event.event)}</strong>
                {event.actor ? ` · ${event.actor}` : ""}
                {event.at
                  ? ` · ${new Date(event.at).toLocaleString("pt-BR")}`
                  : ""}
              </li>
            ))}
          </ol>
        ) : (
          <p>Sem eventos registrados.</p>
        )}
      </CfDetailCard>
    </section>
  );
}
