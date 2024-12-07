from shiny import App, render, ui, reactive
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# UI
app_ui = ui.page_fluid(
    ui.input_select(
        id='attribute', 
        label='Choose an attribute to create a choropleth map:', 
        choices=['cancer_all_sites', 'diabetes_related', 'below_poverty_level']
    ),
    ui.input_checkbox(
        id="show_buffer",
        label="Show Buffer Layer for Community Health Center ",
        value=False  
    ),
    ui.input_slider(
        id="buffer_distance",
        label="Buffer Distance (meters):",
        min=100,
        max=2000,
        value=500,
        step=100
    ),
    ui.output_plot("ts"),
    ui.output_table("subsetted_data_table")
)

# Server
def server(input, output, session):
    @reactive.calc
    def full_data():
        df = gpd.read_file("/Users/tsaili-ting/Uchicago/Year2/Y2Fall/Python2/python_final/chi_shp_dem.geojson")
        return df

    @reactive.calc
    def subsetted_data():
        df = full_data()
        selected_att = input.attribute.get()
        return df[["community_area_name", selected_att, "geometry"]]

    @reactive.calc
    def buffer_layer():
        point = gpd.read_file("/Users/tsaili-ting/Uchicago/Year2/Y2Fall/Python2/python_final/point.geojson")
        point_projected = point.to_crs(epsg=32616) 
        buffer_distance = input.buffer_distance.get()
        point_projected["buffer"] = point_projected.geometry.buffer(buffer_distance)
        buffer_gdf = point_projected.set_geometry("buffer")
        buffer_gdf = buffer_gdf.to_crs(full_data().crs)
        return buffer_gdf

    @render.plot
    def ts():
        main_df = subsetted_data()
        buffer_df = buffer_layer() if input.show_buffer.get() else None
        fig, ax = plt.subplots(1, 1, figsize=(3,6))
        main_df.plot(
            column=input.attribute.get(),
            cmap="Greens",
            edgecolor="lightgrey",
            legend=True,
            ax=ax
        )
        
        # Plot buffer layer
        if buffer_df is not None:
            buffer_df = buffer_df.to_crs(main_df.crs)
            buffer_df.plot(
                ax=ax,
                color="blue",
                alpha=0.2,
                edgecolor="red"  
            )

        ax.set_title(f"Choropleth Map of {input.attribute.get()}", fontsize=16)
        ax.axis("off")

        return fig
    
    @render.table
    def subsetted_data_table():
        df = subsetted_data()
        selected_att = input.attribute.get()
        return df[["community_area_name", selected_att]].sort_values(by = selected_att,ascending = False)
        
# App
app = App(app_ui, server)