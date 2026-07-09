import { ToolbarSelectField, type ToolbarSelectFieldProps } from "@delpi/plugin-ui";

export type ChatRichUxSelectProps = ToolbarSelectFieldProps;

/** Alias do chat — toolbar de apresentação rica (gráfico/tabela). */
export function ChatRichUxSelect(props: ChatRichUxSelectProps) {
  return <ToolbarSelectField {...props} />;
}
