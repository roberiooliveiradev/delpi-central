import { BarChart3, MessageSquareText } from "lucide-react";

import type { SipatSummary } from "../api/cipaApi";
import { SIPAT_QUESTION_TYPE_LABELS } from "../constants/labels";

type SummaryQuestion = SipatSummary["questions"][number];
type CountEntry = { label: string; count: number; share: number };

const DONUT_COLORS = [
  "#089bdb",
  "#003866",
  "#30b8ec",
  "#5b8def",
  "#7c6cf0",
  "#0c6fb0",
  "#56c2a0",
  "#f0a05a",
];

function sortedCountEntries(
  counts: Record<string, number>,
  questionType: string,
): Array<[string, number]> {
  const entries = Object.entries(counts);
  if (questionType === "likert_5") {
    return entries.sort((a, b) => Number(a[0]) - Number(b[0]) || a[0].localeCompare(b[0]));
  }
  return entries.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}

function toEntries(
  counts: Record<string, number>,
  questionType: string,
  answerCount: number,
): CountEntry[] {
  const pairs = sortedCountEntries(counts, questionType);
  const total = answerCount || pairs.reduce((sum, [, count]) => sum + count, 0);
  return pairs.map(([label, count]) => ({
    label,
    count,
    share: total > 0 ? Math.round((count / total) * 100) : 0,
  }));
}

function isTextQuestion(type: string): boolean {
  return type === "text_short" || type === "text_long";
}

function visualKind(item: SummaryQuestion): "likert" | "donut" | "bars" {
  if (item.question_type === "likert_5") return "likert";
  if (item.question_type === "yes_no") return "donut";
  const categories = item.counts ? Object.keys(item.counts).length : 0;
  if (item.question_type === "single_choice" && categories > 0 && categories <= 6) {
    return "donut";
  }
  return "bars";
}

type Props = {
  questions: SummaryQuestion[];
  responseCount: number;
};

export function SipatResultsSection({ questions, responseCount }: Props) {
  if (responseCount === 0) {
    return (
      <div className="cipa-sipat-results-empty">
        <p>Ainda não há respostas para exibir.</p>
        <span>Quando os participantes enviarem, as distribuições e comentários aparecem aqui.</span>
      </div>
    );
  }

  const chartQuestions = questions.filter(
    (item) => !isTextQuestion(item.question_type) && item.counts && Object.keys(item.counts).length > 0,
  );
  const textQuestions = questions.filter(
    (item) => isTextQuestion(item.question_type) && (item.sample_texts?.length ?? 0) > 0,
  );

  return (
    <div className="cipa-sipat-results-layout">
      <div className="cipa-sipat-results-layout__block">
        <header className="cipa-sipat-results-layout__subhead">
          <BarChart3 size={16} aria-hidden />
          <div>
            <h4>Distribuições</h4>
            <p>Visão agregada por pergunta fechada.</p>
          </div>
        </header>

        {chartQuestions.length === 0 ? (
          <p className="cipa-sipat-empty-note">
            Nenhuma pergunta fechada com respostas para visualizar.
          </p>
        ) : (
          <div className="cipa-sipat-chart-grid">
            {chartQuestions.map((item, index) => (
              <DistributionCard key={item.question_id} item={item} index={index} />
            ))}
          </div>
        )}
      </div>

      <div className="cipa-sipat-results-layout__block">
        <header className="cipa-sipat-results-layout__subhead">
          <MessageSquareText size={16} aria-hidden />
          <div>
            <h4>Comentários abertos</h4>
            <p>Respostas em texto, agrupadas por pergunta.</p>
          </div>
        </header>

        {textQuestions.length === 0 ? (
          <p className="cipa-sipat-empty-note">Ainda não há comentários em texto.</p>
        ) : (
          <div className="cipa-sipat-comments-grid">
            {textQuestions.map((item, index) => (
              <article key={item.question_id} className="cipa-sipat-comment-card">
                <header className="cipa-sipat-result__head">
                  <span className="cipa-sipat-result__index">{index + 1}</span>
                  <div>
                    <h4>{item.label}</h4>
                    <p>
                      {item.answer_count} resposta{item.answer_count === 1 ? "" : "s"}
                    </p>
                  </div>
                </header>
                <ul className="cipa-sipat-quotes">
                  {(item.sample_texts ?? []).slice(0, 12).map((text, quoteIndex) => (
                    <li key={`${item.question_id}-${quoteIndex}`}>
                      <blockquote>{text}</blockquote>
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function DistributionCard({ item, index }: { item: SummaryQuestion; index: number }) {
  const entries = toEntries(item.counts || {}, item.question_type, item.answer_count);
  const total = item.answer_count || entries.reduce((sum, entry) => sum + entry.count, 0);
  const kind = visualKind(item);

  return (
    <article className="cipa-sipat-chart-card">
      <header className="cipa-sipat-result__head">
        <span className="cipa-sipat-result__index">{index + 1}</span>
        <div>
          <h4>{item.label}</h4>
          <p>
            {SIPAT_QUESTION_TYPE_LABELS[item.question_type] || item.question_type}
            {" · "}
            {total} resposta{total === 1 ? "" : "s"}
          </p>
        </div>
      </header>

      {kind === "likert" ? <LikertSpectrum entries={entries} /> : null}
      {kind === "donut" ? <DonutChart entries={entries} total={total} /> : null}
      {kind === "bars" ? <RankBars entries={entries} /> : null}
    </article>
  );
}

function LikertSpectrum({ entries }: { entries: CountEntry[] }) {
  const max = Math.max(1, ...entries.map((entry) => entry.count));
  const weighted = entries.reduce((sum, entry) => {
    const level = Number(entry.label);
    return sum + (Number.isFinite(level) ? level * entry.count : 0);
  }, 0);
  const totalCount = entries.reduce((sum, entry) => sum + entry.count, 0);
  const average = totalCount > 0 ? weighted / totalCount : 0;

  return (
    <div className="cipa-sipat-likert-viz">
      <div className="cipa-sipat-likert-viz__score">
        <span>Média</span>
        <strong>{average.toFixed(1)}</strong>
        <em>de 5</em>
      </div>
      <ul className="cipa-sipat-likert-bars" aria-label="Distribuição da escala">
        {entries.map((entry, index) => (
          <li key={entry.label}>
            <div className="cipa-sipat-likert-bars__meta">
              <span className="cipa-sipat-likert-bars__label">
                <em style={{ background: DONUT_COLORS[index % DONUT_COLORS.length] }} />
                Nível {entry.label}
              </span>
              <span className="cipa-sipat-likert-bars__value">
                {entry.count} <strong>{entry.share}%</strong>
              </span>
            </div>
            <div className="cipa-sipat-likert-bars__track">
              <div
                className="cipa-sipat-likert-bars__fill"
                style={{
                  width: `${Math.max(entry.count > 0 ? 8 : 0, (entry.count / max) * 100)}%`,
                  background: `linear-gradient(90deg, ${DONUT_COLORS[index % DONUT_COLORS.length]}, color-mix(in srgb, ${DONUT_COLORS[index % DONUT_COLORS.length]} 50%, #003866))`,
                }}
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function DonutChart({ entries, total }: { entries: CountEntry[]; total: number }) {
  const radius = 54;
  const stroke = 16;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  return (
    <div className="cipa-sipat-donut">
      <div className="cipa-sipat-donut__plot">
        <svg viewBox="0 0 140 140" className="cipa-sipat-donut__svg" aria-hidden>
          <circle
            cx="70"
            cy="70"
            r={radius}
            fill="none"
            stroke="color-mix(in srgb, var(--cipa-accent) 12%, transparent)"
            strokeWidth={stroke}
          />
          {entries.map((entry, index) => {
            const length = total > 0 ? (entry.count / total) * circumference : 0;
            const dashOffset = -offset;
            offset += length;
            return (
              <circle
                key={entry.label}
                cx="70"
                cy="70"
                r={radius}
                fill="none"
                stroke={DONUT_COLORS[index % DONUT_COLORS.length]}
                strokeWidth={stroke}
                strokeLinecap="butt"
                strokeDasharray={`${length} ${circumference - length}`}
                strokeDashoffset={dashOffset}
                transform="rotate(-90 70 70)"
              />
            );
          })}
        </svg>
        <div className="cipa-sipat-donut__center">
          <strong>{total}</strong>
          <span>respostas</span>
        </div>
      </div>
      <ul className="cipa-sipat-donut__legend">
        {entries.map((entry, index) => (
          <li key={entry.label}>
            <span
              className="cipa-sipat-donut__swatch"
              style={{ background: DONUT_COLORS[index % DONUT_COLORS.length] }}
            />
            <span className="cipa-sipat-donut__name">{entry.label}</span>
            <strong>
              {entry.count} <em>{entry.share}%</em>
            </strong>
          </li>
        ))}
      </ul>
    </div>
  );
}

function RankBars({ entries }: { entries: CountEntry[] }) {
  const max = Math.max(1, ...entries.map((entry) => entry.count));
  return (
    <ul className="cipa-sipat-rank">
      {entries.map((entry, index) => (
        <li key={entry.label}>
          <div className="cipa-sipat-rank__meta">
            <span className="cipa-sipat-rank__label">
              <em style={{ background: DONUT_COLORS[index % DONUT_COLORS.length] }} />
              {entry.label}
            </span>
            <span className="cipa-sipat-rank__value">
              {entry.count} <strong>{entry.share}%</strong>
            </span>
          </div>
          <div className="cipa-sipat-rank__track">
            <div
              className="cipa-sipat-rank__fill"
              style={{
                width: `${(entry.count / max) * 100}%`,
                background: `linear-gradient(90deg, ${DONUT_COLORS[index % DONUT_COLORS.length]}, color-mix(in srgb, ${DONUT_COLORS[index % DONUT_COLORS.length]} 55%, #003866))`,
              }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}
