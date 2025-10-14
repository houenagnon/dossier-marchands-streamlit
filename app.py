import os
import pandas as pd
from reportlab.pdfgen import canvas
import shutil
import streamlit as st
from tempfile import TemporaryDirectory

# --- FONCTIONS UTILITAIRES ---

def clean_id(value):
    """Nettoie les valeurs d'ID (supprime .0 et garde des chaînes propres)."""
    if pd.isna(value):
        return ""
    val = str(value).strip()
    # Supprimer les .0 typiques d'une conversion float
    if val.endswith(".0"):
        val = val[:-2]
    return val

def create_pdf(path: str):
    """Crée un PDF vide."""
    c = canvas.Canvas(path)
    c.save()

def create_structure_personne_physique(base_dir: str, npi: str):
    """Crée la structure pour une personne physique."""
    npi_dir = os.path.join(base_dir, npi)
    justificatifs_dir = os.path.join(npi_dir, "justificatifs")
    os.makedirs(justificatifs_dir, exist_ok=True)

    # informations.txt
    with open(os.path.join(npi_dir, "informations.txt"), "w", encoding="utf-8") as f:
        f.write(f"NPI: {npi}")

    # ifu.pdf
    create_pdf(os.path.join(justificatifs_dir, "ifu.pdf"))

def create_structure_personne_morale(base_dir: str, ifu: str):
    """Crée la structure pour une personne morale."""
    ifu_dir = os.path.join(base_dir, ifu)
    justificatifs_dir = os.path.join(ifu_dir, "justificatifs")
    os.makedirs(justificatifs_dir, exist_ok=True)

    # informations.txt
    with open(os.path.join(ifu_dir, "informations.txt"), "w", encoding="utf-8") as f:
        f.write(f"IFU: {ifu}")

    # ifu.pdf et rccm.pdf
    create_pdf(os.path.join(justificatifs_dir, "ifu.pdf"))
    create_pdf(os.path.join(justificatifs_dir, "rccm.pdf"))

def process_dataframe(df: pd.DataFrame, output_dir: str, progress_bar):
    """Crée la structure complète selon la catégorie du marchand."""
    npi_column = "NPI"
    ifu_column = "IFU"
    category_column = "CATEGORIE DU MARCHAND"

    total = len(df)
    count_morale = 0
    count_physique = 0

    for i, row in df.iterrows():
        categorie = str(row.get(category_column, "")).strip()
        npi = clean_id(row.get(npi_column))
        ifu = clean_id(row.get(ifu_column))

        if categorie == "Pers Morale" and ifu:
            create_structure_personne_morale(output_dir, ifu)
            count_morale += 1
        elif categorie != "Pers Morale" and npi:
            create_structure_personne_physique(output_dir, npi)
            count_physique += 1

        progress_bar.progress((i + 1) / total)

    return count_morale, count_physique

def zip_folder(folder_path: str) -> str:
    """Compresse un dossier et retourne le chemin du zip."""
    zip_path = f"{folder_path}.zip"
    if os.path.exists(zip_path):
        os.remove(zip_path)
    shutil.make_archive(folder_path, "zip", folder_path)
    return zip_path

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="📦 Générateur Dossiers Marchands", layout="centered")

st.title("📂 Générateur de Dossiers Marchands")
st.write("Ce module génère automatiquement les dossiers, fichiers et PDF pour chaque marchand à partir d’un fichier Excel.")

uploaded_file = st.file_uploader("📤 Importer le fichier Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    # Lecture sans conversion automatique en float
    df = pd.read_excel(uploaded_file, dtype=str)
    df = df.fillna("")  # éviter les NaN

    st.success(f"✅ Fichier chargé avec {len(df)} lignes.")
    st.dataframe(df.head())

    if st.button("🚀 Générer les dossiers et le ZIP"):
        with st.spinner("Génération en cours..."):
            with TemporaryDirectory() as tmpdir:
                output_dir = os.path.join(tmpdir, "PAHOU")
                os.makedirs(output_dir, exist_ok=True)

                progress_bar = st.progress(0)
                count_morale, count_physique = process_dataframe(df, output_dir, progress_bar)

                zip_path = zip_folder(output_dir)

                st.success(f"""
                ✅ Création terminée !
                - **{count_morale}** dossiers de *personnes morales*
                - **{count_physique}** dossiers de *personnes physiques*
                """)

                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="📦 Télécharger le ZIP",
                        data=f,
                        file_name="PAHOU.zip",
                        mime="application/zip"
                    )

        st.balloons()
