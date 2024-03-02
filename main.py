# modules are single python files
# package is a directory that contains one or more modules

# pandas package allows data analysis of data frames
import pandas as pd

# glob finds filename patterns (module within Python's standard library thus do no need to download package first)
import glob

# os module provides useful functions for working with files and directories
import os

# import numpy to perform numerical computations on data i.e. calculating IQR for outlier detection
import numpy as np


# Define path of excel files
# Use of r'' allows string to be interpreted as raw string
#  Thus \ is not interpreted as a special character
path = r'C:\Users\mbgm4fs3\OneDrive - The University of Manchester\PhD\Experimental\Data\Mechanical Stimulation\Main study\Y201\qPCR'


# Import all excel files in directory into pandas using glob
# glob creates a list containing all excel file names
# create empty list li and use for loop to append excel files to list

excel_files = glob.glob(path + "/*.xls")

# Initialise empty list to store all data frames
# dictionary assigns keys to values e.g. filename, rather than indices (numbers) to values
# list assignms numerical index to values
df_dictionary = {}

# Loop through each Excel file and read it into a DataFrame
# 'file' is just a placeholder for each item in the iterable list i.e. excel_files list
for file in excel_files:
    # extract filename without extension
    # splits path string by first '.' instring [0] and first '\' from the end [-1]
    # indexing starts at 0 in python
    # negative index counts position backwards from end of list/tuple
    filename = file.split('\\')[-1].split('.')[0]

    # read excel file into dataframe, for qPCR data - header start at row 8
    # no index collumn so indexing is down by row number
    df = pd.read_excel(file, header=7)


    # create new dataframe with only desirable collumn data
    # want sample name, gene target name and CT value
    # indexing multiple collumns required double square brackets
    df = df[['Sample Name', 'Target Name', 'Cт']]

    # drops rows with NaN
    df = df.dropna()

    # Create new dataframe taking all rows without 'undetermined' string
    # in Ct collumn using boolean indexing
    # In boolean indexing, we will select subsets of data based on the actual
    # values of the data in the DataFrame and not on their row/column labels or integer locations.
    # In boolean indexing, we use a boolean vector to filter the data
    #
    # Boolean data type = a form of data with only two possible values e.g. True or False
    # Create boolean mask
    mask = df['Cт'] != 'Undetermined'
    # Apply mask to filter out rows containing string
    df = df[mask]

    # convert ct collumn to numerical values so we can perform aggregate and statistical operations later
    df['Cт'] = pd.to_numeric(df['Cт'])

    # Create new dataframe which groups data by sample name and target gene name
    # use agg() function to perform aggregate operations to data e.g. mean, std, sum, count etc.
    grouped_df = df.groupby(['Sample Name', 'Target Name'])

    # Detect outliers using 1.5 x IQR rule
    # first calculate Q1 and Q3 of grouped data using quantile function from numpy package
    # the quantile is worked out based on rank order of values e.g. 0.5 quantile = median
    # pandas automatically applies any function, i.e. quantile(), to each group seperately within a grouped dataframe
    # This behaviour is inherent to 'groupby()' functionality in panda

    Q1 = grouped_df['Cт'].quantile(0.25)
    Q3 = grouped_df['Cт'].quantile(0.75)
    IQR = Q3 - Q1

    # Define upper and lower bound for outlier detection using 1.5 X IQR rule
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Filter out outliers from each group
    # This code uses the apply() function which allows you to apply a function along an axis of a dataframe or series
    # this can be useful for aggregating and transforming data
    # the function applies is a lambda function, aka anonymous function, which are small, inline functions defined without a name
    # lambda functions are useful when you need a simple function for a short period of time e.g. for one line of code
    # In this code lambda function takes one argument 'x' representing the grouped dataframe its being iterated over
    # x['Ct'] indexes the Ct collumn from the grouped dataframe
    # this codes only keeps data which is between lower and upper bound, filtering out other data with a boolean mask
    # x.name represents the name of each group i.e. a tuple containing 'Sample Name' and'Target Name'
    # Using x.name allows you to calculate the lower and upper bounds specific to each group, ensuring that outliers are determined based on the quartiles and IQR of each individual group's 'Cт' values.
    filtered_groups = grouped_df.apply(lambda x: x[(x['Cт'] >= lower_bound[x.name]) & (x['Cт'] <= upper_bound[x.name])], include_groups=False)

    # Iterate through each group in the DataFrame
    # need to groupby() again as we have applied a function to the previously grouped object, thus resulting in
    # a combined data frame (split-apply-combine)
    for group_key, group_value in filtered_groups.groupby(['Sample Name', 'Target Name']):
        # state CT variable from the group_value index
        CT = group_value['Cт']
        # if loop, whne the number of CT values within the group is 3, we perform some vector operations to calculate the absolute differences between all combinations of CT value within that group
        # this is done by subtracting a 1D row vectors containing the CT values from a 2D collumn vector containing the same CT values (transpose of 1D row vector)
        # This produces a 2D matrix containing all the possible absolute differences between CT combinations
        if len(group_value) == 3:
            # calculate differences between CT values
            diffs = abs(group_value.values[:,None] - group_value.values)
            # find the maximum differences
            max_diff = np.max(diffs)
            # check is max difference exceeds threshold of 1
            if max_diff > 1:
                # find index of the samples with the max difference
                max_diff_index = np.unravel_index(np.argmax(diffs), diffs.shape)
                # drop corresponding row from group
                group_value.drop(group_value.index[max_diff_index[0]])



        print(max_diff_index)
        print(group_value)
        print('BREAKKKKKK')
    df_dictionary[filename] = filtered_groups
