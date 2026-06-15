import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import type { HTMLAttributes, ReactNode } from "react";

type LauncherPinnedGridProps = {
  className?: string;
  itemIds: readonly string[];
  animateList?: boolean;
  children: (itemId: string, index: number) => ReactNode;
} & Omit<HTMLAttributes<HTMLDivElement>, "children">;

export function LauncherPinnedGrid({
  className,
  itemIds,
  animateList = true,
  children,
  ...rest
}: LauncherPinnedGridProps) {
  const reduceMotion = useReducedMotion();

  if (!animateList || reduceMotion) {
    return (
      <div className={className} {...rest}>
        {itemIds.map((itemId, index) => (
          <div key={itemId} className="launcher-pinned-grid-item">
            {children(itemId, index)}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={className} {...rest}>
      <AnimatePresence mode="popLayout" initial={false}>
        {itemIds.map((itemId, index) => (
          <motion.div
            key={itemId}
            className="launcher-pinned-grid-item"
            layout={false}
            initial={{ opacity: 0, scale: 0.94, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.94, y: -6 }}
            transition={{
              duration: 0.28,
              ease: [0.22, 1, 0.36, 1],
              layout: { duration: 0.24, ease: [0.22, 1, 0.36, 1] },
            }}
          >
            {children(itemId, index)}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
