import { useState } from "react";
import { dataTableBemClasses } from "@delpi/plugin-ui/index";

import type { AppProps } from "../../../App";
import { Pagination } from "../../../components/Pagination";
import { TableHeader } from "../../../components/TableHeader";
import { TableRowActions } from "../../../components/ui/TableRowActions";
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
import { formatDisplayDate } from "../../../utils/dates";
import {
  labelTipoInvestimento,
} from "../../../utils/catalogLabels";
import { formatCurrency, formatDecimal } from "../../../utils/format";
import { InvestimentoFormFields } from "../InvestimentoFormFields";
import {
  emptyInvestimentoForm,
  investimentoFormFromEntity,
  payloadFromInvestimentoForm,
} from "../investimentoForm";
import { CadastroSection } from "./CadastroSection";
import { useConfirm } from "../../../components/ui/ConfirmDialogProvider";
import { DS_GHOST_BTN, dsGhostBtn } from "../../../components/ghostChrome";

const CADASTRO_TABLE_PAGE_SIZE = 10;
const C = TM_HELP_TOOLTIPS.columns;
const I = TM_HELP_TOOLTIPS.investimentos;
const tableCn = dataTableBemClasses("ds");

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
  const confirm = useConfirm();
  const [invForm, setInvForm] = useState(() => emptyInvestimentoForm(options));
  const [editingInvestimentoId, setEditingInvestimentoId] = useState<string | null>(null);
  const [editInvForm, setEditInvForm] = useState(() => emptyInvestimentoForm(options));
  const { slice, page, setPage, total } = useClientPagination(
    investimentos,
    CADASTRO_TABLE_PAGE_SIZE
  );

  const editingInvestimento = editingInvestimentoId
    ? investimentos.find((item) => item.investimento_id === editingInvestimentoId) ?? null
    : null;

  function startEditInvestimento(inv: Investimento) {
    const index = investimentos.findIndex((item) => item.investimento_id === inv.investimento_id);
    if (index >= 0) {
      setPage(Math.floor(index / CADASTRO_TABLE_PAGE_SIZE) + 1);
    }
    setEditingInvestimentoId(inv.investimento_id);
    setEditInvForm(investimentoFormFromEntity(inv));
  }

  function cancelEditInvestimento() {
    setEditingInvestimentoId(null);
    setEditInvForm(emptyInvestimentoForm(options));
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
      cancelEditInvestimento();
      await onReload();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao atualizar investimento");
    }
  }

  async function handleDeleteInvestimento(inv: Investimento) {
    const confirmed = await confirm({
      title: "Remover investimento",
      message: `Remover o investimento "${inv.descricao_item}"?`,
      confirmLabel: "Remover",
      variant: "danger",
    });
    if (!confirmed) {
      return;
    }
    onError(null);
    try {
      await deleteInvestimento(inv.investimento_id, getAccessToken);
      if (editingInvestimentoId === inv.investimento_id) {
        cancelEditInvestimento();
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
                  <th>
                    <TableHeader label="Tipo" hint={I.tipo} />
                  </th>
                  <th className={tableCn.colWide}>
                    <TableHeader label="Descrição" hint={I.descricao} />
                  </th>
                  <th className={tableCn.colNumeric}>
                    <TableHeader label="Qtd" hint={I.quantidade} />
                  </th>
                  <th className={tableCn.colNumeric}>
                    <TableHeader label="Unit." hint={C.unitario} />
                  </th>
                  <th className={tableCn.colNumeric}>
                    <TableHeader label="Total" hint={I.total} />
                  </th>
                  <th>
                    <TableHeader label="Data" hint={I.data} />
                  </th>
                  <th className={tableCn.colNumeric}>
                    <TableHeader label="Meses vig." hint={C.mesesVigenciaCurto} />
                  </th>
                  {!readOnly ? (
                    <th className="ds-table__actions-col">
                      <TableHeader label="Ações" hint={C.acoes} />
                    </th>
                  ) : null}
                </tr>
              </thead>
              <tbody>
                {slice.map((inv) => {
                  const isEditing = !readOnly && editingInvestimentoId === inv.investimento_id;
                  return (
                    <tr
                      key={inv.investimento_id}
                      className={isEditing ? "ds-table__row--editing" : undefined}
                    >
                      <td>{labelTipoInvestimento(inv.tipo_investimento)}</td>
                      <td className={tableCn.colWide}>{inv.descricao_item}</td>
                      <td className={tableCn.colNumeric}>{formatDecimal(inv.quantidade, 2)}</td>
                      <td className={tableCn.colNumeric}>{formatCurrency(inv.valor_unitario)}</td>
                      <td className={tableCn.colNumeric}>{formatCurrency(inv.valor_total)}</td>
                      <td>{formatDisplayDate(toDateInputValue(inv.data_investimento))}</td>
                      <td className={tableCn.colNumeric}>{inv.meses_vigencia ?? "—"}</td>
                      {!readOnly ? (
                        <td className="ds-table__actions-col">
                          <TableRowActions>
                            <button
                              type="button"
                              className={DS_GHOST_BTN}
                              disabled={isEditing}
                              onClick={() => startEditInvestimento(inv)}
                            >
                              Editar
                            </button>
                            <button
                              type="button"
                              className={dsGhostBtn("danger")}
                              onClick={() => void handleDeleteInvestimento(inv)}
                            >
                              Remover
                            </button>
                          </TableRowActions>
                        </td>
                      ) : null}
                    </tr>
                  );
                })}
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

      {!readOnly && editingInvestimento ? (
        <form
          className="ds-cadastro-subsection ds-cadastro-subsection--divider"
          onSubmit={handleSaveEditInvestimento}
        >
          <h4 className="ds-cadastro-subsection__title">
            Editar investimento — {editingInvestimento.descricao_item}
          </h4>
          <InvestimentoFormFields
            form={editInvForm}
            options={options}
            onChange={setEditInvForm}
            idPrefix={`tm-inv-edit-${editingInvestimento.investimento_id}`}
          />
          <div className="ds-cadastro-form__actions">
            <button type="submit" className="ds-primary-btn">
              Salvar investimento
            </button>
            <button type="button" className={DS_GHOST_BTN} onClick={cancelEditInvestimento}>
              Cancelar
            </button>
          </div>
        </form>
      ) : null}

      {!readOnly && !editingInvestimentoId ? (
        <form
          className="ds-cadastro-subsection ds-cadastro-subsection--divider"
          onSubmit={handleAddInvestimento}
        >
          <h4 className="ds-cadastro-subsection__title">Adicionar investimento</h4>
          <InvestimentoFormFields
            form={invForm}
            options={options}
            onChange={setInvForm}
            idPrefix="tm-inv-add"
          />
          <div className="ds-cadastro-form__actions">
            <button type="submit" className="ds-primary-btn">
              Adicionar investimento
            </button>
          </div>
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
