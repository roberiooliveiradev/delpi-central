import type { DataTableColumn } from "../components/DataTable";
import { TableRowActions } from "../components/ui/TableRowActions";
import { BeneficioCalculoChip } from "../components/BeneficioCalculoChip";
import { TM_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { ProcessoComparativoItem, Revisao } from "../data/api/transformometroApi";
import { cenarioLabel } from "../content/cenarioLabels";
import { toDateInputValue } from "./dateInputs";
import { revisaoDisplayLabel } from "./revisaoLabels";
import { DS_GHOST_BTN, dsGhostBtn } from "../components/ghostChrome";

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
      render: (row) => cenarioLabel(row.cenario_tipo),
    },
    {
      key: "categoria",
      header: "Categoria",
      headerHint: C.beneficioCategoria,
      render: (row) => (
        <BeneficioCalculoChip
          value={row.beneficio_calculo_categoria}
          hideWhenBaseline
          cenarioTipo={row.cenario_tipo}
        />
      ),
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
      key: "tempo",
      header: "Tempo",
      headerHint: C.economiaTempo,
      className: "ds-table__col--numeric",
      render: (row) => formatProcessoNumber(row.breakdown?.economia_tempo),
    },
    {
      key: "retrabalho",
      header: "Retrabalho",
      headerHint: C.economiaRetrabalho,
      className: "ds-table__col--numeric",
      render: (row) => formatProcessoNumber(row.breakdown?.economia_retrabalho),
    },
    {
      key: "erros",
      header: "Erros",
      headerHint: C.economiaErros,
      className: "ds-table__col--numeric",
      render: (row) => formatProcessoNumber(row.breakdown?.economia_erros),
    },
    {
      key: "outros",
      header: "Outros",
      headerHint: C.economiaOutros,
      className: "ds-table__col--numeric",
      render: (row) => formatProcessoNumber(row.breakdown?.economia_outros),
    },
    {
      key: "liquida",
      header: "Economia líquida",
      headerHint: C.economiaLiquida,
      className: "ds-table__col--numeric",
      render: (row) => formatProcessoNumber(row.totais.economia_liquida_mes),
    },
    {
      key: "capacidade",
      header: "Ganho capacidade",
      headerHint: C.ganhoCapacidade,
      className: "ds-table__col--numeric",
      render: (row) => formatProcessoNumber(row.totais.ganho_capacidade),
    },
    {
      key: "reducaoVolume",
      header: "Sinal ↓ volume",
      headerHint: C.economiaReducaoVolume,
      className: "ds-table__col--numeric",
      render: (row) => formatProcessoNumber(row.totais.economia_reducao_volume),
    },
    {
      key: "deltaVolume",
      header: "Δ volume",
      headerHint: C.deltaVolume,
      className: "ds-table__col--numeric",
      render: (row) => formatProcessoNumber(row.totais.delta_volume),
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
  onDuplicate: (revisao: Revisao) => void;
  onDelete: (revisao: Revisao) => void;
  revisoesById?: Map<string, Revisao>;
};

function renderReferenciaLabel(revisao: Revisao, revisoesById?: Map<string, Revisao>): string {
  if ((revisao.cenario_tipo ?? "").toLowerCase() === "baseline") return "—";
  const refId = revisao.revisao_referencia_id;
  if (!refId) return "Linha de base (automático)";
  const ref = revisoesById?.get(refId);
  return ref ? revisaoDisplayLabel(ref) : "—";
}

export function buildRevisaoColumns({
  onOpen,
  onDuplicate,
  onDelete,
  revisoesById,
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
      render: (r) => cenarioLabel(r.cenario_tipo),
    },
    {
      key: "categoria",
      header: "Categoria",
      headerHint: C.beneficioCategoria,
      render: (r) => (
        <BeneficioCalculoChip
          value={r.beneficio_calculo_categoria}
          hideWhenBaseline
          cenarioTipo={r.cenario_tipo}
        />
      ),
    },
    {
      key: "referencia",
      header: "Compara com",
      headerHint: C.referenciaComparacao,
      render: (r) => renderReferenciaLabel(r, revisoesById),
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
      header: "Ações",
      headerHint: C.acoes,
      className: "ds-table__actions-col",
      render: (r) => (
        <TableRowActions>
          <button
            type="button"
            className={DS_GHOST_BTN}
            onClick={(e) => {
              e.stopPropagation();
              onOpen(r.revisao_id);
            }}
          >
            Abrir
          </button>
          <button
            type="button"
            className={DS_GHOST_BTN}
            onClick={(e) => {
              e.stopPropagation();
              void onDuplicate(r);
            }}
          >
            Duplicar
          </button>
          <button
            type="button"
            className={dsGhostBtn('danger')}
            onClick={(e) => {
              e.stopPropagation();
              void onDelete(r);
            }}
          >
            Excluir
          </button>
        </TableRowActions>
      ),
    },
  ];
}
