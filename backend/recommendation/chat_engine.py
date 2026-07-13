import json
import re
import unicodedata

SPECIALITES = [
    "Big Data",
    "Intelligence Artificielle",
    "Cybersécurité",
    "Développement Full Stack",
    "Robotique et Cobotique"
]

MODULES = [
    "Algorithmique et programmation",
    "Programmation Python",
    "Programmation C / C++",
    "Probabilités et statistiques",
    "Analyse / Algèbre / Analyse numérique",
    "Architecture des ordinateurs",
    "Système d’exploitation",
    "Électronique numérique / analogique",
    "Électronique embarquée",
    "Matlab / Simulink",
    "Langues et communication"
]

QUESTIONS = [
    {
        "code_question": "q1",
        "texte": "Quels types de projets aimeriez-vous réaliser ?",
        "type_question": "choix_multiple",
        "consigne": "Cochez toutes les propositions qui correspondent à votre profil.",
        "options": [
            {"texte": "Analyser de grandes quantités de données", "scores": {"Big Data": 4, "Intelligence Artificielle": 1}},
            {"texte": "Créer des modèles intelligents capables d’apprendre", "scores": {"Intelligence Artificielle": 4, "Big Data": 1}},
            {"texte": "Développer une application web ou mobile", "scores": {"Développement Full Stack": 4}},
            {"texte": "Sécuriser un système informatique", "scores": {"Cybersécurité": 4}},
            {"texte": "Automatiser un système physique", "scores": {"Robotique et Cobotique": 4, "Intelligence Artificielle": 1}},
            {"texte": "Travailler avec des capteurs ou des robots", "scores": {"Robotique et Cobotique": 4}},
            {"texte": "Créer une plateforme complète avec interface utilisateur", "scores": {"Développement Full Stack": 4, "Big Data": 1}},
            {"texte": "Détecter des attaques ou protéger des données", "scores": {"Cybersécurité": 4, "Big Data": 1}}
        ]
    },
    {
        "code_question": "q2",
        "texte": "Quelles activités vous motivent le plus ?",
        "type_question": "choix_multiple",
        "option_exclusive": "Je ne sais pas encore",
        "consigne": "Cochez toutes les activités qui vous motivent. Si vous choisissez “Je ne sais pas encore”, cette option sera prise seule.",
        "options": [
            {"texte": "Comprendre et interpréter des données", "scores": {"Big Data": 4}},
            {"texte": "Créer un système intelligent", "scores": {"Intelligence Artificielle": 4}},
            {"texte": "Développer une application complète", "scores": {"Développement Full Stack": 4}},
            {"texte": "Protéger un système contre les attaques", "scores": {"Cybersécurité": 4}},
            {"texte": "Faire fonctionner un système électronique ou robotisé", "scores": {"Robotique et Cobotique": 4}},
            {"texte": "Je ne sais pas encore", "scores": {}}
        ]
    },
    {
        "code_question": "q3",
        "texte": "Quels styles de travail préférez-vous ?",
        "type_question": "choix_multiple",
        "consigne": "Cochez tous les styles de travail qui vous correspondent.",
        "options": [
            {"texte": "Analyse et réflexion", "scores": {"Big Data": 2, "Intelligence Artificielle": 2, "Cybersécurité": 1}},
            {"texte": "Développement pratique", "scores": {"Développement Full Stack": 3, "Robotique et Cobotique": 1}},
            {"texte": "Recherche et expérimentation", "scores": {"Intelligence Artificielle": 3, "Robotique et Cobotique": 1}},
            {"texte": "Travail sur des systèmes complexes", "scores": {"Cybersécurité": 3, "Robotique et Cobotique": 2}},
            {"texte": "Travail orienté utilisateur", "scores": {"Développement Full Stack": 3}},
            {"texte": "Travail avec du matériel ou des systèmes physiques", "scores": {"Robotique et Cobotique": 4}}
        ]
    },
    {
        "code_question": "q4",
        "texte": "Quels modules avez-vous le mieux réussis ?",
        "type_question": "choix_multiple",
        "consigne": "Cochez les modules où vous pensez avoir obtenu de bons résultats.",
        "options": [{"texte": module} for module in MODULES]
    },
    {
        "code_question": "q5",
        "texte": "Quels modules avez-vous le plus appréciés ?",
        "type_question": "choix_multiple",
        "consigne": "Cochez les modules que vous avez réellement appréciés, même si ce ne sont pas forcément ceux où vous avez eu les meilleures notes.",
        "options": [{"texte": module} for module in MODULES]
    },
    {
        "code_question": "q6",
        "texte": "Quels modules avez-vous trouvés les plus difficiles ?",
        "type_question": "choix_multiple",
        "option_exclusive": "Aucun module en particulier",
        "consigne": "Cochez les modules qui vous ont semblé difficiles, ou choisissez “Aucun module en particulier”.",
        "options": [{"texte": module} for module in MODULES] + [{"texte": "Aucun module en particulier"}]
    },
    {
        "code_question": "q7",
        "texte": "Quels métiers vous attirent le plus ?",
        "type_question": "choix_multiple",
        "option_exclusive": "Je ne sais pas encore",
        "consigne": "Cochez les métiers qui vous attirent. Si vous choisissez “Je ne sais pas encore”, cette option sera prise seule.",
        "options": [
            {"texte": "Data Analyst / Data Engineer", "scores": {"Big Data": 4}},
            {"texte": "AI Engineer / Machine Learning Engineer", "scores": {"Intelligence Artificielle": 4}},
            {"texte": "Ingénieur Cybersécurité", "scores": {"Cybersécurité": 4}},
            {"texte": "Développeur Full Stack", "scores": {"Développement Full Stack": 4}},
            {"texte": "Ingénieur Robotique / Automatisation", "scores": {"Robotique et Cobotique": 4}},
            {"texte": "Je ne sais pas encore", "scores": {}}
        ]
    },
    {
        "code_question": "q8",
        "texte": "Dans votre choix, qu’est-ce qui compte le plus pour vous ?",
        "type_question": "choix_unique",
        "consigne": "Choisissez la réponse qui représente le mieux votre manière de décider.",
        "options": [
            {"texte": "Mes résultats académiques", "scores": {}},
            {"texte": "Mes préférences personnelles", "scores": {}},
            {"texte": "Mes objectifs professionnels", "scores": {}},
            {"texte": "Un équilibre entre les trois", "scores": {}}
        ]
    },
    {
        "code_question": "q9",
        "texte": "Ressentez-vous une hésitation entre plusieurs spécialités ?",
        "type_question": "hesitation",
        "consigne": "Répondez Oui ou Non. Si vous répondez Oui, cochez les spécialités entre lesquelles vous hésitez.",
        "specialites": SPECIALITES,
        "min_specialites": 1
    },
    {
        "code_question": "q10",
        "texte": "Décrivez brièvement le type de projet que vous aimeriez réaliser dans le futur.",
        "type_question": "texte_libre",
        "consigne": "Réponse libre courte : 2 ou 3 phrases suffisent."
    }
]

PONDERATIONS = {
    "q1": 2.0,
    "q2": 1.7,
    "q3": 1.2,
    "q4": 1.4,
    "q5": 1.3,
    "q6": -0.5,
    "q7": 1.8,
    "q8": 0.4,
    "q9": 0.7,
    "q10": 1.4,
    "clarification": 2.0
}

MAPPING_MODULES = {
    "Algorithmique et programmation": {"Intelligence Artificielle": 2, "Développement Full Stack": 2, "Big Data": 1},
    "Programmation Python": {"Intelligence Artificielle": 2, "Big Data": 2, "Développement Full Stack": 1},
    "Programmation C / C++": {"Développement Full Stack": 2, "Robotique et Cobotique": 2, "Cybersécurité": 1},
    "Probabilités et statistiques": {"Big Data": 3, "Intelligence Artificielle": 2},
    "Analyse / Algèbre / Analyse numérique": {"Intelligence Artificielle": 2, "Big Data": 2, "Robotique et Cobotique": 1},
    "Architecture des ordinateurs": {"Cybersécurité": 2, "Robotique et Cobotique": 1},
    "Système d’exploitation": {"Cybersécurité": 3, "Développement Full Stack": 1},
    "Électronique numérique / analogique": {"Robotique et Cobotique": 3},
    "Électronique embarquée": {"Robotique et Cobotique": 4, "Cybersécurité": 1},
    "Matlab / Simulink": {"Robotique et Cobotique": 2, "Big Data": 1},
    "Langues et communication": {"Développement Full Stack": 0.5}
}

MOTS_CLES_PROJET = {
    "Big Data": ["donnée", "donnees", "data", "analyse", "statistique", "tableau de bord", "visualisation", "prediction", "prédiction"],
    "Intelligence Artificielle": ["ia", "ai", "intelligent", "modèle", "modele", "machine learning", "apprentissage", "deep learning", "automatique"],
    "Cybersécurité": ["sécurité", "securite", "attaque", "hacking", "protection", "réseau", "reseau", "cryptographie", "vulnérabilité"],
    "Développement Full Stack": ["application", "web", "mobile", "interface", "site", "plateforme", "frontend", "backend", "full stack"],
    "Robotique et Cobotique": ["robot", "robotique", "capteur", "automatisation", "automatiser", "embarqué", "embarque", "mécatronique", "mecatronique"]
}


def _normaliser(texte):
    texte = str(texte or "").lower()
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return texte


def get_scores_vides():
    return {specialite: 0 for specialite in SPECIALITES}


def initialiser_scores():
    return get_scores_vides()


def nombre_questions():
    return len(QUESTIONS)


def get_question_par_index(index):
    try:
        index = int(index)
    except Exception:
        return None

    if 0 <= index < len(QUESTIONS):
        return QUESTIONS[index]

    return None


def _question_depuis_texte(question):
    if isinstance(question, dict):
        return question

    texte = str(question or "")
    for item in QUESTIONS:
        if item["texte"] == texte:
            return item

    return {
        "code_question": "question_inconnue",
        "texte": texte,
        "type_question": "texte_libre"
    }


def _liste_options(question):
    options = question.get("options", [])
    valeurs = []
    for option in options:
        if isinstance(option, dict):
            valeurs.append(option.get("texte", ""))
        else:
            valeurs.append(str(option))
    return valeurs


def _extraire_reponses_selectionnees(message, question):
    texte = str(message or "")
    normalise = _normaliser(texte)
    reponses = []

    for option in _liste_options(question):
        if _normaliser(option) in normalise:
            reponses.append(option)

    if len(reponses) == 0:
        morceaux = re.split(r"[;\n,]+", texte)
        for morceau in morceaux:
            propre = morceau.strip(" .:-")
            if propre:
                reponses.append(propre)

    return list(dict.fromkeys(reponses))


def _ajouter_score(scores, specialite, valeur):
    if specialite not in scores:
        scores[specialite] = 0
    scores[specialite] += float(valeur)


def _scores_modules(reponses, coefficient=1):
    scores = get_scores_vides()
    for reponse in reponses:
        for module, mapping in MAPPING_MODULES.items():
            if _normaliser(module) == _normaliser(reponse) or _normaliser(module) in _normaliser(reponse):
                for specialite, valeur in mapping.items():
                    _ajouter_score(scores, specialite, valeur * coefficient)
    return scores


def _scores_options(question, reponses, coefficient=1):
    scores = get_scores_vides()
    for option in question.get("options", []):
        if not isinstance(option, dict):
            continue
        texte_option = option.get("texte", "")
        if any(_normaliser(texte_option) == _normaliser(rep) or _normaliser(texte_option) in _normaliser(rep) for rep in reponses):
            for specialite, valeur in option.get("scores", {}).items():
                _ajouter_score(scores, specialite, valeur * coefficient)
    return scores


def _scores_hesitation(message, coefficient=1):
    scores = get_scores_vides()
    texte = _normaliser(message)
    if "non" in texte and "oui" not in texte:
        return scores
    for specialite in SPECIALITES:
        if _normaliser(specialite) in texte:
            _ajouter_score(scores, specialite, 1 * coefficient)
    return scores


def _scores_reponse_libre(message, coefficient=1):
    scores = get_scores_vides()
    texte = _normaliser(message)
    for specialite, mots in MOTS_CLES_PROJET.items():
        for mot in mots:
            if _normaliser(mot) in texte:
                _ajouter_score(scores, specialite, 1 * coefficient)
    return scores


def traiter_message_etudiant(question_actuelle, message_etudiant, scores_actuels=None, historique=None):
    question = _question_depuis_texte(question_actuelle)
    code = question.get("code_question", "")
    type_question = question.get("type_question", "texte_libre")
    coefficient = PONDERATIONS.get(code, 1)

    texte = str(message_etudiant or "").strip()
    if texte == "":
        return {
            "type_message": "demande_clarification",
            "message_bot": "Veuillez sélectionner une réponse ou écrire une réponse courte pour continuer.",
            "scores": get_scores_vides(),
            "domaines_detectes": [],
            "hesitation_detectee": False,
            "commentaire_analyse": "Réponse vide."
        }

    if type_question in ["choix_multiple", "choix_unique"]:
        reponses = _extraire_reponses_selectionnees(texte, question)
        if code in ["q4", "q5"]:
            scores = _scores_modules(reponses, coefficient)
        elif code == "q6":
            scores = _scores_modules(reponses, coefficient)
        else:
            scores = _scores_options(question, reponses, coefficient)
        domaines = reponses
    elif type_question == "hesitation":
        scores = _scores_hesitation(texte, coefficient)
        domaines = [specialite for specialite in SPECIALITES if _normaliser(specialite) in _normaliser(texte)]
    else:
        scores = _scores_reponse_libre(texte, coefficient)
        domaines = [s for s, v in scores.items() if v > 0]

    return {
        "type_message": "reponse_orientation",
        "message_bot": "Réponse prise en compte.",
        "scores": scores,
        "domaines_detectes": domaines,
        "hesitation_detectee": code == "q9" and len(domaines) >= 2,
        "commentaire_analyse": "Analyse par règles pondérées du questionnaire final.",
        "source": "moteur_local_questions_finales"
    }


def appliquer_scores(scores_actuels, scores_a_ajouter):
    scores = get_scores_vides()

    if isinstance(scores_actuels, dict):
        for specialite in SPECIALITES:
            try:
                scores[specialite] = float(scores_actuels.get(specialite, 0))
            except Exception:
                scores[specialite] = 0

    if isinstance(scores_a_ajouter, dict):
        for specialite, valeur in scores_a_ajouter.items():
            if specialite in scores:
                try:
                    scores[specialite] += float(valeur)
                except Exception:
                    pass

    for specialite in scores:
        if scores[specialite] < 0:
            scores[specialite] = 0

    return scores


def _pourcentages(scores):
    total = sum(float(v or 0) for v in scores.values())
    if total <= 0:
        return {specialite: 20 for specialite in SPECIALITES}
    return {specialite: round((float(scores.get(specialite, 0)) / total) * 100, 2) for specialite in SPECIALITES}


def construire_resultat_final(scores):
    scores_corriges = get_scores_vides()
    for specialite in SPECIALITES:
        try:
            scores_corriges[specialite] = round(float(scores.get(specialite, 0)), 2)
        except Exception:
            scores_corriges[specialite] = 0

    pourcentages = _pourcentages(scores_corriges)
    specialite_recommandee = max(pourcentages, key=pourcentages.get)

    return {
        "specialite_recommandee": specialite_recommandee,
        "scores": scores_corriges,
        "pourcentages": pourcentages,
        "resume": (
            "Le résultat est calculé à partir des projets préférés, des activités motivantes, "
            "du style de travail, du profil académique, des métiers visés, "
            "de l’hésitation déclarée et de la réponse libre."
        )
    }


def _code_est_clarification(code_question):
    code = str(code_question or "").strip().lower()
    return code.startswith("qc") or code.startswith("clarification_")


def _reponses_deja_clarifiees(reponses):
    total = 0

    if not isinstance(reponses, list):
        return total

    for rep in reponses:
        if not isinstance(rep, dict):
            continue

        if _code_est_clarification(rep.get("code_question")):
            total += 1

    return total


def _cle_paire_specialites(s1, s2):
    return frozenset([_normaliser(s1), _normaliser(s2)])


def _paires_deja_clarifiees(reponses):
    paires = set()

    if not isinstance(reponses, list):
        return paires

    for rep in reponses:
        if not isinstance(rep, dict):
            continue

        question_obj = rep.get("question_obj")

        if not isinstance(question_obj, dict):
            continue

        code = question_obj.get("code_question", "")

        if not _code_est_clarification(code):
            continue

        options = question_obj.get("options", [])
        specialites_options = []

        for option in options:
            if not isinstance(option, dict):
                continue

            texte = option.get("texte", "")

            if texte in SPECIALITES:
                specialites_options.append(texte)

        if len(specialites_options) >= 2:
            paires.add(_cle_paire_specialites(specialites_options[0], specialites_options[1]))

    return paires


def _specialites_hesitees_declarees(reponses):
    if not isinstance(reponses, list):
        return []

    for rep in reponses:
        if not isinstance(rep, dict):
            continue

        if rep.get("code_question") == "q9":
            texte = _normaliser(rep.get("reponse", ""))

            if "non" in texte and "oui" not in texte:
                return []

            resultat = []

            for specialite in SPECIALITES:
                if _normaliser(specialite) in texte:
                    resultat.append(specialite)

            return resultat

    return []


def _specialites_citees_dans_reponse_libre(reponses):
    """
    Extrait les spécialités citées dans la réponse libre finale q10.

    Cette information est utilisée uniquement pour éviter de poser une
    clarification hors sujet. Exemple : si l'étudiant écrit "Full Stack et Big
    Data", on ne doit pas ensuite lui poser une question Big Data / Cybersécurité.
    """
    if not isinstance(reponses, list):
        return []

    for rep in reversed(reponses):
        if not isinstance(rep, dict):
            continue

        if rep.get("code_question") == "q10":
            texte = _normaliser(rep.get("reponse", ""))
            resultat = []

            for specialite in SPECIALITES:
                if _normaliser(specialite) in texte:
                    resultat.append(specialite)

            return resultat

    return []


def _score_de(scores, specialite):
    if not isinstance(scores, dict):
        return 0

    return float(scores.get(specialite, 0) or 0)


def _ecart_score_brut(scores, s1, s2):
    return abs(_score_de(scores, s1) - _score_de(scores, s2))


def _paire_est_reellement_proche(scores, pourcentages, s1, s2):
    """
    Une clarification ne doit être posée que si l'écart est réellement faible.

    On combine deux critères :
    - écart en pourcentage de recommandation ;
    - écart en score brut.

    Cela évite les questions supplémentaires inutiles lorsque la filière
    dominante est déjà clairement devant.
    """
    p1 = float(pourcentages.get(s1, 0) or 0)
    p2 = float(pourcentages.get(s2, 0) or 0)
    ecart_pourcentage = abs(p1 - p2)
    ecart_score = _ecart_score_brut(scores, s1, s2)

    return ecart_pourcentage <= 5.0 or ecart_score <= 3.0


def _choisir_paire_a_clarifier(scores, reponses):
    pourcentages = _pourcentages(scores)
    tries = sorted(pourcentages.items(), key=lambda item: item[1], reverse=True)

    if len(tries) < 2:
        return None

    paires_deja_posees = _paires_deja_clarifiees(reponses)
    specialites_reponse_libre = _specialites_citees_dans_reponse_libre(reponses)
    hesitations = _specialites_hesitees_declarees(reponses)

    # Si l'étudiant a cité exactement deux spécialités dans sa réponse libre,
    # cette paire est prioritaire. On ne pose pas une question sur une autre paire.
    if len(specialites_reponse_libre) == 2:
        s1, s2 = specialites_reponse_libre
        cle = _cle_paire_specialites(s1, s2)

        if cle not in paires_deja_posees and _paire_est_reellement_proche(scores, pourcentages, s1, s2):
            return s1, s2

        return None

    # Si l'étudiant a déclaré une hésitation entre 2 ou 3 spécialités, on peut
    # choisir la paire la plus proche parmi celles-ci. S'il coche toutes les
    # spécialités, ce n'est pas une vraie hésitation exploitable : on ignore la
    # liste et on revient aux scores.
    if 2 <= len(hesitations) <= 3:
        paires_candidates = []

        for index_1 in range(len(hesitations)):
            for index_2 in range(index_1 + 1, len(hesitations)):
                s1 = hesitations[index_1]
                s2 = hesitations[index_2]
                cle = _cle_paire_specialites(s1, s2)

                if cle in paires_deja_posees:
                    continue

                if not _paire_est_reellement_proche(scores, pourcentages, s1, s2):
                    continue

                paires_candidates.append((_ecart_score_brut(scores, s1, s2), abs(pourcentages.get(s1, 0) - pourcentages.get(s2, 0)), s1, s2))

        if paires_candidates:
            paires_candidates.sort(key=lambda item: (item[0], item[1]))
            return paires_candidates[0][2], paires_candidates[0][3]

        return None

    # Cas général : seulement la paire des deux meilleurs scores, et seulement
    # si elle est vraiment proche.
    s1, p1 = tries[0]
    s2, p2 = tries[1]
    cle = _cle_paire_specialites(s1, s2)

    if cle in paires_deja_posees:
        return None

    if not _paire_est_reellement_proche(scores, pourcentages, s1, s2):
        return None

    return s1, s2


def get_question_clarification_si_necessaire(scores, reponses):
    nombre_clarifications = _reponses_deja_clarifiees(reponses)

    # Une seule question de clarification suffit.
    # Cela évite les deux questions finales systématiques.
    if nombre_clarifications >= 1:
        return None

    paire_a_clarifier = _choisir_paire_a_clarifier(scores, reponses)

    if paire_a_clarifier is None:
        return None

    s1, s2 = paire_a_clarifier
    paire = {_normaliser(s1), _normaliser(s2)}

    textes = {
        frozenset([_normaliser("Intelligence Artificielle"), _normaliser("Big Data")]): "Préférez-vous construire des modèles intelligents capables d’apprendre ou analyser de grandes quantités de données pour aider à la décision ?",
        frozenset([_normaliser("Intelligence Artificielle"), _normaliser("Robotique et Cobotique")]): "Préférez-vous travailler sur des modèles logiciels intelligents ou sur des systèmes physiques automatisés ?",
        frozenset([_normaliser("Développement Full Stack"), _normaliser("Cybersécurité")]): "Préférez-vous créer des applications complètes ou sécuriser des systèmes informatiques existants ?",
        frozenset([_normaliser("Big Data"), _normaliser("Développement Full Stack")]): "Préférez-vous exploiter les données ou développer des plateformes complètes avec interface utilisateur ?",
        frozenset([_normaliser("Cybersécurité"), _normaliser("Robotique et Cobotique")]): "Préférez-vous protéger des systèmes informatiques ou contrôler des systèmes physiques automatisés ?"
    }

    texte_question = textes.get(
        frozenset(paire),
        f"Votre profil est proche entre {s1} et {s2}. Laquelle de ces deux spécialités vous attire le plus ?"
    )

    return {
        "code_question": f"qc{nombre_clarifications + 1}",
        "texte": texte_question,
        "type_question": "choix_unique",
        "consigne": "Choisissez la réponse qui correspond le mieux à votre préférence pour affiner la recommandation.",
        "options": [
            {"texte": s1, "scores": {s1: 4}},
            {"texte": s2, "scores": {s2: 4}},
            {"texte": "Les deux m’intéressent", "scores": {s1: 2, s2: 2}}
        ]
    }
