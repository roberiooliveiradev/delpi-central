import { isHtmlEmpty } from "../utils/htmlContent";

type Props = {
  html: string;
  emptyLabel: string;
};

export function HtmlPreview({ html, emptyLabel }: Props) {
  if (isHtmlEmpty(html)) {
    return <p className="cec-review-empty">{emptyLabel}</p>;
  }
  return <div className="cec-prose" dangerouslySetInnerHTML={{ __html: html }} />;
}
