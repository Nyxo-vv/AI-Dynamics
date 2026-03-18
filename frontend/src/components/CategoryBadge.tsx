import { CATEGORY_LABELS, CATEGORY_COLORS } from "@/lib/constants";

interface CategoryBadgeProps {
  tag: string;
  count?: number;
  active?: boolean;
  onClick?: () => void;
}

export function CategoryBadge({ tag, count, active, onClick }: CategoryBadgeProps) {
  const colors = CATEGORY_COLORS[tag] ?? { bg: "bg-gray-50", text: "text-gray-700" };
  const label = CATEGORY_LABELS[tag] ?? tag;

  const base = `inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium transition-all duration-150`;
  const colorClass = active
    ? `${colors.bg} ${colors.text} ring-1 ring-current`
    : `${colors.bg} ${colors.text}`;
  const interactive = onClick ? "cursor-pointer hover:opacity-80" : "";

  return (
    <span className={`${base} ${colorClass} ${interactive}`} onClick={onClick}>
      {label}
      {count != null && <span className="opacity-70">({count})</span>}
    </span>
  );
}
