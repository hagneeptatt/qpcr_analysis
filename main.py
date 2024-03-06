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

excel_files = glob.glob(path + "/*.xls")


# Initialise empty list to store all data frames
# dictionary assigns keys to values e.g. filename, rather than indices (numbers) to values
# list assignms numerical index to values
df_dictionary = {}

# Loop through each Excel file and read it into a dataframe
# 'file' is just a placeholder for each item in the iterable list i.e. excel_files list
# this for loop reads the data in a cleans it
for file in excel_files:
    # extract filename without extension
    # splits path string by first '.' instring [0] and first '\' from the end [-1]
    # indexing starts at 0 in python
    # negative index counts position backwards from end of list/tuple
    filename = file.split('\\')[-1].split('.')[0]

    # read excel file into dataframe, for qPCR data - header start at row 8
    # no index collumn so indexing is down by row number
    df = pd.read_excel(file, header=7)

    # Lete rename the CT collumn header as it uses strange syntax for CT, requiring us to copy and paste. Therefore lets change it to CT.
    # inplace = True means the dataframe is renamed in place rather than returning a copy when inplace = False, which is the default. if we used the latter we would require df = df.rename() to replace our dataframe with the new copy
    df.rename(columns = {'Cт':'CT'}, inplace = True)

    # create new dataframe with only desirable collumn data
    # want sample name, gene target name and CT value
    # indexing multiple collumns required double square brackets
    df = df[['Sample Name', 'Target Name', 'CT']]

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
    mask = df['CT'] != 'Undetermined'
    # Apply mask to filter out rows containing string
    df = df[mask]

    # convert ct collumn to numerical values so we can perform aggregate and statistical operations later
    df['CT'] = pd.to_numeric(df['CT'])

    # Create new dataframe which groups data by sample name and target gene name
    # use agg() function to perform aggregate operations to data e.g. mean, std, sum, count etc.
    # Grouping by several collumns results in a dataframe with multi-index (aka hierachihcal index)
    grouped_df = df.groupby(['Sample Name', 'Target Name'])

    # Detect outliers using 1.5 x IQR rule
    # first calculate Q1 and Q3 of grouped data using quantile function from numpy package
    # the quantile is worked out based on rank order of values e.g. 0.5 quantile = median
    # pandas automatically applies any function, i.e. quantile(), to each group seperately within a grouped dataframe
    # This behaviour is inherent to 'groupby()' functionality in panda

    Q1 = grouped_df['CT'].quantile(0.25)
    Q3 = grouped_df['CT'].quantile(0.75)
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
    # Using x.name allows you to calculate the lower and upper bounds specific to each group, ensuring that outliers are determined based on the quartiles and IQR of each individual group's 'CT' values.
    filtered_groups = grouped_df.apply(lambda x: x[(x['CT'] >= lower_bound[x.name]) & (x['CT'] <= upper_bound[x.name])], include_groups=False)

    # Iterate through each group in the DataFrame
    # need to groupby() again as we have applied a function to the previously grouped object, thus resulting in
    # a combined data frame (split-apply-combine)
    for group_key, group in filtered_groups.groupby(['Sample Name', 'Target Name']):

        # Get the number of samples within the group
        num_value = len(group)

        # state threshold value
        threshold = 1

        # If only one CT value is present, remove it
        # .loc() allows us ot access a group of rows and collumns by the labels being looped
        if num_value == 1:
            filtered_groups.loc[group_key] = None
        elif num_value == 2:
            # If 2 CT values are present, check that the absolute difference between them is less than threshold apart
            diff = np.abs(group['CT'].values[0] - group['CT'].values[1])
           # if the differece is above threshold, remove both CT value
            if diff > threshold:
                filtered_groups.loc[group_key] = None
        else:
            # for 3 CT values, work out the median and remove CT value than are greater than threshold away from median
            median_ct = np.median(group['CT'].values)
            diff = np.abs(group['CT'].values - median_ct)
            # check if any of the calculates diffrences beween ct and median are above threshold and remove CT values that are above threshold
            if np.any(diff > threshold):
                group = group[diff <= threshold]
            # if all CT values are more than threshold apart from median, remove them all
            elif np.all(diff > threshold):
                filtered_groups.loc[group_key] = None

            # update original dataframe with the modified group
            filtered_groups.loc[group_key] = group

    # drop NaN values from filtered groups
    filtered_groups = filtered_groups.dropna()


    ## This section of the for loop calculates 2^-dCT for each datafram

    # first we calculate the mean CT values for each sample and target gene by grouping the data and using mean function
    CT_mean = filtered_groups.groupby(['Sample Name', 'Target Name'])['CT'].mean()

    # We can now reset the index of the dataframe so that the levels 'Sample Name' 'Target Nmae' now become collumn headers again. As our CT collumn now only contains one value, this makes it easier to index out data when calculating dCT and ddCT
    CT_mean = CT_mean.reset_index()


    # Heres where you can input the string for your housekeeping gene i.e. GAPDH
    housekeeping_name = 'GAPDH'

    # Create new independent dataframes for houskeeping gene and target genes
    control_CT_mean = CT_mean[CT_mean['Target Name'] == housekeeping_name]
    target_CT_mean = CT_mean[CT_mean['Target Name'] != housekeeping_name]


    # Merge the housekeeping and target dataframes based on the key 'Sample Name' i.e. d1, d7, d21_con, d21_exp on = ['Sample Name'] specifies collumn to merge on, thus rows with same sample name we be merged together. suffixes=() is optional, but ensures that we add suffixes to identify collumns which have the same name in the independent dataframes i.e 'CT' and 'Name'
    merged_df = pd.merge(target_CT_mean, control_CT_mean, on = ['Sample Name'], suffixes = ('', '_' + housekeeping_name))

    merged_df['dCT'] = merged_df['CT'] - merged_df['CT' + '_' + housekeeping_name]

    # export the merged df to csv
    merged_df.to_csv(filename + '.csv')

    # Add filtered data to dictionary the filename as the key
    df_dictionary[filename] = merged_df


## We now want to calculate 2^-ddCT for each dataframe in our new dictionary as we must select which dataframes contain our control/untreated sample data i.e. d1 alginate free swelling controls
# First, lets extract our control data by looping through our dictionary
# State suitable substring identifier within filename of control, and the corresponding control sample names
control_filename = 'alginate'
control_sample_name = 'd1'

sample1_filename = '400um'

sample2_filename = '800um'

# Create empy dataframe to containg control data
control_dictionary_d1 = {}
control_dictionary = {}

# Create empty dictionary for sample data
sample1_dictionary = {}
sample2_dictionary = {}


# for loop extracts out control data and sample data to new dictionaries
for filename in df_dictionary.keys():
    if control_filename in filename:

        # first lets extract entire control data
        control_data = df_dictionary[filename]

        # Now lets extract the the control timepoint data that we will use for ddCT calculation i.e Alginate d1 control
        # here we use boolean indexing to select subset of data within dataframe within dictionary, so all rows that contain the control sample name are indexed
        control_data_d1 = df_dictionary[filename][df_dictionary[filename]['Sample Name'] == control_sample_name]
        control_dictionary_d1[filename + 'd1'] = control_data_d1
        control_dictionary[filename] = control_data

        # now extract sample1 and sample2 data into independent dictionaries
    elif sample1_filename in filename:
        sample1_data = df_dictionary[filename]
        sample1_dictionary[filename] = sample1_data
    elif sample2_filename in filename:
        sample2_data = df_dictionary[filename]
        sample2_dictionary[filename] = sample2_data


# Now need another loop through our dictionaries to extract relevant biological replicate pairs i.e. same number after '_n' in the filename
# can iterate through keys of dictionary using for loop
# we can iterate through both keys and items within a dictionary by using the .items() method. This method returns a view object (object that changes with parent dictionary) containing the items within a dictionary as key-value tuples (same as list but immutable/can't change the items within it).
# if you have only one vairbale in the for loop it produces a tuple containing ('filename', dataframe
# if you have two variable in for loop such as in our code, you can unpack the filenames and dictionarieas into seperate variables, one for key and one for values
# we will also use the zip() function to loop through

# setup empty dictionary for final data

final_data = {}

# Iterate over each pair of dataframes from the sample and control dictionaries
for (sample1_key, sample1_data), (sample2_key, sample2_data), (control_key, control_data), (control_key_d1, control_data_d1) in zip(sample1_dictionary.items(), sample2_dictionary.items(),control_dictionary.items(), control_dictionary_d1.items()):

    # merge sample dataframes with control dataframe. The merge is done on the names within 'Target Name' to ensure each target gene row is merged
    control_merged = pd.merge(control_data[['Sample Name', 'Target Name', 'dCT']], control_data_d1[['Sample Name', 'Target Name', 'dCT']], on = ['Target Name'], suffixes = ('_' + control_filename, '_' + control_filename + '_' + control_sample_name))
    sample1_merged = pd.merge(sample1_data[['Sample Name', 'Target Name', 'dCT']], control_data_d1[['Sample Name', 'Target Name', 'dCT']], on = ['Target Name'], suffixes = ('_' + sample1_filename, '_' + control_filename + '_' + control_sample_name))
    sample2_merged = pd.merge(sample2_data[['Sample Name', 'Target Name', 'dCT']], control_data_d1[['Sample Name', 'Target Name', 'dCT']], on = ['Target Name'], suffixes = ('_' + sample2_filename, '_' + control_filename + '_' + control_sample_name))

    # Calculate ddCT by subtracting control dCT collumn by sample dCt collumn
    control_merged['ddCT'] = control_merged['dCT' + '_' + control_filename] - control_merged['dCT' + '_' + control_filename + '_' + control_sample_name]
    sample1_merged['ddCT'] = sample1_merged['dCT' + '_' + sample1_filename] - sample1_merged['dCT' + '_' + control_filename + '_' + control_sample_name]
    sample2_merged['ddCT'] = sample2_merged['dCT' + '_' + sample2_filename] - sample2_merged['dCT' + '_' + control_filename + '_' + control_sample_name]

    # Calculate 2^-ddCT
    control_merged['2^-ddCT'] = 2**(-control_merged['ddCT'])
    sample1_merged['2^-ddCT'] = 2**(-sample1_merged['ddCT'])
    sample2_merged['2^-ddCT'] = 2**(-sample2_merged['ddCT'])

    # convert final merged data sets to CSV
    control_merged.to_csv(control_key + '_results.csv')
    sample1_merged.to_csv(sample1_key + '_results.csv')
    sample2_merged.to_csv(sample2_key + '_results.csv')









