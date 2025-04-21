# Evaluating-AI-embedding-models-as-a-tool-for-assessing-corporate-purpose
code: website scraping, employing AI embedding models, calculating cosine similarities | results: manual scoring sentences, cosine similarities each model, Hollensbe value, definition length

Downloading the python dependencies can be done by running:
```bash
make venv-create
conda activate paper-values
make install
```

First, edit the websites to analyze in `config.py`, then running the models can be done by running:
```bash
python scraping.py
python combine.py
python openAiSearch-getEmbedding.py
python openAiSearch-Search.py
python otherModels.py
```
