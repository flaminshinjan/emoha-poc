/* ============================================================
   DIRECTION A — "HEARTH"
   Warm editorial. Soft cream background, serif headlines,
   generous whitespace. Feels like opening a letter from family.
   ============================================================ */

function DirectionA({ density = "roomy", insightVisible = true, avatarShape = "soft" }) {
  const [screen, setScreen] = React.useState("landing");
  const [brief, setBrief] = React.useState({
    caller_name: "",
    parent_name: "",
    parent_relation: "mother",
    city: "",
    lives_alone: null,
    distance: "different_city",
    mobility: null,
    conditions: [],
    prompt: "",
  });
  const [briefStep, setBriefStep] = React.useState(0);
  const [advisor, setAdvisor] = React.useState("priya");

  // Allow external skip-to-step via window event
  React.useEffect(() => {
    const onSkip = (e) => {
      if (e.detail?.target === "a") setScreen(e.detail.screen);
    };
    window.addEventListener("proto-skip", onSkip);
    return () => window.removeEventListener("proto-skip", onSkip);
  }, []);

  const go = (s) => setScreen(s);

  return (
    <div className={`proto dir-a density-${density}`} style={{ background: "var(--bg)", color: "var(--ink)" }}>
      <AHeader screen={screen} go={go} brief={brief} />
      <div className="proto-frame">
        {screen === "landing" && <ALanding key="landing" go={go} />}
        {screen === "brief" && (
          <ABrief key="brief" brief={brief} setBrief={setBrief} step={briefStep} setStep={setBriefStep} go={go} />
        )}
        {screen === "advisor" && (
          <AAdvisor key="advisor" advisor={advisor} setAdvisor={setAdvisor} go={go} />
        )}
        {screen === "call" && (
          <ACall key="call" brief={brief} advisor={advisor} insightVisible={insightVisible}
                 avatarShape={avatarShape} go={go} />
        )}
        {screen === "summary" && <ASummary key="summary" brief={brief} go={go} />}
      </div>
    </div>
  );
}

// ---------- Header (consistent across screens) ----------
function AHeader({ screen, go, brief }) {
  return (
    <header style={{
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "22px 36px", flexShrink: 0,
      borderBottom: "1px solid rgba(0,0,0,0.04)",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }} onClick={() => go("landing")}>
        <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden>
          <path d="M16 4 Q 26 12 26 22 Q 26 28 16 28 Q 6 28 6 22 Q 6 12 16 4 Z" fill="var(--ink)" />
          <circle cx="16" cy="20" r="3.5" fill="var(--bg)" />
        </svg>
        <div>
          <div className="serif" style={{ fontSize: 18, lineHeight: 1, fontWeight: 500 }}>emoha</div>
          <div style={{ fontSize: 11, color: "var(--ink-mute)", marginTop: 2, letterSpacing: "0.02em" }}>
            care advisor
          </div>
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
        {screen !== "landing" && (
          <span className="serif" style={{ fontSize: 14, color: "var(--ink-soft)", fontStyle: "italic" }}>
            {screenLabelA(screen)}
          </span>
        )}
        <EmergencyButton variant="a" onClick={() => alert("Connecting you to a human advisor in a moment…")} />
      </div>
    </header>
  );
}
function screenLabelA(s) {
  return { brief: "A short brief", advisor: "Choose who you'd like to speak with",
           call: "In conversation", summary: "What we heard" }[s] || "";
}

// ---------- 1. Landing ----------
function ALanding({ go }) {
  return (
    <div className="screen" style={{ padding: "var(--pad-y) var(--pad-x)" }}>
      <div style={{
        display: "grid",
        gridTemplateColumns: "minmax(0, 1.2fr) minmax(0, 1fr)",
        gap: 48,
        alignItems: "center",
        maxWidth: 1100, margin: "20px auto",
      }}>
        <div>
          <div style={{
            fontSize: 11, letterSpacing: "0.18em", color: "var(--ink-mute)",
            textTransform: "uppercase", marginBottom: 22,
          }}>For families with a parent who lives far away</div>

          <h1 className="serif" style={{
            margin: 0, fontSize: "clamp(36px, 4vw, 56px)", lineHeight: 1.05,
            fontWeight: 400, letterSpacing: "-0.02em", textWrap: "balance",
          }}>
            If you've been worrying about a parent who lives alone,<br />
            <em style={{ color: "var(--accent)" }}>start here.</em>
          </h1>

          <p style={{
            margin: "26px 0 36px", maxWidth: 480,
            fontSize: 16, lineHeight: 1.6, color: "var(--ink-soft)",
          }}>
            Have an honest, unhurried conversation with Priya — our care advisor.
            She'll help you think through what's happening, what feels heavy, and what kind
            of support might fit. There is nothing to buy on this call.
          </p>

          <div style={{ display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap" }}>
            <button className="btn-primary btn-hover" onClick={() => go("brief")}>
              Talk with Priya
            </button>
            <button className="btn-ghost btn-hover" onClick={() => go("brief")}>
              <span style={{ opacity: 0.7, marginRight: 6 }}>About 10 minutes</span>
              <span style={{ opacity: 0.4 }}>·</span>
              <span style={{ marginLeft: 6 }}>Free</span>
            </button>
          </div>

          <div style={{
            marginTop: 56, display: "flex", gap: 40, color: "var(--ink-soft)", fontSize: 13,
          }}>
            <ALandingPoint num="01" t="Tell us a little about your parent" />
            <ALandingPoint num="02" t="Speak with Priya, one-to-one" />
            <ALandingPoint num="03" t="Receive a written care summary" />
          </div>
        </div>

        <div style={{ position: "relative" }}>
          <div style={{
            position: "relative",
            width: "100%", aspectRatio: "4 / 5",
            borderRadius: 28, overflow: "hidden",
            boxShadow: "var(--shadow)",
            border: "1px solid rgba(0,0,0,0.04)",
          }}>
            <AvatarPortrait name="Priya" />
            <div style={{
              position: "absolute", left: 0, right: 0, bottom: 0,
              padding: "22px 26px",
              background: "linear-gradient(0deg, rgba(20,30,28,0.72) 0%, transparent 100%)",
              color: "#f7f2e6",
            }}>
              <div className="serif" style={{ fontSize: 28, lineHeight: 1.1 }}>Priya</div>
              <div style={{ fontSize: 13, opacity: 0.85, marginTop: 4 }}>
                Senior Care Advisor · with Emoha since 2019
              </div>
            </div>
          </div>
          <div style={{
            position: "absolute", bottom: -16, right: -16,
            background: "var(--card)", padding: "14px 18px",
            borderRadius: 14, boxShadow: "0 14px 36px -18px rgba(0,0,0,0.2)",
            border: "1px solid var(--line)",
            maxWidth: 220, fontSize: 13, lineHeight: 1.45,
          }}>
            <div className="serif" style={{ fontSize: 14, marginBottom: 4, color: "var(--accent-deep)" }}>
              Available now
            </div>
            <div style={{ color: "var(--ink-soft)" }}>
              No appointment needed. Just tap when you're ready.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
function ALandingPoint({ num, t }) {
  return (
    <div style={{ flex: 1 }}>
      <div className="mono" style={{ fontSize: 11, color: "var(--accent)", marginBottom: 6 }}>{num}</div>
      <div style={{ color: "var(--ink)" }}>{t}</div>
    </div>
  );
}

// ---------- 2. Brief (6-step intake) ----------
function ABrief({ brief, setBrief, step, setStep, go }) {
  const cur = BRIEF_STEPS[step];
  const total = BRIEF_STEPS.length;

  const next = () => step < total - 1 ? setStep(step + 1) : go("advisor");
  const back = () => step > 0 ? setStep(step - 1) : go("landing");

  return (
    <div className="screen" style={{ padding: "var(--pad-y) var(--pad-x)" }}>
      <div style={{ maxWidth: 640, margin: "0 auto" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 56 }}>
          <span className="mono" style={{ fontSize: 11, color: "var(--ink-mute)", letterSpacing: "0.1em" }}>
            STEP {String(step + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}
          </span>
          <StepDots count={total} current={step} />
        </div>

        <div style={{ minHeight: 320 }}>
          <h2 className="serif" style={{
            margin: 0, fontSize: "clamp(28px, 3.4vw, 40px)", lineHeight: 1.15,
            fontWeight: 400, letterSpacing: "-0.015em", textWrap: "balance",
          }}>{cur.q}</h2>

          <div style={{ marginTop: 36 }}>
            <ABriefField step={cur} brief={brief} setBrief={setBrief} onEnter={next} />
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 56 }}>
          <button className="btn-ghost btn-hover" onClick={back} style={{ background: "transparent", border: "none" }}>
            ← Back
          </button>
          <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
            <button onClick={() => go("advisor")} className="btn-hover"
              style={{ color: "var(--ink-mute)", fontSize: 14, padding: "10px 14px" }}>
              Skip — Priya will ask
            </button>
            <button className="btn-primary btn-hover" onClick={next}>
              {step === total - 1 ? "Continue" : "Next"}  →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ABriefField({ step, brief, setBrief, onEnter }) {
  const updateBrief = (patch) => setBrief({ ...brief, ...patch });

  if (step.kind === "text") {
    return (
      <input type="text" placeholder={step.placeholder}
        value={brief[step.id] || ""} autoFocus
        onChange={(e) => updateBrief({ [step.id]: e.target.value })}
        onKeyDown={(e) => e.key === "Enter" && onEnter()} />
    );
  }
  if (step.kind === "textarea") {
    return (
      <textarea rows={3} placeholder={step.placeholder}
        value={brief.prompt || ""}
        onChange={(e) => updateBrief({ prompt: e.target.value })}
        style={{ fontFamily: "inherit", resize: "none", lineHeight: 1.5 }} />
    );
  }
  if (step.kind === "parent") {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 26 }}>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {["mother", "father", "both"].map((r) => (
            <button key={r}
              className={`chip ${brief.parent_relation === r ? "selected" : ""}`}
              onClick={() => updateBrief({ parent_relation: r })}>
              {r === "both" ? "Both parents" : `My ${r}`}
            </button>
          ))}
        </div>
        <input type="text" placeholder="Their name (optional)"
          value={brief.parent_name || ""}
          onChange={(e) => updateBrief({ parent_name: e.target.value })}
          onKeyDown={(e) => e.key === "Enter" && onEnter()} />
      </div>
    );
  }
  if (step.kind === "where") {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
        <input type="text" placeholder="City"
          value={brief.city || ""} autoFocus
          onChange={(e) => updateBrief({ city: e.target.value })}
          onKeyDown={(e) => e.key === "Enter" && onEnter()} />
        <div>
          <div style={{ fontSize: 13, color: "var(--ink-mute)", marginBottom: 10 }}>Do they live alone?</div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {[
              { id: true, label: "Yes, on their own" },
              { id: false, label: "With family or help" },
            ].map((o) => (
              <button key={String(o.id)}
                className={`chip ${brief.lives_alone === o.id ? "selected" : ""}`}
                onClick={() => updateBrief({ lives_alone: o.id })}>
                {o.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <div style={{ fontSize: 13, color: "var(--ink-mute)", marginBottom: 10 }}>And you?</div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {[
              { id: "same_city", label: "Same city" },
              { id: "different_city", label: "Different city in India" },
              { id: "abroad", label: "I live abroad" },
            ].map((o) => (
              <button key={o.id}
                className={`chip ${brief.distance === o.id ? "selected" : ""}`}
                onClick={() => updateBrief({ distance: o.id })}>
                {o.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }
  if (step.kind === "options") {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {step.options.map((o) => (
          <button key={o.id}
            onClick={() => updateBrief({ mobility: o.id })}
            className="btn-hover"
            style={{
              textAlign: "left", padding: "18px 22px", borderRadius: 14,
              border: `1px solid ${brief.mobility === o.id ? "var(--accent)" : "var(--line)"}`,
              background: brief.mobility === o.id ? "rgba(59,106,99,0.06)" : "var(--card)",
              fontSize: 16, color: "var(--ink)", display: "flex", alignItems: "center", gap: 14,
            }}>
            <span style={{
              width: 16, height: 16, borderRadius: 999,
              border: `1px solid ${brief.mobility === o.id ? "var(--accent)" : "var(--line)"}`,
              background: brief.mobility === o.id ? "var(--accent)" : "transparent",
              flexShrink: 0,
            }}></span>
            {o.label}
          </button>
        ))}
      </div>
    );
  }
  if (step.kind === "chips") {
    const cur = brief.conditions || [];
    const toggle = (c) => {
      if (c === "None right now") { updateBrief({ conditions: ["None right now"] }); return; }
      const next = cur.filter((x) => x !== "None right now");
      updateBrief({ conditions: next.includes(c) ? next.filter((x) => x !== c) : [...next, c] });
    };
    return (
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        {step.options.map((o) => (
          <button key={o} onClick={() => toggle(o)} className={`chip ${cur.includes(o) ? "selected" : ""}`}>
            {o}
          </button>
        ))}
      </div>
    );
  }
  return null;
}

// ---------- 3. Advisor picker ----------
function AAdvisor({ advisor, setAdvisor, go }) {
  return (
    <div className="screen" style={{ padding: "var(--pad-y) var(--pad-x)" }}>
      <div style={{ maxWidth: 1000, margin: "0 auto" }}>
        <h2 className="serif" style={{
          fontSize: "clamp(28px, 3.2vw, 40px)", margin: "0 0 8px", fontWeight: 400, letterSpacing: "-0.015em",
        }}>Who would you like to speak with?</h2>
        <p style={{ color: "var(--ink-soft)", margin: "0 0 40px", maxWidth: 540, lineHeight: 1.6 }}>
          Each of our advisors has been trained the same way. The difference is mostly in how
          they sound and the rhythm of their conversation. Pick whoever feels right today —
          you can change next time.
        </p>

        <div style={{
          display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 18,
        }}>
          {ADVISORS.map((a) => {
            const sel = advisor === a.slug;
            return (
              <button key={a.slug} onClick={() => setAdvisor(a.slug)} className="card btn-hover"
                style={{
                  textAlign: "left", padding: 22,
                  border: `1px solid ${sel ? "var(--accent)" : "var(--line)"}`,
                  background: sel ? "rgba(59,106,99,0.05)" : "var(--card)",
                  display: "flex", flexDirection: "column", gap: 14,
                  position: "relative", overflow: "hidden",
                }}>
                <div style={{
                  width: 76, height: 96, borderRadius: 14, overflow: "hidden",
                  position: "relative", flexShrink: 0,
                }}>
                  <AvatarPortrait name={a.slug} />
                </div>
                <div>
                  <div className="serif" style={{ fontSize: 22 }}>{a.name}</div>
                  <div style={{ fontSize: 12, color: a.color, marginTop: 2, fontStyle: "italic" }}>{a.role}</div>
                </div>
                <div style={{ fontSize: 13, color: "var(--ink-soft)", lineHeight: 1.5 }}>{a.desc}</div>
                {sel && (
                  <div className="mono" style={{
                    position: "absolute", top: 16, right: 16, fontSize: 10, letterSpacing: "0.1em",
                    color: "var(--accent)", textTransform: "uppercase",
                  }}>Selected</div>
                )}
              </button>
            );
          })}

          <div className="card" style={{
            padding: 22, display: "flex", flexDirection: "column", gap: 12,
            background: "transparent", border: "1px dashed var(--line)",
          }}>
            <div className="serif" style={{ fontSize: 18 }}>Use your own voice</div>
            <div style={{ fontSize: 13, color: "var(--ink-soft)", lineHeight: 1.5 }}>
              Upload a 10–30 second clip — your advisor will speak in that voice for this call.
            </div>
            <button className="btn-ghost btn-hover" style={{ padding: "10px 16px", fontSize: 13, alignSelf: "flex-start" }}>
              Upload a clip
            </button>
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 44 }}>
          <button className="btn-hover" onClick={() => go("brief")}
            style={{ color: "var(--ink-mute)", fontSize: 14, padding: "10px 14px" }}>
            ← Back
          </button>
          <button className="btn-primary btn-hover" onClick={() => go("call")}>
            Start the conversation  →
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------- 4. Live call ----------
function ACall({ brief, advisor, insightVisible, avatarShape, go }) {
  const [muted, setMuted] = React.useState(false);
  const [speaking, setSpeaking] = React.useState(true);
  const [insightPhase, setInsightPhase] = React.useState(0);
  const [elapsed, setElapsed] = React.useState(0);
  const [transcript, setTranscript] = React.useState([]);

  React.useEffect(() => {
    const t = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(t);
  }, []);
  React.useEffect(() => {
    const t = setInterval(() => setSpeaking((s) => !s), 2400);
    return () => clearInterval(t);
  }, []);
  React.useEffect(() => {
    const t = setInterval(() => setInsightPhase((p) => Math.min(p + 1, 4)), 5500);
    return () => clearInterval(t);
  }, []);

  // Drip transcript lines in
  React.useEffect(() => {
    let i = 0;
    const tick = () => {
      if (i < TRANSCRIPT.length) {
        setTranscript((cur) => [...cur, TRANSCRIPT[i]]);
        i++;
        setTimeout(tick, 3500);
      }
    };
    const id = setTimeout(tick, 1200);
    return () => clearTimeout(id);
  }, []);

  const adv = ADVISORS.find((a) => a.slug === advisor) || ADVISORS[0];
  const mm = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const ss = String(elapsed % 60).padStart(2, "0");

  const shape =
    avatarShape === "circle" ? "50%" :
    avatarShape === "rect" ? "16px" :
    "32px";

  return (
    <div className="screen" style={{ padding: "26px var(--pad-x) var(--pad-y)" }}>
      <div style={{
        display: "grid", gridTemplateColumns: "minmax(0, 1.5fr) minmax(280px, 1fr)",
        gap: 32, alignItems: "stretch",
        maxWidth: 1180, margin: "0 auto",
      }}>
        {/* HERO avatar */}
        <div style={{
          position: "relative", borderRadius: shape, overflow: "hidden",
          aspectRatio: "5 / 6", boxShadow: "var(--shadow)",
          minHeight: 520,
        }}>
          <AvatarPortrait name={adv.name} speaking={speaking} />
          <div className={`speak-ring ${speaking && !muted ? "active" : ""}`}></div>

          {/* Top bar (live tag + timer) */}
          <div style={{
            position: "absolute", top: 18, left: 18, right: 18,
            display: "flex", justifyContent: "space-between", alignItems: "center",
            color: "#f7f2e6",
          }}>
            <div style={{
              display: "inline-flex", alignItems: "center", gap: 8,
              padding: "6px 12px", borderRadius: 999,
              background: "rgba(20,30,28,0.55)", backdropFilter: "blur(8px)",
              fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase",
            }}>
              <span style={{
                width: 6, height: 6, borderRadius: 999, background: "#67d18f",
                boxShadow: "0 0 0 4px rgba(103,209,143,0.25)",
              }}></span>
              In conversation
            </div>
            <div className="mono" style={{
              padding: "6px 12px", borderRadius: 999,
              background: "rgba(20,30,28,0.55)", backdropFilter: "blur(8px)",
              fontSize: 12,
            }}>{mm}:{ss}</div>
          </div>

          {/* Name overlay */}
          <div style={{
            position: "absolute", left: 0, right: 0, bottom: 0,
            padding: "26px 26px 20px",
            background: "linear-gradient(0deg, rgba(20,30,28,0.7) 0%, transparent 100%)",
            color: "#f7f2e6",
          }}>
            <div className="serif" style={{ fontSize: 32, lineHeight: 1.05 }}>{adv.name}</div>
            <div style={{ fontSize: 13, opacity: 0.85, marginTop: 4 }}>{adv.role} · Care Advisor</div>
          </div>
        </div>

        {/* Right column */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20, minHeight: 0 }}>
          {/* Insight ribbon */}
          {insightVisible && (
            <div className="card" style={{ padding: "16px 20px", background: "rgba(255,255,255,0.5)" }}>
              <div className="mono" style={{
                fontSize: 10, letterSpacing: "0.16em", color: "var(--ink-mute)",
                marginBottom: 10, textTransform: "uppercase",
              }}>
                What Priya is taking in
              </div>
              <InsightRibbon active={true} variant="a" phase={insightPhase} />
            </div>
          )}

          {/* Transcript preview */}
          <div className="card" style={{
            padding: 20, flex: 1, minHeight: 240, display: "flex", flexDirection: "column",
            background: "var(--card)",
          }}>
            <div className="mono" style={{
              fontSize: 10, letterSpacing: "0.16em", color: "var(--ink-mute)",
              marginBottom: 14, textTransform: "uppercase",
            }}>
              Live transcript
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10, overflowY: "auto" }}>
              {transcript.length === 0 && (
                <div style={{ color: "var(--ink-mute)", fontStyle: "italic", fontSize: 14 }}>
                  Connecting…
                </div>
              )}
              {transcript.map((line, i) => {
                const text = line.t
                  .replace("{name}", brief.caller_name || "")
                  .replace("{parent}", brief.parent_name || "your mother");
                return (
                  <div key={i} className={`bubble ${line.who}`}>{text}</div>
                );
              })}
            </div>
          </div>

          {/* Controls */}
          <div className="card" style={{
            padding: "16px 18px", display: "flex", alignItems: "center", justifyContent: "space-between",
            gap: 12, background: "var(--card)",
          }}>
            <button onClick={() => setMuted(!muted)} className="btn-hover" style={{
              display: "flex", alignItems: "center", gap: 8,
              padding: "10px 14px", borderRadius: 999,
              border: "1px solid var(--line)",
              background: muted ? "rgba(200,116,86,0.15)" : "transparent",
              color: muted ? "var(--warm)" : "var(--ink)", fontSize: 13,
            }}>
              <span style={{ display: "inline-block", width: 14, textAlign: "center" }}>
                {muted ? "🔇" : "🎙"}
              </span>
              {muted ? "Mic muted" : "Mic live"}
            </button>

            <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--accent)" }}>
              <LevelBars />
            </div>

            <button onClick={() => go("summary")} className="btn-hover" style={{
              padding: "10px 16px", borderRadius: 999,
              background: "var(--ink)", color: "#f7f2e6", fontSize: 13,
            }}>
              End gently
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------- 5. Summary ----------
function ASummary({ brief, go }) {
  // Derive a plausible plan + score from the brief
  const condCount = (brief.conditions || []).filter((c) => c !== "None right now").length;
  const limited = brief.mobility === "limited";
  const partial = brief.mobility === "partial";
  const distant = brief.distance === "abroad" || brief.distance === "different_city";

  const score = Math.max(3, Math.min(8,
    7 - (limited ? 3 : partial ? 1 : 0) - Math.min(2, condCount) - (brief.lives_alone ? 1 : 0)
  ));
  const plan = score >= 7 ? "wellness" : score >= 5 ? "plus" : "total";
  const planMeta = {
    wellness: { name: "Emoha Wellness", tag: "A gentle starting point", price: "₹2,499 / month",
      why: "Things sound largely under control. A lighter starting point gives families peace of mind without making parents feel monitored.",
      includes: ["Regular wellness check-in calls", "Festival & birthday calls", "Community engagement invites", "Family alerted if a check-in is missed"] },
    plus: { name: "Emoha Care Plus", tag: "Active care coordination", price: "₹5,999 / month",
      why: "A dedicated coordinator — an Emoha Daughter — handles appointments, reminders and emergency coordination, so you can stop being the on-call manager from far away.",
      includes: ["A dedicated Emoha Daughter", "Doctor appointment accompaniment", "Medication & refill reminders", "24×7 emergency coordination", "Wellness calls + community"] },
    total: { name: "Emoha Total Care", tag: "Full-spectrum care", price: "₹11,999 / month",
      why: "Given the recent event and the distance between you, the priority is having someone close by who can step in for emergencies, home visits and travel.",
      includes: ["Everything in Care Plus", "Priority emergency response", "Home visits by care managers", "Travel coordination across cities", "Emotional wellbeing sessions"] },
  }[plan];

  const parentName = brief.parent_name || "your mother";
  const callerName = brief.caller_name || "friend";
  const city = brief.city || "Lucknow";

  // Compose risk profile based on inputs
  const risk = {
    prep: limited ? 1 : partial ? 2 : 3,
    isolation: brief.lives_alone === true ? 4 : 2,
    coordination: distant ? 3 : partial || limited ? 3 : 2,
  };

  return (
    <div className="screen" style={{ padding: "var(--pad-y) var(--pad-x)" }}>
      <div style={{ maxWidth: 1080, margin: "0 auto" }}>
        {/* Header — letter heading */}
        <div className="mono" style={{
          fontSize: 11, letterSpacing: "0.18em", color: "var(--ink-mute)", textTransform: "uppercase",
          marginBottom: 14, display: "flex", alignItems: "center", gap: 10,
        }}>
          <span style={{ width: 22, height: 1, background: "currentColor" }}></span>
          A note from your call
          <span style={{ flex: 1, height: 1, background: "rgba(0,0,0,0.08)", marginLeft: 6 }}></span>
          <span style={{ color: "var(--ink-soft)" }}>Tuesday · 11:42 am</span>
        </div>

        <h2 className="serif" style={{
          fontSize: "clamp(30px, 3.6vw, 44px)", margin: "0 0 14px", fontWeight: 400, letterSpacing: "-0.015em",
          textWrap: "balance", lineHeight: 1.12,
        }}>
          Thank you for talking with us, {callerName}.
        </h2>
        <p style={{ color: "var(--ink-soft)", margin: "0 0 36px", maxWidth: 660, lineHeight: 1.65, fontSize: 17 }}>
          Here is what I heard, and what I think might come next. None of this is a contract —
          it's a starting point you can sit with. <span style={{ color: "var(--ink)" }}>I'll be here when you want to talk again.</span>
        </p>

        {/* Top row — score + emotional arc + urgency */}
        <div style={{ display: "grid", gridTemplateColumns: "minmax(220px, 0.9fr) minmax(0, 1.6fr) minmax(180px, 0.7fr)", gap: 18, marginBottom: 18 }}>
          {/* Confidence ring */}
          <div className="card" style={{ padding: 24, display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center" }}>
            <div className="mono" style={{ fontSize: 10, letterSpacing: "0.16em", color: "var(--ink-mute)", textTransform: "uppercase", marginBottom: 14 }}>
              Care confidence
            </div>
            <div style={{ position: "relative" }}>
              <ScoreRing value={score} max={10} size={130} stroke={9} />
              <div style={{
                position: "absolute", inset: 0, display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center",
              }}>
                <div className="serif" style={{ fontSize: 38, lineHeight: 1 }}>{score}<span style={{ fontSize: 16, color: "var(--ink-mute)" }}>/10</span></div>
              </div>
            </div>
            <div style={{ marginTop: 14, fontSize: 13, color: "var(--ink-soft)", lineHeight: 1.5, maxWidth: 200 }}>
              {score >= 7 ? "Calm picture today — light support recommended."
                : score >= 5 ? "Coordination gaps to address — middle ground recommended."
                : "Several pressing concerns — fuller cover recommended."}
            </div>
          </div>

          {/* Emotional arc */}
          <div className="card" style={{ padding: 24 }}>
            <div className="mono" style={{ fontSize: 10, letterSpacing: "0.16em", color: "var(--ink-mute)", textTransform: "uppercase", marginBottom: 14 }}>
              How the conversation felt
            </div>
            <EmotionalArc />
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 10, fontSize: 12, color: "var(--ink-mute)" }}>
              <span>Start of call</span>
              <span>Middle</span>
              <span>End of call</span>
            </div>
            <p style={{ margin: "16px 0 0", fontSize: 13.5, color: "var(--ink-soft)", lineHeight: 1.55 }}>
              Anxiety and guilt opened the call. Both eased as we talked through what's actually
              in your hands and what is not.
            </p>
          </div>

          {/* Urgency */}
          <div className="card" style={{ padding: 24, background: score < 5 ? "rgba(200, 116, 86, 0.08)" : "var(--card)" }}>
            <div className="mono" style={{ fontSize: 10, letterSpacing: "0.16em", color: "var(--ink-mute)", textTransform: "uppercase", marginBottom: 12 }}>
              Urgency
            </div>
            <div className="serif" style={{ fontSize: 24, lineHeight: 1.1, marginBottom: 8 }}>
              {score < 5 ? "Don't wait" : score < 7 ? "Soon" : "When you're ready"}
            </div>
            <p style={{ margin: 0, fontSize: 13, color: "var(--ink-soft)", lineHeight: 1.55 }}>
              {score < 5
                ? "Recent event + distance means we'd like a care manager visiting within the week."
                : score < 7
                ? "Nothing critical tonight. We'll follow up within 48 hours."
                : "No action needed. We're here whenever you'd like to begin."}
            </p>
          </div>
        </div>

        {/* Main two-column body */}
        <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.5fr) minmax(280px, 1fr)", gap: 24 }}>
          {/* Left column */}
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            {/* What Priya heard */}
            <div className="card" style={{ padding: 28 }}>
              <div className="mono" style={{ fontSize: 10, letterSpacing: "0.16em", color: "var(--ink-mute)", textTransform: "uppercase", marginBottom: 18 }}>
                What I heard
              </div>

              {/* Pulled-quote */}
              <blockquote className="serif" style={{
                margin: "0 0 22px", fontSize: 22, lineHeight: 1.35,
                color: "var(--ink)", fontStyle: "italic", letterSpacing: "-0.005em",
                paddingLeft: 18, borderLeft: "2px solid var(--accent)",
                textWrap: "balance",
              }}>
                "I'm in Bangalore and she's alone in {city}. I don't know how to stop worrying."
              </blockquote>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px 28px" }}>
                <ASumLine label={`Worry that's been quietly building since ${parentName}'s fall`} />
                <ASumLine label={`Guilt about being far away`} />
                <ASumLine label={`The wish to keep ${parentName} feeling independent`} />
                <ASumLine label={`Wanting someone closer who can step in for emergencies`} />
              </div>
            </div>

            {/* Family situation */}
            <div className="card" style={{ padding: 28 }}>
              <div className="mono" style={{ fontSize: 10, letterSpacing: "0.16em", color: "var(--ink-mute)", textTransform: "uppercase", marginBottom: 18 }}>
                Your family — at a glance
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 18 }}>
                <ASumFact label="Parent" value={`${brief.parent_relation === "father" ? "Father" : "Mother"}${brief.parent_name ? `, ${brief.parent_name}` : ""}`} />
                <ASumFact label="Lives in" value={`${city}${brief.lives_alone === true ? ", alone" : brief.lives_alone === false ? ", with family" : ""}`} />
                <ASumFact label="You live" value={brief.distance === "abroad" ? "Abroad" : brief.distance === "same_city" ? "Same city" : "A different city"} />
                <ASumFact label="Mobility" value={mobLabelA(brief.mobility) || "Some support needed"} />
                <ASumFact label="Conditions" value={(brief.conditions?.filter((c) => c !== "None right now").join(" · ")) || "—"} />
                <ASumFact label="Recent event" value="Bathroom fall, ~2 weeks ago" />
              </div>
            </div>

            {/* Recommended plan */}
            <div className="card" style={{ padding: 28, position: "relative", overflow: "hidden" }}>
              <div className="mono" style={{ fontSize: 10, letterSpacing: "0.16em", color: "var(--accent)", textTransform: "uppercase", marginBottom: 14 }}>
                A possible direction · {planMeta.tag}
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 14, gap: 10, flexWrap: "wrap" }}>
                <h3 className="serif" style={{ margin: 0, fontSize: 30, fontWeight: 400, letterSpacing: "-0.01em" }}>
                  {planMeta.name}
                </h3>
                <span style={{ color: "var(--ink-soft)", fontSize: 14 }}>{planMeta.price} · cancel any time</span>
              </div>
              <p style={{ margin: "0 0 22px", color: "var(--ink-soft)", lineHeight: 1.65, fontSize: 15.5 }}>
                {planMeta.why}
              </p>
              <ul style={{ margin: 0, paddingLeft: 0, listStyle: "none", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {planMeta.includes.map((it) => (
                  <li key={it} style={{ display: "flex", alignItems: "flex-start", gap: 10, fontSize: 14, color: "var(--ink)" }}>
                    <span style={{ width: 14, flexShrink: 0, color: "var(--accent)", marginTop: 3 }}>—</span>
                    <span>{it}</span>
                  </li>
                ))}
              </ul>

              <div style={{ display: "flex", gap: 10, marginTop: 22, alignItems: "center", flexWrap: "wrap" }}>
                <button className="btn-primary btn-hover" onClick={() => alert("In production, this opens the plan in the Emoha app.")}>
                  Explore {planMeta.name}
                </button>
                <button className="btn-ghost btn-hover">
                  Compare with other plans
                </button>
                <span style={{ marginLeft: "auto", fontSize: 12.5, color: "var(--ink-mute)" }}>
                  Nothing has been charged.
                </span>
              </div>
            </div>
          </div>

          {/* Right column */}
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            {/* Risk indicators */}
            <div className="card" style={{ padding: 24 }}>
              <div className="mono" style={{ fontSize: 10, letterSpacing: "0.16em", color: "var(--ink-mute)", textTransform: "uppercase", marginBottom: 16 }}>
                Where to focus
              </div>
              <ARiskRow label="Emergency readiness" v={risk.prep} hint="Who picks up when something happens" />
              <ARiskRow label="Care coordination" v={5 - risk.coordination} hint="Appointments, refills, follow-ups" />
              <ARiskRow label="Connection" v={5 - risk.isolation} hint="Daily warmth, not just safety" inverted />
              <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid var(--line)", fontSize: 12.5, color: "var(--ink-mute)", lineHeight: 1.55 }}>
                Higher is better. These are Priya's read of the situation, not a diagnosis.
              </div>
            </div>

            {/* Callback */}
            <div className="card" style={{ padding: 24, background: "rgba(59,106,99,0.04)", border: "1px solid rgba(59,106,99,0.2)" }}>
              <div className="mono" style={{ fontSize: 10, letterSpacing: "0.16em", color: "var(--accent)", textTransform: "uppercase", marginBottom: 10 }}>
                Next step
              </div>
              <div className="serif" style={{ fontSize: 22, lineHeight: 1.2, marginBottom: 10 }}>
                Meera will call you Tuesday, 6:30 pm
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                <div style={{ width: 36, height: 36, borderRadius: 999, background: "var(--accent)", color: "#f7f2e6", display: "grid", placeItems: "center", fontWeight: 500, flexShrink: 0 }}>
                  M
                </div>
                <div>
                  <div style={{ fontSize: 14, color: "var(--ink)" }}>Meera Bhalla</div>
                  <div style={{ fontSize: 12, color: "var(--ink-soft)" }}>Senior Care Advisor · Delhi</div>
                </div>
              </div>
              <p style={{ fontSize: 13, color: "var(--ink-soft)", margin: 0, lineHeight: 1.55 }}>
                Meera has this summary. She's already read it. Just pick up when she calls.
              </p>
              <div style={{ display: "flex", gap: 6, marginTop: 14, flexWrap: "wrap" }}>
                <button className="btn-ghost btn-hover" style={{ padding: "8px 12px", fontSize: 12.5 }}>Reschedule</button>
                <button className="btn-ghost btn-hover" style={{ padding: "8px 12px", fontSize: 12.5 }}>Add to calendar</button>
              </div>
            </div>

            {/* What we set up */}
            <div className="card" style={{ padding: 24 }}>
              <div className="mono" style={{ fontSize: 10, letterSpacing: "0.16em", color: "var(--ink-mute)", textTransform: "uppercase", marginBottom: 14 }}>
                What we've already done
              </div>
              <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 12 }}>
                <ADoneItem text={`Emailed this note to ${callerName.toLowerCase() === "friend" ? "you" : callerName}`} />
                <ADoneItem text={`Briefed Meera before Tuesday's call`} />
                <ADoneItem text={`Added a wellness check-in for ${parentName} on Friday`} />
              </ul>
            </div>

            {/* Share with family */}
            <div className="card" style={{ padding: 22, background: "transparent", border: "1px dashed var(--line)" }}>
              <div className="serif" style={{ fontSize: 17, marginBottom: 6 }}>
                Share this with your sibling?
              </div>
              <p style={{ fontSize: 13, color: "var(--ink-soft)", margin: "0 0 12px", lineHeight: 1.55 }}>
                If someone else helps with care, they should see this too.
              </p>
              <div style={{ display: "flex", gap: 6 }}>
                <button className="btn-ghost btn-hover" style={{ padding: "8px 12px", fontSize: 12.5 }}>Send via WhatsApp</button>
                <button className="btn-ghost btn-hover" style={{ padding: "8px 12px", fontSize: 12.5 }}>Send via email</button>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          display: "flex", justifyContent: "space-between", marginTop: 40, alignItems: "center",
          paddingTop: 26, borderTop: "1px solid var(--line)",
        }}>
          <button className="btn-hover" onClick={() => go("landing")}
            style={{ color: "var(--ink-mute)", fontSize: 14, padding: "10px 14px" }}>
            ← Start a new conversation
          </button>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn-ghost btn-hover" style={{ padding: "10px 16px", fontSize: 13 }}>
              Download as PDF
            </button>
            <button className="btn-ghost btn-hover" style={{ padding: "10px 16px", fontSize: 13 }}>
              Print
            </button>
          </div>
        </div>

        {/* Letter signoff */}
        <div style={{ marginTop: 36, textAlign: "center" }}>
          <div className="serif" style={{ fontSize: 18, fontStyle: "italic", color: "var(--ink-soft)" }}>
            With warmth,
          </div>
          <div className="serif" style={{ fontSize: 28, marginTop: 4, color: "var(--ink)" }}>
            Priya
          </div>
          <div className="mono" style={{ fontSize: 10, letterSpacing: "0.18em", color: "var(--ink-mute)", marginTop: 10, textTransform: "uppercase" }}>
            on behalf of the Emoha team
          </div>
        </div>
      </div>
    </div>
  );
}
function ASumLine({ label }) {
  return (
    <div style={{ display: "flex", gap: 12, alignItems: "flex-start", fontSize: 15, lineHeight: 1.5 }}>
      <span style={{ color: "var(--accent)", marginTop: 7, flexShrink: 0 }}>—</span>
      <span>{label}</span>
    </div>
  );
}
function ASumFact({ label, value }) {
  return (
    <div>
      <div className="mono" style={{ fontSize: 10, color: "var(--ink-mute)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 6 }}>
        {label}
      </div>
      <div className="serif" style={{ fontSize: 17, color: "var(--ink)", lineHeight: 1.35 }}>{value}</div>
    </div>
  );
}
function ARiskRow({ label, v, hint, inverted = false }) {
  const color = v >= 4 ? "var(--accent)" : v >= 3 ? "#8aa15e" : v >= 2 ? "#c89a3e" : "#c87456";
  const pct = (v / 5) * 100;
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
        <span style={{ fontSize: 13.5, color: "var(--ink)", fontWeight: 500 }}>{label}</span>
        <span className="mono" style={{ fontSize: 10.5, color: "var(--ink-mute)", letterSpacing: "0.08em" }}>
          {v}/5
        </span>
      </div>
      <div style={{ position: "relative", height: 5, background: "rgba(0,0,0,0.06)", borderRadius: 2 }}>
        <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${pct}%`, background: color, borderRadius: 2, transition: "width 0.7s ease" }}></div>
      </div>
      <div style={{ fontSize: 12, color: "var(--ink-mute)", marginTop: 5, lineHeight: 1.4 }}>{hint}</div>
    </div>
  );
}
function ADoneItem({ text }) {
  return (
    <li style={{ display: "flex", alignItems: "flex-start", gap: 10, fontSize: 13.5, color: "var(--ink)" }}>
      <span style={{
        width: 16, height: 16, borderRadius: 999, background: "var(--accent)", color: "#f7f2e6",
        display: "grid", placeItems: "center", fontSize: 10, flexShrink: 0, marginTop: 2,
      }}>✓</span>
      <span>{text}</span>
    </li>
  );
}
function mobLabelA(m) {
  return { full: "Independent", partial: "Some support — uses a cane", limited: "Limited — needs help most days" }[m];
}

// ---------- Emotional arc — simple SVG sparkline ----------
function EmotionalArc() {
  // Points: anxiety (start high) → guilt → fear → relief → calm
  const points = [
    { x: 0, y: 30, label: "Anxious", color: "#c87456" },
    { x: 22, y: 38, label: "Guilty", color: "#b06b56" },
    { x: 45, y: 32, label: "Worried", color: "#a87253" },
    { x: 68, y: 52, label: "Reflecting", color: "#7e8a55" },
    { x: 88, y: 68, label: "Easing", color: "#5b8b71" },
    { x: 100, y: 76, label: "Steadier", color: "#3b6a63" },
  ];
  const pathD = `M ${points.map((p) => `${p.x} ${100 - p.y}`).join(" L ")}`;
  const fillD = pathD + ` L 100 100 L 0 100 Z`;
  return (
    <div style={{ position: "relative", width: "100%" }}>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: "100%", height: 130, display: "block" }}>
        <defs>
          <linearGradient id="arc-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="rgba(59,106,99,0.18)" />
            <stop offset="1" stopColor="rgba(59,106,99,0)" />
          </linearGradient>
        </defs>
        <path d={fillD} fill="url(#arc-fill)" />
        <path d={pathD} fill="none" stroke="var(--accent)" strokeWidth="0.8" strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
        {points.map((p, i) => (
          <circle key={i} cx={p.x} cy={100 - p.y} r="1.4" fill={p.color} vectorEffect="non-scaling-stroke" />
        ))}
      </svg>
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: 130,
        pointerEvents: "none",
      }}>
        {points.filter((_, i) => i === 0 || i === points.length - 1 || i === 3).map((p, i) => (
          <span key={i} style={{
            position: "absolute",
            left: `${p.x}%`,
            top: `${100 - p.y - 8}%`,
            transform: p.x > 70 ? "translate(-100%, -100%)" : p.x > 30 ? "translate(-50%, -100%)" : "translate(0, -100%)",
            fontSize: 11, color: p.color, fontStyle: "italic",
            whiteSpace: "nowrap",
            padding: "2px 6px",
            background: "rgba(251, 248, 241, 0.85)",
            borderRadius: 4,
          }}>{p.label}</span>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { DirectionA });
