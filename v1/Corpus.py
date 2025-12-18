import pandas as pd

class Corpus:
    def __init__(self, nom):
        self.nom = nom
        self.authors = {}
        self.id2doc = {}
        
    @property
    def ndoc(self):
        return len(self.id2doc)

    @property
    def naut(self):
        return len(self.authors)
    
    def add_document(self, doc):
        self.id2doc[doc.titre] = doc
        if doc.auteur not in self.authors:
            from Author import Author
            self.authors[doc.auteur] = Author(doc.auteur)
        self.authors[doc.auteur].add(doc)
    
    def afficher_tri_date(self, n=5):
        docs = sorted(self.id2doc.values(), key=lambda d: d.date, reverse=True)[:n]
        for doc in docs:
            print(doc)
    
    def afficher_tri_titre(self, n=5):
        docs = sorted(self.id2doc.values(), key=lambda d: d.titre.lower())[:n]
        for doc in docs:
            print(doc)
    
    def save(self, path):
        data = [{
            "titre": doc.titre,
            "auteur": doc.auteur,
            "date": doc.date,
            "url": doc.url,
            "texte": doc.texte
        } for doc in self.id2doc.values()]
        df = pd.DataFrame(data)
        df.to_csv(path, index=False)
        print(f"Corpus sauvegardé dans {path}")
    

    def load(self, path):
        from Document import Document
        df = pd.read_csv(path)
        for _, row in df.iterrows():
            doc = Document(row["titre"], row["auteur"], row["date"], row["url"], row["texte"])
            self.add_document(doc)
        print(f"Corpus chargé depuis {path}")
    
    def __repr__(self):
        return f"Corpus(nom={self.nom}) - {self.ndoc} docs, {self.naut} auteurs"