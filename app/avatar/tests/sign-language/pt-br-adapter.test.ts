import { describe, expect, it } from "vitest";
import { normalizePtBrForPrototype } from "../../src/sign-language/pt-br-adapter";

describe("ponte pt-BR do protótipo de sinais", () => {
  it("normaliza frases curtas conhecidas para o glossário herdado", () => {
    expect(normalizePtBrForPrototype("Olá, eu amo Libras")).toBe("hello, I love sign-language");
  });

  it("preserva palavras desconhecidas para soletração", () => {
    expect(normalizePtBrForPrototype("Rain caminha")).toBe("Rain caminha");
  });
});

