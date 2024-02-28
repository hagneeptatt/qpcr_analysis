# Install libraries
pip install pandas

# modules are single python files
# package is a directory that contains one or more modules
# pandas package allows data analysis of data frames
import pandas as pd
# glob finds filename patterns (module within Python's standard library thus do no need to download package first)
import glob
# os module provides useful functions for working with files and directories
# modules withing Python's standard library
import os

# Define path of excel files
# Use of r'' allows string to be interpreted as raw string
#  Thus \ is not interpreted as a special character

path = r'C:\Users\mbgm4fs3\OneDrive - The University of Manchester\PhD\Experimental\Data\Mechanical Stimulation\Main study\Y201\qPCR'


# Import all excel files in directory into pandas using glob
# create empty list li and use for loop to append excel files to list

excel_files = glob.glob(path + "/*.xls")

# Initialise empty dictionary to store all data frames
# dictionary assigns keys to values e.g. filename, rather than indices (numbers) to values
# In examples values are the data frames and kays will be the filenames
dictionary = {}

# Loop through each Excel file and read it into a DataFrame
for file in excel_files:
    # extract filename without extension
    filename = file.split('/')[-1].split('.')[0]
    # read excel file into dataframe, for qPCR data - header start at row 8
    # no index collumn so indexing is down by row number
    df = pd.read_excel(file, index_col=none, header=7)
    dictionary[filename] = df

