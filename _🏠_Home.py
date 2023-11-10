import base64
import io
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import qoplots.qoplots as qp
import re
from contextlib import nullcontext
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
import time

st.set_page_config(
    page_title="Plotting",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from data import (
    AxisProperties,
    Color,
    DataSeries,
    FigureProperties,
    LegendEntry,
    Line,
    LineOfBestFit,
    Marker,
)
from constants import MarkerStyles, LineStyles
from fitting import fit, get_fitted_data
from text import process_fit, process_units
from errors import (
    handle_data_error,
    handle_fit_error,
    handle_json_error,
    handle_latex_error,
)
from persistance import (
    clean_old_files,
    get_key,
    load_data,
    save_data,
    clear_data,
    get_all_cookies,
)



def add_transparency(color, opacity):
    # color is in hex format, opacity is 0 to 1
    # returns the colour as (r,g,b,a)
    if color.startswith("#"):
        color = color[1:]
    if len(color) == 3:
        color = "".join([c + c for c in color])
    if len(color) != 6:
        raise ValueError("Invalid hex colour.")
    r, g, b = color[:2], color[2:4], color[4:]
    return (int(r, 16)/255, int(g, 16)/255, int(b, 16)/255, opacity)


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


key = get_key()
st.session_state.key_cookie = key

if not "should_load" in st.session_state:
    st.session_state.should_load = True

st.markdown(
    """<style>
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
    unsafe_allow_html=True,
)


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
        logging.error(
            f"Number of x-values ({len(x_data)}) does not match number of y-values ({len(y_data)})."
        )
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
        name=new_name,
        x=x_data,
        y=y_data,
        marker=Marker(
            style=MarkerStyles.POINT,
            color=Color.default(),
            size=10,
        ),
        line=Line(
            style=LineStyles.SOLID,
            color=Color.default(),
            width=1,
        ),
        legend_entry=LegendEntry(
            show=True,
            label=new_name,
        ),
        line_of_best_fit=LineOfBestFit(
            show=False,
            line=Line(
                style=LineStyles.DASHED,
                color=Color.default(),
                width=1,
            ),
            fit_type="Linear",
            fit_params=[1, 0],
            r_squared=1,
            legend_entry=LegendEntry(
                show=False,
                label="Fit",
            ),
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
        series.line_of_best_fit.fit_params, series.line_of_best_fit.r_squared = fit(fit_type, series.x, series.y)
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
    to_remove = changed["deleted_rows"]
    # sort reversed so that the indices don't change
    to_remove.sort(reverse=True)
    for row in to_remove:
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
    update_fit(series, series.line_of_best_fit.fit_type, series.line_of_best_fit.show)


# plot
@st.cache_data
def plot(data_series, figure_properties):
    fig, ax = plt.subplots()
    for s in data_series:
        x_data = s.x
        y_data = s.y
        legend = {}
        if s.legend_entry.show:
            legend["label"] = process_units(s.legend_entry.label)
        marker = {
            "marker": s.marker.style.value,
            "markersize": s.marker.size,
        }
        if s.marker.color.auto_color or s.line.color.auto_color:
            # get the next colour from the matplotlib cycler
            next_color = ax._get_lines.get_next_color()
        if s.marker.color.auto_color:
            marker["markerfacecolor"] = add_transparency(next_color, s.marker.color.opacity)
            marker["markeredgecolor"] = add_transparency(next_color, s.marker.color.opacity)
        else:
            marker["markerfacecolor"] = add_transparency(s.marker.color.color, s.marker.color.opacity)
            marker["markeredgecolor"] = add_transparency(s.marker.color.color, s.marker.color.opacity)
        line = {
            "linestyle": s.line.style.value,
            "linewidth": s.line.width,
        }
        if s.line.color.auto_color:
            line["color"] = add_transparency(next_color, s.line.color.opacity)
        else:
            line["color"] = add_transparency(s.line.color.color, s.line.color.opacity)
        ax.plot(
            x_data,
            y_data,
            **legend,
            **marker,
            **line,
        )

        # line of best fit
        if not s.line_of_best_fit.show:
            continue

        x_temp = np.linspace(x_data.min(), x_data.max(), max(100, len(x_data)))
        y_temp = get_fitted_data(
            x_temp,
            s.line_of_best_fit.fit_type,
            s.line_of_best_fit.fit_params,
        )
        legend = (
            {
                "label": process_fit(
                    process_units(s.line_of_best_fit.legend_entry.label),
                    s.line_of_best_fit.fit_params,
                ),
            }
            if s.line_of_best_fit.legend_entry.show
            else {}
        )
        line = {
            "linestyle": s.line_of_best_fit.line.style.value,
            "linewidth": s.line_of_best_fit.line.width,
        }
        if s.line_of_best_fit.line.color.auto_color:
            next_color = ax._get_lines.get_next_color()
            line["color"] = add_transparency(next_color, s.line_of_best_fit.line.color.opacity)
        else:
            line["color"] = add_transparency(s.line_of_best_fit.line.color.color, s.line_of_best_fit.line.color.opacity)
        ax.plot(
            x_temp,
            y_temp,
            **legend,
            **line,
        )
    ax.set_xlim(
        figure_properties.x_axis.min,
        figure_properties.x_axis.max,
    )
    ax.set_ylim(
        figure_properties.y_axis.min,
        figure_properties.y_axis.max,
    )
    ax.set_xlabel(
        process_units(figure_properties.x_axis.label),
        fontsize=figure_properties.x_axis.font_size,
    )
    ax.set_ylabel(
        process_units(figure_properties.y_axis.label),
        fontsize=figure_properties.y_axis.font_size,
    )
    if figure_properties.legend.show:
        legend_opts = {
            "loc": figure_properties.legend.position.lower(),
            "fontsize": figure_properties.legend.font_size,
        }
        if not figure_properties.legend.background_color.auto_color:
            legend_opts["facecolor"] = figure_properties.legend.background_color.color
            legend_opts[
                "framealpha"
            ] = figure_properties.legend.background_color.opacity
        ax.legend(
            **legend_opts,
        )
    ax.set_title(
        process_units(figure_properties.title.text),
        fontsize=figure_properties.title.font_size,
    )
    f_svg = io.BytesIO()
    try:
        plt.savefig(f_svg, format="svg", bbox_inches="tight")
        f_svg.seek(0)
        data_svg = base64.b64encode(f_svg.read()).decode("utf-8")
    except Exception as e:
        st.error(handle_latex_error(e))
        data_svg = None
    f_download = io.BytesIO()
    fmt = figure_properties.file_type.lower()
    options = {
        "bbox_inches": "tight",
        "format": fmt,
    }
    if fmt == "png":
        options["dpi"] = 300
    try:
        plt.savefig(f_download, **options)
        f_download.seek(0)
    except Exception as e:
        st.error(handle_latex_error(e))
        f_download = None
    return data_svg, f_download

def confirm(
        confirmation_message: str,
        on_confirm: callable,
        on_cancel: callable = None,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
):
    def _on_confirm():
        st.session_state.getting_confirmation = False
        on_confirm()
    def _on_cancel():
        st.session_state.getting_confirmation = False
        if on_cancel is not None:
            on_cancel()
    st.session_state.getting_confirmation = True
    st.session_state.confirmation_message = confirmation_message
    st.session_state.confirmation_on_confirm = _on_confirm
    st.session_state.confirmation_on_cancel = _on_cancel
    st.session_state.confirmation_confirm_text = confirm_text
    st.session_state.confirmation_cancel_text = cancel_text

def get_confirmation(
        confirmation_message: str,
        on_confirm: callable,
        on_cancel: callable = None,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
):
    st.header("Are you sure?")
    st.write(confirmation_message)
    cols = st.columns(2)
    with cols[0]:
        if st.button(confirm_text, type = "primary"):
            on_confirm()
            st.rerun()
    with cols[1]:
        if st.button(cancel_text):
            if on_cancel is not None:
                on_cancel()
                st.rerun()
            else:
                st.rerun()


if st.session_state.should_load:
    _data_series, _figure_properties = load_data(key)
    st.session_state.data_series = _data_series
    st.session_state.figure_properties = _figure_properties
    st.session_state.should_load = False

# session state variables
if "figure_properties" not in st.session_state:
    st.session_state.figure_properties = FigureProperties.default()
if "active_series" not in st.session_state:
    st.session_state.active_series = None
if "data_series" not in st.session_state:
    st.session_state.data_series = []
# Sidebar -------------------------------------


def colour_choice(
    label: str,
    colour: Color,
    auto_key: str,
    colour_key: str,
    auto_callback=None,
    colour_callback=None,
    show_opacity: bool = False,
    always_show_opacity: bool = False,  # show even with auto colour
    opacity_key: str = None,
    opacity_callback=None,
):
    if auto_callback is None:
        on_change = {}
    else:
        on_change = {"on_change": auto_callback}
    auto_color = st.toggle(
        "Use Automatic Colour",
        colour.auto_color,
        key=auto_key,
        **on_change,
    )
    if not auto_color:
        if colour_callback is None:
            on_change = {}
        else:
            on_change = {"on_change": colour_callback}
        st.color_picker(
            label,
            colour.color,
            key=colour_key,
            **on_change,
        )
    if show_opacity and (not auto_color or always_show_opacity):
        if opacity_callback is None:
            on_change = {}
        else:
            on_change = {"on_change": opacity_callback}
        st.slider(
            "Opacity",
            0,
            100,
            int(colour.opacity * 100),
            step=1,
            format="%d%%",
            key=opacity_key,
            **on_change,
        )


def data_sidebar():
    if st.session_state.active_series is None:
        st.session_state.active_series = st.session_state.data_series[0]
    if len(st.session_state.data_series) == 0:
        return
    if len(st.session_state.data_series) > 1:
        st.sidebar.selectbox(
            "Data Series",
            [s.name for s in st.session_state.data_series],
            index=0,
            key="active_series_name",
            on_change=lambda: change_active_series(st.session_state.active_series_name),
        )
    data_series_options()
    st.sidebar.toggle(
        "Line of Best Fit",
        st.session_state.active_series.line_of_best_fit.show,
        key="show_line_of_best_fit",
        on_change=lambda: update_fit(
            st.session_state.active_series,
            st.session_state.active_series.line_of_best_fit.fit_type,
            st.session_state.show_line_of_best_fit,
        ),
    )
    if st.session_state.active_series.line_of_best_fit.show:
        line_of_best_fit_options()


def marker_options():
    colour_choice(
        "Marker Colour",
        st.session_state.active_series.marker.color,
        "marker_auto_color",
        "marker_color",
        auto_callback=lambda: setattr(
            st.session_state.active_series.marker.color,
            "auto_color",
            st.session_state.marker_auto_color,
        ),
        colour_callback=lambda: setattr(
            st.session_state.active_series.marker.color,
            "color",
            st.session_state.marker_color,
        ),
        show_opacity=True,
        always_show_opacity=True,
        opacity_key="marker_opacity",
        opacity_callback=lambda: setattr(
            st.session_state.active_series.marker.color,
            "opacity",
            st.session_state.marker_opacity / 100,
        ),
    )
    # marker size
    st.slider(
        "Marker Size",
        0.0,
        20.0,
        float(st.session_state.active_series.marker.size),
        step=0.2,
        key="marker_size",
        on_change=lambda: setattr(
            st.session_state.active_series.marker,
            "size",
            st.session_state.marker_size,
        ),
    )


def line_options(
    line: Line,
    style_key: str,
    auto_key: str,
    colour_key: str,
    width_key: str,
    opacity_key: str,
):
    # line style
    st.selectbox(
        "Line Style",
        list(LineStyles),
        key=style_key,
        format_func=lambda x: x.name.replace("_", " ").title(),
        index=line.style.index,
        on_change=lambda: setattr(
            line,
            "style",
            st.session_state[style_key],
        ),
    )
    if st.session_state[style_key] != LineStyles.NONE:
        colour_choice(
            "Line Colour",
            line.color,
            auto_key,
            colour_key,
            auto_callback=lambda: setattr(
                line.color,
                "auto_color",
                st.session_state[auto_key],
            ),
            colour_callback=lambda: setattr(
                line.color,
                "color",
                st.session_state[colour_key],
            ),
            show_opacity=True,
            always_show_opacity=True,
            opacity_key=opacity_key,
            opacity_callback=lambda: setattr(
                line.color,
                "opacity",
                st.session_state[opacity_key] / 100,
            ),
        )
        # line width
        st.slider(
            "Line Width",
            1.0,
            5.0,
            float(line.width),
            step=0.1,
            key=width_key,
            on_change=lambda: setattr(
                line,
                "width",
                st.session_state[width_key],
            ),
        )


def data_series_options():
    with st.sidebar.expander("**Data Series**", expanded=False):
        st.subheader("Marker")
        marker_style = st.selectbox(
            "Marker",
            list(MarkerStyles),
            key="marker",
            format_func=lambda x: x.name.replace("_", " ").title(),
            index=st.session_state.active_series.marker.style.index,
            on_change=lambda: setattr(
                st.session_state.active_series.marker, "style", st.session_state.marker
            ),
        )
        if marker_style != MarkerStyles.NONE:
            marker_options()

        st.subheader("Line")
        line_options(
            st.session_state.active_series.line,
            "line_style",
            "line_auto_color",
            "line_color",
            "line_width",
            "line_opacity",
        )
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


def text_options(
    label: str,
    text: str,
    font_size: int,
    text_key: str,
    font_size_key: str,
    text_callback=None,
    font_size_callback=None,
    text_help=None,
):
    st.text_input(
        label,
        text,
        key=text_key,
        on_change=text_callback,
    )
    st.slider(
        "Font Size",
        6,
        32,
        int(font_size),
        key=font_size_key,
        on_change=font_size_callback,
    )


def line_of_best_fit_options():
    with st.sidebar.expander("**Line of Best Fit**", expanded=False):
        st.subheader("Fit")
        # fit type
        st.selectbox(
            "Fit Type",
            [
                "Linear",
                "Quadratic",
                "Cubic",
                "Exponential",
                "Logarithmic",
                "Sinusoidal",
            ],
            key="fit_type",
            index=0,
            on_change=lambda: update_fit(
                st.session_state.active_series,
                st.session_state.fit_type,
                st.session_state.show_line_of_best_fit,
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
        show = st.toggle("Show Fit Parameters", False)
        if show:
            column_config = {}
            for i in range(
                len(st.session_state.active_series.line_of_best_fit.fit_params)
            ):
                column_config[str(i)] = chr(ord("a") + i)
            st.dataframe(
                [st.session_state.active_series.line_of_best_fit.fit_params],
                hide_index=True,
                use_container_width=True,
                column_config=column_config,
            )
        st.subheader("Line")
        line_options(
            st.session_state.active_series.line_of_best_fit.line,
            "line_of_best_fit_style",
            "line_of_best_fit_auto_color",
            "line_of_best_fit_color",
            "line_of_best_fit_width",
            "line_of_best_fit_opacity",
        )
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


def axis_options(
    axis: AxisProperties,
    axis_name: str,  # x or y
):
    # cols = st.columns(2)
    # for i, lim in enumerate(["min", "max"]):
    #     with cols[i]:
    #         key = f"{axis_name}_{lim}"
    #         st.text_input(
    #             f"${axis_name}$ {lim}",
    #             "" if axis[lim] is None else str(axis[lim]),
    #             key=key,
    #             help="Leave blank for automatic scaling.",
    #             # on_change=lambda: setattr(
    #             #     axis,
    #             #     lim,
    #             #     None
    #             #     if st.session_state[f"{axis_name}_{lim}"].strip() == ""
    #             #     else float(st.session_state[f"{axis_name}_{lim}"]),
    #             # ),
    #             on_change = lambda: print("Axis limit: ", st.session_state[key])
    #         )
    min_col, max_col = st.columns(2)
    with min_col:
        key = f"{axis_name}_axis_min"
        axis_lim = st.text_input(
            f"${axis_name}$ Min",
            "" if axis.min is None else str(axis.min),
            key=key,
            help="Leave blank for automatic scaling.",
        )
        axis_lim = None if len(axis_lim.strip()) == 0 else float(axis_lim)
        axis.min = axis_lim
    with max_col:
        key = f"{axis_name}_max"
        axis_lim = st.text_input(
            f"${axis_name}$ Max",
            "" if axis.max is None else str(axis.max),
            key=key,
            help="Leave blank for automatic scaling.",
        )
        
        axis_lim = None if len(axis_lim.strip()) == 0 else float(axis_lim)
        axis.max = axis_lim
    text_options(
        f"${axis_name}$ Axis Label",
        axis.label,
        axis.font_size,
        f"{axis_name}_label",
        f"font_size_{axis_name}",
        text_callback=lambda: setattr(
            axis,
            "label",
            st.session_state[f"{axis_name}_label"],
        ),
        font_size_callback=lambda: setattr(
            axis,
            "font_size",
            st.session_state[f"font_size_{axis_name}"],
        ),
    )


def figure_sidebar():
    with st.sidebar.expander("**$x$ Axis**"):
        axis_options(
            st.session_state.figure_properties.x_axis,
            "x",
        )
    with st.sidebar.expander("**$y$ Axis**"):
        axis_options(
            st.session_state.figure_properties.y_axis,
            "y",
        )
    with st.sidebar.expander("**Title**"):
        text_options(
            "Title",
            st.session_state.figure_properties.title.text,
            st.session_state.figure_properties.title.font_size,
            "title",
            "font_size_title",
            text_callback=lambda: setattr(
                st.session_state.figure_properties.title,
                "text",
                st.session_state.title,
            ),
            font_size_callback=lambda: setattr(
                st.session_state.figure_properties.title,
                "font_size",
                st.session_state.font_size_title,
            ),
        )
    with st.sidebar.expander("**Legend**"):
        show_legend = st.toggle(
            "Show Legend", 
            True, 
            key="show_legend",
            on_change=lambda: setattr(
                st.session_state.figure_properties.legend,
                "show",
                st.session_state.show_legend,
            ),
        )
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
                index=positions.index(
                    st.session_state.figure_properties.legend.position
                ),
                on_change=lambda: setattr(
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
                on_change=lambda: setattr(
                    st.session_state.figure_properties.legend,
                    "font_size",
                    st.session_state.font_size_legend,
                ),
            )
            colour_choice(
                "Background Colour",
                st.session_state.figure_properties.legend.background_color,
                "legend_auto_color",
                "legend_background_color",
                auto_callback=lambda: setattr(
                    st.session_state.figure_properties.legend.background_color,
                    "auto_color",
                    st.session_state.legend_auto_color,
                ),
                colour_callback=lambda: setattr(
                    st.session_state.figure_properties.legend.background_color,
                    "color",
                    st.session_state.legend_background_color,
                ),
                show_opacity=True,
                opacity_key="legend_opacity",
                opacity_callback=lambda: setattr(
                    st.session_state.figure_properties.legend.background_color,
                    "opacity",
                    st.session_state.legend_opacity / 100,
                ),
            )

    themes = [
        "Afterglow",
        "Andromeda",
        # "Apex",
        "Aspect",
        "Blazer",
        # "Blueberrypie",
        "Breeze",
        # "Broadcast",
        "Chalkboard",
        "Concourse",
        "Espresso",
        "Executive",
        # "Flatland",
        "Japanesque",
        "Jellybeans",
        "Jubi",
        "Lab Fox",
        "Lovelace",
        "Material",
        "Module",
        # "Nemo",
        "Neutron",
        "Newcastle",
        "Nord",
        "Office Default",
        "Popping and Locking",
        # "Red Planet",
        "Rose Pine",
        "Sketchbook",
        "Solstice",
        "Spacegray",
        "Sundried",
        "Twilight",
        "Urban",
    ]
    st.sidebar.selectbox(
        "Theme",
        themes,
        index=themes.index(st.session_state.figure_properties.theme),
        key="theme",
        on_change=lambda: setattr(
            st.session_state.figure_properties,
            "theme",
            st.session_state.theme,
        ),
    )


def file_sidebar():
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
        index=formats.index(st.session_state.figure_properties.file_type.upper()),
        on_change=lambda: setattr(
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
        help="Do not include the file extension.",
        on_change=lambda: setattr(
            st.session_state.figure_properties,
            "filename",
            st.session_state.file_name,
        ),
    )


st.sidebar.title("Options")
st.sidebar.header("Data")
if len(st.session_state.data_series) == 0:
    st.sidebar.markdown("*Add a data series to get started.*")
else:
    data_sidebar()
    st.sidebar.divider()
    st.sidebar.header("Figure")
    figure_sidebar()
    st.sidebar.divider()
    st.sidebar.header("File")
    file_sidebar()

# Main ----------------------------------------

def main_panes():
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
                            key=f"{s.name}_data",
                            on_change=update_data,
                            args=(s, f"{s.name}_data"),
                            column_config={"0": "x", "1": "y"},
                            num_rows="dynamic",
                        )
                        left, right = st.columns(2)
                        with left:
                            # Delete button
                            st.button(
                                "🗑️ Delete Series",
                                key=f"{s.name}_delete",
                                type="primary",
                                on_click=confirm,
                                args=(
                                    "Are you sure you want to delete this data series? :red[This cannot be undone].",
                                    lambda: delete_series(s.name),
                                    None,
                                    "Delete",
                                    "Cancel",
                                ),
                                help="Delete the **entire** data series. :red[This cannot be undone].",
                            )
                            
                        with right:
                            # reset button
                            st.button(
                                "🔄 Reset Data",
                                key=f"{s.name}_reset",
                                on_click=confirm,
                                args=(
                                    "Are you sure you want to reset this data series? All changes will be lost. :red[This cannot be undone].",
                                    lambda: s.reset_data(),
                                    None,
                                    "Reset",
                                    "Cancel",
                                ),
                                help="Reset the data to the original values. :red[This cannot be undone].",
                            )
        with new_data:
            # new data name
            new_name = st.text_input(
                "Name",
                f"Data Series {len(st.session_state.data_series) + 1}",
                key="new_name",
            )
            new_x, new_y = st.columns(2)
            with new_x:
                x_data = st.text_area(
                    "X Data",
                    key="new_x_data",
                    help="Paste your $x$-data here, with each value on a new line. \nDo not include the header row.",
                    height=300,
                )
            with new_y:
                y_data = st.text_area(
                    "Y Data",
                    key="new_y_data",
                    help="Paste your $y$-data here, with each value on a new line. \nDo not include the header row.",
                    height=300,
                )
            # add button
            st.button("Add Data", key="add_data", on_click=add_new_data)

    if len(st.session_state.data_series) > 0:
        set_theme(st.session_state.theme)



    with plot_col:
        with st.spinner("Generating Plot"):
            # time.sleep(20)
            if len(st.session_state.data_series) > 0:
                start = time.perf_counter_ns()
                svg_data, download_data = plot(
                    st.session_state.data_series,
                    st.session_state.figure_properties,
                )
                end = time.perf_counter_ns()
                logging.info(f"Plot generated in {format_elapsed_time(end - start)}")
                if svg_data is not None:
                    st.write(
                        f'<img src="data:image/svg+xml;base64,{svg_data}" alt="Plot" class="img-fluid" style="width: 100%;">',
                        unsafe_allow_html=True,
                    )
                if download_data is not None:
                    st.sidebar.download_button(
                        "Download",
                        download_data,
                        f"{st.session_state.figure_properties.filename}.{st.session_state.file_format.lower()}",
                        key="download",
                        type="primary",
                        help="Download the figure in the specified file format.",
                        use_container_width=True,
                    )
        # st.write(get_all_cookies())
        # logging.info(get_all_cookies())

    st.sidebar.divider()
    st.sidebar.header("Advanced")

    if len(st.session_state.data_series) > 0:
        json_data = json.dumps(
            {
                "data_series": [s.to_dict() for s in st.session_state.data_series],
                "figure_properties": st.session_state.figure_properties.to_dict(),
            }
        )
        left, right = st.sidebar.columns(2)
        left.download_button(
            "Download Data",
            json_data,
            st.session_state.figure_properties.filename + ".json",
            key="download_data",
            help="Download the data and settings as a .json file.",
            use_container_width=True,
        )
        right.button(
            "New Figure",
            key="new",
            help="Start a new plot. **:red[This will clear all current data.]**",
            on_click=confirm,
            args=(
                "Are you sure you want to start a new figure? :red[This will clear all current data.]",
                lambda: clear_data(st.session_state.key_cookie),
            ),
            type="primary",
            use_container_width=True,
        )
    else:
        # upload data
        uploaded_file = st.sidebar.file_uploader("Upload Data", type=["json"])
        if uploaded_file is not None:
            try:
                data = json.load(uploaded_file)
                st.session_state.data_series = []
                for s in data["data_series"]:
                    st.session_state.data_series.append(DataSeries.from_dict(s))
                st.session_state.figure_properties = FigureProperties.from_dict(
                    data["figure_properties"]
                )
                st.rerun()
            except Exception as e:
                st.error(handle_json_error(e))
                raise (e)

    # save the data
    if (
        len(st.session_state.data_series) > 0
        or not st.session_state.figure_properties.is_default()
    ):
        save_data(
            key,
            st.session_state.data_series,
            st.session_state.figure_properties,
        )
    clean_old_files()

if "getting_confirmation" not in st.session_state:
    st.session_state.getting_confirmation = False

if st.session_state.getting_confirmation:
    left, _ = st.columns(2)
    with left:
        get_confirmation(
            st.session_state.confirmation_message,
            st.session_state.confirmation_on_confirm,
            st.session_state.confirmation_on_cancel,
            st.session_state.confirmation_confirm_text,
            st.session_state.confirmation_cancel_text,
        )
else:
    main_panes()
