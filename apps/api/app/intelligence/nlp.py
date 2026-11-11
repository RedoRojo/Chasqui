import hashlib
import math
import re
import unicodedata

import numpy as np

SPANISH_STOPWORDS = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un",
    "para", "con", "no", "una", "su", "al", "lo", "como", "mas", "pero", "sus", "le",
    "ya", "o", "este", "si", "porque", "esta", "entre", "cuando", "muy", "sin", "sobre",
    "también", "tambien", "me", "hasta", "hay", "donde", "quien", "desde", "todo", "nos",
    "durante", "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante",
    "ellos", "e", "esto", "mi", "antes", "algunos", "unos", "yo", "otro", "otras",
    "otra", "tanto", "esa", "estos", "mucho", "quienes", "nada", "muchos", "cual",
    "poco", "ella", "estar", "estas", "algunas", "algo", "nosotros", "mis", "tu",
    "te", "ti", "tus", "ellas", "nosotras", "vosotros", "os", "mio", "mia",
    "mios", "mias", "tuyo", "tuya", "tuyos", "tuyas", "suyo", "suya", "suyos", "suyas",
    "nuestro", "nuestra", "nuestros", "nuestras", "vuestro", "vuestra", "vuestros",
    "fue", "fueron", "ha", "han", "habia", "segun", "según", "tras", "cada", "día", "dia",
    "hoy", "ayer", "bolivia", "boliviano", "boliviana", "nacional", "pais", "país",
}

DEPARTMENT_KEYWORDS: dict[str, list[str]] = {
    "La Paz": [
        "la paz", "el alto", "alteño", "alteña", "viacha", "achacachi", "caranavi",
        "coroico", "yungas", "chulumani", "madidi", "rurrenabaque", "mapiri", "tipuani",
        "guanay", "laja", "desaguadero", "copacabana", "patacamaya", "senkata",
        "murillo", "paceño", "paceña", "teleférico", "teleferico", "san pedro",
    ],
    "Santa Cruz": [
        "santa cruz", "cruceño", "cruceña", "montero", "warnes", "yapacani", "yapacaní",
        "san julian", "san julián", "chiquitania", "chiquitanía", "san ignacio de velasco",
        "roboré", "robore", "concepción", "san matías", "camiri", "pailon", "pailón",
        "puerto suárez", "samaipata", "viru viru", "palmasola", "norte integrado",
    ],
    "Cochabamba": [
        "cochabamba", "chapare", "trópico", "tropico", "quillacollo", "sacaba", "parotani",
        "colomi", "villa tunari", "el castillo", "shinahota", "chimoré", "chimore",
        "punata", "mizque", "aiquile", "capinota", "tiquipaya", "tunari", "cochabambino",
        "valluno", "reyes villa",
    ],
    "Potosí": [
        "potosi", "potosí", "cerro rico", "uyuni", "llallagua", "uncia", "uncía",
        "colquechaca", "tupiza", "villazon", "villazón", "betanzos", "cotagaita",
        "pilcomayo", "salar de uyuni", "norte de potosi", "potosino", "potosina",
    ],
    "Oruro": [
        "oruro", "poopo", "poopó", "uru uru", "huanuni", "challapata", "caracollo",
        "pisiga", "tambo quemado", "sabaya", "corque", "orureño", "orureña",
    ],
    "Tarija": [
        "tarija", "tariquia", "tariquía", "yacuiba", "villamontes", "villa montes",
        "bermejo", "carapari", "caraparí", "entre rios", "padcaya", "gran chaco",
        "san lorenzo", "guadalquivir", "la mamora", "tarijeño", "tarijeña",
    ],
    "Chuquisaca": [
        "chuquisaca", "sucre", "monteagudo", "camargo", "tarabuco", "padilla",
        "yamparaez", "incahuasi", "san lucas", "chuquisaqueño", "la calancha", "tsj",
    ],
    "Beni": [
        "beni", "trinidad", "riberalta", "guayaramerin", "guayaramerín", "san borja",
        "santa ana del yacuma", "reyes", "mamore", "mamoré", "beniano", "beniana",
    ],
    "Pando": [
        "pando", "cobija", "porvenir", "manuripi", "madre de dios", "tahauamanu",
        "el sena", "pandino", "acre",
    ],
}

CATEGORY_RULES: dict[str, list[str]] = {
    "Justicia y Seguridad Ciudadana": [
        "aprehenden", "aprehendido", "aprehension", "detencion", "detenido", "fiscalia",
        "fiscalía", "felcn", "felcc", "policia", "policía", "tdj", "tsj", "tribunal",
        "juez", "jueces", "vocal", "quezada", "maletas", "corrupcion", "corrupción",
        "allanamiento", "narcotrafico", "narcotráfico", "sustancias controladas",
        "umopar", "contrabando", "aduana", "feminicidio", "carcel", "cárcel",
        "penitenciaria", "juicio", "imputacion", "imputación", "salvoconducto", "beller",
        "asilo", "migracion", "migración", "cerimedo", "items", "ítems",
    ],
    "Política y Gestión Pública": [
        "gobierno", "presidente", "rodrigo paz", "lara", "legislatura", "asamblea",
        "legislativa", "diputados", "senadores", "senado", "gabinete", "ministro",
        "ministerio", "alcaldia", "alcaldía", "alcalde", "alcaldes", "amb", "concejal",
        "gobernacion", "gobernación", "elecciones", "tse", "cancilleria", "cancillería",
        "garcia linera", "garcía linera", "diplomatico", "bilateral", "decreto", "ley",
    ],
    "Economía y Abastecimiento": [
        "economia", "economía", "inflacion", "inflación", "precio", "precios", "pan",
        "canasta familiar", "alimentos", "mercados", "combustible", "combustibles",
        "diesel", "diésel", "gasolina", "surtidor", "fila", "filas", "anh", "ypfb",
        "dolar", "dólar", "divisas", "banca", "credito", "crédito", "presupuesto",
        "idh", "tributaria", "deuda", "financiamiento", "euros", "millones", "emapa",
        "fletes", "importacion", "exportacion", "producir", "productores",
    ],
    "Conflictos Sociales": [
        "bloqueo", "bloqueos", "paro", "marcha", "protesta", "movilizacion", "movilización",
        "magisterio", "maestros", "institutos", "cob", "ampliado", "cocaleros",
        "federaciones", "puesto de control", "rebasan", "conflicto", "huelga",
        "pliego", "demanda", "sindicato", "transporte", "gremiales", "vecinos",
        "emergencia", "cabildo", "cívica", "civica",
    ],
    "Salud y Servicios Básicos": [
        "salud", "sedes", "hospital", "medicamentos", "diabetes", "antirrabica",
        "antirrábica", "vacunacion", "vacunación", "cns", "educacion", "educación",
        "clases", "escuela", "colegios", "teleferico", "teleférico", "agua potable",
        "aguas servidas", "alcantarillado", "ecojet", "vuelos", "pasajes", "discapacidad",
    ],
    "Medio Ambiente y Territorio": [
        "incendio", "incendios", "hectareas", "hectáreas", "quemadas", "bosque", "bosques",
        "cop31", "cop 31", "amazonia", "amazonía", "sequia", "sequía", "contaminacion",
        "contaminación", "guadalquivir", "mercurio", "tariquia", "tariquía", "madidi",
        "chiquitania", "chiquitanía", "pilcomayo", "poopó", "uru uru", "clima",
    ],
    "Minería y Extractivismo": [
        "mineria", "minería", "minero", "mineros", "cooperativa", "cooperativas",
        "aurifera", "aurífera", "oro", "litio", "cerro rico", "comibol", "ajam",
        "fencomin", "dique de colas", "ingenio", "huanuni", "uyuni", "hidrocarburos",
    ],
}

KNOWN_ENTITIES: list[str] = [
    "FELCN", "FELCC", "TDJ Santa Cruz", "TSJ", "Fiscalía", "Magisterio Rural",
    "COB", "AMB", "YPFB", "ANH", "Aduana Nacional", "DGAC", "NAABOL", "SEDES",
    "INE", "Defensoría del Pueblo", "Asamblea Legislativa", "Cancillería",
    "Mi Teleférico", "UMOPAR", "COP31", "Caso Maletas", "Caso Hotel Las Américas",
    "Seis Federaciones del Trópico", "COMIBOL", "SERNAP", "INRA", "ABT", "AJAM",
    "SENAMHI", "EMAPA", "ABC",
]

SEMANTIC_CONCEPTS: list[list[str]] = [
    ["quezada", "maletas", "tdj", "aprehenden", "felcn", "allanamiento", "cajas", "vocal", "sustancias"],
    ["magisterio", "maestros", "institutos", "tecnicos", "transferencia", "gobierno", "suspende", "acuerdo", "educacion"],
    ["beller", "nadia", "salvoconducto", "mexico", "asilo", "cancilleria", "salida", "alanoca"],
    ["garcia", "linera", "asilo", "mexico", "migracion", "hotel", "americas", "calancha", "rada"],
    ["cocaleros", "tropico", "villa", "tunari", "castillo", "umopar", "policias", "federaciones", "kawsachun"],
    ["cerimedo", "zamora", "items", "dgac", "naabol", "ortiz", "gabinete", "corrupcion", "investigacion"],
    ["cop31", "alemania", "brasil", "lula", "bosques", "hectareas", "quemadas", "amazonia", "euros"],
    ["cob", "argollo", "ampliado", "sectores", "laborales", "movilizaciones", "pliego", "trabajadores"],
    ["tsj", "rosell", "saucedo", "sala", "plena", "magistrados", "judicial", "sucre"],
    ["alcaldia", "amb", "municipios", "presupuesto", "obras", "tributaria", "concejal", "reyes", "villa"],
    ["combustible", "gasolina", "diesel", "anh", "ypfb", "contrabando", "litros", "aduana", "mamora", "yacuiba"],
    ["precio", "pan", "inflacion", "canasta", "familiar", "mercados", "alimentos", "transporte", "pasajes"],
    ["salud", "sedes", "diabetes", "antirrabica", "campana", "hospital", "cns", "pacientes"],
    ["guadalquivir", "aguas", "servidas", "contaminacion", "san", "lorenzo", "tariquia", "pilcomayo", "uru"],
    ["incendio", "fuego", "chaqueo", "chiquitania", "sequia", "agua", "bosque", "abt"],
    ["mineria", "oro", "mercurio", "litio", "potosi", "cooperativas", "cerro", "rico", "madidi"],
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
    for suffix in (
        "ciones", "cion", "miento", "mientos", "idades", "idad",
        "mente", "eros", "eras", "istas", "ista", "ando", "iendo", "es", "s",
    ):
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
        return "Política y Gestión Pública"
    return max(scores.items(), key=lambda item: item[1])[0]


def extract_entities(title: str, content: str) -> list[str]:
    text = f"{title}. {content[:1500]}"
    found: list[str] = []
    lower_text = text.lower()
    for ent in KNOWN_ENTITIES:
        if ent.lower() in lower_text and ent not in found:
            found.append(ent)

    matches = re.findall(
        r"\b([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?:de|del|la|las|los|y)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+|\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,2})\b",
        text,
    )
    ignore = {
        "El Deber", "La Razón", "Los Tiempos", "Red Erbol", "Correo del Sur",
        "El País", "La Patria", "El Potosí", "Red Uno", "Unitel Digital",
        "Radio Fides", "Radio Panamericana", "Santa Cruz", "La Paz",
    }
    for m in matches:
        cleaned = m.strip()
        if cleaned not in found and cleaned not in ignore and len(cleaned) >= 5:
            found.append(cleaned)
        if len(found) >= 8:
            break
    return found[:8]


def generate_summary(title: str, content: str, max_chars: int = 320) -> str:
    clean = re.sub(r"\s+", " ", content).strip()
    if not clean or clean.lower() == title.strip().lower():
        return title.strip()
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
    vec = np.zeros(dim, dtype=np.float64)
    tokens = tokenize(text)
    if not tokens:
        return [0.0] * dim

    stems = [stem_es(t) for t in tokens]
    stem_counts: dict[str, int] = {}
    for s in stems:
        stem_counts[s] = stem_counts.get(s, 0) + 1

    num_concepts = min(len(SEMANTIC_CONCEPTS), 16)
    for idx in range(num_concepts):
        concept_terms = [stem_es(t) for t in SEMANTIC_CONCEPTS[idx]]
        hits = sum(stem_counts.get(ct, 0) for ct in concept_terms)
        if hits > 0:
            vec[idx] = math.log1p(hits) * 2.5

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
