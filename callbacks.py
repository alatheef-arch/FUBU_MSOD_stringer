"""
Defines all callbacks for updating the stringer tab of the Dash application.
"""

# /callbacks/callbacks_stringer.py
import json
import traceback
from math import pi

import pandas as pd  # type: ignore
from dash import Input, Output, State, dash, html

from app import app
from callbacks.callbacks_helpers import _load_df, _load_json_safe
from data_processing.constants import stringer_columns
from data_processing.helpers import format_value_for_csv


def _calculate_stringer_weights(df, props, cs_lookup):
    """Calculates weights for the stringer DataFrame based on global properties."""
    g_thick = props.get("global_stringer_thickness", 0.0)
    g_dens = props.get("global_stringer_density", 0.0)
    g_duck = props.get("global_duck_feet_selection", "No")
    g_str_w = props.get("global_stringer_width", 0.0)
    g_strip_w = props.get("global_strip_width", 0.0)

    df["Stringer Thickness (mm)"] = g_thick
    df["Stringer Density (g/cm³)"] = g_dens
    df["Duck Feet Applied"] = "Yes" if g_duck == "Yes" else "No"
    df["Stringer Cross Section (mm²)"] = [
        cs_lookup.get(r.get("stringer name", "").split("_")[-1].strip(), {}).get(
            str(r.get("Frame ID", "")).strip(), 0.0
        )
        for _, r in df.iterrows()
    ]

    if g_duck == "Yes":
        pitch_cm = pd.to_numeric(df["Stringer Pitch (mm)"], "coerce").fillna(0)
        strip_area = (pitch_cm - g_str_w).clip(lower=0) * g_strip_w
        curve_area = (4 - pi) * (20**2 / 2)
        df["Duck Feet"] = ((strip_area + curve_area) * g_thick * g_dens) / 1000000.0
    else:
        df["Duck Feet"] = 0.0

    cs_cm2 = (
        pd.to_numeric(df["Stringer Cross Section (mm²)"], "coerce").fillna(0) / 100.0
    )
    len_cm = pd.to_numeric(df["Frame Length (Pitch) (mm)"], "coerce").fillna(0) / 10.0
    df["Weight (g)"] = cs_cm2 * len_cm * g_dens
    return df


def _update_panels_with_stringer_weights(panels, df, props):
    """Updates panel data with aggregated stringer and duck feet weights."""
    if "Zone Name" in df.columns and not df.empty:
        grouped = df.groupby("Zone Name")[["Duck Feet", "Weight (g)"]].sum()
        for p in panels:
            name = p.get("name")
            if name in grouped.index:
                p["total_stringer_weight"] = grouped.loc[name, "Weight (g)"]
                p["total_duck_feet"] = grouped.loc[name, "Duck Feet"]
            # FIX: This line was un-indented to ensure it runs for all panels.
            p["stringer_density"] = props.get("global_stringer_density", 0.0)
    return panels


@app.callback(
    [
        Output("stringer-csv-table", "data"),
        Output("stringer-csv-table", "columns"),
        Output("stringer-data-store", "data", allow_duplicate=True),
        Output("custom-panels-store", "data", allow_duplicate=True),
    ],
    [Input("custom-panels-store", "data"), Input("stringer-data-store", "data")],
    [
        State("stringer-cross-section-store", "data"),
        State("global-properties-store", "data"),
    ],
    prevent_initial_call=True,
)
def update_stringer_tab_table(panels, stringer_json, cs_lookup, props_json):
    """Updates stringer tab table dynamically"""
    if not stringer_json or not cs_lookup:
        return [], [], dash.no_update, panels or []
    try:
        df = _load_df(stringer_json)
        if df.empty:
            return [], [], dash.no_update, panels or []

        props = _load_json_safe(props_json)
        df = _calculate_stringer_weights(df, props, cs_lookup)

        df_for_display = df.rename(columns={"Duck Feet": "Duck Feet (kg)"})
        cols = stringer_columns
        df_for_display = df_for_display[
            [c for c in cols if c in df_for_display.columns]
        ]

        return (
            df_for_display.to_dict("records"),
            [{"name": i, "id": i} for i in df_for_display.columns],
            df.to_json(orient="split"),
            panels,
        )
    # pylint: disable=broad-exception-caught
    except Exception:
        traceback.print_exc()
        return [], [], dash.no_update, panels or []


# pylint: disable=too-many-arguments, too-many-positional-arguments
@app.callback(
    [
        Output("global-props-status-output", "children", allow_duplicate=True),
        Output("stringer-data-store", "data", allow_duplicate=True),
        Output("custom-panels-store", "data", allow_duplicate=True),
        Output("global-properties-store", "data", allow_duplicate=True),
    ],
    Input("global-props-save-button", "n_clicks"),
    [
        State("global-stringer-thickness-input", "value"),
        State("global-stringer-density-input", "value"),
        State("global-duck-feet-dropdown", "value"),
        State("global-stringer-width-input", "value"),
        State("global-strip-width-input", "value"),
        State("stringer-data-store", "data"),
        State("custom-panels-store", "data"),
        State("global-properties-store", "data"),
    ],
    prevent_initial_call=True,
)
def save_global_stringer_properties(
    n_clicks, thick, dens, duck, str_w, strip_w, stringer_json, panels, props_json
):
    """Saves global stringer properties for each cell in the zone"""
    if not n_clicks:
        return (dash.no_update,) * 4
    props = _load_json_safe(props_json)
    df = _load_df(stringer_json)
    try:
        props.update(
            {
                "global_stringer_thickness": float(thick or 0),
                "global_stringer_density": float(dens or 0),
                "global_duck_feet_selection": duck,
                "global_stringer_width": float(str_w or 0),
                "global_strip_width": float(strip_w or 0),
            }
        )

        if not df.empty:
            df = _calculate_stringer_weights(df, props, {})
            props["total_stringers"] = len(df)
            stringer_pitch = pd.to_numeric(
                df.get("Stringer Pitch (mm)", 0), errors="coerce"
            )
            props["total_stringer_pitch"] = stringer_pitch.fillna(0).sum()

        panels = _update_panels_with_stringer_weights(
            [p.copy() for p in (panels or [])], df, props
        )
        return (
            html.P("Global properties saved!", style={"color": "green"}),
            df.to_json(orient="split"),
            panels,
            json.dumps(props),
        )
    # pylint: disable=broad-exception-caught
    except Exception as e:
        traceback.print_exc()
        return (html.P(f"Error: {e}", style={"color": "red"}), (dash.no_update,) * 3)


@app.callback(
    [
        Output("zone-stringer-weight-summary-table", "data"),
        Output("zone-stringer-weight-summary-table", "columns"),
    ],
    [Input("stringer-data-store", "data")],
)
def update_zone_stringer_summary(stringer_json):
    """Saves stringer zone level summary information dynamically"""
    df = _load_df(stringer_json)
    if df.empty or not all(c in df.columns for c in ["Weight (g)", "Duck Feet"]):
        return [], []
    summary = (
        df.groupby("Zone Name")[["Weight (g)", "Duck Feet"]]
        .sum()
        .reset_index()
        .assign(
            **{
                "Total Stringer Weight (kg)": lambda x: x["Weight (g)"] / 1000,
                "Total Duck Feet (kg)": lambda x: x["Duck Feet"],
            }
        )
        .drop(columns=["Weight (g)", "Duck Feet"])
    )
    for col in ["Total Stringer Weight (kg)", "Total Duck Feet (kg)"]:
        summary[col] = summary[col].apply(format_value_for_csv)

    return (summary.to_dict("records"), [{"name": i, "id": i} for i in summary.columns])
