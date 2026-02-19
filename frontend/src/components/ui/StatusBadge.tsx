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
    active: "success",
    past: "secondary",
    cancelled: "destructive",
    postponed: "outline",
  };

  return (
    <Badge variant={variantMap[status]}>
      {formatStatus(status)}
    </Badge>
  );
}
