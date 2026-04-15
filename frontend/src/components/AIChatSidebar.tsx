"use client";

import { useEffect, useRef, useState } from "react";

export type ChatMessage = { role: "user" | "assistant"; content: string };

type AIChatSidebarProps = {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (message: string) => void;
  onClose: () => void;
};

export const AIChatSidebar = ({ messages, loading, onSend, onClose }: AIChatSidebarProps) => {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    onSend(trimmed);
    setInput("");
  };

  return (
    <aside className="sticky top-0 flex h-screen w-96 shrink-0 flex-col border-l border-[var(--stroke)] bg-white/90 backdrop-blur">
      <div className="flex items-center justify-between border-b border-[var(--stroke)] px-5 py-4">
        <h2 className="font-display text-sm font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]">
          AI Chat
        </h2>
        <button
          onClick={onClose}
          aria-label="Close AI chat"
          className="rounded-lg px-2 py-1 text-sm text-[var(--gray-text)] transition-colors hover:text-[var(--navy-dark)]"
        >
          ✕
        </button>
      </div>

      <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-5 py-4">
        {messages.length === 0 && (
          <p className="text-center text-xs leading-5 text-[var(--gray-text)]">
            Ask me anything about your board — or tell me to move, add, or delete cards.
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={msg.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div
              className={
                msg.role === "user"
                  ? "max-w-[80%] rounded-2xl rounded-tr-sm bg-[var(--primary-blue)] px-4 py-2.5 text-sm leading-5 text-white"
                  : "max-w-[80%] rounded-2xl rounded-tl-sm border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2.5 text-sm leading-5 text-[var(--navy-dark)]"
              }
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-tl-sm border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2.5 text-sm text-[var(--gray-text)]">
              ...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-[var(--stroke)] p-4">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask or instruct..."
          disabled={loading}
          className="flex-1 rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none placeholder:text-[var(--gray-text)] focus:border-[var(--primary-blue)] disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded-xl bg-[var(--primary-blue)] px-4 py-2 text-sm font-semibold text-white transition-opacity disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </aside>
  );
};
