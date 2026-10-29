import { useCallback, useEffect, useState } from "react";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringDetailCard,
  EngineeringDetailFieldGrid,
  EngineeringEmptyState,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringSectionCard,
  EngineeringStateBanner,
  EngineeringStatusBadge,
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

function detailFields(record: Nonconformity) {
  return [
    { label: "OV", value: record.sale_number ?? "—" },
    { label: "LMP", value: record.lmp_number ?? "—" },
    { label: "Cliente", value: record.customer_name ?? "—" },
    { label: "Data de ocorrência", value: formatNcDate(record.occurrence_date) },
    { label: "Registrado em", value: formatNcDateTime(record.registered_at) },
    { label: "Data de lançamento", value: formatNcDate(record.launch_date) },
    { label: "Última revisão", value: formatNcDate(record.last_revision_date) },
    { label: "Executado por", value: record.executed_by ?? "—" },
    { label: "Liberado por", value: record.released_by ?? "—" },
    { label: "Criado por", value: record.created_by ?? "—" },
    { label: "Atualizado por", value: record.updated_by ?? "—" },
  ];
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
            title="Produtos associados"
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
            {history && history.length ? (
              <ol className="engineering-nc-history">
                {history.map((event) => (
                  <li key={event.id} className="engineering-nc-history-item">
                    <header>
                      <EngineeringStatusBadge
                        label={
                          event.event_type === "created"
                            ? "Criação"
                            : "Atualização"
                        }
                        variant={
                          event.event_type === "created" ? "info" : "neutral"
                        }
                      />
                      <span className="engineering-nc-muted">
                        {formatNcDateTime(event.created_at)} —{" "}
                        {event.actor_name ?? event.actor_email ?? event.actor_user_id}
                      </span>
                    </header>
                    {(event.changes?.fields ?? []).length ? (
                      <ul>
                        {event.changes.fields!.map((change, idx) => (
                          <li key={idx}>
                            <strong>{change.label}</strong>:{" "}
                            {formatChangeValue(change.old)} →{" "}
                            {formatChangeValue(change.new)}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </li>
                ))}
              </ol>
            ) : (
              <p className="engineering-nc-muted">Sem eventos registrados.</p>
            )}
          </EngineeringSectionCard>
        </>
      ) : null}
    </main>
  );
}

function formatChangeValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.join(", ") || "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
