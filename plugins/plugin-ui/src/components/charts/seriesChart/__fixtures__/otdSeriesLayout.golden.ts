/** Fixture canônica OTD — regressão de clipping/layout (sem depender do editor). */
export const OTD_SERIES_LAYOUT_GOLDEN = {
  name: "OTD — série temporal (golden layout)",
  viewW: 640,
  viewH: 320,
  categoryPaddingPercent: 3,
  showXAxisLabels: true,
  showXAxisTitle: false,
  points: [
    { label: "11/06/26", value: 42 },
    { label: "15/06/26", value: 58 },
    { label: "20/06/26", value: 71 },
    { label: "25/06/26", value: 66 },
    { label: "01/07/26", value: 88 },
    { label: "05/07/26", value: 94 },
    { label: "10/07/26", value: 100 },
  ],
} as const;
