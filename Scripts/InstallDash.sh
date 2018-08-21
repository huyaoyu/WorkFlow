#!/bin/sh

# Execute with caution!

# The following commands are copied from
# https://dash.plot.ly/installation

pip install dash==0.24.1  # The core dash backend
pip install dash-renderer==0.13.0  # The dash front-end
pip install dash-html-components==0.11.0  # HTML components
pip install dash-core-components==0.27.1  # Supercharged components
pip install plotly --upgrade  # Plotly graphing library used in example
