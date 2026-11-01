/**
 * Histórico/auditoria do checklist mestre em página contextual
 * (UX-015, nível 4) — substitui o modal de eventos da Administração.
 * `closing/admin/events` lista o histórico do template inteiro;
 * `closing/admin/versions/{n}/events` recorta por versão via
 * `?version=` da BFF, sem duplicar consulta.
 *
 * Integridade: eventos vêm ordenados do backend e o ator é exibido
 * como `actor_subject` — o enriquecimento de identidade (nome/avatar)
 * depende do contrato decidido em UX-014; até lá o fallback honesto é
 * o identificador técnico. Nenhuma consulta direta ao Core é feita.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import {
  listChecklistTemplates,
  listTemplateEvents,
  type ChecklistTemplate,
  type TemplateAuditEvent,
} from "../../api/adminApi";
import { CfQueryErrorBanner } from "../../app/cfFeedbackUi";
import {
  CfEmptyState,
  CfPagePath,
  CfSectionCard,
  CfTimeline,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  navigatePluginPath,
  navigatePluginView,
} from "../../app/pluginNavigation";
import { checklistAdminVersionPath } from "../../app/pluginRoutes";
import {
  EVENT_LABELS,
  EVENT_TONES,
  toQueryError,
  type QueryError,
} from "./checklistAdminShared";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";

function eventDetail(event: TemplateAuditEvent): string {
  // `actor_subject` é o identificador técnico da trilha de auditoria
  // (UX-014 pendente de contrato de identidade) — rotulado como tal,
  // nunca apresentado como nome de usuário.
  const parts = [
    `v${event.version}`,
    `Ator (id): ${event.actor_subject}`,
  ];
  const extras = Object.entries(event.detail ?? {});
  for (const [key, value] of extras) {
    parts.push(
      `${key}=${
        typeof value === "string" ? value : JSON.stringify(value)
      }`,
    );
  }
  return parts.join(" · ");
}

export function ChecklistAdminEventsPage({
  basePath,
  version,
}: {
  basePath: string;
  /** Número da versão quando a rota é `versions/{n}/events`. */
  version?: number | null;
}) {
  const [nonce, setNonce] = useState(0);
  const [template, setTemplate] = useState<ChecklistTemplate | null>(
    null,
  );
  const [templateLoaded, setTemplateLoaded] = useState(false);
  const [events, setEvents] = useState<{
    key: string;
    items: TemplateAuditEvent[];
  } | null>(null);
  const [error, setError] = useState<QueryError | null>(null);

  const requestId = useRef(0);
  const eventsKey = template
    ? `${template.template_id}:${version ?? "all"}:${nonce}`
    : "";
  const currentEvents =
    events?.key === eventsKey ? events.items : null;
  const loading = !templateLoaded && !error;

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  const backToAdmin = useCallback(
    () => navigatePluginView("checklist_admin", { basePath }),
    [basePath],
  );
  const backToVersion = useCallback(
    () =>
      version !== null && version !== undefined
        ? navigatePluginPath(
            checklistAdminVersionPath(version, basePath),
          )
        : backToAdmin(),
    [version, basePath, backToAdmin],
  );

  useEffect(() => {
    const id = ++requestId.current;
    const controller = new AbortController();
    listChecklistTemplates({ signal: controller.signal })
      .then((items) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setTemplate(items[0] ?? null);
        setTemplateLoaded(true);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setError(
          toQueryError(err, "Falha ao listar templates de checklist."),
        );
      });
    return () => controller.abort();
  }, [nonce]);

  useEffect(() => {
    if (!template) return;
    const id = ++requestId.current;
    const controller = new AbortController();
    listTemplateEvents(template.template_id, version ?? undefined, {
      signal: controller.signal,
    })
      .then((items) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setEvents({ key: eventsKey, items });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setError(toQueryError(err, "Falha ao listar os eventos."));
      });
    return () => controller.abort();
  }, [template, version, eventsKey]);

  const adminCrumb = {
    id: "admin",
    label: "Administração",
    href: `${basePath}/closing/admin`,
    onNavigate: (event: { preventDefault: () => void }) => {
      event.preventDefault();
      backToAdmin();
    },
  };
  const versionCrumb =
    version !== null && version !== undefined
      ? {
          id: "version",
          label: `Versão v${version}`,
          href: checklistAdminVersionPath(version, basePath),
          onNavigate: (event: { preventDefault: () => void }) => {
            event.preventDefault();
            backToVersion();
          },
        }
      : null;

  const scoped = version !== null && version !== undefined;
  const title = scoped
    ? `Histórico — versão v${version}`
    : "Histórico do checklist";

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label={title}
    >
      <CfPagePath
        ariaLabel="Caminho da página"
        size="sm"
        back={
          scoped
            ? {
                label: `Versão v${version}`,
                href: checklistAdminVersionPath(version, basePath),
                onNavigate: (event: {
                  preventDefault: () => void;
                }) => {
                  event.preventDefault();
                  backToVersion();
                },
              }
            : {
                label: "Administração",
                href: `${basePath}/closing/admin`,
                onNavigate: (event: {
                  preventDefault: () => void;
                }) => {
                  event.preventDefault();
                  backToAdmin();
                },
              }
        }
        items={versionCrumb ? [adminCrumb, versionCrumb] : [adminCrumb]}
        current="Histórico"
      />

      <div className="cf-checklist-page__content">
        <div className="cf-lead-stack">
          <CfTitleWithHelp
            title={title}
            hint={CF_HELP.adminEvents.page}
          />
          {template ? (
            <p className="cf-validation-panel__doc-detail">
              {`${template.name} — ${
                scoped
                  ? `eventos registrados na versão v${version}.`
                  : "eventos de todas as versões, em ordem cronológica."
              }`}
            </p>
          ) : null}
        </div>

        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="o histórico de eventos"
            onRetry={reload}
          />
        ) : null}

        {loading ||
        (templateLoaded && template && !currentEvents && !error) ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Carregando eventos…"
          />
        ) : !error && templateLoaded && !template ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Nenhum template de checklist registrado."
          />
        ) : currentEvents ? (
          <CfSectionCard title="Eventos">
            {currentEvents.length === 0 ? (
              <CfEmptyState
                classNames={cfEmptyStateClassNames}
                defaultMessage="Nenhum evento registrado."
              />
            ) : (
              <CfTimeline
                items={currentEvents.map((event) => ({
                  id: event.event_id,
                  title:
                    EVENT_LABELS[event.event_type] ?? event.event_type,
                  occurredAt: event.created_at,
                  timeLabel: formatDateTime(event.created_at),
                  detail: eventDetail(event),
                  tone: EVENT_TONES[event.event_type] ?? "default",
                }))}
                emptyMessage="Nenhum evento registrado."
                aria-label={title}
              />
            )}
          </CfSectionCard>
        ) : null}
      </div>
    </section>
  );
}
