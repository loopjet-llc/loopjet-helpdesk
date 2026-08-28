<template>
  <div class="comm-area">
    <div
      class="flex justify-between gap-3 border-t px-6 md:px-5 py-4 md:py-2.5"
    >
      <div class="flex gap-1.5 items-center">
        <Button
          ref="sendEmailRef"
          variant="ghost"
          :label="__('Kommentar')"
          :class="[
            showEmailBox ? '!bg-surface-gray-4 hover:!bg-surface-gray-3' : '',
          ]"
          @click="toggleEmailBox()"
        >
          <template #prefix>
            <CommentIcon class="h-4" />
          </template>
        </Button>
        <Button
          variant="ghost"
          :label="__('Interner Kommentar')"
          :class="[
            showCommentBox ? '!bg-surface-gray-4 hover:!bg-surface-gray-3' : '',
          ]"
          @click="toggleCommentBox()"
        >
          <template #prefix>
            <LucideLockKeyhole class="h-4" />
          </template>
        </Button>
        <TypingIndicator :ticketId="ticketId" />
      </div>
    </div>
    <Transition name="slide">
      <div
        v-show="showEmailBox"
        ref="emailBoxRef"
        @keydown.ctrl.enter.capture.stop="submitEmail"
        @keydown.meta.enter.capture.stop="submitEmail"
        @keydown.esc.capture.stop="showEmailBox = false"
      >
        <div class="overflow-hidden">
          <EmailEditor
            ref="emailEditorRef"
            public-comment
            :label="
              isMobileView
                ? __('Kommentar senden')
                : isMac
                ? __('Kommentar senden (⌘ + ⏎)')
                : __('Kommentar senden (Ctrl + ⏎)')
            "
            :placeholder="__('Kommentar für den Kunden schreiben …')"
            :ticketId="ticketId"
            :to-emails="toEmails"
            :cc-emails="ccEmails"
            :bcc-emails="bccEmails"
            @submit="
              () => {
                showEmailBox = false;
                emit('update');
              }
            "
            @discard="
              () => {
                showEmailBox = false;
              }
            "
          />
        </div>
      </div>
    </Transition>
    <Transition name="slide">
      <div
        v-show="showCommentBox"
        ref="commentBoxRef"
        @keydown.ctrl.enter.capture.stop="submitComment"
        @keydown.meta.enter.capture.stop="submitComment"
        @keydown.esc.capture.stop="showCommentBox = false"
      >
        <div class="overflow-hidden">
          <div
            class="mx-5 mt-3 flex items-center gap-2 rounded-lg bg-surface-amber-2 px-3 py-2 text-p-xs text-ink-amber-3"
          >
            <LucideLockKeyhole class="size-4 shrink-0" />
            {{
              __("Nur für Loopjet – wird nicht per E-Mail an Kunden gesendet.")
            }}
          </div>
          <CommentTextEditor
            ref="commentTextEditorRef"
            :label="
              isMobileView
                ? __('Intern speichern')
                : isMac
                ? __('Intern speichern (⌘ + ⏎)')
                : __('Intern speichern (Ctrl + ⏎)')
            "
            :ticketId="ticketId"
            :editable="showCommentBox"
            :doctype="doctype"
            :placeholder="__('Interne Notiz für das Loopjet-Team …')"
            @submit="
              () => {
                showCommentBox = false;
                emit('update');
              }
            "
            @discard="
              () => {
                showCommentBox = false;
              }
            "
          />
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { CommentTextEditor, EmailEditor, TypingIndicator } from "@/components";
import { CommentIcon } from "@/components/icons/";
import { useDevice } from "@/composables";
import { useScreenSize } from "@/composables/screen";
import { useShortcut } from "@/composables/shortcuts";
import { showCommentBox, showEmailBox } from "@/pages/ticket/modalStates";
import { onClickOutside } from "@vueuse/core";
import { ref, watch } from "vue";
import { __ } from "@/translation";

const emit = defineEmits(["update"]);
const content = defineModel("content");
const { isMac } = useDevice();
const { isMobileView } = useScreenSize();
let doc = defineModel();
// let doc = inject(TicketSymbol)?.value.doc
const emailEditorRef = ref(null);
const commentTextEditorRef = ref(null);
const emailBoxRef = ref(null);
const commentBoxRef = ref(null);

function toggleEmailBox() {
  if (showCommentBox.value) {
    showCommentBox.value = false;
  }
  showEmailBox.value = !showEmailBox.value;
}

function toggleCommentBox() {
  if (showEmailBox.value) {
    showEmailBox.value = false;
  }
  showCommentBox.value = !showCommentBox.value;
}

function submitEmail() {
  if (emailEditorRef.value.submitMail()) {
    emit("update");
  }
}

function submitComment() {
  if (commentTextEditorRef.value.submitComment()) {
    emit("update");
  }
}

function splitIfString(str: string | string[]) {
  if (typeof str === "string") {
    return str.split(",");
  }
  return str;
}

function replyToEmail(data: object) {
  showEmailBox.value = true;

  emailEditorRef.value.addToReply(
    data.content,
    splitIfString(data.to),
    splitIfString(data.cc),
    splitIfString(data.bcc)
  );
}

const props = defineProps({
  doctype: {
    type: String,
    default: "HD Ticket",
  },
  ticketId: {
    type: String,
    default: null,
  },
  toEmails: {
    type: Array,
    default: () => [],
  },
  ccEmails: {
    type: Array,
    default: () => [],
  },
  bccEmails: {
    type: Array,
    default: () => [],
  },
});

watch(
  () => showEmailBox.value,
  (value) => {
    if (value) {
      emailEditorRef.value?.editor?.commands?.focus("start");
    }
  }
);

watch(
  () => showCommentBox.value,
  (value) => {
    if (value) {
      commentTextEditorRef.value?.editor?.commands?.focus();
    }
  }
);

useShortcut("r", () => {
  toggleEmailBox();
});
useShortcut("c", () => {
  toggleCommentBox();
});

defineExpose({
  replyToEmail,
  toggleEmailBox,
  toggleCommentBox,
  editor: emailEditorRef,
});

onClickOutside(
  emailBoxRef,
  () => {
    if (showEmailBox.value) {
      showEmailBox.value = false;
    }
  },
  {
    ignore: [
      ".tippy-box",
      ".tippy-content",
      ".PopoverContent",
      '[role="dialog"]',
      ".dialog-overlay",
    ],
  }
);

onClickOutside(
  commentBoxRef,
  () => {
    if (showCommentBox.value) {
      showCommentBox.value = false;
    }
  },
  {
    ignore: [
      ".tippy-box",
      ".tippy-content",
      ".PopoverContent",
      '[role="dialog"]',
      ".dialog-overlay",
    ],
  }
);
</script>

<style>
@media screen and (max-width: 640px) {
  .comm-area {
    width: 100vw;
  }
}

.slide-enter-active,
.slide-leave-active {
  display: grid;
  transition: grid-template-rows 0.25s ease;
}
.slide-enter-from,
.slide-leave-to {
  grid-template-rows: 0fr;
}
.slide-enter-to,
.slide-leave-from {
  grid-template-rows: 1fr;
}
</style>
