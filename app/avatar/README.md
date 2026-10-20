# Livi 2D

Aplicação web da personagem Livi, uma figura vetorial articulada para
experimentos de animação procedural e futura execução de sinais de Libras.

O runtime usa React, TypeScript e SVG, sem backend, banco de dados ou assets
binários de personagem.

## Executar

Na pasta `app/avatar`:

```powershell
npm install
npm run dev
```

Abra o endereço informado pelo Vite, normalmente
`http://127.0.0.1:8080/`.

Validações e build:

```powershell
npm run typecheck
npm test
npm run build:web
```

O comando `npm run build` continua disponível para gerar também os artefatos
Electron herdados do projeto, mas a personagem e a interface web não dependem
do Electron.

## Controle por JavaScript/TypeScript

Depois que a aplicação carrega, a API fica exposta no console do navegador:

```js
window.livi.setPose({
  headRotation: -8,
  arms: {
    right: { upperArm: -55, forearm: 18, wrist: -12 },
  },
  legs: {
    left: { thigh: -10, shin: 8 },
  },
});

window.livi.setHandShape("right", "point");
window.livi.setFingerCurl("right", "middle", 0.8);
window.livi.setFingerJointRotation("right", "index", "middle", 48);
window.livi.setPartTransform("rightHand", {
  x: 14,
  y: -8,
  rotation: 22,
  scaleX: 1.2,
});
window.livi.moveHand("right", { x: 310, y: 300 });
window.livi.setExpression("smile", 0.8);
window.livi.setExpression("browLeft", -0.7);
window.livi.lookAt(0.6, -0.2);
window.livi.blink("left");
window.livi.sign("hello");
```

`window.avatar` aponta para a mesma API por compatibilidade com o protótipo
anterior. A API inclui:

- `setPose(...)` para aplicar vários segmentos de uma vez;
- `setSegmentRotation(...)` para tronco, cabeça, braços, antebraços, pulsos,
  coxas, canelas e tornozelos;
- `setPartTransform(...)` para mover, rotacionar e redimensionar cada grupo SVG
  do corpo;
- `setHandShape(...)`, `setFingerCurl(...)` e `setFingerJointRotation(...)`
  para controlar cada dedo e cada uma de suas juntas (base, meio, ponta e
  abertura lateral);
- `moveHand(...)` para resolver a posição da mão usando dois segmentos;
- `setExpression(...)`, `lookAt(...)` e `blink(...)` para controlar a face,
  incluindo boca, bochechas, sobrancelhas e olhos;
- `execute(...)` para reproduzir keyframes interpolados;
- `sign(...)` para acessar coreografias de demonstração até que o vocabulário
  de Libras validado seja conectado.

## Organização

- `src/avatar/2d/livi-types.ts`: estado, poses, keyframes e contratos da API;
- `src/avatar/2d/livi-controller.ts`: controlador procedural, IK planar,
  interpolação e coreografias;
- `src/avatar/components/livi-avatar-2d.tsx`: árvore SVG articulada;
- `src/avatar/components/livi-controls.tsx`: painel para inspecionar e
  controlar corpo, braços, mãos, dedos, pernas e expressão;
- `src/avatar/animation/sequence-player.ts`: timeline renderer-independent
  preservada para futuras sequências mais complexas.

Cada parte da personagem possui um grupo SVG identificável por `data-part` e
as articulações das mãos por `data-finger`, permitindo que novas camadas de
animação sejam adicionadas sem trocar o renderer.

## Camada visual

O rig e o estado continuam independentes da arte. A camada SVG atual apresenta
a Livi da cintura para cima, com rosto adulto, cabelo castanho em camadas,
blazer azul, mangas contínuas e mãos desenhadas como formas sobrepostas para
que as juntas internas não apareçam como peças. O componente aceita
`debug={true}` quando for necessário exibir os pontos básicos do rig; o padrão
é `debug={false}`.
