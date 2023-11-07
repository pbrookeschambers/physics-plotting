import base64
import io
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import qoplots.qoplots as qp
import re
from contextlib import nullcontext
import logging
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s",
)
import time

from data import DataSeries, FigureProperties, LegendEntry, Line, LineOfBestFit, Marker
from constants import MarkerStyles, LineStyles
from fitting import fit, get_fitted_data
from text import process_fit, process_units
from errors import handle_data_error, handle_fit_error, handle_latex_error

def format_elapsed_time(t_ns: float):
    # time is in nanoseconds, format in an appropriate unit to 3 significant figures (NOT 3 decimal places)
    timestring = None
    unit = None
    if t_ns < 1e3:
        # return f"{t_ns:#.3g} ns"
        timestring = f"{t_ns:#.3g}"
        unit = "ns"
    elif t_ns < 1e6:
        # return f"{t_ns / 1e3:#.3g} \xb5s"
        timestring = f"{t_ns / 1e3:#.3g}"
        unit = "\xb5s"
    elif t_ns < 1e9:
        # return f"{t_ns / 1e6:#.3g} ms"
        timestring = f"{t_ns / 1e6:#.3g}"
        unit = "ms"
    elif t_ns < 60e9:
        # return f"{t_ns / 1e9:#.3g} s"
        timestring = f"{t_ns / 1e9:#.3g}"
        unit = "s"
    elif t_ns < 60e9 * 60:
        # return as ##m ##s
        m = int(t_ns / 60e9)
        s = int((t_ns - m * 60e9) / 1e9)
        return f"{m}m {s:0>2d}s"
    else:
        # return as ##h ##m ##s. I really hope we never need this
        h = int(t_ns / 3600e9)
        m = int((t_ns - h * 3600e9) / 60e9)
        s = int((t_ns - h * 3600e9 - m * 60e9) / 1e9)
        return f"{h}h {m:0>2d}m {s:0>2d}s"

    if timestring.endswith("."):
        timestring = timestring[:-1]
    return timestring + " " + unit

logging.info("Starting App")

# Setup ---------------------------------------

st.set_page_config(
    page_title="Plotting",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""<style>
    div[data-testid="stColorBlock"] {
        margin: auto;
        width: 50%;
    }
    div:has(> div[data-testid="stColorBlock"]) {
        width: 100%;
    }
    div.stSpinner > div {
        display: flex;
        align-items: center;
        justify-content: center;
    }
</style>""",
    unsafe_allow_html=True,)

def set_theme(theme):
    logging.info(f"Setting theme to {theme}...")
    start = time.perf_counter_ns()
    qp.init(theme.lower().replace(" ", "_"), "light", "report")
    end = time.perf_counter_ns()
    logging.info(f"Theme set in {format_elapsed_time(end - start)}")


def change_active_series(name: str):
    for s in st.session_state.data_series:
        if s.name == name:
            st.session_state.active_series = s
            break
    else:
        raise ValueError(f"Series with name {name} not found.")

def extract_data(text: str) -> np.array:
    # data could be comma separated, space separated, tab separated, or new line separated
    separated = re.split(r"[,\s\t\n]+", text)
    if len(separated) == 1:
        raise ValueError("No data found.")
    try:
        data = np.array([float(x) for x in separated])
        return data
    except ValueError:
        raise ValueError("Data must be numeric.")

def add_new_data():
    try:
        x_data = extract_data(st.session_state.new_x_data.strip())
        y_data = extract_data(st.session_state.new_y_data.strip())
    except Exception as e:
        st.error(handle_data_error(e))
        return
    if len(x_data) != len(y_data):
        st.error("The number of $x$-values must match the number of $y$-values.")
        logging.error(f"Number of x-values ({len(x_data)}) does not match number of y-values ({len(y_data)}).")
        return
    try:
        x_data = np.array([float(x) for x in x_data])
        y_data = np.array([float(y) for y in y_data])
    except ValueError:
        st.error("The data must be numeric.")
        logging.error("Data is not numeric.")
        return
    new_name = st.session_state.new_name
    # check if the name is already taken
    for s in st.session_state.data_series:
        if s.name == new_name:
            st.error("A data series with that name already exists.")
            logging.error(f"Data series with name {new_name} already exists.")
            return
    # clear the new data
    st.session_state.new_x_data = ""
    st.session_state.new_y_data = ""
    # create the new data series
    s = DataSeries(
        name = new_name,
        x = x_data,
        y = y_data,
        marker = Marker(
            style = MarkerStyles.POINT,
            color = "#000000",
            size = 10,
            auto_color=True,
        ),
        line = Line(
            style = LineStyles.SOLID,
            color = "#000000",
            width = 1,
            auto_color=True,
        ),
        legend_entry = LegendEntry(
            show = True,
            label = new_name,
        ),
        line_of_best_fit = LineOfBestFit(
            show = False,
            line = Line(
                style=LineStyles.DASHED,
                color="#000000",
                width=1,
            ),
            fit_type = "Linear",
            fit_params = [1, 0],
            auto_color=True,
            legend_entry = LegendEntry(
                show = False,
                label = "Fit",
            )
        ),
    )
    st.session_state.data_series.append(s)

def delete_series(s_name: str):
    # remove the series. If it is the active series, set the active series to the first (or None)
    for s in st.session_state.data_series:
        if s.name == s_name:
            st.session_state.data_series.remove(s)
            break
    if st.session_state.active_series.name == s_name:
        if len(st.session_state.data_series) > 0:
            st.session_state.active_series = st.session_state.data_series[0]
        else:
            st.session_state.active_series = None

def update_fit(series: DataSeries, fit_type: str, show_fit: bool):
    series.line_of_best_fit.attempt_plot = True
    # fit the data
    try:
        series.line_of_best_fit.fit_params = fit(fit_type, series.x, series.y)
    except Exception as e:
        st.error(handle_fit_error(e, fit_type, series.name))
        series.line_of_best_fit.attempt_plot = False
    # update the fit type
    series.line_of_best_fit.fit_type = fit_type
    # update showing
    series.line_of_best_fit.show = show_fit

def update_data(series: DataSeries, key: str):
    # has format {"edited_rows": {row: {column: value}}}
    # will only ever have one row and one column
    changed = st.session_state[key]
    for row, ch in changed["edited_rows"].items():
        for column, value in ch.items():
            if column == "0":
                try:
                    if value is None:
                        series.x[row] = 0
                    else:
                        series.x[row] = float(value)
                except Exception as e:
                    st.error("The data must be numeric.")
                    return
            elif column == "1":
                try:
                    if value is None:
                        series.y[row] = 0
                    else:
                        series.y[row] = float(value)
                except Exception as e:
                    st.error("The data must be numeric.")
                    return
            else:
                raise ValueError(f"Invalid column index: {column}")
    for row in changed["deleted_rows"]:
        series.x = np.delete(series.x, row)
        series.y = np.delete(series.y, row)
    for row in changed["added_rows"]:
        # added rows are always at the end
        if "0" not in row:
            series.x = np.append(series.x, 0)
        else:
            series.x = np.append(series.x, float(row["0"]))
        if "1" not in row:
            series.y = np.append(series.y, 0)
        else:
            series.y = np.append(series.y, float(row["1"]))
        



# session state variables
if "figure_properties" not in st.session_state:
    st.session_state.figure_properties = FigureProperties.default()
if "active_series" not in st.session_state:
    st.session_state.active_series = None
if "data_series" not in st.session_state:
    st.session_state.data_series = [
        # DataSeries(
        #     name="Sine",
        #     x=np.linspace(-10, 10, 100),
        #     y=np.sin(np.linspace(-10, 10, 100)),
        #     marker=Marker(
        #         style=MarkerStyles.NONE,
        #         color="#ff0000",
        #         size=10,
        #     ),
        #     line=Line(
        #         style=LineStyles.SOLID,
        #         color="#ff0000",
        #         width=1,
        #     ),
        #     legend_entry=LegendEntry(
        #         show=True,
        #         label=r"$y = \sin(x)$",
        #     ),
        #     line_of_best_fit=LineOfBestFit(
        #         show=False,
        #         line = Line(
        #             style=LineStyles.DASHED,
        #             color="#000000",
        #             width=1,
        #         ),
        #         fit_type="Linear",
        #         fit_params=[1, 0],
        #         legend_entry=LegendEntry(
        #             show=False,
        #             label="Fit",
        #         )
        #     ),
        # ),
        # DataSeries(
        #     name="Cosine",
        #     x=np.linspace(-10, 10, 100),
        #     y=np.cos(np.linspace(-10, 10, 100)),
        #     marker=Marker(
        #         style=MarkerStyles.POINT,
        #         color="#0000ff",
        #         size=10,
        #     ),
        #     line=Line(
        #         style=LineStyles.DASHED,
        #         color="#0000ff",
        #         width=1,
        #     ),
        #     legend_entry=LegendEntry(
        #         show=True,
        #         label=r"$y = \cos(x)$",
        #     ),
        #     line_of_best_fit=LineOfBestFit(
        #         show=False,
        #         line = Line(
        #             style=LineStyles.DASHED,
        #             color="#000000",
        #             width=1,
        #         ),
        #         fit_type="Linear",
        #         fit_params=[1, 0],
        #         legend_entry=LegendEntry(
        #             show=False,
        #             label="Fit",
        #         )
        #     ),
        # ),
    ]

# Sidebar -------------------------------------



st.sidebar.title("Options")
st.sidebar.header("Data")
if len(st.session_state.data_series) == 0:
    st.sidebar.markdown("*Add a data series to get started.*")
else:

    if st.session_state.active_series is None:
        st.session_state.active_series = st.session_state.data_series[0]
    # active series
    if len(st.session_state.data_series) > 1:
        st.sidebar.selectbox(
            "Data Series",
            [s.name for s in st.session_state.data_series],
            index=0,
            key="active_series_name",
            on_change=lambda: change_active_series(st.session_state.active_series_name),
        )
    with st.sidebar.expander("**Data Series**", expanded=False):
        # marker
        st.subheader("Marker")
        # possible matplotlib markers
        marker_style = st.selectbox(
            "Marker",
            list(MarkerStyles),
            key="marker",
            format_func=lambda x: x.name.replace("_", " ").title(),
            # default to the marker style of the selected series
            index=st.session_state.active_series.marker.style.index,
            on_change=lambda: setattr(
                st.session_state.active_series.marker, "style", st.session_state.marker
            ),
        )
        if marker_style != MarkerStyles.NONE:
            # auto colour?
            marker_auto_color = st.toggle(
                "Use Automatic Colour",
                st.session_state.active_series.marker.auto_color,
                key="marker_auto_color",
                on_change=lambda: setattr(
                    st.session_state.active_series.marker,
                    "auto_color",
                    st.session_state.marker_auto_color,
                ),
            )
            if not marker_auto_color:
            # marker colour
                st.color_picker(
                    "Marker Color",
                    st.session_state.active_series.marker.color,
                    key="marker_color",
                    on_change=lambda: setattr(
                        st.session_state.active_series.marker,
                        "color",
                        st.session_state.marker_color,
                    ),
                )
            # marker size
            st.slider(
                "Marker Size",
                0.0,
                20.0,
                float(st.session_state.active_series.marker.size),
                step = 0.2,
                key="marker_size",
                on_change=lambda: setattr(
                    st.session_state.active_series.marker,
                    "size",
                    st.session_state.marker_size,
                ),
            )

        # line
        st.subheader("Line")
        # line style
        st.selectbox(
            "Line Style",
            list(LineStyles),
            key="line_style",
            format_func=lambda x: x.name.replace("_", " ").title(),
            # default to the marker style of the selected series
            index=st.session_state.active_series.line.style.index,
            on_change=lambda: setattr(
                st.session_state.active_series.line,
                "style",
                st.session_state.line_style,
            ),
        )
        if st.session_state.line_style != LineStyles.NONE:
            # auto colour?
            line_auto_color = st.toggle(
                "Use Automatic Colour",
                st.session_state.active_series.line.auto_color,
                key="line_auto_color",
                on_change=lambda: setattr(
                    st.session_state.active_series.line,
                    "auto_color",
                    st.session_state.line_auto_color,
                ),
            )
            if not line_auto_color:
                # line colour
                st.color_picker(
                    "Line Color",
                    st.session_state.active_series.line.color,
                    key="line_color",
                    on_change=lambda: setattr(
                        st.session_state.active_series.line,
                        "color",
                        st.session_state.line_color,
                    ),
                )
            # line width
            st.slider(
                "Line Width",
                1.0,
                5.0,
                float(st.session_state.active_series.line.width),
                step=0.1,
                key="line_width",
                on_change=lambda: setattr(
                    st.session_state.active_series.line,
                    "width",
                    st.session_state.line_width,
                ),
            )

        # legend
        st.subheader("Legend")
        # show in legend?
        st.toggle(
            "Show in Legend",
            True,
            key="show_in_legend",
            on_change=lambda: setattr(
                st.session_state.active_series.legend_entry,
                "show",
                st.session_state.show_in_legend,
            ),
        )
        # label
        if st.session_state.show_in_legend:
            st.text_input(
                "Legend Label",
                st.session_state.active_series.legend_entry.label,
                key="legend_label",
                on_change=lambda: setattr(
                    st.session_state.active_series.legend_entry,
                    "label",
                    st.session_state.legend_label,
                ),
            )
    # Line of best fit
    st.sidebar.toggle(
        "Line of Best Fit",
        st.session_state.active_series.line_of_best_fit.show,
        key="show_line_of_best_fit",
        on_change=lambda: update_fit(
            st.session_state.active_series, 
            st.session_state.active_series.line_of_best_fit.fit_type, 
            st.session_state.show_line_of_best_fit
        ),
    )
    if st.session_state.active_series.line_of_best_fit.show:
        with st.sidebar.expander("Line of Best Fit", expanded=False):
            st.subheader("Fit")
            # fit type
            st.selectbox(
                "Fit Type",
                ["Linear", "Quadratic", "Cubic", "Exponential", "Logarithmic", "Sinusoidal"],
                key="fit_type",
                index=0,
                on_change=lambda: update_fit(
                    st.session_state.active_series, st.session_state.fit_type, st.session_state.show_line_of_best_fit
                ),

            )
            # show the equation of the selected type of fit
            st.write("Fit Equation")
            match st.session_state.fit_type:
                case "Linear":
                    st.latex(r"y = ax + b")
                case "Quadratic":
                    st.latex(r"y = ax^2 + bx + c")
                case "Cubic":
                    st.latex(r"y = ax^3 + bx^2 + cx + d")
                case "Exponential":
                    st.latex(r"y = a\text{e}^{bx} + c")
                case "Sinusoidal":
                    st.latex(r"y = a\sin(bx + c) + d")
                case "Logarithmic":
                    st.latex(r"y = a\ln(bx) + c")
                case _:
                    st.error("Invalid fit type.")
            st.subheader("Line")
            # line style
            st.selectbox(
                "Line Style",
                list(LineStyles),
                key="line_of_best_fit_style",
                format_func=lambda x: x.name.replace("_", " ").title(),
                # default to the marker style of the selected series
                index=st.session_state.active_series.line_of_best_fit.line.style.index,
                on_change=lambda: setattr(
                    st.session_state.active_series.line_of_best_fit.line,
                    "style",
                    st.session_state.line_of_best_fit_style,
                ),
            )
            if st.session_state.line_of_best_fit_style != LineStyles.NONE:
                # auto colour?
                line_of_best_fit_auto_color = st.toggle(
                    "Use Automatic Colour",
                    st.session_state.active_series.line_of_best_fit.line.auto_color,
                    key="line_of_best_fit_auto_color",
                    on_change=lambda: setattr(
                        st.session_state.active_series.line_of_best_fit.line,
                        "auto_color",
                        st.session_state.line_of_best_fit_auto_color,
                    ),
                )
                if not line_of_best_fit_auto_color:
                    # line colour
                    st.color_picker(
                        "Line Color",
                        st.session_state.active_series.line_of_best_fit.line.color,
                        key="line_of_best_fit_color",
                        on_change=lambda: setattr(
                            st.session_state.active_series.line_of_best_fit.line,
                            "color",
                            st.session_state.line_of_best_fit_color,
                        ),
                    )
                # line width
                st.slider(
                    "Line Width",
                    1.0,
                    5.0,
                    float(st.session_state.active_series.line_of_best_fit.line.width),
                    step=0.1,
                    key="line_of_best_fit_width",
                    on_change=lambda: setattr(
                        st.session_state.active_series.line_of_best_fit.line,
                        "width",
                        st.session_state.line_of_best_fit_width,
                    ),
                )
            # legend
            st.subheader("Legend")
            # show in legend?
            st.toggle(
                "Show in Legend",
                st.session_state.active_series.line_of_best_fit.legend_entry.show,
                key="show_line_of_best_fit_in_legend",
                on_change=lambda: setattr(
                    st.session_state.active_series.line_of_best_fit.legend_entry,
                    "show",
                    st.session_state.show_line_of_best_fit_in_legend,
                ),
            )
            if st.session_state.show_line_of_best_fit_in_legend:
                # label
                st.text_input(
                    "Legend Label",
                    st.session_state.active_series.line_of_best_fit.legend_entry.label,
                    key="line_of_best_fit_legend_label",
                    on_change=lambda: setattr(
                        st.session_state.active_series.line_of_best_fit.legend_entry,
                        "label",
                        st.session_state.line_of_best_fit_legend_label,
                    ),
                )



st.sidebar.divider()
st.sidebar.header("Figure")

with st.sidebar.expander("$x$ Axis", expanded=False):
    # x axis limits
    col1, col2 = st.columns(2)
    with col1:
        x_min = st.text_input(
            "$x$ Min", 
            "" if st.session_state.figure_properties.x_axis.min is None else st.session_state.figure_properties.x_axis.min, 
            key="x_min",
            help = "Leave blank for automatic scaling.",
            on_change = lambda: setattr(
                st.session_state.figure_properties.x_axis,
                "min",
                None if st.session_state.x_min == "" else float(st.session_state.x_min),
            ),
        )
    with col2:
        # x_max = st.number_input("$x$ Max", -100, 100, 10, key = "x_max")
        x_max = st.text_input(
            "$x$ Max", 
            "" if st.session_state.figure_properties.x_axis.max is None else st.session_state.figure_properties.x_axis.max, 
            key="x_max",
            help = "Leave blank for automatic scaling.",
            on_change = lambda: setattr(
                st.session_state.figure_properties.x_axis,
                "max",
                None if st.session_state.x_max == "" else float(st.session_state.x_max),
            ),
        )
    # x axis label
    st.text_input(
        "$x$ Axis Label", 
        st.session_state.figure_properties.x_axis.label,
        key="x_label",
        on_change = lambda: setattr(
            st.session_state.figure_properties.x_axis,
            "label",
            st.session_state.x_label,
        ),
    )
    # font size
    st.slider(
        "Font Size", 
        6, 
        32, 
        int(st.session_state.figure_properties.x_axis.font_size), 
        key="font_size_x",
        on_change = lambda: setattr(
            st.session_state.figure_properties.x_axis,
            "font_size",
            st.session_state.font_size_x,
        ),
    )
with st.sidebar.expander("$y$ Axis", expanded=False):
    # y axis limits
    col1, col2 = st.columns(2)
    with col1:
        # y_min = st.number_input("$y$ Min", -100, 100, -10, key = "y_min")
        y_min = st.text_input(
            "$y$ Min", 
            "" if st.session_state.figure_properties.y_axis.min is None else st.session_state.figure_properties.y_axis.min,
            key="y_min",
            help = "Leave blank for automatic scaling.",
            on_change = lambda: setattr(
                st.session_state.figure_properties.y_axis,
                "min",
                None if st.session_state.y_min == "" else float(st.session_state.y_min),
            ),
        )
    with col2:
        # y_max = st.number_input("$y$ Max", -100, 100, 10, key = "y_max")
        y_max = st.text_input(
            "$y$ Max", 
            "" if st.session_state.figure_properties.y_axis.max is None else st.session_state.figure_properties.y_axis.max,
            key="y_max",
            help = "Leave blank for automatic scaling.",
            on_change = lambda: setattr(
                st.session_state.figure_properties.y_axis,
                "max",
                None if st.session_state.y_max == "" else float(st.session_state.y_max),
            ),
        )
    # y axis label
    st.text_input(
        "$y$ Axis Label", 
        st.session_state.figure_properties.y_axis.label, 
        key="y_label",
        on_change = lambda: setattr(
            st.session_state.figure_properties.y_axis,
            "label",
            st.session_state.y_label,
        ),
    )
    # font size
    st.slider(
        "Font Size", 
        6, 
        32, 
        int(st.session_state.figure_properties.y_axis.font_size), 
        key="font_size_y",
        on_change = lambda: setattr(
            st.session_state.figure_properties.y_axis,
            "font_size",
            st.session_state.font_size_y,
        ),
    )
with st.sidebar.expander("Title", expanded=False):
    # title
    st.text_input(
        "Title", 
        st.session_state.figure_properties.title.text, 
        key="title",
        on_change = lambda: setattr(
            st.session_state.figure_properties.title,
            "text",
            st.session_state.title,
        ),
    )
    # font size
    st.slider(
        "Font Size", 
        6, 
        32, 
        int(st.session_state.figure_properties.title.font_size),
        key="font_size_title",
        on_change = lambda: setattr(
            st.session_state.figure_properties.title,
            "font_size",
            st.session_state.font_size_title,
        ),
    )
with st.sidebar.expander("Legend", expanded=False):
    # position
    show_legend = st.toggle("Show Legend", True, key="show_legend")
    if show_legend:
        positions = [
                "Best",
                "Upper Right",
                "Upper Left",
                "Lower Left",
                "Lower Right",
                "Right",
                "Center Left",
                "Center Right",
                "Lower Center",
                "Upper Center",
                "Center",
            ]
        st.selectbox(
            "Position",
            positions,
            key="legend_position",
            index = positions.index(st.session_state.figure_properties.legend.position),
            on_change = lambda: setattr(
                st.session_state.figure_properties.legend,
                "position",
                st.session_state.legend_position,
            ),
        )
        # font size
        st.slider(
            "Font Size", 
            6, 
            32, 
            int(st.session_state.figure_properties.legend.font_size),
            key="font_size_legend",
            on_change = lambda: setattr(
                st.session_state.figure_properties.legend,
                "font_size",
                st.session_state.font_size_legend,
            ),
        )
        # use automatic colour?
        st.toggle(
            "Use Automatic Colour",
            st.session_state.figure_properties.legend.auto_color,
            key="legend_auto_color",
            on_change=lambda: setattr(
                st.session_state.figure_properties.legend,
                "auto_color",
                st.session_state.legend_auto_color,
            ),
        )
        if not st.session_state.figure_properties.legend.auto_color:
            # legend background colour
            st.color_picker(
                "Background Color", 
                st.session_state.figure_properties.legend.background_color,
                key="legend_background_color",
                on_change=lambda: setattr(
                    st.session_state.figure_properties.legend,
                    "background_color",
                    st.session_state.legend_background_color,
                ),
            )
            # opacity
            st.slider(
                "Opacity", 
                0.0, 
                1.0, 
                float(st.session_state.figure_properties.legend.opacity),
                step = 0.05,
                key="legend_opacity",
                on_change=lambda: setattr(
                    st.session_state.figure_properties.legend,
                    "opacity",
                    st.session_state.legend_opacity,
                ),
            )
# background colour
# st.sidebar.color_picker("Background Color", "#ffffff", key="background_color")
themes = [
    "Newcastle",
    "Rose Pine",
    "Nord",
    "Twilight",
    "Catppuccin"
]
st.sidebar.selectbox(
    "Theme",
    themes,
    index = themes.index(st.session_state.figure_properties.theme),
    key="theme",
    on_change = lambda: setattr(
        st.session_state.figure_properties,
        "theme",
        st.session_state.theme,
    ),
)
st.sidebar.divider()
st.sidebar.header("File")
# file format
formats = [
        "PDF",
        "PNG",
        "SVG",
        "PS",
        "EPS",
    ]
st.sidebar.selectbox(
    "File Format",
    formats,
    key="file_format",
    index = formats.index(st.session_state.figure_properties.file_type.upper()),
    on_change = lambda: setattr(
        st.session_state.figure_properties,
        "file_type",
        st.session_state.file_format.upper(),
    ),
)
# file name
st.sidebar.text_input(
    "File Name", 
    st.session_state.figure_properties.filename,
    key="file_name", 
    help = "Do not include the file extension.",
    on_change = lambda: setattr(
        st.session_state.figure_properties,
        "filename",
        st.session_state.file_name,
    ),
)
# # download
# st.sidebar.button("Download", key="download", type = "primary")


# Main ----------------------------------------

plot_col, data_col = st.columns([0.6, 0.4])

plot_col.header("Plot")

data_col.header("Data")

with data_col:
    current_data, new_data = st.tabs(["Current Data", "Add New Data"])
    with current_data:
        if len(st.session_state.data_series) == 0:
            st.markdown("No data series added. Add a data series to get started.")
        else:
            expanders = []
            for s in st.session_state.data_series:
                if len(st.session_state.data_series) == 1:
                    expanders.append(nullcontext())
                else:
                    expanders.append(st.expander(s.name, expanded=False))
                with expanders[-1]:
                    left, right = st.columns(2)
                    name = st.text_input(
                        "Name", 
                        s.name, 
                        key=f"{s.name}_name", 
                        on_change=lambda: setattr(
                            s, "name", st.session_state[f"{s.name}_name"]
                        ),
                    )
                    data = np.array([s.x, s.y]).T
                    st.data_editor(
                        data, 
                        use_container_width=True, 
                        key = f"{s.name}_data",
                        on_change=update_data,
                        args=(s, f"{s.name}_data"),
                        column_config = {"0": "x", "1": "y"},
                        num_rows="dynamic"
                    )
                    # delete button
                    st.button(
                        "🗑️ Delete Series", 
                        key=f"{s.name}_delete", 
                        type = "primary",
                        on_click=delete_series,
                        args = (s.name,),
                    )
    with new_data:
        # new data name
        new_name = st.text_input("Name", f"Data Series {len(st.session_state.data_series) + 1}", key="new_name")
        new_x, new_y = st.columns(2)
        with new_x:
            x_data = st.text_area(
                "X Data", 
                key="new_x_data",
                help = "Paste your $x$-data here, with each value on a new line. \nDo not include the header row.",
                height = 300,
            )
        with new_y:
            y_data = st.text_area(
                "Y Data", 
                key="new_y_data",
                help = "Paste your $y$-data here, with each value on a new line. \nDo not include the header row.",
                height = 300,
            )
        # add button
        st.button(
            "Add Data", 
            key="add_data",
            on_click = add_new_data
        )

set_theme(st.session_state.theme)

# plot

with plot_col:
    with st.spinner("Generating Plot"):
        # time.sleep(20)
        if len(st.session_state.data_series) > 0:
            logging.debug("Creating empty figure")
            fig, ax = plt.subplots()
            logging.debug("Plotting data")
            start = time.perf_counter_ns()
            for s in st.session_state.data_series:
                x_data = s.x
                y_data = s.y
                legend = {
                    "label": process_units(s.legend_entry.label),
                } if s.legend_entry.show else {}
                marker = {
                    "marker": s.marker.style.value,
                    "markersize": s.marker.size,
                }
                if not s.marker.auto_color:
                    marker["markerfacecolor"] = s.marker.color
                    marker["markeredgecolor"] = s.marker.color
                line = {
                    "linestyle": s.line.style.value,
                    "linewidth": s.line.width,
                }
                if not s.line.auto_color:
                    line["color"] = s.line.color
                ax.plot(
                    x_data,
                    y_data,
                    **legend,
                    **marker,
                    **line,
                )
                # line of best fit
                if s.line_of_best_fit.show and s.line_of_best_fit.attempt_plot:
                    x_temp = np.linspace(x_data.min(), x_data.max(), max(100, len(x_data)))
                    y_temp = get_fitted_data(x_temp, s.line_of_best_fit.fit_type, s.line_of_best_fit.fit_params)
                    legend = {
                        "label": process_fit(process_units(s.line_of_best_fit.legend_entry.label), s.line_of_best_fit.fit_params),
                    } if s.line_of_best_fit.legend_entry.show else {}
                    line = {
                        "linestyle": s.line_of_best_fit.line.style.value,
                        "linewidth": s.line_of_best_fit.line.width,
                    }
                    if not s.line_of_best_fit.line.auto_color:
                        line["color"] = s.line_of_best_fit.line.color
                    ax.plot(
                        x_temp,
                        y_temp,
                        **legend,
                        **line,
                    )
            end = time.perf_counter_ns()
            logging.debug(f"Plotted data in {format_elapsed_time(end - start)}")
            logging.debug("Setting figure properties")
            ax.set_xlim(st.session_state.figure_properties.x_axis.min, st.session_state.figure_properties.x_axis.max)
            ax.set_ylim(st.session_state.figure_properties.y_axis.min, st.session_state.figure_properties.y_axis.max)
            ax.set_xlabel(
                process_units(st.session_state.figure_properties.x_axis.label),
                fontsize=st.session_state.figure_properties.x_axis.font_size,
            )
            ax.set_ylabel(
                process_units(st.session_state.figure_properties.y_axis.label),
                fontsize=st.session_state.figure_properties.y_axis.font_size,
            )
            if show_legend:
                legend_opts = {
                    "loc": st.session_state.figure_properties.legend.position.lower(),
                    "fontsize": st.session_state.figure_properties.legend.font_size,
                }
                if not st.session_state.figure_properties.legend.auto_color:
                    legend_opts["facecolor"] = st.session_state.figure_properties.legend.background_color
                    legend_opts["framealpha"] = st.session_state.figure_properties.legend.opacity
                ax.legend(
                    **legend_opts,
                )
            ax.set_title(
                process_units(st.session_state.figure_properties.title.text),
                fontsize=st.session_state.figure_properties.title.font_size,
            )
            # ax.set_facecolor(st.session_state.background_color)
            logging.info("Plotting figure for display")
            start = time.perf_counter_ns()
            f = io.BytesIO()
            try:
                plt.savefig(f, format="svg", bbox_inches = "tight")
                f.seek(0)

                data = base64.b64encode(f.read()).decode("utf-8")
                st.write(
                    f'<img src="data:image/svg+xml;base64,{data}" alt="Plot" class="img-fluid" style="width: 100%;">',
                    unsafe_allow_html=True,
                )
                end = time.perf_counter_ns()
                logging.info(f"Figure plotted in {format_elapsed_time(end - start)}")
                logging.info("Plotting figure for download")
                start = time.perf_counter_ns()
                plot_file = io.BytesIO()
                fmt = st.session_state.figure_properties.file_type.lower()
                options = {
                    "bbox_inches" : "tight",
                    "format" : fmt,
                }
                if fmt == "png":
                    options["dpi"] = 300
                plt.savefig(plot_file, **options)
                plot_file.seek(0)
                end = time.perf_counter_ns()
                logging.info(f"Figure plotted in {format_elapsed_time(end - start)}")

                # sidebar download button
                st.sidebar.download_button(
                    "Download",
                    plot_file,
                    f"{st.session_state.figure_properties.filename}.{st.session_state.file_format.lower()}",
                    key="download",
                    type="primary"
                )
            except Exception as e:
                st.error(handle_latex_error(e))