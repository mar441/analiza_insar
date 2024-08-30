import os
from flask import Flask
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

def load_and_reshape(file_path, file_label):
    df = pd.read_csv(file_path)
    date_columns = [col for col in df.columns if col.isdigit()]

    reshaped_df = df.melt(id_vars=['pid', 'latitude', 'longitude', 'height'],
                          value_vars=date_columns,
                          var_name='timestamp',
                          value_name='displacement')
 
    reshaped_df['timestamp'] = pd.to_datetime(reshaped_df['timestamp'], format='%Y%m%d')
    reshaped_df = reshaped_df.dropna(subset=['displacement'])
    reshaped_df['file'] = file_label
    
    return reshaped_df

file_paths = {
    '124_0770_IW3_VV': '124_0770_IW3_VV.csv',
    '124_0771_IW3_VV': '124_0771_IW3_VV.csv',
    '175_0303_IW1_VV': '175_0303_IW1_VV.csv',
    '175_0304_IW1_VV': '175_0304_IW1_VV.csv',
    '022_0770_IW1_VV': '022_0770_IW1_VV.csv',
    '073_0301_IW3_VV': '073_0301_IW3_VV.csv',
    '073_0302_IW3_VV': '073_0302_IW3_VV.csv'
}

all_data = pd.concat([load_and_reshape(path, label) for label, path in file_paths.items()], ignore_index=True)

server = Flask(__name__)
app = dash.Dash(__name__, server=server)

app.layout = html.Div([
    dcc.Graph(id='map', style={'height': '80vh'}),  # Zwiększ wysokość mapy do 80% wysokości widoku
    html.Div(id='displacement-container', children=[
        dcc.Graph(id='displacement-graph')
    ], style={'display': 'none'})
])

@app.callback(
    Output('map', 'figure'),
    Input('map', 'id')
)
def update_map(_):
    fig = px.scatter_mapbox(
        all_data.drop_duplicates(subset=['pid']), 
        lat='latitude', 
        lon='longitude', 
        hover_name='pid', 
        color='file',
        zoom=5,
        height=600
    )

    min_lat = all_data['latitude'].min()
    max_lat = all_data['latitude'].max()
    min_lon = all_data['longitude'].min()
    max_lon = all_data['longitude'].max()

    fig.update_layout(mapbox_style="open-street-map", 
                      mapbox_center={"lat": (min_lat + max_lat) / 2, "lon": (min_lon + max_lon) / 2},
                      mapbox_zoom=5)

    fig.update_layout(mapbox_bounds={"west": min_lon - 0.05, "east": max_lon + 0.05, "south": min_lat - 0.05, 
                                     "north": max_lat + 0.05})


    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin={"r":0,"t":0,"l":0,"b":0}  
    )
    
    fig.update_layout(legend_title_text='File number') 
    return fig

@app.callback(
    [Output('displacement-graph', 'figure'),
     Output('displacement-container', 'style')],
    Input('map', 'clickData')
)
def display_displacement(clickData):
    if clickData is None:
        return {}, {'display': 'none'}
    
    point_id = clickData['points'][0]['hovertext']
    filtered_data = all_data[all_data['pid'] == point_id]

    fig = px.line(filtered_data, x='timestamp', y='displacement', 
                  title=f"Przemieszczenie dla punktu {point_id}",
                  markers=True)
    fig.update_layout(xaxis_title='Data', yaxis_title='Przemieszczenie(mm)')
    
    return fig, {'display': 'block'}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)