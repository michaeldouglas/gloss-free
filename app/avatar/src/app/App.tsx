import { useEffect, useState } from "react";
import { createLiviJavaScriptApi } from "../avatar/avatar-api";
import { Livi2DController } from "../avatar/2d/livi-controller";
import { LiviAvatar2D } from "../avatar/components/livi-avatar-2d";
import { LiviControls } from "../avatar/components/livi-controls";
import type { LiviJavaScriptApi } from "../avatar/avatar-api";
import "./app.css";

function App() {
  const [controller] = useState(() => new Livi2DController());

  useEffect(() => {
    const livi = createLiviJavaScriptApi(controller);
    window.livi = livi;
    window.avatar = livi;
    return () => {
      delete window.livi;
      delete window.avatar;
    };
  }, [controller]);

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Dissertação · personagem articulada</p>
          <h1>Livi 2D</h1>
          <p className="subtitle">
            Uma personagem vetorial controlada por TypeScript, preparada para receber poses, expressões e sequências de Libras.
          </p>
        </div>
        <div className="status-stack">
          <span className="status-badge">SVG + React</span>
          <span className="status-badge status-badge--quiet">procedural</span>
        </div>
      </header>

      <section className="workspace" aria-label="Área de trabalho da Livi">
        <LiviAvatar2D controller={controller} className="livi-stage" />
        <LiviControls controller={controller} />
      </section>

      <footer className="api-footer">
        <span>API:</span> <code>window.livi.setPose(...)</code> <code>window.livi.moveHand(...)</code> <code>window.livi.sign("hello")</code>
      </footer>
    </main>
  );
}

export default App;

declare global {
  interface Window {
    livi?: LiviJavaScriptApi;
    avatar?: LiviJavaScriptApi;
  }
}
