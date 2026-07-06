import { useState } from "react";
import type { AppProps } from "../../../App";
import { Pagination } from "../../../components/Pagination";
import { TableHeader } from "../../../components/HelpTooltip";
import { TM_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import { useClientPagination } from "../../../hooks/useClientPagination";
import {
  createInvestimento,
  deleteInvestimento,
  updateInvestimento,
  type Investimento,
  type OptionsData,
} from "../../../data/api/transformometroApi";
import { toDateInputValue } from "../../../utils/dateInputs";
import { InvestimentoFormFields } from "../InvestimentoFormFields";
import {
  emptyInvestimentoForm,
  investimentoFormFromEntity,
  payloadFromInvestimentoForm,
} from "../investimentoForm";
import { CadastroSection } from "./CadastroSection";

const CADASTRO_TABLE_PAGE_SIZE = 10;
const C = TM_HELP_TOOLTIPS.columns;
const I = TM_HELP_TOOLTIPS.investimentos;

type Props = Pick<AppProps, "getAccessToken"> & {
  revisaoId: string;
  options: OptionsData;
  investimentos: Investimento[];
  readOnly?: boolean;
  embeddedInCard?: boolean;
  onError: (message: string | null) => void;
  onReload: () => Promise<void>;
};

export function RevisaoInvestimentosSection({
  revisaoId,
  options,
  investimentos,
  readOnly = false,
  embeddedInCard = false,
  getAccessToken,
  onError,
  onReload,
}: Props) {
  const [invForm, setInvForm] = useState(() => emptyInvestimentoForm(options));
  const [editingInvestimentoId, setEditingInvestimentoId] = useState<string | null>(null);
  const [editInvForm, setEditInvForm] = useState(() => emptyInvestimentoForm(options));
  const { slice, page, setPage, total } = useClientPagination(
    investimentos,
    CADASTRO_TABLE_PAGE_SIZE
  );

  function startEditInvestimento(inv: Investimento) {
    const index = investimentos.findIndex((item) => item.investimento_id === inv.investimento_id);
    if (index >= 0) {
      setPage(Math.floor(index / CADASTRO_TABLE_PAGE_SIZE) + 1);
    }
    setEditingInvestimentoId(inv.investimento_id);
    setEditInvForm(investimentoFormFromEntity(inv));
  }

  async function handleAddInvestimento(e: React.FormEvent) {
    e.preventDefault();
    onError(null);
    try {
      await createInvestimento(
        { revisao_id: revisaoId, ...payloadFromInvestimentoForm(invForm) },
        getAccessToken
      );
      setInvForm(emptyInvestimentoForm(options));
      await onReload();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao criar investimento");
    }
  }

  async function handleSaveEditInvestimento(e: React.FormEvent) {
    e.preventDefault();
    if (!editingInvestimentoId) return;
    onError(null);
    try {
      await updateInvestimento(
        editingInvestimentoId,
        payloadFromInvestimentoForm(editInvForm),
        getAccessToken
      );
      setEditingInvestimentoId(null);
      setEditInvForm(emptyInvestimentoForm(options));
      await onReload();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao atualizar investimento");
    }
  }

  async function handleDeleteInvestimento(inv: Investimento) {
    if (!window.confirm(`Remover o investimento "${inv.descricao_item}"?`)) {
      return;
    }
    onError(null);
    try {
      await deleteInvestimento(inv.investimento_id, getAccessToken);
      if (editingInvestimentoId === inv.investimento_id) {
        setEditingInvestimentoId(null);
        setEditInvForm(emptyInvestimentoForm(options));
      }
      await onReload();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao excluir investimento");
    }
  }

  const body = (
    <>
      {investimentos.length > 0 ? (
        <>
          <div className="ds-table-wrap ds-cadastro-section__table">
            <table className="ds-table ds-table--compact">
              <thead>
                <tr>
                  <th><TableHeader label="Tipo" hint={I.tipo} /></th>
                  <th><TableHeader label="Descrição" hint={I.descricao} /></th>
                  <th><TableHeader label="Qtd" hint={I.quantidade} /></th>
                  <th><TableHeader label="Unit." hint={C.unitario} /></th>
                  <th><TableHeader label="Total" hint={I.total} /></th>
                  <th><TableHeader label="Data" hint={I.data} /></th>
                  <th><TableHeader label="Meses vig." hint={C.mesesVigenciaCurto} /></th>
                  {!readOnly ? (
                    <th className="ds-table__actions-col">
                      <TableHeader label="Ações" hint={C.acoes} />
                    </th>
                  ) : null}
                </tr>
              </thead>
              <tbody>
                {slice.map((inv) =>
                  !readOnly && editingInvestimentoId === inv.investimento_id ? (
                    <tr key={inv.investimento_id} className="ds-table__row--editing">
                      <td colSpan={8}>
                        <form className="ds-cadastro-subsection" onSubmit={handleSaveEditInvestimento}>
                          <h4 className="ds-cadastro-subsection__title">
                            Editar investimento — {inv.descricao_item}
                          </h4>
                          <InvestimentoFormFields
                            form={editInvForm}
                            options={options}
                            onChange={setEditInvForm}
                            idPrefix={`tm-inv-edit-${inv.investimento_id}`}
                          />
                          <div className="ds-cadastro-form__actions">
                            <button type="submit" className="ds-primary-btn">
                              Salvar investimento
                            </button>
                            <button
                              type="button"
                              className="ds-ghost-btn"
                              onClick={() => {
                                setEditingInvestimentoId(null);
                                setEditInvForm(emptyInvestimentoForm(options));
                              }}
                            >
                              Cancelar
                            </button>
                          </div>
                        </form>
                      </td>
                    </tr>
                  ) : (
                    <tr key={inv.investimento_id}>
                      <td>{inv.tipo_investimento}</td>
                      <td>{inv.descricao_item}</td>
                      <td>{inv.quantidade}</td>
                      <td>{inv.valor_unitario.toLocaleString("pt-BR")}</td>
                      <td>{inv.valor_total.toLocaleString("pt-BR")}</td>
                      <td>{toDateInputValue(inv.data_investimento) || "—"}</td>
                      <td>{inv.meses_vigencia ?? "—"}</td>
                      {!readOnly ? (
                        <td>
                          <div className="ds-table__actions">
                            <button
                              type="button"
                              className="ds-ghost-btn"
                              onClick={() => startEditInvestimento(inv)}
                            >
                              Editar
                            </button>
                            <button
                              type="button"
                              className="ds-ghost-btn"
                              onClick={() => void handleDeleteInvestimento(inv)}
                            >
                              Remover
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
          <Pagination
            page={page}
            pageSize={CADASTRO_TABLE_PAGE_SIZE}
            total={total}
            onPageChange={setPage}
            hideWhenSinglePage
          />
        </>
      ) : (
        <p className="ds-state-box">Nenhum investimento nesta revisão.</p>
      )}

      {!readOnly ? (
        <form className="ds-cadastro-subsection" onSubmit={handleAddInvestimento}>
          <h4 className="ds-cadastro-subsection__title">Adicionar investimento</h4>
          <InvestimentoFormFields form={invForm} options={options} onChange={setInvForm} />
          <button type="submit" className="ds-primary-btn">
            Adicionar investimento
          </button>
        </form>
      ) : null}
    </>
  );

  if (embeddedInCard) return body;

  return (
    <CadastroSection
      embedded
      title="Investimentos"
      hint="Custos únicos ou recorrentes ligados a esta revisão (software, equipamento, horas, etc.)."
      badge={`${investimentos.length}`}
    >
      {body}
    </CadastroSection>
  );
}
