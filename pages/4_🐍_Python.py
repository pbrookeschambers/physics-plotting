from io import StringIO
import json
import logging
import re
import streamlit as st
import os
import black
import qoplots.qoplots as qp

st.set_page_config(
    page_title="Plotting - Python",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    # menu_items={
    #     "About": about
    # }
)

st.markdown("""# Python Code""")

left, right = st.columns([0.35, 0.65])

with left:
    st.markdown("## Options")
    st.markdown(
        """On the right hand side, you can find the python code necessary to recreate the figure you have created. Below are some settings for this code.
                
***:blue[Note:]** For the sake of cleaner code, the code provided does not allow for separate marker and line opacities on the same data series. Instead, it uses whichever is the largest of the two.*"""
    )
    st.divider()
    st.markdown("""## Code Settings""")
    use_qoplots = st.toggle("Use `qoplots`", True, help = "If disabled, styling will be included directly")
    if use_qoplots:
        st.markdown("The `qoplots` Python package can be found here: [QoPlots](https://github.com/pbrookeschambers/qoplots).")
    inline_data = st.toggle("Inline data", True, help = "if disabled, data will be loaded from a file")
    if not inline_data and "data_series" in st.session_state and len(st.session_state.data_series) > 0:
        if len(st.session_state.data_series) == 1:
            data = st.session_state.data_series[0].to_csv()
            filename = st.session_state.figure_properties.filename + "_data.csv"
        else:
            data = json.dumps([s.to_plot_json() for s in st.session_state.data_series], indent = 4)
            filename = st.session_state.figure_properties.filename + "_data.json"
        st.download_button(
            "Download data",
            data,
            filename,
            type = "primary"
        )
    include_comments = st.toggle("Include comments", True, help = "Include helpful comments in the code")
    use_latex = st.toggle("Use $\LaTeX$", True, help = "If disabled, use matplotlib's default text rendering")

with right:
    if "data_series" in st.session_state:
        st.markdown("""## Code""")
        code = StringIO()
        code.write(
            f"""import numpy as np
{f'''import qoplots.qoplots as qp
qp.init("{st.session_state.figure_properties.theme.lower().replace(" ", "_")}")''' if use_qoplots else ""}
import matplotlib.pyplot as plt
{'''import matplotlib as mpl''' if not use_qoplots or not use_latex else ""}
{'''from cycler import cycler''' if not use_qoplots else ""}
from scipy.optimize import curve_fit
"""
        )
        if len(st.session_state.data_series) > 1 and not inline_data:
            code.write("import json\n")
        if not use_qoplots or not use_latex:
            code.write(f"#{' Setting Default Styling ':-<100s}\n")
        if not use_qoplots:
            new_params = qp.init(st.session_state.figure_properties.theme.lower().replace(" ", "_"))
            if not use_latex:
                new_params["text.usetex"] = False
            code.write(f"mpl.rcParams.update({new_params})\n")
        elif not use_latex:
            code.write(f"mpl.rcParams.update({{'text.usetex': False}})\n")
        if len(st.session_state.data_series) == 1:
            code.write(f"#{' Data ':-<100s}\n")
            if inline_data:
                code.write(
                    f"x_data = np.array([{', '.join([str(v) for v in st.session_state.data_series[0].x])}])\n"
                )
                code.write(
                    f"y_data = np.array([{', '.join([str(v) for v in st.session_state.data_series[0].y])}])\n"
                )
            else:
                code.write(f"""data_file_name = "{st.session_state.figure_properties.filename}_data.csv"
with open(data_file_name, "r") as data_file:
    data = np.genfromtxt(data_file, delimiter=", ")
x_data = data[:, 0]
y_data = data[:, 1]
""")
            code.write(f"\n\n#{' Plotting Data ':-<100s}\n")
            code.write("fig, ax = plt.subplots()\n")
            code.write(st.session_state.data_series[0].to_plot_code())
        elif len(st.session_state.data_series) > 1:
            # gather the fit functions
            fit_funcs_needed = []
            for s in st.session_state.data_series:
                if s.line_of_best_fit.show and s.line_of_best_fit.fit_type not in fit_funcs_needed:
                    fit_funcs_needed.append(s.line_of_best_fit.fit_type)
            fit_funcs = {
                "Linear": """def linear_fit_func(x, a, b):
    return a*x + b""",
                "Quadratic": """def quadratic_fit_func(x, a, b, c):
    return a*x**2 + b*x + c""",
                "Cubic": """def cubic_fit_func(x, a, b, c, d):
    return a*x**3 + b*x**2 + c*x + d""",
                "Exponential": """def exponential_fit_func(x, a, b, c):
    return a*np.exp(b*x) + c""",
                "Logarithmic": """def logarithmic_fit_func(x, a, b, c):
    return a*np.log(b*x) + c""",
                "Sinusoidal": """def sinusoidal_fit_func(x, a, b, c, d):
    return a*np.sin(b*x + c) + d""",
            }
            if len(fit_funcs_needed) > 0:
                code.write(f"#{' Fit Functions ':-<100s}\n")
                for fit_func in fit_funcs_needed:
                    code.write(fit_funcs[fit_func] + "\n\n")
                code.write("fit_funcs = {\n")
                for fit_func in fit_funcs_needed:
                    code.write(f'    "{fit_func}": {fit_func.lower()}_fit_func,\n')
                code.write("}\n\n")
            code.write(f"#{' Data ':-<100s}\n")
            if inline_data:
                code.write("data = " + json.dumps([s.to_plot_json() for s in st.session_state.data_series]))
            else:
                code.write(f"""data_file_name = "{st.session_state.figure_properties.filename}_data.json"
with open(data_file_name, "r") as data_file:
    data = json.load(data_file)
""")
            code.write(f"\n\n#{' Plotting Data ':-<100s}\n")
            code.write("fig, ax = plt.subplots()\n")
            code.write("""
for data_series in data:
    x_data = np.array(data_series["x_data"])
    y_data = np.array(data_series["y_data"])
    plt.plot(x_data, y_data, **data_series["plot_opts"])
    if "line_of_best_fit" in data_series:
        lobf = data_series["line_of_best_fit"]
        # Fit the data
        fit_func = fit_funcs[lobf["fit_type"]]
        fit_params, pcov = curve_fit(fit_func, x_data, y_data)
        # Take a sensible number of sample points (100, or the number of data points if that's larger)
        num_points = max(100, len(x_data))
        x_fit = np.linspace(min(x_data), max(x_data), num_points)
        y_fit = fit_func(x_fit, *fit_params)
        # Prepare for label formatting
        # This will create a dictionary with {"a": a_value, "b": b_value, ...} for however many we have
        params = {chr(ord("a") + i): param for i, param in enumerate(fit_params)}
        fit_label = lobf["plot_opts"]["label"].format(**params)
        # remove the label from the plot options
        lobf["plot_opts"].pop("label")
        plt.plot(x_fit, y_fit, label=fit_label, **lobf["plot_opts"])
""")
        code.write(f"\n\n#{' Figure Properties ':-<100s}\n")
        code.write(st.session_state.figure_properties.to_plot_code())
        code = code.getvalue()
        if not include_comments:
            code = "\n".join([l for l in code.split("\n") if not l.strip().startswith("#")])
        code = black.format_str(code, mode=black.Mode())
        st.code(code, language="python")
