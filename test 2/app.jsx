/* ============================================================
   App orchestrator — full-bleed Direction A prototype with tweaks.
   ============================================================ */

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "density": "roomy",
  "insightVisible": true,
  "avatarShape": "soft"
}/*EDITMODE-END*/;

function App() {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);

  return (
    <>
      <div data-screen-label="App" style={{ width: "100%", height: "100vh", display: "flex", flexDirection: "column" }}>
        <DirectionA
          density={tweaks.density}
          insightVisible={tweaks.insightVisible}
          avatarShape={tweaks.avatarShape}
        />
      </div>

      <TweaksPanel title="Tweaks" defaultOpen={false}>
        <TweakSection title="Layout">
          <TweakRadio
            label="Density"
            value={tweaks.density}
            onChange={(v) => setTweak("density", v)}
            options={[
              { value: "cozy", label: "Cozy" },
              { value: "roomy", label: "Roomy" },
            ]}
          />
        </TweakSection>

        <TweakSection title="Call screen">
          <TweakToggle
            label="Show insight panel"
            value={tweaks.insightVisible}
            onChange={(v) => setTweak("insightVisible", v)}
          />
          <TweakRadio
            label="Avatar shape"
            value={tweaks.avatarShape}
            onChange={(v) => setTweak("avatarShape", v)}
            options={[
              { value: "soft", label: "Soft" },
              { value: "rect", label: "Sharp" },
              { value: "circle", label: "Circle" },
            ]}
          />
        </TweakSection>

        <TweakSection title="Jump to step">
          <SkipRow />
        </TweakSection>
      </TweaksPanel>
    </>
  );
}

function SkipRow() {
  const steps = [
    ["landing", "Landing"],
    ["brief", "Brief"],
    ["advisor", "Advisor"],
    ["call", "Call"],
    ["summary", "Summary"],
  ];
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
      {steps.map(([id, label]) => (
        <button key={id}
          onClick={() => window.dispatchEvent(new CustomEvent("proto-skip", { detail: { target: "a", screen: id } }))}
          style={{
            padding: "6px 10px", borderRadius: 4,
            border: "1px solid rgba(255,255,255,0.12)",
            background: "transparent",
            color: "rgba(255,255,255,0.85)",
            fontSize: 12, cursor: "pointer",
          }}>
          {label}
        </button>
      ))}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
