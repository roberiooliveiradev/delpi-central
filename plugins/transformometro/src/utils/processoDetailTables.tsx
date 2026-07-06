import type { DataTableColumn } from "../components/DataTable";
import { TM_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { ProcessoComparativoItem, Revisao } from "../data/api/transformometroApi";
import { toDateInputValue } from "./dateInputs";

const C = TM_HELP_TOOLTIPS.columns;

export const formatProcessoNumber = (value?: number | null) =>
  Number(value ?? 0).toLocaleString("pt-BR");

export function buildComparativoColumns(): DataTableColumn<ProcessoComparativoItem>[] {
  return [
    {
      key: "versao",
      header: "Versão",
      headerHint: C.versao,
      render: (row) => row.versao_revisao ?? "—",
    },
    {
      key: "cenario",
      header: "Cenário",
      headerHint: C.cenario,
      render: (row) => row.cenario_tipo ?? "—",
    },
    {
      key: "ativa",
      header: "Ativa",
      headerHint: C.ativa,
      render: (row) => (row.revisao_ativa ? "sim" : "—"),
    },
    {
      key: "competencia",
      header: "Última competência",
      headerHint: C.competencia,
      render: (row) => row.ultima_competencia ?? "—",
    },
    {
      key: "meses",
      header: "Meses c/ dados",
      headerHint: C.mesesComDados,
      className: "ds-table__col--numeric",
      render: (row) => row.meses_com_dados ?? 0,
    },
    {
      key: "bruta",
      header: "Economia bruta",
      headerHint: C.economiaBruta,
      className: "ds-table__col--numeric",
      render: (row) => formatProcessoNumber(row.totais.economia_bruta),
    },
    {
      key: "liquida",
      header: "Economia líquida",
      headerHint: C.economiaLiquida,
      className: "ds-table__col--numeric",
      render: (row) => formatProcessoNumber(row.totais.economia_liquida_mes),
    },
    {
      key: "investimento",
      header: "Invest. total",
      headerHint: C.investimentoTotal,
      className: "ds-table__col--numeric",
      render: (row) => formatProcessoNumber(row.totais.investimento_total_mes),
    },
    {
      key: "recursos",
      header: "Recursos comp.",
      headerHint: C.recursosComp,
      className: "ds-table__col--numeric",
      render: (row) => formatProcessoNumber(row.totais.custo_recursos_compartilhados_mes),
    },
    {
      key: "horas",
      header: "Horas/mês",
      headerHint: C.horasMes,
      className: "ds-table__col--numeric",
      render: (row) => formatProcessoNumber(row.totais.horas_economizadas_mes),
    },
  ];
}

type RevisaoColumnOptions = {
  onOpen: (revisaoId: string) => void;
  onDelete: (revisao: Revisao) => void;
};

export function buildRevisaoColumns({
  onOpen,
  onDelete,
}: RevisaoColumnOptions): DataTableColumn<Revisao>[] {
  return [
    {
      key: "versao",
      header: "Versão",
      headerHint: C.versao,
      render: (r) => r.versao_revisao,
    },
    {
      key: "cenario",
      header: "Cenário",
      headerHint: C.cenario,
      render: (r) => r.cenario_tipo,
    },
    {
      key: "inicio",
      header: "Início",
      headerHint: C.inicio,
      render: (r) => toDateInputValue(r.data_inicio_vigencia) || "—",
    },
    {
      key: "impl",
      header: "Implantação",
      headerHint: C.implantacao,
      render: (r) => toDateInputValue(r.data_implantacao) || "—",
    },
    {
      key: "fim",
      header: "Fim",
      headerHint: C.fim,
      render: (r) => toDateInputValue(r.data_fim_vigencia) || "—",
    },
    {
      key: "ativa",
      header: "Ativa",
      headerHint: C.ativa,
      render: (r) =>
        r.revisao_ativa ? <span className="ds-badge ds-badge--success">ativa</span> : "—",
    },
    {
      key: "acoes",
      header: "",
      className: "ds-table__actions",
      render: (r) => (
        <div
          className="ds-table__actions"
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => e.stopPropagation()}
        >
          <button type="button" className="ds-ghost-btn" onClick={() => onOpen(r.revisao_id)}>
            Abrir
          </button>
          <button type="button" className="ds-ghost-btn ds-ghost-btn--danger" onClick={() => void onDelete(r)}>
            Excluir
          </button>
        </div>
      ),
    },
  ];
}
