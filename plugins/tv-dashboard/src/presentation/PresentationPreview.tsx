import { usePresentationEngine, useFullscreenStage } from "@delpi/tv-dashboard-presentation";

import type { PresentationPayload } from "../api/tvDashboardApi";
import { ExternalSlidePreview } from "./ExternalSlidePreview";
import "../presentation/presentation.css";

type Props = {
  payload: PresentationPayload;
  onClose?: () => void;
  onRefresh?: () => Promise<PresentationPayload>;
};

function formatPct(value: unknown) {
  if (value === null || value === undefined || value === "") return "—";
  const num = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(num)) return String(value);
  return `${num.toFixed(1)}%`;
}

function formatNumber(value: unknown) {
  if (value === null || value === undefined || value === "") return "—";
  const num = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(num)) return String(value);
  return num.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}

function KpiDual({
  data,
  eyebrow,
  primaryLabel,
  primaryValue,
  secondaryLabel,
  secondaryValue,
}: {
  data: Record<string, unknown>;
  eyebrow: string;
  primaryLabel: string;
  primaryValue: string;
  secondaryLabel: string;
  secondaryValue: string;
}) {
  if (data.error) {
    return <div className="tdp-empty">{String(data.message ?? "Dados indisponíveis.")}</div>;
  }
  return (
    <div className="tdp-native-screen tdp-oee">
      <header className="tdp-oee__header">
        <p className="tdp-oee__eyebrow">{eyebrow}</p>
        <h1 className="tdp-oee__title">{String(data.label ?? primaryLabel)}</h1>
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
    </div>
  );
}

function NativeSlide({ native }: NonNullable<PresentationPayload["slides"][0]["native"]>) {
  const data = native.data;
  const key = native.screenKey;
  if (key === "production_oee_overview") {
    return (
      <KpiDual
        data={data}
        eyebrow="Produção"
        primaryLabel="OEE"
        primaryValue={formatPct(data.oeePct)}
        secondaryLabel="Meta"
        secondaryValue={formatPct(data.targetPct)}
      />
    );
  }
  if (key === "production_otd_summary") {
    return (
      <KpiDual
        data={data}
        eyebrow="Produção"
        primaryLabel="OTD"
        primaryValue={formatPct(data.otdPct)}
        secondaryLabel="Meta"
        secondaryValue={formatPct(data.targetPct)}
      />
    );
  }
  if (key === "quality_ppm_summary") {
    return (
      <KpiDual
        data={data}
        eyebrow="Qualidade"
        primaryLabel={`PPM ${String(data.ppmType ?? "")}`.trim()}
        primaryValue={formatNumber(data.ppmValue)}
        secondaryLabel="Meta"
        secondaryValue={formatPct(data.targetPct)}
      />
    );
  }
  if (key === "supplies_stock_value") {
    return (
      <div className="tdp-native-screen tdp-oee">
        <header className="tdp-oee__header">
          <p className="tdp-oee__eyebrow">Suprimentos</p>
          <h1 className="tdp-oee__title">{String(data.label ?? "Valor de estoque")}</h1>
        </header>
        <div className="tdp-oee__grid">
          <article className="tdp-oee__kpi tdp-oee__kpi--primary">
            <span className="tdp-oee__kpi-label">Valor</span>
            <strong className="tdp-oee__kpi-value">{formatNumber(data.stockValue)}</strong>
          </article>
        </div>
      </div>
    );
  }
  if (key === "custom_message") {
    return (
      <div className="tdp-native-screen tdp-message">
        <div className="tdp-message__inner">
          <h1>{String(data.headline ?? "Comunicado")}</h1>
          {data.subtitle ? <p>{String(data.subtitle)}</p> : null}
        </div>
      </div>
    );
  }
  return <div className="tdp-empty">Tela nativa não suportada.</div>;
}

export function PresentationPreview({ payload: initial, onRefresh }: Props) {
  const { ref, toggleFullscreen } = useFullscreenStage();
  const { index, slides, viewport, transition } = usePresentationEngine({
    initialPayload: initial,
    onRefresh,
    enableHiddenPause: false,
  });

  if (!slides.length) {
    return (
      <div className="tdp-stage" data-viewport={viewport}>
        <div className="tdp-empty">Nenhuma tela configurada.</div>
      </div>
    );
  }

  return (
    <div
      ref={ref}
      className="tdp-stage tdp-stage--preview-shell"
      data-viewport={viewport}
      onDoubleClick={() => void toggleFullscreen()}
    >
      <div className="tdp-preview-badge">Pré-visualização · duplo-clique = tela cheia</div>
      {slides.map((slide, slideIndex) => {
        const active = slideIndex === index;
        return (
          <div
            key={slide.id}
            className={`tdp-slide tdp-slide--${transition}${active ? " tdp-slide--active" : ""}`}
            aria-hidden={!active}
          >
            {slide.slideType === "native" && slide.native ? (
              <NativeSlide native={slide.native} />
            ) : (
              <ExternalSlidePreview
                url={slide.external?.url}
                title={slide.title}
                sandbox={slide.external?.sandbox}
                active={active}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
