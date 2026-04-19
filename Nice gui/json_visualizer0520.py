from nicegui import ui
import json
import numpy as np 
import plotly.graph_objects as go
import pandas as pd
import re
from datetime import datetime, timedelta

# Global variables to store the loaded data
df_hf = None
lf_data = None

async def load_json(e):
    """Load JSON file and store data globally"""
    global df_hf, lf_data
    
    try:
        # Read and parse JSON content
        file_content = e.content.read().decode('utf-8')
        data = json.loads(file_content)
        print('the json file is loaded')
        # Extract high-frequency column names
        hf_col = [item["Name"][:-1] + item["Axis"] for item in data["Header"].get("SignalListHFData")]
        
        # Parse initial timestamp and cycle counter
        tmp = data['Header'].get("Initial")["Time"]
        pattern = '(.*)T(.*)Z'
        init_time_stamp = re.search(pattern, tmp).groups()
        init_cyclecounter = data['Header'].get("Initial")['HFProbeCounter']
        dt = data['Header'].get('CycleTimeMs')
        
        # Initialize DataFrames
        lf_data = pd.DataFrame(columns=['HFProbeCounter', 'timestamp', 'address', 'value_type', 'value'])
        df_hf = pd.DataFrame()
        
        # Process payload data
        for payload_item in data["Payload"]:
            lf_item = payload_item.get("LFData")
            hf_item = payload_item.get("HFData")
            if lf_item:
                for item in lf_item:
                    lf_data = pd.concat([lf_data, pd.DataFrame([item])], ignore_index=True)
            if hf_item:
                df_hf = pd.concat([df_hf, pd.DataFrame.from_dict(hf_item)], axis=0, ignore_index=True)
        
        # Set column names for high-frequency data
        df_hf.columns = hf_col

        df_hf['timespan'] = df_hf.CYCLCycle.apply(lambda x: 
            datetime.strptime(f'{init_time_stamp[0]} {init_time_stamp[1]}', '%Y-%m-%d %H:%M:%S.%f') + 
            timedelta(milliseconds=dt * (x - init_cyclecounter)))
        
        df_hf['ENC_Vel|X1'] = differential(df_hf['timespan'],df_hf['ENC_POS|X1']) 
        # df_hf['ENC_Vel|Y1'] = differential(df_hf['timespan'],df_hf['ENC_POS|Y1']) 
        # df_hf['ENC_Vel|Z1'] = differential(df_hf['timespan'],df_hf['ENC_POS|Z1']) 
        df_hf['ENC_Acc|X1'] = differential(df_hf['timespan'],df_hf['ENC_Vel|X1']) 
        # df_hf['ENC_Acc|Y1'] = differential(df_hf['timespan'],df_hf['ENC_Vel|Y1']) 
        # df_hf['ENC_Acc|Z1'] = differential(df_hf['timespan'],df_hf['ENC_Vel|Z1']) 

        # Update dropdown options
        x_dropdown.options = list(df_hf.columns)
        y_dropdown.options = list(df_hf.columns)  # Use df_hf columns for both x and y
        y_dropdown.props['multiple'] = True  # Enable multiple selections for y_dropdown
        
        # Set default selections
        if len(df_hf.columns) > 0:
            x_dropdown.value = 'timespan'  # Default to timespan for x-axis
            y_dropdown.value = [df_hf.columns[0]]  # Default to first signal for y-axis
            
        # Show the plot section
        plot_container1.visible = True
        plot_container2.visible = True
        plot_container3.visible = True
        status_label.text = f"File loaded successfully. HF columns: {', '.join(df_hf.columns)}"
        
        # Trigger initial plot
        update_plot()
        
    except json.JSONDecodeError:
        status_label.text = "Error: Invalid JSON file."
        plot_container1.visible = False
        plot_container2.visible = False
        plot_container3.visible = False
    
    except Exception as e:
        status_label.text = f"Error: {str(e)}"
        plot_container1.visible = False
        plot_container2.visible = False
        plot_container3.visible = False
        
def differential(time_span,data):
    if len(data) < 1:
        return []
    time_numeric = (time_span - time_span.iloc[0]).dt.total_seconds().values
    
    dif_data = np.zeros(len(data))
    for i in range(len(data)-1):
        dt = time_numeric[i+1] - time_numeric[i]
        dif_data[i] = (data.iloc[i+1]-data.iloc[i])/dt
        # dif_data[i] = (data[i+1]-data[i])/(time_numerical[i+1]-time_numerical[i])
        #dif_data[-1] = (data[-1]-data[-2])/(time_span[-1]-time_span[-2])
    if len(data) > 1 :
        dif_data[-1] = dif_data[-2]  
    else:
        dif_data[-1] = 0
            
    return dif_data

def update_plot():
    """Update the plots based on selected columns"""
    global df_hf, lf_data
    
    if df_hf is None or not x_dropdown.value or not y_dropdown.value:
        status_label.text = "No data loaded or axes not selected."
        return
    
    try:
        # Clear existing plots
        plot_container1.clear()
        plot_container2.clear()
        plot_container3.clear()
        
        # Get selected y-axis columns (up to 3)
        selected_y_columns = y_dropdown.value if isinstance(y_dropdown.value, list) else [y_dropdown.value]
        selected_y_columns = selected_y_columns[:3]  # Limit to 3 columns
        
        # Create plots for each selected y-column
        for i, y_col in enumerate(selected_y_columns):
            # Select the appropriate container
            container = [plot_container1, plot_container2, plot_container3][i]
            
            # Create a scatter plot
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_hf[x_dropdown.value],
                y=df_hf[y_col],
                mode='markers',
                marker=dict(
                    size=8,
                    color=['blue', 'green', 'red'][i],  # Different colors for each plot
                    opacity=0.7
                )
            ))
            
            # Update layout
            fig.update_layout(
                title=f"{y_col} vs {x_dropdown.value}",
                xaxis_title=x_dropdown.value,
                yaxis_title=y_col,
                template="plotly_white"
            )
            
            # Add the plot and statistics to the container
            with container:
                ui.plotly(fig).classes('w-full h-64')
                
                # Add basic statistics
                with ui.card().classes('w-full'):
                    ui.label('Basic Statistics:').classes('text-lg font-bold')
                    with ui.row():
                        with ui.column():
                            ui.label(f"X: {x_dropdown.value}")
                            ui.label(f"Min: {df_hf[x_dropdown.value].min():.2f}")
                            ui.label(f"Max: {df_hf[x_dropdown.value].max():.2f}")
                            ui.label(f"Mean: {df_hf[x_dropdown.value].mean():.2f}")
                        with ui.column():
                            ui.label(f"Y: {y_col}")
                            ui.label(f"Min: {df_hf[y_col].min():.2f}")
                            ui.label(f"Max: {df_hf[y_col].max():.2f}")
                            ui.label(f"Mean: {df_hf[y_col].mean():.2f}")
        
        # Hide unused containers
        for i in range(len(selected_y_columns), 3):
            container = [plot_container1, plot_container2, plot_container3][i]
            container.clear()
            with container:
                ui.label("Select additional Y-axis column to display plot").classes('text-gray-500')
        
    except Exception as e:
        for container in [plot_container1, plot_container2, plot_container3]:
            container.clear()
            with container:
                ui.label(f"Error generating plot: {str(e)}").classes('text-red-500')

# Main UI layout
with ui.card().classes('w-full max-w-4xl mx-auto'):  # Increased max-width for better layout
    ui.label('JSON Data Visualizer').classes('text-2xl font-bold')
    
    # File upload section
    with ui.card().classes('w-full'):
        ui.label('Step 1: Load JSON File').classes('text-lg font-bold')
        ui.upload(on_upload=load_json, label='Upload JSON file', auto_upload=True).props('accept=.json')
        status_label = ui.label('No file loaded').classes('text-gray-500')
    
    # Plot configuration
    with ui.card().classes('w-full'):
        ui.label('Step 2: Select Data to Plot').classes('text-lg font-bold')
        with ui.row():
            with ui.column():
                ui.label('X-Axis:')
                x_dropdown = ui.select(options=[], on_change=update_plot).classes('w-full')
            with ui.column():
                ui.label('Y-Axis (Select up to 3):')
                y_dropdown = ui.select(options=[], on_change=update_plot, multiple=True).classes('w-full')
    
    # Plot containers (initially hidden)
    ui.label('Plots:').classes('text-lg font-bold mt-4')
    plot_container1 = ui.card().classes('w-full')
    plot_container2 = ui.card().classes('w-full')
    plot_container3 = ui.card().classes('w-full')
    plot_container1.visible = False
    plot_container2.visible = False
    plot_container3.visible = False

ui.run(title="JSON Data Visualizer")
