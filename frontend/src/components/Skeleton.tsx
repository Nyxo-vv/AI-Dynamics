export function CardSkeleton() {
  return (
    <div className="bg-card rounded-xl p-5 border border-border animate-pulse">
      <div className="h-5 bg-muted rounded w-3/4 mb-3" />
      <div className="h-4 bg-muted rounded w-full mb-2" />
      <div className="h-4 bg-muted rounded w-2/3 mb-4" />
      <div className="flex gap-2">
        <div className="h-5 bg-muted rounded-full w-16" />
        <div className="h-5 bg-muted rounded-full w-20" />
        <div className="ml-auto h-4 bg-muted rounded w-12" />
      </div>
    </div>
  );
}

export function CardGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

export function ListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="bg-card rounded-xl border border-border divide-y divide-border">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="px-4 py-3 animate-pulse flex items-center gap-3">
          <div className="flex-1">
            <div className="h-4 bg-muted rounded w-2/3 mb-1.5" />
            <div className="h-3 bg-muted rounded w-1/2" />
          </div>
          <div className="h-5 bg-muted rounded-full w-16" />
          <div className="h-3 bg-muted rounded w-10" />
        </div>
      ))}
    </div>
  );
}
