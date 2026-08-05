import { useEffect, useState } from "react";
import {
  BookOpen,
  CalendarDays,
  CheckCircle2,
  Download,
  FileText,
  Lightbulb,
  Target,
} from "lucide-react";

import {
  acknowledgeCurrentGuidance,
  downloadGuidanceDocument,
  fetchCurrentGuidance,
  fetchCurrentGuidanceDocuments,
} from "../api/budgetPlanningApi";
import type { GuidanceCurrent, GuidanceDocument } from "../types/budgetPlanning";
import { PageShell } from "../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../components/uiKit";

const DECLARATION_TEXT =
  "Declaro que li e compreendi as orientações para elaboração do Planejamento Orçamentário.";

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function OrientacoesPage() {
  const [guidance, setGuidance] = useState<GuidanceCurrent | null>(null);
  const [documents, setDocuments] = useState<GuidanceDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [declared, setDeclared] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);

    Promise.all([
      fetchCurrentGuidance(controller.signal),
      fetchCurrentGuidanceDocuments(controller.signal),
    ])
      .then(([guidanceData, docs]) => {
        setGuidance(guidanceData);
        setDocuments(docs);
        setConfirmed(Boolean(guidanceData.acknowledged));
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar orientações.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, []);

  async function handleConfirm() {
    if (!declared || submitting || confirmed) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      await acknowledgeCurrentGuidance();
      setConfirmed(true);
      if (guidance) setGuidance({ ...guidance, acknowledged: true });
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : "Não foi possível confirmar a leitura.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDownload(doc: GuidanceDocument) {
    setDownloadingId(doc.id);
    try {
      const blob = await downloadGuidanceDocument(doc.id);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = doc.original_name || doc.display_name;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : "Falha ao baixar documento.");
    } finally {
      setDownloadingId(null);
    }
  }

  return (
    <PageShell
      title="Orientações institucionais"
      subtitle="Carta orientadora, premissas, cronograma e materiais de apoio do ciclo orçamentário."
      icon={<BookOpen size={28} strokeWidth={1.75} aria-hidden="true" />}
      backRoute="home"
    >
      {loading ? (
        <LoadingActivityCard title="Carregando orientações…" variant="panel" />
      ) : null}

      {!loading && error ? (
        <StateBox variant="error" dismissible={false}>
          {error}
        </StateBox>
      ) : null}

      {!loading && !error && guidance ? (
        <div className="po-page-stack">
          {confirmed ? (
            <div data-testid="orientacoes-confirmed">
              <StateBox variant="success" dismissible={false}>
                Leitura confirmada com sucesso. Os módulos de elaboração serão liberados conforme
                seu escopo e o status do exercício.
              </StateBox>
            </div>
          ) : null}

          <SectionCard title="Mensagem da diretoria" hint="Comunicado oficial de abertura do ciclo.">
            <p className="po-prose">{guidance.board_message}</p>
          </SectionCard>

          <SectionCard title="Objetivo do exercício" hint="Resultado esperado do planejamento.">
            <div className="po-highlight-row">
              <Target size={20} aria-hidden="true" />
              <p className="po-prose">{guidance.objective}</p>
            </div>
          </SectionCard>

          <SectionCard title="Premissas" hint="Pressupostos macroeconômicos e operacionais.">
            <div className="po-card-grid">
              {guidance.premises.map((premise) => (
                <article key={premise.id ?? premise.name} className="po-premise-card">
                  <h3>{premise.name}</h3>
                  <p>{premise.value_text ?? premise.value_numeric ?? premise.description ?? "—"}{premise.unit_label ? ` ${premise.unit_label}` : ""}</p>
                </article>
              ))}
            </div>
          </SectionCard>

          <SectionCard title="Orientações gerais" hint="Diretrizes para elaboração por área.">
            <div className="po-highlight-row">
              <Lightbulb size={20} aria-hidden="true" />
              <div className="po-prose po-prose--pre">{guidance.general_guidance}</div>
            </div>
          </SectionCard>

          <SectionCard title="Cronograma" hint="Marcos institucionais do ciclo.">
            <ol className="po-timeline">
              {guidance.schedule.map((item, index) => (
                <li key={item.id ?? item.title} className="po-timeline__item">
                  <span className="po-timeline__marker" aria-hidden="true">
                    {index + 1}
                  </span>
                  <div className="po-timeline__body">
                    <div className="po-timeline__head">
                      <strong>{item.title}</strong>
                      <span className="po-timeline__date">
                        <CalendarDays size={14} aria-hidden="true" />
                        {formatDate(item.starts_on)}
                      </span>
                    </div>
                    {item.description ? <p className="po-muted">{item.description}</p> : null}
                  </div>
                </li>
              ))}
            </ol>
          </SectionCard>

          <SectionCard title="Documentos de apoio" hint="Materiais complementares para download.">
            {documents.length === 0 ? (
              <p className="po-muted">Nenhum documento anexado à versão publicada.</p>
            ) : (
              <ul className="po-doc-list">
                {documents.map((doc) => (
                  <li key={doc.id}>
                    <div className="po-doc-list__meta">
                      <FileText size={18} aria-hidden="true" />
                      <div>
                        <strong>{doc.display_name}</strong>
                        <span className="po-muted">
                          {doc.original_name} · {formatBytes(doc.size_bytes)}
                        </span>
                      </div>
                    </div>
                    <button
                      type="button"
                      className="po-btn po-btn--secondary"
                      disabled={downloadingId === doc.id}
                      onClick={() => void handleDownload(doc)}
                    >
                      <Download size={16} aria-hidden="true" />
                      {downloadingId === doc.id ? "Baixando…" : "Baixar"}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>

          {!confirmed ? (
            <SectionCard title="Confirmação de leitura" hint="Obrigatória para liberar os módulos.">
              <label className="po-declaration" htmlFor="po-declaration-checkbox">
                <input
                  id="po-declaration-checkbox"
                  data-testid="orientacoes-declaration-checkbox"
                  type="checkbox"
                  checked={declared}
                  onChange={(event) => setDeclared(event.target.checked)}
                />
                <span>{DECLARATION_TEXT}</span>
              </label>

              {submitError ? (
                <StateBox variant="error" dismissible={false}>
                  {submitError}
                </StateBox>
              ) : null}

              <div className="po-form-actions">
                <button
                  type="button"
                  className="po-btn po-btn--primary"
                  data-testid="orientacoes-confirm-button"
                  disabled={!declared || submitting}
                  onClick={() => void handleConfirm()}
                >
                  <CheckCircle2 size={16} aria-hidden="true" />
                  {submitting ? "Registrando…" : "Confirmar leitura"}
                </button>
              </div>
            </SectionCard>
          ) : null}
        </div>
      ) : null}
    </PageShell>
  );
}

export { DECLARATION_TEXT };
