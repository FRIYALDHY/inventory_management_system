import { Inbox } from "lucide-react";

export function EmptyState({ title = "Belum ada data" }: { title?: string }) {
  return (
    <div className="flex min-h-32 flex-col items-center justify-center rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
      <Inbox className="mb-2 h-5 w-5" />
      {title}
    </div>
  );
}

