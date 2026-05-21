import type { DepartmentTreeSparkPoint } from "../../data/types/departmentTree";
import { PresentationDepartmentSparkline } from "./PresentationDepartmentSparkline";
import "./TreeSparkline.css";

type TreeSparklineProps = {
  points: DepartmentTreeSparkPoint[];
  direction?: "up" | "down" | "stable";
  height?: number;
  label?: string;
};

export function TreeSparkline({
  points,
  direction = "stable",
  height = 52,
  label = "Evolução",
}: TreeSparklineProps) {
  return (
    <div className="si-tree-sparkline">
      <span className="si-tree-sparkline__label">{label}</span>
      <PresentationDepartmentSparkline
        points={points}
        direction={direction}
        height={height}
        compact
      />
    </div>
  );
}
