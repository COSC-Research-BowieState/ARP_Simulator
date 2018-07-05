#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  4 17:41:56 2018

@author: hubert kyeremateng-boateng
"""
import numpy as np
import pandas as pd

recipes = pd.read_csv('arp_dataset.csv', header=None)
recipes.rename(columns={0: 'name'}, inplace=True)
print(np.transpose(recipes))