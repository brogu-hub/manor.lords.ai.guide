import { useState, useRef, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "~/components/ui/card";
import { Input } from "~/components/ui/input";
import { Button } from "~/components/ui/button";
import { ScrollArea } from "~/components/ui/scroll-area";

interface Message {
  role: "user" | "ai";
  text: string;
  loading?: boolean;
}

interface Props {
  askQuestion: (q: string) => Promise<string>;
  hasState: boolean;
}

export function ChatPanel({ askQuestion, hasState }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setLoading(true);
    setMessages((prev) => [
      ...prev,
      { role: "ai", text: "Thinking...", loading: true },
    ]);

    const answer = await askQuestion(question);
    setMessages((prev) => {
      const updated = [...prev];
      updated[updated.length - 1] = { role: "ai", text: answer };
      return updated;
    });
    setLoading(false);
  }

  return (
    <Card className="col-span-full bg-card border-border flex flex-col max-h-[300px]">
      <CardHeader className="bg-[var(--color-panel-header)] border-b border-[var(--color-gold-dim)] py-2 px-4">
        <CardTitle className="font-heading text-xs font-semibold text-primary uppercase tracking-wider">
          Counsel Chamber
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0 flex-1 flex flex-col min-h-0">
        <ScrollArea className="flex-1 p-3" ref={scrollRef}>
          {messages.length === 0 ? (
            <p className="text-muted-foreground italic text-sm px-1">
              {hasState
                ? "Pose your questions to the advisor"
                : "Analyse a save first to ask questions"}
            </p>
          ) : (
            <div className="space-y-2">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`px-3 py-2 rounded-sm text-sm ${
                    msg.role === "user"
                      ? "bg-secondary/40 border-l-2 border-border"
                      : "bg-[var(--color-ok-green)]/5 border-l-2 border-[var(--color-ok-green)]"
                  } ${msg.loading ? "animate-pulse-gold" : ""}`}
                >
                  <span className="font-heading text-xs text-muted-foreground">
                    {msg.role === "user" ? "You" : "Advisor"}:
                  </span>{" "}
                  {msg.text}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
        <form
          onSubmit={handleSubmit}
          className="flex gap-2 p-3 pt-0 border-t border-border"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask your advisor a question..."
            className="flex-1 bg-input border-border text-foreground"
            disabled={!hasState || loading}
          />
          <Button
            type="submit"
            variant="destructive"
            className="font-heading text-xs uppercase tracking-wide"
            disabled={!hasState || loading}
          >
            Send
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
