<script setup lang="ts">
type ComparisonItem = { label: string; value: number; display: string; accent?: "blue" | "teal" | "purple" };

const props = defineProps<{
  title: string;
  caption: string;
  items: ComparisonItem[];
  max?: number;
}>();

const scale = () => props.max ?? Math.max(1, ...props.items.map((item) => item.value));
const width = (value: number) => `${Math.max(0, Math.min(100, (value / scale()) * 100))}%`;
</script>

<template>
  <figure class="data-comparison">
    <figcaption class="comparison-title">{{ title }}</figcaption>
    <table>
      <tbody>
        <tr v-for="item in items" :key="item.label">
          <th scope="row">{{ item.label }}</th>
          <td class="bar-cell" aria-hidden="true">
            <span class="bar-track"><span class="bar-fill" :class="item.accent || 'teal'" :style="{ width: width(item.value) }" /></span>
          </td>
          <td class="comparison-value">{{ item.display }}</td>
        </tr>
      </tbody>
    </table>
    <p class="comparison-caption">{{ caption }}</p>
  </figure>
</template>

<style scoped>
.data-comparison { margin: 0; padding: 1.1rem 1.25rem; border: 1px solid var(--research-line); border-radius: .8rem; background: white; }
.comparison-title { margin-bottom: .8rem; color: var(--research-navy); font-family: "Crimson Pro", Georgia, serif; font-size: 1.35rem; font-weight: 600; }
table { width: 100%; border-collapse: separate; border-spacing: 0 .55rem; font-size: .9rem; }
th { width: 10rem; padding-right: .8rem; color: var(--research-ink); text-align: left; font-weight: 700; }
.bar-cell { width: 100%; }
.bar-track { display: block; height: .85rem; overflow: hidden; border-radius: 99px; background: #e8edf3; }
.bar-fill { display: block; height: 100%; border-radius: inherit; background: var(--research-turquoise); }
.bar-fill.blue { background: var(--research-blue); }
.bar-fill.purple { background: var(--research-purple); }
.comparison-value { width: 7.2rem; padding-left: .8rem; color: var(--research-navy); text-align: right; font-variant-numeric: tabular-nums; font-weight: 700; white-space: nowrap; }
.comparison-caption { margin: .8rem 0 0; color: var(--research-muted); font-size: .8rem; line-height: 1.35; }
</style>
