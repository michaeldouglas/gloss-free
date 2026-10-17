import { useCallback, useEffect, useState } from "react";
import { AvatarRuntime } from "../services/avatar-runtime";
import type { AvatarSource, LoadedAvatar } from "../avatar/types/avatar";

export function useAvatarRuntime() {
  const [runtime] = useState(() => new AvatarRuntime());
  const [model, setModel] = useState<LoadedAvatar | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAvatar = useCallback(
    async (source: AvatarSource) => {
      setIsLoading(true);
      setError(null);
      try {
        const loaded = await runtime.load(source);
        setModel(loaded);
      } catch (cause) {
        const message = cause instanceof Error ? cause.message : "Falha ao carregar o avatar.";
        setError(message);
        setModel(null);
      } finally {
        setIsLoading(false);
      }
    },
    [runtime],
  );

  useEffect(() => () => runtime.dispose(), [runtime]);

  return {
    controller: runtime.controller,
    model,
    isLoading,
    error,
    loadAvatar,
  };
}
