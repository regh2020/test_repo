import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { PlusCircle, X } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { FormField } from "@/components/ui/FormField";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { cn } from "@/utils/cn";
import { useAddDate } from "./useConferences";

const IMPORTANT_DATE_TYPES = [
  { value: "submission_deadline", label: "Submission Deadline" },
  { value: "notification", label: "Notification" },
  { value: "camera_ready", label: "Camera Ready" },
  { value: "workshop_deadline", label: "Workshop Deadline" },
  { value: "early_registration", label: "Early Registration" },
  { value: "conference_start", label: "Conference Start" },
  { value: "conference_end", label: "Conference End" },
  { value: "other", label: "Other" },
] as const;

const schema = z.object({
  type: z.enum([
    "submission_deadline",
    "notification",
    "camera_ready",
    "workshop_deadline",
    "early_registration",
    "conference_start",
    "conference_end",
    "other",
  ]),
  date_time: z.string().min(1, "Date is required"),
  timezone: z.string().optional(),
  note: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export function AddDateDialog({ conferenceId }: { conferenceId: string }) {
  const [open, setOpen] = useState(false);
  const addDate = useAddDate(conferenceId);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { type: "submission_deadline" },
  });

  const onSubmit = async (values: FormValues) => {
    await addDate.mutateAsync({
      type: values.type,
      date_time: new Date(values.date_time).toISOString(),
      timezone: values.timezone || null,
      note: values.note || null,
    });
    reset();
    setOpen(false);
  };

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <Button variant="outline" size="sm">
          <PlusCircle className="h-3.5 w-3.5" />
          Add Date
        </Button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30 z-40" />
        <Dialog.Content
          className={cn(
            "fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2",
            "z-50 w-full max-w-md rounded-lg bg-white border border-slate-200 shadow-xl p-6"
          )}
        >
          <div className="flex items-center justify-between mb-4">
            <Dialog.Title className="font-semibold text-slate-900">
              Add Important Date
            </Dialog.Title>
            <Dialog.Close asChild>
              <button
                aria-label="Close"
                className="text-slate-400 hover:text-slate-700"
              >
                <X className="h-4 w-4" />
              </button>
            </Dialog.Close>
          </div>

          {addDate.isError && (
            <ErrorMessage error={addDate.error} className="mb-4" />
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <FormField label="Type" required error={errors.type?.message}>
              <select
                {...register("type")}
                className="h-9 w-full rounded-md border border-slate-200 bg-white px-3 py-1 text-sm"
              >
                {IMPORTANT_DATE_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </FormField>

            <FormField label="Date" required error={errors.date_time?.message}>
              <Input
                type="datetime-local"
                {...register("date_time")}
                error={Boolean(errors.date_time)}
              />
            </FormField>

            <FormField label="Timezone" error={errors.timezone?.message}>
              <Input
                {...register("timezone")}
                placeholder="e.g. UTC, America/New_York"
              />
            </FormField>

            <FormField label="Note" error={errors.note?.message}>
              <Input {...register("note")} placeholder="Optional note…" />
            </FormField>

            <div className="flex justify-end gap-2 pt-2">
              <Dialog.Close asChild>
                <Button type="button" variant="outline" size="sm">
                  Cancel
                </Button>
              </Dialog.Close>
              <Button type="submit" size="sm" loading={addDate.isPending}>
                Add Date
              </Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
