import { ArrowRight } from "lucide-react";
import { motion } from "framer-motion";
import type { ReactNode } from "react";

export const homeFadeUp = {
  hidden: { opacity: 0, y: 10 },
  show: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.22, delay: 0.04 * i },
  }),
};

type HomePanelHeaderProps = {
  title: string;
  hint?: string;
  actionLabel?: string;
  onAction?: () => void;
  badge?: ReactNode;
};

export function HomePanelHeader({
  title,
  hint,
  actionLabel,
  onAction,
  badge,
}: HomePanelHeaderProps) {
  return (
    <div className="home-panel-header">
      <div>
        <h3 className="home-panel-title">{title}</h3>
        {hint ? <p className="home-panel-hint">{hint}</p> : null}
      </div>
      {badge}
      {actionLabel && onAction ? (
        <button type="button" className="home-panel-action" onClick={onAction}>
          {actionLabel}
          <ArrowRight size={14} aria-hidden="true" />
        </button>
      ) : null}
    </div>
  );
}

type HomeSummaryCardProps = {
  icon: ReactNode;
  title: string;
  value: number | string;
  subtitle: string;
  onClick?: () => void;
  dataTour?: string;
  className?: string;
};

export function HomeSummaryCard({
  icon,
  title,
  value,
  subtitle,
  onClick,
  dataTour,
  className,
}: HomeSummaryCardProps) {
  return (
    <motion.button
      type="button"
      className={["home-summary-card", className].filter(Boolean).join(" ")}
      data-tour={dataTour}
      onClick={onClick}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.98 }}
    >
      <span className="home-summary-icon">{icon}</span>

      <span className="home-summary-main">
        <span className="home-summary-title">{title}</span>
        <span className="home-summary-value">{value}</span>
        <span className="home-summary-sub">{subtitle}</span>
      </span>

      <span className="home-summary-arrow">
        <ArrowRight size={16} />
      </span>
    </motion.button>
  );
}
