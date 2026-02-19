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
import { useAddSource } from "./useConferences";
import type { SourceType } from "@/types";

const schema = z.object({
  type: z.enum(["website", "cfp", "twitter", "rss"] as const),
  url: z.string().url("Must be a valid URL"),
  refresh_interval_hours: z.coerce.number().int().positive().optional(),
  refresh_enabled: z.boolean().default(true),
});

type FormValues = z.infer<typeof schema>;

export function AddSourceDialog({ conferenceId }: { conferenceId: string }) {
  const [open, setOpen] = useState(false);
  const addSource = useAddSource(conferenceId);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { type: "website", refresh_enabled: true },
  });

  const onSubmit = async (values: FormValues) => {
    await addSource.mutateAsync({
      type: values.type as SourceType,
      url: values.url,
      refresh_interval_hours: values.refresh_interval_hours,
      refresh_enabled: values.refresh_enabled,
    });
    reset();
    setOpen(false);
  };

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <Button variant="outline" size="sm">
          <PlusCircle className="h-3.5 w-3.5" />
          Add Source
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
              Add Source
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

          {addSource.isError && (
            <ErrorMessage error={addSource.error} className="mb-4" />
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <FormField label="Type" required error={errors.type?.message}>
              <select
                {...register("type")}
                className="h-9 w-full rounded-md border border-slate-200 bg-white px-3 py-1 text-sm"
              >
                <option value="website">Website</option>
                <option value="cfp">CFP</option>
                <option value="twitter">Twitter</option>
                <option value="rss">RSS</option>
              </select>
            </FormField>

            <FormField label="URL" required error={errors.url?.message}>
              <Input
                {...register("url")}
                placeholder="https://example.com/cfp"
                error={Boolean(errors.url)}
              />
            </FormField>

            <FormField
              label="Refresh interval (hours)"
              error={errors.refresh_interval_hours?.message}
              hint="Leave blank to use default (24 h)"
            >
              <Input
                type="number"
                {...register("refresh_interval_hours")}
                placeholder="24"
              />
            </FormField>

            <div className="flex items-center gap-2">
              <input
                id="refresh_enabled"
                type="checkbox"
                {...register("refresh_enabled")}
                className="rounded"
              />
              <label htmlFor="refresh_enabled" className="text-sm text-slate-700">
                Enable automatic refresh
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Dialog.Close asChild>
                <Button type="button" variant="outline" size="sm">
                  Cancel
                </Button>
              </Dialog.Close>
              <Button type="submit" size="sm" loading={addSource.isPending}>
                Add Source
              </Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
