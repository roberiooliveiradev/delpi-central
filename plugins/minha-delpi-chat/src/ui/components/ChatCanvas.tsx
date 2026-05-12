import { Maximize2, X } from "lucide-react";

import { DataTable, type DataTableColumn } from "./DataTable";
import "./ChatCanvas.css";

type ChatCanvasTable = {
  type: "table";
  title: string;
  columns: DataTableColumn[];
  rows: Record<string, unknown>[];
};

type ChatCanvasJson = {
  type: "json";
  title: string;
  data: unknown;
};

export type ChatCanvasContent = ChatCanvasTable | ChatCanvasJson;

type ChatCanvasProps = {
  content?: ChatCanvasContent | null;
  onClose?: () => void;
};

export function ChatCanvas({ content, onClose }: ChatCanvasProps) {
  if (!content) {
    return null;
  }

  return (
    <aside className="mdc-chat-canvas" aria-label="Lousa do Chat DELPI">
      <header className="mdc-chat-canvas__header">
        <div>
          <p className="mdc-chat-eyebrow">Lousa</p>
          <h2>{content.title}</h2>
        </div>

        <div className="mdc-chat-canvas__actions">
          <button type="button" title="Expandir">
            <Maximize2 size={16} aria-hidden="true" />
          </button>

          <button type="button" onClick={onClose} title="Fechar">
            <X size={16} aria-hidden="true" />
          </button>
        </div>
      </header>

      <div className="mdc-chat-canvas__body">
        {content.type === "table" ? (
          <DataTable
            title={content.title}
            columns={content.columns}
            rows={content.rows}
          />
        ) : (
          <pre>{JSON.stringify(content.data, null, 2)}</pre>
        )}
      </div>
    </aside>
  );
}
