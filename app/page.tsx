import Link from "next/link";

export default function Home() {
  return (
    <main className="max-w-2xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-2">Anki AI Companion</h1>
      <p className="text-gray-500 mb-8">AI-assisted card creation and editing via AnkiConnect.</p>

      <div className="grid gap-4">
        <Link href="/generate" className="block border rounded-lg p-5 hover:border-blue-500 transition-colors">
          <h2 className="font-semibold text-lg">Generate Cards</h2>
          <p className="text-sm text-gray-500 mt-1">Paste text and let AI draft new cards for review.</p>
        </Link>

        <Link href="/bulk-edit" className="block border rounded-lg p-5 hover:border-blue-500 transition-colors">
          <h2 className="font-semibold text-lg">Bulk AI Edit</h2>
          <p className="text-sm text-gray-500 mt-1">Apply a natural language instruction across an entire deck.</p>
        </Link>
      </div>
    </main>
  );
}
