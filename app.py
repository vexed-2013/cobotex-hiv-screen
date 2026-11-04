import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="HIV Protease Docking Screen", page_icon="🧬", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 2rem;}
.hero {border: 1px solid #1f2a44; border-radius: 14px; padding: 22px 26px;
       background: linear-gradient(135deg, #0f1a33 0%, #0b1020 65%); margin-bottom: 18px;}
.hero h1 {margin: 0; font-size: 2rem; color: #E6EDF7;}
.hero p {margin: 6px 0 0 0; color: #8FA3C4; font-family: monospace;}
.card {border: 1px solid #1f2a44; border-radius: 12px; padding: 14px 18px; background: #131A2E;}
.card .label {color: #8FA3C4; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;}
.card .value {font-family: monospace; font-size: 1.7rem; color: #22D3EE;}
.card .sub {color: #8FA3C4; font-size: 0.8rem;}
.card .value.good {color: #34D399;}
.card .value.bad {color: #F87171;}
</style>
""", unsafe_allow_html=True)


def card(label, value, sub="", cls=""):
    return ('<div class="card"><div class="label">%s</div>'
            '<div class="value %s">%s</div><div class="sub">%s</div></div>'
            % (label, cls, value, sub))


@st.cache_data
def load():
    return pd.read_csv("results.csv")


df = load().copy()

# --- the rule (sliders start at the locked values) ---
st.sidebar.header("Decision rule")
score_cut = st.sidebar.slider("Vina score at or below (kcal/mol)", -12.0, -4.0, -8.0, 0.1)
contact_cut = st.sidebar.slider("Minimum Asp25 contacts", 0, 6, 4)
st.sidebar.caption("Locked rule from the development set: score <= -8.0 and contacts >= 4. "
                   "Moving the sliders shows what-if results only.")

df["verdict"] = np.where(
    (df["score"] <= score_cut) & (df["asp25_contacts"] >= contact_cut),
    "HIV-like", "not HIV-like")
df["correct"] = (df["verdict"] == "HIV-like") == (df["group"] == "HIV drug")

st.markdown(
    '<div class="hero"><h1>🧬 HIV-1 protease docking screen</h1>'
    '<p>AutoDock Vina · RDKit · Asp25 contact check · %d chemicals in 2 test sets</p></div>'
    % len(df), unsafe_allow_html=True)

# --- result cards for each dataset ---
datasets = list(df["dataset"].unique())
cols = st.columns(len(datasets))
for col, name in zip(cols, datasets):
    part = df[df["dataset"] == name]
    hiv = part[part["group"] == "HIV drug"]
    non = part[part["group"] != "HIV drug"]
    note = ("used to choose the rule" if name == "development"
            else "never used to choose the rule")
    with col:
        st.markdown("##### " + name.upper() + " SET")
        a, b, c = st.columns(3)
        a.markdown(card("Correct overall", "%d / %d" % (part["correct"].sum(), len(part)), note),
                   unsafe_allow_html=True)
        b.markdown(card("HIV drugs found", "%d / %d" % (hiv["correct"].sum(), len(hiv)),
                        "true positives",
                        "good" if hiv["correct"].all() else "bad"), unsafe_allow_html=True)
        c.markdown(card("Non-HIV rejected", "%d / %d" % (non["correct"].sum(), len(non)),
                        "true negatives",
                        "good" if non["correct"].all() else "bad"), unsafe_allow_html=True)

st.write("")
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Explore a chemical", "Table", "About and limits"])

with tab1:
    colors = {"HIV drug": "#22D3EE", "decoy": "#F59E0B", "control": "#94A3B8"}
    fig = px.scatter(
        df, x="score", y="asp25_contacts", color="group", symbol="dataset",
        hover_name="chemical", hover_data=["heavy_atoms", "asp25_min_dist", "verdict"],
        color_discrete_map=colors, template="plotly_dark",
        labels={"score": "Vina score (kcal/mol), stronger binding to the right",
                "asp25_contacts": "Contacts with Asp25 (N/O atoms within 3.5 A)"})
    fig.add_shape(type="rect", x0=score_cut, x1=-12.5, y0=contact_cut - 0.5, y1=6.7,
                  fillcolor="rgba(34,211,238,0.10)", line_width=0)
    fig.add_vline(x=score_cut, line_dash="dash", line_color="#8FA3C4")
    fig.add_hline(y=contact_cut - 0.5, line_dash="dash", line_color="#8FA3C4")
    fig.update_xaxes(range=[-4.5, -12.5])
    fig.update_yaxes(range=[-0.7, 6.7])
    fig.update_traces(marker=dict(size=14, line=dict(width=1, color="#0B1020")))
    fig.update_layout(height=540, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig)
    st.caption("The shaded zone is where a chemical is called HIV-like. "
               "Hover over a point to see which chemical it is.")

with tab2:
    pick = st.selectbox("Pick a chemical", list(df.sort_values("score")["chemical"]))
    r = df[df["chemical"] == pick].iloc[0]
    rank = int((df["score"] < r["score"]).sum()) + 1
    good = bool(r["correct"])
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(card("True group", r["group"], r["dataset"]), unsafe_allow_html=True)
    c2.markdown(card("Vina score", "%.2f" % r["score"], "rank %d of %d by score" % (rank, len(df))),
                unsafe_allow_html=True)
    c3.markdown(card("Asp25 contacts", int(r["asp25_contacts"]),
                     "closest approach %.2f A" % r["asp25_min_dist"]), unsafe_allow_html=True)
    c4.markdown(card("Rule verdict", r["verdict"], "correct call" if good else "wrong call",
                     "good" if good else "bad"), unsafe_allow_html=True)
    st.write("")
    st.markdown("- Score test (%.2f against a cutoff of %.1f): **%s**"
                % (r["score"], score_cut, "pass" if r["score"] <= score_cut else "fail"))
    st.markdown("- Contact test (%d against a minimum of %d): **%s**"
                % (r["asp25_contacts"], contact_cut,
                   "pass" if r["asp25_contacts"] >= contact_cut else "fail"))
    st.info("Open the **3D viewer** page in the sidebar to see this chemical in the protease pocket.")

with tab3:
    f1, f2 = st.columns(2)
    all_groups = sorted(df["group"].unique())
    groups_sel = f1.multiselect("Group", all_groups, default=all_groups)
    wrong_only = f2.checkbox("Show only wrong calls")
    show = df[df["group"].isin(groups_sel)]
    if wrong_only:
        show = show[~show["correct"]]
    show = show.sort_values("score")[["chemical", "group", "dataset", "heavy_atoms", "score",
                                      "asp25_min_dist", "asp25_contacts", "verdict", "correct"]]
    st.dataframe(show, hide_index=True)

with tab4:
    st.markdown("""
**How it works**
1. Each chemical's structure is fetched from PubChem and built into 3D.
2. AutoDock Vina docks it into the HIV-1 protease active site.
3. The pose is checked for contact with the catalytic Asp25 residues. A contact is a pair of
   a ligand N or O atom and an Asp25 carboxylate oxygen closer than 3.5 A.

**Validation**
- Re-docking indinavir reproduced the experimental pose within 0.93 A RMSD.
- The decision rule (score <= -8.0 and contacts >= 4) was chosen on the development set and then fixed.
- It was tested on 12 further chemicals not used to choose it: 10 of 12 correct.

**Limits**
- Small number of chemicals; one docking run each.
- Vina scores are rough estimates, not measurements of drug strength.
- Large drugs score well just by being large, which is why the contact check is needed.
- The rule missed 2 of 4 HIV drugs in the independent test (ritonavir, tipranavir), so it is strict and may miss real inhibitors.
- This is an educational screening tool, not a way to find real medicines.
""")