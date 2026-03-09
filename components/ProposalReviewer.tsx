"use client";
// TODO: Step-through accept/reject UI for AI proposals
export interface Proposal {
  id: string;
  original?: Record<string, string>;
  proposed: Record<string, string>;
  rationale?: string;
}

interface Props {
  proposals: Proposal[];
  onAccept: (p: Proposal) => void;
  onSkip: (p: Proposal) => void;
}

export default function ProposalReviewer({ proposals, onAccept, onSkip }: Props) {
  return (
    <div>
      {proposals.map((p) => (
        <div key={p.id} className="border rounded p-4 mb-4">
          <pre className="text-sm whitespace-pre-wrap">{JSON.stringify(p.proposed, null, 2)}</pre>
          {p.rationale && <p className="text-xs text-gray-500 mt-2">{p.rationale}</p>}
          <div className="flex gap-2 mt-3">
            <button onClick={() => onAccept(p)} className="px-3 py-1 bg-green-600 text-white rounded text-sm">Accept</button>
            <button onClick={() => onSkip(p)} className="px-3 py-1 bg-gray-300 rounded text-sm">Skip</button>
          </div>
        </div>
      ))}
    </div>
  );
}
