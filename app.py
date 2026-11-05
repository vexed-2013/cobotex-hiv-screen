import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
POSES = ROOT / "poses"

st.set_page_config(page_title="HIV Protease Docking Screen", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@500;700&family=Source+Sans+3:wght@400;600;700&display=swap');

[data-testid="stSidebar"], [data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"], [data-testid="stToolbar"],
[data-testid="stSidebarNav"], footer {display: none !important;}
header[data-testid="stHeader"] {background: transparent;}
.block-container {padding-top: 1.5rem; max-width: 1200px;}

.stApp, .stApp p, .stApp li, .stApp label, .stApp button, .stApp input
    {font-family: 'Source Sans 3', sans-serif;}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .hero h1, .setname
    {font-family: 'Lora', serif;}

.hero {border-radius: 16px; padding: 26px 30px; margin-bottom: 14px;
       background: linear-gradient(120deg, #14532D 0%, #166534 55%, #16A34A 100%);}
.hero .eyebrow {color: #BEF264; font-size: 0.75rem; letter-spacing: 2px; font-weight: 600;}
.hero h1 {margin: 4px 0 6px 0; font-size: 2.1rem; color: #FFFFFF !important; font-weight: 700;}
.hero p {margin: 0; color: #DCFCE7; font-size: 1rem;}

.steps {display: flex; gap: 10px; margin: 6px 0 14px 0; flex-wrap: wrap;}
.step {flex: 1; min-width: 120px; padding: 8px 12px; border-radius: 999px; background: #E8F0E4;
       color: #4B5F52; font-weight: 600; font-size: 0.9rem; text-align: center;}
.step span {display: inline-block; width: 22px; height: 22px; line-height: 22px;
            border-radius: 50%; background: #FFFFFF; margin-right: 8px; font-size: 0.8rem;}
.step.now {background: #14532D; color: #FFFFFF;}
.step.now span {background: #84CC16; color: #14532D;}
.step.done {background: #16A34A; color: #FFFFFF;}
.step.done span {background: #FFFFFF; color: #16A34A;}

@keyframes fadeUp {
  from {opacity: 0; transform: translateY(14px);}
  to {opacity: 1; transform: translateY(0);}
}
.card {border: 1px solid #DCE8D6; border-left: 4px solid #16A34A; border-radius: 10px;
       padding: 12px 16px; background: #FFFFFF; margin-bottom: 8px;
       animation: fadeUp 0.7s ease both;}
.card.bad {border-left-color: #C2410C;}
.card .label {color: #4B5F52; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px;}
.card .value {font-size: 1.6rem; font-weight: 700; color: #14532D; line-height: 1.3;}
.card .sub {color: #4B5F52; font-size: 0.82rem;}
.card.bad .value {color: #C2410C;}
.setname {font-size: 1rem; font-weight: 700; color: #14532D; margin: 6px 0;}
.foot {color: #4B5F52; font-size: 0.8rem; margin-top: 30px; text-align: center;}
</style>
""", unsafe_allow_html=True)


def card(label, value, sub="", bad=False, delay=0.0):
    return ('<div class="card%s" style="animation-delay:%.2fs"><div class="label">%s</div>'
            '<div class="value">%s</div><div class="sub">%s</div></div>'
            % (" bad" if bad else "", delay, label, value, sub))


@st.cache_data
def load():
    return pd.read_csv(ROOT / "results.csv")


df = load().copy()

# the locked rule, used for the Screen and Test steps
df["verdict"] = np.where((df["score"] <= -8.0) & (df["asp25_contacts"] >= 4),
                         "HIV-like", "not HIV-like")
df["correct"] = (df["verdict"] == "HIV-like") == (df["group"] == "HIV drug")

# ---------- step navigation ----------
STEPS = ["Validate", "Screen", "Test", "Explore"]
if "step" not in st.session_state:
    st.session_state.step = 0


def go(d):
    st.session_state.step = min(max(st.session_state.step + d, 0), len(STEPS) - 1)


step = st.session_state.step

st.markdown(
    '<div class="hero"><div class="eyebrow">STRUCTURE-BASED VIRTUAL SCREENING</div>'
    '<h1>HIV-1 Protease Docking Screen</h1>'
    '<p>AutoDock Vina · RDKit · catalytic Asp25 contact check · %d chemicals in two test sets</p></div>'
    % len(df), unsafe_allow_html=True)

html = '<div class="steps">'
for i, s in enumerate(STEPS):
    cls = "done" if i < step else ("now" if i == step else "")
    html += '<div class="step %s"><span>%d</span>%s</div>' % (cls, i + 1, s)
html += "</div>"
st.markdown(html, unsafe_allow_html=True)

n1, n2, n3 = st.columns([1, 4, 1])
n1.button("← Back", on_click=go, args=(-1,), disabled=(step == 0))
n3.button("Next →", on_click=go, args=(1,), disabled=(step == len(STEPS) - 1))


def set_cards(name):
    part = df[df["dataset"] == name]
    hiv = part[part["group"] == "HIV drug"]
    non = part[part["group"] != "HIV drug"]
    note = ("used to choose the rule" if name == "development"
            else "never used to choose the rule")
    a, b, c = st.columns(3)
    a.markdown(card("Correct overall", "%d / %d" % (part["correct"].sum(), len(part)), note),
               unsafe_allow_html=True)
    b.markdown(card("HIV drugs found", "%d / %d" % (hiv["correct"].sum(), len(hiv)),
                    "true positives", bad=not hiv["correct"].all(), delay=0.25),
               unsafe_allow_html=True)
    c.markdown(card("Non-HIV rejected", "%d / %d" % (non["correct"].sum(), len(non)),
                    "true negatives", bad=not non["correct"].all(), delay=0.5),
               unsafe_allow_html=True)


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
            out.append("HETATM" + line[6:54] + "  1.00  0.00" + " " * 10 + el.rjust(2))
    return "\n".join(out) + "\nEND\n"


TEMPLATE = """
<div id="v" style="width:100%;height:520px;position:relative;border-radius:12px;overflow:hidden;"></div>
<script src="https://cdn.jsdelivr.net/npm/3dmol@2.4.2/build/3Dmol-min.js"></script>
<script>
const viewer = $3Dmol.createViewer("v", {backgroundColor: "#0F2A1B"});
viewer.addModel(__PROT__, "pdbqt");
viewer.addModel(__LIG__, "pdb");
viewer.setStyle({model: 0}, {cartoon: {color: "#BBD3B0", opacity: 0.35}});
viewer.addStyle({model: 0, within: {distance: 5, sel: {model: 1}}}, {line: {color: "#8FB38A"}});
viewer.addStyle({model: 0, resn: "ASP", resi: 25}, {stick: {color: "#F59E0B", radius: 0.25}});
viewer.setStyle({model: 1}, {stick: {colorscheme: "greenCarbon", radius: 0.3}, sphere: {colorscheme: "greenCarbon", scale: 0.3}});
viewer.zoomTo({model: 1});
viewer.render();
viewer.spin("y", 0.5);
const el = document.getElementById("v");
["mousedown", "touchstart", "wheel"].forEach(function (e) {
  el.addEventListener(e, function () { viewer.spin(false); }, {passive: true});
});
</script>
"""


def show_viewer(name):
    prot_path = POSES / "protein.pdbqt"
    lig_path = POSES / ("docked.pdbqt" if name == "indinavir" else name + "_docked.pdbqt")
    if not prot_path.exists() or not lig_path.exists():
        st.warning("Pose file not found for " + name)
        return
    page = (TEMPLATE
            .replace("__PROT__", json.dumps(prot_path.read_text()))
            .replace("__LIG__", json.dumps(ligand_as_pdb(lig_path))))
    components.html(page, height=530)
    st.caption("Ribbon: protease. Amber sticks: catalytic Asp25. Green: docked drug. "
               "It spins until you touch it. Drag to rotate, scroll to zoom.")


# ---------- step 1: validate ----------
if step == 0:
    st.markdown("### Step 1: Does the pipeline find a known answer?")
    a, b, c = st.columns(3)
    a.markdown(card("Re-dock RMSD", "0.93 Å", "indinavir vs the experimental pose"),
               unsafe_allow_html=True)
    b.markdown(card("Success threshold", "&lt; 2 Å", "standard cutoff", delay=0.25),
               unsafe_allow_html=True)
    c.markdown(card("Outcome", "Validated", "pose reproduced", delay=0.5),
               unsafe_allow_html=True)
    st.markdown("""
Before trusting the tool on unknown chemicals, it has to find a known answer.
Indinavir was taken out of the protein, placed in a random shape, and docked back into the
HIV-1 protease pocket. Vina put it back within 0.93 Å of where the real experiment found it,
well under the 2 Å limit.

This is the easiest test, because the answer is already known. It shows that the pipeline
works, but not yet that it can tell HIV drugs from other chemicals. That is the next step.
""")

# ---------- step 2: screen ----------
elif step == 1:
    st.markdown("### Step 2: Can it separate drugs from non-drugs?")
    st.markdown('<div class="setname">Development set: 14 chemicals</div>', unsafe_allow_html=True)
    set_cards("development")
    dev = df[df["dataset"] == "development"]
    colors = {"HIV drug": "#16A34A", "decoy": "#B45309", "control": "#64748B"}
    fig = px.scatter(
        dev, x="score", y="asp25_contacts", color="group",
        hover_name="chemical", hover_data=["heavy_atoms", "asp25_min_dist", "verdict"],
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
    st.markdown("""
Score alone is not enough: large non-HIV drugs such as imatinib score better than amprenavir,
because big molecules touch more of the protein. The contact check fixes this. HIV drugs reach
the catalytic Asp25 residues, and the decoys do not.

The shaded zone is the rule that was chosen here and then locked:
**score ≤ -8.0 and Asp25 contacts ≥ 4.**
""")

# ---------- step 3: test ----------
elif step == 2:
    st.markdown("### Step 3: Does the rule hold on chemicals it has never seen?")
    st.markdown('<div class="setname">Independent test set: 12 chemicals</div>',
                unsafe_allow_html=True)
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
        b.markdown(card("Vina score", "%.2f" % r["score"], "rank %d of %d" % (rank, len(df)),
                        delay=0.2), unsafe_allow_html=True)
        c, d = st.columns(2)
        c.markdown(card("Asp25 contacts", int(r["asp25_contacts"]),
                        "closest approach %.2f Å" % r["asp25_min_dist"], delay=0.4),
                   unsafe_allow_html=True)
        d.markdown(card("Rule verdict", "HIV-like" if hit else "not HIV-like",
                        "correct call" if good else "wrong call", bad=not good, delay=0.6),
                   unsafe_allow_html=True)
        st.markdown("**Score test:** %.2f against a cutoff of %.1f, **%s**"
                    % (r["score"], score_cut, "pass" if r["score"] <= score_cut else "fail"))
        st.markdown("**Contact test:** %d against a minimum of %d, **%s**"
                    % (r["asp25_contacts"], contact_cut,
                       "pass" if r["asp25_contacts"] >= contact_cut else "fail"))
    with right:
        show_viewer(pick)

st.markdown('<div class="foot">Educational project · Docking scores are estimates, '
            'not measurements of drug strength</div>', unsafe_allow_html=True)
