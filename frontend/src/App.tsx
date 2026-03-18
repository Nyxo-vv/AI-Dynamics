import { useState, useEffect, useCallback } from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ToastProvider, useToast } from "@/components/Toast";
import { FetchProgress } from "@/components/FetchProgress";
import { triggerFetch, getBacklogStatus } from "@/lib/api";
import BriefingPage from "@/pages/Briefing";
import FeedPage from "@/pages/Feed";
import StarredPage from "@/pages/Starred";

type Page = "briefing" | "feed" | "starred";

const TABS: { key: Page; label: string }[] = [
  { key: "briefing", label: "简报" },
  { key: "feed", label: "信息流" },
  { key: "starred", label: "收藏" },
];

function AppContent() {
  const [page, setPage] = useState<Page>("briefing");
  const [fetching, setFetching] = useState(false);
  const [backlog, setBacklog] = useState<{ unprocessed: number; total: number } | null>(null);
  const { toast } = useToast();

  // Poll backlog status every 10s
  useEffect(() => {
    const poll = async () => {
      try {
        const data = await getBacklogStatus();
        setBacklog(data);
      } catch {
        // silent — backend may not be running
      }
    };
    poll();
    const interval = setInterval(poll, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleFetch = useCallback(async () => {
    setFetching(true);
    try {
      await triggerFetch();
      toast("抓取任务已启动", "info");
    } catch (e) {
      toast(e instanceof Error ? e.message : "抓取启动失败", "error");
      setFetching(false);
    }
  }, [toast]);

  const handleFetchComplete = useCallback(() => {
    setFetching(false);
    toast("抓取完成", "success");
  }, [toast]);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white border-b border-border">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <h1 className="text-xl font-bold text-foreground tracking-tight">
            AI Daily
          </h1>

          <nav className="flex gap-1">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setPage(tab.key)}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  page === tab.key
                    ? "bg-white text-accent-dark shadow-sm border border-border"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>

          <Button
            variant="outline"
            size="sm"
            onClick={handleFetch}
            disabled={fetching}
          >
            <RefreshCw
              className={`h-4 w-4 mr-1.5 ${fetching ? "animate-spin" : ""}`}
            />
            {fetching ? "抓取中..." : "立即刷新"}
          </Button>
        </div>
      </header>

      {/* Fetch progress bar */}
      {fetching && (
        <div className="max-w-5xl mx-auto px-6 pt-3">
          <FetchProgress active={fetching} onComplete={handleFetchComplete} />
        </div>
      )}

      {/* Backlog progress bar */}
      {backlog && backlog.unprocessed > 0 && (
        <div className="max-w-5xl mx-auto px-6 pt-3">
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5 flex items-center gap-3 text-sm text-amber-800">
            <div className="flex-1">
              待处理文章：{backlog.unprocessed} / {backlog.total} 篇
              <span className="ml-2 opacity-60">
                (已完成 {Math.round(((backlog.total - backlog.unprocessed) / backlog.total) * 100)}%)
              </span>
            </div>
            <div className="w-32 h-1.5 bg-amber-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-500 rounded-full transition-all duration-500"
                style={{ width: `${((backlog.total - backlog.unprocessed) / backlog.total) * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      <main className="max-w-5xl mx-auto px-6 py-6">
        <ErrorBoundary>
          {page === "briefing" && <BriefingPage />}
          {page === "feed" && <FeedPage />}
          {page === "starred" && <StarredPage />}
        </ErrorBoundary>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AppContent />
    </ToastProvider>
  );
}
