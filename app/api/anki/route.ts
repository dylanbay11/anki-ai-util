import { NextRequest, NextResponse } from "next/server";

const ANKI_URL = process.env.ANKI_CONNECT_URL ?? "http://localhost:8765";

export async function POST(req: NextRequest) {
  const body = await req.json();
  try {
    const res = await fetch(ANKI_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { result: null, error: "AnkiConnect is not reachable" },
      { status: 502 }
    );
  }
}
