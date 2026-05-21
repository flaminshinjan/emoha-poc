/* App entry — renders Direction A (Hearth) full-bleed. */

function App() {
  return (
    <div data-screen-label="App" style={{ width: "100%", height: "100vh", display: "flex", flexDirection: "column" }}>
      <DirectionA density="roomy" insightVisible={true} avatarShape="soft" />
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
