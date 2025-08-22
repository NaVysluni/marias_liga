import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict
import random
import math
import json
import io

st.set_page_config(layout="centered", page_title="Mariášová Liga")
st.markdown(
    """
    <style>
    /* Odsazení celého hlavního obsahu od horního okraje */
    main > div:has(.block-container) {
        padding-top: 60px;
    }
    .stApp {
        background-image: url('https://img41.rajce.idnes.cz/d4102/19/19642/19642596_185bd55429092dbd5dccd20ff2c485cb/images/card_back_texture.jpg?ver=0');
        background-repeat: repeat;
        background-size: 100px 100px;
        background-attachment: fixed;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Pozadí hlavního kontejneru – textura papíru */
    .block-container {
        background-image: url('https://img41.rajce.idnes.cz/d4102/19/19642/19642596_185bd55429092dbd5dccd20ff2c485cb/images/paper.jpg?ver=0');
        background-repeat: repeat;
        background-size: 300px 300px;
        background-color: rgba(255, 255, 255, 0.75);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    h1 {
        margin-top: 0px;
        text-align: left;
        color: #2c2c2c;
        text-shadow: 1px 1px 1px #fff9;
    }

    h2, h3 {
        color: #2c2c2c;
        text-shadow: 1px 1px 1px #fff9;
    }
    
    .param-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        margin-bottom: 2rem;
    }

    .param-container .stNumberInput, 
    .param-container div[data-baseweb="select"] {
        width: 300px !important;
    }

    .stTextInput, .stNumberInput, .stSelectbox {
        background-color: #ffffffcc;
        border-radius: 8px;
    }

    button[kind="primary"] {
        background-color: #8b5e3c;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: bold;
    }

    button[kind="primary"]:hover {
        background-color: #5c3a1e;
    }
    
    .player-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    
    .player-table th, .player-table td {
        border: 1px solid #8b5e3c;
        padding: 8px;
        text-align: left;
    }
    
    .player-table th {
        background-color: #8b5e3c;
        color: white;
    }
    
    .player-table tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    
    .player-table tr:hover {
        background-color: #e6e6e6;
    }
    
    .highlight-winner {
        background-color: #d4edda !important;
        font-weight: bold;
    }
    
    .highlight-loser {
        background-color: #f8d7da !important;
    }
    
    .session-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    
    .session-table th, .session-table td {
        border: 1px solid #8b5e3c;
        padding: 8px;
        text-align: center;
    }
    
    .session-table th {
        background-color: #8b5e3c;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Inicializace session state
if 'players' not in st.session_state:
    st.session_state.players = {}  # Slovník všech hráčů: {jméno: {'celkovy_zisk': 0, 'pocet_dnu': 0}}
    
if 'sessions' not in st.session_state:
    st.session_state.sessions = []  # Seznam sezení: každé sezení je slovník s daty a výsledky
    
if 'current_session' not in st.session_state:
    st.session_state.current_session = None  # Aktuální sezení, které se právě zadává
    
if 'vklad' not in st.session_state:
    st.session_state.vklad = 100  # Výchozí vklad

if 'league_name' not in st.session_state:
    st.session_state.league_name = "Mariášová Liga"

# Funkce pro výpočet statistik hráčů
def calculate_player_stats():
    """Vypočítá statistiky pro všechny hráče"""
    player_stats = {}
    for player in st.session_state.players:
        total_zisk = st.session_state.players[player]['celkovy_zisk']
        pocet_dnu = st.session_state.players[player]['pocet_dnu']
        prumer_zisk = total_zisk / pocet_dnu if pocet_dnu > 0 else 0
        player_stats[player] = {
            'celkovy_zisk': total_zisk,
            'pocet_dnu': pocet_dnu,
            'prumer_zisk': prumer_zisk
        }
    return player_stats

# Funkce pro generování rozlosování švýcarským systémem
def generate_swiss_pairings(players, group_size=3, previous_pairings=None):
    """
    Generuje rozlosování pomocí švýcarského systému
    players: seznam hráčů s jejich celkovými zisky
    group_size: počet hráčů u stolu (3 nebo 4)
    previous_pairings: předchozí párování pro kontrolu opakování
    """
    # Seřadit hráče podle celkového zisku (sestupně)
    sorted_players = sorted(players.items(), key=lambda x: x[1]['celkovy_zisk'], reverse=True)
    player_names = [p[0] for p in sorted_players]
    
    # Pokud je počet hráčů nedělitelný, přidáme "dummy" hráče
    remainder = len(player_names) % group_size
    if remainder != 0:
        # Místo dummy hráčů rozdělíme přebývající hráče do existujících skupin
        groups = []
        num_groups = len(player_names) // group_size
        
        # Rozdělit hráče do skupin podle pořadí
        for i in range(num_groups):
            group = player_names[i*group_size:(i+1)*group_size]
            groups.append(group)
        
        # Rozdělit zbylé hráče do existujících skupin
        remaining_players = player_names[num_groups*group_size:]
        for i, player in enumerate(remaining_players):
            groups[i % len(groups)].append(player)
    else:
        # Přesný počet skupin
        num_groups = len(player_names) // group_size
        groups = [player_names[i*group_size:(i+1)*group_size] for i in range(num_groups)]
    
    return groups

# Funkce pro uložení ligy
def save_league():
    """Uloží aktuální stav ligy do JSON objektu"""
    league_data = {
        'league_name': st.session_state.league_name,
        'vklad': st.session_state.vklad,
        'players': st.session_state.players,
        'sessions': st.session_state.sessions
    }
    return json.dumps(league_data, ensure_ascii=False)

# Funkce pro načtení ligy
def load_league(uploaded_file):
    """Načte stav ligy z JSON souboru"""
    try:
        league_data = json.load(uploaded_file)
        st.session_state.league_name = league_data.get('league_name', 'Mariášová Liga')
        st.session_state.vklad = league_data.get('vklad', 100)
        st.session_state.players = league_data.get('players', {})
        st.session_state.sessions = league_data.get('sessions', [])
        st.session_state.current_session = None
        return True
    except Exception as e:
        st.error(f"Chyba při načítání souboru: {e}")
        return False

# Funkce pro založení nové ligy
def create_new_league():
    """Vytvoří novou ligu"""
    st.session_state.league_name = "Nová Mariášová Liga"
    st.session_state.vklad = 100
    st.session_state.players = {}
    st.session_state.sessions = []
    st.session_state.current_session = None

# Hlavička aplikace
col1, col2 = st.columns([0.7, 0.3])
with col1:
    st.header(f"{st.session_state.league_name} - Švýcarský Systém")
with col2:
    st.image("https://marias-turnaj.zya.me/marias.png")

# Hlavní navigace aplikace
app_mode = st.sidebar.selectbox(
    "Navigace",
    ["Založit/Uložit/Načíst", "Správa hráčů", "Nastavení ligy", "Hrací den - Rozlosování", "Hrací den - Zadání výsledků", "Průběžná tabulka"]
)

# Režim: Založit/Uložit/Načíst
if app_mode == "Založit/Uložit/Načíst":
    st.subheader("Správa ligy")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Založit novou ligu")
        if st.button("Nová liga", use_container_width=True):
            create_new_league()
            st.success("Nová liga byla vytvořena!")
            st.rerun()
    
    with col2:
        st.markdown("### Uložit aktuální ligu")
        league_json = save_league()
        st.download_button(
            label="Stáhnout ligový soubor",
            data=league_json,
            file_name=f"{st.session_state.league_name.replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col3:
        st.markdown("### Načíst existující ligu")
        uploaded_file = st.file_uploader("Vyberte soubor ligy", type="json", label_visibility="collapsed")
        if uploaded_file is not None:
            if st.button("Načíst ligu", use_container_width=True):
                if load_league(uploaded_file):
                    st.success("Liga byla úspěšně načtena!")
                    st.rerun()

# Režim: Správa hráčů
elif app_mode == "Správa hráčů":
    st.subheader("Správa hráčů ligy")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Přidat nového hráče")
        new_player = st.text_input("Jméno hráče")
        if st.button("Přidat hráče") and new_player:
            if new_player in st.session_state.players:
                st.error("Tento hráč již existuje!")
            else:
                st.session_state.players[new_player] = {'celkovy_zisk': 0, 'pocet_dnu': 0}
                st.success(f"Hráč {new_player} byl přidán!")
                st.rerun()
    
    with col2:
        st.markdown("### Odstranit hráče")
        if st.session_state.players:
            player_to_remove = st.selectbox("Vyberte hráče k odstranění", list(st.session_state.players.keys()))
            if st.button("Odstranit hráče") and player_to_remove:
                del st.session_state.players[player_to_remove]
                st.success(f"Hráč {player_to_remove} byl odstraněn!")
                st.rerun()
        else:
            st.info("Žádní hráči k odstranění")
    
    # Zobrazení seznamu hráčů
    st.markdown("### Seznam hráčů v lize")
    if st.session_state.players:
        player_stats = calculate_player_stats()
        df_players = pd.DataFrame({
            'Hráč': list(player_stats.keys()),
            'Celkový zisk': [stats['celkovy_zisk'] for stats in player_stats.values()],
            'Počet dní': [stats['pocet_dnu'] for stats in player_stats.values()],
            'Průměrný zisk': [round(stats['prumer_zisk'], 2) for stats in player_stats.values()]
        }).sort_values('Celkový zisk', ascending=False)
        
        st.dataframe(df_players, use_container_width=True, hide_index=True)
    else:
        st.info("Zatím nejsou přidáni žádní hráči. Přidejte první hráče výše.")

# Režim: Nastavení ligy
elif app_mode == "Nastavení ligy":
    st.subheader("Nastavení ligy")
    
    st.session_state.league_name = st.text_input("Název ligy", value=st.session_state.league_name)
    st.session_state.vklad = st.number_input(
        "Základní vklad na hráče (Kč)", 
        min_value=10, 
        step=10, 
        value=st.session_state.vklad
    )
    
    st.info(f"Aktuální počet hráčů v lize: {len(st.session_state.players)}")
    st.info(f"Aktuální základní vklad: {st.session_state.vklad} Kč")

# Režim: Hrací den - Rozlosování
elif app_mode == "Hrací den - Rozlosování":
    st.subheader("Hrací den - Rozlosování")
    
    if not st.session_state.players:
        st.warning("Použij'Navigaci'.")
    else:
        # Výběr hráčů přítomných v daném dni
        st.markdown("### Výběr přítomných hráčů")
        all_players = list(st.session_state.players.keys())
        present_players = st.multiselect(
            "Vyberte hráče přítomné dnes", 
            all_players,
            default=all_players  # Výchozí všichni hráči
        )
        
        if not present_players:
            st.warning("Vyberte alespoň jednoho hráče.")
        else:
            # Výběr velikosti skupiny
            group_size = st.radio("Počet hráčů u stolu", [3, 4], horizontal=True)
            
            if len(present_players) < group_size:
                st.warning(f"Pro hru potřebujete alespoň {group_size} hráče.")
            else:
                if st.button("Generovat rozlosování"):
                    # Získat celkové zisky přítomných hráčů
                    present_players_with_scores = {p: st.session_state.players[p] for p in present_players}
                    
                    # Generovat rozlosování
                    pairings = generate_swiss_pairings(present_players_with_scores, group_size)
                    
                    # Uložit rozlosování do session state
                    st.session_state.current_session = {
                        'date': pd.Timestamp.now().strftime('%Y-%m-%d'),
                        'players': present_players,
                        'group_size': group_size,
                        'pairings': pairings,
                        'results': None
                    }
                    
                    st.success("Rozlosování bylo vygenerováno!")
                
                # Zobrazit aktuální rozlosování, pokud existuje
                if st.session_state.current_session and st.session_state.current_session['results'] is None:
                    st.markdown("### Aktuální rozlosování")
                    st.info(f"Datum: {st.session_state.current_session['date']}")
                    st.info(f"Počet hráčů: {len(present_players)}")
                    
                    for i, table in enumerate(st.session_state.current_session['pairings']):
                        st.markdown(f"**Stůl {i+1}:** {', '.join(table)}")
                    
                    if st.button("Přejít k zadávání výsledků"):
                        st.session_state.current_session['results'] = {}
                        st.rerun()

# Režim: Hrací den - Zadání výsledků
elif app_mode == "Hrací den - Zadání výsledků":
    st.subheader("Hrací den - Zadání výsledků")
    
    if not st.session_state.current_session or st.session_state.current_session['results'] is None:
        st.warning("Použij'Navigaci'.")
    else:
        session = st.session_state.current_session
        st.info(f"Datum: {session['date']}")
        st.info(f"Počet hráčů: {len(session['players'])}")
        
        # Zadávání výsledků pro každý stůl
        all_results = []
        valid_session = True
        
        for table_idx, table_players in enumerate(session['pairings']):
            st.markdown(f"### Stůl {table_idx + 1}: {', '.join(table_players)}")
            
            sum_na_stole, sum_dokup = 0, 0
            table_results = []
            
            for player in table_players:
                col1, col2 = st.columns(2)
                with col1:
                    na_stole = st.number_input(
                        f"{player} – na stole (Kč)", 
                        min_value=0, 
                        step=10, 
                        key=f"stole_{table_idx}_{player}"
                    )
                with col2:
                    dokup = st.number_input(
                        f"{player} – dokup (Kč)", 
                        min_value=0, 
                        step=10, 
                        key=f"dokup_{table_idx}_{player}"
                    )
                
                sum_na_stole += na_stole
                sum_dokup += dokup
                zisk = na_stole - st.session_state.vklad - dokup
                
                table_results.append({
                    'Hráč': player, 
                    'Na stole': na_stole, 
                    'Dokup': dokup, 
                    'Zisk': zisk,
                    'Stůl': table_idx + 1
                })
            
            # Kontrola správnosti vkladů
            expected = st.session_state.vklad * len(table_players)
            diff = expected + sum_dokup - sum_na_stole
            
            if diff != 0:
                st.error(f"❌ Nesedí vklady u stolu {table_idx + 1}: rozdíl {diff} Kč")
                valid_session = False
            else:
                st.success("✅ Vklady souhlasí")
            
            # Zobrazení zisků s zvýrazněním vítěze a poraženého
            df_table = pd.DataFrame(table_results)
            max_zisk = df_table["Zisk"].max()
            min_zisk = df_table["Zisk"].min()
            
            for _, row in df_table.iterrows():
                style = ""
                if row["Zisk"] == max_zisk:
                    style = "color:green; font-weight:bold"
                elif row["Zisk"] == min_zisk:
                    style = "color:red; font-weight:bold"
                st.markdown(f"<div style='{style}'>{row['Hráč']}: zisk {row['Zisk']} Kč</div>", unsafe_allow_html=True)
            
            all_results.extend(table_results)
        
        # Tlačítko pro uložení výsledků
        if st.button("Uložit výsledky hracího dne"):
            if not valid_session:
                st.warning("Nelze uložit výsledky, dokud nejsou vklady vyrovnané u všech stolů.")
            else:
                # Uložit výsledky do session state
                st.session_state.current_session['results'] = all_results
                
                # Aktualizovat celkové zisky hráčů a počet odehraných dní
                for result in all_results:
                    player = result['Hráč']
                    zisk = result['Zisk']
                    st.session_state.players[player]['celkovy_zisk'] += zisk
                    st.session_state.players[player]['pocet_dnu'] += 1
                
                # Přidat sezení do historie
                st.session_state.sessions.append(st.session_state.current_session.copy())
                
                # Resetovat aktuální sezení
                st.session_state.current_session = None
                
                st.success("Výsledky byly úspěšně uloženy!")
                st.rerun()

# Režim: Průběžná tabulka
elif app_mode == "Průběžná tabulka":
    st.subheader("Průběžná tabulka ligy")
    
    if not st.session_state.players:
        st.warning("Žádní hráči v lize.")
    else:
        # Vypočítat statistiky hráčů
        player_stats = calculate_player_stats()
        
        # Vytvořit datový rámec s pořadím hráčů
        df_leaderboard = pd.DataFrame({
            'Hráč': list(player_stats.keys()),
            'Celkový zisk': [stats['celkovy_zisk'] for stats in player_stats.values()],
            'Počet dní': [stats['pocet_dnu'] for stats in player_stats.values()],
            'Průměrný zisk': [round(stats['prumer_zisk'], 2) for stats in player_stats.values()]
        }).sort_values('Celkový zisk', ascending=False)
        
        df_leaderboard['Pořadí'] = range(1, len(df_leaderboard) + 1)
        df_leaderboard = df_leaderboard[['Pořadí', 'Hráč', 'Celkový zisk', 'Počet dní', 'Průměrný zisk']]
        
        # Zobrazení tabulky
        st.dataframe(df_leaderboard, use_container_width=True, hide_index=True)
        
        # Možnost exportu do CSV
        csv = df_leaderboard.to_csv(index=False, sep=';', encoding='cp1250')
        st.download_button(
            label="Stáhnout tabulku jako CSV",
            data=csv,
            file_name=f"{st.session_state.league_name.replace(' ', '_')}_tabulka.csv",
            mime="text/csv"
        )
    
    # Zobrazení historie sezení
    st.markdown("### Historie hracích dnů")
    if not st.session_state.sessions:
        st.info("Zatím nebyl odehrán žádný hrací den.")
    else:
        for i, session in enumerate(reversed(st.session_state.sessions)):
            with st.expander(f"Hrací den {i+1} - {session['date']} ({len(session['players'])} hráčů)"):
                # Převést výsledky na DataFrame pro lepší zobrazení
                df_session = pd.DataFrame(session['results'])
                df_session = df_session[['Hráč', 'Na stole', 'Dokup', 'Zisk', 'Stůl']]
                
                # Seřadit podle zisku
                df_session = df_session.sort_values('Zisk', ascending=False)
                
                st.dataframe(df_session, use_container_width=True, hide_index=True)

# Informace v postranním panelu
st.sidebar.markdown("---")
st.sidebar.info(
    """
    **Mariášová Liga - Nápověda**
    
    1. **Založit/Uložit/Načíst**: Správa ligových souborů
    2. **Správa hráčů**: Přidejte nebo odeberte hráče ligy
    3. **Nastavení ligy**: Nastavte název a základní vklad
    4. **Hrací den**: Vygenerujte rozlosování a zadejte výsledky
    5. **Průběžná tabulka**: Prohlédněte si celkové výsledky ligy
    """
)