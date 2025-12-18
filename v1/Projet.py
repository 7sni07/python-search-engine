import praw
import requests
import xmltodict
from datetime import datetime
from Corpus import Corpus
from Document import Document, ArxivDocument, RedditDocument
from DocumentGenerator import DocumentGenerator

reddit = praw.Reddit(client_id='1bn0-J4XhJYm57I0RqMpNw', client_secret='Z62ueMNVfmebWXProdQKgb47issCvg', user_agent='Scraping Text')


corpus = Corpus("Reddit + arXiv Football")

# arXiv
url = 'http://export.arxiv.org/api/query?search_query=all:football&start=0&max_results=50'
response = requests.get(url)
data = xmltodict.parse(response.text)
entries = data['feed'].get('entry', [])

# Si arXiv ne renvoie qu’un seul article, "entry" n’est pas une liste
if isinstance(entries, dict):
    entries = [entries]

docs_arxiv = []

for entry in entries:
    co_authors = []
    title = entry.get('title', 'Titre inconnu').strip().replace('\n', ' ')
    summary = entry.get('summary', '').strip()
    url = entry.get('id', '')
    published = entry.get('published', '')

    # Récupérer la date proprement
    try:
        date = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        date = published  # garder la chaîne brute si parsing impossible

    # Extraire le ou les auteurs
    authors_data = entry.get('author', [])
    if isinstance(authors_data, dict):  # un seul auteur
        authors_data = [authors_data]
    

    for author in authors_data:
        auteur_nom = author.get('name', 'Inconnu')
        co_authors.append(auteur_nom)
        if summary:
            #doc = ArxivDocument(title, auteur_nom, date, url, summary)
            #doc.set_coAuteurs(co_authors)
            doc = DocumentGenerator.factory(title, auteur_nom, date, url, summary, "Arxiv")
            doc.set_coAuteurs(co_authors)
            docs_arxiv.append(doc)

for doc in docs_arxiv:
    corpus.add_document(doc)


# Reddit
for post in reddit.subreddit('Football').hot(limit=50):
    if post.is_self and post.selftext.strip():
        created_time = datetime.fromtimestamp(post.created_utc)
        auteur = post.author.name if post.author else "Inconnu"
        nb_commentaires = post.num_comments
        #doc = RedditDocument(post.title, auteur, created_time, post.url, post.selftext)
        #doc.set_nbCommentaire(nb_commentaires)
        doc = DocumentGenerator.factory(post.title, auteur, created_time, post.url, post.selftext, "Reddit")
        doc.set_nbCommentaire(nb_commentaires)
        corpus.add_document(doc)

print(corpus)
corpus.afficher_tri_date(3)

corpus.save("corpus_reddit&arXiv.csv")




