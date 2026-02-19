import { useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useForm, useFieldArray, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { PlusCircle, Trash2, ChevronLeft } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { FormField } from "@/components/ui/FormField";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { SpinnerPage } from "@/components/ui/Spinner";
import { Card, CardContent } from "@/components/ui/Card";
import { ROUTES } from "@/router/routes";
import {
  useConference,
  useCreateConference,
  useUpdateConference,
} from "./useConferences";

const conferenceSchema = z.object({
  name: z.string().min(1, "Name is required"),
  acronym: z.string().optional(),
  series: z.string().optional(),
  topics: z.array(z.object({ value: z.string() })).default([]),
  city: z.string().optional(),
  country: z.string().optional(),
  venue: z.string().optional(),
  is_online: z.boolean().default(false),
  is_hybrid: z.boolean().default(false),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
  cfp_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  website_url: z
    .string()
    .url("Must be a valid URL")
    .optional()
    .or(z.literal("")),
  status: z
    .enum(["active", "past", "cancelled", "postponed"])
    .default("active"),
});

type FormValues = z.infer<typeof conferenceSchema>;

interface Props {
  mode: "create" | "edit";
}

export function ConferenceFormPage({ mode }: Props) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const existing = useConference(id ?? "");
  const createConference = useCreateConference();
  const updateConference = useUpdateConference(id ?? "");

  const {
    register,
    handleSubmit,
    reset,
    control,
    watch,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(conferenceSchema),
    defaultValues: { topics: [], is_online: false, is_hybrid: false, status: "active" },
  });

  const { fields: topicFields, append, remove } = useFieldArray({
    control,
    name: "topics",
  });

  const isOnline = watch("is_online");

  // Populate form in edit mode once data is loaded
  useEffect(() => {
    if (mode === "edit" && existing.data) {
      const c = existing.data;
      reset({
        name: c.name,
        acronym: c.acronym ?? "",
        series: c.series ?? "",
        topics: c.topics.map((v) => ({ value: v })),
        city: c.city ?? "",
        country: c.country ?? "",
        venue: c.venue ?? "",
        is_online: c.is_online,
        is_hybrid: c.is_hybrid,
        start_date: c.start_date?.slice(0, 10) ?? "",
        end_date: c.end_date?.slice(0, 10) ?? "",
        cfp_url: c.cfp_url ?? "",
        website_url: c.website_url ?? "",
        status: c.status,
      });
    }
  }, [mode, existing.data, reset]);

  const onSubmit = async (values: FormValues) => {
    const payload = {
      ...values,
      topics: values.topics.map((t) => t.value).filter(Boolean),
      acronym: values.acronym || null,
      series: values.series || null,
      city: values.city || null,
      country: values.country || null,
      venue: values.venue || null,
      start_date: values.start_date || null,
      end_date: values.end_date || null,
      cfp_url: values.cfp_url || null,
      website_url: values.website_url || null,
    };

    if (mode === "create") {
      const created = await createConference.mutateAsync(payload);
      navigate(ROUTES.conferenceDetail(created.id));
    } else {
      await updateConference.mutateAsync(payload);
      navigate(ROUTES.conferenceDetail(id!));
    }
  };

  if (mode === "edit" && existing.isPending) return <SpinnerPage />;
  if (mode === "edit" && existing.isError)
    return <ErrorMessage error={existing.error} />;

  const mutation = mode === "create" ? createConference : updateConference;

  return (
    <div>
      <div className="mb-1">
        <Button variant="ghost" size="sm" asChild>
          <Link to={mode === "edit" ? ROUTES.conferenceDetail(id!) : ROUTES.conferences}>
            <ChevronLeft className="h-4 w-4" />
            Back
          </Link>
        </Button>
      </div>
      <PageHeader
        title={mode === "create" ? "Add Conference" : "Edit Conference"}
        description={
          mode === "create"
            ? "Manually add a new conference record."
            : "Update conference details."
        }
      />

      {mutation.isError && (
        <ErrorMessage error={mutation.error} className="mb-6" />
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Basic info */}
          <Card>
            <CardContent className="pt-5 space-y-4">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                Basic Information
              </p>

              <FormField
                label="Conference Name"
                required
                error={errors.name?.message}
              >
                <Input
                  {...register("name")}
                  placeholder="International Conference on Machine Learning"
                  error={Boolean(errors.name)}
                />
              </FormField>

              <div className="grid grid-cols-2 gap-3">
                <FormField label="Acronym" error={errors.acronym?.message}>
                  <Input {...register("acronym")} placeholder="ICML" />
                </FormField>
                <FormField label="Series" error={errors.series?.message}>
                  <Input {...register("series")} placeholder="ICML 2025" />
                </FormField>
              </div>

              <FormField label="Status" error={errors.status?.message}>
                <select
                  {...register("status")}
                  className="h-9 w-full rounded-md border border-slate-200 bg-white px-3 py-1 text-sm"
                >
                  <option value="active">Active</option>
                  <option value="past">Past</option>
                  <option value="cancelled">Cancelled</option>
                  <option value="postponed">Postponed</option>
                </select>
              </FormField>

              {/* Topics */}
              <div>
                <p className="text-sm font-medium text-slate-700 mb-1.5">
                  Topics
                </p>
                <div className="space-y-2">
                  {topicFields.map((field, index) => (
                    <div key={field.id} className="flex gap-2">
                      <Input
                        {...register(`topics.${index}.value`)}
                        placeholder="e.g. Machine Learning"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => remove(index)}
                      >
                        <Trash2 className="h-3.5 w-3.5 text-slate-400" />
                      </Button>
                    </div>
                  ))}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => append({ value: "" })}
                  >
                    <PlusCircle className="h-3.5 w-3.5" />
                    Add Topic
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Location & dates */}
          <Card>
            <CardContent className="pt-5 space-y-4">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                Location & Dates
              </p>

              <div className="flex gap-4">
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    {...register("is_online")}
                    className="rounded"
                  />
                  Online
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    {...register("is_hybrid")}
                    className="rounded"
                  />
                  Hybrid
                </label>
              </div>

              {!isOnline && (
                <>
                  <FormField label="Venue" error={errors.venue?.message}>
                    <Input
                      {...register("venue")}
                      placeholder="Convention Center"
                    />
                  </FormField>
                  <div className="grid grid-cols-2 gap-3">
                    <FormField label="City" error={errors.city?.message}>
                      <Input {...register("city")} placeholder="Vienna" />
                    </FormField>
                    <FormField label="Country" error={errors.country?.message}>
                      <Input {...register("country")} placeholder="Austria" />
                    </FormField>
                  </div>
                </>
              )}

              <div className="grid grid-cols-2 gap-3">
                <FormField
                  label="Start Date"
                  error={errors.start_date?.message}
                >
                  <Input type="date" {...register("start_date")} />
                </FormField>
                <FormField label="End Date" error={errors.end_date?.message}>
                  <Input type="date" {...register("end_date")} />
                </FormField>
              </div>
            </CardContent>
          </Card>

          {/* URLs */}
          <Card className="lg:col-span-2">
            <CardContent className="pt-5 space-y-4">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                Links
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField
                  label="Website URL"
                  error={errors.website_url?.message}
                >
                  <Input
                    {...register("website_url")}
                    type="url"
                    placeholder="https://icml.cc"
                    error={Boolean(errors.website_url)}
                  />
                </FormField>
                <FormField label="CFP URL" error={errors.cfp_url?.message}>
                  <Input
                    {...register("cfp_url")}
                    type="url"
                    placeholder="https://icml.cc/cfp"
                    error={Boolean(errors.cfp_url)}
                  />
                </FormField>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Submit */}
        <div className="flex justify-end gap-3 mt-6">
          <Button
            type="button"
            variant="outline"
            onClick={() =>
              navigate(
                mode === "edit"
                  ? ROUTES.conferenceDetail(id!)
                  : ROUTES.conferences
              )
            }
          >
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending}>
            {mode === "create" ? "Create Conference" : "Save Changes"}
          </Button>
        </div>
      </form>
    </div>
  );
}
