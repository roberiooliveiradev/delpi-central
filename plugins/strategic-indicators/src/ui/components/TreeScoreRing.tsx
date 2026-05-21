import type { ScoreStatusVariant } from "../shared/scoreVariant";
import "./TreeScoreRing.css";

type TreeScoreRingProps = {
  score: number;
  max?: number;
  label?: string;
  tone: ScoreStatusVariant | "igd" | "scope" | "empty";
  size?: number;
};

export function TreeScoreRing({
  score,
  max = 10,
  label = "IDD",
  tone,
  size = 72,
}: TreeScoreRingProps) {
  const radius = (size - 10) / 2;
  const circumference = 2 * Math.PI * radius;
  const safeScore = Number.isFinite(score) ? Math.max(0, Math.min(score, max)) : 0;
  const progress = safeScore / max;
  const offset = circumference * (1 - progress);
  const center = size / 2;

  return (
    <div
      className={`si-tree-ring si-tree-ring--${tone}`}
      style={{ width: size, height: size }}
      aria-hidden
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          className="si-tree-ring__track"
          cx={center}
          cy={center}
          r={radius}
        />
        <circle
          className="si-tree-ring__progress"
          cx={center}
          cy={center}
          r={radius}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="si-tree-ring__label">
        <span>{label}</span>
        <strong>{safeScore.toFixed(1)}</strong>
      </div>
    </div>
  );
}
