# toperrors
toperrors is a program for extracting parameter values and uncertainties
from a series of TOPAS .inp or .out files and depositing said values into a
text file, such that they can be easily read by plotting software.

## How to use
### Things to vary in the toperrors.py file
1. ```fnames```: a list of file names to read; the example code uses an
```fpath``` variable and a basic list comprehension.
2. ```out_name```: file name to write the values to once they're extracted.
3. ```extra_values```: a list of values beyond the normal structural values
to read out. Add as required (e.g. 'gof' might be wanted). Values that
appear in ```extra_values``` but not in the files themselves will not raise
errors.
4. ```macro_keys```: a list of macro keywords for macros that values are
required from.
5. ```macro_structures```: TOPAS is very flexible in how it allows macros
to be defined, but this is a nightmare for reading the .inp/.out files. As a
result toperrors requires a structure for each macro keyword. Each structure
is a list of values corresponding to the variables within the macro brackets
(i.e. n+1 values are required, where n is the number of commas within the 
brackets). These values are: (i) 0 for an ignored value (e.g. 
```TOF_Strain_G``` takes t1 as an argument, but that isn't a varied 
parameter); (ii) 1 for when a parameter name or @ or blank space is 
expected; (iii) 2 for when a parameter value is expected (this can still take the form of ```prm_name prm_value```).
### Running the functions
Once the above variables have been adjusted and toperrors.py run, then the
relevant line of code is:
    get_multiple_values(out_name, fnames, extra_values, macro_keys,
                        macro_structures)
This will output a text file with the first line as the saved parameter
names, followed by columns of the parameter values themselves.
```get_multiple_values``` takes a number of keyword arguments, which can
be listed by typing ```help(get_multiple_values)``` in the python console.
It returns a list of missing files (in case that is required).
