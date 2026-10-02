import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { downloadReceivedInvoiceDanfe, receivedInvoiceDanfePath, receivedInvoicesPath } from "../api/financialApi";
import { configureHttpClient, filenameFromContentDisposition, httpGetBlob } from "../api/httpClient";
import { copy } from "../content/copy";
import { InvoicesPage } from "../pages/InvoicesPage";
import type { ReceivedInvoicesPayload } from "../types";
import { invoiceSearchHref } from "../utils/invoiceFilters";

const harness = vi.hoisted(() => ({
  data: null as ReceivedInvoicesPayload | null,
  loading: true,
  error: null as string | null,
}));

vi.mock("../hooks/useReceivedInvoices", () => ({
  useReceivedInvoices: () => ({
    data: harness.data,
    loading: harness.loading,
    error: harness.error,
    reload: () => undefined,
  }),
}));

const ACCESS_KEY = "3".repeat(44);
const DOCUMENT_ID = "aabbccddeeff001122334455";

function payload(danfeAvailable: boolean): ReceivedInvoicesPayload {
  return {
    filters: { invoiceNumber: "22844", value: null, supplierCnpj: null },
    pagination: {
      page: 2,
      pageSize: 25,
      totalItems: 40,
      totalPages: 2,
      hasNext: false,
      hasPrevious: true,
      isComplete: true,
    },
    items: [
      {
        documentId: DOCUMENT_ID,
        accessKey: ACCESS_KEY,
        invoiceNumber: "22844",
        series: "1",
        issuerName: "FLORICULTURA FLORISA LTDA EPP",
        issuerCnpj: "04252011000110",
        receiverName: "DELPI COMPONENTES LTDA",
        emissionAt: "2026-09-30T21:40:44Z",
        amount: "108",
        amountFormatted: "R$ 108,00",
        manifestationCode: "4",
        manifestationDescription: "Ciência da Operação",
        danfeAvailable,
        branchCode: "01",
      },
    ],
  };
}

function renderPage() {
  return renderToStaticMarkup(
    <InvoicesPage
      branch="01"
      invoiceNumber="22844"
      invoiceValue={null}
      supplierCnpj={null}
      page={2}
    />,
  );
}

describe("invoice search", () => {
  it("sends applied filters to the financial-api and resets the page", () => {
    expect(
      invoiceSearchHref({
        branch: "01",
        invoiceNumber: " 22844 ",
        invoiceValue: "108,00",
        supplierCnpj: "04.252.011/0001-10",
      }),
    ).toBe(
      "/apps/financial/invoices?branch=01&invoiceNumber=22844&invoiceValue=108%2C00&supplierCnpj=04.252.011%2F0001-10",
    );
    const path = receivedInvoicesPath({
      invoiceNumber: "22844",
      invoiceValue: "108,00",
      supplierCnpj: "04252011000110",
      page: 1,
    });
    expect(path.startsWith("/invoices/received?")).toBe(true);
    expect(path).toContain("invoiceNumber=22844");
    expect(path).toContain("value=108");
    expect(path).not.toContain("supplierName");
    expect(path).not.toContain("questor");
  });
});

describe("InvoicesPage", () => {
  it("shows the loading state without a supplier-name filter", () => {
    harness.loading = true;
    harness.error = null;
    harness.data = null;
    const html = renderPage();
    expect(html).toContain(copy.invoices.loading);
    expect(html).toContain(copy.invoices.title);
    expect(html).toContain("Número da NF");
    expect(html).toContain("CNPJ fornecedor");
    expect(html).not.toContain("Nome do fornecedor");
    expect(html).not.toContain("questorpublico");
    expect(html).not.toContain("showBranchSelector");
  });

  it("shows the empty state", () => {
    harness.loading = false;
    harness.error = null;
    harness.data = { ...payload(true), items: [], pagination: { ...payload(true).pagination, totalItems: 0 } };
    expect(renderPage()).toContain(copy.invoices.empty);
  });

  it("shows the error state", () => {
    harness.loading = false;
    harness.error = "Falha controlada";
    harness.data = null;
    const html = renderPage();
    expect(html).toContain("Falha controlada");
    expect(html).not.toContain("FLORICULTURA FLORISA LTDA EPP");
  });

  it("renders the invoice, pagination and an enabled DANFE action", () => {
    harness.loading = false;
    harness.error = null;
    harness.data = payload(true);
    const html = renderPage();
    expect(html).toContain("22844");
    expect(html).toContain("FLORICULTURA FLORISA LTDA EPP");
    expect(html).toContain("04.252.011/0001-10");
    expect(html).toContain("R$ 108,00");
    expect(html).toContain("Visualizar");
    expect(html).toContain("Baixar DANFE");
    expect(html).toContain("26–40 de 40");
    const action = html.match(/<button[^>]*>[\s\S]*?Baixar DANFE[\s\S]*?<\/button>/);
    expect(action?.[0] ?? "").not.toContain("disabled");
    expect(html).toContain(ACCESS_KEY);
  });

  it("disables DANFE when the provider says it is unavailable", () => {
    harness.loading = false;
    harness.error = null;
    harness.data = payload(false);
    const html = renderPage();
    const action = html.match(/<button[^>]*>[\s\S]*?DANFE não disponível[\s\S]*?<\/button>/);
    expect(action?.[0] ?? "").toContain("disabled");
  });
});

describe("DANFE download", () => {
  it("calls the financial-api blob endpoint and never the Questor host", async () => {
    const requests: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        requests.push(url);
        return new Response(new Uint8Array([0x25, 0x50, 0x44, 0x46]), {
          status: 200,
          headers: { "Content-Disposition": `attachment; filename="NFe-${ACCESS_KEY}.pdf"` },
        });
      }),
    );
    configureHttpClient(() => "portal-jwt");
    const downloaded = await httpGetBlob(
      `http://localhost/apps/financial-api${receivedInvoiceDanfePath(DOCUMENT_ID, ACCESS_KEY)}`,
    );
    expect(downloaded.filename).toBe(`NFe-${ACCESS_KEY}.pdf`);
    expect(requests[0]).toContain("/apps/financial-api/invoices/received/");
    expect(requests[0]).toContain(DOCUMENT_ID);
    expect(requests[0]).not.toContain("questorpublico");
    expect(requests[0]).not.toContain("entrarcomtoken");

    const clicks: string[] = [];
    vi.stubGlobal("document", {
      body: { appendChild: () => undefined },
      createElement: () => ({
        href: "",
        download: "",
        rel: "",
        click() {
          clicks.push(this.download);
        },
        remove() {
          return undefined;
        },
      }),
    });
    vi.stubGlobal("URL", {
      createObjectURL: () => "blob:financial-api",
      revokeObjectURL: () => undefined,
    });
    await downloadReceivedInvoiceDanfe(DOCUMENT_ID, ACCESS_KEY);
    expect(clicks).toEqual([`NFe-${ACCESS_KEY}.pdf`]);
    expect(requests.every((url) => !url.includes("questorpublico"))).toBe(true);
    vi.unstubAllGlobals();
  });

  it("reads the filename from Content-Disposition", () => {
    expect(filenameFromContentDisposition('attachment; filename="NFe-1.pdf"')).toBe("NFe-1.pdf");
  });
});

describe("invoice sources", () => {
  it("does not offer a supplier-name search or a direct Questor call", () => {
    const root = join(dirname(fileURLToPath(import.meta.url)), "..");
    const page = readFileSync(join(root, "pages/InvoicesPage.tsx"), "utf8");
    const api = readFileSync(join(root, "api/financialApi.ts"), "utf8");
    const client = readFileSync(join(root, "api/httpClient.ts"), "utf8");
    expect(page).toContain("showBranchSelector={false}");
    expect(page).toContain("hideSearch");
    expect(page).not.toContain("supplierName");
    expect(page).not.toContain("questorpublico");
    expect(api).not.toContain("questorpublico");
    expect(client).not.toContain("questorpublico");
    expect(page).not.toContain("onChange={(event) => replaceFinancialQuery");
    expect(page).toContain("FilePreviewModal");
    expect(page).toContain("fetchReceivedInvoiceDanfe");
    expect(page).not.toContain("window.open");
  });
});
