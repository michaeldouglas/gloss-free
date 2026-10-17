# Libras Avatar

Base web e desktop para o avatar humano 3D da dissertação. O projeto fica
isolado em `app/avatar` e não altera o módulo Python existente em `app/`.

## Executar

Na pasta `app/avatar`:

```powershell
npm install
npm run dev
```

Para executar a mesma interface em Electron durante o desenvolvimento:

```powershell
npm run dev:electron
```

Validações e build:

```powershell
npm run typecheck
npm test
npm run build
```

O pacote desktop pode ser produzido com `npm run package:desktop`. Os
artefatos compilados ficam em `dist/`, `dist-electron/` e `release/`; todos
estão ignorados pelo Git.

## Arquitetura

`src/` é o runtime compartilhável da aplicação. Ele não importa Electron:

- `src/avatar/loaders/` abstrai o carregamento de VRM 1.0, GLB e GLTF;
- `src/avatar/controllers/` contém controle de ossos, mãos, dedos,
  expressões e reprodução temporal sem dependência de uma interface específica;
- `src/avatar/animation/` contém o timeline determinístico para futuras
  sequências de Libras;
- `src/avatar/components/` contém a cena Three.js/R3F;
- `src/services/` coordena carregamento e ciclo de vida do runtime;
- `src/hooks/` conecta o runtime às interfaces React.

`electron/` contém somente a janela desktop e o preload seguro. A comunicação
entre Electron e o renderer é mínima e feita com `contextIsolation`,
`sandbox` e `contextBridge`. A interface web continua funcionando sem Electron.

Os arquivos de avatar futuros devem ser colocados em `public/avatars/` quando
forem assets versionáveis. O carregador também aceita arquivos escolhidos pelo
usuário, sem exigir que o modelo seja incluído agora.

## Decisões de compatibilidade

As dependências foram fixadas em versões estáveis consultadas no registry npm.
O Vite 8 requer Node 20.19+ ou 22.12+; este ambiente usa Node 24.11.1. R3F,
Drei e `@pixiv/three-vrm` compartilham Three.js como dependência explícita,
mantendo uma única versão no projeto.
