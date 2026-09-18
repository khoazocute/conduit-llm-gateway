"use client";

import { use, useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { useAuth } from "@/context/auth-context";
import { API_BASE_URL, ApiClientError, apiFetch } from "@/lib/api/client";
import type { ChatMessage, Conversation, ConversationListResponse, MessageListResponse } from "@/lib/api/types";

interface ChatPageProps {
  params: Promise<{ id: string }>;
}

// EventSource can't send an Authorization header, so the SSE response from
// POST /conversations/{id}/messages is read manually via fetch + a
// ReadableStream, parsing the "event: X\ndata: Y\n\n" frames ourselves.
async function streamChat(
  conversationId: string,
  content: string,
  token: string,
  onChunk: (delta: string) => void,
  onDone: (message: ChatMessage) => void,
  onError: (message: string) => void,
) {
  const res = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ content }),
  });

  if (!res.ok || !res.body) {
    onError(`Request failed (${res.status})`);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sepIndex;
    while ((sepIndex = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, sepIndex);
      buffer = buffer.slice(sepIndex + 2);

      const eventLine = frame.split("\n").find((l) => l.startsWith("event:"));
      const dataLine = frame.split("\n").find((l) => l.startsWith("data:"));
      if (!eventLine || !dataLine) continue;

      const eventName = eventLine.slice("event:".length).trim();
      const data = JSON.parse(dataLine.slice("data:".length).trim());

      if (eventName === "chunk") onChunk(data.delta ?? "");
      else if (eventName === "done") onDone(data.message as ChatMessage);
      else if (eventName === "error") onError(data.message ?? "Unknown error");
    }
  }
}

export default function AgentChatPage({ params }: ChatPageProps) {
  const { id: agentId } = use(params);
  const { accessToken } = useAuth();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  const setup = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    try {
      // Reuse an existing conversation for this agent if one exists, so
      // reopening the chat page doesn't spawn a new conversation every time.
      const mine = await apiFetch<ConversationListResponse>("/conversations", {
        token: accessToken,
        searchParams: { size: 100 },
      });
      let conv = mine.items.find((c) => c.agent_id === agentId) ?? null;

      if (!conv) {
        conv = await apiFetch<Conversation>("/conversations", {
          method: "POST",
          token: accessToken,
          body: { agent_id: agentId },
        });
      }
      setConversation(conv);

      const history = await apiFetch<MessageListResponse>(`/conversations/${conv.id}/messages`, {
        token: accessToken,
        searchParams: { size: 100 },
      });
      setMessages(history.items);
    } catch (err) {
      toast.error(
        err instanceof ApiClientError
          ? err.apiError.message
          : "Failed to start chat. Have you purchased this agent?",
      );
    } finally {
      setLoading(false);
    }
  }, [accessToken, agentId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setup();
  }, [setup]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!conversation || !accessToken || !input.trim()) return;

    const userMessage: ChatMessage = {
      id: `local-${Date.now()}`,
      conversation_id: conversation.id,
      role: "user",
      content: input,
      credit_charged: null,
      model_used: null,
      latency_ms: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    const content = input;
    setInput("");
    setSending(true);

    await streamChat(
      conversation.id,
      content,
      accessToken,
      () => {},
      (message) => {
        setMessages((prev) => [...prev, message]);
        if (message.credit_charged) {
          toast.success(`-${message.credit_charged} credit`);
        }
        setSending(false);
      },
      (errorMessage) => {
        toast.error(errorMessage);
        setSending(false);
      },
    );
  }

  return (
    <div className="page" style={{ maxWidth: 720, display: "flex", flexDirection: "column", height: "calc(100vh - 100px)" }}>
      <div className="page-header">
        <div>
          <div className="page-eyebrow">
            <span className="accent">●</span> conduit://agents/{agentId.slice(0, 8)}/chat
          </div>
          <h1 className="page-title">Chat</h1>
        </div>
      </div>

      <div className="card" style={{ flex: 1, overflowY: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 10 }}>
        {loading ? (
          <p className="faint">Loading...</p>
        ) : messages.length === 0 ? (
          <p className="faint">No messages yet. Say hello!</p>
        ) : (
          messages.map((m) => (
            <div
              key={m.id}
              style={{
                alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                maxWidth: "80%",
                background: m.role === "user" ? "var(--accent)" : "var(--panel-2, var(--panel))",
                color: m.role === "user" ? "var(--bg)" : "var(--text)",
                borderRadius: 10,
                padding: "8px 12px",
              }}
            >
              {m.content ?? <span className="faint">(no response — provider error)</span>}
              {m.credit_charged != null && (
                <div className="faint" style={{ fontSize: "var(--t-1)", marginTop: 4 }}>
                  -{m.credit_charged} credit
                </div>
              )}
            </div>
          ))
        )}
        {sending && <p className="faint">Assistant is typing...</p>}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="row" style={{ gap: 10, marginTop: 12 }}>
        <input
          className="input"
          style={{ flex: 1 }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          disabled={sending || !conversation}
        />
        <button type="submit" className="btn btn-primary" disabled={sending || !conversation || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
