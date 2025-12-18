import pandas as pd
import regex as re
import numpy as np
from scipy.sparse import csr_matrix


class Corpus:
    def __init__(self, nom):
        self.nom = nom
        self.authors = {}
        self.id2doc = {}
        self.txtCorpus = ""
        self.vocab = {}
        self.mat_TF = None
        self.mat_TFxIDF = None
        
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
    
    def search(self, keyword):
        if len(self.txtCorpus) == 0:
            self.txtCorpus = " ".join([doc.texte for doc in self.id2doc.values()])
        
        pattern = fr"([^.?!]*\b(?:{keyword})\b[^.?!]*[.?!])"
        
        matches = [m.strip() for m in re.findall(pattern, self.txtCorpus, flags=re.IGNORECASE)]
        
        return matches

    def concorde(self, keyword,contextLength=30):
        if len(self.txtCorpus) == 0:
            self.txtCorpus = " ".join([doc.texte for doc in self.id2doc.values()])
        
        data = []

        for match in re.finditer(keyword, self.txtCorpus, flags=re.IGNORECASE):
            start = match.start()
            end = match.end()

            left_idx = max(0, start - contextLength)
            right_idx = min(len(self.txtCorpus), end + contextLength)

            contexte_gauche = self.txtCorpus[left_idx:start].replace('\n', ' ')
            motif_trouve = match.group()
            contexte_droit = self.txtCorpus[end:right_idx].replace('\n', ' ')

            data.append({
                "contexte_gauche": contexte_gauche,
                "motif": motif_trouve,
                "contexte_droit": contexte_droit
            })

            df = pd.DataFrame(data)
        
        return df

    def nettoyer_texte(self, texte):
        
        texte = texte.lower()

        texte = texte.replace('\n',' ')
        
        texte = re.sub(r'[^a-z\s]', '', texte)

        texte = re.sub(r'\s+', ' ', texte).strip()
        
        return texte
    
    def construire_matrices(self):

        unique_words = set()

        # Premier passage pour identifier tous les mots uniques
        for doc in self.id2doc.values():
            clean_txt = self.nettoyer_texte(doc.texte)
            words = clean_txt.split()
            unique_words.update(words)

        # On crée le dictionnaire vocab avec les IDs
        sorted_words = sorted(list(unique_words))
        self.vocab = {
            mot: {'id': i, 'total_occ': 0, 'doc_freq': 0} 
            for i, mot in enumerate(sorted_words)
        }

        n_docs = self.ndoc
        n_words = len(self.vocab)

        # Pour construire une CSR matrix, on a besoin de 3 listes :
        rows = []  # Indices des documents (lignes)
        cols = []  # Indices des mots (colonnes)
        data = []  # Valeurs (nombre d'occurrences)

        # On parcourt les documents (c'est ici qu'on remplit les listes)
        doc_indices = list(self.id2doc.values()) # Pour garder un ordre fixe

        for doc_idx, doc in enumerate(doc_indices):
            clean_txt = self.nettoyer_texte(doc.texte)
            words = clean_txt.split()
            
            doc_counts = {}
            for w in words:
                if w in doc_counts:
                    doc_counts[w] += 1
                else:
                    doc_counts[w] = 1

            # Remplissage des listes pour la matrice creuse
            for word, count in doc_counts.items():
                word_id = self.vocab[word]['id']
                rows.append(doc_idx)
                cols.append(word_id)
                data.append(count)

        # Création de la matrice creuse
        self.mat_TF = csr_matrix((data, (rows, cols)), shape=(n_docs, n_words))

        # Étape 1.3 : Mise à jour de vocab avec TF total et DF
        # Somme sur les colonnes (axis=0) pour avoir le total par mot
        total_occurrences = self.mat_TF.sum(axis=0).A1 # .A1 convertit en array 1D
        
        # Pour le Document Frequency, on binarise la matrice (0 ou 1)
        # et on somme sur les colonnes
        binary_mat = self.mat_TF.copy()
        binary_mat.data[:] = 1 # Remplace toutes les valeurs non-nulles par 1
        doc_frequencies = binary_mat.sum(axis=0).A1
        
        # Mise à jour du dictionnaire vocab
        for mot, infos in self.vocab.items():
            word_id = infos['id']
            infos['total_occ'] = int(total_occurrences[word_id])
            infos['doc_freq'] = int(doc_frequencies[word_id])
        
        # Étape 1.4 : Calcul de mat_TFxIDF
        # Calcul de l'IDF pour chaque mot : log( N / (DF + 1) ) + 1
        # On ajoute +1 au dénominateur pour éviter la division par zéro (lissage)
        idf_values = np.log((n_docs + 1) / (doc_frequencies + 1)) + 1
        
        # Pour multiplier chaque colonne de mat_TF par la valeur IDF correspondante,
        # le plus efficace avec scipy est de passer par une matrice diagonale
        from scipy.sparse import diags
        idf_diag = diags(idf_values)
        
        # Multiplication matricielle : TF * Matrice_Diagonale_IDF
        self.mat_TFxIDF = self.mat_TF.dot(idf_diag)


    def stats(self, n=10):
        """Affiche les statistiques demandées"""
        if self.vocab == {}:
            self.construire_matrices()
            
        print(f"Nombre de mots différents : {len(self.vocab)}")
        
        # Pour afficher le top N, on peut trier le dictionnaire vocab
        # selon 'total_occ'
        sorted_vocab = sorted(
            self.vocab.items(), 
            key=lambda item: item[1]['total_occ'], 
            reverse=True
        )[:n]
        
        print(f"\nLes {n} mots les plus fréquents :")
        print(f"{'Mot':<15} | {'TF (Total)':<10} | {'DF (Docs)'}")
        print("-" * 40)
        for mot, infos in sorted_vocab:
            print(f"{mot:<15} | {infos['total_occ']:<10} | {infos['doc_freq']}")

    def __repr__(self):
        return f"Corpus(nom={self.nom}) - {self.ndoc} docs, {self.naut} auteurs"