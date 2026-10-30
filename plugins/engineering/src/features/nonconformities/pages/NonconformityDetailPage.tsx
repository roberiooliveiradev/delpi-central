import { useCallback, useEffect, useState } from "react";

import type { TimelineItemModel } from "@delpi/plugin-ui/index";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringDetailCard,
  EngineeringDetailFieldGrid,
  EngineeringEmptyState,
  EngineeringInitialsAvatar,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringSectionCard,
  EngineeringStateBanner,
  EngineeringStatusBadge,
  EngineeringTimeline,
} from "../../../ui/engineeringUi";
import {
  deleteNonconformity,
  fetchNonconformity,
  fetchNonconformityContext,
  fetchNonconformityHistory,
} from "../api/nonconformityApi";
import {
  formatNcDate,
  formatNcDateTime,
  NC_HELP,
  NC_STATUS_LABELS,
  NC_STATUS_VARIANTS,
} from "../ncCopy";
import {
  ncHistoryActorLabel,
  ncHistoryChangeLines,
} from "../ncPresentation";
import { NC_PATHS, navigateNc } from "../nonconformityRoutes";
import type {
  NcContextPayload,
  NcHistoryEvent,
  Nonconformity,
} from "../types";

function errorMessage(error: unknown, fallback: string): string {
  if (error instanceof HomeApiError) return error.message;
  return fallback;
}

/** Identidade de pessoa — avatar oficial por iniciais + nome acessível.
 * Sem endpoint por-usuário de foto no MFE (Core expõe foto só via S2S
 * ou /me), iniciais são o fallback honesto e estável. */
function NcUserIdentity({ name }: { name: string | null }) {
  const label = name?.trim() || "—";
  if (label === "—") return <span className="engineering-nc-muted">—</span>;
  return (
    <span className="engineering-nc-user">
      <EngineeringInitialsAvatar name={label} size="sm" />
      <span>{label}</span>
    </span>
  );
}

function detailFields(record: Nonconformity) {
  return [
    { label: "OV", hint: NC_HELP.saleNumber, value: record.sale_number ?? "—" },
    { label: "LMP", hint: NC_HELP.lmpNumber, value: record.lmp_number ?? "—" },
    {
      label: "Cliente",
      hint: NC_HELP.customerName,
      value: record.customer_name ?? "—",
    },
    {
      label: "Data de ocorrência",
      hint: NC_HELP.occurrenceDate,
      value: formatNcDate(record.occurrence_date),
    },
    {
      label: "Registrado em",
      hint: NC_HELP.registeredAt,
      value: formatNcDateTime(record.registered_at),
    },
    {
      label: "Data de lançamento",
      hint: NC_HELP.launchDate,
      value: formatNcDate(record.launch_date),
    },
    {
      label: "Última revisão",
      hint: NC_HELP.lastRevisionDate,
      value: formatNcDate(record.last_revision_date),
    },
    {
      label: "Executado por",
      hint: NC_HELP.executedBy,
      value: <NcUserIdentity name={record.executed_by} />,
    },
    {
      label: "Liberado por",
      hint: NC_HELP.releasedBy,
      value: <NcUserIdentity name={record.released_by} />,
    },
    {
      label: "Criado por",
      hint: NC_HELP.createdBy,
      value: <NcUserIdentity name={record.created_by} />,
    },
    {
      label: "Atualizado por",
      hint: NC_HELP.updatedBy,
      value: <NcUserIdentity name={record.updated_by} />,
    },
  ];
}

/** Evento de auditoria → item da Timeline oficial do kit. */
function toTimelineItem(event: NcHistoryEvent): TimelineItemModel {
  const actorLabel = ncHistoryActorLabel(event);
  const changes = ncHistoryChangeLines(event);
  return {
    id: event.id,
    tone: event.event_type === "created" ? "success" : "info",
    title:
      event.event_type === "created" ? "Registro criado" : "Atualização",
    occurredAt: event.created_at,
    timeLabel: formatNcDateTime(event.created_at),
    meta: (
      <span
        className="engineering-nc-user"
        title={`${NC_HELP.historyActor} — ${actorLabel}`}
      >
        <EngineeringInitialsAvatar name={actorLabel} size="sm" />
        <span>{actorLabel}</span>
      </span>
    ),
    detail: changes.length ? (
      <ul className="engineering-nc-change-list">
        {changes.map((line, idx) => (
          <li key={idx}>{line}</li>
        ))}
      </ul>
    ) : (
      "Sem campos alterados registrados."
    ),
  };
}

export function NonconformityDetailPage({ recordId }: { recordId: string }) {
  const [record, setRecord] = useState<Nonconformity | null>(null);
  const [history, setHistory] = useState<NcHistoryEvent[] | null>(null);
  const [context, setContext] = useState<NcContextPayload | null>(null);
  const [contextStatus, setContextStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setNotFound(false);
    try {
      const recordResult = await fetchNonconformity(recordId);
      setRecord(recordResult);
      const [historyResult, contextResult] = await Promise.allSettled([
        fetchNonconformityHistory(recordId),
        fetchNonconformityContext(recordId),
      ]);
      setHistory(
        historyResult.status === "fulfilled" ? historyResult.value : [],
      );
      if (contextResult.status === "fulfilled") {
        setContext(contextResult.value);
        setContextStatus(null);
      } else {
        setContext(null);
        setContextStatus(
          errorMessage(contextResult.reason, "Contexto indisponível."),
        );
      }
    } catch (err) {
      if (err instanceof HomeApiError && err.status === 404) {
        setNotFound(true);
      } else {
        setError(errorMessage(err, "Não foi possível carregar a não conformidade."));
      }
      setRecord(null);
    } finally {
      setLoading(false);
    }
  }, [recordId]);

  useEffect(() => {
    void load();
  }, [load]);

  const onDelete = async () => {
    setDeleting(true);
    try {
      await deleteNonconformity(recordId);
      navigateNc(NC_PATHS.list);
    } catch (err) {
      setError(errorMessage(err, "Falha ao excluir a não conformidade."));
      setDeleting(false);
      setConfirmDelete(false);
    }
  };

  const timelineItems = (history ?? []).map(toTimelineItem);

  return (
    <main className="engineering-nonconformities">
      <EngineeringPagePath
        back={{
          label: "Não conformidades",
          href: NC_PATHS.list,
          onNavigate: (event) => {
            event.preventDefault();
            navigateNc(NC_PATHS.list);
          },
        }}
        items={[]}
        current={record ? `NC ${record.sale_number ?? record.id.slice(0, 8)}` : "Detalhe"}
      />

      <EngineeringPageHero
        eyebrow="Portal Engenharia • Não conformidades"
        title={
          record
            ? `Não conformidade ${record.sale_number ?? "sem OV"}`
            : "Não conformidade"
        }
        description="Detalhe oficial do registro, histórico de auditoria e contexto da proposta."
        badge={
          record ? (
            <EngineeringStatusBadge
              label={NC_STATUS_LABELS[record.status] ?? record.status}
              variant={NC_STATUS_VARIANTS[record.status] ?? "neutral"}
            />
          ) : undefined
        }
        actions={
          record ? (
            <>
              <EngineeringActionButton
                variant="primary"
                onClick={() => navigateNc(NC_PATHS.edit(record.id))}
              >
                Editar
              </EngineeringActionButton>
              {!confirmDelete ? (
                <EngineeringActionButton
                  variant="ghost"
                  onClick={() => setConfirmDelete(true)}
                >
                  Excluir
                </EngineeringActionButton>
              ) : (
                <>
                  <EngineeringActionButton
                    variant="primary"
                    onClick={() => void onDelete()}
                    disabled={deleting}
                  >
                    {deleting ? "Excluindo…" : "Confirmar exclusão"}
                  </EngineeringActionButton>
                  <EngineeringActionButton
                    variant="ghost"
                    onClick={() => setConfirmDelete(false)}
                    disabled={deleting}
                  >
                    Cancelar
                  </EngineeringActionButton>
                </>
              )}
            </>
          ) : undefined
        }
      />

      {loading ? (
        <EngineeringLoadingActivityCard
          title="Carregando não conformidade"
          description="Consultando o registro oficial."
        />
      ) : null}

      {notFound ? (
        <EngineeringEmptyState message="Não conformidade não encontrada — ela pode ter sido removida.">
          <EngineeringActionButton
            variant="primary"
            onClick={() => navigateNc(NC_PATHS.list)}
          >
            Voltar à listagem
          </EngineeringActionButton>
        </EngineeringEmptyState>
      ) : null}

      {error ? (
        <EngineeringStateBanner variant="error">
          {`Falha ao carregar — ${error} `}
          <EngineeringActionButton variant="ghost" onClick={() => void load()}>
            Tentar novamente
          </EngineeringActionButton>
        </EngineeringStateBanner>
      ) : null}

      {record ? (
        <>
          <EngineeringDetailCard title="Identificação">
            <EngineeringDetailFieldGrid fields={detailFields(record)} />
          </EngineeringDetailCard>

          <EngineeringSectionCard
            title="Produtos associados"
            hint={NC_HELP.productsSection}
            subtitle={`${record.products.length} item(ns)`}
          >
            {record.products.length ? (
              <ul className="engineering-nc-product-list">
                {record.products.map((product) => (
                  <li key={product.product_code}>
                    <strong>{product.product_code}</strong>
                    {product.product_description
                      ? ` — ${product.product_description}`
                      : ""}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="engineering-nc-muted">Nenhum produto associado.</p>
            )}
          </EngineeringSectionCard>

          <EngineeringSectionCard title="Problema e tratativa">
            <dl className="engineering-nc-text-block">
              <dt>Descrição do problema</dt>
              <dd>{record.defect_description ?? "—"}</dd>
              <dt>Ações corretivas</dt>
              <dd>{record.corrective_actions ?? "—"}</dd>
              <dt>Parecer técnico</dt>
              <dd>{record.technical_opinion ?? "—"}</dd>
            </dl>
          </EngineeringSectionCard>

          <EngineeringSectionCard
            title="Problemas identificados"
            hint={NC_HELP.problemTagsSection}
            subtitle={`${record.problem_tags.length} tag(s)`}
          >
            {record.problem_tags.length ? (
              <ul className="engineering-nc-tag-list">
                {record.problem_tags.map((tag) => (
                  <li key={tag}>
                    <EngineeringStatusBadge label={tag} variant="neutral" />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="engineering-nc-muted">Nenhuma tag associada.</p>
            )}
          </EngineeringSectionCard>

          <EngineeringSectionCard
            title="Contexto da proposta e produtos"
            hint={NC_HELP.context}
            subtitle="Fatos oficiais TOTVS via Engineering API — disponibilidade por fonte."
          >
            {contextStatus ? (
              <EngineeringStateBanner variant="default">
                {`Contexto indisponível — ${contextStatus}`}
              </EngineeringStateBanner>
            ) : context ? (
              <div className="engineering-nc-context">
                <p className="engineering-nc-muted">
                  OV oficial:{" "}
                  {context.ov_status === "available"
                    ? "disponível"
                    : context.ov_status === "not_linked"
                      ? "sem OV vinculada"
                      : context.ov_status}
                </p>
                {context.product_contexts.length ? (
                  <ul className="engineering-nc-product-list">
                    {context.product_contexts.map((item) => (
                      <li key={item.product_code}>
                        <strong>{item.product_code}</strong>
                        {item.product_description
                          ? ` — ${item.product_description}`
                          : ""}{" "}
                        <span className="engineering-nc-muted">
                          (estrutura: {item.structure_status})
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="engineering-nc-muted">
                    Sem produtos para enriquecimento.
                  </p>
                )}
              </div>
            ) : null}
          </EngineeringSectionCard>

          <EngineeringSectionCard
            title="Histórico"
            hint={NC_HELP.history}
            subtitle="Eventos de auditoria append-only — mais recentes primeiro."
          >
            <EngineeringTimeline
              items={timelineItems}
              loading={history === null}
              loadingMessage="Carregando histórico…"
              emptyMessage="Sem eventos registrados."
              aria-label="Histórico da não conformidade"
            />
          </EngineeringSectionCard>
        </>
      ) : null}
    </main>
  );
}

