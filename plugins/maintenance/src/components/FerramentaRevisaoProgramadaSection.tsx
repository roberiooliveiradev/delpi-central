import { useCallback, useEffect, useState } from "react";
import { CalendarClock, ChevronDown } from "lucide-react";

import { CONFIG_TOOLTIPS } from "../content/configTooltips";
import {
  createRevisaoProgramada,
  deleteRevisaoProgramada,
  fetchRevisaoProgramadaAlertas,
  fetchRevisaoProgramadaRealizacoes,
  fetchRevisoesProgramadas,
  registrarRevisaoProgramada,
  updateRevisaoProgramada,
  type RevisaoProgramadaAlerta,
  type RevisaoProgramadaItem,
  type RevisaoProgramadaRealizacao,
} from "../data/api/maintenanceApi";
import { FieldLabel, HelpTooltip, PendingChangeBadge, StateBox, StatusBadge } from "./data";
import { fromDateInputValue, toDateInputValue } from "../utils/datetimeLocal";

type FerramentaRevisaoProgramadaSectionProps = {
  filial: string;
  codigoFerramenta: string;
  canManage: boolean;
  reloadKey?: number;
  getAccessToken?: () => string | undefined;
  onFeedback?: (message: { type: "success" | "error"; text: string }) => void;
};

type RevisaoDraft = {
  intervalo_meses: number;
  observacao: string;
  data_referencia: string;
};

const DEFAULT_DRAFT: RevisaoDraft = {
  intervalo_meses: 3,
  observacao: "",
  data_referencia: "",
};

const REALIZACOES_LIMIT = 8;

function toDraft(item: RevisaoProgramadaItem): RevisaoDraft {
  return {
    intervalo_meses: item.intervalo_meses,
    observacao: item.observacao ?? "",
    data_referencia: item.data_ultima_revisao ? toDateInputValue(item.data_ultima_revisao) : "",
  };
}

function referenceInputValue(item: RevisaoProgramadaItem): string {
  return item.data_ultima_revisao ? toDateInputValue(item.data_ultima_revisao) : "";
}

function isDirty(item: RevisaoProgramadaItem, draft: RevisaoDraft): boolean {
  return (
    draft.intervalo_meses !== item.intervalo_meses ||
    draft.observacao.trim() !== (item.observacao ?? "").trim() ||
    draft.data_referencia !== referenceInputValue(item)
  );
}

function formatDateTime(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("pt-BR");
}

function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("pt-BR");
}

export function FerramentaRevisaoProgramadaSection({
  filial,
  codigoFerramenta,
  canManage,
  reloadKey = 0,
  getAccessToken,
  onFeedback,
}: FerramentaRevisaoProgramadaSectionProps) {
  const [loading, setLoading] = useState(false);
  const [schedule, setSchedule] = useState<RevisaoProgramadaItem | null>(null);
  const [alerta, setAlerta] = useState<RevisaoProgramadaAlerta | null>(null);
  const [realizacoes, setRealizacoes] = useState<RevisaoProgramadaRealizacao[]>([]);
  const [draft, setDraft] = useState<RevisaoDraft>(DEFAULT_DRAFT);
  const [createDraft, setCreateDraft] = useState<RevisaoDraft>(DEFAULT_DRAFT);
  const [feitoDate, setFeitoDate] = useState(() => toDateInputValue(new Date()));
  const [formExpanded, setFormExpanded] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [programacao, alertas, historico] = await Promise.all([
        fetchRevisoesProgramadas(
          filial,
          { page: 1, pageSize: 1 },
          { codigo_ferramenta: codigoFerramenta },
          getAccessToken,
        ),
        fetchRevisaoProgramadaAlertas(
          filial,
          { page: 1, pageSize: 1 },
          { ferramenta: codigoFerramenta },
          getAccessToken,
        ),
        fetchRevisaoProgramadaRealizacoes(
          filial,
          codigoFerramenta,
          { page: 1, pageSize: REALIZACOES_LIMIT, sortKey: "data", sortDirection: "desc" },
          getAccessToken,
        ),
      ]);

      const item = programacao.items?.[0] ?? null;
      setSchedule(item);
      setDraft(item ? toDraft(item) : DEFAULT_DRAFT);
      setAlerta(alertas.items?.[0] ?? null);
      setRealizacoes(historico.items ?? []);
    } catch (err) {
      onFeedback?.({
        type: "error",
        text: err instanceof Error ? err.message : "Falha ao carregar revisão programada.",
      });
      setSchedule(null);
      setAlerta(null);
      setRealizacoes([]);
    } finally {
      setLoading(false);
    }
  }, [codigoFerramenta, filial, getAccessToken, onFeedback]);

  useEffect(() => {
    void load();
  }, [load, reloadKey]);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!canManage) return;
    setSaving(true);
    try {
      await createRevisaoProgramada(
        {
          filial,
          codigo_ferramenta: codigoFerramenta,
          intervalo_meses: createDraft.intervalo_meses,
          observacao: createDraft.observacao.trim() || undefined,
          data_ultima_revisao: createDraft.data_referencia
            ? fromDateInputValue(createDraft.data_referencia)
            : undefined,
        },
        getAccessToken,
      );
      setCreateDraft(DEFAULT_DRAFT);
      setFormExpanded(false);
      onFeedback?.({ type: "success", text: "Revisão programada criada." });
      await load();
    } catch (err) {
      onFeedback?.({
        type: "error",
        text: err instanceof Error ? err.message : "Falha ao programar revisão.",
      });
    } finally {
      setSaving(false);
    }
  }

  async function handleSave() {
    if (!canManage || !schedule) return;
    setSaving(true);
    try {
      const body: {
        filial: string;
        intervalo_meses: number;
        observacao: string;
        data_ultima_revisao?: string | null;
      } = {
        filial,
        intervalo_meses: draft.intervalo_meses,
        observacao: draft.observacao.trim(),
      };
      if (draft.data_referencia !== referenceInputValue(schedule)) {
        body.data_ultima_revisao = draft.data_referencia
          ? fromDateInputValue(draft.data_referencia)
          : null;
      }
      await updateRevisaoProgramada(schedule.revisao_id, body, getAccessToken);
      onFeedback?.({ type: "success", text: "Revisão programada atualizada." });
      await load();
    } catch (err) {
      onFeedback?.({
        type: "error",
        text: err instanceof Error ? err.message : "Falha ao salvar revisão programada.",
      });
    } finally {
      setSaving(false);
    }
  }

  async function handleRegistrar() {
    if (!canManage || !schedule) return;
    const label = formatDate(fromDateInputValue(feitoDate));
    if (!window.confirm(`Registrar revisão feita em ${label} para ${codigoFerramenta}?`)) return;
    setSaving(true);
    try {
      await registrarRevisaoProgramada(
        schedule.revisao_id,
        filial,
        fromDateInputValue(feitoDate),
        getAccessToken,
      );
      setFeitoDate(toDateInputValue(new Date()));
      onFeedback?.({ type: "success", text: "Revisão registrada." });
      await load();
    } catch (err) {
      onFeedback?.({
        type: "error",
        text: err instanceof Error ? err.message : "Falha ao registrar revisão.",
      });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!canManage || !schedule) return;
    if (!window.confirm(`Remover programação de revisão de ${codigoFerramenta}?`)) return;
    setSaving(true);
    try {
      await deleteRevisaoProgramada(schedule.revisao_id, filial, getAccessToken);
      setFormExpanded(false);
      onFeedback?.({ type: "success", text: "Revisão programada removida." });
      await load();
    } catch (err) {
      onFeedback?.({
        type: "error",
        text: err instanceof Error ? err.message : "Falha ao remover revisão programada.",
      });
    } finally {
      setSaving(false);
    }
  }

  const formToggleLabel = schedule
    ? formExpanded
      ? "Ocultar configuração"
      : "Configurar programação"
    : formExpanded
      ? "Ocultar formulário"
      : "Programar revisão";

  return (
    <section className="dm-card dm-revisao-ferramenta">
      <div className="dm-section-header">
        <div className="dm-section-header__title-group">
          <h3 className="dm-section-header__title">
            Revisão programada
            <HelpTooltip
              content={CONFIG_TOOLTIPS.revisaoSection}
              ariaLabel="Ajuda: revisão programada"
              className="dm-section-header__help"
            />
          </h3>
          <p className="dm-section-header__hint">
            Periodicidade de inspeção desta ferramenta no módulo preventivo.
          </p>
        </div>
        {alerta ? (
          <div className="dm-section-header__meta">
            <StatusBadge status={alerta.status} />
          </div>
        ) : null}
      </div>

      {loading ? <StateBox>Carregando revisão programada…</StateBox> : null}

      {!loading && schedule && alerta ? (
        <div className="dm-revisao-ferramenta__metrics">
          <div className="dm-revisao-ferramenta__metric">
            <CalendarClock size={16} aria-hidden="true" />
            <span>Referência</span>
            <strong>{formatDateTime(alerta.data_referencia)}</strong>
          </div>
          <div className="dm-revisao-ferramenta__metric">
            <span>Próxima revisão</span>
            <strong>{formatDate(alerta.data_proxima_revisao)}</strong>
          </div>
          <div className="dm-revisao-ferramenta__metric">
            <span>Dias restantes</span>
            <strong>
              {alerta.dias_restantes === null || alerta.dias_restantes === undefined
                ? "—"
                : alerta.dias_restantes.toLocaleString("pt-BR")}
            </strong>
          </div>
        </div>
      ) : null}

      {!loading && !schedule && !canManage ? (
        <StateBox>Revisão periódica não programada para esta ferramenta.</StateBox>
      ) : null}

      {!loading && canManage && schedule ? (
        <div className="dm-revisao-ferramenta__feito">
          <label className="dm-field">
            <FieldLabel label="Data do feito" hint={CONFIG_TOOLTIPS.revisaoRegistrar} />
            <input
              type="date"
              value={feitoDate}
              onChange={(event) => setFeitoDate(event.target.value)}
            />
          </label>
          <button
            type="button"
            className="dm-primary-btn"
            onClick={() => void handleRegistrar()}
            disabled={saving}
          >
            Marcar feito
          </button>
        </div>
      ) : null}

      {!loading ? (
        <div className="dm-revisao-ferramenta__historico">
          <div className="dm-revisao-ferramenta__historico-header">
            <h4 className="dm-revisao-ferramenta__historico-title">
              Últimas revisões feitas
              <HelpTooltip
                content={CONFIG_TOOLTIPS.revisaoHistorico}
                ariaLabel="Ajuda: histórico de revisões"
              />
            </h4>
          </div>
          {realizacoes.length === 0 ? (
            <StateBox>Nenhuma revisão marcada como feita ainda.</StateBox>
          ) : (
            <div className="dm-revisao-historico-scroll">
              <table className="dm-revisao-historico-table">
                <thead>
                  <tr>
                    <th>Data da revisão</th>
                    <th>Intervalo</th>
                    <th>Registrado em</th>
                    <th>Observação</th>
                  </tr>
                </thead>
                <tbody>
                  {realizacoes.map((item) => (
                    <tr key={item.realizacao_id}>
                      <td>{formatDateTime(item.data_revisao)}</td>
                      <td>{item.intervalo_meses} mes(es)</td>
                      <td>{formatDateTime(item.data_registro)}</td>
                      <td>{item.observacao?.trim() || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : null}

      {!loading && canManage ? (
        <div className="dm-revisao-ferramenta__form-panel">
          <button
            type="button"
            className="dm-revisao-ferramenta__toggle"
            aria-expanded={formExpanded}
            onClick={() => setFormExpanded((current) => !current)}
          >
            <span>{formToggleLabel}</span>
            <ChevronDown
              size={16}
              aria-hidden="true"
              className={formExpanded ? "dm-revisao-ferramenta__toggle-icon is-open" : "dm-revisao-ferramenta__toggle-icon"}
            />
          </button>

          {formExpanded && !schedule ? (
            <form className="dm-form-grid dm-revisao-ferramenta__form" onSubmit={handleCreate}>
              <label className="dm-field">
                <FieldLabel label="Intervalo (meses)" hint={CONFIG_TOOLTIPS.revisaoIntervalo} />
                <input
                  type="number"
                  min={1}
                  max={120}
                  value={createDraft.intervalo_meses}
                  onChange={(event) =>
                    setCreateDraft((prev) => ({
                      ...prev,
                      intervalo_meses: Number(event.target.value),
                    }))
                  }
                />
              </label>
              <label className="dm-field">
                <FieldLabel label="Data de referência" hint={CONFIG_TOOLTIPS.revisaoReferencia} />
                <input
                  type="date"
                  value={createDraft.data_referencia}
                  onChange={(event) =>
                    setCreateDraft((prev) => ({ ...prev, data_referencia: event.target.value }))
                  }
                />
              </label>
              <label className="dm-field dm-field--span-full">
                <FieldLabel label="Observação" hint={CONFIG_TOOLTIPS.revisaoObservacao} />
                <input
                  value={createDraft.observacao}
                  onChange={(event) =>
                    setCreateDraft((prev) => ({ ...prev, observacao: event.target.value }))
                  }
                  placeholder="Opcional — checklist ou pontos a verificar"
                />
              </label>
              <div className="dm-form-grid__buttons dm-field--span-full">
                <button type="submit" className="dm-primary-btn" disabled={saving}>
                  Programar revisão
                </button>
              </div>
            </form>
          ) : null}

          {formExpanded && schedule ? (
            <div className="dm-revisao-ferramenta__edit">
              <label className="dm-field">
                <FieldLabel label="Intervalo (meses)" hint={CONFIG_TOOLTIPS.revisaoIntervalo} />
                <div className="dm-editable-cell">
                  <input
                    type="number"
                    min={1}
                    max={120}
                    value={draft.intervalo_meses}
                    onChange={(event) =>
                      setDraft((prev) => ({ ...prev, intervalo_meses: Number(event.target.value) }))
                    }
                  />
                  <PendingChangeBadge visible={isDirty(schedule, draft)} />
                </div>
              </label>
              <label className="dm-field">
                <FieldLabel label="Observação" hint={CONFIG_TOOLTIPS.revisaoObservacao} />
                <input
                  value={draft.observacao}
                  onChange={(event) =>
                    setDraft((prev) => ({ ...prev, observacao: event.target.value }))
                  }
                  placeholder="Opcional"
                />
              </label>
              <label className="dm-field">
                <FieldLabel label="Data de referência" hint={CONFIG_TOOLTIPS.revisaoReferencia} />
                <div className="dm-editable-cell">
                  <input
                    type="date"
                    value={draft.data_referencia}
                    onChange={(event) =>
                      setDraft((prev) => ({ ...prev, data_referencia: event.target.value }))
                    }
                  />
                  <PendingChangeBadge
                    visible={draft.data_referencia !== referenceInputValue(schedule)}
                  />
                </div>
                {!schedule.data_ultima_revisao && alerta?.data_referencia ? (
                  <span className="dm-field-hint">
                    Referência automática: {formatDate(alerta.data_referencia)} (data de criação da
                    programação). Preencha para fixar manualmente.
                  </span>
                ) : null}
              </label>
              <div className="dm-revisao-ferramenta__actions">
                <button
                  type="button"
                  className="dm-ghost-btn"
                  onClick={() => void handleSave()}
                  disabled={saving || !isDirty(schedule, draft)}
                >
                  Salvar alterações
                </button>
                <button
                  type="button"
                  className="dm-ghost-btn dm-ghost-btn--danger"
                  onClick={() => void handleDelete()}
                  disabled={saving}
                >
                  Remover
                </button>
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
