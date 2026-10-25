import type { App } from "vue";

// Slidev 53 installs this VitePress-only plugin in every deck. Its optional
// FloatingVue patch assumes VMenu.components.Popper exists, which is not true
// in the resolved FloatingVue 5.4.0. These decks do not use Twoslash tooltips.
export default {
  install(_app: App): void {},
};
