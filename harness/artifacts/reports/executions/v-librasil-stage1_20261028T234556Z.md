# V-LIBRASIL — fechamento da Etapa 1 para revisão humana

Execução técnica: 28/10/2026 20:12:23 a 20:39:10 (UTC−03), em 1606.806 segundos.
Geração canônica: 20261028T234556Z-12866758. Estado: revisão humana pendente.

Este relatório é uma projeção dos artefatos técnicos indicados abaixo. A decisão global da Etapa 1 permanece em aberto. Nenhuma EDA, Etapa 2 ou avaliação de modelo foi iniciada.

A revalidação ligou cada anotação a um único vídeo por uma chave normalizada, preservando o nome original. As três entradas de error.csv foram documentadas separadamente e não entraram no manifest.

## Resultado do V-LIBRASIL

| Verificação | Quantidade |
|---|---:|
| Registros CSV | 4.086 |
| Arquivos físicos | 4.086 |
| Correspondências | 4.086 |
| Ausentes | 0 |
| Extras | 0 |
| Duplicados após normalização — CSV | 0 |
| Duplicados após normalização — filesystem | 0 |
| Válidos | 4.086 |
| INFO | 3 |
| WARNING | 0 |
| ERROR | 0 |
| CRITICAL | 0 |
| Exceções documentadas | 3 |
| Arquivos ilegíveis pelo ffprobe | 0 |
| Ocorrências de issues | 3 |
| Arquivos físicos afetados | 0 |
| Anotações afetadas | 0 |

As ocorrências INFO pertencem às exceções de error.csv, fora do corpus válido. Elas não representam vídeos válidos ausentes nem falhas de leitura de arquivos físicos.

## Regra de identidade

NFC → mapeamento U+F022 para aspas, U+F03F para interrogação e U+F05C para barra invertida literal → remoção de espaços externos → casefold.
A barra invertida permanece um caractere do nome desde a enumeração. Nenhuma chave normalizada foi usada para renomear ou abrir um caminho reconstruído.

| Família revalidada | Anotações | Correspondências únicas |
|---|---:|---:|
| Frente\Á Frente_Articulador* | 3 | 3 |
| Cérebro (de "ervilha")_Articulador* | 3 | 3 |
| O quê?_Articulador* | 3 | 3 |

## Campo fps

| Verificação | Resultado |
|---|---:|
| Hipótese sustentada | actual_frame_count |
| Correspondências com actual_fps | 0 |
| Correspondências com actual_frame_count | 4086 |
| Ambas | 0 |
| Nenhuma | 0 |
| Inconclusivos | 0 |
| Valores declarados inválidos | 0 |
| Cobertura das duas hipóteses | 4086/4086 |
| Confiança operacional | high |
| Tolerância absoluta para taxa | 0.01 frames/s |

A confiança é uma regra determinística de cobertura, não uma medida de inferência estatística. Alta exige cobertura total e correspondência exclusiva de uma hipótese em todos os registros, sem ambiguidades ou inconclusivos; moderada exige pelo menos 95% de cobertura e correspondência exclusiva no total de anotações.
Fontes observadas: taxa {"avg_frame_rate": 4086}; frames {"nb_frames": 4086}. A contagem de frames é comparada exatamente.
Os valores originais e o nome da coluna fps foram preservados. As observações vieram da inspeção desta execução; as comparações foram rederivadas pelo código final contra as anotações originais.

## Definições de validade

- metadata_match: estado de concordância; exige correspondência única, dimensões compatíveis e suporte de uma hipótese temporal.
- technical_valid: vídeo legível com stream, dimensões, taxa e duração positivas e codec identificado, independentemente da concordância com o CSV.
- dataset_valid: registro com schema e nome válidos, identidade única, validade técnica, metadados compatíveis e ausência de bloqueios.

## Sete eixos operacionais

A especificação contém 18 FR e 8 SC, sem lista canônica de sete itens. A tabela consolida as seções 3–8 do notebook e explicita o mapeamento no JSON detalhado.

| Eixo | Status | Justificativa | Evidência |
|---|---|---|---|
| Leitura e preservação das fontes | PASS | Hashes tabulares e inventário físico antes/depois são iguais. | data/raw/v-librasil-raw/annotations.csv; data/raw/v-librasil-raw/videos/ |
| Schema e valores obrigatórios | PASS | 0 ocorrências em nove colunas obrigatórias. | data/raw/v-librasil-raw/annotations.csv |
| Chaves e unicidade | PASS | Colisões: 0; video_name/video_id/class+user foram avaliados. | data/raw/v-librasil-raw/annotations.csv; data/raw/v-librasil-raw/videos/ |
| Reconciliação CSV × filesystem | PASS | 4086 anotações, 4086 arquivos físicos, 4086 correspondências, 0 ausentes, 0 extras e 0 duplicados. | data/raw/v-librasil-raw/annotations.csv; data/raw/v-librasil-raw/videos/ |
| Metadados técnicos e fps | PASS | 4086/4086 tecnicamente válidos; FPS high. | data/processed/metadata-validation/v-librasil-raw/metadata_validation.json |
| Convenção dos nomes | PASS | 0 nomes inválidos; None permanece como PARTIAL. | data/processed/metadata-validation/v-librasil-raw/manifests/v_librasil_validated.parquet |
| Proveniência e manifest | PASS | Exceções observadas=True; manifest consistente=True; 3 issues e 0 arquivos afetados. | data/processed/metadata-validation/v-librasil-raw/reports/metadata_summary.json; data/processed/metadata-validation/v-librasil-raw/manifests/v_librasil_validated.parquet |

## Exceções documentadas

- Congelar_Articulador3.mp4: Ausência documentada; campos técnicos zerados na origem; fora do manifest.
- Criança_Articulador3.mp4: Ausência documentada; campos técnicos zerados na origem; fora do manifest.
- Poesia_Articulador2.mp4: Ausência documentada; campos técnicos zerados na origem; fora do manifest.

## Manifest

| Verificação | Linhas |
|---|---:|
| Esperadas a partir de annotations.csv | 4086 |
| Geradas | 4086 |

O gate conferiu contagens, identidade e unicidade das chaves, origem das linhas e os hashes de todos os artefatos do conjunto.
A publicação ativou um diretório completo e arquivou o resultado anterior como superado. No Windows pode existir breve ausência do caminho durante as renomeações; falhas síncronas têm rollback. Não se promete transação ACID com o registry.

## Preservação e rastreabilidade

- MINDS-Libras: 10 artefatos com SHA-256 idêntico antes e depois; entrada no registry preservada.
- Vídeos e CSVs brutos: montagem de entrada somente leitura; hashes dos CSVs e inventários de nomes/tamanhos/timestamps equivalentes.
- Foram normalizadas apenas diferenças textuais de zeros fracionários finais nos timestamps do inventário de auditoria. Não houve alteração nos arquivos de origem.
- O JSON técnico preserva os comandos efetivamente executados. Referências de fontes e saídas canônicas são relativas à pasta app.
- O ffprobe verifica streams e metadados; isso não comprova decodificação completa de todos os frames nem qualidade linguística.

## Artefatos canônicos

- [Relatório técnico](../../../../app/data/processed/metadata-validation/v-librasil-raw/reports/metadata_validation_report.md)
- [Resumo JSON](../../../../app/data/processed/metadata-validation/v-librasil-raw/reports/metadata_summary.json)
- [Revisão dos sete eixos](../../../../app/data/processed/metadata-validation/v-librasil-raw/reports/stage1_review.json)
- [Manifest Parquet](../../../../app/data/processed/metadata-validation/v-librasil-raw/manifests/v_librasil_validated.parquet)
- [Geração e hashes](../../../../app/data/processed/metadata-validation/v-librasil-raw/publication.json)
- [Execução e ferramentas](../../../../app/data/processed/metadata-validation/v-librasil-raw/execution_manifest.json)
- SHA-256 do resumo técnico: 2f268253d408880610363c3c431294aad81d749065024c8bf7306dea5bdf181a

Os artefatos científicos completos em app/data/processed/ são ignorados pelo Git. Esta projeção versionável mantém a origem, o identificador da geração e a evidência de preservação, sem substituir a fonte técnica.

Próxima ação: revisão humana deste fechamento exclusivo do V-LIBRASIL. Não foi emitida uma decisão global da Etapa 1.
