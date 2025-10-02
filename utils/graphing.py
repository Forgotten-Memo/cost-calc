import numpy as np
import pandas as pd
import plotly.graph_objects as go
import json
import streamlit as st

def hex_to_rgba(hex_color, alpha=0.2):
    """Convert hex color to rgba string with given alpha."""
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


def plot_class_trendlines_px(classes, pipeline, bp_min=55000, bp_max_plot=100000, n_points=100, std_scale=1):
    """
    Plot predicted damage trendlines with filled std bands using Plotly.
    """
    class_std = json.load(open('./static/class_std.json'))

    if isinstance(classes, str):
        classes = [classes]

    fig = go.Figure()
    colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3']

    for i, cls in enumerate(classes):
        # Trendline
        bp_range = np.linspace(bp_min, bp_max_plot, n_points)
        X_trend = pd.DataFrame({'bp': bp_range, 'class': cls})
        y_trend = pipeline.predict(X_trend)

        y_lower = y_trend - std_scale * class_std[cls] * y_trend
        y_upper = y_trend + std_scale * class_std[cls] * y_trend
        color = colors[i % len(colors)]
        fill_color = hex_to_rgba(color, alpha=0.2)

        # Add upper band (invisible line)
        fig.add_trace(go.Scatter(
            x=bp_range,
            y=y_upper,
            mode='lines',
            line=dict(width=0),
            showlegend=False
        ))

        # Add lower band (fill to previous)
        fig.add_trace(go.Scatter(
            x=bp_range,
            y=y_lower,
            fill='tonexty',
            fillcolor=fill_color,
            line=dict(width=0),
            name=f'{cls} ±{std_scale} std'
        ))

        # Add trendline
        fig.add_trace(go.Scatter(
            x=bp_range,
            y=y_trend,
            mode='lines',
            line=dict(color=color, width=3),
            name=f'{cls} Trendline'
        ))

    fig.update_layout(
        title=f"Predicted Damage Trendlines for Classes: {', '.join(classes)}",
        xaxis_title='Battle Rating (bp)',
        yaxis_title='Predicted Damage (M)',
        legend_title_text='Class'
    )
    
    return fig
