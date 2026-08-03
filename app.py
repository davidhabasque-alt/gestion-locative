import streamlit as st
import pandas as pd
import datetime
import io
import json
import urllib.request
import urllib.parse

st.set_page_config(
    page_title="Gestion Locative Immo",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #E2E8F0;
        margin-bottom: 15px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

if "biens" not in st.session_state:
    st.session_state.biens = pd.DataFrame(columns=[
        "id", "nom_bien", "type", "adresse", "surface", "pieces", 
        "loyer_hc", "charges", "depot_garantie", "mode_chauffage"
    ])

if "locataires" not in st.session_state:
    st.session_state.locataires = pd.DataFrame(columns=[
        "id", "civilite", "nom", "prenom", "date_naissance", 
        "lieu_naissance", "adresse_actuelle", "email", "telephone", "bien_id"
    ])

if "loyers" not in st.session_state:
    st.session_state.loyers = pd.DataFrame(columns=[
        "id", "bien_id", "locataire_id", "mois_annee", "montant_hc", 
        "montant_charges", "statut", "date_paiement"
    ])

if "bailleur" not in st.session_state:
    st.session_state.bailleur = {
        "civilite": "M.",
        "nom": "DUPONT",
        "prenom": "Jean",
        "date_naissance": "1980-05-15",
        "lieu_naissance": "Paris (75001)",
        "adresse": "12 Rue de la Paix, 75002 Paris",
        "email": "jean.dupont@email.com",
        "telephone": "06 12 34 56 78"
    }

def chercher_adresse_ban(query):
    """Recherche d'adresse via l'API officielle de la Base Adresse Nationale (BAN)"""
    if not query or len(query.strip()) < 3:
        return []
    try:
        url = f"https://api-adresse.data.gouv.fr/search/?q={urllib.parse.quote(query)}&limit=5"
        req = urllib.request.Request(url, headers={'User-Agent': 'StreamlitApp/1.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            results = [feature['properties']['label'] for feature in data.get('features', [])]
            return results
    except Exception:
        return []

def get_next_id(df):
    if df.empty:
        return 1
    return int(df["id"].max()) + 1

st.sidebar.title("🏠 Immogestion")
menu = st.sidebar.radio(
    "Navigation",
    [
        "📊 Tableau de Bord",
        "👤 Profil Bailleur",
        "🏡 Biens Immobiliers",
        "👥 Locataires",
        "📜 Générateur de Bail (ALUR)",
        "🧾 Suivi des Loyers & Quittances",
        "🧮 Calculateur Révision IRL"
    ]
)

st.sidebar.divider()
st.sidebar.caption("© Application de Gestion Locative v2.0")

if menu == "📊 Tableau de Bord":
    st.markdown('<div class="main-header">📊 Tableau de Bord</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Aperçu rapide de votre patrimoine et des encaissements</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    nb_biens = len(st.session_state.biens)
    nb_locataires = len(st.session_state.locataires)
    
    total_loyers = 0.0
    if not st.session_state.biens.empty:
        total_loyers = float(st.session_state.biens["loyer_hc"].sum() + st.session_state.biens["charges"].sum())
        
    col1.metric("Biens gérés", nb_biens)
    col2.metric("Locataires actifs", nb_locataires)
    col3.metric("Revenus mensuels attendus", f"{total_loyers:.2f} €")
    col4.metric("Taux d'occupation", f"{100 if nb_biens > 0 and nb_locataires >= nb_biens else (nb_locataires/nb_biens*100 if nb_biens>0 else 0):.0f} %")

    st.divider()
    st.subheader("📋 Liste récapitulative du parc immobilier")

    if not st.session_state.biens.empty:
        biens_df = st.session_state.biens.copy()
        locataires_df = st.session_state.locataires.copy() if not st.session_state.locataires.empty else pd.DataFrame()

        if not locataires_df.empty and "bien_id" in locataires_df.columns:
            df_display = biens_df.merge(
                locataires_df,
                left_on="id",
                right_on="bien_id",
                how="left",
                suffixes=("_bien", "_locataire")
            )
        else:
            df_display = biens_df.copy()
            df_display["nom_locataire"] = "Aucun"
            df_display["prenom"] = ""

        # Construct safe display dataframe without KeyError
        cols_to_select = {}
        if "nom_bien" in df_display.columns:
            cols_to_select["nom_bien"] = "Nom du Logement"
        elif "nom" in df_display.columns:
            cols_to_select["nom"] = "Nom du Logement"

        if "type" in df_display.columns:
            cols_to_select["type"] = "Type"
        if "adresse" in df_display.columns:
            cols_to_select["adresse"] = "Adresse"
        if "loyer_hc" in df_display.columns:
            cols_to_select["loyer_hc"] = "Loyer HC (€)"
        if "charges" in df_display.columns:
            cols_to_select["charges"] = "Charges (€)"

        if "nom_locataire" in df_display.columns:
            cols_to_select["nom_locataire"] = "Nom Locataire"
        elif "nom_y" in df_display.columns:
            cols_to_select["nom_y"] = "Nom Locataire"

        if "prenom" in df_display.columns:
            cols_to_select["prenom"] = "Prénom Locataire"

        final_df = df_display[list(cols_to_select.keys())].rename(columns=cols_to_select)
        st.dataframe(final_df, use_container_width=True)
    else:
        st.info("Aucun bien enregistré pour le moment. Allez dans le menu 'Biens Immobiliers' pour en ajouter un.")

elif menu == "👤 Profil Bailleur":
    st.markdown('<div class="main-header">👤 Profil du Bailleur (Propriétaire)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ces informations figurent obligatoirement sur les baux et quittances</div>', unsafe_allow_html=True)

    with st.form("form_bailleur"):
        col1, col2, col3 = st.columns([1, 2, 2])
        civilite = col1.selectbox("Civilité", ["M.", "Mme", "Société / SCI"], index=["M.", "Mme", "Société / SCI"].index(st.session_state.bailleur.get("civilite", "M.")))
        nom = col2.text_input("Nom ou Raison Sociale", st.session_state.bailleur.get("nom", ""))
        prenom = col3.text_input("Prénom", st.session_state.bailleur.get("prenom", ""))

        col_d, col_l = st.columns(2)
        date_naissance = col_d.text_input("Date de naissance / Création", st.session_state.bailleur.get("date_naissance", "1980-01-01"))
        lieu_naissance = col_l.text_input("Lieu de naissance / Siège social", st.session_state.bailleur.get("lieu_naissance", "Paris"))

        st.subheader("📍 Adresse du Bailleur")
        saisie_adr_b = st.text_input("Rechercher l'adresse (Autocomplétion BAN)", value="", help="Tapez votre adresse puis sélectionnez ci-dessous")
        propositions_b = chercher_adresse_ban(saisie_adr_b) if saisie_adr_b else []
        
        adresse_actuelle_b = st.session_state.bailleur.get("adresse", "")
        if propositions_b:
            adresse_finale_b = st.selectbox("Sélectionner l'adresse exacte trouvée :", propositions_b)
        else:
            adresse_finale_b = st.text_input("Adresse enregistrée", value=adresse_actuelle_b)

        col_e, col_t = st.columns(2)
        email = col_e.text_input("Adresse Email", st.session_state.bailleur.get("email", ""))
        telephone = col_t.text_input("Téléphone", st.session_state.bailleur.get("telephone", ""))

        submit_b = st.form_submit_button("💾 Enregistrer le Profil Bailleur")
        if submit_b:
            st.session_state.bailleur = {
                "civilite": civilite,
                "nom": nom,
                "prenom": prenom,
                "date_naissance": date_naissance,
                "lieu_naissance": lieu_naissance,
                "adresse": adresse_finale_b,
                "email": email,
                "telephone": telephone
            }
            st.success("Profil bailleur mis à jour avec succès !")

elif menu == "🏡 Biens Immobiliers":
    st.markdown('<div class="main-header">🏡 Gestion des Biens Immobiliers</div>', unsafe_allow_html=True)

    with st.expander("➕ Ajouter un nouveau logement", expanded=True):
        with st.form("form_bien"):
            col1, col2 = st.columns(2)
            nom_bien = col1.text_input("Nom / Identifiant du bien", placeholder="Ex: Studio Centre Ville - Apt 12")
            type_bien = col2.selectbox("Type de location", ["Meublé", "Nu (Non meublé)", "Garage / Parking", "Local Commercial"])

            st.write("📍 **Adresse du Logement**")
            saisie_adr = st.text_input("Recherche d'adresse (API Base Adresse Nationale)", placeholder="Tapez ex: 10 rue de la République Lyon")
            props_adr = chercher_adresse_ban(saisie_adr) if saisie_adr else []
            
            if props_adr:
                adresse_choisie = st.selectbox("Propositions d'adresses officielles :", props_adr)
            else:
                adresse_choisie = st.text_input("Saisie manuelle si non trouvée", value=saisie_adr)

            col3, col4, col5 = st.columns(3)
            surface = col3.number_input("Surface (m²)", min_value=1.0, value=35.0, step=0.5)
            pieces = col4.number_input("Nombre de pièces main", min_value=1, value=2)
            mode_chauffage = col5.selectbox("Chauffage / Eau", ["Individuel Électrique", "Individuel Gaz", "Collectif", "Autre"])

            col6, col7, col8 = st.columns(3)
            loyer_hc = col6.number_input("Loyer Hors Charges (€)", min_value=0.0, value=550.0, step=10.0)
            charges = col7.number_input("Provision sur Charges (€)", min_value=0.0, value=50.0, step=5.0)
            depot = col8.number_input("Dépôt de garantie (€)", min_value=0.0, value=550.0, step=50.0)

            submit_bien = st.form_submit_button("➕ Ajouter ce bien")
            if submit_bien:
                if not nom_bien or not adresse_choisie:
                    st.error("Veuillez indiquer un nom et une adresse pour le logement.")
                else:
                    new_id = get_next_id(st.session_state.biens)
                    new_row = pd.DataFrame([{
                        "id": new_id,
                        "nom_bien": nom_bien,
                        "type": type_bien,
                        "adresse": adresse_choisie,
                        "surface": surface,
                        "pieces": pieces,
                        "loyer_hc": loyer_hc,
                        "charges": charges,
                        "depot_garantie": depot,
                        "mode_chauffage": mode_chauffage
                    }])
                    st.session_state.biens = pd.concat([st.session_state.biens, new_row], ignore_index=True)
                    st.success(f"Logement '{nom_bien}' ajouté avec succès !")
                    st.rerun()

    st.subheader("📜 Liste de vos logements")
    if not st.session_state.biens.empty:
        st.dataframe(st.session_state.biens, use_container_width=True)
    else:
        st.info("Aucun logement enregistré.")

elif menu == "👥 Locataires":
    st.markdown('<div class="main-header">👥 Gestion des Locataires</div>', unsafe_allow_html=True)

    with st.expander("➕ Enregistrer un nouveau locataire", expanded=True):
        with st.form("form_locataire"):
            col1, col2, col3 = st.columns([1, 2, 2])
            civilite_loc = col1.selectbox("Civilité", ["M.", "Mme"])
            nom_loc = col2.text_input("Nom de famille")
            prenom_loc = col3.text_input("Prénom")

            col4, col5 = st.columns(2)
            date_naiss_loc = col4.text_input("Date de naissance", placeholder="JJ/MM/AAAA (ex: 12/04/1995)")
            lieu_naiss_loc = col5.text_input("Lieu de naissance", placeholder="Ex: Lyon (69)")

            st.write("📍 **Adresse actuelle du locataire (avant emménagement)**")
            saisie_adr_loc = st.text_input("Chercher l'adresse actuelle", placeholder="Tapez l'ancienne adresse du locataire")
            props_adr_loc = chercher_adresse_ban(saisie_adr_loc) if saisie_adr_loc else []
            if props_adr_loc:
                adresse_actuelle_loc = st.selectbox("Choisir l'adresse trouvée :", props_adr_loc)
            else:
                adresse_actuelle_loc = st.text_input("Saisie manuelle adresse actuelle", value=saisie_adr_loc)

            col6, col7 = st.columns(2)
            email_loc = col6.text_input("Adresse Email")
            tel_loc = col7.text_input("Numéro de Téléphone")

            st.divider()
            st.write("🏠 **Attribution d'un logement**")
            
            biens_dispos = st.session_state.biens
            options_biens = {"Aucun logement attribué": None}
            if not biens_dispos.empty:
                for _, row in biens_dispos.iterrows():
                    options_biens[f"{row['nom_bien']} ({row['adresse']})"] = row["id"]
            
            bien_selectionne_label = st.selectbox("Assigner à un logement :", list(options_biens.keys()))
            bien_id_associe = options_biens[bien_selectionne_label]

            submit_loc = st.form_submit_button("➕ Enregistrer le locataire")
            if submit_loc:
                if not nom_loc or not prenom_loc:
                    st.error("Veuillez remplir au moins le nom et le prénom.")
                else:
                    new_id_loc = get_next_id(st.session_state.locataires)
                    new_loc_row = pd.DataFrame([{
                        "id": new_id_loc,
                        "civilite": civilite_loc,
                        "nom": nom_loc,
                        "prenom": prenom_loc,
                        "date_naissance": date_naiss_loc,
                        "lieu_naissance": lieu_naiss_loc,
                        "adresse_actuelle": adresse_actuelle_loc,
                        "email": email_loc,
                        "telephone": tel_loc,
                        "bien_id": bien_id_associe
                    }])
                    st.session_state.locataires = pd.concat([st.session_state.locataires, new_loc_row], ignore_index=True)
                    st.success(f"Locataire {prenom_loc} {nom_loc} enregistré !")
                    st.rerun()

    st.subheader("📋 Liste des locataires enregistrés")
    if not st.session_state.locataires.empty:
        st.dataframe(st.session_state.locataires, use_container_width=True)
    else:
        st.info("Aucun locataire enregistré pour le moment.")

elif menu == "📜 Générateur de Bail (ALUR)":
    st.markdown('<div class="main-header">📜 Générateur de Contrat de Bail conforme (ALUR / ÉLAN)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Générez un contrat complet et légal prêt à l\'impression</div>', unsafe_allow_html=True)

    if st.session_state.biens.empty or st.session_state.locataires.empty:
        st.warning("⚠️ Pour générer un bail, vous devez avoir enregistré au moins **un bien** et **un locataire**.")
    else:
        col_b, col_l = st.columns(2)
        
        # Select Property
        biens_dict = {f"{row['nom_bien']} - {row['adresse']}": row['id'] for _, row in st.session_state.biens.iterrows()}
        bien_label = col_b.selectbox("1. Sélectionner le Logement", list(biens_dict.keys()))
        selected_bien_id = biens_dict[bien_label]
        bien_info = st.session_state.biens[st.session_state.biens['id'] == selected_bien_id].iloc[0]

        # Select Tenant
        locs_dict = {f"{row['civilite']} {row['prenom']} {row['nom']}": row['id'] for _, row in st.session_state.locataires.iterrows()}
        loc_label = col_l.selectbox("2. Sélectionner le Locataire", list(locs_dict.keys()))
        selected_loc_id = locs_dict[loc_label]
        loc_info = st.session_state.locataires[st.session_state.locataires['id'] == selected_loc_id].iloc[0]

        st.subheader("⚙️ Conditions du bail")
        col_c1, col_c2, col_c3 = st.columns(3)
        date_debut = col_c1.date_input("Date de prise d'effet du bail", datetime.date.today())
        duree_annees = col_c2.number_input("Durée du bail (Années)", min_value=1, value=1 if bien_info['type'] == "Meublé" else 3)
        jour_paiement = col_c3.number_input("Jour du mois pour le paiement", min_value=1, max_value=31, value=5)

        b_info = st.session_state.bailleur

        # Generating Lease Markdown Document
        lease_text = f"""
# CONTRAT DE BAIL DE LOCATION D'HABITATION
*(Soumis au régime de la loi n° 89-462 du 6 juillet 1989 et conforme à la loi ALUR)*

---

### I. DÉSIGNATION DES PARTIES

**LE BAILLEUR (Propriétaire) :**
- **Nom et Prénom / Raison sociale :** {b_info.get('civilite', '')} {b_info.get('prenom', '')} {b_info.get('nom', '')}
- **Date et lieu de naissance :** Né(e) le {b_info.get('date_naissance', 'N/A')} à {b_info.get('lieu_naissance', 'N/A')}
- **Demeurant à :** {b_info.get('adresse', 'N/A')}
- **Email :** {b_info.get('email', 'N/A')} | **Tél :** {b_info.get('telephone', 'N/A')}

**LE LOCATAIRE :**
- **Nom et Prénom :** {loc_info.get('civilite', '')} {loc_info.get('prenom', '')} {loc_info.get('nom', '')}
- **Date et lieu de naissance :** Né(e) le {loc_info.get('date_naissance', 'N/A')} à {loc_info.get('lieu_naissance', 'N/A')}
- **Adresse précédente :** {loc_info.get('adresse_actuelle', 'N/A')}
- **Email :** {loc_info.get('email', 'N/A')} | **Tél :** {loc_info.get('telephone', 'N/A')}

---

### II. OBJET ET DÉSIGNATION DES LIEUX
- **Adresse du logement loué :** {bien_info['adresse']}
- **Type de contrat :** Location en {bien_info['type']}
- **Surface habitable :** {bien_info['surface']} m²
- **Nombre de pièces principales :** {bien_info['pieces']}
- **Équipements & Chauffage :** {bien_info['mode_chauffage']}

---

### III. DURÉE ET PRISE D'EFFET
Le présent contrat est conclu pour une durée de **{duree_annees} an(s)** prenant effet le **{date_debut.strftime('%d/%m/%Y')}**.

---

### IV. CONDITIONS FINANCIÈRES
- **Loyer mensuel hors charges :** {bien_info['loyer_hc']:.2f} €
- **Provision mensuelle sur charges :** {bien_info['charges']:.2f} €
- **TOTAL MENSUEL :** **{(bien_info['loyer_hc'] + bien_info['charges']):.2f} €**
- **Paiement :** Le loyer et les charges sont payables d'avance le **{jour_paiement}** de chaque mois.
- **Dépôt de garantie :** Un dépôt de garantie d'un montant de **{bien_info['depot_garantie']:.2f} €** est versé ce jour.

---

### V. CLAUSES LEGALES & SIGNATURES
Fait à __________________________, le ______________________ en 2 exemplaires originaux.

**Signature du Bailleur**                                   **Signature du Locataire**
*(Précédée de la mention "Lu et approuvé")*                     *(Précédée de la mention "Lu et approuvé")*
        """

        st.divider()
        st.subheader("📄 Aperçu du Contrat de Bail")
        st.markdown(f"<div class='card'>{lease_text}</div>", unsafe_allow_html=True)

        st.download_button(
            label="📥 Télécharger le Bail au format Texte / Markdown",
            data=lease_text,
            file_name=f"Bail_{loc_info['nom']}_{bien_info['nom_bien']}.md",
            mime="text/markdown"
        )

elif menu == "🧾 Suivi des Loyers & Quittances":
    st.markdown('<div class="main-header">🧾 Suivi des Loyers & Quittances</div>', unsafe_allow_html=True)

    if st.session_state.biens.empty or st.session_state.locataires.empty:
        st.info("Veuillez d'abord ajouter des biens et des locataires.")
    else:
        st.subheader("➕ Déclarer un loyer reçu")
        with st.form("form_loyer"):
            col1, col2, col3 = st.columns(3)
            
            biens_list = {row['nom_bien']: row['id'] for _, row in st.session_state.biens.iterrows()}
            b_selected = col1.selectbox("Bien", list(biens_list.keys()))
            b_id = biens_list[b_selected]

            locs_list = {f"{row['prenom']} {row['nom']}": row['id'] for _, row in st.session_state.locataires.iterrows()}
            l_selected = col2.selectbox("Locataire", list(locs_list.keys()))
            l_id = locs_list[l_selected]

            mois = col3.text_input("Période / Mois", value=datetime.date.today().strftime("%B %Y"))

            bien_data = st.session_state.biens[st.session_state.biens['id'] == b_id].iloc[0]
            col4, col5, col6 = st.columns(3)
            l_hc = col4.number_input("Loyer HC (€)", value=float(bien_data['loyer_hc']))
            l_ch = col5.number_input("Charges (€)", value=float(bien_data['charges']))
            date_p = col6.date_input("Date du règlement", datetime.date.today())

            submit_paye = st.form_submit_button("✅ Enregistrer le paiement & Éditer la Quittance")
            if submit_paye:
                new_l_id = get_next_id(st.session_state.loyers)
                new_loyer = pd.DataFrame([{
                    "id": new_l_id,
                    "bien_id": b_id,
                    "locataire_id": l_id,
                    "mois_annee": mois,
                    "montant_hc": l_hc,
                    "montant_charges": l_ch,
                    "statut": "Payé",
                    "date_paiement": date_p.strftime('%d/%m/%Y')
                }])
                st.session_state.loyers = pd.concat([st.session_state.loyers, new_loyer], ignore_index=True)
                st.success("Paiement enregistré !")

        st.divider()
        st.subheader("📄 Générateur de Quittance de Loyer")
        
        b_prof = st.session_state.bailleur
        if not st.session_state.loyers.empty:
            loyer_sel_idx = st.selectbox("Sélectionner un loyer payé pour afficher la quittance :", st.session_state.loyers.index)
            r_loyer = st.session_state.loyers.loc[loyer_sel_idx]
            
            r_loc = st.session_state.locataires[st.session_state.locataires['id'] == r_loyer['locataire_id']].iloc[0]
            r_bien = st.session_state.biens[st.session_state.biens['id'] == r_loyer['bien_id']].iloc[0]

            quittance_text = f"""
================================================================================
                           QUITTANCE DE LOYER
================================================================================

Période : {r_loyer['mois_annee']}

BAILLEUR :
{b_prof.get('civilite', '')} {b_prof.get('prenom', '')} {b_prof.get('nom', '')}
{b_prof.get('adresse', '')}

LOCATAIRE :
{r_loc.get('civilite', '')} {r_loc.get('prenom', '')} {r_loc.get('nom', '')}
Apt situé au : {r_bien['adresse']}

--------------------------------------------------------------------------------
DÉTAIL DU RÈGLEMENT :
- Loyer Hors Charges : {r_loyer['montant_hc']:.2f} €
- Provision pour charges : {r_loyer['montant_charges']:.2f} €
--------------------------------------------------------------------------------
TOTAL REÇU : {(r_loyer['montant_hc'] + r_loyer['montant_charges']):.2f} €

Je soussigné(e) {b_prof.get('prenom', '')} {b_prof.get('nom', '')}, propriétaire du logement 
désigné ci-dessus, reconnais avoir reçu la somme de {(r_loyer['montant_hc'] + r_loyer['montant_charges']):.2f} € 
au titre du paiement du loyer et des charges pour la période mentionnée.

Date du règlement : {r_loyer['date_paiement']}

Fait pour valoir ce que de droit.
Signature du Bailleur.
================================================================================
            """
            st.code(quittance_text, language="text")

            st.download_button(
                label="📥 Télécharger la Quittance (Fichier texte)",
                data=quittance_text,
                file_name=f"Quittance_{r_loc['nom']}_{r_loyer['mois_annee']}.txt",
                mime="text/plain"
            )

elif menu == "🧮 Calculateur Révision IRL":
    st.markdown('<div class="main-header">🧮 Calculateur de Révision de Loyer (IRL)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Formule légale : Nouveau Loyer = Loyer Actuel x (Nouvel IRL / Ancien IRL)</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    loyer_actuel = col1.number_input("Loyer HC Actuel (€)", min_value=0.0, value=600.0, step=10.0)
    irl_ancien = col2.number_input("Ancien Indice IRL (Ex: Trimestre A-1)", value=141.03, step=0.01)

    irl_nouveau = st.number_input("Nouveau Indice IRL publié", value=144.21, step=0.01)

    if irl_ancien > 0:
        nouveau_loyer = loyer_actuel * (irl_nouveau / irl_ancien)
        augmentation = nouveau_loyer - loyer_actuel

        st.success(f"💶 **Nouveau Loyer révisé estimé : {nouveau_loyer:.2f} € HC**")
        st.info(f"📈 Augmentation mensuelle : +{augmentation:.2f} € (+{(augmentation/loyer_actuel*100):.2f} %)")
