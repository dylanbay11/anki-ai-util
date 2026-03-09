"use client";
import { useState } from "react";

interface Props {
  value: string;
  onChange: (val: string) => void;
  label?: string;
}

export default function MarkdownEditor({ value, onChange, label }: Props) {
  const [preview, setPreview] = useState(false);

  return (
    <div>
      {label && <label className="block text-sm font-medium mb-1">{label}</label>}
      <div className="flex gap-2 mb-1">
        <button onClick={() => setPreview(false)} className={`text-xs px-2 py-0.5 rounded ${!preview ? "bg-blue-600 text-white" : "bg-gray-200"}`}>Edit</button>
        <button onClick={() => setPreview(true)} className={`text-xs px-2 py-0.5 rounded ${preview ? "bg-blue-600 text-white" : "bg-gray-200"}`}>Preview</button>
      </div>
      {preview ? (
        <div className="prose prose-sm border rounded p-3 min-h-[80px] bg-white" dangerouslySetInnerHTML={{ __html: value }} />
      ) : (
        <textarea
          className="w-full border rounded p-2 font-mono text-sm min-h-[80px]"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </div>
  );
}
