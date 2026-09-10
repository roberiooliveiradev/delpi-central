import type { ReactNode } from "react";

type DetailStatusBannerProps = {
  variant?: "warning" | "error";
  title: string;
  message: ReactNode;
};

/** Banner leve de problema no detalhe (kit StateBox não expõe warning). */
export function DetailStatusBanner({
  variant = "warning",
  title,
  message,
}: DetailStatusBannerProps) {
  return (
    <div
      className={`pp-detail-status-banner pp-detail-status-banner--${variant}`}
      role={variant === "error" ? "alert" : "status"}
    >
      <strong className="pp-detail-status-banner__title">{title}</strong>
      <p className="pp-detail-status-banner__message">{message}</p>
    </div>
  );
}
