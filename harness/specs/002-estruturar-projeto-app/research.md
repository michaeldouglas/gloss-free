# Research: Estruturar Projeto App

**Feature**: [spec.md](spec.md)
**Status**: Complete
**Reviewed**: 2026-10-11

## Decision: Manter `../app/` separado do harness

O código executável, a configuração do projeto, os dados e os testes ficam em
`../app/`. O Spec Kit, suas especificações, planos e scripts ficam em
`harness/`.

Essa separação preserva o harness como ferramenta de governança e reduz o risco
de misturar arquivos de aplicação com artefatos de planejamento.

## Decision: Preservar o projeto Python existente

O projeto usa Python >=3.10 conforme `../app/pyproject.toml`, com `uv` para
resolver o ambiente. A aplicação expõe a CLI `libras` e mantém sua implementação
em `dataset/src/libras_translation/`.

Essa decisão reflete o código implementado e evita impor uma migração de
linguagem, frontend ou arquitetura sem uma nova necessidade funcional.

## Decision: Usar a integração oficial do Hugging Face

O cliente externo usa `huggingface_hub`, resolve o commit remoto antes da
operação e preserva caminhos, tamanhos e estados nos manifestos locais.

Isso fornece rastreabilidade e permite retomar aquisições sem substituir
silenciosamente uma versão de dataset por outra.

## Decision: Manter testes determinísticos com `unittest`

A suíte usa fakes, mocks e diretórios temporários para validar aquisição,
manifestos, configuração e CLI sem downloads reais, credenciais ou acesso à
rede. A validação atual contém 11 testes e termina com sucesso.

Essa abordagem mantém o ciclo local rápido e reserva chamadas reais ao Hugging
Face para verificações operacionais explícitas, fora da suíte padrão.
