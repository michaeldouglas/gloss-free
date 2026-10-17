export {};

declare global {
  interface Window {
    desktop?: {
      isDesktop: boolean;
      platform: string;
    };
  }
}
