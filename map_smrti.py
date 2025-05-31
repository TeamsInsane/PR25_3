import plotly.express as px

def get_map(data):
    smrtne = data[data["KlasifikacijaNesrece"] == "S SMRTNIM IZIDOM"]

    fig = px.scatter_map(
        smrtne,
        lat="lat",
        lon="lon",
        color_discrete_sequence=["red"],
        zoom=7,
        center={"lat": 46.0, "lon": 14.5},
        height=800,
        title="Smrtne nesreče (lokacije)"
    )

    fig.update_traces(hoverinfo='skip')
    fig.update_layout(map_style="open-street-map")
    return fig