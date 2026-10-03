# Graph Report - app  (2026-10-03)

## Corpus Check
- 11 files · ~68,253 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 50 nodes · 85 edges · 8 communities (5 shown, 3 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `647ba593`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- DatasetAcquisition
- acquisition.py
- Settings
- HuggingFaceClient
- cli.py
- Libras Translation — aquisição de datasets
- FakeClient
- libras-translation

## God Nodes (most connected - your core abstractions)
1. `DatasetAcquisition` - 10 edges
2. `HuggingFaceClient` - 10 edges
3. `main()` - 8 edges
4. `FakeClient` - 8 edges
5. `Settings` - 7 edges
6. `RemoteFile` - 7 edges
7. `AcquisitionTests` - 7 edges
8. `Libras Translation — aquisição de datasets` - 4 edges
9. `format_size()` - 3 edges
10. `_atomic_json()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `AcquisitionTests` --uses--> `Settings`  [INFERRED]
  dataset/tests/test_acquisition.py → dataset/src/libras_translation/config.py
- `FakeClient` --uses--> `RemoteFile`  [INFERRED]
  dataset/tests/test_acquisition.py → dataset/src/libras_translation/infrastructure/huggingface_client.py
- `main()` --calls--> `DatasetAcquisition`  [EXTRACTED]
  dataset/src/libras_translation/cli.py → dataset/src/libras_translation/acquisition.py
- `AcquisitionTests` --uses--> `DatasetAcquisition`  [INFERRED]
  dataset/tests/test_acquisition.py → dataset/src/libras_translation/acquisition.py
- `main()` --calls--> `Settings`  [EXTRACTED]
  dataset/src/libras_translation/cli.py → dataset/src/libras_translation/config.py

## Import Cycles
- None detected.

## Communities (8 total, 3 thin omitted)

### Community 0 - "DatasetAcquisition"
Cohesion: 0.36
Nodes (3): DatasetAcquisition, Read HF_TOKEN populated from the environment or the project .env., AcquisitionTests

### Community 1 - "acquisition.py"
Cohesion: 0.33
Nodes (5): _atomic_json(), _error_message(), Path, RemoteFile, Exception

### Community 2 - "Settings"
Cohesion: 0.29
Nodes (3): Path, Settings, Ferramentas de pesquisa para tradução Gloss-Free de Libras.

### Community 4 - "cli.py"
Cohesion: 0.53
Nodes (4): ArgumentParser, format_size(), build_parser(), main()

### Community 5 - "Libras Translation — aquisição de datasets"
Cohesion: 0.40
Nodes (4): Ambiente no Windows (PowerShell), Aquisição de vídeos, Estrutura atual, Libras Translation — aquisição de datasets

## Knowledge Gaps
- **4 isolated node(s):** `libras-translation`, `Ambiente no Windows (PowerShell)`, `Aquisição de vídeos`, `Estrutura atual`
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `HuggingFaceClient` connect `HuggingFaceClient` to `acquisition.py`, `cli.py`?**
  _High betweenness centrality (0.170) - this node is a cross-community bridge._
- **Why does `DatasetAcquisition` connect `DatasetAcquisition` to `acquisition.py`, `HuggingFaceClient`, `cli.py`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Why does `FakeClient` connect `FakeClient` to `DatasetAcquisition`, `acquisition.py`, `Settings`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **What connects `libras-translation`, `Ambiente no Windows (PowerShell)`, `Aquisição de vídeos` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._