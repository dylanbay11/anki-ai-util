import { NextRequest, NextResponse } from "next/server";
import { callLLM, callLLMJson } from "@/lib/llm";

export async function POST(req: NextRequest) {
  const { system, user, json } = await req.json();
  try {
    if (json) {
      const result = await callLLMJson({ system, user });
      return NextResponse.json({ result });
    } else {
      const result = await callLLM({ system, user });
      return NextResponse.json({ result });
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
