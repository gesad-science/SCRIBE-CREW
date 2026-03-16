import { useNavigate } from "react-router-dom";
import { Feather, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

const Index = () => {
  const navigate = useNavigate();

  return (
    <div className="flex h-screen flex-col items-center justify-center bg-background px-4 text-center">
      <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-secondary">
        <Feather className="h-10 w-10 text-accent" />
      </div>
      <h1 className="font-display text-4xl font-bold tracking-tight text-foreground mb-3">
        Scribe
      </h1>
      <p className="max-w-md text-lg text-muted-foreground leading-relaxed mb-10">
        Your academic review assistant. Analyze papers, theses, and scientific articles with AI.
      </p>
      <Button size="lg" className="gap-2 text-base" onClick={() => navigate("/chat")}>
        Start a conversation
        <ArrowRight className="h-4 w-4" />
      </Button>
    </div>
  );
};

export default Index;
