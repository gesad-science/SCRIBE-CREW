import { useState, useRef, useEffect } from "react";
import { BookOpen, Feather } from "lucide-react";
import { useNavigate } from "react-router-dom";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import { executeSimple, executeWithPdf } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const Chat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleSend = async (message: string, pdf?: File) => {
    const userContent = pdf ? `${message}\n\n📎 ${pdf.name}` : message;
    setMessages((prev) => [...prev, { role: "user", content: userContent }]);
    setIsLoading(true);

    try {
      let result: unknown;
      if (pdf) {
        const res = await executeWithPdf(message, pdf);
        result = res.result;
      } else {
        result = await executeSimple(message);
      }
      const text = typeof result === "string" ? result : JSON.stringify(result, null, 2);
      setMessages((prev) => [...prev, { role: "assistant", content: text }]);
    } catch {
      toast({
        title: "Request error",
        description: "Could not connect to the server. Make sure the API is running.",
        variant: "destructive",
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, an error occurred. Please check if the server is running." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-background">
      <header className="flex items-center gap-3 border-b border-border bg-card px-6 py-4">
        <button onClick={() => navigate("/")} className="flex items-center gap-3 hover:opacity-80 transition-opacity">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <Feather className="h-5 w-5" />
          </div>
          <div className="text-left">
            <h1 className="font-display text-xl font-bold tracking-tight text-foreground">Scribe</h1>
            <p className="text-xs text-muted-foreground">Academic review assistant</p>
          </div>
        </button>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <BookOpen className="h-10 w-10 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Send a message or attach a PDF to get started.</p>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-4">
            {messages.map((msg, i) => (
              <ChatMessage key={i} role={msg.role} content={msg.content} />
            ))}
            {isLoading && (
              <div className="flex gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent/30 text-accent-foreground">
                  <BookOpen className="h-4 w-4" />
                </div>
                <div className="rounded-2xl bg-chat-assistant px-4 py-3">
                  <div className="flex gap-1">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="mx-auto w-full max-w-3xl">
        <ChatInput onSend={handleSend} isLoading={isLoading} />
      </div>
    </div>
  );
};

export default Chat;
