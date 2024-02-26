import dash
from dash import dcc, html, Output, Input, State, ctx, \
                Dash, callback, clientside_callback, register_page, \
                no_update
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from dash_iconify import DashIconify



app = Dash(__name__, 
           use_pages=True,
           external_stylesheets=[dbc.themes.BOOTSTRAP],
           meta_tags=[
               {"name": "viewport", "content": "width=device-width, initial-scale=1"}
             ],
            suppress_callback_exceptions=False
           )
server = app.server

app.layout = dmc.MantineProvider(
        theme={
            'fontFamily': '"Inter", sans-serif',
            },
        children=[
            html.Div(
                style={"backgroundColor": "whitesmoke", 'minHeight':'100vh', 'display':'flex', 'flexDirection':'column'},
                children = [
                    dcc.Location(id='url', refresh=False),
                    html.Div([
                        dash.page_container
                    ], style={ "maxWidth":'1500px', 'width':'100%', 'margin':'auto', 'padding':'10px'}), 
                    html.Div(id='app-notification')
                ]
            )
        ]
)

if __name__ == '__main__':
    app.run_server(debug=True, port=8053)