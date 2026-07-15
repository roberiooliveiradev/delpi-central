import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";

import {
  getPublicProcedure,
  type ApiProcedureDetail,
} from "../api/guiasProcedimentosApi";
import { HttpRequestError } from "../api/httpClient";
import { GuideArticleAttachments } from "../components/GuideArticleAttachments";
import { GuideMetaBar } from "../components/GuideMetaBar";
import { ModuleHeader } from "../components/ModuleHeader";
import { SanitizedArticleContent } from "../components/SanitizedArticleContent";
import { BACK_TO_DEPARTMENTS_LABEL } from "../content/catalog";
import {
  fallbackProcedure,
  shouldUseCatalogFallback,
  warnFallback,
} from "../data/catalogFallback";
import type { GuideMeta } from "../types/guide";
import { navigateGuiasProcedimentos } from "../utils/navigation";
import { GUIAS_PROCEDIMENTOS_ROUTES } from "../utils/route";

type GuideDetailPageProps = {
  slug: string;
  standalone?: boolean;
};

function formatDateLabel(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("pt-BR");
}

function toMeta(procedure: ApiProcedureDetail): GuideMeta {
  return {
    id: procedure.id,
    slug: procedure.slug,
    departmentId: procedure.department.id,
    title: procedure.title,
    summary: procedure.summary,
    tags: [],
    responsibleArea: procedure.department.name,
    updatedAtLabel: formatDateLabel(
      procedure.updated_at ?? procedure.published_at,
    ),
    readingTimeMinutes: procedure.reading_time_minutes ?? 1,
    status: "published",
  };
}

export function GuideDetailPage({
  slug,
  standalone = false,
}: GuideDetailPageProps) {
  const [procedure, setProcedure] = useState<ApiProcedureDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setNotFound(false);
    setError(null);

    getPublicProcedure(slug)
      .then((data) => {
        if (!cancelled) setProcedure(data);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof HttpRequestError && err.status === 404) {
          setNotFound(true);
          setProcedure(null);
          return;
        }
        if (shouldUseCatalogFallback(err)) {
          warnFallback(`getPublicProcedure:${slug}`, err);
          const local = fallbackProcedure(slug);
          if (local) {
            setProcedure(local);
            return;
          }
          setNotFound(true);
          return;
        }
        if (err instanceof HttpRequestError && err.status === 403) {
          setError("Você não tem permissão para consultar este conteúdo.");
        } else {
          setError("Não foi possível carregar o procedimento.");
        }
        setProcedure(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (loading) {
    return (
      <div className="dashboard-guias-procedimentos gp-page">
        <div className="gp-shell gp-shell--article">
          <ModuleHeader brandOnly showThemeToggle={standalone} />
          <p className="gp-intro">Carregando procedimento…</p>
        </div>
      </div>
    );
  }

  if (notFound || (!procedure && !error)) {
    return (
      <div className="dashboard-guias-procedimentos gp-page">
        <div className="gp-shell">
          <ModuleHeader brandOnly showThemeToggle={standalone} />
          <p className="gp-intro">Guia não encontrado.</p>
          <button
            type="button"
            className="gp-btn gp-btn--ghost gp-no-print-hide"
            onClick={() =>
              navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.home)
            }
          >
            <ArrowLeft size={16} strokeWidth={2} aria-hidden="true" />
            {BACK_TO_DEPARTMENTS_LABEL}
          </button>
        </div>
      </div>
    );
  }

  if (error || !procedure) {
    return (
      <div className="dashboard-guias-procedimentos gp-page">
        <div className="gp-shell">
          <ModuleHeader brandOnly showThemeToggle={standalone} />
          <p className="gp-feedback gp-feedback--error">{error}</p>
          <button
            type="button"
            className="gp-btn gp-btn--ghost"
            onClick={() =>
              navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.home)
            }
          >
            <ArrowLeft size={16} strokeWidth={2} aria-hidden="true" />
            {BACK_TO_DEPARTMENTS_LABEL}
          </button>
        </div>
      </div>
    );
  }

  const backHref = GUIAS_PROCEDIMENTOS_ROUTES.department(
    procedure.department.slug,
  );
  const backLabel = `Voltar para ${procedure.department.name}`;
  const meta = toMeta(procedure);

  return (
    <div className="dashboard-guias-procedimentos gp-page gp-page--detail">
      <div className="gp-shell gp-shell--article">
        <ModuleHeader brandOnly showThemeToggle={standalone} />

        <nav className="gp-back gp-no-print-hide" aria-label="Navegação">
          <button
            type="button"
            className="gp-btn gp-btn--ghost"
            onClick={() => navigateGuiasProcedimentos(backHref)}
          >
            <ArrowLeft size={16} strokeWidth={2} aria-hidden="true" />
            {backLabel}
          </button>
        </nav>

        <article className="gp-article">
          <p className="gp-article__category">{procedure.department.name}</p>
          <h1 className="gp-article__title">{procedure.title}</h1>
          <p className="gp-article__intro">{procedure.summary}</p>

          <GuideMetaBar meta={meta} />

          <div className="gp-article__body">
            <SanitizedArticleContent html={procedure.content_html} />
          </div>

          <GuideArticleAttachments procedureId={procedure.id} />
        </article>
      </div>
    </div>
  );
}
