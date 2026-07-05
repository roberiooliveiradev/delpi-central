import { useEffect, useMemo, useState } from "react";

import type { PresentationPayload } from "../api/tvDashboardApi";
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

function NativeSlide({ native }: NonNullable<PresentationPayload["slides"][0]["native"]>) {
  const data = native.data;
  if (native.screenKey === "production_oee_overview") {
    return (
      <div className="tdp-native-screen tdp-oee">
        <header className="tdp-oee__header">
          <p className="tdp-oee__eyebrow">Produção</p>
          <h1 className="tdp-oee__title">OEE — visão geral</h1>
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
      </div>
    );
  }
  if (native.screenKey === "custom_message") {
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
  const [payload, setPayload] = useState(initial);
  const [index, setIndex] = useState(0);
  const slides = useMemo(
    () => [...payload.slides].sort((a, b) => a.sortOrder - b.sortOrder),
    [payload.slides],
  );
  const current = slides[index];
  const viewport = payload.playlist.viewportProfile || "1080p";

  useEffect(() => setPayload(initial), [initial]);

  useEffect(() => {
    if (!slides.length) return;
    const durationMs =
      (current?.durationSec ?? payload.playlist.defaultDurationSec ?? 30) * 1000;
    const timer = window.setTimeout(() => {
      setIndex((prev) => (prev + 1) % slides.length);
    }, durationMs);
    return () => window.clearTimeout(timer);
  }, [slides.length, index, current, payload.playlist.defaultDurationSec]);

  useEffect(() => {
    const refreshSec = payload.playlist.globalRefreshSec || 300;
    const timer = window.setInterval(() => {
      if (!onRefresh) return;
      void onRefresh().then((next) => setPayload(next));
    }, refreshSec * 1000);
    return () => window.clearInterval(timer);
  }, [onRefresh, payload.playlist.globalRefreshSec]);

  if (!slides.length) {
    return (
      <div className="tdp-stage" data-viewport={viewport}>
        <div className="tdp-empty">Nenhuma tela configurada.</div>
      </div>
    );
  }

  return (
    <div className="tdp-stage" data-viewport={viewport}>
      <div className="tdp-preview-badge">Pré-visualização</div>
      {slides.map((slide, slideIndex) => {
        const active = slideIndex === index;
        return (
          <div
            key={slide.id}
            className={`tdp-slide${active ? " tdp-slide--active" : ""}`}
            aria-hidden={!active}
          >
            {slide.slideType === "native" && slide.native ? (
              <NativeSlide native={slide.native} />
            ) : (
              <iframe
                className="tdp-external-frame"
                src={slide.external?.url}
                title={slide.title}
                sandbox={slide.external?.sandbox ?? undefined}
                allow="fullscreen"
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
