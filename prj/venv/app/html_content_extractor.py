import requests
from bs4 import BeautifulSoup
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords

from nltk.stem import PorterStemmer

import numpy as np
import pandas as pd
import re

from sklearn.feature_extraction.text import TfidfVectorizer

swords = np.array(stopwords.words('english'))
ps = PorterStemmer()

requested_desc = None
requested_tags = None

def update_request(desc, tags):
    global requested_desc
    global requested_tags
    requested_desc = desc
    requested_tags = tags
    print("updated request!")

def getContentFromURL(req_url):
    r = requests.get(url=req_url)
    #print(r.content)
    soup = BeautifulSoup(r.content, 'html.parser')

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

    return text
    #print(text)

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

def tfidf(list_of_docs):
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(list_of_docs)
    namelist = vectorizer.get_feature_names()
    X = X.transpose()
    return pd.DataFrame(data=X.todense(),index=namelist, columns=np.arange(len(list_of_docs)))

def getRankedListAndTags(list_of_docs):
    tfidf_result = tfidf(list_of_docs)



#txt = getContentFromURL("https://github.com/JCDetwiler/batch-size-mnist")
#txt2 = getContentFromURL("https://www.cs.ox.ac.uk/efai/towards-a-code-of-ethics-for-artificial-intelligence/what-are-the-issues/ai-ethics-fails-case-studies/")
#txt3 = getContentFromURL("https://www.propublica.org/article/facebook-enabled-advertisers-to-reach-jew-haters")

#tfidf_result = tfidf([txt,txt2,txt3])
#print(tfidf_result)