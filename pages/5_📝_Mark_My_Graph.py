
from io import StringIO
import streamlit as st

from constants import LineStyles, MarkerStyles

st.set_page_config(
    page_title="Plotting - Mark My Graph",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Problems:
# - Do multiple data series share the same marker or line style?
# - Does anything have an opacity below 0.3?
# - Are there axis labels?
# - Do both axis labels contain units?
# - Is there a legend?
# - Are any lines of best fit reasonable? (base on R^2)
# - Are the axis limits reasonable?
#     - If manually set, does the data cover at least 75% of the axis?
# - Are the font sizes reasonable? (above 8pt, below 20pt)
# - Do line of best fit legend entries contain at least one fit parameter?

def check_markers():
    markers_used = []
    for series in st.session_state.data_series:
        if series.marker.style != MarkerStyles.NONE:
            markers_used.append((series.name, series.marker.style))
    if len(markers_used) == 0:
        return True, {}
    # Check for duplicated markers
    duplicates = {}
    for s, m in markers_used:
        if m.name not in duplicates:
            duplicates[m.name] = [s]
        else:
            duplicates[m.name].append(s)
    # filter out any marker with only one series
    duplicates = {m: s for m, s in duplicates.items() if len(s) > 1}
    if len(duplicates) == 0:
        return True, {}
    return False, duplicates

def check_line_styles():
    # identical to markers, just for line styles
    lines_used = []
    for series in st.session_state.data_series:
        if series.line.style != LineStyles.NONE:
            lines_used.append((series.name, series.line.style))
    if len(lines_used) == 0:
        return True, {}
    # Check for duplicated line styles
    duplicates = {}
    for s, l in lines_used:
        if l.name not in duplicates:
            duplicates[l.name] = [s]
        else:
            duplicates[l.name].append(s)
    # filter out any line style with only one series
    duplicates = {l: s for l, s in duplicates.items() if len(s) > 1}
    if len(duplicates) == 0:
        return True, {}
    return False, duplicates

def check_opacities():
    low_opacities = []
    for series in st.session_state.data_series:
        if series.marker.color.opacity < 0.3:
            low_opacities.append(series.name + " (Marker)")
        if series.line.color.opacity < 0.3:
            low_opacities.append(series.name + " (Line)")
        if series.line_of_best_fit.show and series.line_of_best_fit.line.color.opacity < 0.3:
            low_opacities.append(series.name + " (Line of Best Fit)")
    if len(low_opacities) == 0:
        return True, []
    return False, low_opacities

def check_axis_labels():
    x_good, y_good = True, True
    if st.session_state.figure_properties.x_axis.label in ["", "$x$"]:
        x_good = False
    if st.session_state.figure_properties.y_axis.label in ["", "$y$"]:
        y_good = False
    return x_good, y_good

def check_axis_units():
    # x axis
    x_label = st.session_state.figure_properties.x_axis.label
    x_good = True
    if not ("unit{" in x_label or "dimensionless" in x_label.lower() or "unitless" in x_label.lower()):
        x_good = False
    # y axis
    y_label = st.session_state.figure_properties.y_axis.label
    y_good = True
    if not ("unit{" in y_label or "dimensionless" in y_label.lower() or "unitless" in y_label.lower()):
        y_good = False

    return x_good, y_good

def check_legend():
    if len(st.session_state.data_series) == 1 and not st.session_state.data_series[0].line_of_best_fit.show:
        return True
    return st.session_state.figure_properties.legend.show

def check_line_of_best_fit():
    out = []
    for series in st.session_state.data_series:
        if series.line_of_best_fit.show:
            if series.line_of_best_fit.r_squared < 0.6:
                out.append((series.name, series.line_of_best_fit.r_squared))
    if len(out) == 0:
        return True, []
    return False, out

def check_axis_limits():
    # if axis limits are set manually, the data should cover at least 75% of the axis range
    x_min = st.session_state.figure_properties.x_axis.min
    x_max = st.session_state.figure_properties.x_axis.max
    y_min = st.session_state.figure_properties.y_axis.min
    y_max = st.session_state.figure_properties.y_axis.max
    if x_min is None and x_max is None and y_min is None and y_max is None:
        return True, True
    x_data_min = min([min(s.x_data) for s in st.session_state.data_series])
    x_data_max = max([max(s.x_data) for s in st.session_state.data_series])
    y_data_min = min([min(s.y_data) for s in st.session_state.data_series])
    y_data_max = max([max(s.y_data) for s in st.session_state.data_series])
    x_good = True
    y_good = True
    if x_min is not None or x_max is not None:
        if x_min is None:
            x_min = x_data_min
        if x_max is None:
            x_max = x_data_max
        if x_data_min < x_min or x_data_max > x_max:
            x_good = False
        if x_data_max - x_data_min < 0.75*(x_max - x_min):
            x_good = False
    if y_min is not None or y_max is not None:
        if y_min is None:
            y_min = y_data_min
        if y_max is None:
            y_max = y_data_max
        if y_data_min < y_min or y_data_max > y_max:
            y_good = False
        if y_data_max - y_data_min < 0.75*(y_max - y_min):
            y_good = False
    return x_good, y_good

def check_font_sizes():
    problems = []
    fig_props = st.session_state.figure_properties
    if fig_props.title.font_size < 8 or fig_props.title.font_size > 20:
        problems.append(("Title", fig_props.title.font_size))
    if fig_props.x_axis.font_size < 8 or fig_props.x_axis.font_size > 20:
        problems.append(("X Axis Label", fig_props.x_axis.font_size))
    if fig_props.y_axis.font_size < 8 or fig_props.y_axis.font_size > 20:
        problems.append(("Y Axis Label", fig_props.y_axis.font_size))
    if fig_props.legend.font_size < 8 or fig_props.legend.font_size > 20:
        problems.append(("Legend", fig_props.legend.font_size))
    
    return len(problems) == 0, problems

def check_line_of_best_fit_legend():
    problems = []
    for series in st.session_state.data_series:
        if series.line_of_best_fit.show and series.line_of_best_fit.legend_entry.show:
            legend_entry = series.line_of_best_fit.legend_entry.label
            if not "fit{" in legend_entry:
                problems.append(series.name)
    
    return len(problems) == 0, problems

def get_problems_message():
    found_some_problems = False
    st.markdown("I found the following potential problems with your graph:")
    cols = st.columns(3)
    idx = 0

    markers_good, markers_duplicates = check_markers()
    lines_good, lines_duplicates = check_line_styles()
    if not markers_good or not lines_good:
        found_some_problems = True
        with cols[idx % 3]:
            with st.expander("##### Duplicate Markers or Lines"):
                text = StringIO()
                if not markers_good:
                    text.write("You have used the same marker style for multiple data series:\n\n")
                    for m, s in markers_duplicates.items():
                        text.write(f"- These series all use the marker style \"{m.lower().title()}\":\n")
                        for series in s:
                            text.write(f"    - {series}\n")
                text.write("\n")
                if not lines_good:
                    text.write("You have used the same line style for multiple data series:\n\n")
                    for l, s in lines_duplicates.items():
                        text.write(f"- These series all use the line style \"{l.lower().title()}\":\n")
                        for series in s:
                            text.write(f"    - {series}\n")
                st.markdown(text.getvalue())
                st.markdown("""###### Explanation
                            
You should try to use different marker styles and line styles for each data series so that they are easily distinguishable even in black and white or for people with colour blindness.""")
        idx += 1

    opacities_good, low_opacities = check_opacities()
    if not opacities_good:
        found_some_problems = True
        with cols[idx % 3]:
            with st.expander("##### Low Opacities"):
                text = StringIO()
                text.write("You have used a low opacity for some markers or lines in the following series:\n\n")
                for series in low_opacities:
                    text.write(f"- {series}\n")
                st.markdown(text.getvalue())
                st.markdown("""###### Explanation
                            
Low opacity markers and lines can be very hard to see, and should usually be avoided except in very specific circumstances. If you are using a low (or zero) opacity to make a line or marker invisible, you should instead remove the line or marker by setting its style to "None".""")
        idx += 1

    x_good, y_good = check_axis_labels()
    if not x_good or not y_good:
        found_some_problems = True
        with cols[idx % 3]:
            with st.expander("##### Missing Axis Labels"):
                text = StringIO()
                text.write(f"""You have have not specified an axis label for {' either axis' if not x_good and not y_good else f' the {"x" if not x_good else "y"} axis'}.\n""")
                st.markdown(text.getvalue())
                st.markdown("""###### Explanation

Every graph **must** have an axis label for each axis. If there is no axis label, then the data on the graph can't be read and understood, meaning that the graph and any conclusions based on the graph are useless.""")
        idx += 1


    x_good, y_good = check_axis_units()
    if not x_good or not y_good:
        found_some_problems = True
        with cols[idx % 3]:
            with st.expander("##### Missing Axis Units"):
                text = StringIO()
                text.write(f"""It looks like you have have not specified units for {' either axis' if not x_good and not y_good else f' the {"x" if not x_good else "y"} axis'}.\n""")
                st.markdown(text.getvalue())
                st.markdown("""###### Explanation
                            
If you have not specified units for an axis, then the data on the graph can't be read and understood, meaning that the graph and any conclusions based on the graph are useless. If the quantity on that axis has no units, consider stating this explicitly by including "dimensionless" or "unitless" if appropriate.""")
        idx += 1

    has_legend = check_legend()
    if not has_legend:
        found_some_problems = True
        with cols[idx % 3]:
            with st.expander("##### Missing Legend"):
                text = StringIO()
                text.write("You have not included a legend\n")
                st.markdown(text.getvalue())
                st.markdown("""###### Explanation
                            
If you have more than one data series, or a line of best fit, the reader needs to know what each line or data series represents. The legend is the best way to do this.""")
        idx += 1

    line_of_best_fit_good, bad_fits = check_line_of_best_fit()
    if not line_of_best_fit_good:
        found_some_problems = True
        with cols[idx % 3]:
            with st.expander("##### Poor Quality Fits"):
                text = StringIO()
                text.write("Some of your lines of best fit have a low $R^2$ value (i.e., are a weak fit to your data):\n\n")
                for series, R2 in bad_fits:
                    text.write(f"- {series}: $R^2 \\approx {R2:.4f}$\n")
                st.markdown(text.getvalue())
                st.markdown("""###### Explanation
                            
An $R^2$ value is a measure of how well a set of data fits a given model. An $R^2$ value of $1$ means that the data fits the model perfectly (i.e, every data point lies on the line of best fit), while an $R^2$ value of $0$ means that the data does not fit the model at all. An $R^2$ value of $0.8$ or above is generally considered a good fit, while an $R^2$ value of $0.5$ or below is generally considered a poor fit.
                            
If your $R^2$ value is very low, this could indicate that you are not using the appropriate model for your data, or that your data has too much uncertainty to be reliably modelled.""")
        idx += 1

    x_good, y_good = check_axis_limits()
    if not x_good or not y_good:
        found_some_problems = True
        with cols[idx % 3]:
            with st.expander("##### Axis Limits Too Wide"):
                text = StringIO()
                text.write(f"""Your axis limits are too wide: the data does not cover at least 75% of the axis range for {' either axis' if not x_good and not y_good else f' the {"x" if not x_good else "y"} axis'}\n""")
                st.markdown(text.getvalue())
                st.markdown("""###### Explanation
                            
If you have set the axis limits manually, you should ensure that the data covers at least 75% of the axis range. In particular, it's not usually advisable to set the $y$-axis to start at $0$ if the data starts at a higher value.""")
        idx += 1


    font_size_good, bad_font_sizes = check_font_sizes()
    if not font_size_good:
        found_some_problems = True
        with cols[idx % 3]:
            with st.expander("##### Font Sizes"):
                text = StringIO()
                text.write("You have used a font size that may be either too small or too large for the following elements:\n\n")
                for element, size in bad_font_sizes:
                    text.write(f"- {element}: {size}pt\n")
                st.markdown(text.getvalue())
                st.markdown("""###### Explanation
                            
Font sizes below 8pt can be very hard to read, while font sizes above 20pt can be very distracting. Remember where you are using this graph - if it is for a report, then it is likely to be much smaller than it appears. As a rule of thumb, use a font size 2pt larger or smaller than your body text. For a presentation, you can use larger font sizes.""")


    line_of_best_fit_legend_good, bad_fits = check_line_of_best_fit_legend()
    if not line_of_best_fit_legend_good:
        found_some_problems = True
        with cols[idx % 3]:
            with st.expander("##### Missing Fit Parameters"):
                text = StringIO()
                text.write("It looks like your legend entries don't include any fit parameters for the line of best fit for the following data series:\n\n")
                for series in bad_fits:
                    text.write(f"- {series}\n")
                st.markdown(text.getvalue())
                st.markdown("""###### Explanation
                            
When including a line of best fit on a graph, you need to tell the reader what that line represents. Usually, this means including the equation (or type, such as "linear") and often some of the fit parameters. If you are not planning to do so in a caption, then you should consider including this information in the legend.""")

    if not found_some_problems:
        st.markdown("I couldn't find any problems with your graph! 🎉")
    else:
        st.markdown("*This is just a guide, and is far from comprehensive. It also isn't perfect; it might not detect things that you have done well, and it might miss some problems.*")

if "data_series" in st.session_state and len(st.session_state.data_series) > 0:
    get_problems_message()