import type { ProductSalesReportPayload } from "../types";

export async function downloadProductSalesExcel(data: ProductSalesReportPayload): Promise<void> {
  const module = await import("exceljs");
  const ExcelJS = module.default ?? module;
  const book = new ExcelJS.Workbook();
  book.creator = "DELPI - Portal PCP";
  const decorate = (sheet: import("exceljs").Worksheet) => {
    sheet.getRow(1).font = { bold: true, color: { argb: "FFFFFFFF" } };
    sheet.getRow(1).fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FF003866" } };
    sheet.views = [{ state: "frozen", ySplit: 1 }];
    sheet.columns.forEach((column) => { column.width = 26; });
  };
  const summary = book.addWorksheet("Resumo");
  summary.addRow(["Indicador", "Valor"]);
  summary.addRows([
    ["Filial", data.branch], ["Produto", data.product.code],
    ["Descrição", data.product.description], ["Unidade", data.product.unit],
    ["Início", data.period.from], ["Fim", data.period.to], ["Meses", data.period.months],
    ["Volume líquido", data.summary.total_quantity],
    ["Faturado", data.summary.gross_quantity], ["Devolvido", data.summary.returned_quantity],
    ["Média semanal", data.summary.weekly_average],
    ["Média mensal", data.summary.monthly_average],
    ["Média anual equivalente", data.summary.yearly_average],
    ["Clientes", data.summary.customer_count], ["Meses com venda", data.summary.active_month_count],
    ["Fonte", data.source],
  ]);
  decorate(summary);
  const monthly = book.addWorksheet("Evolução mensal");
  monthly.addRow(["Mês", "Faturado", "Devolvido", "Líquido"]);
  data.monthly.forEach((r) => monthly.addRow([r.month, r.gross_quantity, r.returned_quantity, r.quantity]));
  decorate(monthly);
  const customers = book.addWorksheet("Clientes");
  customers.addRow(["Código", "Loja", "Cliente", "Faturado", "Devolvido", "Líquido"]);
  data.customers.forEach((r) => customers.addRow([
    r.customer_code, r.customer_store, r.customer_name,
    r.gross_quantity, r.returned_quantity, r.quantity,
  ]));
  decorate(customers);
  customers.getColumn(3).width = 48;
  const buffer = await book.xlsx.writeBuffer();
  const blob = new Blob([buffer], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "Raio-X-Produto-" + data.product.code + "-" + data.branch + "-" + data.period.months + "m.xlsx";
  anchor.click();
  URL.revokeObjectURL(url);
}
