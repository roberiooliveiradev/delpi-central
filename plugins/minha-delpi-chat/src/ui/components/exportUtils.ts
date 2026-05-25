import type { ChatPresentation } from "../../data/api/chatTypes";

type TablePresentation = Extract<ChatPresentation, { type: "table" }>;

export function exportToXlsx(presentation: TablePresentation) {
  import("xlsx").then((XLSX) => {
    const headers = presentation.columns.map((c) => c.label);
    const data = presentation.rows.map((row) =>
      presentation.columns.map((c) => row[c.key] ?? "")
    );

    const ws = XLSX.utils.aoa_to_sheet([headers, ...data]);

    const colWidths = presentation.columns.map((col) => {
      const maxLen = Math.max(
        col.label.length,
        ...presentation.rows.map((r) => String(r[col.key] ?? "").length)
      );
      return { wch: Math.min(maxLen + 2, 50) };
    });
    ws["!cols"] = colWidths;

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, presentation.title || "Dados");
    XLSX.writeFile(wb, `${sanitizeFilename(presentation.title || "dados")}.xlsx`);
  });
}

export function exportToPdf(presentation: TablePresentation) {
  Promise.all([
    import("jspdf"),
    import("jspdf-autotable"),
  ]).then(([{ jsPDF }, _autoTable]) => {
    const doc = new jsPDF({ orientation: "landscape" });

    doc.setFontSize(14);
    doc.text(presentation.title || "Dados", 14, 18);

    const headers = presentation.columns.map((c) => c.label);
    const body = presentation.rows.map((row) =>
      presentation.columns.map((c) => String(row[c.key] ?? ""))
    );

    (doc as any).autoTable({
      head: [headers],
      body,
      startY: 24,
      styles: { fontSize: 8 },
      headStyles: { fillColor: [14, 165, 233] },
    });

    doc.save(`${sanitizeFilename(presentation.title || "dados")}.pdf`);
  });
}

export function exportChartToPng(chartRef: HTMLDivElement | null, title: string) {
  if (!chartRef) return;
  const svg = chartRef.querySelector("svg");
  if (!svg) return;

  const clone = svg.cloneNode(true) as SVGElement;
  clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");

  const svgData = new XMLSerializer().serializeToString(clone);
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const img = new Image();
  img.onload = () => {
    canvas.width = img.width * 2;
    canvas.height = img.height * 2;
    ctx.scale(2, 2);
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);
    const link = document.createElement("a");
    link.download = `${sanitizeFilename(title)}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  };
  img.src = `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svgData)))}`;
}

function sanitizeFilename(name: string): string {
  return name
    .replace(/[^a-zA-Z0-9À-ÿ\s_-]/g, "")
    .replace(/\s+/g, "_")
    .slice(0, 60);
}
