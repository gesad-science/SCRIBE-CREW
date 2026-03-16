import ReactMarkdown from "react-markdown";
import { BookOpen, User, Copy, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
}

// Função para substituir URLs por [domínio](url)
function replaceUrlsWithMarkdown(text: string): string {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  return text.replace(urlRegex, (url) => {
    try {
      const urlObj = new URL(url);
      const domain = urlObj.hostname.replace(/^www\./, '');
      return `[${domain}](${url})`;
    } catch {
      return url;
    }
  });
}

// Parser simples de BibTeX (extrai campos principais)
function parseBibTeX(bibtex: string) {
  const entryTypeMatch = bibtex.match(/@(\w+)\{/);
  const entryType = entryTypeMatch ? entryTypeMatch[1] : "article";

  // Remove @tipo{ e o } final
  const content = bibtex.replace(/^@\w+\{/, '').replace(/\}\s*$/, '').trim();

  const fields: Record<string, string> = {};
  let current = '';
  let braceLevel = 0;
  const parts: string[] = [];

  // Divide os campos por vírgula, respeitando chaves aninhadas
  for (let char of content) {
    if (char === '{') braceLevel++;
    else if (char === '}') braceLevel--;

    if (char === ',' && braceLevel === 0) {
      parts.push(current);
      current = '';
    } else {
      current += char;
    }
  }
  if (current) parts.push(current);

  parts.forEach(part => {
    const eqIndex = part.indexOf('=');
    if (eqIndex !== -1) {
      const key = part.slice(0, eqIndex).trim();
      let value = part.slice(eqIndex + 1).trim();
      // Remove chaves externas
      if (value.startsWith('{') && value.endsWith('}')) {
        value = value.slice(1, -1);
      }
      fields[key] = value;
    }
  });

  return { type: entryType, fields };
}

// Componente que exibe um card BibTeX
const BibTeXCard = ({ bibtex }: { bibtex: string }) => {
  const [expanded, setExpanded] = useState(false);
  const { fields } = parseBibTeX(bibtex);

  const title = fields.title || "Sem título";
  const author = fields.author || "Autor desconhecido";
  const year = fields.year || "s.d.";
  const journal = fields.journal || fields.booktitle || "Publicação desconhecida";

  return (
    <div className="my-2 rounded-lg border border-gray-200 bg-gray-50 p-3 font-sans text-sm dark:border-gray-700 dark:bg-gray-800">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="font-medium text-gray-900 dark:text-gray-100">{title}</p>
          <p className="text-gray-600 dark:text-gray-400">{author} • {year}</p>
          <p className="text-gray-500 dark:text-gray-500">{journal}</p>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="ml-2 rounded p-1 hover:bg-gray-200 dark:hover:bg-gray-700"
          title="Ver BibTeX completo"
        >
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>
      {expanded && (
        <div className="mt-2">
          <pre className="overflow-x-auto rounded bg-gray-100 p-2 text-xs dark:bg-gray-900">
            {bibtex}
          </pre>
          <button
            onClick={() => navigator.clipboard.writeText(bibtex)}
            className="mt-1 flex items-center gap-1 text-xs text-blue-600 hover:underline dark:text-blue-400"
          >
            <Copy size={12} /> Copy BibTeX
          </button>
        </div>
      )}
    </div>
  );
};

// Função para extrair blocos BibTeX com posições
function extractBibTeXBlocks(text: string): { start: number; end: number; bibtex: string }[] {
  const blocks = [];
  let i = 0;

  while (i < text.length) {
    const atIndex = text.indexOf('@', i);
    if (atIndex === -1) break;

    // Verifica se é início de um bloco BibTeX (ex: @article{, @book{, etc.)
    const match = text.slice(atIndex).match(/^@[A-Za-z]+\{/);
    if (!match) {
      i = atIndex + 1;
      continue;
    }

    const start = atIndex;
    let braceCount = 1;
    let j = atIndex + match[0].length; // posição após o {

    while (j < text.length && braceCount > 0) {
      if (text[j] === '{') braceCount++;
      else if (text[j] === '}') braceCount--;
      j++;
    }

    if (braceCount === 0) {
      const end = j; // após o } final
      const bibtex = text.slice(start, end);
      blocks.push({ start, end, bibtex });
      i = end;
    } else {
      i = atIndex + 1;
    }
  }

  return blocks;
}

const ChatMessage = ({ role, content }: ChatMessageProps) => {
  const isUser = role === "user";

  // Processa o conteúdo: divide em partes (texto normal e blocos BibTeX)
  const renderContent = () => {
    const blocks = extractBibTeXBlocks(content);
    if (blocks.length === 0) {
      // Se não há BibTeX, apenas aplica o markdown com links substituídos
      return (
        <ReactMarkdown
          components={{
            a: ({ href, children }) => (
              <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline dark:text-blue-400">
                {children}
              </a>
            ),
          }}
        >
          {replaceUrlsWithMarkdown(content)}
        </ReactMarkdown>
      );
    }

    // Constrói uma lista de partes
    const parts: JSX.Element[] = [];
    let lastIndex = 0;

    blocks.forEach((block, idx) => {
      // Texto antes do bloco
      if (block.start > lastIndex) {
        const textBefore = content.slice(lastIndex, block.start);
        parts.push(
          <ReactMarkdown
            key={`text-${idx}`}
            components={{
              a: ({ href, children }) => (
                <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline dark:text-blue-400">
                  {children}
                </a>
              ),
            }}
          >
            {replaceUrlsWithMarkdown(textBefore)}
          </ReactMarkdown>
        );
      }
      // Bloco BibTeX
      parts.push(<BibTeXCard key={`bib-${idx}`} bibtex={block.bibtex} />);
      lastIndex = block.end;
    });

    // Texto após o último bloco
    if (lastIndex < content.length) {
      const textAfter = content.slice(lastIndex);
      parts.push(
        <ReactMarkdown
          key="text-last"
          components={{
            a: ({ href, children }) => (
              <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline dark:text-blue-400">
                {children}
              </a>
            ),
          }}
        >
          {replaceUrlsWithMarkdown(textAfter)}
        </ReactMarkdown>
      );
    }

    return <>{parts}</>;
  };

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
          isUser ? "bg-primary text-primary-foreground" : "bg-accent/30 text-accent-foreground"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <BookOpen className="h-4 w-4" />}
      </div>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-chat-user text-chat-user-foreground"
            : "bg-chat-assistant text-chat-assistant-foreground"
        }`}
      >
        <div className="prose prose-sm max-w-none prose-headings:font-display prose-headings:text-inherit prose-p:text-inherit prose-strong:text-inherit prose-code:font-mono prose-code:text-xs">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
