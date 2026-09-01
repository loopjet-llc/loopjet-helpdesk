<template>
  <div
    class="flex min-h-0 flex-1 overflow-x-auto overflow-y-hidden bg-surface-gray-1 px-4 pb-5 pt-2 sm:px-5"
  >
    <div class="flex h-full min-h-0 min-w-max gap-4">
      <section
        v-for="column in columns"
        :key="column.name"
        class="flex h-full min-h-0 w-[19rem] flex-col"
      >
        <header class="mb-2 flex h-9 items-center justify-between px-1">
          <div class="flex min-w-0 items-center gap-2">
            <span
              class="size-2 shrink-0 rounded-full"
              :class="statusDot(column.status)"
            />
            <span class="truncate text-sm font-semibold text-ink-gray-8">
              {{ statusLabel(column.status) }}
            </span>
            <span class="text-p-xs text-ink-gray-5">{{
              column.tickets.length
            }}</span>
          </div>
        </header>

        <draggable
          :list="column.tickets"
          item-key="name"
          :group="isCustomerPortal ? undefined : 'helpdesk-tickets'"
          :sort="!isCustomerPortal"
          :disabled="isCustomerPortal"
          ghost-class="opacity-40"
          drag-class="shadow-lg"
          class="min-h-0 flex-1 space-y-2.5 overflow-x-hidden overflow-y-auto overscroll-contain rounded-xl bg-surface-gray-2 p-2"
          @change="(event) => handleMove(column.name, event)"
        >
          <template #item="{ element: ticket }">
            <button
              type="button"
              class="group block w-full rounded-xl border border-outline-gray-1 bg-surface-white p-3.5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-outline-gray-3 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-outline-gray-3"
              @click="emit('open', ticket.name)"
            >
              <div class="mb-2 flex items-center justify-between gap-2">
                <span class="text-p-xs font-medium text-ink-gray-5"
                  >#{{ ticket.name }}</span
                >
                <span
                  v-if="ticket.priority"
                  class="rounded-md px-2 py-1 text-p-xs font-medium"
                  :class="priorityClass(ticket.priority)"
                >
                  {{ __(ticket.priority) }}
                </span>
              </div>
              <h3
                class="line-clamp-2 text-base font-semibold leading-5 text-ink-gray-9"
              >
                {{ ticket.subject }}
              </h3>
              <p class="mt-1 truncate text-p-xs text-ink-gray-5">
                {{ ticket.customer || ticket.contact || __("Kein Kunde") }}
              </p>

              <div
                v-if="ticket.resolution_by || ticket.agreement_status"
                class="mt-3 flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-p-xs"
                :class="slaClass(ticket.agreement_status)"
              >
                <LucideClock3 class="size-3.5 shrink-0" />
                <span class="truncate">{{ slaLabel(ticket) }}</span>
              </div>

              <div class="mt-3 flex items-center justify-between border-t pt-3">
                <div class="flex min-w-0 items-center gap-2">
                  <span
                    class="grid size-6 shrink-0 place-items-center rounded-full bg-surface-blue-2 text-[10px] font-semibold text-ink-blue-3"
                  >
                    {{ assigneeInitials(ticket._assign) }}
                  </span>
                  <span class="truncate text-p-xs text-ink-gray-5">
                    {{ assigneeLabel(ticket._assign) }}
                  </span>
                </div>
                <span
                  v-if="!isSeen(ticket)"
                  class="size-2 shrink-0 rounded-full bg-surface-blue-5"
                  :title="__('Ungelesen')"
                />
              </div>
            </button>
          </template>
        </draggable>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { __ } from "@/translation";
import { shortDuration } from "@/utils";
import { call, toast } from "frappe-ui";
import { computed, ref, watch } from "vue";
import draggable from "vuedraggable";

interface Props {
  rows: Record<string, any>[];
  isCustomerPortal?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  rows: () => [],
  isCustomerPortal: false,
});
const emit = defineEmits<{
  open: [ticket: string];
  updated: [];
}>();

const { statuses } = useTicketStatusStore();
const { userId } = useAuthStore();
const boardColumns = ref<Record<string, Record<string, any>[]>>({});

const enabledStatuses = computed(() => {
  const configured = (statuses.data || []).filter((status) => status.enabled);
  const known = new Set(configured.map((status) => status.label_agent));
  const missing = Array.from(
    new Set(
      props.rows.map((row) => row.status).filter((name) => !known.has(name))
    )
  ).map((name) => ({
    label_agent: name,
    label_customer: name,
    name,
    parsed_color: "!text-gray-500",
  }));
  return [...configured, ...missing];
});

const columns = computed(() =>
  enabledStatuses.value.map((status) => ({
    name: status.label_agent,
    status,
    tickets: boardColumns.value[status.label_agent] || [],
  }))
);

function rebuildColumns() {
  const next: Record<string, Record<string, any>[]> = {};
  for (const status of enabledStatuses.value) {
    next[status.label_agent] = [];
  }
  for (const row of props.rows) {
    if (!next[row.status]) next[row.status] = [];
    next[row.status].push({ ...row });
  }
  boardColumns.value = next;
}

watch([() => props.rows, enabledStatuses], rebuildColumns, {
  immediate: true,
  deep: true,
});

function statusLabel(status) {
  return props.isCustomerPortal
    ? status.label_customer || status.label_agent
    : status.label_agent;
}

function statusDot(status) {
  return status.parsed_color?.replace("text-", "bg-") || "bg-surface-gray-5";
}

function priorityClass(priority: string) {
  const normalized = priority.toLowerCase();
  if (["urgent", "dringend"].includes(normalized)) {
    return "bg-surface-red-1 text-ink-red-3";
  }
  if (["high", "hoch"].includes(normalized)) {
    return "bg-surface-orange-1 text-orange-700";
  }
  return "bg-surface-gray-2 text-ink-gray-6";
}

function slaClass(status: string) {
  if (status === "Failed") return "bg-surface-red-1 text-ink-red-3";
  if (status === "Paused") return "bg-surface-amber-2 text-ink-amber-3";
  return "bg-surface-gray-2 text-ink-gray-6";
}

function slaLabel(ticket) {
  if (ticket.agreement_status === "Failed") return __("SLA überschritten");
  if (ticket.agreement_status === "Paused") return __("SLA pausiert");
  if (!ticket.resolution_by) return __(ticket.agreement_status || "Aktiv");
  return __("Lösung {0}", [shortDuration(ticket.resolution_by)]);
}

function assignees(value: string | string[] | undefined): string[] {
  if (Array.isArray(value)) return value;
  if (!value) return [];
  try {
    return JSON.parse(value);
  } catch {
    return [];
  }
}

function assigneeLabel(value) {
  const names = assignees(value);
  if (!names.length) return __("Nicht zugewiesen");
  const first = names[0].split("@")[0].replace(/[._-]/g, " ");
  return names.length > 1 ? `${first} +${names.length - 1}` : first;
}

function assigneeInitials(value) {
  const label = assigneeLabel(value);
  if (label === __("Nicht zugewiesen")) return "?";
  return label
    .split(" ")
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

function isSeen(ticket) {
  if (!ticket._seen) return false;
  try {
    return JSON.parse(ticket._seen).includes(userId || "");
  } catch {
    return false;
  }
}

async function handleMove(status: string, event) {
  if (props.isCustomerPortal || !event.added) return;
  const ticket = event.added.element;
  const oldStatus = ticket.status;
  if (oldStatus === status) return;
  ticket.status = status;
  try {
    await call("frappe.client.set_value", {
      doctype: "HD Ticket",
      name: ticket.name,
      fieldname: "status",
      value: status,
    });
    const targetStatus = enabledStatuses.value.find(
      (item) => item.label_agent === status
    );
    toast.success(
      __("Ticket in {0} verschoben", [
        targetStatus ? statusLabel(targetStatus) : status,
      ])
    );
    emit("updated");
  } catch (error) {
    rebuildColumns();
    toast.error(__("Status konnte nicht geändert werden."));
  }
}
</script>
