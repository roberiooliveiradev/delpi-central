import { useCallback, useEffect, useState } from "react";
import type { AppProps } from "../../App";
import { FieldLabel, NativeTextControl } from "@delpi/plugin-ui/index";
import { DS_TABLE_CLASS_NAMES } from "../../components/dataTableUi";
import { TableHeader } from "../../components/TableHeader";
import { TableRowActions } from "../../components/ui/TableRowActions";
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
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { DS_FILTERS_ROW, DS_FILTER_BOX_PLAIN, DS_FILTER_BOX_WIDE } from "../../components/filterChrome";
import { EMPTY_STATE_CLASS } from "../../components/emptyStateUi";

const C = TM_HELP_TOOLTIPS.columns;
const R = TM_HELP_TOOLTIPS.recursos;
const tableCn = DS_TABLE_CLASS_NAMES;

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
  const confirm = useConfirm();
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
    const confirmed = await confirm({
      title: "Excluir vigência",
      message: "Excluir esta vigência de custo?",
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!confirmed) return;
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
        <p className={EMPTY_STATE_CLASS}>Carregando histórico…</p>
      ) : custos.length > 0 ? (
        <div className={`${tableCn.wrap} ds-cadastro-section__table`}>
          <table className={tableCn.compactTable}>
            <thead>
              <tr>
                <th className={tableCn.colNumeric}>
                  <TableHeader label="Valor/mês" hint={C.valorMes} />
                </th>
                <th><TableHeader label="Início" hint={C.custoInicio} /></th>
                <th><TableHeader label="Fim" hint={C.fim} /></th>
                <th className={tableCn.colWide}>
                  <TableHeader label="Obs." hint={C.observacoes} />
                </th>
                {!readOnly ? (
                  <th className={tableCn.colActions}>
                    <TableHeader label="Ações" hint={C.acoes} />
                  </th>
                ) : null}
              </tr>
            </thead>
            <tbody>
              {custos.map((c) =>
                !readOnly && editingId === c.recurso_custo_id ? (
                  <tr key={c.recurso_custo_id} className={tableCn.rowEditing}>
                    <td colSpan={5}>
                      <form onSubmit={handleSaveEdit}>
                        <div className={DS_FILTERS_ROW}>
                          <label className={DS_FILTER_BOX_PLAIN}>
                            <FieldLabel className="tm-field__label" label="Valor (R$)" hint={C.valorMes} />
                            <NativeTextControl
                              type="number"
                              min={0}
                              step="any"
                              required
                              value={editForm.valor_mensal}
                              onChange={(valor_mensal) =>
                                setEditForm({ ...editForm, valor_mensal })
                              }
                            />
                          </label>
                          <label className={DS_FILTER_BOX_PLAIN}>
                            <FieldLabel className="tm-field__label" label="Início *" hint={C.custoInicio} />
                            <NativeTextControl
                              type="date"
                              required
                              value={editForm.data_inicio_vigencia}
                              onChange={(data_inicio_vigencia) =>
                                setEditForm({
                                  ...editForm,
                                  data_inicio_vigencia,
                                })
                              }
                            />
                          </label>
                          <label className={DS_FILTER_BOX_PLAIN}>
                            <FieldLabel className="tm-field__label" label="Fim" hint={C.fim} />
                            <NativeTextControl
                              type="date"
                              value={editForm.data_fim_vigencia}
                              onChange={(data_fim_vigencia) =>
                                setEditForm({ ...editForm, data_fim_vigencia })
                              }
                            />
                          </label>
                        </div>
                        <label className={DS_FILTER_BOX_WIDE}>
                          <FieldLabel className="tm-field__label" label="Observações" hint={C.observacoes} />
                          <NativeTextControl
                            value={editForm.observacoes}
                            onChange={(observacoes) =>
                              setEditForm({ ...editForm, observacoes })
                            }
                          />
                        </label>
                        <div className="ds-cadastro-form__actions">
                          <button type="submit" className="ds-primary-btn">
                            Salvar período
                          </button>
                          <button
                            type="button"
                            className={DS_GHOST_BTN}
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
                    <td className={tableCn.colNumeric}>{formatCurrency(c.valor_mensal)}</td>
                    <td>{toDateInputValue(c.data_inicio_vigencia) || "—"}</td>
                    <td>{toDateInputValue(c.data_fim_vigencia) || "—"}</td>
                    <td className={tableCn.colWide}>{c.observacoes || "—"}</td>
                    {!readOnly ? (
                      <td className={tableCn.colActions}>
                        <TableRowActions>
                          <button
                            type="button"
                            className={DS_GHOST_BTN}
                            onClick={() => startEdit(c)}
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            className={DS_GHOST_BTN}
                            onClick={() => void handleDelete(c)}
                          >
                            Excluir
                          </button>
                        </TableRowActions>
                      </td>
                    ) : null}
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <p className={EMPTY_STATE_CLASS}>Nenhum período de custo cadastrado.</p>
      )}

      {!readOnly ? (
        <form className="ds-cadastro-subsection" onSubmit={handleReajuste}>
          <h4 className="ds-cadastro-subsection__title">Registrar reajuste</h4>
          <div className={DS_FILTERS_ROW}>
            <label className={DS_FILTER_BOX_PLAIN}>
              <FieldLabel className="tm-field__label" label="Novo valor mensal (R$) *" hint={R.reajusteValor} />
              <NativeTextControl
                type="number"
                min={0}
                step="any"
                required
                value={reajuste.valor_mensal}
              onChange={(valor_mensal) => setReajuste({ ...reajuste, valor_mensal })}
              />
            </label>
            <label className={DS_FILTER_BOX_PLAIN}>
              <FieldLabel className="tm-field__label" label="Vigente a partir de *" hint={R.reajusteDesde} />
              <NativeTextControl
                type="date"
                required
                value={reajuste.vigente_desde}
              onChange={(vigente_desde) => setReajuste({ ...reajuste, vigente_desde })}
              />
            </label>
          </div>
          <label className={DS_FILTER_BOX_WIDE}>
            <FieldLabel className="tm-field__label" label="Observações" hint={C.observacoes} />
            <NativeTextControl
              value={reajuste.observacoes}
            onChange={(observacoes) => setReajuste({ ...reajuste, observacoes })}
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
