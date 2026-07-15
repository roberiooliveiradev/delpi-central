/**
 * Fallback temporário do catálogo TypeScript local.
 * Remover quando a API e o RBAC estiverem estáveis em todos os ambientes.
 */
import { HttpRequestError } from "../api/httpClient";
import type {
  ApiDepartmentDetail,
  ApiDepartmentListItem,
  ApiProcedureDetail,
} from "../api/guiasProcedimentosApi";
import {
  formatReadingTime,
  getDepartmentBySlug,
  getDepartmentSummaries,
  getGuideBySlug,
  getGuidesByDepartment,
  toGuideSummary,
} from "../content/catalog";

export function shouldUseCatalogFallback(error: unknown): boolean {
  if (!(error instanceof HttpRequestError)) {
    // rede / parse
    return true;
  }
  if (error.status === 401 || error.status === 403 || error.status === 404) {
    return false;
  }
  return error.status >= 500;
}

export function warnFallback(context: string, error: unknown): void {
  if (import.meta.env.DEV) {
    console.warn(`[guias-procedimentos] fallback catálogo local: ${context}`, error);
  }
}

export function fallbackDepartments(): ApiDepartmentListItem[] {
  return getDepartmentSummaries().map((department) => ({
    id: department.id,
    name: department.name,
    slug: department.slug,
    description: department.description ?? "",
    icon: department.icon,
    order_index: department.order,
    procedure_count: department.guideCount,
    active: true,
  }));
}

export function fallbackDepartment(slug: string): ApiDepartmentDetail | null {
  const department = getDepartmentBySlug(slug);
  if (!department) return null;
  const guides = getGuidesByDepartment(department.id).map(toGuideSummary);
  return {
    id: department.id,
    name: department.name,
    slug: department.slug,
    description: department.description ?? "",
    icon: department.icon,
    order_index: department.order,
    procedure_count: guides.length,
    active: true,
    procedures: guides.map((guide) => ({
      id: guide.id,
      title: guide.title,
      slug: guide.slug,
      summary: guide.summary,
      reading_time_minutes: guide.readingTimeMinutes,
      order_index: 1,
    })),
  };
}

/** Converte guia tipado local em HTML simples para fallback do detalhe. */
function guideToHtml(slug: string): string | null {
  const guide = getGuideBySlug(slug);
  if (!guide) return null;
  const sections = guide.sections
    .map((section) => {
      const items = section.items
        .map((item) =>
          item.emphasis
            ? `<li><strong>${escapeHtml(item.text)}</strong></li>`
            : `<li>${escapeHtml(item.text)}</li>`,
        )
        .join("");
      return `<h2>${escapeHtml(section.title)}</h2><ul>${items}</ul>`;
    })
    .join("");
  const checklist = guide.checklist
    .map((item) => `<li>${escapeHtml(item.label)}</li>`)
    .join("");
  return [
    `<p>${escapeHtml(guide.introduction)}</p>`,
    sections,
    `<h2>Checklist de conferência</h2><ul>${checklist}</ul>`,
    `<p>${escapeHtml(guide.footerNotice)}</p>`,
  ].join("");
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function fallbackProcedure(slug: string): ApiProcedureDetail | null {
  const guide = getGuideBySlug(slug);
  if (!guide) return null;
  const department = getDepartmentBySlug(
    // departmentId equals slug in V1 catalog
    guide.meta.departmentId,
  );
  const html = guideToHtml(slug);
  if (!html || !department) return null;
  return {
    id: guide.meta.id,
    title: guide.meta.title,
    slug: guide.meta.slug,
    summary: guide.meta.summary,
    content_html: html,
    reading_time_minutes: guide.meta.readingTimeMinutes,
    order_index: 1,
    published_at: null,
    updated_at: null,
    department: {
      id: department.id,
      name: department.name,
      slug: department.slug,
      icon: department.icon,
    },
  };
}

export function formatFallbackReadingLabel(minutes: number | null): string {
  if (minutes == null) return "";
  return formatReadingTime(minutes);
}
