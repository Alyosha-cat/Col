# Modulated Neural ODEs (MoNODE)

Pytorch implementation of Modulated Neural ODEs on AIS data with modification of original code from https://github.com/IlzeAmandaA/MoNODE

## Modifications and added parts:
Preprocessing of AIS data is added : `Preprocess.ipynb`

Data loader modified to load AIS dataset : `data/config.yml`, `data/data_gen.py`, `data/data_utils.py`

Data specific parts of model are modified to make it apply on AIS data : `model/core/vae.py`, `model/core/inv_enc.py`, `model/model_misc.py`

Experiment conductor is added : `Run.ipynb`

Result viewer : Not added, just accessed to the log file saved and checked the test MSE

## Environment setting
You can check the relevant packages in `requirements.txt` (adding a few packages is done cause there are some uncommented packages which is necessaty to run the model)

## Data
AIS data is used for experiment.

But Data is non-public, so it cannot be shared. (Before uploading to github AIS datasets stored in `AIS` folder are removed)

If you want to test on similar dataset, you can use https://www.kaggle.com/datasets/bwandowando/2021-noaa-ais-dataset?resource=download

But features used has different name, so you need to adjust `Preprocess.ipynb` to apply above dataset which is accessible.

You need to adjust data loader parts before applying your own dataset. 

## Train

To the train the models run the `Run.ipynb` file. Relevant arguments are predefined in the code. So, you can just run it if you have adjusted. 

You can still use commands to replicate the results of the MoNODE paper.

## Results

All log files, and trained model will be stored automatically in a results folder.

