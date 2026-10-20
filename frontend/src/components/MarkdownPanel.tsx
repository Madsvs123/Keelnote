import { Check, ClipboardCopy, Download } from "lucide-react";
import { useState } from "react";

export function MarkdownPanel({ markdown, pending }: { markdown?: string; pending: boolean }) {
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState("");

  async function copy() {
    if (!markdown) return;
    try {
      await navigator.clipboard.writeText(markdown);
      setCopyError("");
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopyError("Clipboard is blocked in this browser.");
    }
  }

  function download() {
    if (!markdown) return;
    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "CHANGELOG.md";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="markdown">
      <div className="markdown-bar">
        <strong>CHANGELOG.md</strong>
        <div className="row">
          <button className="btn btn-tiny btn-ghost" type="button" onClick={copy} disabled={!markdown}>
            {copied ? <Check size={14} /> : <ClipboardCopy size={14} />}
            {copied ? "Copied" : "Copy"}
          </button>
          <button className="btn btn-tiny btn-ghost" type="button" onClick={download} disabled={!markdown}>
            <Download size={14} />
            Download
          </button>
        </div>
      </div>
      {copyError && <p className="error">{copyError}</p>}
      {pending && <p className="muted">Writing the log…</p>}
      {markdown && <pre>{markdown}</pre>}
    </section>
  );
}
