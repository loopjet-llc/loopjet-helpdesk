<template>
  <select
    v-if="members.data"
    :value="modelValue || ''"
    :aria-label="__('Customer assignee')"
    :disabled="disabled || save.loading"
    class="min-w-0 rounded-4 border border-outline-gray-2 bg-surface-base px-2 py-1 text-p-sm font-medium text-ink-gray-9 disabled:opacity-50"
    @change="onChange"
  >
    <option value="">{{ __("Unassigned") }}</option>
    <option
      v-if="modelValue && !memberIds.includes(modelValue)"
      :value="modelValue"
    >
      {{ modelValue }}
    </option>
    <option
      v-for="member in members.data"
      :key="member.user"
      :value="member.user"
    >
      {{ member.label }}
    </option>
  </select>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { createResource, toast } from "frappe-ui";
import { computed } from "vue";

const props = defineProps<{
  ticketId: string;
  modelValue?: string;
  disabled?: boolean;
}>();
const emit = defineEmits<{ updated: [] }>();

const members = createResource({
  url: "helpdesk.api.customer_team.get_members",
  params: { ticket: props.ticketId },
  cache: ["Customer Team", props.ticketId],
  auto: true,
});
const memberIds = computed(() =>
  (members.data || []).map((member) => member.user)
);

const save = createResource({
  url: "helpdesk.api.customer_team.assign",
  makeParams: (assignee: string) => ({ ticket: props.ticketId, assignee }),
  onSuccess: () => {
    emit("updated");
    toast.success(__("Customer assignee updated."));
  },
  onError: () => toast.error(__("Customer assignee could not be updated.")),
});

function onChange(event: Event) {
  const select = event.target as HTMLSelectElement;
  const assignee = select.value;
  if (assignee === (props.modelValue || "")) return;
  save.submit(assignee, {
    onError: () => {
      select.value = props.modelValue || "";
    },
  });
}
</script>
