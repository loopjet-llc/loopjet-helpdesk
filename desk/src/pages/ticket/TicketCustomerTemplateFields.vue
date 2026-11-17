<template>
  <div class="space-y-2 px-6 py-3.5 border-b">
    <div class="flex items-center gap-4">
      <span class="w-[150px] shrink-0 text-p-sm text-ink-gray-5">Status</span>
      <span
        class="flex-1 truncate rounded-4 border border-outline-gray-2 bg-surface-base px-2 py-1 text-p-sm text-ink-gray-9"
      >
        {{ ticket.data.status }}
      </span>
    </div>

    <div class="flex items-center gap-4">
      <span class="w-[150px] shrink-0 text-p-sm text-ink-gray-5">{{
        __("Priority")
      }}</span>
      <TicketPrioritySelect
        :ticket-id="ticket.data.name"
        :model-value="ticket.data.priority"
        :disabled="
          !(auth.isAdmin || auth.isManager) &&
          (ticket.data.status === 'Closed' || !!ticket.data.feedback_rating)
        "
        class="min-w-0 flex-1"
        @updated="ticket.reload()"
      />
    </div>

    <div v-if="ticket.data.customer" class="flex items-center gap-4">
      <span class="w-[150px] shrink-0 text-p-sm text-ink-gray-5">{{
        __("Customer assignee")
      }}</span>
      <TicketCustomerAssigneeSelect
        :ticket-id="ticket.data.name"
        :model-value="ticket.data.customer_assignee"
        :disabled="
          !(auth.isAdmin || auth.isManager) &&
          (ticket.data.status === 'Closed' || !!ticket.data.feedback_rating)
        "
        class="min-w-0 flex-1"
        @updated="ticket.reload()"
      />
    </div>

    <div v-if="auth.isAdmin || auth.isManager" class="flex items-center gap-4">
      <span class="w-[150px] shrink-0 text-p-sm text-ink-gray-5">{{
        __("Bearbeiter")
      }}</span>
      <AssignTo class="min-w-0 flex-1" hide-label />
    </div>

    <div
      v-for="field in customFields"
      :key="field.fieldname"
      class="flex items-center gap-4"
    >
      <span class="w-[150px] shrink-0 text-p-sm text-ink-gray-5">{{
        __(field.label)
      }}</span>
      <span
        class="flex-1 truncate rounded-4 border border-outline-gray-2 bg-surface-base px-2 py-1 text-p-sm text-ink-gray-9"
      >
        {{ ticket.data[field.fieldname] }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import TicketPrioritySelect from "@/components/ticket/TicketPrioritySelect.vue";
import TicketCustomerAssigneeSelect from "@/components/ticket/TicketCustomerAssigneeSelect.vue";
import AssignTo from "@/components/ticket-agent/AssignTo.vue";
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import { Field } from "@/types";
import { computed, inject } from "vue";
import { ITicket } from "./symbols";

const ticket = inject(ITicket);
const auth = useAuthStore();

const customFields = computed(() =>
  ticket.data.template.fields.filter(
    (f: Field) =>
      f.fieldname !== "priority" &&
      ticket.data[f.fieldname] != null &&
      ticket.data[f.fieldname] !== ""
  )
);
</script>
