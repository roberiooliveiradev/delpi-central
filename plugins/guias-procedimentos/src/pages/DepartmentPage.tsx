import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";

import {
  getPublicDepartment,
  type ApiDepartmentDetail,
} from "../api/guiasProcedimentosApi";
import { HttpRequestError } from "../api/httpClient";
import { DepartmentIcon } from "../components/DepartmentIcon";
import { GuideCard } from "../components/GuideCard";
import { GuidesListSection } from "../components/GuidesListSection";
import { ModuleHeader } from "../components/ModuleHeader";
import {
  BACK_TO_DEPARTMENTS_LABEL,
  formatProcedureCount,
} from "../content/catalog";
import {
  fallbackDepartment,
  shouldUseCatalogFallback,
  warnFallback,
} from "../data/catalogFallback";
import type { GuideSummary } from "../types/guide";
import { navigateGuiasProcedimentos } from "../utils/navigation";
import { GUIAS_PROCEDIMENTOS_ROUTES } from "../utils/route";

type DepartmentPageProps = {
  slug: string;
  standalone?: boolean;
};

function toGuideSummaries(detail: ApiDepartmentDetail): GuideSummary[] {
  return detail.procedures.map((procedure) => ({
    id: procedure.id,
    slug: procedure.slug,
    departmentId: detail.id,
    title: procedure.title,
    summary: procedure.summary,
    tags: [],
    responsibleArea: detail.name,
    updatedAtLabel: "",
    readingTimeMinutes: procedure.reading_time_minutes ?? 1,
    status: "published",
    departmentName: detail.name,
  }));
}

export function DepartmentPage({
  slug,
  standalone = false,
}: DepartmentPageProps) {
  const [detail, setDetail] = useState<ApiDepartmentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setNotFound(false);
    setError(null);

    getPublicDepartment(slug)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof HttpRequestError && err.status === 404) {
          setNotFound(true);
          setDetail(null);
          return;
        }
        if (shouldUseCatalogFallback(err)) {
          warnFallback(`getPublicDepartment:${slug}`, err);
          const local = fallbackDepartment(slug);
          if (local) {
            setDetail(local);
            return;
          }
          setNotFound(true);
          return;
        }
        if (err instanceof HttpRequestError && err.status === 403) {
          setError("Você não tem permissão para consultar este conteúdo.");
        } else {
          setError("Não foi possível carregar o departamento.");
        }
        setDetail(null);
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
        <div className="gp-shell">
          <ModuleHeader brandOnly showThemeToggle={standalone} />
          <p className="gp-intro">Carregando departamento…</p>
        </div>
      </div>
    );
  }

  if (notFound || (!detail && !error)) {
    return (
      <div className="dashboard-guias-procedimentos gp-page">
        <div className="gp-shell">
          <ModuleHeader brandOnly showThemeToggle={standalone} />
          <p className="gp-intro">Departamento não encontrado.</p>
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

  if (error || !detail) {
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

  const guides = toGuideSummaries(detail);
  const icon = detail.icon || "book-open";

  return (
    <div className="dashboard-guias-procedimentos gp-page">
      <div className="gp-shell">
        <ModuleHeader brandOnly showThemeToggle={standalone} />

        <nav className="gp-back gp-no-print-hide" aria-label="Navegação">
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
        </nav>

        <header className="gp-dept-page__header">
          <span className="gp-dept-page__circle" aria-hidden="true">
            <DepartmentIcon icon={icon} size={28} />
          </span>
          <div className="gp-dept-page__titles">
            <h1 className="gp-dept-page__title">{detail.name}</h1>
            <p className="gp-dept-page__intro">
              {detail.description ||
                `Consulte os procedimentos e orientações do setor de ${detail.name}.`}
            </p>
            <p className="gp-dept-page__count">
              {formatProcedureCount(detail.procedure_count)}
            </p>
          </div>
        </header>

        {guides.length > 0 ? (
          <GuidesListSection title="Procedimentos">
            {guides.map((guide) => (
              <GuideCard key={guide.id} guide={guide} showDepartment={false} />
            ))}
          </GuidesListSection>
        ) : (
          <p className="gp-intro">Nenhum procedimento disponível neste setor.</p>
        )}
      </div>
    </div>
  );
}
