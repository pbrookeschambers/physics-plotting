If you have used Python before, you may find that there are certain changes you'd like to make which are not possible using this tool. To help with this, the page [Python](/Python) provides a python script which can be used to recreate your figure yourself in python. The code given will recreate the figure exactly as it appears in the tool - use it as a starting point to make your own changes. 

There are a few options which can be used to customise the script.

###### Use `qoplots`

For the basic theming and the automatic colours, a python library called `qoplots` is used. It can be found here: [https://github.com/pbrookeschambers/qoplots](https://github.com/pbrookeschambers/qoplots). With the "Use `qoplots`" option enabled, the script will import this library and use its built-in theming. This means you can easily change the theme from within the script. 

Disabling this option will remove it as a dependency, and the script will instead include some (quite lengthy) code to recreate the theming. This is static; you cannot easily change the theme after downloading the script.

###### Inline Data

If this option is enabled, the data will be specified as part of the script. For large data sets, or for multiple data series, this can make the script rather large. Disabling this option will instead load the data from a CSV file (or a JSON file if there are multiple data series). This keeps the script small and readable, and makes it easier to change the data after downloading the script. If this option is disabled, a button will be shown to download the data file. The filename will be taken from the filename specified in the "Figure" options on the home page, suffixed with `_data`.

###### Include Comments

By default, the script will include some helpful comments to identify different regions of the script. Disabling this option will remove these comments.

###### Use $\LaTeX$

If enabled, `matplotlib` will be set to use an external $\LaTeX$ renderer for all text - this requires an available $\LaTeX$ installation.  If you do not have $\LaTeX$ installed, you can disable this option and the script will use the default renderer instead. Most of the time, this will make a slight difference to the appearance, but should not cause any errors. However, for complicated text, the default renderer may not be able to render the text correctly, and might throw an error.