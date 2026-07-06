import { useCallback, useEffect, useState } from "react";
import type { AppProps } from "../../App";
import { FieldLabel, TableHeader } from "../../components/HelpTooltip";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  deleteRecursoCusto,
  fetchRecursoCustos,
  reajusteRecursoCusto,
  updateRecursoCusto,
  type RecursoCusto,
} from "../../data/api/transformometroApi";
import { optionalDateField, todayDateInput, toDateInputValue } from "../../utils/dateInputs";
import { formatCurrency } from "../../utils/format";

const C = TM_HELP_TOOLTIPS.columns;
const R = TM_HELP_TOOLTIPS.recursos;

type Props = Pick<AppProps, "getAccessToken"> & {
  recursoId: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  onError: (message: string | null) => void;
  onRecursoSynced: () => void;
};

export function RecursoCustosSection({
  recursoId,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  onError,
  onRecursoSynced,
}: Props) {
  const [custos, setCustos] = useState<RecursoCusto[]>([]);
  const [loading, setLoading] = useState(true);
  const [reajuste, setReajuste] = useState({
    valor_mensal: "",
    vigente_desde: todayDateInput(),
    observacoes: "",
  });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    valor_mensal: "",
    data_inicio_vigencia: "",
    data_fim_vigencia: "",
    observacoes: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const res = await fetchRecursoCustos(recursoId, getAccessToken);
      setCustos(res.items);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar histórico de custos");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, onError, recursoId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleReajuste(e: React.FormEvent) {
    e.preventDefault();
    const valor = Number.parseFloat(reajuste.valor_mensal);
    if (!Number.isFinite(valor) || valor < 0) {
      onError("Informe um valor mensal válido.");
      return;
    }
    onError(null);
    try {
      await reajusteRecursoCusto(
        recursoId,
        {
          valor_mensal: valor,
          vigente_desde: reajuste.vigente_desde,
          observacoes: reajuste.observacoes.trim() || undefined,
        },
        getAccessToken
      );
      setReajuste({ valor_mensal: "", vigente_desde: todayDateInput(), observacoes: "" });
      await load();
      onRecursoSynced();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao registrar reajuste");
    }
  }

  function startEdit(c: RecursoCusto) {
    setEditingId(c.recurso_custo_id);
    setEditForm({
      valor_mensal: String(c.valor_mensal),
      data_inicio_vigencia: toDateInputValue(c.data_inicio_vigencia),
      data_fim_vigencia: toDateInputValue(c.data_fim_vigencia),
      observacoes: c.observacoes ?? "",
    });
  }

  async function handleSaveEdit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingId) return;
    const valor = Number.parseFloat(editForm.valor_mensal);
    if (!Number.isFinite(valor) || valor < 0) {
      onError("Informe um valor mensal válido.");
      return;
    }
    onError(null);
    try {
      await updateRecursoCusto(
        editingId,
        {
          valor_mensal: valor,
          data_inicio_vigencia: editForm.data_inicio_vigencia,
          data_fim_vigencia: optionalDateField(editForm.data_fim_vigencia),
          observacoes: editForm.observacoes.trim() || undefined,
        },
        getAccessToken
      );
      setEditingId(null);
      await load();
      onRecursoSynced();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao atualizar vigência");
    }
  }

  async function handleDelete(c: RecursoCusto) {
    if (!window.confirm("Excluir esta vigência de custo?")) return;
    onError(null);
    try {
      await deleteRecursoCusto(c.recurso_custo_id, getAccessToken);
      if (editingId === c.recurso_custo_id) setEditingId(null);
      await load();
      onRecursoSynced();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao excluir vigência");
    }
  }

  const body = (
    <>
      {embeddedInCard ? null : (
        <>
          <h3 className="ds-cadastro-subsection__title">Custos ao longo do tempo</h3>
          <p className="ds-hint">
            O dashboard usa o valor vigente em cada mês (competência). Registre reajustes com a data de
            início; períodos anteriores permanecem com o valor antigo no cálculo retroativo.
          </p>
        </>
      )}

      {loading ? (
        <p className="ds-state-box">Carregando histórico…</p>
      ) : custos.length > 0 ? (
        <div className="ds-table-wrap ds-cadastro-section__table">
          <table className="ds-table ds-table--compact">
            <thead>
              <tr>
                <th><TableHeader label="Valor/mês" hint={C.valorMes} /></th>
                <th><TableHeader label="Início" hint={C.inicio} /></th>
                <th><TableHeader label="Fim" hint={C.fim} /></th>
                <th><TableHeader label="Obs." hint={C.observacoes} /></th>
                {!readOnly ? (
                  <th className="ds-table__actions-col">
                    <TableHeader label="Ações" hint={C.acoes} />
                  </th>
                ) : null}
              </tr>
            </thead>
            <tbody>
              {custos.map((c) =>
                !readOnly && editingId === c.recurso_custo_id ? (
                  <tr key={c.recurso_custo_id} className="ds-table__row--editing">
                    <td colSpan={5}>
                      <form onSubmit={handleSaveEdit}>
                        <div className="ds-filters-row">
                          <label className="ds-filter-box">
                            <FieldLabel label="Valor (R$)" hint={C.valorMes} />
                            <input
                              type="number"
                              min={0}
                              step="any"
                              required
                              value={editForm.valor_mensal}
                              onChange={(e) =>
                                setEditForm({ ...editForm, valor_mensal: e.target.value })
                              }
                            />
                          </label>
                          <label className="ds-filter-box">
                            <FieldLabel label="Início *" hint={C.inicio} />
                            <input
                              type="date"
                              required
                              value={editForm.data_inicio_vigencia}
                              onChange={(e) =>
                                setEditForm({
                                  ...editForm,
                                  data_inicio_vigencia: e.target.value,
                                })
                              }
                            />
                          </label>
                          <label className="ds-filter-box">
                            <FieldLabel label="Fim" hint={C.fim} />
                            <input
                              type="date"
                              value={editForm.data_fim_vigencia}
                              onChange={(e) =>
                                setEditForm({ ...editForm, data_fim_vigencia: e.target.value })
                              }
                            />
                          </label>
                        </div>
                        <label className="ds-filter-box ds-filter-box--wide">
                          <FieldLabel label="Observações" hint={C.observacoes} />
                          <input
                            value={editForm.observacoes}
                            onChange={(e) =>
                              setEditForm({ ...editForm, observacoes: e.target.value })
                            }
                          />
                        </label>
                        <div className="ds-cadastro-form__actions">
                          <button type="submit" className="ds-primary-btn">
                            Salvar período
                          </button>
                          <button
                            type="button"
                            className="ds-ghost-btn"
                            onClick={() => setEditingId(null)}
                          >
                            Cancelar
                          </button>
                        </div>
                      </form>
                    </td>
                  </tr>
                ) : (
                  <tr key={c.recurso_custo_id}>
                    <td>{formatCurrency(c.valor_mensal)}</td>
                    <td>{toDateInputValue(c.data_inicio_vigencia) || "—"}</td>
                    <td>{toDateInputValue(c.data_fim_vigencia) || "—"}</td>
                    <td>{c.observacoes || "—"}</td>
                    {!readOnly ? (
                      <td>
                        <div className="ds-table__actions">
                          <button
                            type="button"
                            className="ds-ghost-btn"
                            onClick={() => startEdit(c)}
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            className="ds-ghost-btn"
                            onClick={() => void handleDelete(c)}
                          >
                            Excluir
                          </button>
                        </div>
                      </td>
                    ) : null}
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="ds-state-box">Nenhum período de custo cadastrado.</p>
      )}

      {!readOnly ? (
        <form className="ds-cadastro-subsection" onSubmit={handleReajuste}>
          <h4 className="ds-cadastro-subsection__title">Registrar reajuste</h4>
          <div className="ds-filters-row">
            <label className="ds-filter-box">
              <FieldLabel label="Novo valor mensal (R$) *" hint={R.reajusteValor} />
              <input
                type="number"
                min={0}
                step="any"
                required
                value={reajuste.valor_mensal}
                onChange={(e) => setReajuste({ ...reajuste, valor_mensal: e.target.value })}
              />
            </label>
            <label className="ds-filter-box">
              <FieldLabel label="Vigente a partir de *" hint={R.reajusteDesde} />
              <input
                type="date"
                required
                value={reajuste.vigente_desde}
                onChange={(e) => setReajuste({ ...reajuste, vigente_desde: e.target.value })}
              />
            </label>
          </div>
          <label className="ds-filter-box ds-filter-box--wide">
            <FieldLabel label="Observações" hint={C.observacoes} />
            <input
              value={reajuste.observacoes}
              onChange={(e) => setReajuste({ ...reajuste, observacoes: e.target.value })}
              placeholder="Ex.: Renovação anual / renegociação"
            />
          </label>
          <button type="submit" className="ds-primary-btn">
            Registrar reajuste
          </button>
        </form>
      ) : null}
    </>
  );

  if (embeddedInCard) return body;

  return <section className="ds-cadastro-subsection">{body}</section>;
}
