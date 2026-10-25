<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  detail?: string;
  accent?: "blue" | "teal" | "purple";
}>();
</script>

<template>
  <article class="metric-card" :class="accent || 'teal'" role="group" :aria-label="`${label}: ${value}`">
    <p class="metric-label">{{ label }}</p>
    <p class="metric-value">{{ value }}</p>
    <p v-if="detail" class="metric-detail">{{ detail }}</p>
  </article>
</template>

<style scoped>
.metric-card { min-height: 9rem; padding: 1.1rem 1.2rem; border: 1px solid var(--research-line); border-top: 4px solid var(--research-turquoise); border-radius: .8rem; background: var(--research-white); }
.metric-card.blue { border-top-color: var(--research-blue); }
.metric-card.purple { border-top-color: var(--research-purple); }
.metric-label { margin: 0; color: var(--research-muted); font-size: .88rem; font-weight: 700; }
.metric-value { margin: .25rem 0; color: var(--research-navy); font-family: "Crimson Pro", Georgia, serif; font-size: 2.6rem; font-weight: 600; line-height: 1; }
.metric-detail { margin: .5rem 0 0; color: var(--research-muted); font-size: .84rem; line-height: 1.3; }
</style>
