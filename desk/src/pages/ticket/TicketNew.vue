<template>
  <div class="flex flex-col overflow-y-auto">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <CustomActions
          v-if="template.data?._customActions"
          :actions="template.data?._customActions"
        />
      </template>
    </LayoutHeader>
    <!-- Container -->
    <div
      class="flex flex-col gap-5 py-6 h-full flex-1 self-center overflow-auto mx-auto w-full max-w-4xl px-5"
    >
      <!-- custom fields descriptions -->
      <div v-if="Boolean(template.data?.about)" class="">
        <div class="prose-f" v-html="sanitize(template.data.about)" />
      </div>
      <div v-if="isCustomerPortal" class="flex flex-col gap-2">
        <label class="text-sm text-ink-gray-7">{{ __("Priority") }}</label>
        <TicketPrioritySelect v-model="priority" class="w-full sm:w-64" />
      </div>
      <div v-if="isCustomerPortal && companies.length" class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label for="ticket-company" class="text-sm text-ink-gray-7">
            {{ __("Kunde") }}
          </label>
          <select
            v-if="companies.length > 1"
            id="ticket-company"
            v-model="selectedCompany"
            class="w-full rounded-4 border border-outline-gray-2 bg-surface-base px-3 py-2 text-p-sm text-ink-gray-8 focus:border-outline-gray-4 focus:outline-none sm:max-w-md"
            @change="selectedProject = ''"
          >
            <option value="">{{ __("Kunde auswählen") }}</option>
            <option v-for="company in companies" :key="company" :value="company">
              {{ company }}
            </option>
          </select>
          <div v-else id="ticket-company" class="text-p-sm font-medium text-ink-gray-9">
            {{ activeCompany }}
          </div>
        </div>
        <div v-if="companyProjects.length" class="flex flex-col gap-2">
          <label for="ticket-project" class="text-sm text-ink-gray-7">
            {{ __("Projekt") }}
          </label>
          <select
            v-if="companyProjects.length > 1"
            id="ticket-project"
            v-model="selectedProject"
            class="w-full rounded-4 border border-outline-gray-2 bg-surface-base px-3 py-2 text-p-sm text-ink-gray-8 focus:border-outline-gray-4 focus:outline-none sm:max-w-md"
          >
            <option value="">{{ __("Projekt auswählen") }}</option>
            <option
              v-for="project in companyProjects"
              :key="project.customer"
              :value="project.customer"
            >
              {{ project.label }}
            </option>
          </select>
          <div
            v-else-if="companyProjects[0].project_label"
            id="ticket-project"
            class="text-p-sm font-medium text-ink-gray-9"
          >
            {{ companyProjects[0].label }}
          </div>
        </div>
      </div>
      <!-- custom fields -->
      <div
        class="grid grid-cols-1 gap-4 sm:grid-cols-3"
        v-if="Boolean(visibleFields)"
      >
        <UniInput
          v-for="field in visibleFields"
          :key="field.fieldname"
          :field="field"
          :value="templateFields[field.fieldname]"
          @change="
            (e) => handleOnFieldChange(e, field.fieldname, field.fieldtype)
          "
        >
          <template v-if="field.fieldname === 'priority'" #label-extra>
            <template
              v-if="
                ticketPriorityResource.dataMap[templateFields[field.fieldname]]
                  ?.description
              "
            >
              <Tooltip
                :text="
                  ticketPriorityResource.dataMap[
                    templateFields[field.fieldname]
                  ].description.trim()
                "
              >
                <lucide-circle-question-mark class="h-4 w-4 text-ink-gray-6" />
              </Tooltip>
            </template>
          </template>
        </UniInput>
      </div>
      <!-- existing fields -->
      <div
        class="flex flex-col"
        :class="(subject.length >= 2 || description.length) && 'gap-5'"
      >
        <div class="flex flex-col gap-2">
          <span class="block text-sm text-ink-gray-6">
            {{ __("Subject") }}
            <span class="place-self-center text-ink-red-5"> * </span>
          </span>
          <!-- TextInput rings only on :focus-visible, so a click leaves the
               field with no outline; class lands on its wrapper, not the input -->
          <TextInput
            v-model="subject"
            variant="outline"
            :placeholder="__('A short description')"
            maxlength="140"
          />
        </div>
        <SearchArticles
          v-if="isCustomerPortal"
          :query="subject"
          class="shadow-sm"
        />
        <div v-if="isCustomerPortal">
          <h4
            v-show="subject.length <= 2 && description.length === 0"
            class="text-p-sm text-ink-gray-4 ms-1"
          >
            {{ __("Please enter a subject to continue") }}
          </h4>
          <TicketTextEditor
            v-show="subject.length > 2 || description.length > 0"
            ref="editor"
            v-model:attachments="attachments"
            v-model:content="description"
            :placeholder="__('Detailed explanation')"
            expand
            :uploadFunction="
              (file: any, options: any) =>
                track(uploadFunction(file, null, null, true, options))
            "
          >
            <template #bottom-right>
              <!-- A disabled button fires no pointer events, so the span
                   carries the hover for the tooltip -->
              <Tooltip
                :text="isUploading ? __('Please wait, media is uploading') : ''"
              >
                <span class="inline-flex">
                  <Button
                    :label="__('Submit')"
                    theme="gray"
                    variant="solid"
                    :disabled="!canSubmit"
                    @click="() => ticket.submit()"
                  />
                </span>
              </Tooltip>
            </template>
          </TicketTextEditor>
        </div>
      </div>

      <!-- for agent portal -->
      <div v-if="!isCustomerPortal">
        <TicketTextEditor
          ref="editor"
          v-model:attachments="attachments"
          v-model:content="description"
          :placeholder="__('Detailed explanation')"
          expand
          :uploadFunction="
            (file: any, options: any) =>
              track(uploadFunction(file, null, null, true, options))
          "
        >
          <template #bottom-right>
            <Tooltip
              :text="isUploading ? __('Please wait, media is uploading') : ''"
            >
              <span class="inline-flex">
                <Button
                  :label="__('Submit')"
                  theme="gray"
                  variant="solid"
                  :disabled="!canSubmit"
                  @click="() => ticket.submit()"
                />
              </span>
            </Tooltip>
          </template>
        </TicketTextEditor>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { LayoutHeader, UniInput } from "@/components";
import TicketPrioritySelect from "@/components/ticket/TicketPrioritySelect.vue";
import { useCustomerProjects } from "@/composables/useCustomerProjects";
import {
  handleLinkFieldUpdate,
  handleSelectFieldUpdate,
  parseField,
  setupCustomizations,
} from "@/composables/formCustomisation";
import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { Field } from "@/types";
import { useUploadTracker } from "@/composables/useUploadTracker";
import { isContentEmpty, isCustomerPortal, uploadFunction } from "@/utils";
import { useOnboarding } from "@framework/ui";
import {
  Breadcrumbs,
  Button,
  call,
  createListResource,
  createResource,
  TextInput,
  usePageMeta,
} from "frappe-ui";
import sanitizeHtml from "sanitize-html";
import { computed, defineAsyncComponent, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import SearchArticles from "../../components/SearchArticles.vue";
const TicketTextEditor = defineAsyncComponent(
  () => import("./TicketTextEditor.vue")
);

interface P {
  templateId?: string;
}

const props = withDefaults(defineProps<P>(), {
  templateId: "",
});

const route = useRoute();
const router = useRouter();
const { $dialog } = globalStore();
const { updateOnboardingStep } = useOnboarding("helpdesk") ?? {};
const { isManager, userId: userID } = useAuthStore();
const { projects } = useCustomerProjects();
const selectedCompany = ref("");
const selectedProject = ref("");
const companies = computed(() =>
  [...new Set(projects.value.map((project) => project.company))].sort()
);
const activeCompany = computed(
  () => selectedCompany.value || (companies.value.length === 1 ? companies.value[0] : "")
);
const companyProjects = computed(() =>
  projects.value.filter((project) => project.company === activeCompany.value)
);
const activeProject = computed(() =>
  selectedProject.value ||
  (companyProjects.value.length === 1 ? companyProjects.value[0].customer : "")
);
// Pre-filled by the command palette's "Create ticket …" fallback.
const { isUploading, track } = useUploadTracker();
// Read off the content model, not the editor ref: the ref is empty on the first
// render, which let the button paint enabled before flipping to disabled
const canSubmit = computed(
  () =>
    Boolean(subject.value) &&
    !isContentEmpty(description.value) &&
    !ticket.loading &&
    !isUploading.value &&
    (!isCustomerPortal.value || Boolean(activeProject.value))
);

const subject = ref(String(route.query.subject ?? ""));
const description = ref("");
const priority = ref("");
const attachments = ref([]);
const templateFields = reactive({});

const template = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket_template.api.get_one",
  makeParams: () => ({
    name: props.templateId || "Default",
  }),
  auto: true,
  onSuccess: (data) => {
    description.value = data.description_template || "";
    oldFields = window.structuredClone(data.fields || []);
    setupCustomizations(template, {
      doc: templateFields,
      call,
      router,
      $dialog,
      applyFilters,
    });
    setupTemplateFields(data.fields);
  },
});

function setupTemplateFields(fields) {
  fields.forEach((field: Field) => {
    templateFields[field.fieldname] = "";
  });
}

const ticketPriorityResource = createListResource({
  doctype: "HD Ticket Priority",
  fields: ["name", "description"],
  auto: true,
  cache: "ticketPriorities",
});

let oldFields = [];

function applyFilters(fieldname: string, filters: any = null) {
  const f: Field = template.data.fields.find((f) => f.fieldname === fieldname);
  if (!f) return;
  if (f.fieldtype === "Select") {
    handleSelectFieldUpdate(f, fieldname, filters, templateFields, oldFields);
  } else if (f.fieldtype === "Link") {
    handleLinkFieldUpdate(f, fieldname, filters, templateFields, oldFields);
  }
}

const customOnChange = computed(() => template.data?._customOnChange);

const visibleFields = computed(() => {
  let _fields = template.data?.fields?.filter(
    (f) => !isCustomerPortal.value || !["priority", "customer"].includes(f.fieldname)
  );
  if (!_fields) return [];
  return _fields.map((field) => parseField(field, templateFields));
});

function handleOnFieldChange(e: any, fieldname: string, fieldtype: string) {
  templateFields[fieldname] = e.value;
  const fieldDependentFns = customOnChange.value?.[fieldname];
  if (fieldDependentFns) {
    fieldDependentFns.forEach((fn: Function) => {
      fn(e.value, fieldtype);
    });
  }
}

const ticket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.new",
  debounce: 300,
  makeParams: () => ({
    doc: {
      description: description.value,
      subject: subject.value,
      template: props.templateId,
      ...templateFields,
      ...(isCustomerPortal.value ? { customer: activeProject.value } : {}),
      ...(isCustomerPortal.value && priority.value
        ? { priority: priority.value }
        : {}),
    },
    attachments: attachments.value,
  }),
  validate: (params) => {
    if (isCustomerPortal.value && !activeProject.value) {
      return __("Projekt auswählen");
    }
    const fields = visibleFields.value?.filter((f) => f.required) || [];
    const toVerify = [...fields, "subject", "description"];
    for (const field of toVerify) {
      if (!params.doc[field.fieldname || field]) {
        return `${field.label || field} is required`;
      }
    }
  },
  onSuccess: (data) => {
    router.push({
      name: isCustomerPortal.value ? "TicketCustomer" : "TicketAgent",
      params: {
        ticketId: data.name,
      },
    });
    if (isManager) {
      updateOnboardingStep?.("create_first_ticket", true, false, () =>
        localStorage.setItem("firstTicket", data.name)
      );
    }
  },
});

function sanitize(html: string) {
  return sanitizeHtml(html, {
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(["img"]),
  });
}

const breadcrumbs = computed(() => {
  const items = [
    {
      label: __("Tickets"),
      route: {
        name: isCustomerPortal.value ? "TicketsCustomer" : "TicketsAgent",
      },
    },
    {
      label: __("New Ticket"),
      route: {
        name: "TicketNew",
      },
    },
  ];
  return items;
});

usePageMeta(() => ({
  title: __("New Ticket"),
}));

onMounted(() => {
  capture("new_ticket_page", {
    data: {
      user: userID,
    },
  });
});
</script>
