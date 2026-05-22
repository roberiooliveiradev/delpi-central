import { useState } from "react";
import type { AppProps } from "../../../App";
import { Pagination } from "../../../components/Pagination";
import { useClientPagination } from "../../../hooks/useClientPagination";
import {
  createInvestimento,
  deleteInvestimento,
  type Investimento,
  type OptionsData,
} from "../../../data/api/transformometroApi";
import { optionalDateField, todayDateInput, toDateInputValue } from "../../../utils/dateInputs";
import { CadastroSection } from "./CadastroSection";

const CADASTRO_TABLE_PAGE_SIZE = 10;

const emptyInvForm = () => ({
  tipo_investimento: "unico",
  descricao_item: "",
  quantidade: 1,
  valor_unitario: 0,
  recorrencia: "unico",
  categoria_investimento: "",
  data_investimento: todayDateInput(),
  meses_vigencia: "",
});

type Props = Pick<AppProps, "getAccessToken"> & {
  revisaoId: string;
  options: OptionsData;
  investimentos: Investimento[];
  onError: (message: string | null) => void;
  onReload: () => Promise<void>;
};

export function RevisaoInvestimentosSection({
  revisaoId,
  options,
  investimentos,
  getAccessToken,
  onError,
  onReload,
}: Props) {
  const [invForm, setInvForm] = useState(emptyInvForm);
  const { slice, page, setPage, total } = useClientPagination(
    investimentos,
    CADASTRO_TABLE_PAGE_SIZE
  );

  async function handleAddInvestimento(e: React.FormEvent) {
    e.preventDefault();
    onError(null);
    try {
      await createInvestimento(
        {
          revisao_id: revisaoId,
          tipo_investimento: invForm.tipo_investimento,
          descricao_item: invForm.descricao_item,
          quantidade: invForm.quantidade,
          valor_unitario: invForm.valor_unitario,
          recorrencia: invForm.recorrencia,
          categoria_investimento: invForm.categoria_investimento || undefined,
          data_investimento: optionalDateField(invForm.data_investimento),
          meses_vigencia: invForm.meses_vigencia
            ? Number.parseInt(invForm.meses_vigencia, 10)
            : undefined,
        },
        getAccessToken
      );
      setInvForm(emptyInvForm());
      await onReload();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao criar investimento");
    }
  }

  return (
    <CadastroSection
      embedded
      title="Investimentos"
      hint="Custos únicos ou recorrentes ligados a esta revisão (software, equipamento, horas, etc.)."
      badge={`${investimentos.length}`}
    >
      {investimentos.length > 0 ? (
        <>
        <div className="ds-table-wrap ds-cadastro-section__table">
          <table className="ds-table ds-table--compact">
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Descrição</th>
                <th>Qtd</th>
                <th>Unit.</th>
                <th>Total</th>
                <th>Data</th>
                <th>Meses vig.</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {slice.map((inv) => (
                <tr key={inv.investimento_id}>
                  <td>{inv.tipo_investimento}</td>
                  <td>{inv.descricao_item}</td>
                  <td>{inv.quantidade}</td>
                  <td>{inv.valor_unitario.toLocaleString("pt-BR")}</td>
                  <td>{inv.valor_total.toLocaleString("pt-BR")}</td>
                  <td>{toDateInputValue(inv.data_investimento) || "—"}</td>
                  <td>{inv.meses_vigencia ?? "—"}</td>
                  <td>
                    <button
                      type="button"
                      className="ds-ghost-btn"
                      onClick={() =>
                        void deleteInvestimento(inv.investimento_id, getAccessToken).then(onReload)
                      }
                    >
                      Remover
                    </button>
                  </td>
                </tr>
              ))}
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

      <form className="ds-cadastro-subsection" onSubmit={handleAddInvestimento}>
        <h4 className="ds-cadastro-subsection__title">Adicionar investimento</h4>
        <div className="ds-filters-row">
          <label className="ds-filter-box">
            Tipo
            <select
              value={invForm.tipo_investimento}
              onChange={(e) => setInvForm({ ...invForm, tipo_investimento: e.target.value })}
            >
              {options.tipo_investimento.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label className="ds-filter-box ds-filter-box--wide">
            Descrição *
            <input
              required
              value={invForm.descricao_item}
              onChange={(e) => setInvForm({ ...invForm, descricao_item: e.target.value })}
            />
          </label>
          <label className="ds-filter-box">
            Qtd
            <input
              type="number"
              min={0}
              step="any"
              value={invForm.quantidade}
              onChange={(e) => setInvForm({ ...invForm, quantidade: Number(e.target.value) })}
            />
          </label>
          <label className="ds-filter-box">
            Valor unit. (R$)
            <input
              type="number"
              min={0}
              step="any"
              value={invForm.valor_unitario}
              onChange={(e) =>
                setInvForm({ ...invForm, valor_unitario: Number(e.target.value) })
              }
            />
          </label>
          <label className="ds-filter-box">
            Recorrência
            <select
              value={invForm.recorrencia}
              onChange={(e) => setInvForm({ ...invForm, recorrencia: e.target.value })}
            >
              {options.recorrencias.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </label>
          <label className="ds-filter-box">
            Data
            <input
              type="date"
              value={invForm.data_investimento}
              onChange={(e) => setInvForm({ ...invForm, data_investimento: e.target.value })}
            />
          </label>
          <label className="ds-filter-box">
            Meses vigência
            <input
              type="number"
              min={1}
              step={1}
              placeholder="Opcional"
              value={invForm.meses_vigencia}
              onChange={(e) => setInvForm({ ...invForm, meses_vigencia: e.target.value })}
            />
          </label>
        </div>
        <button type="submit" className="ds-primary-btn">
          Adicionar investimento
        </button>
      </form>
    </CadastroSection>
  );
}
