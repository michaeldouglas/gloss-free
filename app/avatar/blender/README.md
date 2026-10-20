# Controles faciais da Livi

Arquivo editável: `../public/avatars/livi.blend`.
Branch utilizada: `feature/validar-metadados-video`.

## Uso no Blender

Na janela 3D, pressione **N** e abra a aba **Livi**. Os controles funcionam
independentemente do objeto selecionado. **Voltar ao neutro** zera os controles;
**Inserir pose na linha do tempo** insere keyframes no frame atual. Os sliders
também aceitam a inserção individual de keyframes pelo menu do botão direito.

| Controle | Intervalo e comportamento |
| --- | --- |
| Fechar ambos | 0: abertos; 1: fechados; valores intermediários: fechamento gradual |
| Fechar esquerdo / direito | Piscar cada olho separadamente |
| Abrir mais | Aumentar a abertura das pálpebras |
| Olhar esquerda / direita | -1: esquerda da personagem; +1: direita da personagem |
| Olhar baixo / cima | -1: baixo; +1: cima |
| Olhar de perto | Convergência gradual dos olhos |
| Sobrancelha esquerda / direita | -1: baixar; +1: levantar |
| Franzir / levantar internas | Controlar as partes internas das sobrancelhas |
| Abrir boca | 0: repouso; 1: abertura máxima configurada |
| Cabeça | Virar, baixar/levantar e inclinar, com cabelo e rosto acompanhando |

Esquerda/direita são sempre os lados da **Livi**, invertidos em relação a quem
a observa de frente. Os movimentos dos olhos têm limites conservadores e as
pálpebras acompanham discretamente o olhar vertical. O fechamento completo tem
prioridade sobre a abertura adicional. Não há piscadas aleatórias nem animação
automática: os controles são manuais e animáveis.

O painel é o módulo de texto `livi_facial_panel.py`, incluído no `.blend`.
Se o painel não aparecer após abrir o arquivo, execute esse texto no workspace
**Scripting**. Não é necessário alterar as preferências de segurança do Blender.
Os controles continuam disponíveis sem executar scripts: selecione o objeto
`Livi_CONTROLES_FACIAIS` e use **Object Properties → Custom Properties**.
Drivers de expressões simples, shape keys e Geometry Nodes ficam salvos no arquivo.

Os botões de poses prontas não substituem uma animação já ativa. Nesse caso,
edite os sliders e seus keyframes diretamente.

## Conteúdo técnico

- 15 propriedades animáveis em `Livi_CONTROLES_FACIAIS`.
- 16 shape keys faciais novas na cabeça; as três chaves artísticas existentes
  foram preservadas. A malha base continua com 4.304 vértices e 4.279 polígonos.
- Pivôs dos olhos transformam esclera, íris, pupila e córnea em conjunto sobre
  as proporções elipsoidais ajustadas à personagem.
- Cílios nativos acompanham o fechamento por Geometry Nodes e atributos de
  deslocamento, preservando os fios originais. Sobrancelhas têm shape keys próprias.
- Cavidade oral existente recebe material interno. Dentes e língua simplificados
  foram adicionados para dar acabamento à abertura da boca.
- Os alvos e a correspondência de vértices estão incorporados ao `.blend`.
  O funcionamento do rig não depende de arquivos temporários nem da internet.

`livi_facial_rig.py` constrói o rig na cena inspecionada e não salva o arquivo
automaticamente. Não deve ser executado como um script de inicialização.
`livi_facial_validate.py` verifica poses, drivers, retorno ao neutro e oclusão.
`livi_facial_preview.py` gera imagens de inspeção e restaura câmera e renderização.

Este rig oferece os movimentos básicos solicitados. Não é um conjunto completo
de visemas, FACS, captura facial ou expressões não manuais de Libras. Também não
foi integrado ao aplicativo web nem exportado para GLB nesta alteração.

## Evidências e preservação

As prévias estão em `previews/` e a auditoria em `validation.json`, também
incorporada como texto `Livi_Rig_Facial_Validacao.json` no Blender. Os testes
incluem fechamento independente, olhar nos quatro sentidos, sobrancelhas,
abertura da boca, movimentos da cabeça e combinações de controles.

Backup anterior à criação do rig, fora do repositório:
`C:/Users/mdbaa/development/Dissertacao-backups/livi/livi_antes_controles_faciais_20261019_215505.blend`.
SHA-256: `490e3751ffa16e6844a50a52d244e1d083603caecbaab5b66a4a3fd8ae96e7e3`.

Nenhum commit ou Pull Request foi criado nesta alteração. As alterações anteriores
do worktree foram preservadas; não houve troca de branch.

## Origem dos alvos

Os dez arquivos de `assets/faceunits/` vêm de
[MakeHuman Community / extra-targets](https://github.com/makehumancommunity/extra-targets/tree/7eaba3453134385bb5ea9811ef0b33b85b4b556d/assets/faceunits01/targets/faceunits),
commit `7eaba3453134385bb5ea9811ef0b33b85b4b556d`, sob CC0 1.0. A licença está
incluída nessa pasta. Os alvos de piscar e mandíbula foram ajustados à modelagem
da Livi; não são uma certificação de realismo anatômico. A proveniência e os
hashes dos arquivos estão em `Livi_Rig_Facial_Fontes.json` dentro do `.blend`.
