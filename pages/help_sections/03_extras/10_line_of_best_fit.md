A line of best fit can be added to any data series. If the sidebar on the left is not already shown, expand it using the small right arrow in the top left. Under "Options" in the "Data" section, you will see a dropdown to select the data series you want to edit. If you only have one set of data, this dropdown will not be shown.

##### Enable line of best fit

Below the expandable "Data Series" section is a switch to enable the line of best fit. Enabling it will add a line of best fit with the default settings (which is linear). Disabling it will remove the line of best fit, but keep any settings you have changed.

##### Line of best fit type

Once enabled, an expandable "Line of Best Fit" section will be shown. Expand it to see a dropdown for the fit type. There are six options:
- Linear, $y = a x + b$
- Quadratic, $y = a x^2 + b x + c$
- Cubic, $y = a x^3 + b x^2 + c x + d$
- Exponential, $y = a e^{b x} + c$
- Logarithmic, $y = a \ln(b x) + c$
- Sinusoidal, $y = a \sin(b x + c) + d$

Choosing an option will update the fit on the plot. There are a few ways this can fail, but primarily each fit type expects a minimum number of data points. Make sure your data has enough points for the fit type you want to use. You'll be notified if that is not the case.

##### Line Options

Under the "Line" heading, you'll find options for the line styling of the line of best fit. These are identical to the options for the data series line style. See the Line Styles section for more information.

##### Legend Entry

The line of best fit can be included in the legend. To do so, enable the "Show in Legend" switch. This will show an additional field for the legend entry. See the sections Maths In Text and Units In Text for more information on formatting this.

###### Including Fit Parameters

In addition to the normal maths and units which can be included, for the line of best fit there are some special options. Each fit type calculates a number of parameters, labelled $a$, $b$ etc. For example, the linear fit calculates the gradient $a$ and the $y$-intercept $b$. You may wish to include these in the legend entry. To do so, there is a special syntax. `fit{a}` will be replaced by the value of $a$, `fit{b}` by $b$ etc. For example, with a linear fit you might want your legend entry to be `Gradient $g = fit{a}$`, which might be rendered as "Gradient $g = 2.377265921$". Note that the parameter names are case sensitive.

By default, these are included to a high precision. This may not always be desireable, so the number of decimal places can be set. Use a colon (`:`) to separate the parameter name from the format specifier. For a simple number with a given number of decimal places, use `fit{a:.2f}` for $2$ decimal places. This might be rendered as "$2.38$". Instead, scientific notation can be used; use `fit{a:.3e}`, which might be rendered as "$3.227\text{e}-4$".