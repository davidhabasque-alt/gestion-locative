import streamlit as st
import pandas as pd
import datetime
import io
import requests

st.set_page_config(
    page_title="Gestion Locative & Baux",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #1E293B;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 2rem;
    }
    .lease-box {
        background-color: #FFFFFF;
        border: 2px solid #2563EB;
        padding: 30px;
        border-radius: 12px;
        font-family: 'Times New Roman', Times, serif;
        line-height: 1.6;
        color: #111827;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

if "bailleur" not in st.session_state:
    st.session_state.bailleur = {
        "civilite": "M.",
        "nom": "DUPONT",
        "prenom": "Jean",
        "date_naissance": datetime.date(1980, 5, 12),
        "lieu_naissance": "Paris (75)",
        "adresse": "10 Rue de la Paix, 75002 Paris",
        "email": "jean.dupont@example.com",
        "telephone": "06 12 34 56 78"
    }

if "biens" not in st.session_state:
    st.session_state.biens = pd.DataFrame([
        {
            "id": 1,
            "nom": "Appartement T2 Centre",
            "adresse": "15 Rue de la République, 75011 Paris",
            "type": "Meublé",
            "surface": 42.5,
            "pieces": 2,
            "loyer_hc": 850.0,
            "charges": 70.0,
            "depot_garantie": 1700.0,
            "date_irl": datetime.date(2023, 7, 1),
            "irl_base": 140.59
        }
    ])

if "locataires" not in st.session_state:
    st.session_state.locataires = pd.DataFrame([
        {
            "id": 1,
            "civilite": "Mme",
            "nom": "MARTIN",
            "prenom": "Sophie",
            "date_naissance": datetime.date(1995, 8, 24),
            "lieu_naissance": "Lyon (69)",
            "adresse_actuelle": "5 Avenue Victor Hugo, 69002 Lyon",
            "email": "sophie.martin@example.com",
            "telephone": "06 98 76 54 32",
            "bien_id": 1,
            "date_entree": datetime.date(2023, 9, 1)
        }
    ])

def chercher_adresse_ban(query):
    """Recherche des adresses officielles via l'API BAN (data.gouv.fr)."""
    if not query or len(query) < 3:
        return []
    try:
        url = "https://api-adresse.data.gouv.fr/search/"
        response = requests.get(url, params={"q": query, "limit": 5}, timeout=3)
        if response.status_code == 200:
            data = response.json()
            return [f["properties"]["label"] for f in data.get("features", [])]
    except Exception:
        pass
    return []

def get_prochain_id(df):
    """Génère le prochain identifiant unique pour un DataFrame."""
    if df.empty:
        return 1
    return int(df["id"].max()) + 1

st.sidebar.title("🏠 Immogestion")
st.sidebar.markdown("*Gestion Locative & Baux Conformes*")

menu = st.sidebar.radio(
    "Menu principal",
    [
        "📊 Tableau de Bord",
        "👤 Profil Bailleur",
        "🏢 Biens Immobiliers",
        "👥 Locataires",
        "📜 Générateur de Bail",
        "💶 Loyers & Quittances",
        "📈 Révision IRL"
    ]
)

if menu == "📊 Tableau de Bord":
    st.markdown('<div class="main-header">Tableau de Bord</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Aperçu synthétique de vos logements et locataires</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    nb_biens = len(st.session_state.biens)
    nb_locataires = len(st.session_state.locataires)
    total_loyers = st.session_state.biens["loyer_hc"].sum() if not st.session_state.biens.empty else 0
    total_charges = st.session_state.biens["charges"].sum() if not st.session_state.biens.empty else 0

    col1.metric("Biens sous gestion", nb_biens)
    col2.metric("Locataires actifs", nb_locataires)
    col3.metric("Loyers HC mensuels", f"{total_loyers:,.2f} €")
    col4.metric("Charges mensuelles", f"{total_charges:,.2f} €")

    st.divider()

    st.subheader("📋 Liste récapitulative")
    if not st.session_state.biens.empty:
        df_display = st.session_state.biens.merge(
            st.session_state.locataires, 
            left_on="id", 
            right_on="bien_id", 
            how="left", 
            suffixes=("_bien", "_locataire")
        )
        st.dataframe(
            df_display[["nom", "type", "loyer_hc", "charges", "nom_locataire", "prenom"]].rename(
                columns={
                    "nom": "Logement",
                    "type": "Type",
                    "loyer_hc": "Loyer HC (€)",
                    "charges": "Charges (€)",
                    "nom_locataire": "Nom Locataire",
                    "prenom": "Prénom Locataire"
                }
            ),
            use_container_width=True
        )
    else:
        st.info("Aucun bien enregistré.")

elif menu == "👤 Profil Bailleur":
    st.markdown('<div class="main-header">Profil du Bailleur / Propriétaire</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Coordonnées légales utilisées pour la génération des baux et quittances</div>', unsafe_allow_html=True)

    with st.form("form_bailleur"):
        c1, c2, c3 = st.columns([1, 2, 2])
        civilite = c1.selectbox(
            "Civilité *", 
            ["M.", "Mme", "Société / SCI"], 
            index=["M.", "Mme", "Société / SCI"].index(st.session_state.bailleur.get("civilite", "M."))
        )
        nom = c2.text_input("Nom / Raison Sociale *", value=st.session_state.bailleur.get("nom", ""))
        prenom = c3.text_input("Prénom (si particulier)", value=st.session_state.bailleur.get("prenom", ""))

        c4, c5 = st.columns(2)
        date_naissance = c4.date_input("Date de naissance", value=st.session_state.bailleur.get("date_naissance", datetime.date(1980, 1, 1)))
        lieu_naissance = c5.text_input("Lieu de naissance (ex: Paris 15e)", value=st.session_state.bailleur.get("lieu_naissance", ""))

        st.markdown("---")
        st.subheader("📍 Adresse & Contact")

        adresse_input = st.text_input("Adresse postale du bailleur *", value=st.session_state.bailleur.get("adresse", ""))
        
        # API BAN Suggestions
        if adresse_input and len(adresse_input) >= 3:
            sug_bailleur = chercher_adresse_ban(adresse_input)
            if sug_bailleur:
                choix_b = st.selectbox("Suggestions d'adresses trouvées :", sug_bailleur, key="sug_bailleur_select")
                if st.checkbox("Utiliser cette adresse officielle", key="check_b_adresse"):
                    adresse_input = choix_b

        c6, c7 = st.columns(2)
        email = c6.text_input("Email *", value=st.session_state.bailleur.get("email", ""))
        telephone = c7.text_input("Téléphone *", value=st.session_state.bailleur.get("telephone", ""))

        submit_bailleur = st.form_submit_button("💾 Enregistrer le profil bailleur")

        if submit_bailleur:
            st.session_state.bailleur = {
                "civilite": civilite,
                "nom": nom,
                "prenom": prenom,
                "date_naissance": date_naissance,
                "lieu_naissance": lieu_naissance,
                "adresse": adresse_input,
                "email": email,
                "telephone": telephone
            }
            st.success("Profil bailleur mis à jour avec succès !")

elif menu == "🏢 Biens Immobiliers":
    st.markdown('<div class="main-header">Gestion des Biens Immobiliers</div>', unsafe_allow_html=True)

    with st.expander("➕ Ajouter un nouveau logement", expanded=False):
        with st.form("form_bien"):
            nom_bien = st.text_input("Nom / Libellé du bien (ex: T2 Centre-Ville)")
            
            adresse_bien = st.text_input("Adresse complète du logement *")
            if adresse_bien and len(adresse_bien) >= 3:
                sug_biens = chercher_adresse_ban(adresse_bien)
                if sug_biens:
                    choix_bien = st.selectbox("Adresses suggérées :", sug_biens, key="sug_bien_select")
                    if st.checkbox("Valider l'adresse suggérée", key="check_bien_adresse"):
                        adresse_bien = choix_bien

            col_a, col_b, col_c = st.columns(3)
            type_bail = col_a.selectbox("Type de bail", ["Nu", "Meublé"])
            surface = col_b.number_input("Surface (m²)", min_value=1.0, value=35.0, step=0.5)
            pieces = col_c.number_input("Nombre de pièces", min_value=1, value=2)

            col_d, col_e, col_f = st.columns(3)
            loyer_hc = col_d.number_input("Loyer Hors Charges (€)", min_value=0.0, value=650.0, step=10.0)
            charges = col_e.number_input("Provisions sur charges (€)", min_value=0.0, value=50.0, step=5.0)
            depot = col_f.number_input("Dépôt de garantie (€)", min_value=0.0, value=650.0, step=10.0)

            submit_bien = st.form_submit_button("Créer le bien")

            if submit_bien:
                nouveau_id = get_prochain_id(st.session_state.biens)
                nouveau_bien = {
                    "id": nouveau_id,
                    "nom": nom_bien,
                    "adresse": adresse_bien,
                    "type": type_bail,
                    "surface": surface,
                    "pieces": pieces,
                    "loyer_hc": loyer_hc,
                    "charges": charges,
                    "depot_garantie": depot,
                    "date_irl": datetime.date.today(),
                    "irl_base": 140.0
                }
                st.session_state.biens = pd.concat([st.session_state.biens, pd.DataFrame([nouveau_bien])], ignore_index=True)
                st.success("Nouveau logement enregistré !")
                st.rerun()

    st.subheader("Parc immobilier enregistré")
    if not st.session_state.biens.empty:
        st.dataframe(st.session_state.biens, use_container_width=True)
    else:
        st.info("Aucun logement enregistré.")

elif menu == "👥 Locataires":
    st.markdown('<div class="main-header">Gestion des Locataires</div>', unsafe_allow_html=True)

    with st.expander("➕ Ajouter un nouveau locataire", expanded=True):
        with st.form("form_locataire"):
            c1, c2, c3 = st.columns([1, 2, 2])
            civilite_loc = c1.selectbox("Civilité *", ["M.", "Mme"])
            nom_loc = c2.text_input("Nom de famille *")
            prenom_loc = c3.text_input("Prénom *")

            c4, c5 = st.columns(2)
            date_naiss_loc = c4.date_input("Date de naissance *", value=datetime.date(1995, 1, 1))
            lieu_naiss_loc = c5.text_input("Lieu de naissance * (ex: Lyon 6e)")

            st.markdown("---")
            st.write("**📍 Adresse actuelle (avant emménagement)**")
            adresse_loc = st.text_input("Rechercher l'adresse actuelle *")
            
            if adresse_loc and len(adresse_loc) >= 3:
                sug_loc = chercher_adresse_ban(adresse_loc)
                if sug_loc:
                    choix_loc = st.selectbox("Suggestions d'adresses officielles :", sug_loc, key="sug_loc_select")
                    if st.checkbox("Valider cette adresse", key="check_loc_adresse"):
                        adresse_loc = choix_loc

            c6, c7 = st.columns(2)
            email_loc = c6.text_input("Email *")
            tel_loc = c7.text_input("Téléphone *")

            st.markdown("---")
            biens_dispos = st.session_state.biens
            bien_id_choisi = None
            if not biens_dispos.empty:
                dict_biens = dict(zip(biens_dispos['id'], biens_dispos['nom']))
                bien_id_choisi = st.selectbox("Attribuer au logement :", options=list(dict_biens.keys()), format_func=lambda x: dict_biens[x])
            
            date_entree = st.date_input("Date d'entrée dans les lieux", value=datetime.date.today())

            submit_loc = st.form_submit_button("Enregistrer le locataire")

            if submit_loc:
                nouveau_id_loc = get_prochain_id(st.session_state.locataires)
                nouveau_loc = {
                    "id": nouveau_id_loc,
                    "civilite": civilite_loc,
                    "nom": nom_loc,
                    "prenom": prenom_loc,
                    "date_naissance": date_naiss_loc,
                    "lieu_naissance": lieu_naiss_loc,
                    "adresse_actuelle": adresse_loc,
                    "email": email_loc,
                    "telephone": tel_loc,
                    "bien_id": bien_id_choisi,
                    "date_entree": date_entree
                }
                st.session_state.locataires = pd.concat([st.session_state.locataires, pd.DataFrame([nouveau_loc])], ignore_index=True)
                st.success("Locataire enregistré avec succès !")
                st.rerun()

    st.subheader("Répertoire des locataires")
    if not st.session_state.locataires.empty:
        st.dataframe(st.session_state.locataires, use_container_width=True)
    else:
        st.info("Aucun locataire enregistré.")

elif menu == "📜 Générateur de Bail":
    st.markdown('<div class="main-header">Générateur de Bail Conforme</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Contrat de location d\'habitation principale (Loi du 6 juillet 1989 / Loi ALUR / Loi ÉLAN)</div>', unsafe_allow_html=True)

    if st.session_state.biens.empty or st.session_state.locataires.empty:
        st.warning("⚠️ Veuillez d'abord ajouter au moins un bien immobilier et un locataire.")
    else:
        c_b, c_l = st.columns(2)
        dict_b = dict(zip(st.session_state.biens['id'], st.session_state.biens['nom']))
        bien_sel_id = c_b.selectbox("Sélectionnez le logement :", options=list(dict_b.keys()), format_func=lambda x: dict_b[x])
        
        locs_filtr = st.session_state.locataires[st.session_state.locataires['bien_id'] == bien_sel_id]
        if locs_filtr.empty:
            locs_filtr = st.session_state.locataires

        dict_l = dict(zip(locs_filtr['id'], locs_filtr['nom'] + " " + locs_filtr['prenom']))
        loc_sel_id = c_l.selectbox("Sélectionnez le locataire :", options=list(dict_l.keys()), format_func=lambda x: dict_l[x])

        info_bailleur = st.session_state.bailleur
        info_bien = st.session_state.biens[st.session_state.biens['id'] == bien_sel_id].iloc[0]
        info_loc = st.session_state.locataires[st.session_state.locataires['id'] == loc_sel_id].iloc[0]

        st.divider()

        with st.expander("⚙️ Options et clauses particulières du bail", expanded=True):
            col_g1, col_g2 = st.columns(2)
            date_effet = col_g1.date_input("Date de prise d'effet du contrat", value=info_loc.get('date_entree', datetime.date.today()))
            
            duree_ans = 3 if info_bien['type'] == 'Nu' else 1
            duree_bail = col_g2.number_input("Durée du bail (en années)", min_value=1, value=duree_ans)

            col_g3, col_g4 = st.columns(2)
            jour_paiement = col_g3.number_input("Jour du mois pour l'échéance du loyer", min_value=1, max_value=31, value=5)
            mode_paiement = col_g4.selectbox("Mode de règlement retenu", ["Virement bancaire", "Prélèvement automatique", "Chèque"])

        loyer_total = info_bien['loyer_hc'] + info_bien['charges']
        date_naiss_loc_str = pd.to_datetime(info_loc['date_naissance']).strftime('%d/%m/%Y') if info_loc['date_naissance'] else ""
        date_naiss_bai_str = pd.to_datetime(info_bailleur['date_naissance']).strftime('%d/%m/%Y') if info_bailleur.get('date_naissance') else ""

        html_bail = f"""
        <div class="lease-box">
            <h2 style="text-align: center; color: #1E3A8A; text-transform: uppercase; margin-bottom: 5px;">CONTRAT DE LOCATION D'HABITATION</h2>
            <p style="text-align: center; font-size: 0.95em; color: #4B5563; font-weight: bold;">
                Soumis au régime de la loi n° 89-462 du 6 juillet 1989 modifiée par la loi ALUR n° 2014-366 et la loi ÉLAN n° 2018-1021<br>
                <em>Logement à usage exclusif d'habitation principale - Location {info_bien['type'].upper()}</em>
            </p>
            <hr style="border: 0; height: 1px; background: #CBD5E1; margin: 20px 0;">

            <h3 style="color: #1E40AF; border-bottom: 1px solid #93C5FD; padding-bottom: 4px;">I. DÉSIGNATION DES PARTIES</h3>
            <p><strong>LE BAILLEUR (Propriétaire) :</strong><br>
            Civilité / Nom : <strong>{info_bailleur.get('civilite', 'M.')} {info_bailleur.get('nom', '')} {info_bailleur.get('prenom', '')}</strong><br>
            Né(e) le : {date_naiss_bai_str} à {info_bailleur.get('lieu_naissance', 'N/C')}<br>
            Demeurant à : <strong>{info_bailleur.get('adresse', 'N/C')}</strong><br>
            Adresse email : {info_bailleur.get('email', '')} — Tél : {info_bailleur.get('telephone', '')}
            </p>

            <p><strong>LE LOCATAIRE :</strong><br>
            Civilité / Nom : <strong>{info_loc.get('civilite', 'M.')} {info_loc.get('nom', '')} {info_loc.get('prenom', '')}</strong><br>
            Né(e) le : {date_naiss_loc_str} à {info_loc.get('lieu_naissance', 'N/C')}<br>
            Adresse actuelle : <strong>{info_loc.get('adresse_actuelle', 'N/C')}</strong><br>
            Adresse email : {info_loc.get('email', '')} — Tél : {info_loc.get('telephone', '')}
            </p>

            <h3 style="color: #1E40AF; border-bottom: 1px solid #93C5FD; padding-bottom: 4px;">II. OBJET DU CONTRAT ET DESCRIPTION DU LOGEMENT</h3>
            <p>Le bailleur loue au locataire le logement désigné ci-après, situé à :<br>
            <strong style="font-size: 1.1em; color: #1E293B;">{info_bien['adresse']}</strong></p>
            <ul>
                <li><strong>Désignation :</strong> {info_bien['nom']}</li>
                <li><strong>Type de location :</strong> {info_bien['type']}</li>
                <li><strong>Surface habitable :</strong> {info_bien['surface']} m²</li>
                <li><strong>Nombre de pièces principales :</strong> {info_bien['pieces']}</li>
            </ul>

            <h3 style="color: #1E40AF; border-bottom: 1px solid #93C5FD; padding-bottom: 4px;">III. DURÉE ET PRISE D'EFFET</h3>
            <p>Le présent bail est conclu pour une durée fixe de <strong>{duree_bail} an(s)</strong> prenant effet à compter du <strong>{date_effet.strftime('%d/%m/%Y')}</strong>.</p>

            <h3 style="color: #1E40AF; border-bottom: 1px solid #93C5FD; padding-bottom: 4px;">IV. CONDITIONS FINANCIÈRES</h3>
            <ul>
                <li><strong>Loyer mensuel hors charges :</strong> {info_bien['loyer_hc']:.2f} €</li>
                <li><strong>Provision mensuelle sur charges :</strong> {info_bien['charges']:.2f} €</li>
                <li><strong>TOTAL MENSUEL À PAYER :</strong> <strong style="color: #1E40AF; font-size: 1.1em;">{loyer_total:.2f} €</strong></li>
            </ul>
            <p>Le loyer est payable d'avance le <strong>{jour_paiement}</strong> de chaque mois par <strong>{mode_paiement}</strong>.</p>
            <p><strong>Dépôt de garantie :</strong> La somme de <strong>{info_bien['depot_garantie']:.2f} €</strong> est versée ce jour par le locataire.</p>

            <h3 style="color: #1E40AF; border-bottom: 1px solid #93C5FD; padding-bottom: 4px;">V. CLAUSES LÉGALES & SIGNATURES</h3>
            <p>Le contrat est assujetti au respect de l'obligation d'assurance risques locatifs, de jouissance paisible des lieux et à la révision annuelle automatique du loyer selon l'Indice de Référence des Loyers (IRL) publié par l'INSEE.</p>

            <br><br>
            <div style="display: flex; justify-content: space-between; margin-top: 30px;">
                <div style="width: 45%;">
                    Fait à ................................., le ....................<br><br>
                    <strong>Signature du Bailleur</strong><br>
                    <em>(Précédée de la mention "Lu et approuvé")</em>
                </div>
                <div style="width: 45%;">
                    <br><br>
                    <strong>Signature du Locataire</strong><br>
                    <em>(Précédée de la mention "Lu et approuvé")</em>
                </div>
            </div>
        </div>
        """

        st.subheader("👁️ Aperçu du Bail de Location")
        st.markdown(html_bail, unsafe_allow_html=True)

        st.divider()
        st.download_button(
            label="📥 Télécharger le Bail Conforme (Format HTML imprimable)",
            data=html_bail,
            file_name=f"Bail_{info_loc['nom']}_{info_bien['nom']}.html",
            mime="text/html"
        )

elif menu == "💶 Loyers & Quittances":
    st.markdown('<div class="main-header">Gestion des Loyers & Quittances</div>', unsafe_allow_html=True)

    if st.session_state.locataires.empty:
        st.warning("Aucun locataire enregistré.")
    else:
        st.subheader("Générer une Quittance de Loyer")
        loc_select_q = st.selectbox(
            "Sélectionner le locataire", 
            options=st.session_state.locataires['id'].tolist(),
            format_func=lambda x: f"{st.session_state.locataires[st.session_state.locataires['id']==x]['nom'].values[0]} {st.session_state.locataires[st.session_state.locataires['id']==x]['prenom'].values[0]}"
        )

        loc_data = st.session_state.locataires[st.session_state.locataires['id'] == loc_select_q].iloc[0]
        bien_data = st.session_state.biens[st.session_state.biens['id'] == loc_data['bien_id']].iloc[0]
        bailleur_data = st.session_state.bailleur

        mois_quittance = st.text_input("Mois concerné (ex: Août 2026)", value="Août 2026")

        loyer_total_q = bien_data['loyer_hc'] + bien_data['charges']

        text_quittance = f"""
===================================================================
                        QUITTANCE DE LOYER
===================================================================

BAILLEUR :
{bailleur_data.get('civilite', 'M.')} {bailleur_data.get('nom', '')} {bailleur_data.get('prenom', '')}
Adresse : {bailleur_data.get('adresse', '')}

LOCATAIRE :
{loc_data['civilite']} {loc_data['nom']} {loc_data['prenom']}
Adresse du logement loué : {bien_data['adresse']}

PÉRIODE : {mois_quittance}

DÉTAIL DU RÈGLEMENT :
- Loyer Hors Charges : {bien_data['loyer_hc']:.2f} €
- Provision sur Charges : {bien_data['charges']:.2f} €
-------------------------------------------------------------------
TOTAL REÇU : {loyer_total_q:.2f} €

Je soussigné(e) {bailleur_data.get('nom', '')} {bailleur_data.get('prenom', '')}, propriétaire du logement 
désigné ci-dessus, reconnais avoir reçu la somme de {loyer_total_q:.2f} € 
au titre du paiement du loyer et des charges pour la période mentionnée.

Fait le {datetime.date.today().strftime('%d/%m/%Y')}
        """

        st.code(text_quittance, language="text")

        st.download_button(
            label="📄 Télécharger la Quittance (.txt)",
            data=text_quittance,
            file_name=f"Quittance_{loc_data['nom']}_{mois_quittance}.txt",
            mime="text/plain"
        )

elif menu == "📈 Révision IRL":
    st.markdown('<div class="main-header">Calculateur de Révision de Loyer (IRL)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Calcul officiel de révision du loyer d\'après les indices INSEE</div>', unsafe_allow_html=True)

    c_r1, c_r2, c_r3 = st.columns(3)
    loyer_actuel = c_r1.number_input("Loyer actuel Hors Charges (€)", min_value=0.0, value=750.0, step=10.0)
    ancien_irl = c_r2.number_input("Ancien IRL (Trimestre N-1)", min_value=100.0, value=141.03, step=0.01)
    nouvel_irl = c_r3.number_input("Nouvel IRL publié", min_value=100.0, value=144.21, step=0.01)

    if ancien_irl > 0:
        nouveau_loyer = (loyer_actuel * nouvel_irl) / ancien_irl
        augmentation = nouveau_loyer - loyer_actuel
        pourcentage = (augmentation / loyer_actuel) * 100

        st.success(f"### Nouveau Loyer Révisé : {nouveau_loyer:.2f} € HC / mois")
        st.info(f"Augmentation mensuelle : +{augmentation:.2f} € (+{pourcentage:.2f} %)")
