import { useId } from "react";

type BrandMarkProps = {
  className?: string;
  /** `dark` = branco/ciano no kiosk; `brand` = navy/ciano da marca. */
  tone?: "dark" | "brand";
};

/**
 * Marca Minha DELPI para splash (swoosh + wordmark tipográfico).
 * Fills adaptados ao tom do fundo (kiosk vs. brand).
 */
export function BrandMark({ className, tone = "dark" }: BrandMarkProps) {
  const gradientId = `delpi-ui-brand-mark-${useId().replace(/:/g, "")}`;
  const swoosh = tone === "dark" ? "#30b8ec" : "#089bdb";
  const swooshDeep = tone === "dark" ? "#089bdb" : "#013866";
  const word = tone === "dark" ? "#e8f4fb" : "#013866";
  const wordAccent = tone === "dark" ? "#30b8ec" : "#089bdb";

  return (
    <svg
      className={className}
      viewBox="0 0 320 200"
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={swooshDeep} />
          <stop offset="45%" stopColor={swoosh} />
          <stop offset="100%" stopColor={swooshDeep} />
        </linearGradient>
      </defs>
      <path
        d="M248 168C330 98 255 -18 138 58C248 -38 372 96 248 168Z"
        fill={`url(#${gradientId})`}
      />
      <text
        x="20"
        y="78"
        fill={wordAccent}
        fontFamily="system-ui, -apple-system, sans-serif"
        fontSize="28"
        fontWeight="700"
        letterSpacing="-0.02em"
      >
        minha
      </text>
      <text
        x="20"
        y="128"
        fill={word}
        fontFamily="system-ui, -apple-system, sans-serif"
        fontSize="36"
        fontWeight="800"
        letterSpacing="-0.03em"
      >
        delpi
      </text>
    </svg>
  );
}
