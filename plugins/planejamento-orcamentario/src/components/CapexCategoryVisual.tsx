import { useEffect, useState } from "react";

import { fetchCapexCategoryIconImageBlob } from "../api/budgetPlanningApi";
import { resolveCapexCategoryIcon } from "../utils/costCenterIcons";

type CapexCategoryVisualProps = {
  categoryId?: string | null;
  iconKey?: string | null;
  hasCustomIcon?: boolean;
  size?: number;
  className?: string;
  alt?: string;
};

/**
 * Exibe imagem customizada autenticada ou ícone Lucide de fallback.
 */
export function CapexCategoryVisual({
  categoryId,
  iconKey,
  hasCustomIcon = false,
  size = 22,
  className,
  alt = "",
}: CapexCategoryVisualProps) {
  const [src, setSrc] = useState<string | null>(null);
  const Icon = resolveCapexCategoryIcon(iconKey);

  useEffect(() => {
    if (!hasCustomIcon || !categoryId) {
      setSrc(null);
      return;
    }
    const controller = new AbortController();
    let objectUrl: string | null = null;
    fetchCapexCategoryIconImageBlob(categoryId, controller.signal)
      .then((blob) => {
        if (controller.signal.aborted) return;
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch(() => {
        if (!controller.signal.aborted) setSrc(null);
      });
    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [categoryId, hasCustomIcon]);

  if (src) {
    return (
      <img
        src={src}
        alt={alt}
        className={className}
        width={size}
        height={size}
        style={{ objectFit: "contain", borderRadius: 8 }}
      />
    );
  }

  return <Icon size={size} strokeWidth={1.75} className={className} aria-hidden={!alt} />;
}
