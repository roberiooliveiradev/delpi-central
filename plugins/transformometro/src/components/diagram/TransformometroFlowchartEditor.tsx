import { forwardRef, type ComponentProps } from "react";

import {
  FlowchartEditor as BaseFlowchartEditor,
  type FlowchartEditorHandle,
  type FlowchartEditorLabels,
} from "@delpi/plugin-ui/index";

import { TRANSFORMOMETRO_FLOWCHART_EDITOR_LABELS } from "../../content/flowchartEditorLabels";
import { useTransformometroDarkMode } from "../../hooks/useTransformometroDarkMode";
import { useConfirm } from "../ui/ConfirmDialogProvider";

export type { FlowchartEditorHandle };

type Props = Omit<
  ComponentProps<typeof BaseFlowchartEditor>,
  "labels" | "confirm" | "colorMode" | "shellClassName"
> & {
  labels?: FlowchartEditorLabels;
};

export const FlowchartEditor = forwardRef<FlowchartEditorHandle, Props>(function FlowchartEditor(
  { labels = TRANSFORMOMETRO_FLOWCHART_EDITOR_LABELS, ...props },
  ref
) {
  const confirm = useConfirm();
  const isDark = useTransformometroDarkMode();

  return (
    <BaseFlowchartEditor
      ref={ref}
      {...props}
      labels={labels}
      confirm={confirm}
      colorMode={isDark ? "dark" : "light"}
      shellClassName="dashboard-transformometro"
    />
  );
});
