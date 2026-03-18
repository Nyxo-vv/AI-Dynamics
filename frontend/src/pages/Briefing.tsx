import { useState, useEffect, useCallback } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ArticleCard } from "@/components/ArticleCard";
import { CategoryBadge } from "@/components/CategoryBadge";
import { DateNavigator } from "@/components/DateNavigator";
import { SearchBar } from "@/components/SearchBar";
import { CardGridSkeleton, ListSkeleton } from "@/components/Skeleton";
import {
  getBriefing,
  getRecentBriefings,
  generateBriefing,
  searchBriefings,
  updateArticle,
} from "@/lib/api";
import { CATEGORY_ORDER } from "@/lib/constants";
import type { Briefing, BriefingStatus, Article } from "@/lib/types";

const today = () => new Date().toISOString().slice(0, 10);

export default function BriefingPage() {
  const [selectedDate, setSelectedDate] = useState(today);
  const [days, setDays] = useState<BriefingStatus[]>([]);
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<Article[] | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  // Load recent days status
  const loadDays = useCallback(async () => {
    try {
      const res = await getRecentBriefings(7);
      setDays(res.items);
    } catch {
      // silent
    }
  }, []);

  // Load briefing for selected date
  const loadBriefing = useCallback(async (date: string) => {
    setLoading(true);
    setError(null);
    setBriefing(null);
    setSearchResults(null);
    setActiveCategory(null);
    try {
      const data = await getBriefing(date);
      setBriefing(data);
    } catch {
      setBriefing(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDays();
  }, [loadDays]);

  useEffect(() => {
    const currentDay = days.find((d) => d.date === selectedDate);
    if (currentDay?.generated) {
      loadBriefing(selectedDate);
    } else {
      setBriefing(null);
      setLoading(false);
    }
  }, [selectedDate, days, loadBriefing]);

  const handleGenerate = useCallback(async () => {
    setGenerating(true);
    setError(null);
    try {
      await generateBriefing(selectedDate);
      await loadDays();
      // Fetch full briefing with articles data
      await loadBriefing(selectedDate);
    } catch (e) {
      setError(e instanceof Error ? e.message : "生成失败");
    } finally {
      setGenerating(false);
    }
  }, [selectedDate, loadDays, loadBriefing]);

  const handleSearch = useCallback(
    async (query: string) => {
      if (!query) {
        setSearchResults(null);
        return;
      }
      try {
        const res = await searchBriefings(query, selectedDate);
        setSearchResults(res.items);
      } catch {
        setSearchResults([]);
      }
    },
    [selectedDate]
  );

  const handleToggleStar = useCallback(
    async (id: number, starred: boolean) => {
      try {
        await updateArticle(id, { is_starred: starred });
        // Update local state
        if (briefing) {
          const updated = { ...briefing };
          const a = updated.articles[id];
          if (a) {
            updated.articles[id] = { ...a, is_starred: starred };
            setBriefing(updated);
          }
        }
      } catch {
        // silent
      }
    },
    [briefing]
  );

  const toggleSection = useCallback((cat: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  }, []);

  const currentDay = days.find((d) => d.date === selectedDate);
  const isGenerated = currentDay?.generated ?? false;
  const articleCount = currentDay?.article_count ?? 0;

  // Headline articles
  const headlines =
    briefing?.content.headlines
      .map((h) => briefing.articles[h.article_id])
      .filter(Boolean) ?? [];

  // Sections with articles
  const sections =
    briefing?.content.sections
      .filter((s) => s.article_ids.length > 0)
      .sort(
        (a, b) =>
          CATEGORY_ORDER.indexOf(a.category as (typeof CATEGORY_ORDER)[number]) -
          CATEGORY_ORDER.indexOf(b.category as (typeof CATEGORY_ORDER)[number])
      ) ?? [];

  return (
    <div className="space-y-6">
      {/* Date Navigator */}
      {days.length > 0 && (
        <DateNavigator
          days={days}
          selectedDate={selectedDate}
          onSelect={setSelectedDate}
        />
      )}

      {/* Status bar + generate button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {!isGenerated && (
            <Button
              onClick={handleGenerate}
              disabled={generating || articleCount === 0}
              size="sm"
            >
              {generating ? (
                <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4 mr-1.5" />
              )}
              {generating ? "生成中..." : "生成今日简报"}
            </Button>
          )}
          {error && <span className="text-sm text-destructive">{error}</span>}
        </div>
        <span className="text-sm text-muted-foreground">
          {isGenerated ? "已生成" : "未生成"} | 共 {articleCount} 条
        </span>
      </div>

      {/* Search */}
      <SearchBar onSearch={handleSearch} />

      {/* Search results */}
      {searchResults !== null && (
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">
            搜索结果 ({searchResults.length})
          </h2>
          {searchResults.length === 0 ? (
            <p className="text-muted-foreground text-sm py-4 text-center">
              未找到匹配文章
            </p>
          ) : (
            <div className="bg-card rounded-xl border border-border divide-y divide-border">
              {searchResults.map((article) => (
                <ArticleCard
                  key={article.id}
                  article={article}
                  compact
                  onToggleStar={handleToggleStar}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-6">
          <CardGridSkeleton count={6} />
          <ListSkeleton count={4} />
        </div>
      )}

      {/* Empty state */}
      {!loading && !briefing && !searchResults && (
        <div className="text-center py-20 text-muted-foreground">
          {articleCount > 0 ? (
            <p>当天简报尚未生成，点击「生成今日简报」开始</p>
          ) : (
            <p>当天暂无文章数据，试试点击顶部「立即刷新」抓取最新内容</p>
          )}
        </div>
      )}

      {/* Briefing content */}
      {briefing && !searchResults && (
        <>
          {/* Headlines */}
          {headlines.length > 0 && (
            <section>
              <h2 className="text-2xl font-bold mb-4">头条 Top {headlines.length}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {headlines.map((article) => (
                  <ArticleCard
                    key={article.id}
                    article={article}
                    onToggleStar={handleToggleStar}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Category sections */}
          {sections.length > 0 && (
            <section>
              <h2 className="text-2xl font-bold mb-4">分类浏览</h2>

              {/* Category tabs */}
              <div className="flex flex-wrap gap-2 mb-4">
                {sections.map((s) => (
                  <CategoryBadge
                    key={s.category}
                    tag={s.category}
                    count={s.article_ids.length}
                    active={activeCategory === s.category}
                    onClick={() =>
                      setActiveCategory(
                        activeCategory === s.category ? null : s.category
                      )
                    }
                  />
                ))}
              </div>

              {/* Section lists */}
              {sections
                .filter((s) => !activeCategory || s.category === activeCategory)
                .map((section) => {
                  const sectionArticles = section.article_ids
                    .map((id) => briefing.articles[id])
                    .filter(Boolean);
                  const expanded = expandedSections.has(section.category);
                  const displayArticles = expanded
                    ? sectionArticles
                    : sectionArticles.slice(0, 8);
                  const hasMore = sectionArticles.length > 8;

                  return (
                    <div key={section.category} className="mb-6">
                      <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                        <CategoryBadge tag={section.category} />
                        <span className="text-muted-foreground text-sm font-normal">
                          ({sectionArticles.length})
                        </span>
                      </h3>
                      <div className="bg-card rounded-xl border border-border divide-y divide-border">
                        {displayArticles.map((article) => (
                          <ArticleCard
                            key={article.id}
                            article={article}
                            compact
                            onToggleStar={handleToggleStar}
                          />
                        ))}
                      </div>
                      {hasMore && (
                        <button
                          onClick={() => toggleSection(section.category)}
                          className="mt-2 text-sm text-accent hover:text-accent-dark transition-colors"
                        >
                          {expanded
                            ? "收起"
                            : `查看更多 (${sectionArticles.length - 8} 条) ↓`}
                        </button>
                      )}
                    </div>
                  );
                })}
            </section>
          )}

          {/* Stats */}
          {briefing.content.stats && (
            <section className="bg-card rounded-xl border border-border p-5">
              <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                数据统计
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-foreground">
                    {briefing.content.stats.total}
                  </div>
                  <div className="text-xs text-muted-foreground">文章总数</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-foreground">
                    {briefing.content.stats.headline_count}
                  </div>
                  <div className="text-xs text-muted-foreground">头条数</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-foreground">
                    {Object.keys(briefing.content.stats.by_category).length}
                  </div>
                  <div className="text-xs text-muted-foreground">分类数</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-foreground">
                    {Object.keys(briefing.content.stats.by_source).length}
                  </div>
                  <div className="text-xs text-muted-foreground">来源数</div>
                </div>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
