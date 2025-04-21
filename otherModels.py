import pandas as pd
from sentence_transformers import SentenceTransformer
import os
from embeddings_utils import cosine_similarity

config = __import__("config")
model_list=["nomic-ai/nomic-embed-text-v1.5","all-MiniLM-L6-v2","hkunlp/instructor-xl","thenlper/gte-small"]

# create search folder
folderNameSearch = os.path.join(config.folderResult, 'searches')
if not os.path.exists(folderNameSearch):
    os.mkdir(folderNameSearch)

def model_embedding(model_name):
    model_name_folder = model_name.replace("/","_")
    model = SentenceTransformer(model_name, trust_remote_code=True)

    # get embedding of search prompts
    searchPromptList = []
    for searchPrompt in config.searchPrompts:
        searchPromptList.append(searchPrompt.prompt)

        # create search hits folder
        folderNameSearchHits = os.path.join(folderNameSearch, searchPrompt.name)
        if not os.path.exists(folderNameSearchHits):
            os.mkdir(folderNameSearchHits)

    print(f"Getting embedding of {len(config.searchPrompts)} search prompts...")
    embeddingsList = model.encode(searchPromptList)
    print(f"Got embedding of {len(config.searchPrompts)} search prompts as {len(embeddingsList)} {len(embeddingsList[0])}")

    # save embeddings in searchPrompts
    index = 0
    for searchPrompt in config.searchPrompts:
        searchPrompt.embedding = embeddingsList[index]
        searchPrompt.hitList = []
        index += 1

    # get embedding of text
    websiteIndex = 0
    for website in config.websites:
        websiteIndex += 1
        folderNameCsv = os.path.join(config.folder, website.name, 'csv')
        folderNameEmbeddingPartial = os.path.join(config.folder, website.name, 'embeddings'+ model_name_folder)

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
            combinedList = df['combined'].tolist()
            df['embedding'] = model.encode(combinedList).tolist()
            df.to_pickle(resultFileName)
            files.pop(0)

        # save for each search the best hits
        searchDict: dict[str, DataFrame] = {}  # {search: hits, search2: hits2}

        #combine partial embeddings into one data frame
        files = os.listdir(folderNameEmbeddingPartial)
        filesLength = len(files)
        filesCounter = 0
        while len(files) > 0:
            filesCounter += 1
            if filesCounter % config.SEARCH_LOG_EVERY == 0:
                print(f"Website {websiteName} {websiteIndex}/{len(config.websites)}: Progress: {round(100*filesCounter/filesLength)}% = {filesCounter}/{filesLength} partial embeddings")

            fname = files.pop(0)
            try:
                df_partial = pd.read_pickle(str(os.path.join(folderNameEmbeddingPartial, fname))).dropna()
            except Exception as e:
                print(f"Website {websiteName}: Error {type(e)} {e} with file {fname}. Skipping - check later (the corresponding .csv) if relevant.")
                continue
            # df_partial["embedding"] = df_partial.embedding.apply(eval).apply(np.array)

            # go through searches and find best fit
            for searchPrompt in config.searchPrompts:
                df_result = df_partial.copy()  # copy data for this search

                def applyFun(x):
                    print(f"Cosine similarity {websiteName}: {x.shape} {searchPrompt.embedding.shape}")
                    return cosine_similarity(x, searchPrompt.embedding)

                df_result[searchPrompt.name] = df_result.embedding.apply(lambda x: cosine_similarity(x, searchPrompt.embedding))  # similarity of text and prompt
                df_result = df_result.drop(columns=['Sentence', 'embedding'])  # cut away embedding

                # combine with existing best hits
                if searchPrompt.name in searchDict:
                    df_result = pd.concat([df_result, searchDict[searchPrompt.name]], ignore_index=True)
                searchDict[searchPrompt.name] = df_result.copy()
        
        # combine results
        df_all = pd.DataFrame([])
        for searchPrompt in config.searchPrompts:
            if df_all.empty:
                df_all = searchDict[searchPrompt.name]
            else:
                df_all[searchPrompt.name] = searchDict[searchPrompt.name][searchPrompt.name]
        
        df_all.to_csv(os.path.join(config.folderResult,model_name_folder+".csv"))


    # Compute cosine similarities
    # for searchPrompt in config.searchPrompts:
    #     df[searchPrompt.name] = df.embedding.apply(lambda x: cosine_similarity(x, searchPrompt.embedding))  # similarity of text and prompt

    # df_result.to_csv(os.path.join(config.folderResult,model_name_folder+".csv"))

for model_n in model_list:
    model_embedding(model_n)
