import { useEffect, useState } from "react";
import { BackLink, DocumentReaderToolbar } from "@delpi/plugin-ui/index";

import { downloadPackagePdf, getReport, type ReportDetail } from "../api/travelExpensesApi";
import { PackageDocumentView } from "../components/PackageDocumentView";
import { useReportReceiptPreviews } from "../hooks/useReportReceiptPreviews";
import { navigateTravel } from "../hooks/useTravelRouterPath";
import { TravelPageHeader, TravelPageNotices, TravelStateBox } from "../ui/travelUi";

export function PackagePage({ reportId }: { reportId: string }) {
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getReport(reportId)
      .then((detail) => {
        if (!cancelled) setReport(detail);
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reportId]);

  const receiptPreviews = useReportReceiptPreviews(reportId, report);

  async function onDownloadPdf() {
    try {
      const blob = await downloadPackagePdf(reportId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${report?.number || "prestacao"}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Não foi possível gerar o PDF do relatório. Tente novamente.",
      );
    }
  }

  return (
    <div className="te-page-stack">
      <TravelPageHeader
        title={report ? `Relatório ${report.number}` : "Relatório da prestação"}
        subtitle="Prévia para o financeiro — o envio fica para a próxima fase."
        nav={
          <BackLink onClick={() => navigateTravel(`/apps/travel-expenses/reports/${reportId}`)}>
            Voltar à ficha
          </BackLink>
        }
      />
      <TravelPageNotices error={error} onDismissError={() => setError(null)} />
      {loading || !report ? (
        <TravelStateBox variant="loading" title="Carregando" message="Montando o relatório…" />
      ) : (
        <PackageDocumentView
          report={report}
          receiptPreviews={receiptPreviews}
          toolbar={
            <DocumentReaderToolbar
              label="Relatório"
              printTitle={report.number}
              onDownloadPdf={onDownloadPdf}
            />
          }
        />
      )}
    </div>
  );
}
