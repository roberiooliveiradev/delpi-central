import { buildDeliveryMapExportFileName } from "./deliveryMapExportFileName";

export const deliveryMapPublicCopy = {
  exportLabel: "Excel",
  exportBusy: "Exportando…",
  exportFileName: buildDeliveryMapExportFileName,
  exportSheetTitle: "Mapa de entrega",
  exportEmpty: "Não há OPs para exportar em Excel.",
  excelColumns: [
    { key: "numero", label: "NUMERO" },
    { key: "produto", label: "PRODUTO" },
    { key: "due", label: "DT. PREVISTA" },
    { key: "planned", label: "QUANT. ORIGINAL" },
    { key: "pending", label: "SALDO A ENTREGAR" },
    { key: "mpOk", label: "MP-OK" },
    { key: "feedback", label: "FEEDBACK" },
    { key: "obs", label: "OBSERVAÇÕES" },
  ],
} as const;
