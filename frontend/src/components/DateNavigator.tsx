import { ChevronLeft, ChevronRight } from "lucide-react";
import type { BriefingStatus } from "@/lib/types";

interface DateNavigatorProps {
  days: BriefingStatus[];
  selectedDate: string;
  onSelect: (date: string) => void;
}

function formatShort(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

function isToday(dateStr: string): boolean {
  return dateStr === new Date().toISOString().slice(0, 10);
}

export function DateNavigator({ days, selectedDate, onSelect }: DateNavigatorProps) {
  const idx = days.findIndex((d) => d.date === selectedDate);

  const canPrev = idx < days.length - 1;
  const canNext = idx > 0;

  return (
    <div className="flex items-center justify-center gap-1">
      <button
        onClick={() => canPrev && onSelect(days[idx + 1].date)}
        disabled={!canPrev}
        className="p-1.5 rounded-md hover:bg-muted disabled:opacity-30 transition-colors"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>

      <div className="flex gap-1">
        {[...days].reverse().map((day) => {
          const selected = day.date === selectedDate;
          const today = isToday(day.date);
          return (
            <button
              key={day.date}
              onClick={() => onSelect(day.date)}
              className={`flex flex-col items-center px-3 py-1.5 rounded-lg text-xs transition-all duration-150 ${
                selected
                  ? "bg-white shadow-sm border border-border text-accent-dark font-semibold"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <span>{today ? "今天" : formatShort(day.date)}</span>
              <span
                className={`mt-1 w-1.5 h-1.5 rounded-full ${
                  day.generated ? "bg-accent" : "bg-border"
                }`}
              />
            </button>
          );
        })}
      </div>

      <button
        onClick={() => canNext && onSelect(days[idx - 1].date)}
        disabled={!canNext}
        className="p-1.5 rounded-md hover:bg-muted disabled:opacity-30 transition-colors"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}
