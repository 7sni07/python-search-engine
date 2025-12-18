class Author:
    def __init__(self, name):
        self.name = name
        self.production = {}

    def add(self, pDoc):
        self.production[pDoc.titre] = pDoc

    def ndoc(self):
        return len(self.production)
    
    
    def __str__(self):
        return f"Le nom du l'author :{self.name} a publié {self.ndoc()} documents"