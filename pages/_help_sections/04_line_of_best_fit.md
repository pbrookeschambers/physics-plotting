In order to add a line of best fit to a data series, enable the "Line of Best Fit" option. This will show a new section, which can be expanded to see the available options. Firstly, there is a dropdown to select the type of fit, which is one of:
- Linear
- Quadratic
- Cubic
- Exponential
- Logarithmic
- Sinusoidal
            
Below this dropdown, the exact equation of the fit is given in terms of $x$. The fit parameters are listed as $a$, $b$, etc. These are the values which will be modified to optimise the fit to your data. They are also the names by which these parameters may be referenced in the legend (see below). Below this you'll find options for the line style, as described above.
            
Below the line style options is the option to show the line in the legend. If enabled, an additional text field will be shown for the label. In this field, you can use maths as normal (see Maths and Units), but you can also reference the fit parameters by name. To do so, use `fit{...}`. For example, the linear fit will fit an equation $y = ax + b$, so your label could read `$y = fit{a}x + fit{b}$`, which may be displayed as $y = 1.423457224x + 0.1221351663$. 
            
By default, the parameters will be given to a high precision. This is often not desirable. You can specify a number of decimal places (and other formatting options) within the fit parameter. Use a colon (`:`) to separate the fit parameter from the format specifier. Then, use `.2f` for 2 decimal places, `.3f` for 3 decimal places, etc. For example, `$y = fit{a:.2f}x + fit{b:.3f}$` may be displayed as $y = 1.42x + 0.122$. Sometimes, you might also want to use scientific notation. To do this, use `e` instead of `f`. If $a = 1.42664\times10^{3}$, then `fit{a:.1e}` would be rendered as $1.4e3$.