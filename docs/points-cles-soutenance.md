# Points clés du projet — pour la soutenance

## Le projet en une phrase
Un système qui fait la présence en classe **automatiquement**, en reconnaissant les visages des étudiants sur une **photo de la classe**.

## Le problème
- L'appel à la main prend du temps (5 à 10 min par séance).
- La fraude : un étudiant peut répondre ou signer pour un absent.
- Le papier se perd, et il n'y a aucune statistique.

## Notre solution
- L'enseignant prend une **photo de la classe**.
- Le système reconnaît les étudiants et **propose** la liste des présents.
- L'enseignant **valide**. Les présences sont enregistrées.
- Un **tableau de bord** donne les statistiques et les rapports (Excel / PDF).

## Comment ça marche (simple)
1. On **détecte** les visages sur la photo (RetinaFace).
2. Chaque visage devient un **code de 512 nombres** (ArcFace).
3. On **compare** ce code à la base des étudiants. Si ça ressemble assez → reconnu.
4. L'enseignant **valide toujours** avant d'enregistrer.

## L'IA en bref (les modèles)

- **RetinaFace** — trouve les visages sur l'image (la *détection*). Il donne la position de chaque visage.
- **ArcFace** — transforme chaque visage en un **code de 512 nombres** (l'*empreinte*). Deux photos de la même personne donnent des codes proches.
- **InsightFace** — la bibliothèque qui contient RetinaFace et ArcFace (pack « buffalo_l ») ; c'est ce que nous utilisons.
- **MiniFASNet** — petit modèle **anti-fraude** : il dit si le visage est une vraie personne ou une photo.

Ces modèles sont **pré-entraînés** (déjà appris sur des millions de visages) et tournent sur un **ordinateur normal** (CPU), sans carte graphique.

## Pourquoi ces choix
- **Modèles déjà existants** (RetinaFace + ArcFace) : parmi les meilleurs, gratuits et très précis. On ne réinvente pas.
- **Ordinateur normal** (CPU) : pas besoin de matériel cher.
- On garde les **codes du visage**, pas les images : protection des données.

## Résultats
- Test sur un jeu public (**LFW**) : **100 %** de bonnes reconnaissances.
- Test **plusieurs visages** : 6 étudiants reconnus, 2 inconnus refusés, en **~2 secondes**.

## Éthique (point fort du projet)
- Le visage est une **donnée sensible** (loi **09-08** / CNDP au Maroc).
- **Consentement écrit** de chaque personne.
- On garde les **empreintes**, pas les images. Données **supprimées** à la fin.

## Limites (rester honnête)
- Testé surtout sur des photos **nettes et de face**.
- Une **vraie classe** (mauvaise lumière, profils, foule) n'est pas encore testée.
- L'anti-fraude n'est pas encore validé contre de vraies attaques.

## Perspectives
- Tester dans une vraie classe.
- Reconnaissance en **temps réel** (webcam).
- Application **mobile**.

---

## Questions probables du jury (réponses courtes)

**Pourquoi la reconnaissance faciale, et pas un badge ou un QR code ?**
Rien à porter ni à perdre, difficile à frauder, et c'est rapide.

**Pourquoi ne pas créer votre propre modèle d'IA ?**
Cela demande énormément de données et de calcul. Les modèles existants sont déjà excellents ; nous les avons intégrés dans une application complète.

**Et si la lumière est mauvaise, ou le visage de profil ?**
La précision baisse. C'est pour cela que l'enseignant valide toujours la liste.

**Où sont stockées les photos des étudiants ?**
On stocke seulement les **empreintes** (des codes numériques), pas les images. L'accès est limité.

**Est-ce légal ?**
Oui, avec le **consentement écrit** des personnes, selon la loi 09-08.

**Que veut dire « 100 % » ?**
C'est sur le jeu de test LFW, en conditions contrôlées. Dans une vraie classe, ce sera un peu moins.

**Peut-on tromper le système avec une photo ?**
Il y a un module **anti-fraude** (détection du vivant). Il reste à valider en conditions réelles.

**Combien de temps pour faire la présence ?**
Environ deux secondes pour toute la photo.

---

## Questions techniques (réponses simples)

**C'est quoi une « empreinte » (embedding) ?**
Un visage transformé en une liste de 512 nombres, comme une signature. Deux photos de la même personne donnent des nombres proches.

**Comment compare-t-on deux visages ?**
On mesure la ressemblance entre les deux listes de nombres (la *similarité cosinus*). Un résultat proche de 1 veut dire très ressemblant.

**C'est quoi le seuil ?**
La limite de décision. Si la ressemblance dépasse 0,35, c'est l'étudiant ; sinon, c'est « inconnu ».

**C'est quoi FAR et FRR ?**
FAR : accepter la mauvaise personne (fausse acceptation). FRR : refuser la bonne personne (faux rejet). On règle le seuil pour éviter les deux.

**Pourquoi ça marche sans carte graphique ?**
Les modèles sont légers et déjà entraînés ; le calcul d'une image est rapide, même sur un simple processeur.
