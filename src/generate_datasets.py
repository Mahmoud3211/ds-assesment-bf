import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os
from tqdm import tqdm
from helpers.datasets import Datasets

datasets = Datasets()

def main():
    
    datasets.generate_datasets()
    

if __name__ == "__main__":
    main()
