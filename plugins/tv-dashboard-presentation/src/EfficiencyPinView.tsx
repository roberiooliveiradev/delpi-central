import type { CSSProperties } from "react";
import { ensureComunicadoDualClass } from "@delpi/plugin-ui/index";

import {
  resolveEfficiencyPinInfoMode,
  resolveEfficiencyPinRole,
  resolveEfficiencyPinState,
  type EfficiencyPinResolvedState,
} from "./efficiencyPin";
import type { ComunicadoDataResolved, ComunicadoShapeBlock } from "./comunicadoTypes";

type Props = {
  block: ComunicadoShapeBlock;
  /** Resolved da fonte ligada (editor: às vezes só no data_source). */
  resolved?: ComunicadoDataResolved | null;
  fontScale?: number;
};

function formatEfficiencyPct(pct: number): string {
  return `${pct.toLocaleString("pt-BR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  })}%`;
}

function EfficiencyPinLabelCard({
  state,
  fontScale = 1,
  fill = false,
}: {
  state: EfficiencyPinResolvedState;
  fontScale?: number;
  /** Preenche o frame (bloco info separado). */
  fill?: boolean;
}) {
  const labelFont = Math.max(12, Math.round((fill ? 16 : 13) * fontScale));
  const pctFont = Math.max(11, Math.round((fill ? 14 : 12) * fontScale));
  const style: CSSProperties = {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 2,
    padding: fill ? "8px 12px" : "3px 8px",
    borderRadius: 8,
    background: "rgba(15, 23, 42, 0.86)",
    color: "#f8fafc",
    lineHeight: 1.15,
    textAlign: "center",
    whiteSpace: "nowrap",
    boxShadow: "0 1px 4px rgba(0,0,0,0.35)",
    boxSizing: "border-box",
    ...(fill
      ? { width: "100%", height: "100%", maxWidth: "100%", whiteSpace: "normal" }
      : { maxWidth: "100%" }),
  };
  return (
    <div
      className={ensureComunicadoDualClass("tdp-comunicado__efficiency-pin__label")}
      style={style}
    >
      <span style={{ fontSize: labelFont, fontWeight: 700, wordBreak: "break-word" }}>
        {state.label}
      </span>
      <span
        className={ensureComunicadoDualClass("tdp-comunicado__efficiency-pin__pct")}
        style={{ fontSize: pctFont, fontWeight: 600, opacity: 0.95 }}
      >
        {state.efficiencyPct != null ? formatEfficiencyPct(state.efficiencyPct) : "—"}
      </span>
    </div>
  );
}

function EfficiencyPinRadar({ color }: { color: string }) {
  return (
    <svg
      className={ensureComunicadoDualClass("tdp-comunicado__efficiency-pin__radar")}
      viewBox="0 0 100 100"
      aria-hidden="true"
      preserveAspectRatio="xMidYMid meet"
      style={{
        display: "block",
        width: "100%",
        height: "100%",
        flex: "1 1 auto",
        minHeight: 0,
        overflow: "visible",
        filter: `drop-shadow(0 0 6px ${color})`,
      }}
    >
      <circle cx="50" cy="50" r="18" fill="none" stroke={color} strokeWidth="3" opacity="0.85">
        <animate attributeName="r" values="16;46" dur="2.2s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.85;0" dur="2.2s" repeatCount="indefinite" />
      </circle>
      <circle cx="50" cy="50" r="18" fill="none" stroke={color} strokeWidth="3" opacity="0.85">
        <animate
          attributeName="r"
          values="16;46"
          dur="2.2s"
          begin="1.1s"
          repeatCount="indefinite"
        />
        <animate
          attributeName="opacity"
          values="0.85;0"
          dur="2.2s"
          begin="1.1s"
          repeatCount="indefinite"
        />
      </circle>
      <circle cx="50" cy="50" r="14" fill={color} stroke="#ffffff" strokeWidth="2.5" />
      <circle cx="50" cy="50" r="6" fill="#ffffff" opacity="0.35" />
    </svg>
  );
}

export function EfficiencyPinView({ block, resolved, fontScale = 1 }: Props) {
  const state = resolveEfficiencyPinState(block, resolved);
  const role = resolveEfficiencyPinRole(block.efficiencyPin);
  const infoMode = resolveEfficiencyPinInfoMode(block.efficiencyPin);
  const titleParts = [
    state.workCenter || "CT",
    state.efficiencyPct != null ? formatEfficiencyPct(state.efficiencyPct) : "sem dados",
  ];

  if (role === "info") {
    return (
      <div
        className={ensureComunicadoDualClass(
          `tdp-comunicado__efficiency-pin tdp-comunicado__efficiency-pin--info tdp-comunicado__efficiency-pin--${state.status}`,
        )}
        style={{
          width: "100%",
          height: "100%",
          boxSizing: "border-box",
          pointerEvents: "none",
        }}
        title={titleParts.join(" · ")}
        role="img"
        aria-label={titleParts.join(", ")}
      >
        <EfficiencyPinLabelCard state={state} fontScale={fontScale} fill />
      </div>
    );
  }

  const showAttachedLabel = infoMode === "attached";

  return (
    <div
      className={ensureComunicadoDualClass(
        `tdp-comunicado__efficiency-pin tdp-comunicado__efficiency-pin--pin tdp-comunicado__efficiency-pin--${state.status}`,
      )}
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: showAttachedLabel ? 6 : 0,
        boxSizing: "border-box",
        padding: 4,
        pointerEvents: "none",
      }}
      title={titleParts.join(" · ")}
      role="img"
      aria-label={titleParts.join(", ")}
    >
      <div
        style={{
          flex: "1 1 auto",
          minHeight: 0,
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <EfficiencyPinRadar color={state.color} />
      </div>
      {showAttachedLabel ? (
        <EfficiencyPinLabelCard state={state} fontScale={fontScale} />
      ) : null}
    </div>
  );
}

/** @deprecated Prefer `EfficiencyPinView` — mantido para testes/preview isolados. */
export function EfficiencyPinGraphic({
  state,
  sizePx,
  showLabel,
  fontScale = 1,
}: {
  state: EfficiencyPinResolvedState;
  sizePx: number;
  showLabel: boolean;
  fontScale?: number;
}) {
  return (
    <div
      style={{
        width: sizePx,
        height: showLabel ? sizePx + 36 : sizePx,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 6,
      }}
    >
      <div style={{ width: sizePx, height: sizePx }}>
        <EfficiencyPinRadar color={state.color} />
      </div>
      {showLabel ? <EfficiencyPinLabelCard state={state} fontScale={fontScale} /> : null}
    </div>
  );
}
