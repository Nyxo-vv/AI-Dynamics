import { useState, useEffect, useCallback } from "react";
import { Loader2, Star } from "lucide-react";
import { ArticleCard } from "@/components/ArticleCard";
import { SearchBar } from "@/components/SearchBar";
import { getArticles, updateArticle } from "@/lib/api";
import type { Article } from "@/lib/types";

export default function StarredPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getArticles({
        starred: true,
        per_page: 100,
        search: search || undefined,
      });
      setArticles(res.items);
    } catch {
      setArticles([]);
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    load();
  }, [load]);

  const handleToggleStar = useCallback(
    async (id: number, starred: boolean) => {
      try {
        await updateArticle(id, { is_starred: starred });
        if (!starred) {
          // Remove from list when unstarred
          setArticles((prev) => prev.filter((a) => a.id !== id));
        }
      } catch {
        // silent
      }
    },
    []
  );

  return (
    <div className="space-y-5">
      <SearchBar onSearch={setSearch} placeholder="搜索收藏文章..." />

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : articles.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-20 text-muted-foreground">
          <Star className="h-10 w-10 opacity-30" />
          <p>{search ? "未找到匹配的收藏文章" : "暂无收藏，在文章卡片上点击星标即可收藏"}</p>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            共 {articles.length} 篇收藏
          </p>
          {articles.map((article) => (
            <ArticleCard
              key={article.id}
              article={article}
              onToggleStar={handleToggleStar}
            />
          ))}
        </div>
      )}
    </div>
  );
}
