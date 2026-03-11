from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
import plotly.io as pio
import plotly.graph_objects as go
import dash_cytoscape as cyto

import json

from utils.colors import AppColors
from utils.graph import elements, stylesheet

# Plotly template
with open("assets/template.json", "r") as f:
    debate_template = json.load(f)
pio.templates["app_template"] = go.layout.Template(debate_template)
pio.templates.default = "app_template"

# Dash app
app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=["custom.css", dbc.themes.BOOTSTRAP],
)

# Dash params
DASHBOARD_NAME = "EU Fact Force"

# Custom dash app tab and logo
app.title = DASHBOARD_NAME
app._favicon = "icon.png"

# Header
header = html.Div(
    dbc.Row(
        dbc.Col(
            html.Div(
                [
                    html.Img(src="assets/icon.png", alt="image", height=50),
                    html.H1(
                        DASHBOARD_NAME,
                        style={
                            "color": AppColors.blue,
                            "font-weight": "bold",
                            "margin": "0",
                            "padding": "0",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "0px",
                },
            ),
            width=12,
        ),
        className="g-0",
    ),
    style={
        "padding": "1rem",
        "background-color": AppColors.green,
        "position": "fixed",
        "width": "100%",
        "zIndex": 1000,
    },
)
# Content
graph_example = html.Div(
    cyto.Cytoscape(
        id="graph",
        elements=elements,
        stylesheet=stylesheet,
        layout={"name": "cose"},
        style={"width": "100%", "height": "500px"},
    ),
    style={
        "border-radius": "15px",
        "padding": "20px",
        "background-color": AppColors.white,
    },
)


content = html.Div(
    children=graph_example,
    id="page-content",
    style={
        "margin-left": "1rem",
        "margin-right": "1rem",
        "padding": "1rem",
        "padding-top": "120px",
    },
)

# Layout
app.layout = html.Div([dcc.Location(id="url", refresh=False), header, content])

if __name__ == "__main__":
    app.run(debug=True)
