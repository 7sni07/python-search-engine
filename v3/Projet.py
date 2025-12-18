import praw
import requests
import xmltodict
from datetime import datetime
from Corpus import Corpus
from DocumentGenerator import DocumentGenerator
from SearchEngine import SearchEngine

reddit = praw.Reddit(client_id='1bn0-J4XhJYm57I0RqMpNw', client_secret='Z62ueMNVfmebWXProdQKgb47issCvg', user_agent='Scraping Text')


corpus = Corpus("Reddit + arXiv Football")

# RÉCUPÉRATION ARXIV
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
    url_doc = entry.get('id', '')
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
            doc = DocumentGenerator.factory(title, auteur_nom, date, url_doc, summary, "Arxiv")
            doc.set_coAuteurs(co_authors)
            docs_arxiv.append(doc)

for doc in docs_arxiv:
    corpus.add_document(doc)


# RÉCUPÉRATION REDDIT
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

# print(corpus)
# corpus.afficher_tri_date(3)

#corpus.save("corpus_reddit&arXiv.csv")

#print(corpus.concorde("ball"))


# 1. Afficher les statistiques du corpus (Vocabulaire & Fréquences)
# Cela va implicitement nettoyer le texte et construire le vocabulaire
print("\n" + "="*40)
print(" STATISTIQUES DU CORPUS ")
print("="*40)
corpus.stats(n=15) # Affiche les 15 mots les plus fréquents

# 2. Initialiser le Moteur de Recherche
# Cela va déclencher la construction des matrices TF et TFxIDF si ce n'est pas déjà fait
print("\n" + "="*40)
print(" INITIALISATION DU MOTEUR ")
print("="*40)
moteur = SearchEngine(corpus)


# 3. Lancer une recherche
# Choisissez des mots susceptibles d'être dans vos textes (ex: "team", "match", "goal", "algorithm")
mots_cles = "team match player goal" 

print(f"\n>>> Recherche en cours pour : '{mots_cles}'")
resultats_df = moteur.search(mots_cles, n_docs=5)

# 4. Affichage du résultat (Tableau Pandas)
if not resultats_df.empty:
    print("\n--- RÉSULTATS LES PLUS PERTINENTS ---")
    # On configure pandas pour bien afficher le texte
    import pandas as pd
    pd.set_option('display.max_colwidth', 100) # Pour voir un bout du texte
    print(resultats_df[['Score', 'Titre', 'Auteur']]) # On affiche les colonnes principales
else:
    print("Aucun résultat trouvé.")