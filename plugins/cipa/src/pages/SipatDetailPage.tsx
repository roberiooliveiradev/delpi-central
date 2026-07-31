import { useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  BackLink,
  StatusBadge,
} from "@delpi/plugin-ui/index";
import {
  ClipboardList,
  Copy,
  FileSpreadsheet,
  Link2,
  Lock,
  MessageSquareText,
  Pencil,
  QrCode,
  RefreshCw,
  Shield,
} from "lucide-react";

import {
  closeSipatSurvey,
  cloneSipatSurvey,
  downloadSipatExcel,
  downloadSipatQr,
  getSipatSummary,
  getSipatSurvey,
  type SipatSummary,
  type SipatSurveyDetail,
} from "../api/cipaApi";
import {
  SIPAT_QUESTION_TYPE_LABELS,
  SIPAT_STATUS_LABELS,
  UNIT_LABELS,
} from "../constants/labels";
import { navigateCipa } from "../hooks/useCipaRouterPath";
import { canUnit, type CipaAccess, type CipaUnitCode } from "../security/cipaAccess";
import {
  CipaFormActions,
  CipaPageHeader,
  CipaPageNotices,
  CipaStateBanner,
  CipaStateBox,
} from "../ui/cipaUi";
import { cipaStatusBadgeClassNames } from "../ui/cipaUiContracts";
import { SipatResultsSection } from "./SipatResultsSection";

type Props = {
  unitCode: CipaUnitCode;
  surveyId: string;
  access: CipaAccess | null;
};

function statusVariant(status: string): "neutral" | "info" | "success" | "warning" | "danger" {
  if (status === "published") return "success";
  if (status === "closed") return "neutral";
  if (status === "draft") return "warning";
  return "info";
}

export function SipatDetailPage({ unitCode, surveyId, access }: Props) {
  const [detail, setDetail] = useState<SipatSurveyDetail | null>(null);
  const [summary, setSummary] = useState<SipatSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const canManage = canUnit(access, unitCode, "sipat_manage");

  const load = () => {
    const controller = new AbortController();
    setLoading(true);
    Promise.all([
      getSipatSurvey(surveyId, controller.signal),
      getSipatSummary(surveyId, controller.signal).catch(() => null),
    ])
      .then(([surveyDetail, surveySummary]) => {
        setDetail(surveyDetail);
        setSummary(surveySummary);
        setError(null);
      })
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setError(err instanceof Error ? err.message : "Erro ao carregar pesquisa.");
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  };

  useEffect(() => load(), [surveyId]);

  const copyLink = async () => {
    const url = detail?.survey.public_url;
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      setSuccess("Link público copiado.");
    } catch {
      setError("Não foi possível copiar o link.");
    }
  };

  const downloadQr = async () => {
    setBusy(true);
    setError(null);
    try {
      const blob = await downloadSipatQr(surveyId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = detail?.survey.qr_filename || `sipat-${surveyId}.png`;
      anchor.click();
      URL.revokeObjectURL(url);
      setSuccess("QR Code baixado.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao baixar QR.");
    } finally {
      setBusy(false);
    }
  };

  const closeSurvey = async () => {
    setBusy(true);
    try {
      const next = await closeSipatSurvey(surveyId);
      setDetail(next);
      setSuccess("Pesquisa encerrada.");
      void load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao encerrar.");
    } finally {
      setBusy(false);
    }
  };

  const cloneSurvey = async () => {
    setBusy(true);
    setError(null);
    try {
      const next = await cloneSipatSurvey(surveyId);
      navigateCipa(`/apps/cipa/filial-${unitCode}/sipat/${next.survey.id}/edit`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao clonar pesquisa.");
      setBusy(false);
    }
  };

  const exportExcel = async () => {
    setBusy(true);
    setError(null);
    try {
      const blob = await downloadSipatExcel(surveyId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      const safeTitle = (detail?.survey.title || "sipat")
        .replace(/[^\w\s-]/g, "")
        .trim()
        .replace(/\s+/g, "-")
        .slice(0, 40)
        .toLowerCase();
      anchor.download = `sipat-${safeTitle || "resultados"}-resultados.xlsx`;
      anchor.click();
      URL.revokeObjectURL(url);
      setSuccess("Planilha Excel baixada.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao exportar Excel.");
    } finally {
      setBusy(false);
    }
  };

  const responseCount = summary?.response_count ?? detail?.survey.response_count ?? 0;
  const questionCount = detail?.questions.length ?? 0;

  const participationHint = useMemo(() => {
    if (!summary || responseCount === 0) return "Aguardando primeiras respostas anônimas.";
    return `${responseCount} participação${responseCount === 1 ? "" : "ões"} registrada${responseCount === 1 ? "" : "s"}.`;
  }, [summary, responseCount]);

  if (loading) {
    return <CipaStateBox>Carregando pesquisa SIPAT…</CipaStateBox>;
  }
  if (!detail) {
    return (
      <CipaStateBanner variant="error">
        {error || "Pesquisa não encontrada."}
      </CipaStateBanner>
    );
  }

  const survey = detail.survey;

  return (
    <div className="cipa-page-stack cipa-sipat">
      <CipaPageHeader
        nav={
          <BackLink
            variant="prominent"
            onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/sipat`)}
          >
            SIPAT
          </BackLink>
        }
        title={survey.title}
        subtitle={`${UNIT_LABELS[unitCode]} · pesquisa anônima`}
        actions={
          <>
            <ActionButton variant="ghost" onClick={() => void load()}>
              <RefreshCw size={16} /> Atualizar
            </ActionButton>
            {canManage ? (
              <ActionButton disabled={busy} onClick={() => void cloneSurvey()}>
                <Copy size={16} /> Clonar
              </ActionButton>
            ) : null}
            {canManage && survey.status === "draft" ? (
              <ActionButton
                onClick={() =>
                  navigateCipa(`/apps/cipa/filial-${unitCode}/sipat/${surveyId}/edit`)
                }
              >
                <Pencil size={16} /> Editar
              </ActionButton>
            ) : null}
          </>
        }
      />

      <CipaPageNotices>
        {error ? <CipaStateBanner variant="error">{error}</CipaStateBanner> : null}
        {success ? <CipaStateBanner variant="success">{success}</CipaStateBanner> : null}
      </CipaPageNotices>

      <section className="cipa-sipat-hero" aria-label="Identidade SIPAT">
        <div className="cipa-sipat-hero__brand">
          <span className="cipa-sipat-hero__mark">SIPAT</span>
          <div>
            <p className="cipa-sipat-hero__eyebrow">CIPA · {UNIT_LABELS[unitCode]}</p>
            <h2 className="cipa-sipat-hero__title">{survey.title}</h2>
            {survey.description ? (
              <p className="cipa-sipat-hero__lead">{survey.description}</p>
            ) : null}
          </div>
        </div>
        <div className="cipa-sipat-hero__meta">
          <StatusBadge
            classNames={cipaStatusBadgeClassNames}
            label={SIPAT_STATUS_LABELS[survey.status] || survey.status}
            variant={statusVariant(survey.status)}
          />
          <p className="cipa-sipat-hero__privacy">
            <Shield size={14} aria-hidden /> Respostas anônimas — sem nome ou matrícula
          </p>
        </div>
      </section>

      <section className="cipa-sipat-kpis" aria-label="Indicadores">
        <article className="cipa-sipat-kpi">
          <span className="cipa-sipat-kpi__label">Respostas</span>
          <strong className="cipa-sipat-kpi__value">{responseCount}</strong>
          <span className="cipa-sipat-kpi__hint">{participationHint}</span>
        </article>
        <article className="cipa-sipat-kpi">
          <span className="cipa-sipat-kpi__label">Perguntas</span>
          <strong className="cipa-sipat-kpi__value">{questionCount}</strong>
          <span className="cipa-sipat-kpi__hint">Instrumento da pesquisa</span>
        </article>
        <article className="cipa-sipat-kpi">
          <span className="cipa-sipat-kpi__label">Status</span>
          <strong className="cipa-sipat-kpi__value cipa-sipat-kpi__value--text">
            {SIPAT_STATUS_LABELS[survey.status] || survey.status}
          </strong>
          <span className="cipa-sipat-kpi__hint">
            {survey.status === "published"
              ? "Aberta para coleta"
              : survey.status === "closed"
                ? "Coleta encerrada"
                : "Ainda não publicada"}
          </span>
        </article>
      </section>

      <section className="cipa-sipat-panel">
        <header className="cipa-sipat-panel__head">
          <div>
            <h3>Publicação e acesso</h3>
            <p>Compartilhe o link ou o QR com os participantes.</p>
          </div>
          <Link2 size={18} aria-hidden />
        </header>

        {survey.public_url ? (
          <div className="cipa-sipat-share">
            <div className="cipa-sipat-share__link">
              <span className="cipa-sipat-share__label">Link público</span>
              <code>{survey.public_url}</code>
            </div>
            <CipaFormActions>
              <ActionButton onClick={() => void copyLink()}>
                <Copy size={16} /> Copiar link
              </ActionButton>
              <ActionButton disabled={busy} onClick={() => void downloadQr()}>
                <QrCode size={16} /> Baixar QR
              </ActionButton>
              {canManage && survey.status === "published" ? (
                <ActionButton disabled={busy} onClick={() => void closeSurvey()}>
                  <Lock size={16} /> Encerrar coleta
                </ActionButton>
              ) : null}
            </CipaFormActions>
          </div>
        ) : (
          <p className="cipa-sipat-empty-note">
            Publique a pesquisa no wizard para gerar link público e QR Code.
          </p>
        )}
      </section>

      <details className="cipa-sipat-panel cipa-sipat-instrument-panel">
        <summary className="cipa-sipat-instrument-panel__summary">
          <span className="cipa-sipat-instrument-panel__title">
            <ClipboardList size={16} aria-hidden />
            Instrumento
          </span>
          <span className="cipa-sipat-instrument-panel__meta">
            {detail.questions.length} pergunta{detail.questions.length === 1 ? "" : "s"}
          </span>
        </summary>
        <ol className="cipa-sipat-instrument">
          {detail.questions.map((q, index) => (
            <li key={q.id}>
              <span className="cipa-sipat-instrument__n">{index + 1}</span>
              <p className="cipa-sipat-instrument__label">{q.label}</p>
              <span className="cipa-sipat-instrument__type">
                {SIPAT_QUESTION_TYPE_LABELS[q.question_type] || q.question_type}
                {q.is_required ? " · obr." : ""}
              </span>
            </li>
          ))}
        </ol>
      </details>

      <section className="cipa-sipat-panel cipa-sipat-panel--results">
        <header className="cipa-sipat-panel__head">
          <div>
            <h3>Resultados</h3>
            <p>Gráficos de distribuição e comentários abertos.</p>
          </div>
          <div className="cipa-sipat-panel__head-actions">
            <ActionButton disabled={busy} onClick={() => void exportExcel()}>
              <FileSpreadsheet size={16} /> Exportar Excel
            </ActionButton>
            <MessageSquareText size={18} aria-hidden />
          </div>
        </header>

        {!summary ? (
          <div className="cipa-sipat-results-empty">
            <p>Não foi possível carregar o resumo.</p>
            <span>Atualize a página e tente novamente.</span>
          </div>
        ) : (
          <SipatResultsSection
            questions={summary.questions}
            responseCount={responseCount}
          />
        )}
      </section>
    </div>
  );
}
