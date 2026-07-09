type Props = {
  items: Array<string | null | undefined>;
  className?: string;
};

/** Rodapé canônico de metadados (tipo, tamanho, data). */
export function FilePreviewMetaFooter({ items, className }: Props) {
  const visible = items.map((item) => item?.trim()).filter(Boolean) as string[];

  if (!visible.length) {
    return null;
  }

  return (
    <div className={["delpi-ui-file-preview__meta", className].filter(Boolean).join(" ")}>
      {visible.map((item) => (
        <span key={item}>{item}</span>
      ))}
    </div>
  );
}
