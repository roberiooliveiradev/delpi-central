import type { CSSProperties } from "react";

import { comunicadoBackgroundCssProperties } from "./comunicadoBackgroundStyle";
import { ComunicadoBlockView } from "./comunicadoBlockView";
import { useComunicadoGoogleFonts } from "./comunicadoGoogleFonts";
import { hasRichComunicado, sortBlocksByZIndex, type ComunicadoScreenDataLike } from "./comunicadoHelpers";
import type { ComunicadoBackground } from "./comunicadoTypes";
import { formatNumber, formatPct } from "./nativeFormat";
import "./native-screens.css";

export type KpiScreenData = {
  label?: string;
  startDate?: string;
  endDate?: string;
  branch?: string | null;
  error?: boolean;
  message?: string;
};

export type NativeSlidePayload = {
  screenKey: string;
  config?: Record<string, unknown>;
  data: Record<string, unknown>;
};

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

export type StockAlertItem = {
  productCode?: string;
  description?: string;
  stockValue?: unknown;
  stockQuantity?: unknown;
};

export function SuppliesStockAlertScreen({
  data,
}: {
  data: KpiScreenData & { items?: StockAlertItem[]; itemLimit?: number };
}) {
  if (data.error) return <ErrorScreen message={data.message} />;
  const items = Array.isArray(data.items) ? data.items.slice(0, 6) : [];
  return (
    <div className="tdp-native-screen tdp-stock-alert">
      <header className="tdp-stock-alert__header">
        <p className="tdp-stock-alert__eyebrow">Suprimentos</p>
        <h1 className="tdp-stock-alert__title">{data.label ?? "Itens críticos de estoque"}</h1>
        <p className="tdp-stock-alert__period">
          {data.branch ? `Filial ${data.branch}` : "Consolidado"}
          {items.length ? ` · Top ${items.length}` : ""}
        </p>
      </header>
      <div className="tdp-stock-alert__grid">
        {items.length === 0 ? (
          <p className="tdp-stock-alert__empty">Nenhum item crítico encontrado.</p>
        ) : (
          items.map((item, index) => (
            <article key={`${item.productCode ?? index}`} className="tdp-stock-alert__card">
              <span className="tdp-stock-alert__rank">{index + 1}</span>
              <div className="tdp-stock-alert__copy">
                <strong className="tdp-stock-alert__code">{item.productCode ?? "—"}</strong>
                <p className="tdp-stock-alert__desc">{item.description ?? "—"}</p>
              </div>
              <div className="tdp-stock-alert__metrics">
                <span className="tdp-stock-alert__metric-label">Valor</span>
                <strong>{formatNumber(item.stockValue as number | string | null | undefined)}</strong>
              </div>
            </article>
          ))
        )}
      </div>
      <footer className="tdp-oee__footer">
        <span>Minha DELPI · Painéis TV</span>
      </footer>
    </div>
  );
}

export function StrategicIndicatorsHeroScreen({
  data,
}: {
  data: KpiScreenData & {
    igd?: unknown;
    classification?: string;
    trendLabel?: string;
    bestDepartment?: string;
    primaryRisk?: string;
    competence?: string;
  };
}) {
  if (data.error) return <ErrorScreen message={data.message} />;
  return (
    <div className="tdp-native-screen tdp-si-hero">
      <header className="tdp-si-hero__header">
        <p className="tdp-si-hero__eyebrow">Indicadores estratégicos</p>
        <h1 className="tdp-si-hero__title">{data.label ?? "Índice Global Delpi"}</h1>
        <p className="tdp-si-hero__period">
          {data.competence ? `Competência ${data.competence}` : "Competência atual"}
          {data.branch ? ` · Filial ${data.branch}` : " · Consolidado"}
        </p>
      </header>
      <div className="tdp-si-hero__headline">
        <div className="tdp-si-hero__igd-block">
          <span className="tdp-si-hero__igd-label">IGD</span>
          <strong className="tdp-si-hero__igd-value">
            {formatNumber(data.igd as number | string | null | undefined)}
          </strong>
          <p className="tdp-si-hero__classification">{data.classification ?? "—"}</p>
        </div>
        <article className="tdp-si-hero__trend">
          <span className="tdp-si-hero__chip-label">Tendência</span>
          <strong>{data.trendLabel ?? "—"}</strong>
        </article>
      </div>
      <div className="tdp-si-hero__highlights">
        <article className="tdp-si-hero__highlight">
          <span className="tdp-si-hero__chip-label">Destaque</span>
          <strong>{data.bestDepartment ?? "—"}</strong>
        </article>
        <article className="tdp-si-hero__highlight">
          <span className="tdp-si-hero__chip-label">Atenção</span>
          <strong>{data.primaryRisk ?? "—"}</strong>
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
  data: ComunicadoScreenDataLike & { background?: ComunicadoBackground };
}) {
  if (hasRichComunicado(data)) {
    return <RichComunicadoScreen data={data} />;
  }
  return (
    <div className="tdp-native-screen tdp-message">
      <div className="tdp-message__inner">
        <h1>{data.headline ?? "Título"}</h1>
        {data.subtitle ? <p>{data.subtitle}</p> : null}
      </div>
    </div>
  );
}

function RichComunicadoScreen({
  data,
}: {
  data: ComunicadoScreenDataLike & { background?: ComunicadoBackground };
}) {
  useComunicadoGoogleFonts({ blocks: data.blocks });

  const background = data.background ?? { type: "color", value: "#0f172a" };
  const imageUrl =
    background.type === "image" ? background.url ?? background.value : undefined;
  const bgStyle: CSSProperties = comunicadoBackgroundCssProperties(background, imageUrl);

  const blocks = sortBlocksByZIndex(data.blocks ?? []);

  return (
    <div className="tdp-native-screen tdp-comunicado" style={bgStyle}>
      <div className="tdp-comunicado__stage">
        {blocks.map((block) => (
          <ComunicadoBlockView key={block.id} block={block} />
        ))}
      </div>
    </div>
  );
}

export function NativeSlideView({ native }: { native: NativeSlidePayload }) {
  const key = native.screenKey;
  const data = native.data as Record<string, unknown>;
  if (key === "production_oee_overview") {
    return (
      <ProductionOeeOverviewScreen
        data={data as KpiScreenData & { oeePct?: unknown; targetPct?: unknown }}
      />
    );
  }
  if (key === "production_otd_summary") {
    return (
      <ProductionOtdSummaryScreen
        data={data as KpiScreenData & { otdPct?: unknown; targetPct?: unknown }}
      />
    );
  }
  if (key === "quality_ppm_summary") {
    return (
      <QualityPpmSummaryScreen
        data={
          data as KpiScreenData & {
            ppmValue?: unknown;
            targetPct?: unknown;
            ppmType?: string;
          }
        }
      />
    );
  }
  if (key === "supplies_stock_value") {
    return (
      <SuppliesStockValueScreen
        data={data as KpiScreenData & { stockValue?: unknown; currency?: string }}
      />
    );
  }
  if (key === "supplies_stock_alert") {
    return (
      <SuppliesStockAlertScreen
        data={data as KpiScreenData & { items?: StockAlertItem[]; itemLimit?: number }}
      />
    );
  }
  if (key === "strategic_indicators_hero") {
    return (
      <StrategicIndicatorsHeroScreen
        data={
          data as KpiScreenData & {
            igd?: unknown;
            classification?: string;
            trendLabel?: string;
            bestDepartment?: string;
            primaryRisk?: string;
            competence?: string;
          }
        }
      />
    );
  }
  if (key === "custom_message") {
    return (
      <CustomMessageScreen
        data={
          data as ComunicadoScreenDataLike & {
            background?: ComunicadoBackground;
          }
        }
      />
    );
  }
  return (
    <div className="tdp-native-screen tdp-native-screen--error">
      <p>Tela nativa não suportada: {key}</p>
    </div>
  );
}
