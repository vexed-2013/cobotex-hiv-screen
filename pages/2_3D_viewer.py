import json
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent.parent
POSES = ROOT / "poses"

st.set_page_config(page_title="3D pocket viewer", page_icon="🧬", layout="wide")

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


st.markdown(
    '<div class="hero"><h1>🧬 3D pocket viewer</h1>'
    '<p>Docked drug inside the HIV-1 protease active site · drag to rotate, scroll to zoom</p></div>',
    unsafe_allow_html=True)

df = pd.read_csv(ROOT / "results.csv").sort_values("score")
names = list(df["chemical"])
default = names.index("lopinavir") if "lopinavir" in names else 0
name = st.selectbox("Choose a chemical", names, index=default)
row = df[df["chemical"] == name].iloc[0]

# the locked rule
hiv_like = bool(row["score"] <= -8.0 and row["asp25_contacts"] >= 4)
correct = hiv_like == (row["group"] == "HIV drug")

c1, c2, c3, c4 = st.columns(4)
c1.markdown(card("True group", row["group"], row["dataset"]), unsafe_allow_html=True)
c2.markdown(card("Vina score", "%.2f" % row["score"], "kcal/mol"), unsafe_allow_html=True)
c3.markdown(card("Asp25 contacts", int(row["asp25_contacts"]),
                 "closest approach %.2f A" % row["asp25_min_dist"]), unsafe_allow_html=True)
c4.markdown(card("Rule verdict", "HIV-like" if hiv_like else "not HIV-like",
                 "correct call" if correct else "wrong call",
                 "good" if correct else "bad"), unsafe_allow_html=True)
st.write("")

prot_path = POSES / "protein.pdbqt"
lig_path = POSES / ("docked.pdbqt" if name == "indinavir" else name + "_docked.pdbqt")
if not prot_path.exists() or not lig_path.exists():
    st.error("Missing pose file: " + str(lig_path if prot_path.exists() else prot_path))
    st.stop()

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
<div id="v" style="width:100%;height:600px;position:relative;"></div>
<script src="https://cdn.jsdelivr.net/npm/3dmol@2.4.2/build/3Dmol-min.js"></script>
<script>
const viewer = $3Dmol.createViewer("v", {backgroundColor: "#0B1020"});
viewer.addModel(__PROT__, "pdbqt");
viewer.addModel(__LIG__, "pdb");
viewer.setStyle({model: 0}, {cartoon: {color: "lightgrey", opacity: 0.4}});
viewer.addStyle({model: 0, within: {distance: 5, sel: {model: 1}}}, {line: {color: "#8FA3C4"}});
viewer.addStyle({model: 0, resn: "ASP", resi: 25}, {stick: {color: "orange", radius: 0.25}});
viewer.setStyle({model: 1}, {stick: {colorscheme: "greenCarbon", radius: 0.3}});
viewer.zoomTo({model: 1});
viewer.render();
</script>
"""

html = (TEMPLATE
        .replace("__PROT__", json.dumps(prot_path.read_text()))
        .replace("__LIG__", json.dumps(ligand_as_pdb(lig_path))))
components.html(html, height=620)

st.caption("Grey ribbon: protein. Orange sticks: catalytic Asp25 residues. "
           "Green sticks: the docked drug. Thin lines: protein residues within 5 A of the drug. "
           "Drag to rotate, scroll to zoom.")