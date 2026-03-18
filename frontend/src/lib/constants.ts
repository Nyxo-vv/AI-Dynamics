export const CATEGORY_LABELS: Record<string, string> = {
  all: "全部",
  research: "研究突破",
  product: "产品发布",
  opensource: "开源动态",
  news: "行业新闻",
  funding: "投融资",
  policy: "政策法规",
  community: "社区讨论",
};

export const CATEGORY_COLORS: Record<string, { bg: string; text: string }> = {
  all: { bg: "bg-gray-50", text: "text-gray-700" },
  research: { bg: "bg-emerald-50", text: "text-emerald-700" },
  product: { bg: "bg-blue-50", text: "text-blue-700" },
  opensource: { bg: "bg-violet-50", text: "text-violet-700" },
  news: { bg: "bg-amber-50", text: "text-amber-700" },
  funding: { bg: "bg-pink-50", text: "text-pink-700" },
  policy: { bg: "bg-indigo-50", text: "text-indigo-700" },
  community: { bg: "bg-teal-50", text: "text-teal-700" },
};

export const CATEGORY_ORDER = [
  "research",
  "product",
  "opensource",
  "news",
  "funding",
  "policy",
  "community",
] as const;
