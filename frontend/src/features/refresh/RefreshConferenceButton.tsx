import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useRefreshConference } from "./useRefresh";

export function RefreshConferenceButton({
  conferenceId,
}: {
  conferenceId: string;
}) {
  const refresh = useRefreshConference();

  return (
    <Button
      variant="outline"
      size="sm"
      loading={refresh.isPending}
      onClick={() => refresh.mutate(conferenceId)}
      title="Re-fetch all sources and update extracted data"
    >
      <RefreshCw className="h-3.5 w-3.5" />
      Refresh
    </Button>
  );
}
