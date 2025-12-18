import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import norm # Pour calculer la norme des vecteurs creux

class SearchEngine:
    def __init__(self, corpus):
        """
        Initialise le moteur de recherche avec un corpus donné.
        Lance la construction des matrices TF-IDF si elle n'a pas encore été faite.
        """
        self.corpus = corpus
        
        # Contrainte Partie 3 : La construction doit se faire "dans la foulée"
        if self.corpus.mat_TFxIDF is None:
            print("Initialisation du moteur : Indexation du corpus en cours...")
            self.corpus.construire_matrices()
        else:
            print("Moteur initialisé : Corpus déjà indexé.")

    def search(self, keywords, n_docs=5):
        """
        Recherche les documents les plus pertinents pour les mots-clés donnés.
        
        Args:
            keywords (str): La requête de l'utilisateur.
            n_docs (int): Le nombre de documents à retourner.
            
        Returns:
            pd.DataFrame: Un tableau contenant les résultats triés par score.
        """
        # 1. Nettoyage de la requête (même traitement que le corpus)
        query_clean = self.corpus.nettoyer_texte(keywords)
        query_words = query_clean.split()
        
        # 2. Vectorisation de la requête
        # On doit créer un vecteur de taille (1, taille_vocabulaire)
        vocab = self.corpus.vocab
        n_words = len(vocab)
        
        # On utilise des listes pour construire une matrice creuse (sparse)
        rows = []
        cols = []
        data = []
        
        for word in query_words:
            if word in vocab:
                word_id = vocab[word]['id']
                rows.append(0)       # Toujours ligne 0 car c'est un seul vecteur
                cols.append(word_id) # Colonne correspondant au mot
                data.append(1)       # On met 1 (ou on pourrait compter la fréquence)
        
        # Création du vecteur requête (sparse CSR)
        query_vec = csr_matrix((data, (rows, cols)), shape=(1, n_words))
        
        # Si le vecteur est vide (aucun mot connu), on retourne vide
        if query_vec.nnz == 0:
            print("Aucun mot de la requête n'a été trouvé dans le vocabulaire.")
            return pd.DataFrame()

        # 3. Calcul de la similarité Cosinus
        # Formule : cos(theta) = (A . B) / (||A|| * ||B||)
        
        # A = Matrice des documents (self.corpus.mat_TFxIDF)
        # B = Vecteur requête transposé (query_vec.T)
        
        # a. Produit scalaire (Dot product)
        dot_products = self.corpus.mat_TFxIDF.dot(query_vec.T).toarray().flatten()
        
        # b. Normes (Magnitudes)
        # Norme des documents (pré-calculée ou calculée ici)
        doc_norms = norm(self.corpus.mat_TFxIDF, axis=1)
        # Norme de la requête
        query_norm = norm(query_vec)
        
        # c. Division pour obtenir le cosinus
        # On évite la division par zéro avec np.errstate ou en remplaçant les 0 par 1 (juste pour la division)
        with np.errstate(divide='ignore', invalid='ignore'):
            scores = dot_products / (doc_norms * query_norm)
            
        # Remplacer les NaN (division par zéro si un doc est vide) par 0
        scores = np.nan_to_num(scores, nan=0.0)

        # 4. Tri et Récupération des meilleurs résultats
        # argsort trie par ordre croissant, donc on prend les derniers indices ([::-1])
        top_indices = scores.argsort()[::-1][:n_docs]
        
        results_data = []
        doc_list = list(self.corpus.id2doc.values()) # Liste des objets documents
        
        for idx in top_indices:
            score = scores[idx]
            if score > 0: # On ne retourne que les résultats pertinents
                doc = doc_list[idx]
                results_data.append({
                    "Titre": doc.titre,
                    "Auteur": doc.auteur,
                    "Date": doc.date,
                    "Score": round(score, 4),
                    "Texte (extrait)": doc.texte[:100] + "..." # Aperçu
                })
        
        # 5. Retour sous forme de DataFrame Pandas
        return pd.DataFrame(results_data)