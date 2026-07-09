import { FilePreviewView, useFilePreviewLoader } from "@delpi/plugin-ui";

type Props = {
  file: File;
};

export function EvidenceLocalPreviewContent({ file }: Props) {
  const state = useFilePreviewLoader({
    source: file,
    mimeType: file.type,
    fileName: file.name,
  });

  return <FilePreviewView state={state} title={file.name} />;
}
