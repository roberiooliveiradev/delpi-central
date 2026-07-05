import type { PublicSlideNative } from "./api";
import "./native-screens.css";

type KpiScreenData = {
  label?: string;
  startDate?: string;
  endDate?: string;
  branch?: string | null;
  error?: boolean;
  message?: string;
};

function formatPct(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") return "—";
  const num = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(num)) return String(value);
  return `${num.toFixed(1)}%`;
}

function formatNumber(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") return "—";
  const num = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(num)) return String(value);
  return num.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}

function ErrorScreen({ message }: { message?: string }) {
  return (
    <div className="tdp-native-screen tdp-native-screen--error">
      <p>{message ?? "Dados indisponíveis."}</p>
    </div>
  );
}

function KpiDualScreen({
  data,
  eyebrow,
  primaryLabel,
  primaryValue,
  secondaryLabel,
  secondaryValue,
}: {
  data: KpiScreenData;
  eyebrow: string;
  primaryLabel: string;
  primaryValue: string;
  secondaryLabel: string;
  secondaryValue: string;
}) {
  if (data.error) return <ErrorScreen message={data.message} />;
  return (
    <div className="tdp-native-screen tdp-oee">
      <header className="tdp-oee__header">
        <p className="tdp-oee__eyebrow">{eyebrow}</p>
        <h1 className="tdp-oee__title">{data.label ?? primaryLabel}</h1>
        <p className="tdp-oee__period">
          {data.startDate && data.endDate ? `${data.startDate} → ${data.endDate}` : ""}
          {data.branch ? ` · Filial ${data.branch}` : " · Consolidado"}
        </p>
      </header>
      <div className="tdp-oee__grid">
        <article className="tdp-oee__kpi tdp-oee__kpi--primary">
          <span className="tdp-oee__kpi-label">{primaryLabel}</span>
          <strong className="tdp-oee__kpi-value">{primaryValue}</strong>
        </article>
        <article className="tdp-oee__kpi">
          <span className="tdp-oee__kpi-label">{secondaryLabel}</span>
          <strong className="tdp-oee__kpi-value">{secondaryValue}</strong>
        </article>
      </div>
      <footer className="tdp-oee__footer">
        <span>Minha DELPI · Painéis TV</span>
      </footer>
    </div>
  );
}

export function ProductionOeeOverviewScreen({
  data,
}: {
  data: KpiScreenData & { oeePct?: unknown; targetPct?: unknown };
}) {
  return (
    <KpiDualScreen
      data={data}
      eyebrow="Produção"
      primaryLabel="OEE"
      primaryValue={formatPct(data.oeePct as number | string | null | undefined)}
      secondaryLabel="Meta"
      secondaryValue={formatPct(data.targetPct as number | string | null | undefined)}
    />
  );
}

export function ProductionOtdSummaryScreen({
  data,
}: {
  data: KpiScreenData & { otdPct?: unknown; targetPct?: unknown };
}) {
  return (
    <KpiDualScreen
      data={data}
      eyebrow="Produção"
      primaryLabel="OTD"
      primaryValue={formatPct(data.otdPct as number | string | null | undefined)}
      secondaryLabel="Meta"
      secondaryValue={formatPct(data.targetPct as number | string | null | undefined)}
    />
  );
}

export function QualityPpmSummaryScreen({
  data,
}: {
  data: KpiScreenData & { ppmValue?: unknown; targetPct?: unknown; ppmType?: string };
}) {
  return (
    <KpiDualScreen
      data={data}
      eyebrow="Qualidade"
      primaryLabel={`PPM ${data.ppmType ?? ""}`.trim()}
      primaryValue={formatNumber(data.ppmValue as number | string | null | undefined)}
      secondaryLabel="Meta"
      secondaryValue={formatPct(data.targetPct as number | string | null | undefined)}
    />
  );
}

export function SuppliesStockValueScreen({
  data,
}: {
  data: KpiScreenData & { stockValue?: unknown; currency?: string };
}) {
  if (data.error) return <ErrorScreen message={data.message} />;
  return (
    <div className="tdp-native-screen tdp-oee">
      <header className="tdp-oee__header">
        <p className="tdp-oee__eyebrow">Suprimentos</p>
        <h1 className="tdp-oee__title">{data.label ?? "Valor de estoque"}</h1>
        <p className="tdp-oee__period">{data.branch ? `Filial ${data.branch}` : "Consolidado"}</p>
      </header>
      <div className="tdp-oee__grid tdp-oee__grid--single">
        <article className="tdp-oee__kpi tdp-oee__kpi--primary">
          <span className="tdp-oee__kpi-label">Valor</span>
          <strong className="tdp-oee__kpi-value tdp-oee__kpi-value--compact">
            {formatNumber(data.stockValue as number | string | null | undefined)}
          </strong>
        </article>
      </div>
      <footer className="tdp-oee__footer">
        <span>Minha DELPI · Painéis TV</span>
      </footer>
    </div>
  );
}

export function CustomMessageScreen({
  data,
}: {
  data: { headline?: string; subtitle?: string };
}) {
  return (
    <div className="tdp-native-screen tdp-message">
      <div className="tdp-message__inner">
        <h1>{data.headline ?? "Comunicado"}</h1>
        {data.subtitle ? <p>{data.subtitle}</p> : null}
      </div>
    </div>
  );
}

export function NativeSlideView({ native }: { native: PublicSlideNative }) {
  const key = native.screenKey;
  const data = native.data as Record<string, unknown>;
  if (key === "production_oee_overview") {
    return <ProductionOeeOverviewScreen data={data as KpiScreenData & { oeePct?: unknown; targetPct?: unknown }} />;
  }
  if (key === "production_otd_summary") {
    return <ProductionOtdSummaryScreen data={data as KpiScreenData & { otdPct?: unknown; targetPct?: unknown }} />;
  }
  if (key === "quality_ppm_summary") {
    return <QualityPpmSummaryScreen data={data as KpiScreenData & { ppmValue?: unknown; targetPct?: unknown; ppmType?: string }} />;
  }
  if (key === "supplies_stock_value") {
    return <SuppliesStockValueScreen data={data as KpiScreenData & { stockValue?: unknown; currency?: string }} />;
  }
  if (key === "custom_message") {
    return <CustomMessageScreen data={data as { headline?: string; subtitle?: string }} />;
  }
  return (
    <div className="tdp-native-screen tdp-native-screen--error">
      <p>Tela nativa não suportada: {key}</p>
    </div>
  );
}
