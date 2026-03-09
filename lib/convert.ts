import TurndownService from "turndown";
import { marked } from "marked";

// Cloze placeholder: preserve {{c1::text}} through both directions
const CLOZE_PLACEHOLDER = "__CLOZE__";

function encodeCloze(text: string): { encoded: string; clozes: string[] } {
  const clozes: string[] = [];
  const encoded = text.replace(/\{\{c\d+::.*?\}\}/g, (match) => {
    clozes.push(match);
    return `${CLOZE_PLACEHOLDER}${clozes.length - 1}__`;
  });
  return { encoded, clozes };
}

function decodeCloze(text: string, clozes: string[]): string {
  return text.replace(/__CLOZE__(\d+)__/g, (_, i) => clozes[parseInt(i)]);
}

const td = new TurndownService({ headingStyle: "atx", codeBlockStyle: "fenced" });

export function htmlToMarkdown(html: string): string {
  const { encoded, clozes } = encodeCloze(html);
  const md = td.turndown(encoded);
  return decodeCloze(md, clozes);
}

export function markdownToHtml(md: string): string {
  const { encoded, clozes } = encodeCloze(md);
  const html = marked.parse(encoded) as string;
  return decodeCloze(html, clozes);
}
