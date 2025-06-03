import streamlit as st
import pandas as pd
import pickle
from nb_module import compute_naive_bayes_table
from map_smrti import get_map
from pyproj import Transformer
from main_map import get_main_map
import calplot
import plotly.express as px

# Model

with open("label_encoders.pkl", "rb") as f:
    label_encoders = pickle.load(f)

with open("y_encoder.pkl", "rb") as f:
    y_encoder = pickle.load(f)

st.markdown("""
# Napovedovalec resnosti prometne nesreče

Ta aplikacija uporablja modelno učenje za **napovedovanje resnosti prometne nesreče** na podlagi različnih dejavnikov, kot so:

- ura dneva,  
- vremenske razmere,  
- dan v tednu,  
- stanje vozišča,  
- vrsta ceste,  
- tip nesreče in  
- vrednost alkotesta voznika.

Po vnosu podatkov aplikacija prikaže: **Napovedano klasifikacijo nesreče**
""")

with st.form("nesreca_form"):
    col1, col2 = st.columns(2)

    with col1:
        vreme = st.selectbox("Vreme", ["Jasno", "Deževno", "Oblačno", "Megla", "Sneg", "Veter", "Neznano"])
        dan = st.selectbox("Dan v tednu", ["Ponedeljek", "Torek", "Sreda", "Četrtek", "Petek", "Sobota", "Nedelja"])
        ura = st.slider("Ura nesreče", 0, 23, 12)
        stanje_vozisca = st.selectbox("Stanje Vozišča", ["Mokro", "Suho", "Sneženo - Nepluženo", "Sneženo - Pluženo", "Spolzko"])

    with col2:
        vrsta_ceste = st.selectbox("Vrsta ceste", ["Turistična cesta", "Regionalna Cesta III. Reda", "Regionalna Cesta II. Reda", "Regionalna Cesta", "Naselje z Uličnim Sistemom", "Naselje brez Uličnega Sistema", "Lokalna Cesta", "Hitra Cesta", "Glavna Cesta II. Reda", "Glavna Cesta", "Avtocesta"])
        tip_nesrece = st.selectbox("Tip nesreče", ["Trčenje v stoječe / parkirano vozilo", "Trčenje v objekt", "Prevrnitev vozila", "Povoženje živali", "Povoženje Pešca", "Ostalo", "Oplaženje", "Naletno Trčenje", "Čelno Trčenje", "Bočno Trčenje"])
        alkohol = st.number_input("Vrednost alkotesta (‰)", min_value=0.0, max_value=5.0, step=0.01)
        model_name =  st.selectbox("Izberi model", ["RandomForest", "DecisionTree", "XGBoost"])

    submit = st.form_submit_button("Napovej")

if submit:
    input_dict = {
            "UraPN": [ura],
            "DanVTednu": [dan],
            "VrstaCesteNaselja": [vrsta_ceste],
            "StanjeVozisca": [stanje_vozisca],
            "TipNesrece": [tip_nesrece],
            "VremenskeOkoliscine": [vreme],
            "VrednostAlkotesta": [alkohol],
        }
    user_df = pd.DataFrame(input_dict)
        
    numeric_cols = ["VrednostAlkotesta", "UraPN"]
    user_df[numeric_cols] = user_df[numeric_cols].fillna(0)

    categorical_cols = [col for col in user_df.columns if col not in numeric_cols]
    user_df[categorical_cols] = user_df[categorical_cols].fillna("UNKNOWN")

    for col in user_df.columns:
        if col in label_encoders and col not in numeric_cols:
            user_df[col] = user_df[col].astype(str).str.upper()
            known_labels = label_encoders[col].classes_
            if not user_df[col].iloc[0] in known_labels:
                st.error(f"Unknown value for {col}: {user_df[col].iloc[0]}")
                st.stop()
            user_df[col] = label_encoders[col].transform(user_df[col])
        else:
            user_df[col] = pd.to_numeric(user_df[col], errors="coerce")


    
    with open(f"model_{model_name}.pkl", "rb") as f:
        model = pickle.load(f)



    prediction = model.predict(user_df)
    klasifikacija = y_encoder.inverse_transform(prediction)[0]

    st.success(f"Napovedana klasifikacija nesreče: **{klasifikacija}**")

    probas = model.predict_proba(user_df)[0]
    proba_df = pd.DataFrame({
        "Klasifikacija": y_encoder.inverse_transform(list(range(len(probas)))),
        "Verjetnost": probas
    })

    st.bar_chart(proba_df.set_index("Klasifikacija"))



with open("categorical_nb_model.pkl", "rb") as f:
    model = pickle.load(f)

# Naivni model

st.markdown("""
# Verjetnosti nesreč po vrsti ceste     
        
Spodnja aplikacija predstavlja, kako se resnost prometnih nesreč razlikuje glede na vrsto ceste. Uporabljen je preprost model (Naivni Bayes), ki za vsak tip ceste izračuna verjetnosti za različne izide nesreče.
Izberi leta, ki te zanimajo, in v tabeli se prikažejo verjetnosti za posamezne kategorije. To lahko pomaga pri razumevanju, katere ceste so bolj tvegane in kje se zgodijo hujše nesreče.
""")

years = range(2014, 2024)
dataFrames = []

for year in years:
    dataFrame = pd.read_csv(f"./data/pn{year}.csv", encoding="cp1250", delimiter=";")
    dataFrame["Year"] = year
    dataFrames.append(dataFrame)
    
data = pd.concat(dataFrames, ignore_index=True)

alko_raw = data["VrednostAlkotesta"].astype(str).str.replace(",", ".").str.strip()
alko = pd.to_numeric(alko_raw, errors="coerce").fillna(0)

data["x"] = pd.to_numeric(data["GeoKoordinataX"], errors="coerce")
data["y"] = pd.to_numeric(data["GeoKoordinataY"], errors="coerce")
data = data.dropna(subset=["x", "y"])

transformer = Transformer.from_crs("EPSG:3912", "EPSG:4326", always_xy=True)

lons, lats  = transformer.transform(data["y"].values, data["x"].values)

data["lon"] = lons
data["lat"] = lats

years = sorted(data['Year'].dropna().unique())
selected_years = st.multiselect("Izberi leto za NB:", years, default=years)
filtered_data = data[data["Year"].isin(selected_years)]
result = compute_naive_bayes_table(filtered_data.copy())

formatted_result = result.applymap(lambda x: f"{x*100:.2f}%")

st.dataframe(formatted_result, height=426)

# Map

st.markdown("""
# Zemljevid smrti po letih
            
Na spodnjem zemljevidu so prikazane prometne nesreče s smrtnim izidom. Vsaka rdeča točka predstavlja lokacijo ene takšne nesreče.

Lahko izbereš določena leta in zemljevid se bo posodobil. Tako lahko hitro vidiš, kje so se v določenem obdobju zgodile najhujše nesreče.
""")
years = sorted(data['Year'].dropna().unique())
selected_years_map = st.multiselect("Izberi leto za map:", years, default=years)
filtered_data_map = data[data["Year"].isin(selected_years_map)]
fig = get_map(filtered_data_map)
st.plotly_chart(fig, use_container_width=True)


#OBČINE

main_data = data.copy()

st.title("Zemljevid prometnih nesreč po občinah")
st.write("Zemljevid prikazuje število nesreč glede na izbrane filtre.")


col1, col2 = st.columns(2)
with col1:
    vreme = st.selectbox("Vreme", ["VSE", "Jasno", "Deževno", "Oblačno", "Megla", "Sneg", "Veter", "Neznano"])
    ura = st.slider("Ura nesreče", 0, 23, 12)
    stanje_vozisca = st.selectbox("Stanje vozišča", ["VSE", "Mokro", "Suho", "Sneženo - Nepluženo", "Sneženo - Pluženo", "Spolzko"])

with col2:
    vrsta_ceste = st.selectbox("Vrsta ceste", [
        "VSE", "Turistična cesta", "Regionalna Cesta III. Reda", "Regionalna Cesta II. Reda",
        "Regionalna Cesta", "Naselje z Uličnim Sistemom", "Naselje brez Uličnega Sistema",
        "Lokalna Cesta", "Hitra Cesta", "Glavna Cesta II. Reda", "Glavna Cesta", "Avtocesta"
    ])
    tip_nesrece = st.selectbox("Tip nesreče", [
        "VSE", "Trčenje v stoječe / parkirano vozilo", "Trčenje v objekt", "Prevrnitev vozila",
        "Povoženje živali", "Povoženje Pešca", "Ostalo", "Oplaženje",
        "Naletno Trčenje", "Čelno Trčenje", "Bočno Trčenje"
    ])
    tip = st.selectbox("Klasifikacija nesreče", ["VSE"] + list(main_data["KlasifikacijaNesrece"].unique()))


filtered_df = main_data.copy()

if vreme != "VSE":
    filtered_df = filtered_df[filtered_df["VremenskeOkoliscine"] == vreme.upper()]

if stanje_vozisca != "VSE":
    filtered_df = filtered_df[filtered_df["StanjeVozisca"] == stanje_vozisca.upper()]

if vrsta_ceste != "VSE":
    filtered_df = filtered_df[filtered_df["VrstaCesteNaselja"] == vrsta_ceste.upper()]

if tip_nesrece != "VSE":
    filtered_df = filtered_df[filtered_df["TipNesrece"] == tip_nesrece.upper()]

if tip != "VSE":
    filtered_df = filtered_df[filtered_df["KlasifikacijaNesrece"] == tip]

filtered_df = filtered_df[filtered_df["UraPN"] == ura]

fig = get_main_map(filtered_df)
st.plotly_chart(fig, use_container_width=True)


# Koledar
koledar_data = data.copy()
koledar_data["DatumPN"] = pd.to_datetime(koledar_data["DatumPN"])

st.header("Koledar prometnih nesreč po dnevih")
st.write("Izberi leto in prikaže se število nesreč za vsak dan v tem letu.")

leta = sorted(koledar_data["DatumPN"].dt.year.unique())
izbrano_leto = st.selectbox("Izberi leto", leta)
leto_df = koledar_data[koledar_data["DatumPN"].dt.year == izbrano_leto]
daily_counts = leto_df["DatumPN"].value_counts().reset_index()
daily_counts.columns = ["Datum", "Št_nesreč"]
daily_counts["Mesec"] = daily_counts["Datum"].dt.month
daily_counts["Dan"] = daily_counts["Datum"].dt.day
fig = px.density_heatmap(
    daily_counts,
    x="Dan",
    y="Mesec",
    z="Št_nesreč",
    nbinsx=31,
    nbinsy=12,
    color_continuous_scale="Reds",
    labels={"Št_nesreč": "Število nesreč", "Dan": "Dan", "Mesec": "Mesec"},
    hover_data={"Datum": True, "Št_nesreč": True},
    title=f"Interaktivni koledar nesreč za leto {izbrano_leto}"
)

fig.update_layout(yaxis_nticks=12)
fig.update_coloraxes(colorbar_title="Število nesreč") 

fig.update_traces(hovertemplate="Mesec: %{y}<br>Dan: %{x}<br>Število nesreč: %{z}")

st.plotly_chart(fig, use_container_width=True)

#Alkohol

st.header("Povprečna vrednost alkotesta glede na tip nesreče")

alko_data = data.copy()

alko_data = alko_data.dropna(subset=["VrednostAlkotesta", "TipNesrece"])
alko_data["VrednostAlkotesta"] = alko_data["VrednostAlkotesta"].str.replace(',', '.')
alko_data["VrednostAlkotesta"] = pd.to_numeric(alko_data["VrednostAlkotesta"], errors='coerce')
st.write(f"Število vrstic z alkotestom in tipom nesreče: {len(alko_data)}")

if alko_data.empty:
    st.warning("Ni podatkov za prikaz grafa.")
else:
    avg_alko = alko_data.groupby("TipNesrece")["VrednostAlkotesta"].mean().reset_index()
    avg_alko = avg_alko.sort_values("VrednostAlkotesta")

    fig = px.line(
        avg_alko,
        x="TipNesrece",
        y="VrednostAlkotesta",
        markers=True,
        labels={"TipNesrece": "Tip nesreče", "VrednostAlkotesta": "Povprečna vrednost alkotesta (mg/l)"},
        title="Povprečna vrednost alkotesta glede na tip nesreče"
    )

    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)