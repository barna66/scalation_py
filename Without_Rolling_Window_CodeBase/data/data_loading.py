import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
def load_data(data_file: str, columns = None, skip: int = 0, sort: bool = False, date: str = 'date', main_output: str = 'main_output') -> pd.DataFrame:
    """
    A function used for loading the data file and selecting features for training 

    Arguments
    ----------
    data_file: str
        the name of the dataset 
    columns: list[str]
        columns used for training in the multivariate setting
    skip: int
        ignore the first skip rows
    date: str
        the name of the date/time column 
    main_output: str
        the name of the main output column for evaluation e.g. new_deaths for the COVID dataset
           
    Returned Values
    ----------
    data : pd.DataFrame

    """
    data = pd.read_csv(data_file)
    data[date] = pd.to_datetime(data[date])           #convert string to datetime
    data[date] = [d.date() for d in data[date]]       #convert datetime to date
    data = data.iloc[skip:]                           #keep index location skip to end
    data.reset_index(inplace = True, drop = True) 
    if sort:
        data = data.sort_values(by = date)            #sort by date just to make sure
    if columns is None:
        columns = data.columns
    data = data[columns]                              #keep the column you want
    return data

def plot_data(data: pd.DataFrame):
    """
    A function used for plotting the data

    Arguments
    ----------
    data: DataFrame
        the name of the dataset 
        
    Returned Values
    ----------
    
    """
    return data.plot(subplots = True, figsize = (10, 12))

def plot_train_test(df_raw_scaled: pd.DataFrame, main_output: str, train_size:  float, train: pd.DataFrame, test: pd.DataFrame, forecasts: pd.DataFrame = None, horizon = 24) -> None:
    plt.plot(train, color='red', label='Observed Train')
    plt.plot(test, color='blue', label='Observed Test')
    if forecasts is not None:
        idx = np.arange(train_size+horizon, df_raw_scaled.shape[0], 1)
        plt.plot(idx, forecasts, color='orange', label='Forecasts')
    plt.ticklabel_format(style='plain')
    plt.title('Random Walk - ' + main_output)
    plt.legend()
    plt.show()