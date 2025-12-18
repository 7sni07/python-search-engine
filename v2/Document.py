class Document:
    def __init__(self, titre, auteur, date, url, texte, type):
        self.titre = titre
        self.auteur = auteur
        self.date = date
        self.url = url
        self.texte = texte
        self.type = type

    def taille(self):
        return len(self.texte.split())

    def __str__(self):
        return f"Le titre du document {self.titre}, publié par : {self.auteur} le {self.date})"

class RedditDocument(Document):
    def __init__(self, titre, auteur, date, url, texte):
        super().__init__(titre, auteur, date, url, texte, "Reddit")
        self.nbCommentaire = None

    def get_nbCommentaire(self):
        return self.nbCommentaire
    
    def set_nbCommentaire(self, nbCommentaire):
        self.nbCommentaire = nbCommentaire
    
    def get_type(self):
        return self.type

    def __str__(self):
        return f"Le titre du document Reddit {self.titre}, publié par : {self.auteur} le {self.date})"
    

class ArxivDocument(Document):
    def __init__(self, titre, auteur, date, url, texte):
        super().__init__(titre, auteur, date, url, texte, "Arxiv")
        self.coAuteurs = []

    def get_coAuteurs(self):
        return self.coAuteurs
    
    def set_coAuteurs(self, coAuteurs):
        self.coAuteurs = coAuteurs
    
    def get_type(self):
        return self.type

    def __str__(self):
        return f"Le titre du document Reddit {self.titre}, publié par : {self.auteur} le {self.date})"
