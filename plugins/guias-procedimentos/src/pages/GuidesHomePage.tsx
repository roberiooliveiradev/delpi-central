import { useEffect, useState } from "react";
import { Settings2 } from "lucide-react";

import {
  getPublicDepartment,
  listPublicDepartments,
  type ApiDepartmentListItem,
} from "../api/guiasProcedimentosApi";
import { HttpRequestError } from "../api/httpClient";
import { DepartmentsGrid } from "../components/DepartmentsGrid";
import { GuideSearchEmpty } from "../components/GuideSearchEmpty";
import { GuideSearchField } from "../components/GuideSearchField";
import { GuideCard } from "../components/GuideCard";
import { GuidesListSection } from "../components/GuidesListSection";
import { ModuleHeader } from "../components/ModuleHeader";
import {
  MODULE_INTRO,
  SEARCH_RESULTS_TITLE,
  formatProcedureCount,
} from "../content/catalog";
import {
  fallbackDepartments,
  shouldUseCatalogFallback,
  warnFallback,
} from "../data/catalogFallback";
import { useGuiasPermissions } from "../hooks/useGuiasPermissions";
import type { DepartmentSummary, GuideSummary } from "../types/guide";
import { navigateGuiasProcedimentos } from "../utils/navigation";
import { GUIAS_PROCEDIMENTOS_ROUTES } from "../utils/route";

type GuidesHomePageProps = {
  standalone?: boolean;
};

function toSummaries(items: ApiDepartmentListItem[]): DepartmentSummary[] {
  return items.map((item) => ({
    id: item.id,
    name: item.name,
    slug: item.slug,
    icon: item.icon || "book-open",
    description: item.description,
    order: item.order_index,
    guideCount: item.procedure_count,
  }));
}

export function GuidesHomePage({ standalone = false }: GuidesHomePageProps) {
  const { canManage, loading: permsLoading } = useGuiasPermissions(true);
  const [departments, setDepartments] = useState<DepartmentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<GuideSummary[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listPublicDepartments()
      .then((data) => {
        if (!cancelled) {
          setDepartments(toSummaries(data));
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (shouldUseCatalogFallback(err)) {
          warnFallback("listPublicDepartments", err);
          setDepartments(toSummaries(fallbackDepartments()));
          setError(null);
          return;
        }
        if (err instanceof HttpRequestError && err.status === 403) {
          setError("Você não tem permissão para consultar este conteúdo.");
        } else {
          setError("Não foi possível carregar os departamentos.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const term = query.trim().toLowerCase();
    if (!term) {
      setSearchResults([]);
      setSearching(false);
      return;
    }

    let cancelled = false;
    setSearching(true);

    // Busca client-side sobre departamentos/API: carrega procedimentos por dept. publicados
    // (API de search ainda não existe — usa detalhe dos departamentos já carregados)
    Promise.all(
      departments.map(async (dept) => {
        try {
          const detail = await getPublicDepartment(dept.slug);
          return detail.procedures
            .filter(
              (p) =>
                p.title.toLowerCase().includes(term) ||
                p.summary.toLowerCase().includes(term) ||
                p.slug.toLowerCase().includes(term),
            )
            .map((p) => ({
              id: p.id,
              title: p.title,
              slug: p.slug,
              summary: p.summary,
              readingTimeMinutes: p.reading_time_minutes ?? 1,
              departmentName: detail.name,
              departmentId: detail.id,
              tags: [] as string[],
              responsibleArea: detail.name,
              updatedAtLabel: "",
              status: "published" as const,
            }));
        } catch {
          return [];
        }
      }),
    )
      .then((chunks) => {
        if (!cancelled) setSearchResults(chunks.flat());
      })
      .finally(() => {
        if (!cancelled) setSearching(false);
      });

    return () => {
      cancelled = true;
    };
  }, [query, departments]);

  const isSearching = query.trim().length > 0;

  return (
    <div className="dashboard-guias-procedimentos gp-page">
      <div className="gp-shell">
        <ModuleHeader
          showThemeToggle={standalone}
          actions={
            !permsLoading && canManage ? (
              <button
                type="button"
                className="gp-btn gp-btn--ghost gp-btn--compact"
                onClick={() =>
                  navigateGuiasProcedimentos(GUIAS_PROCEDIMENTOS_ROUTES.admin)
                }
              >
                <Settings2 size={16} strokeWidth={2} aria-hidden="true" />
                Administrar conteúdo
              </button>
            ) : null
          }
        />
        <p className="gp-intro">{MODULE_INTRO}</p>
        <GuideSearchField value={query} onChange={setQuery} />

        {loading ? <p className="gp-intro">Carregando departamentos…</p> : null}
        {error ? <p className="gp-feedback gp-feedback--error">{error}</p> : null}

        {isSearching ? (
          searching ? (
            <p className="gp-intro">Buscando…</p>
          ) : searchResults.length > 0 ? (
            <GuidesListSection title={SEARCH_RESULTS_TITLE}>
              {searchResults.map((guide) => (
                <GuideCard key={guide.id} guide={guide} showDepartment />
              ))}
            </GuidesListSection>
          ) : (
            <GuideSearchEmpty onClear={() => setQuery("")} />
          )
        ) : !loading && !error ? (
          departments.length > 0 ? (
            <DepartmentsGrid departments={departments} />
          ) : (
            <p className="gp-intro">
              Nenhum departamento publicado no momento.{" "}
              {formatProcedureCount(0)}.
            </p>
          )
        ) : null}
      </div>
    </div>
  );
}
