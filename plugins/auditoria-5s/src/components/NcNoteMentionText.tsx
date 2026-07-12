import { splitNoteMentionSegments } from "../utils/ncNoteMentions";

type Props = {
  text: string;
  className?: string;
};

/** Renderiza nota do histórico com menções em negrito e sem o "@". */
export function NcNoteMentionText({ text, className }: Props) {
  const segments = splitNoteMentionSegments(text);

  return (
    <p className={className}>
      {segments.map((segment, index) =>
        segment.type === "mention" ? (
          <strong key={`m-${index}`} className="a5s-nc-note-mention">
            {segment.value}
          </strong>
        ) : (
          <span key={`t-${index}`}>{segment.value}</span>
        ),
      )}
    </p>
  );
}
