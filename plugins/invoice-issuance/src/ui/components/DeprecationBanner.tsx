import { DEPRECATION_BANNER } from "../../content/deprecationBanner";

/** Banner global de cutover — não remove o fluxo legado. */
export function DeprecationBanner() {
  return (
    <div
      className="ii-alert ii-deprecation-banner"
      role="status"
      data-testid={DEPRECATION_BANNER.testId}
    >
      <p>{DEPRECATION_BANNER.message}</p>
      <p className="ii-deprecation-banner__links">
        <a href={DEPRECATION_BANNER.primaryHref}>{DEPRECATION_BANNER.primaryLabel}</a>
        {" · "}
        <a href={DEPRECATION_BANNER.createHref}>{DEPRECATION_BANNER.createLabel}</a>
      </p>
    </div>
  );
}
