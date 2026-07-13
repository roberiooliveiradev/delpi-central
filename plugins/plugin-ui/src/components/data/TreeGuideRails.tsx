/**
 * Trilhos pontilhados suaves para árvores hierárquicas (estilo explorador de arquivos).
 * O consumidor passa o caminho de «é o último irmão?» por nível para cortar a linha vertical.
 */

export type TreeGuideRailsProps = {
  /** Profundidade do nó (0 = raiz). */
  depth: number;
  /**
   * Para cada nível ancestral (índice 0 = primeiro filho da raiz),
   * `true` se aquele ancestral era o último irmão — evita continuar a linha vertical.
   * Comprimento deve ser `depth`.
   */
  isLastSiblingPath?: readonly boolean[];
  className?: string;
};

export function TreeGuideRails({
  depth,
  isLastSiblingPath = [],
  className,
}: TreeGuideRailsProps) {
  if (depth <= 0) return null;

  const slots = Array.from({ length: depth }, (_, level) => {
    const isElbow = level === depth - 1;
    const isLast = Boolean(isLastSiblingPath[level]);
    const classes = ["delpi-ui-tree-guides__slot"];
    if (isElbow) {
      classes.push(isLast ? "delpi-ui-tree-guides__slot--corner" : "delpi-ui-tree-guides__slot--tee");
    } else if (isLast) {
      classes.push("delpi-ui-tree-guides__slot--blank");
    } else {
      classes.push("delpi-ui-tree-guides__slot--vline");
    }
    return <span key={level} className={classes.join(" ")} />;
  });

  return (
    <span
      className={["delpi-ui-tree-guides", className].filter(Boolean).join(" ")}
      aria-hidden="true"
    >
      {slots}
    </span>
  );
}
