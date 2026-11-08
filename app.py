import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
ANIMATE = True  # set to False to switch the page-building animation off
POSES = ROOT / "poses"

st.set_page_config(page_title="HIV Protease Docking Screen", layout="wide",
                   initial_sidebar_state="collapsed")

# ---------- step state (set before drawing so the buttons can show progress) ----------
STEPS = ["Validate", "Screen", "Test", "Explore"]
if "step" not in st.session_state:
    st.session_state.step = 0


def go(d):
    st.session_state.step = min(max(st.session_state.step + d, 0), len(STEPS) - 1)


def jump(i):
    st.session_state.step = i


step = st.session_state.step
arrived = st.session_state.get("last_step") != step
st.session_state["last_step"] = step
VIEW_DELAY = 2400 if (ANIMATE and arrived) else 150

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@500;700&family=Source+Sans+3:wght@400;600;700&display=swap');
[data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stToolbar"], [data-testid="stSidebarNav"], footer {display: none !important;}
header[data-testid="stHeader"] {background: transparent;}
.block-container {padding-top: 1.5rem; max-width: 1200px;}
.stApp, .stApp p, .stApp li, .stApp label, .stApp button, .stApp input {font-family: 'Source Sans 3', sans-serif;}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .hero h1, .setname {font-family: 'Lora', serif;}

/* banner: soft sage instead of deep green */
.hero {border-radius: 16px; padding: 26px 30px; margin-bottom: 14px;
       background: linear-gradient(120deg, #EAF4EC 0%, #D9EDDF 100%); border: 1px solid #C5E0CD;}
.hero .eyebrow {color: #2F7A4E; font-size: 0.75rem; letter-spacing: 2px; font-weight: 600;}
.hero h1 {margin: 4px 0 6px 0; font-size: 2.1rem; color: #1D4D35 !important; font-weight: 700;}
.hero p {margin: 0; color: #3E6B55; font-size: 1rem;}

/* clickable step pills */
[class*="st-key-stepbtn_"] button {width: 100%; border-radius: 999px; border: none; padding: 6px 12px;
       background: #EEF3EC; color: #4B5F52; font-weight: 600;}
[class*="st-key-stepbtn_"] button p {color: inherit !important; font-weight: 600; font-size: 0.95rem;}
[class*="st-key-stepbtn_"] button:hover {background: #E2ECDF; color: #1D4D35; border: none;}
[class*="st-key-stepbtn_"] button[kind="primary"],
[class*="st-key-stepbtn_"] button[data-testid="stBaseButton-primary"] {background: #2F7A4E !important; color: #FFFFFF !important;}

@keyframes fadeUp { from {opacity: 0; transform: translateY(14px);} to {opacity: 1; transform: translateY(0);} }
.card {border: 1px solid #DCE8D6; border-left: 4px solid #16A34A; border-radius: 10px; padding: 12px 16px;
       background: #FFFFFF; margin-bottom: 8px; animation: fadeUp 0.7s ease both;}
.card.bad {border-left-color: #C2410C;}
.card .label {color: #4B5F52; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px;}
.card .value {font-size: 1.6rem; font-weight: 700; color: #14532D; line-height: 1.3;}
.card .sub {color: #4B5F52; font-size: 0.82rem;}
.card.bad .value {color: #C2410C;}
.setname {font-size: 1rem; font-weight: 700; color: #14532D; margin: 6px 0;}
.foot {color: #4B5F52; font-size: 0.8rem; margin-top: 30px; text-align: center;}
.st-key-navback, .st-key-navnext {position: fixed; bottom: 22px; z-index: 1000; width: auto !important;}
.st-key-navback {left: 24px;}
.st-key-navnext {right: 24px;}
.st-key-navback button, .st-key-navnext button {background: #FFFFFF; box-shadow: 0 4px 14px rgba(20,83,45,0.25);}
.block-container {padding-bottom: 5rem !important;}
</style>
""", unsafe_allow_html=True)

# steps already completed get a soft green pill
done_css = "".join(
    ".st-key-stepbtn_%d button {background: #CFE8D7 !important; color: #1D4D35 !important;}" % i
    for i in range(step))
st.markdown("<style>" + done_css + "</style>", unsafe_allow_html=True)
# ---------- visual layer: soft green gradient, aurora banner, glass panels, glow ----------
st.markdown("""
<style>
:root {--g1: #DDF3EA; --g2: #C9EBDD; --g3: #D4EEF0; --g4: #E6F2DF;}

/* page: a very soft sea-glass wash behind everything */
div.stApp {
  background:
    radial-gradient(900px 500px at 8% -5%, rgba(201,235,221,0.75), transparent 60%),
    radial-gradient(800px 500px at 100% 30%, rgba(212,238,240,0.65), transparent 60%),
    radial-gradient(900px 600px at 30% 105%, rgba(230,242,223,0.80), transparent 60%),
    linear-gradient(180deg, #F6FBF8 0%, #EEF7F2 100%) !important;
  background-attachment: fixed !important;
}

/* banner: slowly drifting aurora (on a pseudo-element, so the build animation can't stop it) */
@keyframes aurora {
  0%   {background-position: 0% 50%;}
  50%  {background-position: 100% 50%;}
  100% {background-position: 0% 50%;}
}
.hero {position: relative; overflow: hidden; isolation: isolate; background: none !important;
       border: 1px solid rgba(255,255,255,0.75); box-shadow: 0 6px 24px rgba(31,107,87,0.08);}
.hero::before {content: ""; position: absolute; inset: 0; z-index: -1;
       background: linear-gradient(120deg, var(--g1), var(--g2), var(--g3), var(--g4), var(--g1));
       background-size: 300% 300%; animation: aurora 26s ease-in-out infinite;}
.hero .eyebrow {color: #1F6B57;}
.hero h1 {color: #15493A !important;}
.hero p {color: #2F5F52;}

/* frosted-glass cards and step pills */
.card {background: rgba(255,255,255,0.58); border: 1px solid rgba(255,255,255,0.8);
       border-left: 4px solid #2F9E6B; box-shadow: 0 4px 18px rgba(31,107,87,0.08);
       -webkit-backdrop-filter: blur(12px); backdrop-filter: blur(12px);}
.card.bad {border-left-color: #C2410C;}
[class*="st-key-stepbtn_"] button {background: rgba(255,255,255,0.55);
       border: 1px solid rgba(255,255,255,0.8);
       -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px);}

/* soft glow on the big numbers (orange on the "wrong" cards) */
@keyframes glowGreen {
  0%, 100% {text-shadow: 0 0 0 rgba(22,163,74,0);}
  50%      {text-shadow: 0 0 14px rgba(22,163,74,0.40);}
}
@keyframes glowOrange {
  0%, 100% {text-shadow: 0 0 0 rgba(194,65,12,0);}
  50%      {text-shadow: 0 0 14px rgba(194,65,12,0.40);}
}
.card .value {animation: glowGreen 4.5s ease-in-out infinite;}
.card.bad .value {animation-name: glowOrange;}

@media (prefers-reduced-motion: reduce) {
  .hero::before, .card .value {animation: none !important;}
}
</style>
""", unsafe_allow_html=True)

# if the cursor "building" animation is switched off, fade each step in instead
if not ANIMATE:
    st.markdown("""
<style>
@keyframes stepIn {from {opacity: 0;} to {opacity: 1;}}
[data-testid="stMainBlockContainer"] [data-testid="stElementContainer"] {animation: stepIn 0.7s ease both;}
</style>
""", unsafe_allow_html=True)
# ---------- liquid-glass look: cards, step pills, round Back/Next ----------
GLASS_BASE = """
<style>
/* cards */
.card {position: relative; overflow: hidden;
       background: linear-gradient(135deg, rgba(255,255,255,0.70), rgba(255,255,255,0.28)) !important;
       -webkit-backdrop-filter: blur(18px) saturate(1.6); backdrop-filter: blur(18px) saturate(1.6);
       border: 1px solid rgba(255,255,255,0.80); border-left: 4px solid #2F9E6B;
       box-shadow: inset 0 1px 0 rgba(255,255,255,0.95), inset 0 -1px 0 rgba(255,255,255,0.30),
                   0 10px 28px rgba(31,107,87,0.13);}
.card.bad {border-left-color: #C2410C;}
.card::before {content: ""; position: absolute; left: 0; right: 0; top: 0; height: 50%;
       background: linear-gradient(180deg, rgba(255,255,255,0.55), rgba(255,255,255,0));
       pointer-events: none;}
.card > div {position: relative; z-index: 1;}

/* step pills: glass capsules */
div[class*="st-key-stepbtn_"] button {position: relative; overflow: hidden;
       border-radius: 999px !important; color: #2F5F52 !important;
       background: linear-gradient(135deg, rgba(255,255,255,0.72), rgba(255,255,255,0.30)) !important;
       -webkit-backdrop-filter: blur(16px) saturate(1.6); backdrop-filter: blur(16px) saturate(1.6);
       border: 1px solid rgba(255,255,255,0.85) !important;
       box-shadow: inset 0 1px 0 rgba(255,255,255,0.95), inset 0 -1px 0 rgba(255,255,255,0.30),
                   0 6px 18px rgba(31,107,87,0.14) !important;
       transition: transform 0.2s ease, box-shadow 0.2s ease;}
div[class*="st-key-stepbtn_"] button:hover {transform: translateY(-1px);
       box-shadow: inset 0 1px 0 rgba(255,255,255,0.95), inset 0 -1px 0 rgba(255,255,255,0.30),
                   0 10px 24px rgba(31,107,87,0.22) !important;}
div[class*="st-key-stepbtn_"] button p {position: relative; z-index: 1;}

/* round Back / Next buttons */
div.st-key-navback button, div.st-key-navnext button {position: relative; overflow: hidden;
       width: 58px !important; height: 58px !important; min-height: 0 !important; padding: 0 !important;
       border-radius: 50% !important; color: #1D4D35 !important;
       background: linear-gradient(135deg, rgba(255,255,255,0.78), rgba(255,255,255,0.30)) !important;
       -webkit-backdrop-filter: blur(18px) saturate(1.6); backdrop-filter: blur(18px) saturate(1.6);
       border: 1px solid rgba(255,255,255,0.90) !important;
       box-shadow: inset 0 1px 0 rgba(255,255,255,0.95), inset 0 -1px 0 rgba(255,255,255,0.30),
                   0 10px 26px rgba(31,107,87,0.25) !important;
       transition: transform 0.2s ease;}
div.st-key-navback button:hover, div.st-key-navnext button:hover {transform: scale(1.06);}
div.st-key-navback button:disabled, div.st-key-navnext button:disabled {
       color: rgba(29,77,53,0.35) !important; box-shadow: none !important;}
div.st-key-navback button p, div.st-key-navnext button p {position: relative; z-index: 1;
       font-size: 1.7rem !important; line-height: 1 !important; margin: 0; color: inherit !important;}

/* glossy highlight along the top edge of every glass button */
div[class*="st-key-stepbtn_"] button::before, div.st-key-navback button::before,
div.st-key-navnext button::before {content: ""; position: absolute; left: 8%; right: 8%; top: 0;
       height: 52%; border-radius: 999px; pointer-events: none;
       background: linear-gradient(180deg, rgba(255,255,255,0.60), rgba(255,255,255,0));}

@supports not ((backdrop-filter: blur(4px)) or (-webkit-backdrop-filter: blur(4px))) {
  .card {background: rgba(255,255,255,0.88) !important;}
}
@media (prefers-reduced-motion: reduce) {
  div[class*="st-key-stepbtn_"] button, div.st-key-navback button, div.st-key-navnext button
      {transition: none !important;}
}
"""

# finished steps: green-tinted glass (written after the base rules so they take priority)
GLASS_DONE = "".join(
    "div.st-key-stepbtn_" + str(i) + " button, div.st-key-stepbtn_" + str(i) + " button:hover "
    "{background: linear-gradient(135deg, rgba(190,232,206,0.85), rgba(150,215,180,0.42)) !important; "
    "color: #15493A !important;}"
    for i in range(step))

# the current step: stronger green glass
GLASS_ACTIVE = """
div[class*="st-key-stepbtn_"] button[kind="primary"],
div[class*="st-key-stepbtn_"] button[data-testid="stBaseButton-primary"],
div[class*="st-key-stepbtn_"] button[kind="primary"]:hover,
div[class*="st-key-stepbtn_"] button[data-testid="stBaseButton-primary"]:hover {
       background: linear-gradient(135deg, rgba(52,170,114,0.92), rgba(24,110,80,0.72)) !important;
       color: #FFFFFF !important; border: 1px solid rgba(255,255,255,0.55) !important;
       box-shadow: inset 0 1px 0 rgba(255,255,255,0.55), 0 8px 22px rgba(31,107,87,0.35) !important;}
</style>
"""
st.markdown(GLASS_BASE + GLASS_DONE + GLASS_ACTIVE, unsafe_allow_html=True)

# ---------- layout sizes for cards (used by the new layouts) ----------
st.markdown("""
<style>
.card.big {padding: 22px 26px;}
.card.big .label {font-size: 0.8rem;}
.card.big .value {font-size: 3.2rem; line-height: 1.15;}
.card.big .sub {font-size: 0.95rem;}
.card.small .value {font-size: 1.3rem;}
.card.low {margin-top: 34px;}
@media (max-width: 800px) {.card.low {margin-top: 0;}}
</style>
""", unsafe_allow_html=True)
# ---------- DNA helix background ----------
HELIX_STYLE = "B"   # "A" = CSS 3D helix, "B" = canvas helix, "off" = none


def card(label, value, sub="", bad=False, delay=0.0, size=""):
    return ('<div class="card%s%s" style="animation-delay:%.2fs"><div class="label">%s</div>'
            '<div class="value">%s</div><div class="sub">%s</div></div>'
            % (" bad" if bad else "", (" " + size) if size else "", delay, label, value, sub))


@st.cache_data
def load():
    return pd.read_csv(ROOT / "results.csv")


df = load().copy()

# the locked rule, used for the Screen and Test steps
df["verdict"] = np.where((df["score"] <= -8.0) & (df["asp25_contacts"] >= 4), "HIV-like", "not HIV-like")
df["correct"] = (df["verdict"] == "HIV-like") == (df["group"] == "HIV drug")

# ---------- header and navigation ----------
st.markdown(
    '<div class="hero"><div class="eyebrow">STRUCTURE-BASED VIRTUAL SCREENING</div>'
    '<h1>HIV-1 Protease Docking Screen</h1>'
    '<p>AutoDock Vina · RDKit · catalytic Asp25 contact check · %d chemicals in two test sets</p></div>' % len(df),
    unsafe_allow_html=True)

# click any step directly ...
pill_cols = st.columns(len(STEPS))
for i, name in enumerate(STEPS):
    label = ("✓ " if i < step else "") + "%d · %s" % (i + 1, name)
    pill_cols[i].button(label, key="stepbtn_%d" % i, on_click=jump, args=(i,),
                        type="primary" if i == step else "secondary")

# ... or use Back / Next
n1, n2, n3 = st.columns([1, 4, 1])
n1.button("←", key="navback", help="Back", on_click=go, args=(-1,), disabled=(step == 0))
n3.button("→", key="navnext", help="Next", on_click=go, args=(1,), disabled=(step == len(STEPS) - 1))


def set_cards(name):
    part = df[df["dataset"] == name]
    hiv = part[part["group"] == "HIV drug"]
    non = part[part["group"] != "HIV drug"]
    note = ("used to choose the rule" if name == "development" else "never used to choose the rule")
    a, b, c = st.columns(3)
    a.markdown(card("Correct overall", "%d / %d" % (part["correct"].sum(), len(part)), note),
               unsafe_allow_html=True)
    b.markdown(card("HIV drugs found", "%d / %d" % (hiv["correct"].sum(), len(hiv)), "true positives",
                    bad=not hiv["correct"].all(), delay=0.25), unsafe_allow_html=True)
    c.markdown(card("Non-HIV rejected", "%d / %d" % (non["correct"].sum(), len(non)), "true negatives",
                    bad=not non["correct"].all(), delay=0.5), unsafe_allow_html=True)


# ---------- 3D viewer ----------
ELEMENT = {"OA": "O", "NA": "N", "HD": "H", "A": "C", "SA": "S"}


def ligand_as_pdb(path):
    out = []
    for line in path.read_text().splitlines():
        if line.startswith("ENDMDL"):
            break
        if line.startswith(("ATOM", "HETATM")):
            t = line.split()[-1]
            el = ELEMENT.get(t, t)
            out.append("HETATM" + line[6:54] + " 1.00 0.00" + " " * 10 + el.rjust(2))
    return "\n".join(out) + "\nEND\n"


TEMPLATE = """
<div id="v" style="width:100%;height:450px;position:relative;border-radius:12px;overflow:hidden;background:#0F2A1B;">
  <div id="ph" style="position:absolute;left:0;top:0;right:0;bottom:0;display:flex;align-items:center;justify-content:center;color:#BEF264;font-family:system-ui,sans-serif;font-size:14px;">Loading 3D view...</div>
</div>
<script src="https://cdn.jsdelivr.net/npm/3dmol@2.4.2/build/3Dmol-min.js"></script>
<script>
// the heavy setup waits, so it does not compete with the page-building animation
setTimeout(function () {
  document.getElementById("ph").remove();
  const viewer = $3Dmol.createViewer("v", {backgroundColor: "#0F2A1B", cartoonQuality: 3,
                                           antialias: (window.devicePixelRatio || 1) < 1.5});
  viewer.addModel(__PROT__, "pdbqt");
  viewer.addModel(__LIG__, "pdb");
  viewer.setStyle({model: 0}, {cartoon: {color: "#9DBF93"}});
  viewer.addStyle({model: 0, within: {distance: 5, sel: {model: 1}}}, {line: {color: "#8FB38A"}});
  viewer.addStyle({model: 0, resn: "ASP", resi: 25}, {stick: {color: "#F59E0B", radius: 0.25}});
  viewer.setStyle({model: 1}, {stick: {colorscheme: "greenCarbon", radius: 0.3}});
  viewer.zoomTo({model: 1});
  viewer.render();

  // slow spin at about 15 frames a second; pauses when off-screen or in a hidden tab
  const el = document.getElementById("v");
  let spinning = true, onScreen = true, idle = null;
  const IDLE_MS = 60000;
  if (window.IntersectionObserver) {
    new IntersectionObserver(function (e) { onScreen = e[0].isIntersecting; }).observe(el);
  }
  setInterval(function () {
    if (spinning && onScreen && !document.hidden) { viewer.rotate(2, "y"); }
  }, 66);
  function touched() {
    spinning = false; clearTimeout(idle);
    idle = setTimeout(function () { spinning = true; }, IDLE_MS);
  }
  ["mousedown", "mouseup", "touchstart", "touchend", "wheel"].forEach(function (e) {
    el.addEventListener(e, touched, {passive: true});
  });
}, __DELAY__);
</script>
"""


@st.cache_data
def protein_text(path):
    # heavy atoms only: hydrogens are not needed for the ribbon view
    keep = [l for l in Path(path).read_text().splitlines()
            if l.startswith(("ATOM", "HETATM")) and l.split()[-1] != "HD"]
    return "\n".join(keep) + "\n"


@st.cache_data
def viewer_html(name, delay):
    lig_path = POSES / ("docked.pdbqt" if name == "indinavir" else name + "_docked.pdbqt")
    return (TEMPLATE
            .replace("__PROT__", json.dumps(protein_text(str(POSES / "protein.pdbqt"))))
            .replace("__LIG__", json.dumps(ligand_as_pdb(lig_path)))
            .replace("__DELAY__", str(int(delay))))


def show_viewer(name):
    prot_path = POSES / "protein.pdbqt"
    lig_path = POSES / ("docked.pdbqt" if name == "indinavir" else name + "_docked.pdbqt")
    if not prot_path.exists() or not lig_path.exists():
        st.warning("Pose file not found for " + name)
        return
    components.html(viewer_html(name, VIEW_DELAY), height=460)
    st.caption("Ribbon: protease. Amber sticks: catalytic Asp25. Green: docked drug. "
               "It spins until you touch it, then starts again after a minute of inactivity. "
               "Drag to rotate, scroll to zoom.")


# ---------- step 1: validate ----------
if step == 0:
    st.markdown("### Step 1: Does the pipeline find a known answer?")
    a, b, c = st.columns([1.6, 1, 1])
    a.markdown(card("Re-dock RMSD", "0.93 Å", "indinavir vs the experimental pose", size="big"), unsafe_allow_html=True)
    b.markdown(card("Success threshold", "&lt; 2 Å", "standard cutoff", delay=0.25, size="small"), unsafe_allow_html=True)
    c.markdown(card("Outcome", "Validated", "pose reproduced", delay=0.5, size="small low"), unsafe_allow_html=True)
    text_col, _spare = st.columns([1.5, 1])
    with text_col:
        st.markdown("""
Before trusting the tool on unknown chemicals, it has to find a known answer. Indinavir was taken out of
the protein, placed in a random shape, and docked back into the HIV-1 protease pocket. Vina put it back
within 0.93 Å of where the real experiment found it, well under the 2 Å limit.

This is the easiest test, because the answer is already known. It shows that the pipeline works, but not
yet that it can tell HIV drugs from other chemicals. That is the next step.
""")


# ---------- step 2: screen ----------
elif step == 1:
    st.markdown("### Step 2: Can it separate drugs from non-drugs?")
    st.markdown('<div class="setname">Development set: 14 chemicals</div>', unsafe_allow_html=True)
    part = df[df["dataset"] == "development"]
    hiv = part[part["group"] == "HIV drug"]
    non = part[part["group"] != "HIV drug"]
    a, b, c = st.columns([1, 1, 1.7])
    a.markdown(card("HIV drugs found", "%d / %d" % (hiv["correct"].sum(), len(hiv)), "true positives",
                    bad=not hiv["correct"].all(), size="small"), unsafe_allow_html=True)
    b.markdown(card("Non-HIV rejected", "%d / %d" % (non["correct"].sum(), len(non)), "true negatives",
                    bad=not non["correct"].all(), delay=0.25, size="small low"), unsafe_allow_html=True)
    c.markdown(card("Correct overall", "%d / %d" % (part["correct"].sum(), len(part)),
                    "used to choose the rule", delay=0.5, size="big"), unsafe_allow_html=True)
    text_col, chart_col = st.columns([1, 2.2])
    with text_col:
        st.markdown("""
Score alone is not enough: large non-HIV drugs such as imatinib score better than amprenavir, because big
molecules touch more of the protein. The contact check fixes this. HIV drugs reach the catalytic Asp25
residues, and the decoys do not.

The shaded zone is the rule that was chosen here and then locked: **score ≤ -8.0 and Asp25 contacts ≥ 4.**
""")
    with chart_col:
        dev = df[df["dataset"] == "development"]
        colors = {"HIV drug": "#16A34A", "decoy": "#B45309", "control": "#64748B"}
        fig = px.scatter(
            dev, x="score", y="asp25_contacts", color="group", hover_name="chemical",
            hover_data=["heavy_atoms", "asp25_min_dist", "verdict"],
            color_discrete_map=colors, template="plotly_white",
            labels={"score": "Vina score (kcal/mol), stronger binding to the right",
                    "asp25_contacts": "Contacts with Asp25 (N/O atoms within 3.5 Å)"})
        fig.add_shape(type="rect", x0=-8.0, x1=-12.5, y0=3.5, y1=6.7,
                      fillcolor="rgba(132,204,22,0.18)", line_width=0)
        fig.add_vline(x=-8.0, line_dash="dash", line_color="#4B5F52")
        fig.add_hline(y=3.5, line_dash="dash", line_color="#4B5F52")
        fig.update_xaxes(range=[-4.5, -12.5])
        fig.update_yaxes(range=[-0.7, 6.7])
        fig.update_traces(marker=dict(size=14, line=dict(width=1, color="#FFFFFF")))
        fig.update_layout(height=460, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig)

# ---------- step 3: test ----------
elif step == 2:
    st.markdown("### Step 3: Does the rule hold on chemicals it has never seen?")
    st.markdown('<div class="setname">Independent test set: 12 chemicals</div>', unsafe_allow_html=True)
    set_cards("independent test")
    ind = df[df["dataset"] == "independent test"].sort_values("score")
    st.dataframe(ind[["chemical", "group", "heavy_atoms", "score", "asp25_min_dist",
                      "asp25_contacts", "verdict", "correct"]], hide_index=True)
    st.markdown("""
**Limits**
- Small number of chemicals; one docking run each.
- Vina scores are rough estimates, not measurements of drug strength.
- The rule missed 2 of 4 HIV drugs (ritonavir, tipranavir), so it is strict and may miss real inhibitors.
- It rejected all 8 non-HIV chemicals, with no false alarms.
- This is an educational screening tool, not a way to find real medicines.
""")

# ---------- step 4: explore ----------
else:
    st.markdown("### Step 4: Explore any chemical")
    s1, s2 = st.columns(2)
    score_cut = s1.slider("Vina score at or below (kcal/mol)", -12.0, -4.0, -8.0, 0.1)
    contact_cut = s2.slider("Minimum Asp25 contacts", 0, 6, 4)
    wi = (df["score"] <= score_cut) & (df["asp25_contacts"] >= contact_cut)
    wi_ok = wi == (df["group"] == "HIV drug")
    is_dev = df["dataset"] == "development"
    st.caption("What-if with these sliders: development %d / %d correct, independent test %d / %d "
               "correct. The locked rule is score ≤ -8.0 and contacts ≥ 4."
               % (wi_ok[is_dev].sum(), is_dev.sum(), wi_ok[~is_dev].sum(), (~is_dev).sum()))

    names = list(df.sort_values("score")["chemical"])
    default = names.index("lopinavir") if "lopinavir" in names else 0
    pick = st.selectbox("Select a chemical", names, index=default)
    r = df[df["chemical"] == pick].iloc[0]
    rank = int((df["score"] < r["score"]).sum()) + 1
    hit = bool(r["score"] <= score_cut and r["asp25_contacts"] >= contact_cut)
    good = hit == (r["group"] == "HIV drug")

    left, right = st.columns([1, 1.5])
    with left:
        a, b = st.columns(2)
        a.markdown(card("True group", r["group"], r["dataset"]), unsafe_allow_html=True)
        b.markdown(card("Vina score", "%.2f" % r["score"], "rank %d of %d" % (rank, len(df)), delay=0.2),
                   unsafe_allow_html=True)
        c, d = st.columns(2)
        c.markdown(card("Asp25 contacts", int(r["asp25_contacts"]),
                        "closest approach %.2f Å" % r["asp25_min_dist"], delay=0.4), unsafe_allow_html=True)
        d.markdown(card("Rule verdict", "HIV-like" if hit else "not HIV-like",
                        "correct call" if good else "wrong call", bad=not good, delay=0.6),
                   unsafe_allow_html=True)
        st.markdown("**Score test:** %.2f against a cutoff of %.1f, **%s**"
                    % (r["score"], score_cut, "pass" if r["score"] <= score_cut else "fail"))
        st.markdown("**Contact test:** %d against a minimum of %d, **%s**"
                    % (r["asp25_contacts"], contact_cut, "pass" if r["asp25_contacts"] >= contact_cut else "fail"))
    with right:
        show_viewer(pick)

st.markdown('<div class="foot">Educational project · Docking scores are estimates, '
            'not measurements of drug strength</div>', unsafe_allow_html=True)

# ---------- building animation: cursors place each block on the page, from the top ----------
ANIM = """
<script>
// step __STEP__
(function () {
  var items = [];
  var restorePos = false, scEl = null;
  function showAll() {
    items.forEach(function (it) {
      it.el.style.opacity = "1";
      if (it.parts) it.parts.forEach(function (p) { p.node.textContent = p.text; });
    });
  }
  try {
    var P = window.parent, D = P.document;
    if (P.matchMedia && P.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    var FULL = "__FULL__" === "1", STEP = parseInt("__STEP__", 10);
    var run = (P.__buildRun = (P.__buildRun || 0) + 1);
    var old = D.getElementById("agent-layer"); if (old) old.remove();
    var main = D.querySelector('[data-testid="stMainBlockContainer"]') || D.querySelector(".block-container");
    var vb = main && main.querySelector('[data-testid="stVerticalBlock"]');
    if (!vb) return;
    var me = window.frameElement;

    // ---- 0. find the box that scrolls, so the cursors can live inside it and scroll with the page ----
    function findScroller(start) {
      var e = start, first = null;
      while (e && e !== D.body && e !== D.documentElement) {
        var oy = P.getComputedStyle(e).overflowY;
        if (oy === "auto" || oy === "scroll" || oy === "overlay") {
          if (e.scrollHeight > e.clientHeight + 1) return e;
          if (!first) first = e;
        }
        e = e.parentElement;
      }
      return first;
    }
    var sc = findScroller(main), isDoc = !sc;
    if (isDoc) sc = D.scrollingElement || D.documentElement;
    // where the top-left corner of the whole page sits on the screen right now
    function origin() {
      if (isDoc) return {x: -(P.pageXOffset || 0), y: -(P.pageYOffset || 0)};
      var q = sc.getBoundingClientRect();
      return {x: q.left + sc.clientLeft - sc.scrollLeft, y: q.top + sc.clientTop - sc.scrollTop};
    }

    // ---- 1. find the pieces of the page, in order from the top ----
    function add(kind, el, x) {
      var it = {kind: kind, el: el, parts: null, first: false};
      for (var k in x) it[k] = x[k];
      items.push(it);
    }
    Array.prototype.forEach.call(vb.children, function (ch) {
      if (me && ch.contains(me)) return;
      var hero = ch.querySelector(".hero");
      var chrome = hero || ch.querySelector("[class*='st-key-stepbtn_'], [class*='st-key-nav']");
      if (chrome && !FULL) return;
      var cards = ch.querySelectorAll(".card");
      if (hero) {
        var parts = [];
        hero.querySelectorAll(".eyebrow, h1, p").forEach(function (n) {
          var p = {node: n, text: n.textContent, a: D.createTextNode(""), s: D.createElement("span")};
          p.s.style.opacity = "0"; p.s.textContent = p.text;
          n.textContent = ""; n.appendChild(p.a); n.appendChild(p.s);
          parts.push(p);
        });
        add("hero", hero, {parts: parts, first: true});
      } else if (chrome) {
        ch.querySelectorAll("button").forEach(function (b) { add("tap", b, {first: true}); });
      } else if (cards.length) {
        cards.forEach(function (c) { add("box", c); });
        ch.querySelectorAll("iframe").forEach(function (f) { if (f !== me) add("box", f); });
      } else if (ch.querySelector('[data-testid="stPlotlyChart"], [data-testid="stDataFrame"], iframe')) {
        add("box", ch, {stretch: true, deep: "canvas, svg, iframe, [data-testid='stDataFrameResizable'], [data-testid='stDataFrame'], .js-plotly-plot, .plot-container, .svg-container"});
      } else if (ch.querySelector("h3, .setname")) {
        add("wipe", ch);
      } else if (ch.querySelector('[data-testid="stSlider"], [data-testid="stSelectbox"]')) {
        add("tap", ch);
      } else if (ch.querySelector(".foot")) {
        add("fade", ch);
      } else if (ch.querySelectorAll("p, li").length) {
        ch.querySelectorAll("p, li").forEach(function (n) {
          if (!(n.tagName === "P" && n.closest("li"))) add("line", n);
        });
      } else { add("fade", ch); }
    });
    items.forEach(function (it) { it.el.style.animation = "none"; it.el.style.opacity = "0"; });

    // ---- 2. measure in PAGE coordinates (they do not change when you scroll) ----
    var W = P.innerWidth, H = P.innerHeight;
    var O0 = origin();
    // the part of the page you can see right now: cursors only work inside it
    var win = {left: -O0.x + 6, top: -O0.y + 6, right: -O0.x + W - 6, bottom: -O0.y + H - 6};
    function textRect(el) {
      var g = D.createRange(); g.selectNodeContents(el);
      var q = g.getBoundingClientRect();
      return q.width > 0 ? q : el.getBoundingClientRect();
    }
    function fullRect(it) {
      var r = it.el.getBoundingClientRect();
      var L = r.left, T = r.top, R = r.right, B = r.bottom;
      if (it.deep) {
        it.el.querySelectorAll(it.deep).forEach(function (n) {
          var q = n.getBoundingClientRect();
          if (q.width > 0 && q.height > 0) {
            L = Math.min(L, q.left); T = Math.min(T, q.top); R = Math.max(R, q.right); B = Math.max(B, q.bottom);
          }
        });
      }
      if (it.stretch) { var vr = vb.getBoundingClientRect(); L = vr.left; R = vr.right; }
      return {left: L, top: T, right: R, bottom: B, width: R - L, height: B - T};
    }
    function rectOf(it) {
      return it.kind === "line" ? textRect(it.el)
           : it.kind === "wipe" ? textRect(it.el.querySelector("h3, .setname") || it.el)
           : fullRect(it);
    }
    // read where a piece is RIGHT NOW (called again just before every move)
    function fresh(it) {
      var o = origin(), r = rectOf(it);
      var V = {left: Math.max(r.left - o.x, win.left), top: Math.max(r.top - o.y, win.top),
               right: Math.min(r.right - o.x, win.right), bottom: Math.min(r.bottom - o.y, win.bottom)};
      if (V.right < V.left) V.right = V.left;
      if (V.bottom < V.top) V.bottom = V.top;
      it.V = V; return V;
    }
    items.forEach(function (it) {
      var r = rectOf(it);
      it.r = r; it.area = r.width * r.height;
      it.vis = r.width > 0 && r.bottom > 6 && r.top < H - 6;
      fresh(it);
    });

    // ---- 3. one choreography per screen ----
    var CFG = [
      {from: "L", corner: 0, lanes: 6, mode: 0},   // Validate: from the left, document order
      {from: "R", corner: 1, lanes: 4, mode: 1},   // Screen: from the right, biggest blocks first
      {from: "B", corner: 2, lanes: 5, mode: 2},   // Test: from the bottom, text builds bottom-up
      {from: "T", corner: 3, lanes: 6, mode: 3}    // Explore: from the top, right column first
    ][STEP] || {from: "L", corner: 0, lanes: 5, mode: 0};
    var fixed = items.filter(function (i) { return i.first; });
    var rest = items.filter(function (i) { return !i.first; });
    var wp = rest.filter(function (i) { return i.kind === "wipe"; });
    var bx = rest.filter(function (i) { return i.kind === "box"; });
    var ot = rest.filter(function (i) { return i.kind !== "wipe" && i.kind !== "box"; });
    if (CFG.mode === 1) bx.sort(function (a, b) { return b.area - a.area; });
    if (CFG.mode === 2) ot.reverse();
    if (CFG.mode === 3) bx.sort(function (a, b) { return b.r.left - a.r.left; });
    var order = fixed.concat(CFG.mode === 0 ? rest : wp.concat(bx, ot));

    // ---- 4. cursor layer (lives INSIDE the scrolling page) and effect helpers ----
    var layer = D.createElement("div"); layer.id = "agent-layer";
    var host = isDoc ? D.body : sc;
    if (!isDoc && P.getComputedStyle(sc).position === "static") { sc.style.position = "relative"; restorePos = true; scEl = sc; }
    layer.style.cssText = "position:absolute;left:0;top:0;width:" + sc.scrollWidth + "px;height:" + sc.scrollHeight + "px;pointer-events:none;z-index:99999;overflow:hidden";
    host.appendChild(layer);
    function cleanup() {
      var l = D.getElementById("agent-layer"); if (l) l.remove();
      if (restorePos && scEl) { scEl.style.position = ""; restorePos = false; }
    }
    P.setTimeout(function () { if (run === P.__buildRun) { showAll(); cleanup(); } }, 12000);

    var COLORS = ["#F97316", "#22D3EE", "#A78BFA", "#FACC15", "#F472B6", "#60A5FA"];
    var ARROW = '<svg width="22" height="22" viewBox="0 0 24 24"><path d="M3 2l18 8-8 3-3 8z" fill="COL" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>';
    var X0 = -O0.x, Y0 = -O0.y;   // top-left of what you can see, in page coordinates
    var cur = COLORS.slice(0, CFG.lanes).map(function (col, i) {
      var f = (i + 1) / (CFG.lanes + 1), c = D.createElement("div");
      var x = CFG.from === "L" ? X0 - 30 : CFG.from === "R" ? X0 + W + 30 : X0 + W * f;
      var y = CFG.from === "T" ? Y0 - 30 : CFG.from === "B" ? Y0 + H + 30 : Y0 + H * f;
      c.style.cssText = "position:absolute;left:-3px;top:-2px;transform:translate(" + x + "px," + y + "px)";
      c.innerHTML = ARROW.replace("COL", col); layer.appendChild(c);
      return {el: c, x: x, y: y};
    });
    var EASE = "cubic-bezier(.45,0,.2,1)";
    var COLL = ["inset(-5px 100% 100% -5px)", "inset(-5px -5px 100% 100%)", "inset(100% 100% -5px -5px)", "inset(100% -5px -5px 100%)"];

    function move(L, x, y, ms) {
      var c = cur[L], tf = "translate(" + x + "px," + y + "px)";
      c.el.animate([{transform: "translate(" + c.x + "px," + c.y + "px)"}, {transform: tf}], {duration: ms, easing: EASE});
      c.x = x; c.y = y; c.el.style.transform = tf;
    }
    function pop(el, ms) {
      el.style.opacity = "1";
      var f = el.tagName === "IFRAME" ? [{opacity: 0}, {opacity: 1}] : [{opacity: 0, transform: "scale(.96)"}, {opacity: 1, transform: "none"}];
      el.animate(f, {duration: ms, easing: "ease-out"});
    }
    function wipe(el, ms, axis) {
      el.style.opacity = "1";
      el.animate([{clipPath: axis === "y" ? "inset(0 0 100% 0)" : "inset(0 100% 0 0)"}, {clipPath: "inset(0 0 0 0)"}], {duration: ms, easing: EASE});
    }
    function ripple(x, y) {
      var d = D.createElement("div");
      d.style.cssText = "position:absolute;width:28px;height:28px;border-radius:50%;border:2px solid #3B82F6;left:" + (x - 14) + "px;top:" + (y - 14) + "px";
      layer.appendChild(d);
      d.animate([{transform: "scale(.3)", opacity: 0.9}, {transform: "scale(1.4)", opacity: 0}], {duration: 380, easing: "ease-out"}).onfinish = function () { d.remove(); };
    }
    function mkBox() {
      var b = D.createElement("div");
      b.style.cssText = "position:absolute;box-sizing:border-box;border:1px solid #3B82F6;background:rgba(148,163,184,.28);left:0;top:0;width:0;height:0";
      for (var i = 0; i < 4; i++) {
        var h = D.createElement("i");
        h.style.cssText = "position:absolute;width:7px;height:7px;box-sizing:border-box;background:#fff;border:1px solid #3B82F6;" + (i % 2 ? "right" : "left") + ":-4px;" + (i < 2 ? "top" : "bottom") + ":-4px";
        b.appendChild(h);
      }
      layer.appendChild(b); return b;
    }
    function setBox(b, x1, y1, x2, y2) {
      b.style.left = Math.min(x1, x2) + "px"; b.style.top = Math.min(y1, y2) + "px";
      b.style.width = Math.abs(x2 - x1) + "px"; b.style.height = Math.abs(y2 - y1) + "px";
    }
    function ease(p) { return p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2; }
    function typeParts(parts, ms) {
      var N = parts.reduce(function (s, p) { return s + p.text.length; }, 0), t0 = P.performance.now();
      (function f(now) {
        if (run !== P.__buildRun) return;
        var n = N * Math.min(1, (now - t0) / ms);
        parts.forEach(function (p) {
          var k = Math.max(0, Math.min(p.text.length, Math.floor(n)));
          p.a.nodeValue = p.text.slice(0, k); p.s.textContent = p.text.slice(k); n -= p.text.length;
        });
        if (now - t0 < ms) P.requestAnimationFrame(f);
      })(t0);
    }
    // small geometry helpers (each takes the piece's current box V)
    function corners(V) {
      return [[V.left, V.top, V.right, V.bottom], [V.right, V.top, V.left, V.bottom],
              [V.left, V.bottom, V.right, V.top], [V.right, V.bottom, V.left, V.top]][CFG.corner];
    }
    function mid(V) { return [(V.left + V.right) / 2, (V.top + V.bottom) / 2]; }
    function lineGeo(V) {
      var tall = V.bottom - V.top > 40, my = (V.top + V.bottom) / 2;
      return {tall: tall, sx: V.left + 2, sy: tall ? V.top + 6 : my,
              ex: tall ? V.right - 8 : V.right, ey: tall ? V.bottom - 6 : my};
    }

    // ---- 5. plan every move on one clock, then play it frame by frame ----
    // The plan only decides WHEN things happen. WHERE they happen is read again at the
    // moment of each move, so the cursor and the drag box always sit on the real block.
    var evs = [], last = 0, free = cur.map(function () { return 0; });
    var pp = cur.map(function (c) { return {x: c.x, y: c.y}; });
    function at(t, fn) { evs.push({t: t, fn: fn}); }
    order.forEach(function (it) {
      var L = 0, i;
      for (i = 1; i < free.length; i++) if (free[i] < free[L]) L = i;
      var s = Math.max(free[L], last + 70), V = it.V, el = it.el, k = it.kind, from = pp[L];
      last = s;
      if (!it.vis || k === "fade") { at(s, function () { pop(el, 300); }); return; }
      if (k === "box" || k === "hero") {
        var c = corners(V);
        var tr = 200 + Math.min(240, Math.hypot(from.x - c[0], from.y - c[1]) * 0.25);
        var dr = 300 + Math.min(220, (V.right - V.left + V.bottom - V.top) * 0.18);
        at(s, function () { var q = corners(fresh(it)); move(L, q[0], q[1], tr); });
        at(s + tr, function () {
          var b = it.box = mkBox(), t0 = P.performance.now();
          (function f(now) {
            if (run !== P.__buildRun) return;
            var p = Math.max(0, Math.min(1, (now - t0) / dr)), e = ease(p), q = corners(fresh(it));
            var x = q[0] + (q[2] - q[0]) * e, y = q[1] + (q[3] - q[1]) * e, cc = cur[L];
            setBox(b, q[0], q[1], x, y);
            cc.x = x; cc.y = y; cc.el.style.transform = "translate(" + x + "px," + y + "px)";
            if (p < 1) P.requestAnimationFrame(f);
          })(t0);
        });
        at(s + tr + dr, function () {
          pop(el, 240);
          it.box.animate([{opacity: 1}, {opacity: 0}], {duration: 300, delay: 60, fill: "forwards"});
          P.setTimeout(function () { it.box.remove(); }, 450);
          if (it.parts) typeParts(it.parts, 700);
        });
        pp[L] = {x: c[2], y: c[3]};
        free[L] = s + tr + dr + (it.parts ? 700 : 80);
      } else if (k === "tap") {
        var m = mid(V);
        var t2 = 200 + Math.min(240, Math.hypot(from.x - m[0], from.y - m[1]) * 0.25);
        at(s, function () { var q = mid(fresh(it)); move(L, q[0], q[1], t2); });
        at(s + t2, function () { var q = mid(fresh(it)); ripple(q[0], q[1]); pop(el, 240); });
        pp[L] = {x: m[0], y: m[1]}; free[L] = s + t2 + 80;
      } else {
        var g = lineGeo(V);
        var t3 = 200 + Math.min(240, Math.hypot(from.x - g.sx, from.y - g.sy) * 0.25), d3 = 260 + Math.min(200, (V.right - V.left) * 0.25);
        at(s, function () { var q = lineGeo(fresh(it)); move(L, q.sx, q.sy, t3); });
        at(s + t3, function () { var q = lineGeo(fresh(it)); wipe(el, d3, q.tall ? "y" : "x"); move(L, q.ex, q.ey, d3); });
        pp[L] = {x: g.ex, y: g.ey}; free[L] = s + t3 + d3;
      }
    });
    var endT = Math.max.apply(null, free) + 150;
    at(endT, function () { cur.forEach(function (c) { c.el.animate([{opacity: 1}, {opacity: 0}], {duration: 350, fill: "forwards"}); }); });
    at(endT + 450, function () { showAll(); cleanup(); });
    evs.sort(function (a, b) { return a.t - b.t; });

    var T0 = null, idx = 0, lastSize = 0;
    (function loop(now) {
      if (run !== P.__buildRun) return;
      if (T0 === null) T0 = now;
      if (now - lastSize > 250) {   // keep the cursor layer as big as the page, even if the page grows
        lastSize = now;
        layer.style.width = sc.scrollWidth + "px"; layer.style.height = sc.scrollHeight + "px";
      }
      while (idx < evs.length && evs[idx].t <= now - T0) evs[idx++].fn();
      if (idx < evs.length) P.requestAnimationFrame(loop);
    })(P.performance.now());
  } catch (e) {
    showAll();
    try { var l = window.parent.document.getElementById("agent-layer"); if (l) l.remove(); console.warn("build animation:", e); } catch (_) {}
  }
})();
</script>
"""

if ANIMATE:
    first = not st.session_state.get("intro_played", False)
    st.session_state["intro_played"] = True
    components.html(ANIM.replace("__STEP__", str(step)).replace("__FULL__", "1" if first else "0"), height=0)
# ---------- helix option B: canvas particles ----------
HELIX_B = """
<script>
(function () {
  try {
    var P = window.parent, D = P.document;
    var run = (P.__hxRun = (P.__hxRun || 0) + 1);
    var old = D.getElementById("hx-canvas"); if (old) old.remove();
    var host = D.querySelector(".stApp") || D.body;
    var reduce = P.matchMedia && P.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!D.getElementById("hx-style")) {
      var s = D.createElement("style"); s.id = "hx-style";
      s.textContent = '[data-testid="stAppViewContainer"], [data-testid="stMain"], section.main {background: transparent !important;} [data-testid="stMainBlockContainer"] {position: relative; z-index: 1;}';
      D.head.appendChild(s);
    }
    var cv = D.createElement("canvas"); cv.id = "hx-canvas";
    cv.style.cssText = "position:fixed;left:0;top:0;pointer-events:none;z-index:0";
    host.insertBefore(cv, host.firstChild);
    var ctx = cv.getContext("2d"), W = 0, H = 0;
    var DPR = Math.min(P.devicePixelRatio || 1, 2);
    function size() {
      W = P.innerWidth; H = P.innerHeight;
      cv.width = W * DPR; cv.height = H * DPR;
      cv.style.width = W + "px"; cv.style.height = H + "px";
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    }
    size();
    function onResize() {
      if (run !== P.__hxRun) { P.removeEventListener("resize", onResize); return; }
      size();
    }
    P.addEventListener("resize", onResize);

    var COL = [[47, 158, 107], [34, 166, 179]];
    var dust = [];
    for (var k = 0; k < 40; k++) {
      dust.push({x: Math.random(), y: Math.random(), r: 1.5 + Math.random() * 3,
                 v: 0.00002 + Math.random() * 0.00004, ph: Math.random() * 6.28, c: k % 2});
    }
    function glow(x, y, r, c, a) {
      var g = ctx.createRadialGradient(x, y, 0, x, y, r);
      g.addColorStop(0, "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + a + ")");
      g.addColorStop(0.4, "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + (a * 0.55) + ")");
      g.addColorStop(1, "rgba(" + c[0] + "," + c[1] + "," + c[2] + ",0)");
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill();
    }
    var R = 78, N = 44, STEP = 26, TURN = 0.42, F = 520, PERIOD = 42000;
    function draw(t) {
      ctx.clearRect(0, 0, W, H);
      if (W < 900) return;
      var i, s, rot = reduce ? 0 : (t / PERIOD) * 6.2832;
      for (i = 0; i < dust.length; i++) {
        var d = dust[i], dy = (((d.y - t * d.v) % 1) + 1) % 1;
        glow(d.x * W, dy * H, d.r * 3, COL[d.c], 0.16 + 0.12 * Math.sin(t / 1500 + d.ph));
      }
      ctx.save(); ctx.translate(W * 0.5, H * 0.5); ctx.rotate(0.21);
      var pts = [];
      for (i = 0; i < N; i++) {
        var y = (i - N / 2) * STEP, pair = [];
        for (s = 0; s < 2; s++) {
          var a = i * TURN + s * Math.PI + rot, z = R * Math.cos(a), sc = F / (F - z);
          pair.push({x: R * Math.sin(a) * sc, y: y * sc, z: z, s: s, r: (4 + (i % 3)) * sc});
        }
        pts.push(pair);
      }
      ctx.lineWidth = 1.2; ctx.strokeStyle = "rgba(47,158,107,0.16)";
      for (i = 0; i < N; i += 2) {
        ctx.beginPath(); ctx.moveTo(pts[i][0].x, pts[i][0].y); ctx.lineTo(pts[i][1].x, pts[i][1].y); ctx.stroke();
      }
      var all = [];
      pts.forEach(function (pr) { all.push(pr[0], pr[1]); });
      all.sort(function (m, n) { return m.z - n.z; });
      all.forEach(function (q) { glow(q.x, q.y, q.r * 2.6, COL[q.s], 0.12 + 0.32 * (q.z + R) / (2 * R)); });
      ctx.restore();
    }
    var last = 0;
    function loop(now) {
      if (run !== P.__hxRun) return;
      if (!cv.isConnected) host.insertBefore(cv, host.firstChild);
      if (!D.hidden && now - last > 33) { last = now; draw(now); }
      P.requestAnimationFrame(loop);
    }
    if (reduce) { draw(0); } else { P.requestAnimationFrame(loop); }
  } catch (e) { console.warn("helix:", e); }
})();
</script>
"""

if HELIX_STYLE == "B":
    components.html(HELIX_B, height=0)
