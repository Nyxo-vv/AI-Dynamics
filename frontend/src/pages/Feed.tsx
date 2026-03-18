import { useState, useEffect, useCallback } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ArticleCard } from "@/components/ArticleCard";
import { CategoryBadge } from "@/components/CategoryBadge";
import { SearchBar } from "@/components/SearchBar";
import { CardSkeleton } from "@/components/Skeleton";
import { getArticles, updateArticle } from "@/lib/api";
import { CATEGORY_ORDER } from "@/lib/constants";
import type { Article } from "@/lib/types";

export default function FeedPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getArticles({
        page,
        per_page: 20,
        tag: activeTag ?? undefined,
        search: search || undefined,
      });
      setArticles(res.items);
      setTotalPages(res.pages ?? 1);
      setTotal(res.total);
    } catch {
      setArticles([]);
    } finally {
      setLoading(false);
    }
  }, [page, activeTag, search]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSearch = useCallback((q: string) => {
    setSearch(q);
    setPage(1);
  }, []);

  const handleTagFilter = useCallback((tag: string | null) => {
    setActiveTag(tag);
    setPage(1);
  }, []);

  const handleToggleStar = useCallback(
    async (id: number, starred: boolean) => {
      try {
        await updateArticle(id, { is_starred: starred });
        setArticles((prev) =>
          prev.map((a) => (a.id === id ? { ...a, is_starred: starred } : a))
        );
      } catch {
        // silent
      }
    },
    []
  );

  return (
    <div className="space-y-5">
      {/* Search + filter */}
      <SearchBar onSearch={handleSearch} placeholder="搜索文章标题、摘要..." />

      <div className="flex flex-wrap items-center gap-2">
        <CategoryBadge
          tag="all"
          active={!activeTag}
          onClick={() => handleTagFilter(null)}
        />
        {CATEGORY_ORDER.map((tag) => (
          <CategoryBadge
            key={tag}
            tag={tag}
            active={activeTag === tag}
            onClick={() => handleTagFilter(activeTag === tag ? null : tag)}
          />
        ))}
        <span className="ml-auto text-sm text-muted-foreground">
          共 {total} 篇
        </span>
      </div>

      {/* Article list */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : articles.length === 0 ? (
        <div className="text-center text-muted-foreground py-20">
          暂无文章
        </div>
      ) : (
        <div className="space-y-3">
          {articles.map((article) => (
            <ArticleCard
              key={article.id}
              article={article}
              onToggleStar={handleToggleStar}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 pt-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            上一页
          </Button>
          <span className="text-sm text-muted-foreground">
            {page} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            下一页
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      )}
    </div>
  );
}
