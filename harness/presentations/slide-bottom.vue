<script setup lang="ts">
import { computed } from "vue";
import { useNav, useSlideContext } from "@slidev/client";

const { total, hasPrev, hasNext, prev, next, isPrintMode } = useNav();
const { $page, $renderContext } = useSlideContext();
const progress = computed(() => total.value === 0 ? 0 : Math.round(($page.value / total.value) * 100));
const pageLabel = computed(() => `Slide ${$page.value} de ${total.value}`);
</script>

<template>
  <nav
    v-if="$renderContext === 'slide'"
    class="slide-navigation"
    :class="{ 'slide-navigation--cover': $page === 1 }"
    aria-label="Navegação da apresentação"
  >
    <div
      class="slide-navigation__progress"
      role="progressbar"
      :aria-label="pageLabel"
      aria-valuemin="1"
      :aria-valuemax="total"
      :aria-valuenow="$page"
      :aria-valuetext="pageLabel"
    >
      <span class="slide-navigation__progress-value" :style="{ width: `${progress}%` }" />
    </div>

    <div class="slide-navigation__controls">
      <button
        v-if="!isPrintMode"
        class="slide-navigation__button"
        type="button"
        aria-label="Slide anterior"
        title="Slide anterior"
        :disabled="!hasPrev"
        @click="prev"
      >
        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m15 18-6-6 6-6" />
        </svg>
      </button>

      <p class="slide-navigation__count" role="status" aria-live="polite" aria-atomic="true" :aria-label="pageLabel">
        <span class="slide-navigation__sr-only">Slide </span>
        <strong>{{ String($page).padStart(2, "0") }}</strong>
        <span aria-hidden="true">/</span>
        {{ String(total).padStart(2, "0") }}
        <span class="slide-navigation__sr-only"> de {{ total }} slides</span>
      </p>

      <button
        v-if="!isPrintMode"
        class="slide-navigation__button"
        type="button"
        aria-label="Próximo slide"
        title="Próximo slide"
        :disabled="!hasNext"
        @click="next"
      >
        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m9 18 6-6-6-6" />
        </svg>
      </button>
    </div>
  </nav>
</template>
