import { useEffect, useState, useCallback } from "react";
import { Loader2 } from "lucide-react";
import { getFetchStatus } from "@/lib/api";
import type { FetchStatus } from "@/lib/types";

interface FetchProgressProps {
  active: boolean;
  onComplete?: () => void;
}

export function FetchProgress({ active, onComplete }: FetchProgressProps) {
  const [status, setStatus] = useState<FetchStatus | null>(null);

  const poll = useCallback(async () => {
    try {
      const s = await getFetchStatus();
      setStatus(s);
      if (s.status === "idle" && active) {
        onComplete?.();
      }
    } catch {
      // silent
    }
  }, [active, onComplete]);

  useEffect(() => {
    if (!active) {
      setStatus(null);
      return;
    }
    poll();
    const interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, [active, poll]);

  if (!active || !status || status.status === "idle") return null;

  const isFetching = status.status === "fetching";
  const isProcessing = status.status === "processing";

  const pct = isFetching
    ? status.total_sources > 0
      ? Math.round((status.processed_sources / status.total_sources) * 100)
      : 0
    : status.llm_total > 0
      ? Math.round((status.llm_processed / status.llm_total) * 100)
      : 0;

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-2.5 flex items-center gap-3 text-sm text-blue-800">
      <Loader2 className="h-4 w-4 animate-spin shrink-0" />
      <div className="flex-1">
        {isFetching && (
          <>
            <span>
              正在抓取... {status.processed_sources}/{status.total_sources} 个来源
            </span>
            {status.new_articles > 0 && (
              <span className="ml-2 opacity-70">({status.new_articles} 篇新文章)</span>
            )}
          </>
        )}
        {isProcessing && (
          <span>
            正在处理文章... {status.llm_processed}/{status.llm_total}
          </span>
        )}
      </div>
      <div className="w-24 h-1.5 bg-blue-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs opacity-60 shrink-0">{pct}%</span>
    </div>
  );
}
