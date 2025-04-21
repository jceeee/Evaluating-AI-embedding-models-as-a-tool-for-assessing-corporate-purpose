import gc
import multiprocessing
import os
from multiprocessing.pool import AsyncResult
from typing import NoReturn, List
import traceback

import openai
import pandas as pd
from embeddings_utils import get_embeddings, cosine_similarity
from pandas import DataFrame

from config import Website

client = openai.OpenAI()

def websiteSearch(websiteName: str, websiteIndex: int) -> NoReturn:
    print(f"Website {websiteName} {websiteIndex}/{len(config.websites)} Start")
    try:
        folderNameEmbeddingPartial = os.path.join(config.folder, websiteName, 'embeddings')

        # partial embeddings folder has to exist
        if not os.path.exists(folderNameEmbeddingPartial):
            raise AssertionError(f"\tPartial Embeddings folder does not exist for website {websiteName}. Did you forget to run openAiSearch-getEmbedding.py?")

        # check if results already saved
        skip = True
        skipDict: dict[str, bool] = {}
        for searchPrompt in config.searchPrompts:
            fileNameSearchHits = os.path.join(folderNameSearch, searchPrompt.name, websiteName + "_search.csv")
            if os.path.exists(fileNameSearchHits):
                skipDict[searchPrompt.name] = True

                # add to hitList
                # df_result = pd.read_csv(fileNameSearchHits).dropna()
                # df_result.similarities.astype(float)
                # searchPrompt.hitList.append(df_result)
            else:
                skipDict[searchPrompt.name] = False
                skip = False  # can only skip if all searches are done
        if skip:
            print(f"\tWebsite {websiteName}:\tSkipping - best hits already saved. If you want to regenerate best hits then delete (or rename) files in folder {folderNameSearch}")
            return ""

        # save for each search the best hits
        searchDict: dict[str, DataFrame] = {}  # {search: hits, search2: hits2}

        # go through all partial embeddings of website
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
                # already saved this search
                if skipDict[searchPrompt.name]:
                    continue

                df_result = df_partial.copy()  # copy data for this search

                def applyFun(x):
                    print(f"Cosine similarity {websiteName}: {x.shape} {searchPrompt.embedding.shape}")
                    return cosine_similarity(x, searchPrompt.embedding)

                df_result["similarities"] = df_result.embedding.apply(lambda x: cosine_similarity(x, searchPrompt.embedding))  # similarity of text and prompt
                df_result = df_result.drop(columns=['Sentence', 'embedding'])  # cut away embedding

                # combine with existing best hits
                if searchPrompt.name in searchDict:
                    df_result = pd.concat([df_result, searchDict[searchPrompt.name]], ignore_index=True)

                # only keep best hits
                # df_result = df_result.sort_values("similarities", ascending=False).head(config.searchPreserveCount)[['Company', 'combined', 'similarities']]  # cut away columns
                df_result = df_result.sort_values("similarities", ascending=False).head(config.searchPreserveCount)
                searchDict[searchPrompt.name] = df_result.copy()

                del df_result

            # release memory
            del df_partial
            gc.collect()

        # save best hits in file
        for searchPrompt in config.searchPrompts:
            fileNameSearchHits = os.path.join(folderNameSearch, searchPrompt.name, websiteName + "_search.csv")

            # only load saved results (did nothing for this search in loops before)
            if skipDict[searchPrompt.name]:
                continue

            # searched now: save in file
            df_result = searchDict[searchPrompt.name]
            df_result.to_csv(fileNameSearchHits, index=False)
            # searchPrompt.hitList.append(df_result)

        print(f"Website {websiteName} {websiteIndex}/{len(config.websites)} Finished")
        return ""
    except Exception as e:
        print(f"Error {e}")
        raise e

config = __import__("config")
# create search folder
folderNameSearch = os.path.join(config.folderResult, 'searches')
if not os.path.exists(folderNameSearch):
    os.mkdir(folderNameSearch)
if __name__ == '__main__':
    # Ensure you have your API key set in your environment per the README: https://github.com/openai/openai-python#usage

    # get embedding of search prompts
    searchPromptList = []
    for searchPrompt in config.searchPrompts:
        searchPromptList.append(searchPrompt.prompt)

        # create search hits folder
        folderNameSearchHits = os.path.join(folderNameSearch, searchPrompt.name)
        if not os.path.exists(folderNameSearchHits):
            os.mkdir(folderNameSearchHits)

    print(f"Getting embedding of {len(config.searchPrompts)} search prompts...")
    embeddingsList = get_embeddings(client, searchPromptList, model=config.embedding_model)
    print(f"Got embedding of {len(config.searchPrompts)} search prompts as {len(embeddingsList)} {len(embeddingsList[0])}")

    # save embeddings in searchPrompts
    index = 0
    for searchPrompt in config.searchPrompts:
        searchPrompt.embedding = embeddingsList[index]
        searchPrompt.hitList = []
        index += 1


    # multiple processes tutorial: https://superfastpython.com/multiprocessing-pool-python/
    if config.SEARCH_PROCESSES > 0:
        pool = multiprocessing.Pool(processes=config.SEARCH_PROCESSES)
    else:
        pool = multiprocessing.Pool()

    # search through partial embeddings of websites and save best hits
    waits: List[AsyncResult] = []
    websiteIndexLoop = 0
    for websiteLoop in config.websites:
        websiteIndexLoop += 1
        folderNameEmbeddingPartial = os.path.join(config.folder, websiteLoop.name, 'embeddings')

        # partial embeddings folder has to exist
        if not os.path.exists(folderNameEmbeddingPartial):
            raise AssertionError(f"Partial Embeddings folder does not exist for website {websiteLoop}. Did you forget to run openAiSearch-getEmbedding.py?")

        # add to pool
        print(f"Starting async {websiteIndexLoop}/{len(config.websites)} website {websiteLoop.name}")
        websiteSearch(websiteLoop.name, websiteIndexLoop)
        #wait = pool.apply_async(websiteSearch, args=(websiteLoop.name, websiteIndexLoop))
        #waits.append(wait)

    # wait for all to finish
    print(f"Waiting for processes to finish...")
    websiteIndexLoop = 0
    for asyncResult in waits:
        websiteIndexLoop += 1
        asyncResult.wait()
        if not asyncResult.successful():
            print(f"Subprocess failed website {websiteIndexLoop}/{len(config.websites)} website {config.websites[websiteIndexLoop-1].name} with error")
            asyncResult.get()
    pool.close()
    pool.join()

    print(f"Loading best hits of all websites...")
    index = 0
    for searchPrompt in config.searchPrompts:
        index += 1
        print(f"Search {index}/{len(config.searchPrompts)} for prompt name {searchPrompt.name}")

        # combine searches of websites (not from hitlist, but from website files)
        print(f"\tCombining best hits data")
        bestHits: list[DataFrame] = []
        for websiteLoop in config.websites:
            fileNameSearchHits = os.path.join(folderNameSearch, searchPrompt.name, websiteLoop.name + "_search.csv")
            df_result = pd.read_csv(fileNameSearchHits).dropna()
            df_result.similarities.astype(float)
            bestHits.append(df_result.copy())

        df_combined = pd.concat(bestHits, ignore_index=True)

        print(f"\tSearching for best hits")
        df_combined = df_combined.sort_values("similarities", ascending=False).head(config.searchResultCount)

        # save results in file
        fileNameSearchResult = os.path.join(folderNameSearch, searchPrompt.name + '_result.csv')
        df_combined.to_csv(fileNameSearchResult, index=False)  # save hits as file

    # search: prompt whole paragraph description
