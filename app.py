import streamlit as st
import pandas as pd
import datetime
import io

# -----------------------------------------------------------------------------
# CONFIGURATION DE LA PAGE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Gestion Locative Perso",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style personnalisé léger pour moderniser l'interface
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748B;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .stButton>button {
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# INITIALISATION DE LA BASE DE DONNÉES EN MÉMOIRE (SESSION STATE)
# -----------------------------------------------------------------------------
if 'biens' not in st.session_state:
    st.session_state.biens = pd.DataFrame([
        {
            "id": 1,
            "nom": "Appartement Centre-Ville",
            "adresse": "12 Rue de la République, 75011 Paris",
            "type": "Meublé",
            "loyer_hc": 750.0,
            "charges": 80.0,
            "depot_garantie": 1500.0,
            "valeur_achat": 210000.0
        },
        {
            "id": 2,
            "nom": "Studio T1 Rue Gare",
            "adresse": "5 Avenue de la Gare, 69002 Lyon",
            "type": "Nu",
            "loyer_hc": 520.0,
            "charges": 50.0,
            "depot_garantie": 520.0,
            "valeur_achat": 125000.0
        }
    ])

if 'locataires' not in st.session_state:
    st.session_state.locataires = pd.DataFrame([
        {
            "id": 1,
            "bien_id": 1,
            "nom": "Dupont",
            "prenom": "Thomas",
            "email": "thomas.dupont@example.com",
            "telephone": "06 12 34 56 78",
            "date_entree": datetime.date(2023, 9, 1),
            "date_revision_irl": "Q3"
        },
        {
            "id": 2,
            "bien_id": 2,
            "nom": "Martin",
            "prenom": "Sophie",
            "email": "sophie.martin@example.com",
            "telephone": "06 98 76 54 32",
            "date_entree": datetime.date(2024, 1, 15),
            "date_revision_irl": "Q1"
        }
    ])

if 'paiements' not in st.session_state:
    st.session_state.paiements = pd.DataFrame([
        {"id": 1, "bien_id": 1, "mois": "2026-07", "statut": "Payé", "date_paiement": datetime.date(2026, 7, 3), "montant": 830.0},
        {"id": 2, "bien_id": 2, "mois": "2026-07", "statut": "Payé", "date_paiement": datetime.date(2026, 7, 5), "montant": 570.0},
        {"id": 3, "bien_id": 1, "mois": "2026-08", "statut": "Payé", "date_paiement": datetime.date(2026, 8, 2), "montant": 830.0},
        {"id": 4, "bien_id": 2, "mois": "2026-08", "statut": "En attente", "date_paiement": None, "montant": 570.0},
    ])

# -----------------------------------------------------------------------------
# MENU DE NAVIGATION SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/609/609803.png", width=70)
st.sidebar.title("Gestion Locative")
st.sidebar.caption("Outil personnel sur-mesure")

menu = st.sidebar.radio(
    "Navigation",
    [
        "📊 Tableau de bord",
        "🏢 Biens Immobiliers",
        "👤 Locataires & Baux",
        "💶 Suivi des Loyers",
        "📄 Générateur de Quittance",
        "📐 Calculateur IRL & Rentabilité"
    ]
)

# -----------------------------------------------------------------------------
# 1. TABLEAU DE BORD
# -----------------------------------------------------------------------------
if menu == "📊 Tableau de bord":
    st.markdown('<div class="main-header">Tableau de bord</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Aperçu rapide de votre parc immobilier et des encaissements</div>', unsafe_allow_html=True)

    df_biens = st.session_state.biens
    df_loc = st.session_state.locataires
    df_pay = st.session_state.paiements

    # Calcul des métriques globales
    total_biens = len(df_biens)
    loyer_mensuel_attendu = (df_biens['loyer_hc'] + df_biens['charges']).sum()
    valeur_parc = df_biens['valeur_achat'].sum()
    rentabilite_brute = (loyer_mensuel_attendu * 12 / valeur_parc * 100) if valeur_parc > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Logements", f"{total_biens}")
    with col2:
        st.metric("Loyer Mensuel Total", f"{loyer_mensuel_attendu:.2f} €")
    with col3:
        st.metric("Valeur Estimée Parc", f"{valeur_parc:,.0f} €".replace(",", " "))
    with col4:
        st.metric("Rentabilité Brute Moyenne", f"{rentabilite_brute:.2f} %")

    st.write("---")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📅 Statut des loyers du mois en cours")
        mois_actuel = datetime.datetime.now().strftime("%Y-%m")
        df_mois = df_pay[df_pay['mois'] == mois_actuel]
        
        if df_mois.empty:
            st.info(f"Aucun enregistrement de paiement pour le mois en cours ({mois_actuel}).")
        else:
            merged_statut = df_biens.merge(df_mois, left_on="id", right_on="bien_id", how="left")
            merged_statut['statut'] = merged_statut['statut'].fillna('Non saisi')
            st.dataframe(
                merged_statut[['nom', 'loyer_hc', 'charges', 'statut', 'date_paiement']],
                column_config={
                    "nom": "Bien",
                    "loyer_hc": "Loyer HC (€)",
                    "charges": "Charges (€)",
                    "statut": "Statut du mois",
                    "date_paiement": "Date de réception"
                },
                use_container_width=True
            )

    with col_right:
        st.subheader("💡 Actions Rapides")
        if st.button("➕ Déclarer un loyer reçu", use_container_width=True):
            st.toast("Rendez-vous dans l'onglet 'Suivi des Loyers' pour enregistrer un paiement !")
        if st.button("✉️ Générer la dernière quittance", use_container_width=True):
            st.toast("Rendez-vous dans l'onglet 'Générateur de Quittance' !")

# -----------------------------------------------------------------------------
# 2. BIENS IMMOBILIERS
# -----------------------------------------------------------------------------
elif menu == "🏢 Biens Immobiliers":
    st.markdown('<div class="main-header">Gestion des Biens</div>', unsafe_allow_html=True)
    
    st.subheader("Liste de vos logements")
    st.dataframe(
        st.session_state.biens,
        column_config={
            "id": "ID",
            "nom": "Nom du bien",
            "adresse": "Adresse complète",
            "type": "Type de location",
            "loyer_hc": "Loyer HC (€)",
            "charges": "Provisions Charges (€)",
            "depot_garantie": "Dépôt Garantie (€)",
            "valeur_achat": "Prix d'achat (€)"
        },
        use_container_width=True
    )

    st.write("---")
    st.subheader("➕ Ajouter un nouveau logement")
    
    with st.form("form_bien"):
        col_a, col_b = st.columns(2)
        with col_a:
            nom = st.text_input("Nom de désignation", placeholder="ex: Studio Rivoli")
            adresse = st.text_input("Adresse", placeholder="ex: 10 Rue Rivoli 75004 Paris")
            type_loc = st.selectbox("Type de location", ["Meublé", "Nu", "Colocation", "Parking/Garage"])
            valeur = st.number_input("Valeur / Prix d'achat (€)", min_value=0.0, step=1000.0)
        with col_b:
            loyer_hc = st.number_input("Loyer hors charges (€)", min_value=0.0, step=10.0)
            charges = st.number_input("Provisions pour charges (€)", min_value=0.0, step=5.0)
            depot = st.number_input("Dépôt de garantie (€)", min_value=0.0, step=10.0)

        submitted = st.form_submit_button("Enregistrer le bien")
        if submitted:
            if nom and adresse:
                new_id = len(st.session_state.biens) + 1
                new_row = {
                    "id": new_id,
                    "nom": nom,
                    "adresse": adresse,
                    "type": type_loc,
                    "loyer_hc": loyer_hc,
                    "charges": charges,
                    "depot_garantie": depot,
                    "valeur_achat": valeur
                }
                st.session_state.biens = pd.concat([st.session_state.biens, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Le bien '{nom}' a été ajouté avec succès !")
                st.rerun()
            else:
                st.error("Veuillez remplir au moins le nom et l'adresse.")

# -----------------------------------------------------------------------------
# 3. LOCATAIRES & BAUX
# -----------------------------------------------------------------------------
elif menu == "👤 Locataires & Baux":
    st.markdown('<div class="main-header">Locataires & Baux</div>', unsafe_allow_html=True)

    # Fusion avec les biens pour afficher le nom du logement
    df_merged = st.session_state.locataires.merge(
        st.session_state.biens[['id', 'nom']], left_on='bien_id', right_on='id', suffixes=('', '_bien')
    )

    st.dataframe(
        df_merged[['id', 'nom_bien', 'prenom', 'nom', 'email', 'telephone', 'date_entree', 'date_revision_irl']],
        column_config={
            "id": "ID",
            "nom_bien": "Logement",
            "prenom": "Prénom",
            "nom": "Nom",
            "email": "Email",
            "telephone": "Téléphone",
            "date_entree": "Date d'entrée",
            "date_revision_irl": "Trimestre IRL"
        },
        use_container_width=True
    )

    st.write("---")
    st.subheader("➕ Nouveau Locataire / Nouveau Bail")

    with st.form("form_locataire"):
        col1, col2 = st.columns(2)
        with col1:
            biens_dispos = dict(zip(st.session_state.biens['id'], st.session_state.biens['nom']))
            bien_selected_id = st.selectbox("Sélectionner le logement", options=list(biens_dispos.keys()), format_func=lambda x: biens_dispos[x])
            prenom = st.text_input("Prénom du locataire")
            nom = st.text_input("Nom du locataire")
        with col2:
            email = st.text_input("Adresse e-mail")
            telephone = st.text_input("Numéro de téléphone")
            date_entree = st.date_input("Date de début de bail", value=datetime.date.today())
            trim_irl = st.selectbox("Trimestre d'indexation IRL", ["Q1", "Q2", "Q3", "Q4"])

        submitted_loc = st.form_submit_button("Ajouter le locataire")
        if submitted_loc:
            if prenom and nom:
                new_id = len(st.session_state.locataires) + 1
                new_row = {
                    "id": new_id,
                    "bien_id": bien_selected_id,
                    "nom": nom,
                    "prenom": prenom,
                    "email": email,
                    "telephone": telephone,
                    "date_entree": date_entree,
                    "date_revision_irl": trim_irl
                }
                st.session_state.locataires = pd.concat([st.session_state.locataires, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Locataire {prenom} {nom} enregistré avec succès !")
                st.rerun()

# -----------------------------------------------------------------------------
# 4. SUIVI DES LOYERS
# -----------------------------------------------------------------------------
elif menu == "💶 Suivi des Loyers":
    st.markdown('<div class="main-header">Suivi des Encaissements</div>', unsafe_allow_html=True)

    df_p = st.session_state.paiements.merge(
        st.session_state.biens[['id', 'nom']], left_on='bien_id', right_on='id'
    )

    st.subheader("Historique des paiements")
    st.dataframe(
        df_p[['nom', 'mois', 'montant', 'statut', 'date_paiement']],
        column_config={
            "nom": "Bien",
            "mois": "Mois (AAAA-MM)",
            "montant": "Montant Total (€)",
            "statut": "Statut",
            "date_paiement": "Date du virement"
        },
        use_container_width=True
    )

    st.write("---")
    st.subheader("✏️ Saisir / Mettre à jour un paiement")

    with st.form("form_paiement"):
        col1, col2, col3 = st.columns(3)
        with col1:
            biens_dict = dict(zip(st.session_state.biens['id'], st.session_state.biens['nom']))
            b_id = st.selectbox("Bien concerné", options=list(biens_dict.keys()), format_func=lambda x: biens_dict[x])
            mois_saisie = st.text_input("Mois concerné (Format AAAA-MM)", value=datetime.datetime.now().strftime("%Y-%m"))
        with col2:
            # Calcul automatique du loyer CC par défaut
            b_row = st.session_state.biens[st.session_state.biens['id'] == b_id].iloc[0]
            montant_defaut = float(b_row['loyer_hc'] + b_row['charges'])
            montant_recu = st.number_input("Montant perçu (€)", value=montant_defaut, step=10.0)
            statut_p = st.selectbox("Statut", ["Payé", "En attente", "Partiel", "Retard"])
        with col3:
            date_p = st.date_input("Date de paiement effective", value=datetime.date.today())

        sub_p = st.form_submit_button("Enregistrer le statut")
        if sub_p:
            new_p_id = len(st.session_state.paiements) + 1
            new_p_row = {
                "id": new_p_id,
                "bien_id": b_id,
                "mois": mois_saisie,
                "statut": statut_p,
                "date_paiement": date_p if statut_p == "Payé" else None,
                "montant": montant_recu
            }
            st.session_state.paiements = pd.concat([st.session_state.paiements, pd.DataFrame([new_p_row])], ignore_index=True)
            st.success("Statut de paiement mis à jour !")
            st.rerun()

# -----------------------------------------------------------------------------
# 5. GÉNÉRATEUR DE QUITTANCE
# -----------------------------------------------------------------------------
elif menu == "📄 Générateur de Quittance":
    st.markdown('<div class="main-header">Générateur de Quittance PDF/Texte</div>', unsafe_allow_html=True)
    st.markdown("Édition rapide d'une quittance de loyer conforme et prêtre à l'envoi.")

    biens_dict = dict(zip(st.session_state.biens['id'], st.session_state.biens['nom']))
    bien_id_sel = st.selectbox("Sélectionnez le bien concerné :", options=list(biens_dict.keys()), format_func=lambda x: biens_dict[x])

    # Recherche des infos du bien et du locataire associé
    bien_info = st.session_state.biens[st.session_state.biens['id'] == bien_id_sel].iloc[0]
    loc_info_list = st.session_state.locataires[st.session_state.locataires['bien_id'] == bien_id_sel]

    if loc_info_list.empty:
        st.warning("⚠️ Aucun locataire n'est actuellement associé à ce bien.")
    else:
        loc_info = loc_info_list.iloc[0]

        col1, col2 = st.columns(2)
        with col1:
            mois_quittance = st.text_input("Mois de quittance", value=datetime.datetime.now().strftime("%B %Y").capitalize())
            date_reglement = st.date_input("Date de règlement reçu", value=datetime.date.today())
        with col2:
            nom_bailleur = st.text_input("Nom du Propriétaire / Bailleur", value="M. Pierre DUPONT")
            adresse_bailleur = st.text_input("Adresse du Bailleur", value="1, Rue des Bailleurs 75000 Paris")

        loyer_hc = bien_info['loyer_hc']
        charges = bien_info['charges']
        loyer_total = loyer_hc + charges

        # Modèle de Quittance au format texte
        texte_quittance = f"""
================================================================================
                           QUITTANCE DE LOYER
================================================================================

BAILLEUR :
{nom_bailleur}
{adresse_bailleur}

LOCATAIRE :
{loc_info['prenom']} {loc_info['nom']}
{bien_info['adresse']}

LOGEMENT CONCERNÉ :
{bien_info['adresse']} ({bien_info['type']})

--------------------------------------------------------------------------------
PÉRIODE : Mois de {mois_quittance}
--------------------------------------------------------------------------------

DÉTAIL DU RÈGLEMENT :
  - Loyer Hors Charges : {loyer_hc:.2f} €
  - Provisions pour charges : {charges:.2f} €
  ---------------------------------------
  MONTANT TOTAL ACQUITTÉ : {loyer_total:.2f} €

Le bailleur reconnaît avoir reçu de {loc_info['prenom']} {loc_info['nom']} la somme 
de {loyer_total:.2f} € au titre du paiement du loyer et des charges pour la période 
indiquée ci-dessus, et lui en donne quittance sous réserve de tous ses droits.

Date du paiement reçu : {date_reglement.strftime('%d/%m/%Y')}
Fait à Paris, le {datetime.date.today().strftime('%d/%m/%Y')}

Signature du bailleur :
{nom_bailleur}
================================================================================
"""

        st.subheader("Aperçu de la Quittance :")
        st.text_area("Texte de la quittance", texte_quittance, height=380)

        # Bouton de téléchargement du fichier texte de la quittance
        st.download_button(
            label="📥 Télécharger la Quittance (.txt)",
            data=texte_quittance,
            file_name=f"Quittance_{loc_info['nom']}_{mois_quittance.replace(' ', '_')}.txt",
            mime="text/plain"
        )

# -----------------------------------------------------------------------------
# 6. CALCULATEUR IRL & RENTABILITÉ
# -----------------------------------------------------------------------------
elif menu == "📐 Calculateur IRL & Rentabilité":
    st.markdown('<div class="main-header">Outils de Calcul</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📊 Révision de Loyer (IRL)", "💰 Rentabilité & Fiscalité"])

    with tab1:
        st.subheader("Formule officielle de Révision du Loyer selon l'INSEE")
        st.markdown("""
        Formule : **`Nouveau Loyer = Loyer Actuel x (Nouvel Indice IRL / Ancien Indice IRL)`**
        """)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            loyer_actuel_hc = st.number_input("Loyer Hors Charges actuel (€)", value=750.0, step=10.0)
        with col_b:
            ancien_irl = st.number_input("Ancien indice IRL (Trimestre A-1)", value=141.03, step=0.01)
        with col_c:
            nouvel_irl = st.number_input("Nouveau dernier indice IRL publié", value=144.21, step=0.01)

        if ancien_irl > 0:
            nouveau_loyer_hc = loyer_actuel_hc * (nouvel_irl / ancien_irl)
            augmentation = nouveau_loyer_hc - loyer_actuel_hc

            st.success(f"📈 **Nouveau Loyer Hors Charges estimé : {nouveau_loyer_hc:.2f} € / mois**")
            st.info(f"Augmentation nette de **+{augmentation:.2f} € / mois** (soit +{(augmentation/loyer_actuel_hc)*100:.2f} %)")

    with tab2:
        st.subheader("Calculateur Rapide de Rendement")
        col1, col2 = st.columns(2)
        with col1:
            px_achat = st.number_input("Prix d'achat du bien (€)", value=180000.0, step=5000.0)
            frais_notaire = st.number_input("Frais de notaire / travaux (€)", value=15000.0, step=1000.0)
            px_total = px_achat + frais_notaire
        with col2:
            l_mensuel = st.number_input("Loyer mensuel HC attendu (€)", value=750.0, step=20.0)
            charges_non_recov = st.number_input("Charges non récupérables / an (€)", value=600.0, step=50.0)

        renta_brute = (l_mensuel * 12 / px_total * 100) if px_total > 0 else 0
        renta_nette = ((l_mensuel * 12 - charges_non_recov) / px_total * 100) if px_total > 0 else 0

        st.metric("Rentabilité Brute", f"{renta_brute:.2f} %")
        st.metric("Rentabilité Nette (avant impôts)", f"{renta_nette:.2f} %")
```eof

### 🚀 Comment lancer votre application en 2 minutes :

1. **Installez Streamlit et Pandas** (si ce n'est pas déjà fait) en ouvrant votre terminal :
   
```bash
   pip install streamlit pandas
