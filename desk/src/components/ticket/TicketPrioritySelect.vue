<template>
  <select
    :value="modelValue || ''"
    :aria-label="__('Priority')"
    :disabled="priorities.loading || save.loading"
    class="min-w-0 rounded-4 border border-outline-gray-2 bg-surface-base px-2 py-1 text-p-sm font-medium text-ink-gray-9 disabled:opacity-50"
    @change="onChange"
  >
    <option v-if="!ticketId" value="">
      {{ __("Automatically assigned") }}
    </option>
    <option
      v-if="modelValue && !priorityOptions.includes(modelValue)"
      :value="modelValue"
    >
      {{ __(modelValue) }}
    </option>
    <option
      v-for="priority in priorityOptions"
      :key="priority"
      :value="priority"
    >
      {{ __(priority) }}
    </option>
  </select>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { PRIORITY_DISPLAY_ORDER } from "@/stores/ticketPriority";
import { createResource, toast } from "frappe-ui";
import { computed } from "vue";

const props = defineProps<{
  modelValue?: string;
  ticketId?: string;
}>();
const emit = defineEmits<{
  "update:modelValue": [value: string];
  updated: [];
}>();

const priorities = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket_priority.api.get_active",
  auto: true,
  cache: ["HD Ticket Priority", "customer-select"],
  onError: () => toast.error(__("Priorities could not be loaded.")),
});
const priorityOptions = computed<string[]>(() =>
  [...(priorities.data || [])]
    .sort(
      (a, b) =>
        (PRIORITY_DISPLAY_ORDER[b.level] ?? -1) -
        (PRIORITY_DISPLAY_ORDER[a.level] ?? -1)
    )
    .map((priority) => priority.name)
);

const save = createResource({
  url: "frappe.client.set_value",
  makeParams: (priority: string) => ({
    doctype: "HD Ticket",
    name: props.ticketId,
    fieldname: "priority",
    value: priority,
  }),
  onSuccess: () => {
    emit("updated");
    toast.success(__("Priority updated."));
  },
  onError: () => {
    toast.error(__("Priority could not be updated."));
  },
});

function onChange(event: Event) {
  const select = event.target as HTMLSelectElement;
  const priority = select.value;
  if (!props.ticketId) {
    emit("update:modelValue", priority);
    return;
  }
  if (priority === props.modelValue) return;
  save.submit(priority, {
    onError: () => {
      select.value = props.modelValue || "";
    },
  });
}
</script>
