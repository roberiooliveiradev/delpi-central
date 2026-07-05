import type { PublicSlideNative } from "./api";
import "./native-screens.css";

type OeeOverviewData = {
  oeePct?: number | string | null;
  targetPct?: number | string | null;
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

export function ProductionOeeOverviewScreen({ data }: { data: OeeOverviewData }) {
  if (data.error) {
    return (
      <div className="tdp-native-screen tdp-native-screen--error">
        <p>{data.message ?? "Dados indisponíveis."}</p>
      </div>
    );
  }

  return (
    <div className="tdp-native-screen tdp-oee">
      <header className="tdp-oee__header">
        <p className="tdp-oee__eyebrow">Produção</p>
        <h1 className="tdp-oee__title">{data.label ?? "OEE — visão geral"}</h1>
        <p className="tdp-oee__period">
          {data.startDate && data.endDate ? `${data.startDate} → ${data.endDate}` : ""}
          {data.branch ? ` · Filial ${data.branch}` : " · Consolidado"}
        </p>
      </header>
      <div className="tdp-oee__grid">
        <article className="tdp-oee__kpi tdp-oee__kpi--primary">
          <span className="tdp-oee__kpi-label">OEE</span>
          <strong className="tdp-oee__kpi-value">{formatPct(data.oeePct)}</strong>
        </article>
        <article className="tdp-oee__kpi">
          <span className="tdp-oee__kpi-label">Meta</span>
          <strong className="tdp-oee__kpi-value">{formatPct(data.targetPct)}</strong>
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
    return <ProductionOeeOverviewScreen data={data as OeeOverviewData} />;
  }
  if (key === "custom_message") {
    return (
      <CustomMessageScreen
        data={data as { headline?: string; subtitle?: string }}
      />
    );
  }
  return (
    <div className="tdp-native-screen tdp-native-screen--error">
      <p>Tela nativa não suportada: {key}</p>
    </div>
  );
}
