import React, { useState, useRef, useEffect, useCallback } from "react";
import { chatbotAPI } from "../services/api";
import {
  Send,
  Sparkles,
  User,
  Bot,
  AlertCircle,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Check,
  Trash2,
  Clock,
} from "lucide-react";

const WELCOME_MESSAGE = {
  sender: "bot",
  text: "Hello! I am **AuraHealth AI**. Ask about symptoms, medications, wellness goals, or diabetes risk. I remember our conversation and use trusted medical references.",
  timestamp: new Date().toISOString(),
};

// ─── Simple Markdown Renderer ─────────────────────────────────────────────────
// Handles: **bold**, *italic*, numbered lists, bullet lists, line breaks
function renderMarkdown(text) {
  if (!text) return null;
  const lines = text.split("\n");
  const elements = [];

  lines.forEach((line, idx) => {
    const key = idx;

    // Numbered list: "1. something"
    if (/^\d+\.\s/.test(line)) {
      elements.push(
        <div key={key} className="flex gap-2 my-0.5">
          <span className="text-teal-400 font-bold shrink-0">{line.match(/^\d+/)[0]}.</span>
          <span>{inlineFormat(line.replace(/^\d+\.\s/, ""))}</span>
        </div>
      );
      return;
    }

    // Bullet list: "- " or "• "
    if (/^[-•]\s/.test(line)) {
      elements.push(
        <div key={key} className="flex gap-2 my-0.5">
          <span className="text-teal-400 shrink-0 mt-[2px]">•</span>
          <span>{inlineFormat(line.replace(/^[-•]\s/, ""))}</span>
        </div>
      );
      return;
    }

    // Empty line → spacer
    if (line.trim() === "") {
      elements.push(<div key={key} className="h-2" />);
      return;
    }

    // Regular paragraph
    elements.push(<div key={key}>{inlineFormat(line)}</div>);
  });

  return <>{elements}</>;
}

function inlineFormat(text) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="text-slate-100 font-semibold">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={i} className="text-slate-300 italic">{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

// ─── Copy Button ──────────────────────────────────────────────────────────────
function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <button
      onClick={handleCopy}
      title="Copy message"
      className={`p-1.5 rounded-lg border transition-colors ${
        copied
          ? "border-teal-500 text-teal-400 bg-teal-500/10"
          : "border-aura-border text-aura-text-muted hover:text-teal-400 hover:border-teal-500/30"
      }`}
    >
      {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  );
}

// ─── Timestamp ────────────────────────────────────────────────────────────────
function MessageTime({ timestamp }) {
  if (!timestamp) return null;
  const d = new Date(timestamp);
  const time = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return (
    <span className="text-[10px] text-aura-text-muted flex items-center gap-1 mt-1 px-1">
      <Clock className="h-2.5 w-2.5" />
      {time}
    </span>
  );
}

// ─── Intent / LLM Badges ──────────────────────────────────────────────────────
function MetaBadges({ intent, selected_tool, llm_used }) {
  return (
    <div className="flex flex-wrap gap-1.5 mt-1 px-1">
      {selected_tool && (
        <span className="px-2 py-0.5 bg-teal-500/10 border border-teal-500/20 text-teal-400 text-[10px] font-semibold rounded-full">
          🔧 {selected_tool}
        </span>
      )}
      {intent && (
        <span className="px-2 py-0.5 bg-violet-500/10 border border-violet-500/20 text-violet-400 text-[10px] font-semibold rounded-full">
          🎯 {intent}
        </span>
      )}
      {llm_used && (
        <span className="px-2 py-0.5 bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-semibold rounded-full">
          🤖 LLM
        </span>
      )}
    </div>
  );
}

// ─── Quick Queries ────────────────────────────────────────────────────────────
const QUICK_QUERIES = [
  "Are there drug interactions with Metformin?",
  "Calculate my IDRS risk score",
  "Give me a wellness plan",
  "What is my blood pressure status?",
  "Summarize my medication schedule",
];

// ─── Main Component ───────────────────────────────────────────────────────────
export default function Chatbot({ username }) {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [conversationId, setConversationId] = useState(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [feedbackState, setFeedbackState] = useState({});

  const messagesEndRef = useRef(null);
  const abortControllerRef = useRef(null); // FIX BUG-6: abort controller for cleanup

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // FIX BUG-6: Proper cleanup with AbortController to prevent memory leaks
  useEffect(() => {
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const restoreConversation = async () => {
      try {
        const conversations = await chatbotAPI.getConversations(1);
        if (controller.signal.aborted) return;
        if (!conversations.length) return;

        const latest = conversations[0];
        setConversationId(latest.id);
        const history = await chatbotAPI.getMessages(latest.id);
        if (controller.signal.aborted) return;
        if (!history.length) return;

        const restored = history.map((msg) => ({
          sender: msg.role === "user" ? "user" : "bot",
          text: msg.content,
          messageId: msg.role === "assistant" ? msg.id : undefined,
          intent: msg.intent,
          selected_tool: msg.selected_tool,
          timestamp: msg.created_at,
        }));
        setMessages([WELCOME_MESSAGE, ...restored]);
      } catch (err) {
        if (!controller.signal.aborted) {
          console.warn("Could not restore chat history:", err.message);
        }
      }
    };

    restoreConversation();
    return () => controller.abort();
  }, [username]);

  const handleSend = async (textToSend) => {
    const text = (textToSend || input).trim();
    if (!text) return;

    const msgTimestamp = new Date().toISOString();
    setMessages((prev) => [...prev, { sender: "user", text, timestamp: msgTimestamp }]);
    // L-BUG-6 FIX: always clear the input box after any send, regardless of whether
    // it came from the text field or a quick-query button click
    setInput("");
    setLoading(true);

    try {
      const payload = {
        question: text,
        patient_name: username,
        conversation_id: conversationId,
      };

      const result = await chatbotAPI.chat(payload);
      if (result.conversation_id) setConversationId(result.conversation_id);

      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: result.response,
          messageId: result.message_id,
          intent: result.intent,
          selected_tool: result.selected_tool,
          llm_used: result.llm_used,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: `Error connecting to AI: ${err.message}`,
          isError: true,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (messageId, rating) => {
    if (!messageId) return;
    try {
      await chatbotAPI.submitFeedback(messageId, rating);
      setFeedbackState((prev) => ({ ...prev, [messageId]: rating }));
    } catch (err) {
      console.error("Feedback failed:", err.message);
    }
  };

  const handleClearChat = () => {
    setMessages([{ ...WELCOME_MESSAGE, timestamp: new Date().toISOString() }]);
    setConversationId(null);
    setFeedbackState({});
  };



  const charCount = input.length;
  const maxChars = 500;

  return (
    <div className="glass-panel border border-aura-border h-[650px] flex flex-col justify-between overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-aura-border bg-aura-muted/50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-teal-500/10 border border-teal-500/20 rounded-xl pulse-ring">
            <Sparkles className="h-5 w-5 text-teal-600 dark:text-teal-400" />
          </div>
          <div>
            <h3 className="font-bold text-aura-text">AuraHealth Assistant</h3>
            <span className="text-[10px] text-teal-600 dark:text-teal-400 font-medium flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-500 animate-ping" />
              {conversationId ? "Memory active" : "Online & Ready"}
            </span>
          </div>
        </div>
        <button
          onClick={handleClearChat}
          title="Clear conversation"
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-aura-text-muted hover:text-rose-400 border border-aura-border hover:border-rose-500/30 rounded-lg transition-colors"
        >
          <Trash2 className="h-3.5 w-3.5" />
          Clear Chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex items-start gap-3 max-w-[88%] ${msg.sender === "user" ? "ml-auto flex-row-reverse" : ""}`}
          >
            {/* Avatar */}
            <div
              className={`p-2.5 rounded-xl shrink-0 ${
                msg.sender === "user"
                  ? "bg-teal-600 text-white"
                  : "bg-aura-muted border border-aura-border text-aura-text"
              }`}
            >
              {msg.sender === "user" ? (
                <User className="h-4 w-4" />
              ) : (
                <Bot className="h-4 w-4 text-teal-600 dark:text-teal-400" />
              )}
            </div>

            {/* Bubble */}
            <div className="space-y-1 min-w-0">
              <div
                className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  msg.sender === "user"
                    ? "bg-teal-500/10 text-teal-800 dark:text-teal-300 border border-teal-500/20"
                    : msg.isError
                      ? "bg-red-500/10 border border-red-500/20 text-red-700 dark:text-red-400"
                      : "bg-aura-muted border border-aura-border text-aura-text"
                }`}
              >
                {msg.sender === "bot" && !msg.isError
                  ? renderMarkdown(msg.text)
                  : msg.text}
              </div>

              {/* Meta badges (tool/intent/llm) */}
              {msg.sender === "bot" && (msg.selected_tool || msg.intent || msg.llm_used) && (
                <MetaBadges intent={msg.intent} selected_tool={msg.selected_tool} llm_used={msg.llm_used} />
              )}

              {/* Timestamp */}
              {msg.sender === "user" ? (
                <div className="flex justify-end">
                  <MessageTime timestamp={msg.timestamp} />
                </div>
              ) : (
                <MessageTime timestamp={msg.timestamp} />
              )}

              {/* Actions: Copy + Feedback */}
              {msg.sender === "bot" && !msg.isError && (
                <div className="flex items-center gap-1.5 px-1 pt-0.5">
                  <CopyButton text={msg.text} />
                  {msg.messageId && (
                    <>
                      <button
                        type="button"
                        onClick={() => handleFeedback(msg.messageId, 1)}
                        className={`p-1.5 rounded-lg border transition-colors ${
                          feedbackState[msg.messageId] === 1
                            ? "border-teal-500 text-teal-600 bg-teal-500/10"
                            : "border-aura-border text-aura-text-muted hover:text-teal-600"
                        }`}
                        title="Helpful"
                      >
                        <ThumbsUp className="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleFeedback(msg.messageId, -1)}
                        className={`p-1.5 rounded-lg border transition-colors ${
                          feedbackState[msg.messageId] === -1
                            ? "border-red-500 text-red-600 bg-red-500/10"
                            : "border-aura-border text-aura-text-muted hover:text-red-500"
                        }`}
                        title="Not helpful"
                      >
                        <ThumbsDown className="h-3.5 w-3.5" />
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading dots */}
        {loading && (
          <div className="flex items-start gap-3 max-w-[85%]">
            <div className="p-2.5 bg-aura-muted border border-aura-border rounded-xl shrink-0">
              <Bot className="h-4 w-4 text-teal-600 dark:text-teal-400" />
            </div>
            <div className="px-4 py-3 bg-aura-muted border border-aura-border rounded-2xl text-sm text-aura-text-muted flex items-center gap-1.5">
              <span className="h-2 w-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="h-2 w-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="h-2 w-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}


        <div ref={messagesEndRef} />
      </div>

      {/* Quick Queries */}
      <div className="px-4 py-2 flex flex-wrap gap-2 border-t border-aura-border bg-aura-muted/30">
        {QUICK_QUERIES.map((q) => (
          <button
            key={q}
            onClick={() => handleSend(q)}
            disabled={loading}
            className="text-xs px-3 py-1.5 bg-aura-muted hover:bg-aura-surface border border-aura-border hover:border-teal-500/30 rounded-lg text-aura-text-muted hover:text-aura-text transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input area */}
      <div className="p-4 border-t border-aura-border bg-aura-muted/40">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value.slice(0, maxChars))}
              onKeyDown={(e) => e.key === "Enter" && !loading && handleSend()}
              placeholder="Ask AuraHealth AI a health question..."
              className="auth-input w-full pl-4 pr-12 py-3"
            />
            <button
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              className="absolute right-3 top-3 text-teal-600 dark:text-teal-400 hover:text-teal-500 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Character counter */}
        <div className="flex items-center justify-end mt-1.5 px-1">
          {input.length > 0 && (
            <span className={`text-[10px] ${charCount > maxChars * 0.9 ? "text-amber-400" : "text-aura-text-muted"}`}>
              {charCount}/{maxChars}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
