/// <reference types="vite/client" />

import type { LiviJavaScriptApi } from "./avatar/avatar-api";

declare global {
  interface Window {
    livi?: LiviJavaScriptApi;
    /** Compatibility alias retained for integrations built against the first prototype. */
    avatar?: LiviJavaScriptApi;
    desktop?: { isDesktop: boolean };
  }
}

export {};
