/**
 * Ponte pequena para testar entrada em português no protótipo herdado.
 *
 * O projeto de exemplo possui glossário e regras de ASL em inglês. Esta
 * tabela não pretende ser um tradutor de Libras: ela apenas permite exercitar
 * o pipeline de timeline com frases curtas em pt-BR até que o vocabulário de
 * sinais em Libras seja conectado ao avatar.
 */
const WORDS: Record<string, string> = {
  "a": "the",
  "as": "the",
  "o": "the",
  "os": "the",
  "um": "a",
  "uma": "a",
  "eu": "I",
  "meu": "my",
  "minha": "my",
  "meus": "my",
  "minhas": "my",
  "você": "you",
  "voce": "you",
  "vocês": "you",
  "voces": "you",
  "ele": "he",
  "ela": "she",
  "nós": "we",
  "nos": "we",
  "olá": "hello",
  "ola": "hello",
  "oi": "hello",
  "tchau": "goodbye",
  "amor": "love",
  "amo": "love",
  "amar": "love",
  "ajuda": "help",
  "ajudar": "help",
  "água": "water",
  "agua": "water",
  "comida": "food",
  "comer": "eat",
  "come": "eat",
  "escola": "school",
  "casa": "home",
  "amigo": "friend",
  "amiga": "friend",
  "nome": "name",
  "linguagem": "language",
  "libras": "sign-language",
  "sinais": "sign-language",
  "sinal": "sign",
  "sim": "yes",
  "não": "not",
  "nao": "not",
  "onde": "where",
  "quem": "who",
  "oquê": "what",
  "o-que": "what",
  "que": "what",
  "quando": "when",
  "como": "how",
  "porquê": "why",
  "porque": "why",
  "ontem": "yesterday",
  "hoje": "today",
  "amanhã": "tomorrow",
  "amanha": "tomorrow",
};

function normalizeToken(token: string): string {
  return token
    .toLocaleLowerCase("pt-BR")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

/**
 * Converte apenas palavras conhecidas, preservando pontuação e desconhecidos
 * para que o protótipo possa soletrá-los. O texto resultante é deliberadamente
 * marcado como uma ponte experimental no painel da aplicação.
 */
export function normalizePtBrForPrototype(text: string): string {
  return text.replace(/[\p{L}\p{N}]+(?:-[\p{L}\p{N}]+)*/gu, (raw) => {
    const key = normalizeToken(raw);
    return WORDS[raw.toLocaleLowerCase("pt-BR")] ?? WORDS[key] ?? raw;
  });
}

