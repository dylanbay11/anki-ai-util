const ANKI_URL = process.env.ANKI_CONNECT_URL ?? "http://localhost:8765";

async function invoke(action: string, params: Record<string, unknown> = {}) {
  const res = await fetch(ANKI_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, version: 6, params }),
  });
  const data = await res.json();
  if (data.error) throw new Error(`AnkiConnect error: ${data.error}`);
  return data.result;
}

export async function checkConnection(): Promise<boolean> {
  try {
    await invoke("version");
    return true;
  } catch {
    return false;
  }
}

export async function getDeckNames(): Promise<string[]> {
  return invoke("deckNames");
}

export async function findNotes(query: string): Promise<number[]> {
  return invoke("findNotes", { query });
}

export async function getNotesInfo(noteIds: number[]) {
  return invoke("notesInfo", { notes: noteIds });
}

export async function addNote(params: {
  deckName: string;
  modelName: string;
  fields: Record<string, string>;
  tags?: string[];
}) {
  return invoke("addNote", { note: { ...params, options: { allowDuplicate: false } } });
}

export async function updateNoteFields(noteId: number, fields: Record<string, string>) {
  return invoke("updateNoteFields", { note: { id: noteId, fields } });
}

export async function guiCurrentCard() {
  return invoke("guiCurrentCard");
}

export async function getReviewsOfCards(cardIds: number[]) {
  return invoke("getReviewsOfCards", { cards: cardIds });
}
