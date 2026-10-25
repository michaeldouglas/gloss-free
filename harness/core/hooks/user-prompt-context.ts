import { emitContext, eventString, readHookEvent } from "../lib/hook-protocol.ts";

const event = await readHookEvent();
if (!event) process.exit(0);
const prompt = eventString(event, "prompt");
const codebaseQuestion = /(c[oó]digo|arquivo|arquitetura|estrutura|projeto|repo|reposit[oó]rio|fun[cç][aã]o|m[oó]dulo|onde fica|como funciona|quem chama|grafo|graphify|speckit|spec kit)/i.test(prompt);
if (prompt && codebaseQuestion) emitContext("UserPromptSubmit", "This prompt appears to concern the repository. Follow AGENTS.md: when graphify-out/graph.json exists, run a scoped 'graphify query' first; use graphify path/explain for relationship or concept questions.");
