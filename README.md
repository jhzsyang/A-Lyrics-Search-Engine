# A Simple Lyrics Search Engine
Group Project for Text Technologies for Data Science 
# Dataset
* The current dataset is from [Kaggle](https://www.kaggle.com/deepshah16/song-lyrics-dataset). 
* The scraper fetches artists and related information from  [Genius](https://www.genius.com). 
* The ``create_index.py`` processes data and transforms it into``pickle`` format.
# Requirements
* Python 3.6 or above.
* ``pip install flask==1.1.2``.
* ``pip install stemming==1.0.1``.
# Run (Command):
* Run ``set FLASK_APP=search.py``.
* Run ``set FLASK_ENV=development`` (your current flask environment).
* Run ``python.exe -m flask run``.
* Click http://127.0.0.1:5000/ to see the search engine. 
# Unfinished
* Extract topic words based on (Lasso) LDA Topic models.
* Use (N-gram) Language model to analyze the relations of lyrics.
* Provide more search options and optimize the search interface.

