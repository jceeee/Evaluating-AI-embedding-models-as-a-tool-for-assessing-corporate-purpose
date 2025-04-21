import os.path
import re
import tiktoken

config = __import__("config")

# encoding: can encode text into tokens
embedding_encoding = "cl100k_base"
encoding = tiktoken.get_encoding(embedding_encoding)


# function creates new csv with this index, returns new file
def csv_create(folder, index):
    csvName = os.path.join(folder, f"{website.name}-{index}.csv")
    csv = open(csvName, 'w')
    csv.truncate()
    csv.write("Company,Sentence\n")
    return csv


# go through all websites
websiteCount = 0
websiteLength = len(config.websites)
character_check = config.ai_token_limit  # check tokens if text is longer than these characters - 1 token approx. 4 characters so should be safe
for website in config.websites:
    websiteCount += 1
    folderNameText = os.path.join(config.folder, website.name, 'text')
    filename = os.path.join(config.folderResult, website.name + '.txt')

    # create result file
    linesKnown = set()
    file = open(filename, 'w')
    file.truncate()
    files = os.listdir(folderNameText)
    print(f"Combining text of website {website.name} ({websiteCount}/{websiteLength}): Combining {len(files)} files")
    for fname in files:
        f = open(os.path.join(folderNameText, fname), 'r')
        lines = f.readlines()
        # only add lines which are unknown
        for line in lines:
            # text cleanup: words which are not correctly split e.g. "wordThen",
            text = re.sub("([a-z])([A-Z])", "\\1. \\2", line).replace(" ", " ").replace("​", "").replace(" ", " ")

            # replace special characters
            text = re.sub('[^A-Za-z0-9.?! \\-,äöüÄÖÜ\']+', '', text)
            if text in linesKnown:
                continue
            linesKnown.add(text)
            file.write(text + "\n")
        f.close()
    file.close()

    # read all text
    file = open(filename, 'r')
    text = file.read()
    file.close()

    # create csv folder
    folderNameCsv = os.path.join(config.folder, website.name, 'csv')
    if not os.path.exists(folderNameCsv):
        os.mkdir(folderNameCsv)

    # split into sentences
    sentences = re.split("([^.?!]*[.?!]+)", text)

    # create first result csv
    csvIndex = 0
    csv = csv_create(folderNameCsv, csvIndex)
    csvCount = 0
    for sentence in sentences:
        sentence = sentence.replace("\"", "'").replace("\n", " ").strip()
        if len(sentence) <= 5:
            continue
        if re.search("\dkg[ .;]",sentence) is not None:
            continue
        if sentence[0] == ",":
            continue
        if re.search("\w",sentence) == None: # no letters in string
            continue
        if sentence[0].islower(): # first letter is lower case
            continue
        if sentence.endswith("org."):
            continue
        # check text length - AI can only handle max_tokens at once
        if len(sentence) > character_check:
            if len(encoding.encode(sentence)) > config.ai_token_limit:
                print(
                    f"Warning: Skipped a line at website {website} that has {len(sentence)} characters. Check if punctuation (e.g. '?.!') is missing: {sentence}")
                continue  # just skip sentences longer than this - should not exist
        csv.write(f"\"{website.name}\",\"{sentence}\"\n")

        csvCount += 1
        # create new csv
        if csvCount >= config.ai_rate_limit:
            csv.close()
            csvCount = 0
            csvIndex += 1
            csv = csv_create(folderNameCsv, csvIndex)
    csv.close()
