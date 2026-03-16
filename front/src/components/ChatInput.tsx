import { useState, useRef } from "react";
import { Send, Paperclip, X, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface ChatInputProps {
  onSend: (message: string, pdf?: File) => void;
  isLoading: boolean;
}

const ChatInput = ({ onSend, isLoading }: ChatInputProps) => {
  const [message, setMessage] = useState("");
  const [pdf, setPdf] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if (!message.trim() && !pdf) return;
    onSend(message.trim(), pdf ?? undefined);
    setMessage("");
    setPdf(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-border bg-card p-4">
      {pdf && (
        <div className="mb-3 flex items-center gap-2 rounded-lg bg-secondary px-3 py-2 text-sm text-secondary-foreground">
          <FileText className="h-4 w-4 text-accent" />
          <span className="truncate flex-1 font-mono text-xs">{pdf.name}</span>
          <button onClick={() => setPdf(null)} className="text-muted-foreground hover:text-foreground transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
      <div className="flex items-end gap-2">
        <input
          ref={fileRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.[0]) setPdf(e.target.files[0]);
            e.target.value = "";
          }}
        />
        <Button
          variant="ghost"
          size="icon"
          className="shrink-0 text-muted-foreground hover:text-accent"
          onClick={() => fileRef.current?.click()}
          disabled={isLoading}
        >
          <Paperclip className="h-5 w-5" />
        </Button>
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask your academic question..."
          className="min-h-[44px] max-h-[160px] resize-none bg-secondary border-0 font-body text-sm focus-visible:ring-accent"
          rows={1}
          disabled={isLoading}
        />
        <Button
          size="icon"
          className="shrink-0 bg-primary text-primary-foreground hover:bg-primary/90"
          onClick={handleSend}
          disabled={isLoading || (!message.trim() && !pdf)}
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

export default ChatInput;
