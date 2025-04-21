import os
import pandas as pd
import openai
from embeddings_utils import get_embeddings
import time

# from openai.error import RateLimitError

config = __import__("config")

client = openai.OpenAI()

# only wait if sent something before
before = False

websiteIndex = 0
for website in config.websites:
    websiteIndex += 1
    folderNameCsv = os.path.join(config.folder, website.name, 'csv')
    folderNameEmbeddingPartial = os.path.join(config.folder, website.name, 'embeddings')

    # need to make csv first
    if not os.path.exists(folderNameCsv):
        print(f"Warning: {website.name} has no csv files saved. Did you forget to run combine.py first?")
        continue

    # create partial embeddings folder
    if not os.path.exists(folderNameEmbeddingPartial):
        os.mkdir(folderNameEmbeddingPartial)

    # make embedding of part csv files
    files = os.listdir(folderNameCsv)
    while len(files) > 0:
        fname = files[0]
        print(f"{websiteIndex}/{len(config.websites)} website {website.name} missing {len(files)} partial csv files. At file {fname}")

        # CSV to PKL filename
        resultFileName = str(os.path.join(folderNameEmbeddingPartial, fname))[:-4] + '.pkl'
        if os.path.exists(resultFileName):
            print(f"Info: Skipping {website.name}: {fname} - partial embedding saved.")
            files.pop(0)
            continue

        df = pd.read_csv(str(os.path.join(folderNameCsv, fname))).dropna()
        df['combined'] = df.Sentence.str.strip()

        # make embedding
        if before:
            time.sleep(0.1)  # rate limit
        before = True

        try:
            combinedList = df['combined'].tolist()
            df['embedding'] = get_embeddings(client, combinedList, model=config.embedding_model)
        except openai.RateLimitError:
            print(f"Rate Limit Error: waiting some time at {fname}, missing {len(files)} partial csv files")
            time.sleep(10)
            continue
        df.to_pickle(resultFileName)
        files.pop(0)
