# fubu_stringer/layout.py
"""Defines the dynamically loadable layout for the Stringer tab."""
from dash import dash_table, html
from layouts.components import create_data_table, create_image_and_grid_layout
from layouts.styles import grid_title_style, datatable_style_cell, datatable_style_header

def get_layout():
    """Creates and returns the layout for the stringer component."""
    return html.Div([
        # This function creates the image and the Final Zone Grid
        *create_image_and_grid_layout(
            image_src="/assets/stringer.jpg",
            image_max_width="80%",
            grid_id="stringer-tab-final-zone-grid",
            cell_selectable=True,
        ),
        # This is the first Data View
        html.H3("Stringer Data View", style=grid_title_style),
        create_data_table(table_id="stringer-csv-table"),
        
        # This is the second Data View
        html.H3("Zone Stringer Weight Summary", style=grid_title_style),
        dash_table.DataTable(
            id="zone-stringer-weight-summary-table",
            style_cell={**datatable_style_cell, "minWidth": "150px"},
            style_header=datatable_style_header,
            style_table={"marginBottom": "50px"},
            sort_action="native",
        ),
    ])
