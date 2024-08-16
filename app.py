#!/usr/bin/env python
# coding: utf-8

# In[1]:


import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd


# In[2]:


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


# In[3]:


file_paths = {'124_0770_IW3_VV': '124_0770_IW3_VV.csv',
              '124_0771_IW3_VV': '124_0771_IW3_VV.csv',
              '175_0303_IW1_VV': '175_0303_IW1_VV.csv',
              '175_0304_IW1_VV': '175_0304_IW1_VV.csv',
              '022_0770_IW1_VV': '022_0770_IW1_VV.csv',
              '073_0301_IW3_VV': '073_0301_IW3_VV.csv',
              '073_0302_IW3_VV': '073_0302_IW3_VV.csv'}


# In[4]:


all_data = pd.concat([load_and_reshape(path, label) for label, path in file_paths.items()], ignore_index=True)


# In[49]:


app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='map'),
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
                  title=f"Displacement Data for Point {point_id}",
                  markers=True)
    fig.update_layout(xaxis_title='Date', yaxis_title='Displacement (mm)')
    
    return fig, {'display': 'block'}


# In[50]:


if __name__ == '__main__':
    app.run_server(debug=True)


# In[ ]:




