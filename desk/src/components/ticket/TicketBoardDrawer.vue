<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-40 bg-black/15" @click="emit('close')" />
    <aside
      class="fixed inset-y-0 right-0 z-50 flex w-full flex-col border-l border-outline-gray-2 bg-surface-white shadow-2xl sm:w-[34rem]"
      role="dialog"
      aria-modal="true"
      :aria-label="__('Ticketdetails')"
    >
      <div class="flex items-start justify-between gap-4 border-b px-5 py-4">
        <div class="min-w-0">
          <p class="text-p-xs font-medium text-ink-gray-5">
            #{{ ticketId }}
            <span v-if="displayTicket?.customer">
              · {{ displayTicket.customer }}</span
            >
          </p>
          <h2 class="mt-1 truncate text-lg font-semibold text-ink-gray-9">
            {{ displayTicket?.subject || __("Ticket wird geladen …") }}
          </h2>
        </div>
        <Button icon="x" variant="ghost" @click="emit('close')" />
      </div>

      <div
        v-if="displayTicket"
        class="grid grid-cols-3 divide-x border-b bg-surface-gray-1"
      >
        <div class="min-w-0 px-4 py-3">
          <span class="text-p-xs text-ink-gray-5">{{ __("Status") }}</span>
          <select
            v-if="!isCustomerPortal"
            :value="displayTicket.status"
            class="mt-1 block w-full truncate border-0 bg-transparent p-0 text-sm font-medium text-ink-gray-8 focus:ring-0"
            @change="
              updateAgentField(
                'status',
                ($event.target as HTMLSelectElement).value
              )
            "
          >
            <option
              v-for="status in enabledStatuses"
              :key="status.label_agent"
              :value="status.label_agent"
            >
              {{ status.label_agent }}
            </option>
          </select>
          <p v-else class="mt-1 truncate text-sm font-medium text-ink-gray-8">
            {{ customerStatusLabel(displayTicket.status) }}
          </p>
        </div>
        <div class="min-w-0 px-4 py-3">
          <span class="text-p-xs text-ink-gray-5">{{ __("Priorität") }}</span>
          <p class="mt-1 truncate text-sm font-medium text-ink-gray-8">
            {{ displayTicket.priority || "–" }}
          </p>
        </div>
        <div class="min-w-0 px-4 py-3">
          <span class="text-p-xs text-ink-gray-5">{{ __("Zugewiesen") }}</span>
          <p class="mt-1 truncate text-sm font-medium text-ink-gray-8">
            {{ assigneeLabel(displayTicket._assign) }}
          </p>
        </div>
      </div>

      <div v-if="!displayTicket" class="grid flex-1 place-items-center">
        <LoadingIndicator class="size-6 text-ink-gray-4" />
      </div>

      <div
        v-else-if="!isCustomerPortal"
        class="flex min-h-0 flex-1 flex-col overflow-hidden"
      >
        <TicketActivityPanel />
      </div>

      <template v-else>
        <TicketConversation class="min-h-0 flex-1" :show-header="false" />
        <div
          v-if="displayTicket.status !== 'Closed'"
          class="border-t p-4"
          @keydown.ctrl.enter.capture.stop="sendCustomerComment"
          @keydown.meta.enter.capture.stop="sendCustomerComment"
        >
          <TicketTextEditor
            ref="customerEditor"
            v-model:attachments="customerAttachments"
            v-model:content="customerContent"
            v-model:expand="customerEditorExpanded"
            :placeholder="__('Kommentar schreiben …')"
            :upload-function="
              (file) => uploadFunction(file, 'HD Ticket', ticketId)
            "
          >
            <template #bottom-right>
              <Button
                :label="__('Kommentar senden')"
                variant="solid"
                :disabled="
                  isContentEmpty(customerContent) || customerSend.loading
                "
                :loading="customerSend.loading"
                @click="sendCustomerComment"
              />
            </template>
          </TicketTextEditor>
        </div>
      </template>
    </aside>
  </Teleport>
</template>

<script setup lang="ts">
import TicketActivityPanel from "@/components/ticket-agent/TicketActivityPanel.vue";
import { useTicket } from "@/composables/useTicket";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { __ } from "@/translation";
import { ActivitiesSymbol, TicketSymbol } from "@/types";
import { isContentEmpty, uploadFunction } from "@/utils";
import { Button, createResource, LoadingIndicator, toast } from "frappe-ui";
import { computed, onMounted, onUnmounted, provide, ref } from "vue";
import TicketConversation from "@/pages/ticket/TicketConversation.vue";
import TicketTextEditor from "@/pages/ticket/TicketTextEditor.vue";
import { ITicket } from "@/pages/ticket/symbols";

interface Props {
  ticketId: string;
  isCustomerPortal?: boolean;
}

const props = withDefaults(defineProps<Props>(), { isCustomerPortal: false });
const emit = defineEmits<{ close: []; updated: [] }>();
const { statuses, getStatus } = useTicketStatusStore();
const enabledStatuses = computed(() =>
  (statuses.data || []).filter((status) => status.enabled)
);

const agentTicketComposable = props.isCustomerPortal
  ? null
  : useTicket(props.ticketId);
const agentTicket = computed(() => agentTicketComposable?.ticket);
const agentActivities = computed(() => agentTicketComposable?.activities);
provide(TicketSymbol, agentTicket as any);
provide(ActivitiesSymbol, agentActivities as any);

const customerTicket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_one",
  params: { name: props.ticketId, is_customer_portal: true },
  auto: props.isCustomerPortal,
  onError: () => toast.error(__("Ticket konnte nicht geladen werden.")),
});
provide(ITicket, customerTicket as any);

const displayTicket = computed(() =>
  props.isCustomerPortal ? customerTicket.data : agentTicket.value?.doc
);

function customerStatusLabel(status: string) {
  const record = getStatus(status);
  return record?.label_customer || record?.label_agent || status;
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
  return names
    .map((name) => name.split("@")[0].replace(/[._-]/g, " "))
    .join(", ");
}

function updateAgentField(field: string, value: string) {
  if (!agentTicket.value || displayTicket.value?.[field] === value) return;
  agentTicket.value.setValue.submit(
    { [field]: value },
    {
      onSuccess: () => {
        agentActivities.value?.reload();
        emit("updated");
      },
    }
  );
}

const customerEditor = ref(null);
const customerContent = ref("");
const customerAttachments = ref([]);
const customerEditorExpanded = ref(true);
const customerSend = createResource({
  url: "run_doc_method",
  debounce: 300,
  makeParams: () => ({
    dt: "HD Ticket",
    dn: props.ticketId,
    method: "create_communication_via_contact",
    args: {
      message: customerContent.value,
      attachments: customerAttachments.value,
    },
  }),
  onSuccess: () => {
    customerEditor.value?.editor?.commands?.clearContent(true);
    customerContent.value = "";
    customerAttachments.value = [];
    customerTicket.reload();
    emit("updated");
  },
});

function sendCustomerComment() {
  if (isContentEmpty(customerContent.value) || customerSend.loading) return;
  customerSend.submit();
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") emit("close");
}

onMounted(() => window.addEventListener("keydown", handleKeydown));
onUnmounted(() => window.removeEventListener("keydown", handleKeydown));
</script>
