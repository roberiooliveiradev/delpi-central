import { Database } from "lucide-react";

type TotvsSourceBannerProps = {
  description?: string;
};

export function TotvsSourceBanner({
  description = "Consulta analítica de não conformidades.",
}: TotvsSourceBannerProps) {
  return (
    <div className="dq-totvs-banner" role="note">
      <Database size={18} aria-hidden="true" />
      <div>
        <strong>Origem: TOTVS Protheus</strong>
        <p>{description}</p>
      </div>
    </div>
  );
}
