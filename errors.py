import re
import streamlit as st

# handle error messages for the app

def handle_fit_error(exception, fit_type: str, data_series: str) -> str:
    # if it's a TypeError, it's probably that there are too few points
    if isinstance(exception, TypeError):
        # does it start "The number of func parameters"?
        if exception.args[0].startswith("The number of func parameters"):
            m = re.search(r"The number of func parameters=(?P<params>\d+) must not exceed the number of data points=(?P<vars>\d+)", exception.args[0])
            if m is not None:
                return f"""**Error**

It looks like you don't have enough data points for this type of fit. For a {fit_type} fit, I expect at least {m.group("params")} data points, but you only have {m.group("vars")} in the data series {data_series}."""
    # A RuntimeError is probably because the fit failed to converge
    if isinstance(exception, RuntimeError):
        # does it start "Optimal parameters not found"?
        if exception.args[0].startswith("Optimal parameters not found"):
            return f"""**Error**

It looks like your fit ({fit_type}) failed to converge for the data series {data_series}. This can happen if you have too few data points, or if the data doesn't resemble the function you're trying to fit to it."""
    return f"""**Error**

An unrecognised error has occurred. The full error message is:
```
{exception.args[0]}
```"""

def handle_latex_error(exception) -> str:
    if isinstance(exception, RuntimeError):
        if exception.args[0].startswith("latex was not able"):
            m = re.search(r"latex was not able to process the following string:\s*b'(?P<text>.*?)'", exception.args[0])
            if m is not None:
                text = m.group("text")
                context = None
                to_check = [
                    (st.session_state.figure_properties.title.text, "figure title"),
                    (st.session_state.figure_properties.x_axis.label, "$x$-axis label"),
                    (st.session_state.figure_properties.y_axis.label, "$y$-axis label")
                ]

                for s in st.session_state.data_series:
                    if s.legend_entry.show:
                        to_check.append((s.legend_entry.label, "legend entry for data series " + s.name))
                    if s.line_of_best_fit.show and s.line_of_best_fit.legend_entry.show:
                        to_check.append((s.line_of_best_fit.legend_entry.label, "legend entry for the line of best fit for data series " + s.name))

                for s in to_check:
                    if text == s[0]:
                        context = s[1]

                return f"""**Error**

I couldn't compile the following string you entered{f' for the {context}' if context is not None else ''}: 
```
{text}
```
Check that you don't have mismatched brackets or braces, and that any maths is properly enclosed in dollar signs. Also, check that any percent signs, underscores, or hashes are escaped with a backslash: `\\%`, `\\_`, and `\\#` respectively. The full error message is:
```
{exception.args[0]}
```"""
    return f"""**Error**

An unrecognised error has occurred. The full error message is:
```
{exception.args[0]}
```"""

def handle_data_error(exception, data: str) -> str:
    return f"""**Error**

I couldn't understand the data you entered:
```
{data}
```
Check that you have used one of the supported formats to separate your values: commas, tabs, spaces, or newlines. If in doubt, enter each value on a new line. The full error message is:
```
{exception.args[0]}
```"""

def handle_format_error(e, text: str) -> str:
    return f"""**Error**

There was a problem substituting the values into the string you provided:
```
{text}
```
Please check that it is a valid string. The full error message is:
```
{e.args[0]}
```"""

def handle_json_error(e):
    return e.args[0]