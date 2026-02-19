import { Badge } from "./Badge";
import type { ConferenceStatus } from "@/types";
import { formatStatus } from "@/utils/format";

interface StatusBadgeProps {
  status: ConferenceStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const variantMap: Record<
    ConferenceStatus,
    React.ComponentProps<typeof Badge>["variant"]
  > = {
    upcoming: "success",
    past: "secondary",
    cancelled: "destructive",
    unknown: "outline",
  };

  return (
    <Badge variant={variantMap[status]}>
      {formatStatus(status)}
    </Badge>
  );
}
