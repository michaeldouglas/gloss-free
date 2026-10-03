# Graph Report - harness  (2026-10-03)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 489 nodes · 857 edges · 58 communities (45 shown, 13 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `647ba593`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 54
- Community 55
- Community 56
- Community 57

## God Nodes (most connected - your core abstractions)
1. `main()` - 14 edges
2. `_build_report()` - 13 edges
3. `DatasetAcquisition` - 10 edges
4. `HuggingFaceClient` - 10 edges
5. `init_artifacts()` - 10 edges
6. `main()` - 10 edges
7. `main()` - 10 edges
8. `_HtmlTextParser` - 9 edges
9. `build_report()` - 9 edges
10. `search_docs()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `AcquisitionTests` --uses--> `DatasetAcquisition`  [INFERRED]
  dataset/tests/test_acquisition.py → dataset/src/libras_translation/acquisition.py
- `AcquisitionTests` --uses--> `Settings`  [INFERRED]
  dataset/tests/test_acquisition.py → dataset/src/libras_translation/config.py
- `FakeClient` --uses--> `RemoteFile`  [INFERRED]
  dataset/tests/test_acquisition.py → dataset/src/libras_translation/infrastructure/huggingface_client.py
- `main()` --calls--> `build_report()`  [EXTRACTED]
  .agents/skills/intel-hardware-advisor/scripts/hardware_probe.py → .agents/skills/intel-hardware-advisor/scripts/report_model.py
- `main()` --calls--> `DatasetAcquisition`  [EXTRACTED]
  dataset/src/libras_translation/cli.py → dataset/src/libras_translation/acquisition.py

## Import Cycles
- None detected.

## Communities (58 total, 13 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.22
Nodes (24): _action(), _available(), _build_actions(), _build_report(), _compatible(), _detect_context(), _exact_version(), _live_verify() (+16 more)

### Community 1 - "Community 1"
Cohesion: 0.22
Nodes (23): meaningful(), Any, split_ids(), unresolved_high_priority_novelty_questions(), validate_coverage_questions(), main(), parse_non_negative(), parse_prisma() (+15 more)

### Community 2 - "Community 2"
Cohesion: 0.19
Nodes (14): default_cache_dir(), _download(), ensure_snapshot(), _excerpt(), _extract_archive(), _HtmlTextParser, inspect_cache(), main() (+6 more)

### Community 3 - "Community 3"
Cohesion: 0.23
Nodes (20): collect_additional_configurations(), collect_live(), collect_openvino(), collect_platform(), _configuration(), _device_type(), _has_device_node(), _is_container() (+12 more)

### Community 4 - "Community 4"
Cohesion: 0.24
Nodes (19): _build_parser(), _context_md(), _decision_json(), _evidence_table_md(), _first_table_header(), init_artifacts(), _is_rating(), _load_json() (+11 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (20): Trilhas de anotação, Segmentação ataque até manutenção, Boia MD e ME, Depicção e classificadores MD e ME, ELAN, Face, Glosa funcional, Olhar (+12 more)

### Community 6 - "Community 6"
Cohesion: 0.36
Nodes (17): action_close(), action_list(), action_record_cited(), action_record_papers_received(), action_record_search(), action_start(), action_status(), load_session() (+9 more)

### Community 7 - "Community 7"
Cohesion: 0.23
Nodes (13): Find-SpecifyRoot(), Format-SpecKitCommand(), Get-CurrentBranch(), Get-FeaturePathsEnv(), Get-InvokeSeparator(), Get-NormalizedPriority(), Get-Python3Command(), Get-RepoRoot() (+5 more)

### Community 8 - "Community 8"
Cohesion: 0.30
Nodes (14): evidence(), Inputs, main(), parser(), protocol(), ArgumentParser, Namespace, recall_audit() (+6 more)

### Community 9 - "Community 9"
Cohesion: 0.21
Nodes (10): _build_parser(), _build_search_query(), main(), _normalise_arxiv_id(), _parse_entry(), Any, ArgumentParser, search() (+2 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (13): 1.018 animações geradas, CCD-TAAL, FAPESP Processo 2024/00914-7, IPT, METEOR, Vigência 01/07/2024 a 30/06/2029, ROUGE, SEDPcD (+5 more)

### Community 11 - "Community 11"
Cohesion: 0.32
Nodes (11): deduplicate(), filter_min_citations(), filter_year(), format_markdown(), load_papers(), main(), merge_records(), normalize_arxiv_id() (+3 more)

### Community 12 - "Community 12"
Cohesion: 0.20
Nodes (12): Anamnese: 4.357 sentenças em português, Dataset de anamnese médica, Avaliação com a comunidade surda, Eye tracking: 27 participantes surdos e 30 sentenças, Captura facial e expressões não manuais, Comparação intérprete humano versus Hand Talk e VLibras, ICSL: 127 cenários, 3 veículos e mais de 1,5 milhão de frames, ICSL - Dataset de interação em veículos (+4 more)

### Community 13 - "Community 13"
Cohesion: 0.18
Nodes (12): BLEU-4 24,54 em Gloss2Text, BLEU-4 25,51 PHOENIX14T e 41,12 VLibrasBD, RWTH-PHOENIX-Weather 2014T, Sign2Gloss / Vídeo para Glosa, Produção de língua de sinais (SLP), Reconhecimento de língua de sinais (SLR), Text2Gloss / Texto para Glosa, Tradução Libras para português (+4 more)

### Community 14 - "Community 14"
Cohesion: 0.17
Nodes (12): CLIP / alinhamento visual-textual, GCN e ST-GCN, Redes neurais convolucionais (CNNs), Visão computacional aplicada à tradução de Libras, Redes convolucionais em grafos (GCNs), Modelos de linguagem para tradução semântica, MediaPipe para extração de mãos, face e corpo, Alinhamento multimodal imagem-linguagem (+4 more)

### Community 15 - "Community 15"
Cohesion: 0.33
Nodes (8): action(), build_report(), detect_context(), infer_framework(), load_fixture(), main(), Namespace, redact()

### Community 16 - "Community 16"
Cohesion: 0.20
Nodes (10): Libras como língua de poucos recursos computacionais, Reconstrução de pose mascarada, Corpus local de materiais do projeto, Pré-treinamento multimodal MSLU, Aprendizado contrastivo sinal-texto, SL-1.5M: cerca de 1,5 milhão de amostras pose-texto, GFSLT-VLP 2023, MSLU 2024 (+2 more)

### Community 17 - "Community 17"
Cohesion: 0.39
Nodes (8): _build_parser(), _extract_counts(), main(), _parse_non_negative_int(), ArgumentParser, Path, _render_flow_markdown(), _validate_consistency()

### Community 18 - "Community 18"
Cohesion: 0.64
Nodes (7): build_recommendation(), build_report(), _evidence(), _fact(), Any, _text(), validate_report()

### Community 19 - "Community 19"
Cohesion: 0.50
Nodes (7): clean(), extract_pdf_text(), main(), Path, resolve_source_path(), safe_name(), wanted()

### Community 20 - "Community 20"
Cohesion: 0.29
Nodes (8): Avatar sinalizante 3D Clara, Avatar sinalizante videorrealista, Síntese concatenativa de Libras, Gloss2Sign / Glosa para Vídeo, Suavização por quaternions e continuidade de velocidade, CCD-TAAL Relatório Parcial 01, CCD-TAAL Relatório Parcial 02, Avatar videorrealista adiado

### Community 21 - "Community 21"
Cohesion: 0.36
Nodes (8): BLEU e BLEU-4, Gloss2Text / Glosa para Texto, Sign2Text / Vídeo para Texto direto, Tradução de língua de sinais (SLT), Análise de métodos e bases de dados do CCD-TAAL, Proposta de dissertação: tradução gloss-free Libras–português, Tradução gloss-free de Libras para português escrito, Glosa como representação intermediária

### Community 22 - "Community 22"
Cohesion: 0.25
Nodes (8): CSL-News: 1.985 horas e 751.320 clips, Pré-treinamento generativo, MediaPipe, mT5-base, Prior-Guided Fusion (PGF), Score-aware sampling, Diagrama do framework Uni-Sign, Framework Uni-Sign

### Community 23 - "Community 23"
Cohesion: 0.62
Nodes (6): clean(), extract_front_matter(), main(), Path, read_front_matter(), resolve_source_path()

### Community 24 - "Community 24"
Cohesion: 0.52
Nodes (6): count_signals(), generate_starter_questions(), main(), Any, recommend(), render_human()

### Community 25 - "Community 25"
Cohesion: 0.29
Nodes (7): Aplicações de acessibilidade, Desafios de equipamentos, MoCap e armazenamento, Cardápio: 960 sentenças, Dataset de cardápios Web, Dados de captura de movimento MoCap, Acervo superior a 2 TB, Protótipo de acessibilidade Web com avatar

### Community 26 - "Community 26"
Cohesion: 0.60
Nodes (5): build_query(), fetch_batch(), filter_by_year(), main(), parse_entry()

### Community 27 - "Community 27"
Cohesion: 0.60
Nodes (5): efetch_batch(), esearch(), main(), parse_xml(), _text()

### Community 28 - "Community 28"
Cohesion: 0.60
Nodes (5): consistency_check(), fetch_arxiv_meta(), fetch_crossref_meta(), find_citations(), main()

### Community 29 - "Community 29"
Cohesion: 0.67
Nodes (5): _get_json(), main(), render_human(), search_openalex(), search_pubmed()

### Community 31 - "Community 31"
Cohesion: 0.80
Nodes (4): main(), make_source_id(), Path, register_sources()

### Community 32 - "Community 32"
Cohesion: 0.70
Nodes (4): check_deps(), generate(), main(), Path

### Community 33 - "Community 33"
Cohesion: 0.70
Nodes (4): aggregate(), main(), Any, render_human()

### Community 34 - "Community 34"
Cohesion: 0.83
Nodes (3): context(), load(), main()

### Community 35 - "Community 35"
Cohesion: 0.83
Nodes (3): create_matrices(), main(), Path

### Community 36 - "Community 36"
Cohesion: 0.83
Nodes (3): main(), Path, validate()

### Community 37 - "Community 37"
Cohesion: 0.83
Nodes (3): fetch_page(), main(), normalize()

### Community 38 - "Community 38"
Cohesion: 0.83
Nodes (3): fetch_page(), main(), normalize()

### Community 39 - "Community 39"
Cohesion: 0.83
Nodes (3): fetch_page(), main(), normalize()

### Community 54 - "Community 54"
Cohesion: 0.09
Nodes (18): ArgumentParser, _atomic_json(), DatasetAcquisition, _error_message(), format_size(), Path, build_parser(), main() (+10 more)

### Community 55 - "Community 55"
Cohesion: 0.40
Nodes (4): Ambiente no Windows (PowerShell), Aquisição de vídeos, Estrutura atual, Libras Translation — aquisição de datasets

## Knowledge Gaps
- **11 isolated node(s):** `libras-translation`, `Ambiente no Windows (PowerShell)`, `Aquisição de vídeos`, `Estrutura atual`, `Redes neurais convolucionais (CNNs)` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CCD-TAAL Relatório Parcial 02` connect `Community 20` to `Community 5`, `Community 10`, `Community 12`, `Community 16`, `Community 22`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Why does `Tradução gloss-free de Libras para português escrito` connect `Community 21` to `Community 16`, `Community 20`, `Community 13`, `Community 14`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Why does `Visão computacional aplicada à tradução de Libras` connect `Community 14` to `Community 21`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **What connects `libras-translation`, `Ambiente no Windows (PowerShell)`, `Aquisição de vídeos` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 5` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `Community 54` be split into smaller, more focused modules?**
  _Cohesion score 0.08668076109936575 - nodes in this community are weakly interconnected._