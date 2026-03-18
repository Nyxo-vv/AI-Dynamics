import { ExternalLink, Star } from "lucide-react";
import { CategoryBadge } from "@/components/CategoryBadge";
import type { Article } from "@/lib/types";

interface ArticleCardProps {
  article: Article;
  compact?: boolean;
  onToggleStar?: (id: number, starred: boolean) => void;
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const now = Date.now();
  const diff = now - date.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}小时前`;
  const days = Math.floor(hours / 24);
  return `${days}天前`;
}

export function ArticleCard({ article, compact, onToggleStar }: ArticleCardProps) {
  const title = article.title_zh || article.title;
  const summary = article.summary_zh;

  if (compact) {
    return (
      <div className="group flex items-start gap-3 py-3 px-4 hover:bg-hover-bg transition-colors duration-150 border-l-3 border-transparent hover:border-accent">
        <div className="flex-1 min-w-0">
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[15px] font-medium text-foreground hover:text-accent-dark line-clamp-1"
          >
            {title}
          </a>
          {summary && (
            <p className="text-sm text-muted-foreground line-clamp-1 mt-0.5">
              {summary}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0 text-xs text-muted-foreground mt-0.5">
          {article.source_name && (
            <span className="bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">
              {article.source_name}
            </span>
          )}
          <span>{timeAgo(article.published_at)}</span>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="group bg-card rounded-xl p-5 shadow-[0_1px_3px_rgba(0,0,0,0.06)] hover:shadow-md border border-transparent hover:border-l-3 hover:border-l-accent transition-all duration-150 hover:-translate-y-px">
      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block"
      >
        <h3 className="text-lg font-semibold text-foreground leading-snug line-clamp-2 group-hover:text-accent-dark transition-colors">
          {title}
        </h3>
      </a>

      {summary && (
        <p className="text-[15px] leading-relaxed text-text-tertiary mt-2 line-clamp-2">
          {summary}
        </p>
      )}

      <div className="flex items-center justify-between mt-3">
        <div className="flex items-center gap-2">
          {article.tags?.map((tag) => (
            <CategoryBadge key={tag} tag={tag} />
          ))}
          {article.source_name && (
            <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">
              {article.source_name}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{timeAgo(article.published_at)}</span>
          {onToggleStar && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleStar(article.id, !article.is_starred);
              }}
              className="p-1 hover:text-amber-500 transition-colors"
            >
              <Star
                className={`h-4 w-4 ${article.is_starred ? "fill-amber-400 text-amber-400" : ""}`}
              />
            </button>
          )}
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1 hover:text-accent transition-colors"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      </div>
    </div>
  );
}
