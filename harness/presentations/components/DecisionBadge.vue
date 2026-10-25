<script setup lang="ts">
defineProps<{ decision: string }>();
</script>

<template>
  <span class="decision-badge" :class="decision.toLowerCase().replaceAll('-', '')">
    <span class="decision-symbol" aria-hidden="true">{{ decision === "GO" ? "✓" : "!" }}</span>
    <span>Decisão de integridade: <strong>{{ decision }}</strong></span>
  </span>
</template>

<style scoped>
.decision-badge { display: inline-flex; align-items: center; gap: .6rem; padding: .55rem .8rem; border: 1px solid var(--research-line); border-radius: 999px; background: white; color: var(--research-ink); font-size: .9rem; }
.decision-symbol { display: grid; width: 1.6rem; height: 1.6rem; place-items: center; border-radius: 50%; background: var(--research-soft-teal); color: #075d5c; font-weight: 800; }
.nogo .decision-symbol { background: #fff0ec; color: #8c3425; }
.decision-badge strong { color: var(--research-navy); }
</style>
