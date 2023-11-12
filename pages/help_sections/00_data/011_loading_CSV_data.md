Data can also be added from a `.csv` file. This is done in the "Data" panel on the right hand side. Switch this panel to the "Add From CSV" tab. You'll be presented with a file upload button. Either drag-and-drop a `.csv` (or `.tsv` etc.) file onto this area, or click the "Browse" button to upload a file from your computer.

When you upload a `.csv` file, the app will attempt to work out the format of the file and extract the data. If this is successful, you'll see an expandable "Options" section, and a table of your data. If the app can't determine the format of the file, you'll see an error message and the "Options" section, but the table will not be shown. In this case, you'll need to manually specify some properties of the file.

In either case, expanding the "Options" section will allow you to specify the following properties of the file:
 - **Delimiter**: The character used to separate values in the file.
 - **Comment Character**: Any lines which start with this character will be ignored.
 - **Header Rows**: The number of rows at the top of the file which contain headers, and should be ignored.
 - **Footer Rows**: The number of rows at the bottom of the file which should be ignored.
 - **X Column**: The column which contains the $x$ data.
 - **Y Column**: The column which contains the $y$ data.
 - **Name**: The name of the data series. This is identical to the "Name" field when adding data manually.

Once you've specified these options, click the "Add Data" button to add the data series to the plot. This will not clear the `.csv` file, since it's common to add multiple data series from the same file. If you want to clear the file, click the "Clear CSV" button; this will reset the panel to its initial state, ready for a new file to be uploaded. It does not clear any data which has already been added to the plot.