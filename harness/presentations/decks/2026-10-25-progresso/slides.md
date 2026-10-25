---
theme: default
title: O que fizemos até agora — e o que falta medir
author: Pesquisa em tradução de Libras
aspectRatio: 16/9
colorSchema: light
fonts:
  sans: Atkinson Hyperlegible
  serif: Crimson Pro
  mono: Fira Code
  provider: none
transition: fade
selectable: true
---

<div class="cover-slide">
  <svg class="cover-mark" viewBox="0 0 64 64" role="img" aria-label="Símbolo abstrato de movimento e conexão">
    <path d="M6 39c12 0 12-20 25-20s13 22 27 22" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" />
    <circle cx="8" cy="39" r="4" fill="currentColor" />
    <circle cx="57" cy="41" r="4" fill="currentColor" />
  </svg>
  <h1>O que fizemos até agora</h1>
  <p class="cover-audience">Checkpoint de pesquisa · {{ $date($release.release_date) }}</p>
  <p class="slide-subtitle">Antes de avaliar tradução, verificamos se os dados descrevem os vídeos e suas anotações.</p>
  <div class="cover-accent"></div>
  <p class="cover-meta">MINDS-Libras · V-LIBRASIL · evidências com datas próprias</p>
</div>

<!--
Fala sugerida: “Vou apresentar o avanço da pesquisa até este checkpoint. O trabalho concluído está na preparação e auditoria dos dados; ainda não temos resultado de tradução automática.”
-->

---

# A pesquisa parte de vídeos em Libras e busca texto em português

<p class="claim">A meta é investigar como representações visuais aprendidas podem apoiar a tradução sem uma sequência intermediária de glosas.</p>

<div class="story-flow" aria-label="Objetivo da pesquisa">
  <div class="story-step"><strong>Vídeo em Libras</strong><span>Mãos, rosto e corpo em movimento</span></div>
  <svg class="story-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
  <div class="story-step"><strong>Representação visual</strong><span>Pistas visuais aprendidas por um modelo</span></div>
  <svg class="story-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
  <div class="story-step"><strong>Português escrito</strong><span>Texto como saída da tradução</span></div>
</div>

<div class="evidence-panel blue">
  <h2>O que significa “sem glosas”</h2>
  <p>A tarefa não exige primeiro converter cada sinal em uma sequência de rótulos escritos. Essa é a formulação pretendida da dissertação; ainda não há um tradutor implementado ou avaliado neste projeto.</p>
</div>

<p class="source-note">Base conceitual: proposta de dissertação e referência a Zhou et al. (ICCV 2023).</p>

<!--
Fala sugerida: “A pesquisa quer sair diretamente do vídeo para o texto. ‘Sem glosas’ descreve a ausência de uma sequência intermediária de rótulos; não quer dizer que já construímos ou testamos esse modelo.”
-->

---

# A validação evita que dados desalinhados entrem nos experimentos

<p class="claim">Se uma anotação aponta para o vídeo errado, o experimento começa medindo o par errado.</p>

<div class="two-column">
  <div>
    <h2>O que conferimos</h2>
    <ol class="next-list">
      <li>Se cada registro tem um arquivo de vídeo correspondente.</li>
      <li>Se dimensões e informação temporal da tabela descrevem o vídeo real.</li>
      <li>Se divergências e problemas de origem ficam registrados.</li>
    </ol>
  </div>
  <div class="evidence-panel">
    <h2>Em palavras simples</h2>
    <p><strong>Manifest</strong> é a lista que declara quais arquivos pertencem ao dataset. A auditoria compara essa lista com os arquivos e as anotações disponíveis.</p>
  </div>
</div>

<p class="source-note">Escopo descrito na feature 003 e no notebook de preparação e validação dos datasets.</p>

<!--
Fala sugerida: “Antes de discutir arquitetura de modelo, garantimos que a entrada faz sentido. O manifest é só uma lista de referência; comparamos essa declaração com o que realmente existe.”
-->

---

# A checagem foi implementada como um processo repetível

<div class="story-flow" aria-label="Fluxo da auditoria">
  <div class="story-step"><strong>Entradas</strong><span>Vídeos, CSVs e manifest</span></div>
  <svg class="story-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
  <div class="story-step"><strong>Inspeção</strong><span>Metadados reais lidos de cada vídeo</span></div>
  <svg class="story-arrow" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
  <div class="story-step"><strong>Relatório</strong><span>Correspondências, divergências e proveniência</span></div>
</div>

<div class="two-column">
  <p>O processo compara dimensões e interpretações possíveis do campo temporal, registra as falhas por arquivo e produz resultados estruturados para revisão.</p>
  <div class="evidence-panel blue">
    <h2>Integridade dos dados</h2>
    <p>Os vídeos brutos são lidos, não alterados. As tabelas e os relatórios derivados ficam separados das fontes originais.</p>
  </div>
</div>

<p class="source-note">Notebook: inventário, validação CSV × vídeo real e relatório da execução.</p>

<!--
Fala sugerida: “O importante aqui é que a mesma verificação pode ser repetida e deixa um rastro. Os arquivos originais ficam intactos; as conclusões vêm dos relatórios gerados.”
-->

---

# No MINDS-Libras, os registros auditados correspondem aos vídeos

<p class="claim">{{ $fmt($mind?.key_reconciliation?.matched) }} de {{ $fmt($mind?.key_reconciliation?.csv_records) }} registros do CSV têm vídeo físico correspondente.</p>

<div class="story-stats">
  <div class="story-stat"><strong>{{ $fmt($mind?.counts.physical_videos) }}</strong><span>vídeos físicos</span></div>
  <div class="story-stat"><strong>{{ $fmt($mind?.counts.annotations) }}</strong><span>anotações</span></div>
  <div class="story-stat"><strong>{{ $fmt($mind?.counts.manifest_rows) }}</strong><span>linhas no manifest</span></div>
</div>

<div class="two-column">
  <p><strong>{{ $fmt($mind?.key_reconciliation?.missing) }} ausentes</strong> · <strong>{{ $fmt($mind?.key_reconciliation?.extra) }} extras</strong><br>O resumo registra {{ $fmt($mind?.counts.by_severity.CRITICAL) }} CRITICAL, {{ $fmt($mind?.counts.by_severity.ERROR) }} ERROR e {{ $fmt($mind?.counts.by_severity.WARNING) }} WARNING.</p>
  <div class="evidence-panel">
    <DecisionBadge :decision="$mind?.decision || 'UNKNOWN'" />
    <p>GO significa que os critérios desta auditoria de integridade foram atendidos. Não é um resultado de tradução.</p>
  </div>
</div>

<p class="source-note">Resumo de qualidade: {{ $dateTime($mind?.generated_at_utc) }} · execução técnica: {{ $dateTime($latest.executed_at) }}.</p>

<!--
Fala sugerida: “No resumo do MINDS-Libras, as 800 linhas e os 800 vídeos se alinham; não há registro ausente ou extra. O GO vale para esta conferência dos dados. Não significa que o conjunto já foi validado para qualidade de tradução.”
-->

---

# Neste recorte, o campo fps se comporta como contagem de frames

<div class="two-column">
  <DataComparison
    title="Hipóteses para interpretar o campo fps"
    :items="[
      { label: 'Taxa real', value: $latest.technical_summary.fps_rate_matches, display: $fmt($latest.technical_summary.fps_rate_matches) + ' / ' + $fmt($latest.technical_summary.videos_seen), accent: 'blue' },
      { label: 'Número de frames', value: $latest.technical_summary.fps_frame_count_matches, display: $fmt($latest.technical_summary.fps_frame_count_matches) + ' / ' + $fmt($latest.technical_summary.videos_seen), accent: 'teal' }
    ]"
    :max="$latest.technical_summary.videos_seen"
    caption="Cada valor do CSV foi comparado com as duas interpretações; o arquivo original foi preservado."
  />
  <div>
    <p class="claim">Nos {{ $fmt($latest.technical_summary.videos_seen) }} vídeos, {{ $fmt($latest.technical_summary.fps_rate_matches) }} valores coincidiram com a taxa real e {{ $fmt($latest.technical_summary.fps_frame_count_matches) }} coincidiram com o número de frames.</p>
    <p>Para esta execução, o campo chamado <code>fps</code> descreve melhor uma contagem de quadros do que quadros por segundo.</p>
  </div>
</div>

<p class="source-note">Execução do MINDS-Libras em {{ $dateTime($latest.executed_at) }} · tolerância para a taxa real: {{ $latest.technical_summary.fps_tolerance }}.</p>

<!--
Fala sugerida: “FPS normalmente significa quadros por segundo. Nesta checagem, os valores do campo coincidem com a quantidade total de quadros dos 800 vídeos e não com a taxa real. Preservamos o CSV; a conclusão é sobre como interpretar esse campo neste dataset e nesta execução.”
-->

---

# No V-LIBRASIL, três registros ainda não têm vídeo físico correspondente

<div class="story-stats">
  <div class="story-stat"><strong>{{ $fmt($vlibrasil?.counts.manifest_rows) }}</strong><span>linhas no manifest</span></div>
  <div class="story-stat"><strong>{{ $fmt($vlibrasil?.counts.physical_videos) }}</strong><span>vídeos físicos</span></div>
  <div class="story-stat"><strong>{{ $fmt($vlibrasil?.counts.provenance?.error_missing_file) }}</strong><span>linhas de erro sem arquivo</span></div>
</div>

<div class="two-column">
  <div>
    <p>O relatório aponta {{ $fmt($vlibrasil?.counts.issues) }} ocorrências: {{ $fmt($vlibrasil?.counts.by_severity.CRITICAL) }} CRITICAL e {{ $fmt($vlibrasil?.counts.by_severity.ERROR) }} ERROR.</p>
    <p>As {{ $fmt($vlibrasil?.counts.provenance?.error_rows) }} linhas de <code>error.csv</code> não aparecem em <code>annotations.csv</code> e não têm vídeo físico correspondente.</p>
  </div>
  <div class="evidence-panel purple">
    <DecisionBadge :decision="$vlibrasil?.decision || 'UNKNOWN'" />
    <p>NO-GO registra pendências de integridade e proveniência neste resumo. Não é um julgamento sobre a língua, os sinalizadores ou a qualidade de uma tradução.</p>
  </div>
</div>

<p class="source-note">Resumo de qualidade gerado em {{ $dateTime($vlibrasil?.generated_at_utc) }}.</p>

<!--
Fala sugerida: “O manifest lista três itens a mais que os vídeos físicos. O relatório localiza três linhas sem arquivo e soma outras ocorrências de erro. Por isso, o resumo marca NO-GO até que as divergências sejam analisadas.”
-->

---

# Os relatórios têm datas diferentes e precisam ser lidos com esse contexto

<div class="two-column">
  <section class="evidence-panel">
    <h2>MINDS-Libras</h2>
    <p><strong>Resumo de qualidade</strong><br>{{ $dateTime($mind?.generated_at_utc) }}</p>
    <p><strong>Execução técnica mais recente</strong><br>{{ $dateTime($latest.executed_at) }}</p>
    <p>O resumo e a inspeção técnica foram gerados separadamente no mesmo dia.</p>
  </section>
  <section class="evidence-panel purple">
    <h2>V-LIBRASIL</h2>
    <p><strong>Resumo de qualidade disponível</strong><br>{{ $dateTime($vlibrasil?.generated_at_utc) }}</p>
    <p>Este retrato é anterior ao resumo do MINDS-Libras.</p>
  </section>
</div>

<p class="claim">Podemos descrever o estado registrado de cada dataset. Não devemos apresentar esses dois relatórios como uma comparação feita na mesma data.</p>

<p class="source-note">Datas convertidas para o horário de Brasília; a origem de cada resumo está registrada no snapshot desta versão.</p>

<!--
Fala sugerida: “O MINDS foi verificado em 25 de outubro. O resumo disponível para o V-LIBRASIL é de 14 de outubro à noite. Por isso apresento os números com suas datas e evito interpretar a diferença como se fosse uma comparação simultânea.”
-->

---

# O notebook documenta inventário e validação; os experimentos ainda não aparecem

<div class="research-status">
  <section>
    <h2>Feito e registrado</h2>
    <ul class="next-list">
      <li>Inventário de arquivos e colunas.</li>
      <li>Conferência de chaves e correspondência entre CSV e vídeos.</li>
      <li>Inspeção dos metadados técnicos e da proveniência.</li>
      <li>Relatórios para revisar cada resultado.</li>
    </ul>
  </section>
  <section>
    <h2>Ainda sem resultado neste checkpoint</h2>
    <ul class="next-list">
      <li>Análise exploratória aprofundada dos dados.</li>
      <li>Baseline de tradução ou comparação de modelos.</li>
      <li>Métricas de qualidade da tradução.</li>
    </ul>
  </section>
</div>

<p class="claim">Hoje temos evidência sobre a consistência dos dados. Ainda não temos evidência sobre como um modelo traduz.</p>

<p class="source-note">Escopo observado no notebook de inventário e nos relatórios publicados desta versão.</p>

<!--
Fala sugerida: “O notebook já percorre o inventário e as validações técnicas. No material desta versão não há EDA aprofundada nem experimento de tradução. Essa distinção impede que um avanço de infraestrutura pareça um resultado científico que ainda não foi medido.”
-->

---

# A próxima sequência é resolver pendências e então avaliar modelos

<ol class="next-list">
  <li><strong>Revisar as ocorrências do V-LIBRASIL.</strong> Começar pelos três registros sem arquivo físico e documentar o destino de cada um.</li>
  <li><strong>Consolidar as interpretações dos metadados.</strong> Registrar o significado observado do campo fps sem substituir o valor original do CSV.</li>
  <li><strong>Avançar para a análise exploratória.</strong> Descrever os dados disponíveis antes de definir um baseline e as métricas de avaliação.</li>
  <li><strong>Executar o primeiro experimento de tradução.</strong> Só então reportar resultados de modelo, com protocolo e evidências associados.</li>
</ol>

<p class="source-note">Esta sequência explicita um caminho de trabalho compatível com as pendências dos relatórios e o objetivo da dissertação.</p>

<!--
Fala sugerida: “O próximo marco é fechar a leitura dos dados, seguir para a análise exploratória e só depois comparar um modelo com um protocolo definido. Assim os resultados de tradução terão uma base rastreável.”
-->

---

# O avanço de hoje prepara uma avaliação confiável para amanhã

<p class="claim">Já conseguimos verificar se os vídeos correspondem às anotações. Ainda não medimos a qualidade de uma tradução automática.</p>

<div class="two-column">
  <div>
    <p><strong>MINDS-Libras:</strong> 800 registros correspondentes e campo <code>fps</code> compatível com contagem de frames nesta execução.</p>
    <p><strong>V-LIBRASIL:</strong> três linhas sem vídeo físico no resumo de 14 de outubro.</p>
    <p><strong>Próximo marco:</strong> tratar pendências e iniciar análise exploratória.</p>
  </div>
  <div class="evidence-panel blue">
    <h2>Detalhes e fontes</h2>
    <div class="closing-links">
      <a href="../../validation/index.html">Ver auditorias</a>
      <a href="../../reports/latest.html">Ler relatório técnico</a>
    </div>
  </div>
</div>

<p class="source-note">Síntese do checkpoint de {{ $date($release.release_date) }} · fontes detalhadas nos relatórios e no notebook.</p>

<!--
Fala sugerida: “Para encerrar: nosso avanço foi tornar a qualidade e a proveniência dos dados verificáveis. O estado do V-LIBRASIL ainda tem pendências, e nenhum modelo foi avaliado. O trabalho seguinte começa pelos dados e avança até uma avaliação definida.”
-->