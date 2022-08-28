# import numpy as np
import pandas as pd
import pathlib
# import dash
# from jupyter_dash import JupyterDash
from dash import Dash
import plotly.express as px
import geopandas as gpd
# from geopandas import GeoDataFrame
# from shapely.geometry import Point
# from matplotlib import pyplot as plt
# import folium
import geopandas as gpd
# import plotly.offline as pyo
import plotly.graph_objs as go
from cProfile import label
# from optparse import Option
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.dependencies import Input, Output
pd.set_option('display.max_columns', None)


#import the data
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("Data").resolve()
df_ghg_country = pd.read_csv(DATA_PATH.joinpath("ghg-data.csv"))

# df_ghg_country = pd.read_csv("Data/ghg-data.csv")
df_ghg_country['gdp_per_capita']=df_ghg_country['gdp']/df_ghg_country['population']
countries_gdf = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
df_ghg_country = pd.merge(df_ghg_country, countries_gdf, left_on = 'iso_code', right_on = 'iso_a3')

df_gdp = pd.read_excel("Data/gdp_full.xls", sheet_name='Data')
df_gdp = pd.melt(df_gdp, id_vars = [ "Country Name", "Country Code"], value_vars=df_gdp.iloc[:,-62:])
df_gdp = df_gdp.rename(columns={"value":"GDP per capita (current US$)"})
df_gdp = df_gdp[df_gdp['variable']!='Unnamed: 66']
df_gdp=df_gdp.rename(columns = {"variable":"Year"})
df_gdp['Year']=df_gdp['Year'].astype(int)
df_gdp['GDP per capita (current US$)'] = df_gdp['GDP per capita (current US$)'].astype(float)

df_ghg_country = pd.merge(df_ghg_country, df_gdp, left_on=("iso_code", "year"), right_on= ('Country Code','Year'))
df_ghg_country.sort_values('year', inplace=True)

df_ghg_continent = df_ghg_country.groupby(["continent", "year"], as_index=False)[
    ["co2_per_capita", "GDP per capita (current US$)"]
].sum()

df_ghg_continent["country"] = df_ghg_continent["continent"]
df_ghg_continent["continent"] = "world"

df_ghg_world = df_ghg_country.groupby(["year"], as_index=False)[
    ["co2_per_capita", "GDP per capita (current US$)"]
].sum()
df_ghg_world["country"] = "world"
df_ghg_world["continent"] = ""


df_ghg_total = df_ghg_continent.append(
    df_ghg_country[
        [
            "year",
            "country",
            "continent",
            "co2_per_capita",
            "GDP per capita (current US$)",
        ]
    ]
)
df_ghg_total = df_ghg_total.append(
    df_ghg_world[
        [
            "year",
            "country",
            "continent",
            "co2_per_capita",
            "GDP per capita (current US$)",
        ]
    ]
)


mask = df_ghg_total.year == 2020
df_tmp = (
    df_ghg_total[mask]
    .dropna(subset="co2_per_capita")[["country", "continent", "co2_per_capita"]]
    .fillna("")
)

fig = go.Figure(
    go.Treemap(
        labels=df_tmp["country"],
        values=df_tmp["co2_per_capita"],
        parents=df_tmp["continent"],
        branchvalues="total",
        root_color="lightgrey",
        # textinfo = "label+ percent parent",
        texttemplate="%{label} <br> %{value} tonnes <br> %{percentRoot}",
        pathbar_textfont_size=15,
    )
)
# fig.show()


fig_scatter = px.scatter(
    df_ghg_country[df_ghg_country["year"] == 2016].dropna(
        subset="GDP per capita (current US$)"
    ),
    color="continent",
    size="population",
    color_continuous_scale=px.colors.cyclical.IceFire,
    # animation_frame= "year",
    # animation_group="country",
    hover_name="country",
    size_max=35,
    x="GDP per capita (current US$)",
    y="co2_per_capita",
    range_x=[1000, 70000],
    color_discrete_map={"Europe": "rgba(260,0,0,0.4)"},
)
# fig_scatter.show()


fig_scatter_slider = px.scatter(
df_ghg_country.dropna(subset = 'GDP per capita (current US$)'),
    color = 'continent',
    size= 'population', 
    color_continuous_scale=px.colors.cyclical.IceFire, 
    animation_frame= "year",
    animation_group="country",
    hover_name = 'country',
    size_max=35, 
    x='GDP per capita (current US$)',
    y="co2_per_capita",
    range_x =[1000,70000],
    color_discrete_map={"Europe": 'rgba(260,0,0,0.4)'},
)
# fig_scatter_slider.show()


color_discrete_map = {
    "Asia": "#ffffff",
    "Africa": "purple",
    "Europe": "pink",
    "Antarctica": "orange",
    "South America": "dark red",
    "Oceania": "blue",
    "North America": "yellow",
}

df_ghg_country['color_continent'] = df_ghg_country['continent'].map(color_discrete_map)

years = df_ghg_country['country'].unique()
title = html.H2('Who emits the most Greenhouse gas?')
container = html.Div(
                        [
                        html.Div(
                        [dbc.Label("Select Year"),
                        dcc.Dropdown(id='dropdown_year',
                             options=[{'value': x, 'label': x} for x in df_ghg_country['year'].unique()],

                        
                        )], className="mb-4"
                        ),
                    html.Div(
                        [dbc.Label("Select Continent"),
                        dcc.Checklist(id='dropdown_continent',
                        options=[{'value': x, 'label': x} for x in df_ghg_country['continent'].unique()],
                        )
                        ], className="mb-4"
                        )
                        ]
                    )

tab1 = dcc.Tab([dcc.Graph(id = "year0",figure = fig_scatter_slider )], label = "Animated Co2 per capita (tonnes) vs. GDP per capita")
tab2 = dcc.Tab([dcc.Graph(id="year1", figure= fig_scatter)], label= "Scatter Co2 per capita (tonnes) vs. GDP per capita")
tab3 = dcc.Tab([dcc.Graph(id="year2",figure= fig)], label="Treemap Co2 per capita")
tabs = dcc.Tabs([tab1, tab2, tab3])

layout = html.Div([title, tabs, container])

app = Dash(__name__)
app.layout = layout

server = app.server

@app.callback(
    # Set the input and output of the callback to link the dropdown to the graph
    # Output(component_id='year0',component_property='figure'),
    Output(component_id='year1', component_property='figure'),
    Output(component_id='year2', component_property='figure'),

    Input(component_id= 'dropdown_year', component_property='value'),
    [Input(component_id= 'dropdown_continent', component_property='value')]
)


def update_plot(year_, continent):
    if continent is None: 
        mask = (-1 == df_ghg_country['year'])
    else:
        mask = (year_ == df_ghg_country['year']) & (df_ghg_country['continent'].isin(continent))


    fig1 = px.scatter(
        df_ghg_country[mask].dropna(
            subset="GDP per capita (current US$)"
        ),
        color="continent",
        color_discrete_map = {
    "Asia": "teal",
    "Africa": "purple",
    "Europe": "pink",
    "Antarctica": "orange",
    "South America": "dark red",
    "Oceania": "blue",
    "North America": "yellow"
},
        size="population",
        color_continuous_scale=px.colors.cyclical.IceFire,
        hover_name="country",
        size_max=35,
        x="GDP per capita (current US$)",
        y="co2_per_capita",
        range_x=[1000, 70000],
    )
    if continent is None:
        mask = (-1 == df_ghg_total['year'])
    else:
        # continent+=['world']
        mask_year = (year_ == df_ghg_total['year'])
        mask_continent = (df_ghg_total['continent'].isin(continent) ) #& (~(df_ghg_total['country'].isin(continent[:-1])))
        mask = mask_year & mask_continent

        # mask = (year_ == df_ghg_total['year']) & (df_ghg_total['continent'].isin(continent)) # & (~(df_ghg_total['country'].isin(continent[:-1]))))
        # mask2 = (year_ == df_ghg_total['year']) & (df_ghg_total['country'].isin(continent[:-1]))
        # df_ghg_total[df_ghg_total.continent == 'world'] = df_ghg_total[mask2].co2_per_capita.sum()
        
    fig2 = go.Figure(go.Treemap(
        labels=df_ghg_total[mask]["country"],
        values=df_ghg_total[mask]["co2_per_capita"],
        parents=df_ghg_total[mask]["continent"],
        branchvalues="total",
        root_color="lightgrey",
        # textinfo = "label+ percent parent",
        texttemplate="%{label} <br> %{value} tonnes <br> %{percentRoot}",
        pathbar_textfont_size=15,
    )
)

    # locations = df_ghg_country['iso_code']
    # fig2 =  px.choropleth(df_ghg_country[mask], locations='iso_code', color='co2_per_capita', animation_frame='Year')
    # fig2.layout.coloraxis.colorbar.title = 'tCo2'
    return fig1, fig2


if __name__ == '__main__':
    # app.run_server(mode='inline', height=400, debug = False)
    app.run_server(height=400, debug = False)