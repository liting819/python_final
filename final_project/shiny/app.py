from shiny import App, render, ui, reactive
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# UI
app_ui = ui.page_fluid(
    ui.input_select(
        id='attribute', 
        label='Choose an attribute to create a choropleth map:', 
        choices=['Cancer (All Sites)', 'Diabetes-related', 'Below Poverty Level']
    ),
    ui.input_checkbox(
        id="show_buffer",
        label="Show Buffer Layer for ",
        value=False  # Default: Buffer layer off
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
    # Load the full dataset
    @reactive.calc
    def full_data():
        df = gpd.read_file("/Users/tsaili-ting/Uchicago/Year2/Y2Fall/Python2/final_project/chi_shp_dem.geojson")
        print("Column Names:", df.columns)  # Debugging: Print column names
        print("Main dataset CRS:", df.crs)  # Debugging CRS
        return df

    # Filter data based on input
    @reactive.calc
    def subsetted_data():
        df = full_data()
        selected_att = input.attribute.get()
        return df[["Community Area Name", selected_att, "geometry"]]

    @reactive.calc
    def buffer_layer():
        # Read point data
        point = gpd.read_file("/Users/tsaili-ting/Uchicago/Year2/Y2Fall/Python2/final_project/point.geojson")
        print("Original CRS (points):", point.crs)  # Debugging
        
        # Reproject to a projected CRS for accurate buffering
        point_projected = point.to_crs(epsg=32616)  # UTM Zone 16N for Chicago
        print("Projected CRS (points):", point_projected.crs)
        
        # Create buffer geometries in meters
        buffer_distance = input.buffer_distance.get()
        point_projected["buffer"] = point_projected.geometry.buffer(buffer_distance)
        
        # Create a new GeoDataFrame with the buffer as geometry
        buffer_gdf = point_projected.set_geometry("buffer")
        
        # Reproject back to the main dataset's CRS for alignment
        buffer_gdf = buffer_gdf.to_crs(full_data().crs)
        print("Buffer geometries (reprojected):", buffer_gdf.geometry.head())
        
        return buffer_gdf

    @render.plot
    def ts():
        # Get main and buffer datasets
        main_df = subsetted_data()
        buffer_df = buffer_layer() if input.show_buffer.get() else None

        # Ensure CRS alignment
        if buffer_df is not None:
            buffer_df = buffer_df.to_crs(main_df.crs)

        # Create plot
        fig, ax = plt.subplots(1, 1, figsize=(5, 5))
        
        # Plot main data
        main_df.plot(
            column=input.attribute.get(),
            cmap="Greens",
            edgecolor="lightgrey",
            legend=True,
            ax=ax
        )
        
        # Plot buffer layer
        if buffer_df is not None:
            buffer_df.plot(
                ax=ax,
                color="blue",
                alpha=0.2,
                edgecolor="red"  # Optional: Highlight buffer boundary
            )
        
        # Set title and remove axes
        ax.set_title(f"Choropleth Map of {input.attribute.get()}", fontsize=16)
        ax.axis("off")
        print(f"Plotted choropleth map for attribute: {input.attribute.get()}")
        if buffer_df is not None:
            print("Plotted buffer layer.")
        return fig

    # Render table
    @render.table
    def subsetted_data_table():
        df = subsetted_data()
        return (
            df[["Community Area Name", input.attribute.get()]]
            .reset_index(drop=True)
            .sort_values(by=input.attribute.get(), ascending=False)
        )

# App
app = App(app_ui, server)