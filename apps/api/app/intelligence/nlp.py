import hashlib
import math
import re
import unicodedata
from typing import Any

import numpy as np

SPANISH_STOPWORDS = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un",
    "para", "con", "no", "una", "su", "al", "lo", "como", "mas", "pero", "sus", "le",
    "ya", "o", "este", "si", "porque", "esta", "entre", "cuando", "muy", "sin", "sobre",
    "también", "tambien", "me", "hasta", "hay", "donde", "quien", "desde", "todo", "nos",
    "durante", "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante",
    "ellos", "e", "esto", "mi", "antes", "algunos", "que", "unos", "yo", "otro", "otras",
    "otra", "el", "tanto", "esa", "estos", "mucho", "quienes", "nada", "muchos", "cual",
    "poco", "ella", "estar", "estas", "algunas", "algo", "nosotros", "mi", "mis", "tu",
    "te", "ti", "tus", "ellas", "nosotras", "vosotros", "vosotras", "os", "mio", "mia",
    "mios", "mias", "tuyo", "tuya", "tuyos", "tuyas", "suyo", "suya", "suyos", "suyas",
    "nuestro", "nuestra", "nuestros", "nuestras", "vuestro", "vuestra", "vuestros",
    "fue", "fueron", "ha", "han", "habia", "segun", "según", "tras", "cada", "día", "dia",
    "hoy", "ayer", "bolivia", "boliviano", "boliviana", "nacional", "pais", "país",
}

DEPARTMENT_KEYWORDS: dict[str, list[str]] = {
    "La Paz": [
        "la paz", "el alto", "viacha", "achacachi", "caranavi", "coroico", "yungas",
        "madidi", "rurrenabaque", "mapiri", "tipuani", "guanay", "teoponte", "laja",
        "desaguadero", "copacabana", "patacamaya", "senkata", "murillo", "paceño",
    ],
    "Santa Cruz": [
        "santa cruz", "chiquitania", "chiquitanía", "san ignacio de velasco", "roboré",
        "robore", "concepcion", "concepción", "san matias", "san matías", "montero",
        "warnes", "yapacani", "yapacaní", "camiri", "guarani", "guaraní", "noel kempff",
        "samaipata", "puerto suarez", "puerto suárez", "cruceño", "cruceña", "pailon",
    ],
    "Cochabamba": [
        "cochabamba", "chapare", "trópico", "tropico", "quillacollo", "sacaba", "parotani",
        "colomi", "villa tunari", "shinahota", "chimoré", "chimore", "punata", "mizque",
        "aiquile", "capinota", "tiquipaya", "tunari", "cochabambino",
    ],
    "Potosí": [
        "potosi", "potosí", "cerro rico", "uyuni", "llallagua", "uncia", "uncía",
        "colquechaca", "tupiza", "villazon", "villazón", "betanzos", "cotagaita",
        "pilcomayo", "salar de uyuni", "coroma", "chayanta", "norte de potosi", "potosino",
    ],
    "Oruro": [
        "oruro", "poopo", "poopó", "uru uru", "huanuni", "challapata", "caracollo",
        "pisiga", "tambo quemado", "sabaya", "corque", "desaguadero", "orureño",
    ],
    "Tarija": [
        "tarija", "tariquia", "tariquía", "yacuiba", "villamontes", "villa montes",
        "bermejo", "carapari", "caraparí", "entre rios", "padcaya", "gran chaco", "tarijeño",
    ],
    "Chuquisaca": [
        "chuquisaca", "sucre", "monteagudo", "camargo", "tarabuco", "padilla",
        "yamparaez", "incahuasi", "san lucas", "chuquisaqueño",
    ],
    "Beni": [
        "beni", "trinidad", "riberalta", "guayaramerin", "guayaramerín", "san borja",
        "santa ana del yacuma", "reyes", "mamore", "mamoré", "isiboro", "tipnis", "beniano",
    ],
    "Pando": [
        "pando", "cobija", "porvenir", "manuripi", "madre de dios", "tahauamanu",
        "sena", "el sena", "pandino",
    ],
}

CATEGORY_RULES: dict[str, list[str]] = {
    "Medio Ambiente y Territorio": [
        "incendio", "incendios", "chaqueo", "chaqueos", "deforestacion", "deforestación",
        "bosque", "reserva", "area protegida", "área protegida", "madidi", "tariquia",
        "tariquía", "chiquitania", "chiquitanía", "sequia", "sequía", "contaminacion",
        "contaminación", "mercurio", "rio", "río", "biodiversidad", "agua", "poopó",
        "uru uru", "inundacion", "inundación", "climatica", "climática", "humo",
    ],
    "Minería y Extractivismo": [
        "mineria", "minería", "minero", "mineros", "cooperativa", "cooperativas",
        "aurifera", "aurífera", "oro", "litio", "cerro rico", "comibol", "ajam",
        "fencomin", "dique de colas", "ingenio", "huanuni", "llallagua", "hidrocarburos",
        "pozo", "exploracion", "exploración", "ypfb",
    ],
    "Conflictos Sociales": [
        "bloqueo", "bloqueos", "paro", "marcha", "protesta", "cabildo", "enfrentamiento",
        "movilizacion", "movilización", "carretera", "conflicto", "huelga", "pliego",
        "demanda", "sindicato", "transporte", "gremiales", "vecinos", "emergencia",
    ],
    "Economía y Abastecimiento": [
        "combustible", "diesel", "diésel", "gasolina", "fila", "filas", "surtidor",
        "dolar", "dólar", "divisas", "inflacion", "inflación", "canasta familiar",
        "alimentos", "arroz", "aceite", "precio", "precios", "anh", "emapa", "contrabando",
        "exportacion", "exportación", "crisis economica",
    ],
    "Justicia y Derechos Humanos": [
        "justicia", "fiscalia", "fiscalía", "tribunal", "derechos humanos", "defensoria",
        "defensoría", "violencia", "feminicidio", "impunidad", "denuncia", "corrupcion",
        "corrupción", "detencion", "detención", "libertad de prensa", "periodista",
        "indigena", "indígena", "consulta previa",
    ],
    "Salud y Servicios Básicos": [
        "salud", "hospital", "posta", "medicamentos", "dengue", "epidemia", "agua potable",
        "alcantarillado", "educacion", "educación", "escuela", "item", "ítems", "pacientes",
        "desnutricion", "desnutrición",
    ],
    "Política y Gestión Pública": [
        "asamblea", "legislativa", "diputados", "senadores", "elecciones", "tse",
        "alcaldia", "alcaldía", "gobernacion", "gobernación", "presupuesto", "ley",
        "decreto", "gobierno", "ministerio", "censo",
    ],
}

KNOWN_ENTITIES: list[str] = [
    "YPFB", "ANH", "COMIBOL", "SERNAP", "INRA", "ABT", "AJAM", "SENAMHI", "EMAPA",
    "Defensoría del Pueblo", "FENCOMIN", "COB", "CSUTCB", "CIDOB", "CONAMAQ",
    "CPEMB", "CONTIOCAP", "Reserva de Tariquía", "Parque Nacional Madidi",
    "Lago Uru Uru", "Lago Poopó", "Cerro Rico", "Río Beni", "Río Pilcomayo",
    "Chiquitanía", "Salar de Uyuni", "Tribunal Agroambiental", "ABC",
]

SEMANTIC_CONCEPTS: list[list[str]] = [
    ["incendio", "incendios", "fuego", "chaqueo", "quema", "bosque", "chiquitania", "humo", "abt"],
    ["mercurio", "oro", "aurifera", "mineria", "rio", "beni", "madidi", "contaminacion", "ajam", "dragas"],
    ["tariquia", "reserva", "petrolera", "pozo", "hidrocarburos", "ypfb", "chaco", "tarija", "astillero"],
    ["diesel", "gasolina", "combustible", "surtidor", "fila", "anh", "transporte", "abastecimiento"],
    ["bloqueo", "carretera", "paro", "marcha", "conflicto", "policia", "transporte", "abc"],
    ["sequia", "agua", "laguna", "poopo", "uru", "racionamiento", "lluvia", "altiplano", "cosecha"],
    ["pilcomayo", "dique", "colas", "minero", "potosi", "contaminacion", "metales", "pesca"],
    ["litio", "uyuni", "salar", "ylb", "contrato", "potosi", "regalias", "industrializacion"],
    ["cerro", "rico", "hundimiento", "comibol", "cooperativas", "potosi", "unesco"],
    ["canasta", "familiar", "precios", "alimentos", "inflacion", "dolar", "emapa", "mercados"],
    ["salud", "hospital", "medicamentos", "items", "pacientes", "emergencia", "medico", "rural"],
    ["justicia", "tribunal", "fiscalia", "defensoria", "derechos", "periodistas", "corrupcion"],
    ["inundacion", "desborde", "lluvias", "mamore", "beni", "pando", "damnificados", "defensa"],
    ["educacion", "escuelas", "maestros", "infraestructura", "desayuno", "escolar", "municipio"],
    ["indigena", "territorio", "tco", "inra", "avasallamiento", "tierras", "comunidad", "consulta"],
    ["contrabando", "frontera", "desaguadero", "pisiga", "villazon", "bermejo", "aduana"],
]


def normalize_text(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    without_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9\s]", " ", without_accents)


def tokenize(text: str) -> list[str]:
    norm = normalize_text(text)
    tokens = [t for t in norm.split() if len(t) > 2 and t not in SPANISH_STOPWORDS]
    return tokens


def stem_es(word: str) -> str:
    for suffix in ("ciones", "cion", "miento", "mientos", "idades", "idad", "mente", "eros", "eras", "istas", "ista", "es", "s"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def detect_department(title: str, content: str, fallback: str = "Nacional") -> str:
    combined = f"{title} {title} {content[:1200]}".lower()
    scores: dict[str, int] = {}
    for dept, keywords in DEPARTMENT_KEYWORDS.items():
        score = 0
        for kw in keywords:
            occurrences = combined.count(kw)
            if occurrences > 0:
                score += occurrences * (3 if kw in title.lower() else 1)
        if score > 0:
            scores[dept] = score
    if not scores:
        return fallback
    return max(scores.items(), key=lambda item: item[1])[0]


def detect_all_departments(title: str, content: str, primary: str = "Nacional") -> list[str]:
    combined = f"{title} {content[:1500]}".lower()
    found: list[str] = []
    if primary and primary != "Nacional":
        found.append(primary)
    for dept, keywords in DEPARTMENT_KEYWORDS.items():
        if dept in found:
            continue
        if any(kw in combined for kw in keywords):
            found.append(dept)
    return found or ([primary] if primary else ["Nacional"])


def classify_category(title: str, content: str) -> str:
    combined = f"{title} {title} {content[:1200]}".lower()
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_RULES.items():
        score = sum(combined.count(kw) * (3 if kw in title.lower() else 1) for kw in keywords)
        if score > 0:
            scores[category] = score
    if not scores:
        return "Sociedad y Comunidad"
    return max(scores.items(), key=lambda item: item[1])[0]


def extract_entities(title: str, content: str) -> list[str]:
    text = f"{title}. {content[:1500]}"
    found: list[str] = []
    lower_text = text.lower()
    for ent in KNOWN_ENTITIES:
        if ent.lower() in lower_text and ent not in found:
            found.append(ent)

    # Also detect capitalized multi-word proper nouns in Spanish
    matches = re.findall(r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?:de|del|la|las|los|y)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+|\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,2})\b", text)
    ignore = {"El Deber", "La Razón", "Los Tiempos", "Red Erbol", "Correo del Sur", "El País", "La Patria", "El Potosí"}
    for m in matches:
        cleaned = m.strip()
        if cleaned not in found and cleaned not in ignore and len(cleaned) >= 5:
            found.append(cleaned)
        if len(found) >= 8:
            break
    return found[:8]


def generate_summary(title: str, content: str, max_chars: int = 320) -> str:
    clean = re.sub(r"\s+", " ", content).strip()
    if not clean:
        return title
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    summary_parts: list[str] = []
    current_len = 0
    for s in sentences:
        s_clean = s.strip()
        if len(s_clean) < 25:
            continue
        summary_parts.append(s_clean)
        current_len += len(s_clean)
        if current_len >= max_chars or len(summary_parts) >= 2:
            break
    result = " ".join(summary_parts) if summary_parts else clean[:max_chars]
    if len(result) > max_chars + 40:
        result = result[:max_chars].rsplit(" ", 1)[0] + "..."
    return result


def compute_embedding(text: str, dim: int = 128) -> list[float]:
    """
    Genera un vector semántico denso de `dim` dimensiones combinando:
    1) Dimensiones de conceptos temáticos y regionales de Bolivia (primeras 16 dims)
    2) Feature hashing ponderado de raíces léxicas (stems) y bigramas (112 dims)
    """
    vec = np.zeros(dim, dtype=np.float64)
    tokens = tokenize(text)
    if not tokens:
        return [0.0] * dim

    stems = [stem_es(t) for t in tokens]
    stem_counts: dict[str, int] = {}
    for s in stems:
        stem_counts[s] = stem_counts.get(s, 0) + 1

    # 1. Concept dimensions (0..15)
    num_concepts = min(len(SEMANTIC_CONCEPTS), 16)
    for idx in range(num_concepts):
        concept_terms = [stem_es(t) for t in SEMANTIC_CONCEPTS[idx]]
        hits = sum(stem_counts.get(ct, 0) for ct in concept_terms)
        if hits > 0:
            vec[idx] = math.log1p(hits) * 2.2

    # 2. Hashed lexical & bigram dimensions (16..dim-1)
    hash_space = dim - num_concepts
    for s, count in stem_counts.items():
        weight = 1.0 + math.log(count)
        h = int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16)
        bucket = num_concepts + (h % hash_space)
        sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
        vec[bucket] += sign * weight

    for i in range(len(stems) - 1):
        bigram = f"{stems[i]}_{stems[i + 1]}"
        h = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16)
        bucket = num_concepts + (h % hash_space)
        sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
        vec[bucket] += sign * 0.85

    norm = float(np.linalg.norm(vec))
    if norm > 1e-9:
        vec = vec / norm
    return [round(float(x), 6) for x in vec]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    a = np.array(vec_a, dtype=np.float64)
    b = np.array(vec_b, dtype=np.float64)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom < 1e-9:
        return 0.0
    return float(np.dot(a, b) / denom)


def average_embeddings(vectors: list[list[float]]) -> list[float]:
    valid = [v for v in vectors if v]
    if not valid:
        return []
    mat = np.array(valid, dtype=np.float64)
    mean = np.mean(mat, axis=0)
    norm = float(np.linalg.norm(mean))
    if norm > 1e-9:
        mean = mean / norm
    return [round(float(x), 6) for x in mean]


def slugify(text: str) -> str:
    norm = normalize_text(text).strip()
    slug = re.sub(r"\s+", "-", norm)
    return slug[:90].strip("-") or "hilo-informativo"
