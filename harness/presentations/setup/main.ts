import { defineAppSetup } from "@slidev/types";
import evidence from "../evidence.generated.json";

const formatNumber = (value: number | null | undefined): string => new Intl.NumberFormat("pt-BR").format(value ?? 0);
const formatDate = (value: string | null | undefined): string => value
  ? new Intl.DateTimeFormat("pt-BR", { dateStyle: "long", timeZone: "UTC" }).format(new Date(value))
  : "data não registrada";

export default defineAppSetup(({ app }) => {
  const mind = evidence.datasets.find((item) => item.dataset === "minds-libras-raw");
  const vlibrasil = evidence.datasets.find((item) => item.dataset === "v-librasil-raw");
  const globals = app.config.globalProperties as Record<string, unknown>;
  Object.assign(globals, {
    $release: evidence,
    $mind: mind,
    $vlibrasil: vlibrasil,
    $latest: evidence.latest_execution,
    $progress: evidence.feature_progress,
    $fmt: formatNumber,
    $date: formatDate,
    $evidenceDateMind: formatDate(mind?.generated_at_utc),
    $evidenceDateVlibrasil: formatDate(vlibrasil?.generated_at_utc),
  });
});
