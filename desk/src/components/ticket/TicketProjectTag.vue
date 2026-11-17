<template>
  <span
    class="inline-flex max-w-full shrink-0 items-center truncate rounded-4 border border-outline-gray-2 bg-surface-gray-1 px-2 py-0.5 text-p-xs font-medium text-ink-gray-7"
    :title="label"
  >
    {{ label }}
  </span>
</template>

<script setup lang="ts">
defineProps<{ label: string }>();
</script>
