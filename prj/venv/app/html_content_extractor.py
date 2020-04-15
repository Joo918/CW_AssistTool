import requests
from bs4 import BeautifulSoup
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords

from nltk.stem import PorterStemmer

import numpy as np
import pandas as pd
import re
import mturkHITcreator as mh

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

swords = np.array(stopwords.words('english'))
ps = PorterStemmer()

requested_desc = None
collectedURLs = []
collecting = False

def addURL(url):
    if not url in collectedURLs:
        print("adding URL!")
        collectedURLs.append(url)
    else:
        print("URL already in queue!")

def update_request(desc, time):
    global collecting
    if collecting:
        return
    global requested_desc
    requested_desc = stripify(desc)
    print("updated request!")
    collecting = True
    mh.request_input(desc, time)
    mh.startCollecting()

def stripify(text):
    soup = BeautifulSoup(text, 'html.parser')

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()  # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    #print(text)
    return text

#code from https://stackoverflow.com/questions/22799990/beatifulsoup4-get-text-still-has-javascript
def getContentFromURL(req_url):
    r = requests.get(url=req_url)
    #print(r.content)
    text = stripify(r.content)
    return text

#old method for converting to bag-of-words representation. Not used anymore
def convertToBagOfWords(text):
    arr = np.array(re.split("[.,\s\n;:\|‘’\"\'\(\)]+", text))

    arr2 = []
    #stem
    for w in arr:
        arr2.append(ps.stem(w))

    u, c = np.unique(arr2, return_counts=True)
    new_u = []
    new_c = []
    for i in range(u.size):
        if not u[i] in swords:
            new_u.append(u[i])
            new_c.append(c[i])
    d = {'words': new_u, 'count': new_c}
    return pd.DataFrame(data=d)

#called after all URLs are collected.
#collect content from urls, perform tf-idf, and use cosine-similarity to retrieve ordered list of relevant urls.
def getRankedList():
    docs = []
    docs.append(requested_desc)
    for i in collectedURLs:
        docs.append(getContentFromURL(i))
    tfidf_result = tfidf(tuple(docs))
    cosSim_result = np.array(cosSim(tfidf_result)[0])
    print("cos sim results....")
    print(cosSim_result)
    orderedIndices = cosSim_result.argsort()[::-1]
    print("order of the documents.....")
    print(orderedIndices[1:] - 1)
    npurls = np.array(collectedURLs)[orderedIndices[1:] - 1]
    return npurls.tolist()


def tfidf(list_of_docs):
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(list_of_docs)
    #namelist = vectorizer.get_feature_names()
    #X = X.transpose()
    return X #pd.DataFrame(data=X.todense(),index=namelist, columns=np.arange(len(list_of_docs)))

#performs cosine similarity calculation between first document and the rest of the documents.
def cosSim(vectorspace):
    return cosine_similarity(vectorspace[0:1], vectorspace)

################################TESTING GROUND############################################

#query = "I want to know about machine learning. I especially want to know what are ethical and what are not. What problems do machine learning have?"
#txt = getContentFromURL("https://github.com/JCDetwiler/batch-size-mnist")
#txt2 = getContentFromURL("https://www.cs.ox.ac.uk/efai/towards-a-code-of-ethics-for-artificial-intelligence/what-are-the-issues/ai-ethics-fails-case-studies/")
#txt3 = getContentFromURL("https://www.propublica.org/article/facebook-enabled-advertisers-to-reach-jew-haters")

#tfidf_result = tfidf((query,txt,txt2,txt3))
#print(tfidf_result)
#cosResult = cosSim(tfidf_result)
#print(cosResult)

#update_request("I want to know about machine learning. I especially want to know what are ethical and what are not. What problems do machine learning have?")
#addURL("https://github.com/JCDetwiler/batch-size-mnist")
#addURL("https://www.cs.ox.ac.uk/efai/towards-a-code-of-ethics-for-artificial-intelligence/what-are-the-issues/ai-ethics-fails-case-studies/")
#addURL("https://www.propublica.org/article/facebook-enabled-advertisers-to-reach-jew-haters")
#print(getRankedList())