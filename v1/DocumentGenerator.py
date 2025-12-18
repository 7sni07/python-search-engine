from Document import RedditDocument,ArxivDocument
class DocumentGenerator:

    @staticmethod
    def factory(titre, auteur, date, url, texte, type):
        if type == "Reddit": return RedditDocument(titre, auteur, date, url, texte)
        if type == "Arxiv": return ArxivDocument(titre, auteur, date, url, texte)

        assert 0, "Erreur : " + type