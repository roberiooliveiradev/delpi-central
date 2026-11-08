import { exportTableExcel } from "@delpi/plugin-ui/index";
import type { InspecoesProcessoAuditoriaApontamentoItem } from "../types/api";

function statusLabel(row: InspecoesProcessoAuditoriaApontamentoItem): string {
  if (row.operador_inspecionou) return "Inspecionou";
  if (row.tem_inspecao_na_op_operacao || row.tem_inspecao_amarrada) return "Não inspecionou";
  return "Sem inspeção cadastrada";
}

export async function exportAuditWorkbook(
  items: InspecoesProcessoAuditoriaApontamentoItem[],
  branch: string,
  startDate: string,
  endDate: string,
): Promise<void> {
  await exportTableExcel(
    {
      title: "Auditoria de Inspeções de Processos",
      sheetName: "Apontamentos",
      headers: [
        "Filial", "Data produção", "Status", "Código operador", "Login", "Operador",
        "OP", "Produto", "Descrição", "Operação", "Centro trabalho", "Turno",
        "Início", "Final", "Qtd. apontamentos", "Inspeção exigível", "Operador inspecionou",
      ],
      rows: items.map((row) => [
        row.filial, row.data_producao ?? "", statusLabel(row), row.cod_operador,
        row.login_operador, row.nome_operador, row.op, row.produto, row.descricao_produto,
        row.operacao, row.centro_trabalho, row.turno_label ?? "", row.hora_inicio ?? "",
        row.hora_final ?? "", row.qtd_apontamentos,
        row.tem_inspecao_amarrada || row.tem_inspecao_na_op_operacao ? "Sim" : "Não",
        row.operador_inspecionou ? "Sim" : "Não",
      ]),
    },
    `auditoria-inspecoes-processo_filial-${branch}_${startDate}_${endDate}`,
  );
}
