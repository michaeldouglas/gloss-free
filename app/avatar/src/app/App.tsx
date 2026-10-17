import { AvatarCanvas } from "../avatar/components/avatar-canvas";
import type { LiviAvatarDiagnostics } from "../avatar/components/LiviAvatar";
import { AvatarFilePicker } from "../components/avatar-file-picker";
import { useAvatarRuntime } from "../hooks/use-avatar-runtime";
import { useState } from "react";
import "./app.css";

function App() {
  const { controller, model, isLoading, error, loadAvatar } = useAvatarRuntime();
  const [diagnostics, setDiagnostics] = useState<LiviAvatarDiagnostics | null>(null);

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Dissertação · módulo de avatar</p>
          <h1>Libras Avatar</h1>
          <p className="subtitle">
            Base modular para visualização, controle e futura execução de sequências em Libras.
          </p>
        </div>
        <span className="status-badge">{window.desktop?.isDesktop ? "Electron" : "Web"}</span>
      </header>

      <section className="workspace" aria-label="Área de trabalho do avatar">
        <AvatarCanvas
          className="avatar-canvas"
          controller={controller}
          model={model}
          onDiagnostics={setDiagnostics}
        />

        <aside className="control-panel">
          <div>
            <p className="panel-label">Estado do avatar</p>
            <h2>{model ? "Avatar carregado" : "avatar.glb carregado"}</h2>
            <p className="panel-description">
              O modelo principal é carregado de <code>/avatars/avatar.glb</code>.
            </p>
          </div>

          <AvatarFilePicker
            disabled={isLoading}
            onSelect={(file) => {
              setDiagnostics(null);
              void loadAvatar({ kind: "file", file });
            }}
          />

          {isLoading ? <p className="feedback feedback--info">Carregando modelo…</p> : null}
          {error ? <p className="feedback feedback--error">{error}</p> : null}
          {diagnostics || model ? (
            <dl className="model-details">
              <div>
                <dt>Formato</dt>
                <dd>{model?.format.toUpperCase() ?? "GLB"}</dd>
              </div>
              <div>
                <dt>Origem</dt>
                <dd>{model?.sourceName ?? "/avatars/avatar.glb"}</dd>
              </div>
              {diagnostics ? <>
                <div><dt>Nodes</dt><dd>{diagnostics.nodes}</dd></div>
                <div><dt>Meshes</dt><dd>{diagnostics.meshes}</dd></div>
                <div><dt>Materials</dt><dd>{diagnostics.materials}</dd></div>
                <div><dt>Textures</dt><dd>{diagnostics.textures}</dd></div>
                <div><dt>Bones / skins</dt><dd>{diagnostics.bones} / {diagnostics.skins}</dd></div>
                <div><dt>Animations</dt><dd>{diagnostics.animations}</dd></div>
              </> : null}
            </dl>
          ) : null}

          <div className="architecture-note">
            <p className="panel-label">Próximas camadas</p>
            <ul>
              <li>mapeamento humanoide VRM</li>
              <li>poses de mãos e dedos</li>
              <li>expressões e animações temporais</li>
            </ul>
          </div>
        </aside>
      </section>
    </main>
  );
}

export default App;
