The [Mark My Graph](/Mark_My_Graph) page will attempt to check for several common errors in your graph. If any errors are found, they will be reported along with an explanation of why it is (usually) not good. Below is a list of the common problems which are checked.

- Markers and Lines:
    - Does each data series (and line of best fit) have a unique marker and line style?
    - Are any markers or lines too transparent? (opacity below 30%)
- Lines of Best Fit:
    - Are your lines of best fit "good"? This is evaluated based on their $R^2$ value
    - Do lines of best fit have a descriptive legend entry? This checks that any lines of best fit include at least one of their fit parameters in the legend.
- Axis Labels:
    - Do both axes have labels? (not the default "$x$" and "$y$")
    - Do both axes have units?
    - Are the font sizes (including the legend and title) reasonable?
- Legend:
    - If there are multiple data series, is there a legend?

These are evaluated, and a score is calculated. A score of 100% means that all of the above checks passed. Certain problems are considered "serious" (lack of axis labels, lack of units, and lack of legend) - these reduce your score more than other problems.

A score of 100% does not mean that your figure is perfect; these checks are fairly basic and rudimentary. Similarly, it is possible that some of these checks fail when they shouldn't. This is intended to be a guide only; use it as a checklist to help you improve your figure, but don't rely on it to tell you if your figure is good or not.