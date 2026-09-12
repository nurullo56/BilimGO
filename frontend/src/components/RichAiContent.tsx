import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import DOMPurify from 'dompurify';
import { Check, Copy, Terminal } from 'lucide-react';
import { triggerHaptic } from '../services/telegram';

interface RichAiContentProps {
  content: string;
  isUser?: boolean;
}

export const RichAiContent: React.FC<RichAiContentProps> = ({ content, isUser = false }) => {
  // Sanitize content while preserving safe HTML tags
  const sanitizedContent = React.useMemo(() => {
    if (!content) return '';
    return DOMPurify.sanitize(content, {
      ADD_TAGS: ['iframe', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'code', 'pre', 'mark', 'kbd'],
      ADD_ATTR: ['target', 'rel', 'style', 'class', 'className'],
    });
  }, [content]);

  if (isUser) {
    return <div className="whitespace-pre-wrap leading-relaxed text-xs sm:text-sm">{content}</div>;
  }

  return (
    <div className="rich-ai-content text-xs sm:text-sm leading-relaxed space-y-2 text-tg-text break-words">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-base sm:text-lg font-extrabold text-tg-text mt-3 mb-1.5 pb-1 border-b border-tg-secondary">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-sm sm:text-base font-bold text-tg-text mt-2.5 mb-1 pb-0.5 border-b border-tg-secondary/50">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-xs sm:text-sm font-bold text-blue-600 dark:text-blue-400 mt-2 mb-1">
              {children}
            </h3>
          ),
          p: ({ children }) => (
            <p className="my-1.5 leading-relaxed text-tg-text/95">
              {children}
            </p>
          ),
          strong: ({ children }) => (
            <strong className="font-bold text-tg-text tracking-tight">
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em className="italic text-tg-text/90">
              {children}
            </em>
          ),
          ul: ({ children }) => (
            <ul className="list-disc pl-5 my-2 space-y-1 text-tg-text/90">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-5 my-2 space-y-1 text-tg-text/90">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed pl-0.5">
              {children}
            </li>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-blue-500 bg-blue-500/10 pl-3.5 pr-2 py-1.5 rounded-r-xl my-2 italic text-tg-text/90">
              {children}
            </blockquote>
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 underline underline-offset-2 hover:text-blue-600 font-medium"
            >
              {children}
            </a>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-2.5 rounded-xl border border-tg-secondary shadow-xs">
              <table className="w-full text-left text-xs border-collapse">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-tg-secondary/80 font-bold border-b border-tg-secondary text-tg-text">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-y divide-tg-secondary">
              {children}
            </tbody>
          ),
          tr: ({ children }) => (
            <tr className="hover:bg-tg-secondary/30 transition-colors">
              {children}
            </tr>
          ),
          th: ({ children }) => (
            <th className="px-3 py-2 font-semibold">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-2 text-tg-text/90">
              {children}
            </td>
          ),
          code: ({ node, className, children, ...props }: any) => {
            const match = /language-(\w+)/.exec(className || '');
            const codeString = String(children).replace(/\n$/, '');
            const isMultiLine = codeString.includes('\n') || Boolean(match);

            if (isMultiLine) {
              return (
                <CodeBlock language={match ? match[1] : ''} code={codeString} />
              );
            }

            return (
              <code
                className="px-1.5 py-0.5 rounded-md bg-tg-secondary/90 text-blue-600 dark:text-blue-400 font-mono text-[11px] font-semibold border border-tg-secondary inline-block"
                {...props}
              >
                {children}
              </code>
            );
          },
          hr: () => <hr className="my-3 border-tg-secondary" />,
        }}
      >
        {sanitizedContent}
      </ReactMarkdown>
    </div>
  );
};

// Extracted syntax & copy-enabled CodeBlock component
interface CodeBlockProps {
  language?: string;
  code: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ language, code }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    triggerHaptic('light');
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-2.5 rounded-2xl overflow-hidden border border-tg-secondary bg-slate-950 dark:bg-slate-900 text-slate-100 shadow-sm font-mono text-xs">
      {/* Code Header Bar */}
      <div className="flex items-center justify-between px-3.5 py-2 bg-slate-900/90 dark:bg-slate-800/90 border-b border-slate-800 text-[11px] text-slate-400">
        <div className="flex items-center gap-1.5">
          <Terminal className="w-3.5 h-3.5 text-blue-400" />
          <span className="font-semibold uppercase tracking-wider text-[10px] text-slate-300">
            {language || 'kod'}
          </span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-2 py-0.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors cursor-pointer text-[10px]"
          title="Kodni nusxalash"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400 font-medium">Nusxalandi</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Nusxa olish</span>
            </>
          )}
        </button>
      </div>

      {/* Code Body */}
      <div className="p-3.5 overflow-x-auto font-mono text-[11px] leading-relaxed text-slate-200">
        <pre className="m-0 whitespace-pre">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
};
