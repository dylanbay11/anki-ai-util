import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

interface LLMOptions {
  system: string;
  user: string;
  json?: boolean;
}

export async function callLLM(opts: LLMOptions): Promise<string> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const msg = await client.messages.create({
        model: MODEL,
        max_tokens: 4096,
        system: opts.system,
        messages: [{ role: "user", content: opts.user }],
      });

      const text = msg.content
        .filter((b) => b.type === "text")
        .map((b) => (b as { type: "text"; text: string }).text)
        .join("");

      return text;
    } catch (err) {
      lastError = err as Error;
      const isRateLimit =
        err instanceof Anthropic.RateLimitError ||
        (err instanceof Error && err.message.includes("rate limit"));
      if (!isRateLimit || attempt === 2) throw err;
      await new Promise((r) => setTimeout(r, 2000 * (attempt + 1)));
    }
  }

  throw lastError;
}

export async function callLLMJson<T>(opts: LLMOptions): Promise<T> {
  const raw = await callLLM({ ...opts, json: true });
  try {
    return JSON.parse(raw) as T;
  } catch {
    // Strip markdown fences if present
    const cleaned = raw.replace(/^```(?:json)?\n?/, "").replace(/\n?```$/, "");
    return JSON.parse(cleaned) as T;
  }
}
