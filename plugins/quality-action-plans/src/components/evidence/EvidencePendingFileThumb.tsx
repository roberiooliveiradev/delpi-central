import { FileSpreadsheet, FileText, Image as ImageIcon } from "lucide-react";
import { useEffect, useState } from "react";

import { resolveLocalFilePreviewMode } from "./evidencePreviewUtils";

type Props = {
  file: File;
  className?: string;
};

export function EvidencePendingFileThumb({ file, className = "" }: Props) {
  const [thumbUrl, setThumbUrl] = useState<string | null>(null);
  const mode = resolveLocalFilePreviewMode(file);

  useEffect(() => {
    if (mode !== "image") {
      setThumbUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setThumbUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file, mode]);

  const iconClass = `pac-evidence-pending-thumb${className ? ` ${className}` : ""}`;

  if (mode === "image" && thumbUrl) {
    return (
      <div className={iconClass}>
        <img src={thumbUrl} alt="" className="pac-evidence-pending-thumb__image" />
      </div>
    );
  }

  if (mode === "pdf") {
    return (
      <div className={`${iconClass} pac-evidence-pending-thumb--pdf`} aria-hidden="true">
        <FileText size={18} />
      </div>
    );
  }

  if (file.name.toLowerCase().match(/\.xlsx?$/)) {
    return (
      <div className={`${iconClass} pac-evidence-pending-thumb--sheet`} aria-hidden="true">
        <FileSpreadsheet size={18} />
      </div>
    );
  }

  return (
    <div className={`${iconClass} pac-evidence-pending-thumb--generic`} aria-hidden="true">
      <ImageIcon size={18} />
    </div>
  );
}
