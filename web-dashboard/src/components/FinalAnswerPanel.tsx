import { CheckCircle2 } from "lucide-react";

interface FinalAnswerPanelProps {
  answer: string | null;
}

export function FinalAnswerPanel({ answer }: FinalAnswerPanelProps) {
  return (
    <section className="panel answer-panel" aria-labelledby="final-answer-heading">
      <div className="panel-heading">
        <CheckCircle2 size={18} aria-hidden="true" />
        <h2 id="final-answer-heading">Final answer</h2>
      </div>
      <p>{answer || "The agent did not produce a final answer."}</p>
    </section>
  );
}
