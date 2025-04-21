# download python 3.8 from https://www.python.org/downloads/
# download chromedriver from https://googlechromelabs.github.io/chrome-for-testing/ NOT the normal chrome version, the version where it says chromedriver. Extract and put it in a folder chromedriver_linux64/chromedriver
# optional to use Anaconda. If not using Anaconda, jump to install

# using Anaconda: https://docs.anaconda.com/miniconda/#quick-command-line-install
venv-create:
	conda create -n paper-values python==3.8

# now you need to run
# conda activate paper-values
# to activate the virtual environment

# remove the Anaconda environment again after you're done (do not run now if you want to run the python scripts)
venv-delete:
	conda remove -n paper-values --all

# install requirements with pip
install:
	pip install -r requirements.txt

# can run normal scripts now
scrape:
	python scraping.py

# scraping.py
# combine
# openAiSearch-getEmbedding
# openAiSearch-Search

# otherModels

