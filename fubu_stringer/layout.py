# fubu_stringer/layout.py
"""Defines the dynamically loadable layout for the Stringer tab."""
import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html

from layouts.components import (
    create_final_zone_grid,
    create_tab_content_layout,
    create_two_column_layout,
)
from layouts.styles import (
    datatable_style_cell,
    datatable_style_header,
    datatable_style_table,
    grid_title_style,
)


def get_layout():
    """Creates and returns the layout for the stringer component."""
    
    card_body_content = [
        html.Label("Stringer Thickness (mm):", className="fw-bold"),
        dbc.Input(
            id="global-stringer-thickness-input",
            type="number",
            placeholder="Enter global thickness...",
        ),
        html.Hr(),
        html.Label("Stringer Density (g/cm³):", className="fw-bold mt-2"),
        dbc.Input(
            id="global-stringer-density-input",
            type="number",
            placeholder="Enter global density...",
        ),
        html.Label("Duck Feet Application:", className="fw-bold"),
        dcc.Dropdown(
            id="global-duck-feet-dropdown",
            options=[
                {"label": "No Duck Feet", "value": "No"},
                {"label": "Duck Feet", "value": "Yes"},
            ],
            value="No",
            clearable=False,
        ),
        html.Label("Strip Width Value (mm):"),
        dbc.Input(
            id="global-strip-width-input",
            type="number",
            placeholder="Enter strip width value",
            disabled=True,
        ),
        html.Label("Stringer Width Value (mm):"),
        dbc.Input(
            id="global-stringer-width-input",
            type="number",
            placeholder="Enter stringer width",
            disabled=True,
        ),
        html.Br(),
        dbc.Button(
            "Save Global Properties",
            id="global-props-save-button",
            color="primary",
            className="mt-2",
        ),
        html.Div(id="global-props-status-output", className="mt-2"),
    ]

    stringer_layout = create_tab_content_layout(
        children=[
            create_two_column_layout(
                image_src="/assets/stringer.jpg",
                card_header_text="Global Stringer Properties",
                card_body_content=card_body_content,
            ),
            *create_final_zone_grid(
                grid_id="stringer-tab-final-zone-grid", cell_selectable=False
            ),
            html.H3("Stringer Data View", style=grid_title_style),
            dash_table.DataTable(
                id="stringer-csv-table",
                style_cell={**datatable_style_cell, "minWidth": "120px"},
                style_header=datatable_style_header,
                style_table=datatable_style_table,
                fixed_rows={"headers": True},
                sort_action="native",
                filter_action="native",
                page_action="native",
                page_size=15,
            ),
            html.H3("Zone Stringer Weight Summary", style=grid_title_style),
            dash_table.DataTable(
                id="zone-stringer-weight-summary-table",
                style_cell={**datatable_style_cell, "minWidth": "150px"},
                style_header=datatable_style_header,
                style_table={"marginBottom": "50px"},
                sort_action="native",
            ),
        ]
    )
    
    return stringer_layout
