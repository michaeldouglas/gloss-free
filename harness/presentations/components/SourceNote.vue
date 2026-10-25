<script setup lang="ts">
defineProps<{ source: string; detail?: string }>();
</script>

<template>
  <aside class="source-note" aria-label="Fonte e escopo da evidência">
    <strong>Fonte:</strong> {{ source }}<span v-if="detail"> · {{ detail }}</span>
  </aside>
</template>
