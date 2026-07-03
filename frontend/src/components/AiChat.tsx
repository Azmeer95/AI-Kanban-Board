"use client";

import { useState, type FormEvent } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

type AiChatProps = {
  onBoardRefresh?: () => void;
};

export const AiChat = ({ onBoardRefresh }: AiChatProps) => {
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");
  const [isBusy, setIsBusy] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!message.trim()) {
      return;
    }

    setIsBusy(true);
    try {
      const token = window.localStorage.getItem("kanban-access-token");
      if (!token) {
        setReply("Please sign in first.");
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/ai/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error("Unable to reach AI service");
      }

      const data = await response.json();
      setReply(data.reply);
      if (onBoardRefresh) {
        onBoardRefresh();
      }
    } catch {
      setReply("The AI helper is not available right now.");
    } finally {
      setIsBusy(false);
      setMessage("");
    }
  };

  return (
    <aside className="rounded-[32px] border border-[var(--stroke)] bg-white/90 p-6 shadow-[var(--shadow)]">
      <h2 className="font-display text-2xl font-semibold text-[var(--navy-dark)]">AI assistant</h2>
      <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
        Ask for help planning your board, and the assistant will provide a simple response.
      </p>
      <form onSubmit={handleSubmit} className="mt-6 space-y-3">
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          rows={4}
          className="w-full rounded-2xl border border-[var(--stroke)] px-3 py-2 text-sm outline-none"
          placeholder="Ask the assistant to help with your board"
        />
        <button
          type="submit"
          disabled={isBusy}
          className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-3 text-sm font-semibold text-white disabled:opacity-70"
        >
          {isBusy ? "Thinking..." : "Send"}
        </button>
      </form>
      {reply ? <p className="mt-4 rounded-2xl bg-[var(--surface)] p-3 text-sm text-[var(--navy-dark)]">{reply}</p> : null}
    </aside>
  );
};
