from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.intelligence.clustering import recompute_event_metrics, recompute_thread_metrics
from app.intelligence.nlp import compute_embedding, generate_summary
from app.models import Article, ScrapeRun, Source, StoryEvent, StoryThread
from app.scraper.catalog import BOLIVIAN_SOURCES_CATALOG


def seed_database(db: Session) -> None:
    # 1. Seed Sources
    existing_sources = {s.slug: s for s in db.query(Source).all()}
    for src_data in BOLIVIAN_SOURCES_CATALOG:
        if src_data["slug"] not in existing_sources:
            src = Source(**src_data)
            db.add(src)
            db.flush()
            existing_sources[src.slug] = src
    db.commit()

    # Check if threads already exist
    if db.query(StoryThread).count() > 0:
        return

    now = datetime.now(timezone.utc)

    threads_blueprint = [
        {
            "title": "Avance de la minería aurífera y contaminación por mercurio en el río Beni y Parque Madidi",
            "slug": "mineria-aurifera-mercurio-rio-beni-madidi",
            "status": "active",
            "category": "Minería y Extractivismo",
            "primary_department": "La Paz",
            "departments_affected": ["La Paz", "Beni", "Pando"],
            "key_entities": ["Parque Nacional Madidi", "Río Beni", "CPEMB", "AJAM", "Defensoría del Pueblo"],
            "current_summary": (
                "Pueblos indígenas tacanas, tsimanes y mosetenes documentaron niveles críticos de mercurio y la expansión "
                "de dragas auríferas en los ríos Beni, Madre de Dios y Tuichi. Medios de investigación y radios comunitarias "
                "lideran el seguimiento ante la falta de operativos permanentes del Estado."
            ),
            "events": [
                {
                    "days_ago": 42,
                    "title": "Estudio comunitario revela altos niveles de mercurio en comunidades indígenas del río Beni",
                    "summary": (
                        "Muestras tomadas en comunidades ribereñas del pueblo Ese Ejja y Tsimane superan hasta siete veces "
                        "el límite permitido por la OMS, según reportes difundidos por periodismo de investigación ambiental."
                    ),
                    "department": "Beni",
                    "articles": [
                        {
                            "source_slug": "revista-nomadas",
                            "title": "El veneno invisible del oro: comunidades del río Beni superan en 700% el límite de mercurio",
                            "url": "https://revistanomadas.com/mercurio-comunidades-rio-beni-investigacion",
                            "content": (
                                "Una investigación de campo en comunidades ribereñas de los ríos Beni y Quiquibey documentó "
                                "que mujeres y niños indígenas presentan concentraciones alarmantes de metilmercurio por el consumo "
                                "de pescado contaminado por la actividad aurífera aguas arriba."
                            ),
                        },
                        {
                            "source_slug": "la-region",
                            "title": "Pueblos indígenas de la Amazonía boliviana exigen freno al uso de mercurio en la minería del oro",
                            "url": "https://www.laregion.bo/pueblos-indigenas-amazonia-exigen-freno-mercurio",
                            "content": (
                                "Organizaciones indígenas del norte de La Paz y Beni presentaron ante relatores internacionales "
                                "evidencia sobre la degradación de las cuencas amazónicas y la ausencia de controles sobre la importación de mercurio."
                            ),
                        },
                    ],
                },
                {
                    "days_ago": 18,
                    "title": "Guardaparques y capitanías denuncian incursión de balsas mineras en zona de amortiguamiento del Madidi",
                    "summary": (
                        "Radios comunitarias y agencias independientes reportan la presencia de nuevas cuadrillas y dragas en el "
                        "sector alto del río Tuichi y Guanay sin consulta previa libre e informada."
                    ),
                    "department": "La Paz",
                    "articles": [
                        {
                            "source_slug": "erbol",
                            "title": "Corresponsales en Norte de La Paz alertan sobre nuevas dragas cerca del área protegida Madidi",
                            "url": "https://erbol.com.bo/norte-la-paz-alertan-dragas-area-protegida-madidi",
                            "content": (
                                "Desde Guanay y Rurrenabaque, dirigentes comunales denunciaron a través de la Red Erbol que "
                                "operadores auríferos abrieron sendas y trasladaron maquinaria pesada hacia riberas protegidas."
                            ),
                        },
                        {
                            "source_slug": "anf",
                            "title": "Defensoría del Pueblo pide a la AJAM informe sobre derechos mineros otorgados cerca de áreas protegidas",
                            "url": "https://www.noticiasfides.com/nacional/defensoria-pide-informe-ajam-areas-protegidas",
                            "content": (
                                "La Defensoría del Pueblo reiteró que ninguna cuadrícula minera puede vulnerar la intangibilidad "
                                "de los territorios indígenas ni poner en riesgo las fuentes de agua de la cuenca amazónica."
                            ),
                        },
                        {
                            "source_slug": "guardiana",
                            "title": "Vacíos de fiscalización permiten que cooperativas auríferas operen sin licencia ambiental en el norte paceño",
                            "url": "https://guardiana.com.bo/investigacion/vacios-fiscalizacion-cooperativas-auriferas-norte-paceno",
                            "content": (
                                "Una revisión de registros públicos muestra que más del 75% de las operaciones auríferas en los ríos "
                                "del norte de La Paz carecen de estudio de evaluación de impacto ambiental actualizado."
                            ),
                        },
                    ],
                },
                {
                    "days_ago": 2,
                    "title": "Cabildo de comunidades amazónicas exige auditoría ambiental y suspensión de trámites mineros en ríos",
                    "summary": (
                        "Representantes de 24 comunidades del norte de La Paz y Beni se declararon en emergencia permanente "
                        "y otorgaron un plazo de 15 días para la instalación de una comisión interinstitucional en territorio."
                    ),
                    "department": "La Paz",
                    "articles": [
                        {
                            "source_slug": "palabra-del-beni",
                            "title": "Comunidades de Rurrenabaque y San Buenaventura se declaran en emergencia por contaminación del río Beni",
                            "url": "https://lapalabradelbeni.com/rurrenabaque-san-buenaventura-emergencia-rio-beni",
                            "content": (
                                "Autoridades comunales y operadores de ecoturismo advirtieron que la turbidez del agua y el uso de "
                                "mercurio amenazan tanto la salud humana como la economía sostenible de las comunidades amazónicas."
                            ),
                        },
                        {
                            "source_slug": "sumando-voces",
                            "title": "Mujeres indígenas lideran monitoreo comunitario del agua frente al avance extractivo en la Amazonía",
                            "url": "https://sumandovoces.com.bo/mujeres-indigenas-monitoreo-comunitario-agua-amazonia",
                            "content": (
                                "Brigadas de mujeres indígenas capacitaron a jóvenes comunarios para registrar con georreferenciación "
                                "los puntos de desmonte ribereño y descargas de sedimentos."
                            ),
                        },
                    ],
                },
            ],
        },
        {
            "title": "Defensa comunitaria de la Reserva Nacional de Tariquía frente a proyectos de exploración petrolera",
            "slug": "defensa-reserva-nacional-tariquia-exploracion-petrolera",
            "status": "active",
            "category": "Medio Ambiente y Territorio",
            "primary_department": "Tarija",
            "departments_affected": ["Tarija"],
            "key_entities": ["Reserva de Tariquía", "YPFB", "SERNAP", "CONTIOCAP", "Tribunal Agroambiental"],
            "current_summary": (
                "Comunarios de Chiquiacá y Tariquía en el departamento de Tarija sostienen vigilias y acciones legales "
                "contra el ingreso de actividades hidrocarburíferas al área protegida que abastece de agua y biodiversidad al valle central y Chaco."
            ),
            "events": [
                {
                    "days_ago": 35,
                    "title": "Subcentrales campesinas de Tariquía denuncian reactivación de cronograma de ingreso al bloque exploratorio",
                    "summary": (
                        "Medios regionales de Tarija y radios del sur reportaron el rechazo de las comunidades locales a los "
                        "intentos de socialización fragmentada para el ingreso de equipos técnicos a la reserva."
                    ),
                    "department": "Tarija",
                    "articles": [
                        {
                            "source_slug": "el-pais-tarija",
                            "title": "Chiquiacá se declara en estado de emergencia ante posible ingreso de maquinaria hacia Tariquía",
                            "url": "https://www.elpais.bo/tarija/chiquiaca-estado-emergencia-reserva-tariquia",
                            "content": (
                                "Productores apícolas y agrícolas del cantón Chiquiacá instalaron una asamblea permanente "
                                "asegurando que la perforación de pozos en zona de recarga hídrica afectará de manera irreversible sus vertientes."
                            ),
                        },
                        {
                            "source_slug": "radio-aclo",
                            "title": "Comunidades de Padcaya y Entre Ríos ratifican defensa del agua en la Reserva de Tariquía",
                            "url": "https://aclo.org.bo/tarija-comunidades-padcaya-entre-rios-defensa-agua-tariquia",
                            "content": (
                                "A través de Radio ACLO Tarija, dirigentes comunales denunciaron presiones y divisiones internas "
                                "promovidas para validar autorizaciones de ingreso al área protegida."
                            ),
                        },
                    ],
                },
                {
                    "days_ago": 11,
                    "title": "Presentan acción ambiental preventiva y denuncian hostigamiento a defensores de Tariquía",
                    "summary": (
                        "Colectivos ambientales, instituciones de derechos humanos y comunarios presentaron un recurso ante la "
                        "jurisdicción agroambiental exigiendo medidas cautelares para resguardar la reserva."
                    ),
                    "department": "Tarija",
                    "articles": [
                        {
                            "source_slug": "anf",
                            "title": "Defensores de Tariquía denuncian procesos penales contra comunarios que mantienen vigilia pacífica",
                            "url": "https://www.noticiasfides.com/sociedad/defensores-tariquia-denuncian-procesos-vigilia",
                            "content": (
                                "Representantes de CONTIOCAP y comunarios de Chiquiacá denunciaron en conferencia de prensa que "
                                "al menos ocho dirigentes campesinos enfrentan notificaciones judiciales por defender el área protegida."
                            ),
                        },
                        {
                            "source_slug": "la-region",
                            "title": "Tariquía: por qué el bosque nublado de Tarija es vital para el agua del sur de Bolivia",
                            "url": "https://www.laregion.bo/tariquia-bosque-nublado-vital-agua-sur-bolivia",
                            "content": (
                                "Especialistas en hidrología explican que la Reserva Nacional de Flora y Fauna Tariquía regula el "
                                "régimen hídrico de las cuencas Bermejo y Grande de Tarija."
                            ),
                        },
                        {
                            "source_slug": "cabildeo-digital",
                            "title": "Mujeres defensoras de Tariquía cumplen semanas de guardia en caminos comunales",
                            "url": "https://www.cabildeodigital.com/mujeres-defensoras-tariquia-guardia-caminos",
                            "content": (
                                "Con turnos rotativos día y noche, las mujeres del cantón Chiquiacá encabezan la resistencia pacífica "
                                "exigiendo respeto al Acuerdo de Escazú."
                            ),
                        },
                    ],
                },
            ],
        },
        {
            "title": "Crisis de incendios forestales, desmontes y emergencia hídrica posfuego en la Chiquitanía",
            "slug": "crisis-incendios-forestales-emergencia-hidrica-chiquitania",
            "status": "active",
            "category": "Medio Ambiente y Territorio",
            "primary_department": "Santa Cruz",
            "departments_affected": ["Santa Cruz", "Beni"],
            "key_entities": ["Chiquitanía", "ABT", "INRA", "SENAMHI", "Defensoría del Pueblo"],
            "current_summary": (
                "Tras meses de incendios forestales que devastaron millones de hectáreas de bosque seco chiquitano y Amazonía, "
                "las comunidades indígenas y campesinas enfrentan escasez de agua potable, pérdida de medios de vida y reclaman la abrogación de normas que incentivan el desmonte."
            ),
            "events": [
                {
                    "days_ago": 50,
                    "title": "Bomberos voluntarios y municipios chiquitanos alertan desborde de focos de calor en San Ignacio y Concepción",
                    "summary": (
                        "Antes de la declaratoria nacional, reportes locales desde San Ignacio de Velasco, Concepción y Ascensión de Guarayos "
                        "advertían que el fuego había ingresado a reservas forestales y territorios indígenas."
                    ),
                    "department": "Santa Cruz",
                    "articles": [
                        {
                            "source_slug": "la-region",
                            "title": "Comunidades de Monte Verde y Lomerío combaten el fuego con herramientas manuales ante falta de apoyo aéreo",
                            "url": "https://www.laregion.bo/comunidades-monte-verde-lomerio-combaten-fuego",
                            "content": (
                                "Caciques indígenas y cuadrillas comunales pidieron auxilio urgente tras cinco días de incendios "
                                "continuos que destruyeron sistemas de tuberías de agua y cultivos de yuca y plátano."
                            ),
                        },
                        {
                            "source_slug": "el-deber",
                            "title": "Gobernación y alcaldías de la Chiquitanía piden declaratoria de desastre nacional por incendios",
                            "url": "https://eldeber.com.bo/santa-cruz/alcaldias-chiquitania-declaratoria-desastre-incendios",
                            "content": (
                                "El humo denso obligó a suspender vuelos y clases presenciales mientras más de 40 comunidades "
                                "rurales reportaron daños directos en sus fuentes de abastecimiento."
                            ),
                        },
                    ],
                },
                {
                    "days_ago": 24,
                    "title": "Investigación identifica que más del 60% de áreas quemadas coincide con desmontes no autorizados y tierras en conflicto",
                    "summary": (
                        "Cruces de mapas satelitales con catastros de la ABT e INRA revelan patrones recurrentes de quema "
                        "para ampliación de frontera agropecuaria y especulación de tierras."
                    ),
                    "department": "Santa Cruz",
                    "articles": [
                        {
                            "source_slug": "revista-nomadas",
                            "title": "Mapa de la devastación: cómo el fuego sigue la ruta de los desmontes ilegales en Santa Cruz y Beni",
                            "url": "https://revistanomadas.com/mapa-devastacion-fuego-desmontes-ilegales-santa-cruz-beni",
                            "content": (
                                "El análisis geoespacial de los polígonos incendiados demuestra que las multas administrativas "
                                "por hectárea desmontada siguen siendo mínimas frente a la rentabilidad del tráfico de tierras."
                            ),
                        },
                        {
                            "source_slug": "guardiana",
                            "title": "Sanciones de la ABT por quemas ilegales apenas alcanzan a una fracción de los procesos iniciados",
                            "url": "https://guardiana.com.bo/medio-ambiente/sanciones-abt-quemas-ilegales-fraccion",
                            "content": (
                                "Datos oficiales solicitados por acceso a la información revelan cuellos de botella en la "
                                "ejecución coactiva de multas por incendios forestales de gestiones pasadas."
                            ),
                        },
                        {
                            "source_slug": "los-tiempos",
                            "title": "Organizaciones civiles y colegios profesionales exigen abrogar paquete de leyes incendiarias",
                            "url": "https://www.lostiempos.com/actualidad/pais/organizaciones-exigen-abrogar-leyes-incendiarias",
                            "content": (
                                "En Cochabamba, Santa Cruz y La Paz se realizaron movilizaciones ciudadanas demandando sanciones "
                                "penales efectivas y restauración ecológica con presupuesto garantizado."
                            ),
                        },
                    ],
                },
                {
                    "days_ago": 4,
                    "title": "Crisis posfuego: 38 comunidades chiquitanas sufren contaminación de atajados por ceniza y escasez de agua",
                    "summary": (
                        "Con las primeras lluvias, el arrastre de ceniza y materia orgánica quemada contaminó represas comunales "
                        "y vertientes en San Matías, Roboré y San Ignacio, situación poco visibilizada tras apagarse las llamas."
                    ),
                    "department": "Santa Cruz",
                    "articles": [
                        {
                            "source_slug": "muy-waso",
                            "title": "Cuando se apagan las cámaras: mujeres chiquitanas enfrentan la crisis del agua contaminada por cenizas",
                            "url": "https://muywaso.com/mujeres-chiquitanas-crisis-agua-contaminada-cenizas",
                            "content": (
                                "Aunque los titulares televisivos dejaron de hablar de la Chiquitanía tras las lluvias, en las "
                                "comunidades indígenas el agua de los atajados se volvió negra y provoca afecciones gastrointestinales y dérmicas."
                            ),
                        },
                        {
                            "source_slug": "erbol",
                            "title": "Corresponsalía en San Ignacio reporta que cisternas municipales no abastecen a comunidades alejadas",
                            "url": "https://erbol.com.bo/santa-cruz/cisternas-no-abastecen-comunidades-chiquitanas-posincendio",
                            "content": (
                                "Autoridades comunales piden filtros potabilizadores, rehabilitación de pozos perforados y semillas "
                                "para recuperar los chacos perdidos durante los incendios."
                            ),
                        },
                    ],
                },
            ],
        },
        {
            "title": "Contaminación minera y riesgo en diques de colas en la cuenca alta del río Pilcomayo",
            "slug": "contaminacion-minera-diques-colas-cuenca-rio-pilcomayo",
            "status": "active",
            "category": "Minería y Extractivismo",
            "primary_department": "Potosí",
            "departments_affected": ["Potosí", "Chuquisaca", "Tarija"],
            "key_entities": ["Río Pilcomayo", "COMIBOL", "Cerro Rico", "Defensoría del Pueblo"],
            "current_summary": (
                "Comunidades campesinas e indígenas de Potosí, Chuquisaca y el Chaco tarijeño alertan sobre filtraciones "
                "y falta de mantenimiento en diques de colas mineros que descargan metales pesados hacia afluentes del río Pilcomayo."
            ),
            "events": [
                {
                    "days_ago": 29,
                    "title": "Alerta en municipios de Potosí y Chuquisaca por turbidez y residuos minerales en afluentes del Pilcomayo",
                    "summary": (
                        "Radios comunitarias del sur reportaron cambios de coloración y mortandad de peces en tramos de la "
                        "cuenca alta y media del río Pilcomayo, pidiendo auditoría a los ingenios mineros."
                    ),
                    "department": "Potosí",
                    "articles": [
                        {
                            "source_slug": "radio-pio-xii",
                            "title": "Comunarios de la ribera del Pilcomayo denuncian descargas nocturnas de ingenios en Potosí",
                            "url": "https://radiopioxii.org/comunarios-ribera-pilcomayo-denuncian-descargas-ingenios",
                            "content": (
                                "Agricultores de los municipios de Betanzos y Yocalla alertaron a Radio Pío XII que las aguas "
                                "presentan espuma y sedimentos plomizos que inutilizan los canales de riego comunitarios."
                            ),
                        },
                        {
                            "source_slug": "el-potosi",
                            "title": "Piden inspección técnica urgente a diques de colas en la ribera de los ingenios potosinos",
                            "url": "https://elpotosi.net/local/inspeccion-tecnica-diques-colas-ingenios-potosi",
                            "content": (
                                "Técnicos ambientales advirtieron que el inicio de la época de lluvias incrementa el riesgo de "
                                "rebalse en estructuras de almacenamiento de colas que operan al límite de su capacidad."
                            ),
                        },
                    ],
                },
                {
                    "days_ago": 6,
                    "title": "Pueblo Weenhayek y regantes de Chuquisaca exigen monitoreo trinacional independiente del río Pilcomayo",
                    "summary": (
                        "Representantes indígenas de Villa Montes y regantes de Chuquisaca reclamaron que los informes de "
                        "calidad del agua incluyan muestreos participativos en época de crecida."
                    ),
                    "department": "Chuquisaca",
                    "articles": [
                        {
                            "source_slug": "correo-del-sur",
                            "title": "Regantes de Chuquisaca y Tarija conforman bloque de defensa de la cuenca del Pilcomayo",
                            "url": "https://correodelsur.com/local/regantes-chuquisaca-tarija-bloque-defensa-pilcomayo",
                            "content": (
                                "Productores hortícolas y frutícolas de los valles chuquisaqueños advirtieron que la contaminación "
                                "minera pone en riesgo la seguridad alimentaria y la certificación de sus productos."
                            ),
                        },
                        {
                            "source_slug": "radio-aclo",
                            "title": "Capitanías Weenhayek en el Gran Chaco piden estudios de metales pesados en el sábalo del Pilcomayo",
                            "url": "https://aclo.org.bo/chaco-capitanias-weenhayek-estudios-metales-pesados-pilcomayo",
                            "content": (
                                "Familias pesqueras del pueblo Weenhayek en Villa Montes señalaron que su subsistencia depende "
                                "directamente de la salud ecológica del río Pilcomayo."
                            ),
                        },
                    ],
                },
            ],
        },
        {
            "title": "Desabastecimiento de diésel, filas en surtidores e impacto en el transporte y producción de alimentos",
            "slug": "desabastecimiento-diesel-filas-surtidores-impacto-alimentos",
            "status": "active",
            "category": "Economía y Abastecimiento",
            "primary_department": "Nacional",
            "departments_affected": ["Santa Cruz", "La Paz", "Cochabamba", "Oruro", "Tarija"],
            "key_entities": ["YPFB", "ANH", "EMAPA", "ABC"],
            "current_summary": (
                "La irregularidad en la provisión de diésel y gasolina genera filas recurrentes en estaciones de servicio "
                "del eje central y provincias, afectando la logística del transporte pesado, el agro y los costos de la canasta familiar."
            ),
            "events": [
                {
                    "days_ago": 21,
                    "title": "Productores agrícolas y transporte interdepartamental reportan escasez de diésel en provincias",
                    "summary": (
                        "Mientras en las capitales se prioriza el despacho, cooperativas agrícolas y sindicatos provinciales "
                        "denuncian que los surtidores rurales reciben cupos reducidos."
                    ),
                    "department": "Cochabamba",
                    "articles": [
                        {
                            "source_slug": "erbol",
                            "title": "Municipios productores de papa y hortalizas en Cochabamba y La Paz alertan falta de diésel para tractores",
                            "url": "https://erbol.com.bo/economia/municipios-productores-alertan-falta-diesel-tractores",
                            "content": (
                                "Alcaldes y centrales agrarias de provincias del valle alto y altiplano reportaron que los "
                                "productores deben trasladarse decenas de kilómetros con bidones para conseguir combustible."
                            ),
                        },
                        {
                            "source_slug": "brujula-digital",
                            "title": "Importación de combustibles presiona las reservas de divisas y genera cuellos de botella logísticos",
                            "url": "https://www.brujuladigital.net/economia/importacion-combustibles-divisas-logistica",
                            "content": (
                                "Economistas advierten que los retrasos en pagos a proveedores internacionales provocan baches "
                                "intermitentes en la cadena de distribución interna de YPFB."
                            ),
                        },
                        {
                            "source_slug": "la-razon",
                            "title": "YPFB anuncia incremento en despachos de diésel y controles conjuntos con la ANH contra el desvío",
                            "url": "https://www.la-razon.com/economia/ypfb-incremento-despachos-diesel-controles-anh",
                            "content": (
                                "La estatal petrolera informó que reforzó la recepción en plantas de almacenaje de Senkata, "
                                "Palmasola y Gualberto Villarroel para normalizar el abastecimiento."
                            ),
                        },
                    ],
                },
                {
                    "days_ago": 1,
                    "title": "Mercados populares registran incremento en fletes de traslado de alimentos desde zonas productoras",
                    "summary": (
                        "Comerciantes minoristas y transportistas señalan que el tiempo de espera en surtidores y la escasez "
                        "de repuestos encarecen el transporte de verduras, granos y tubérculos hacia las ciudades."
                    ),
                    "department": "La Paz",
                    "articles": [
                        {
                            "source_slug": "guardiana",
                            "title": "Radiografía del costo del transporte: cómo las filas por diésel impactan el precio de los alimentos",
                            "url": "https://guardiana.com.bo/economia/radiografia-costo-transporte-filas-diesel-alimentos",
                            "content": (
                                "Un recorrido por centros de abasto en El Alto, Cochabamba y Santa Cruz muestra que los camiones "
                                "pierden entre uno y dos días de viaje haciendo fila por combustible."
                            ),
                        },
                        {
                            "source_slug": "el-deber",
                            "title": "Sectores productivos piden garantizar diésel continuo para no comprometer la campaña agrícola",
                            "url": "https://eldeber.com.bo/economia/sectores-productivos-garantizar-diesel-campana-agricola",
                            "content": (
                                "Representantes del agro advirtieron que cada semana de retraso en la preparación de suelos "
                                "reduce el rendimiento de granos estratégicos para el mercado interno."
                            ),
                        },
                        {
                            "source_slug": "rimay-pampa",
                            "title": "Comunidades del altiplano denuncian sobreprecio de combustibles revendidos en ferias rurales",
                            "url": "https://rimaypampa.com/comunidades-altiplano-sobreprecio-combustibles-ferias",
                            "content": (
                                "Ante la ausencia de estaciones de servicio en municipios alejados, transportistas rurales "
                                "pagan hasta el doble del precio oficial por litro de diésel."
                            ),
                        },
                    ],
                },
            ],
        },
        {
            "title": "Sequía y contaminación urbana-minera en los lagos Uru Uru y Poopó afectan a comunidades originarias",
            "slug": "sequia-contaminacion-lagos-uru-uru-poopo-oruro",
            "status": "monitoring",
            "category": "Medio Ambiente y Territorio",
            "primary_department": "Oruro",
            "departments_affected": ["Oruro"],
            "key_entities": ["Lago Uru Uru", "Lago Poopó", "COMIBOL", "SENAMHI"],
            "current_summary": (
                "Las comunidades originarias Urus de Oruro enfrentan el retroceso histórico del espejo de agua en los lagos "
                "Poopó y Uru Uru, agravado por el desvío de caudales del río Desaguadero, pasivos ambientales mineros y residuos sólidos urbanos."
            ),
            "events": [
                {
                    "days_ago": 38,
                    "title": "Pueblos Urus denuncian mortandad de aves y acumulación de plásticos y aguas ácidas en el lago Uru Uru",
                    "summary": (
                        "Medios de Oruro y portales independientes visibilizaron el deterioro del canal Rosso y el ingreso de "
                        "aguas servidas y drenaje ácido de mina hacia el humedal Ramsar."
                    ),
                    "department": "Oruro",
                    "articles": [
                        {
                            "source_slug": "la-patria-oruro",
                            "title": "Comunidades de Llapallapani y Puñaca Tinta María piden declaratoria de emergencia por sequía en el Poopó",
                            "url": "https://lapatria.bo/oruro/llapallapani-punaca-emergencia-sequia-poopo",
                            "content": (
                                "Autoridades originarias de la nación Uru señalaron que la falta de agua obligó a más del 40% "
                                "de los jóvenes de sus comunidades a migrar temporalmente por la desaparición de la pesca."
                            ),
                        },
                        {
                            "source_slug": "muy-waso",
                            "title": "La resistencia de las mujeres Urus: tejer memoria y vida frente a un lago que se seca",
                            "url": "https://muywaso.com/resistencia-mujeres-urus-lago-poopo-oruro",
                            "content": (
                                "Crónica desde las comunidades Urus en Oruro sobre cómo las mujeres sostienen la identidad cultural "
                                "y la economía comunitaria mediante la artesanía en totora pese a la crisis ecológica."
                            ),
                        },
                    ],
                },
                {
                    "days_ago": 9,
                    "title": "Auditoría ciudadana advierte retraso en plantas de tratamiento y remediación de pasivos mineros en Oruro",
                    "summary": (
                        "Organizaciones socioambientales de Oruro presentaron un balance que revela una ejecución menor al 30% "
                        "en los proyectos comprometidos para recuperar la subcuenca Huanuni-Uru Uru."
                    ),
                    "department": "Oruro",
                    "articles": [
                        {
                            "source_slug": "sumando-voces",
                            "title": "Colectivos de Oruro exigen cumplimiento de sentencia agroambiental para salvar el lago Uru Uru",
                            "url": "https://sumandovoces.com.bo/colectivos-oruro-sentencia-agroambiental-lago-uru-uru",
                            "content": (
                                "El monitoreo ciudadano verificó que los canales que desembocan en el lago Uru Uru continúan "
                                "arrastrando residuos sólidos y efluentes sin tratamiento adecuado."
                            ),
                        },
                        {
                            "source_slug": "erbol",
                            "title": "Productores de quinua y camélidos del sur de Oruro reportan salinización de pozos de agua",
                            "url": "https://erbol.com.bo/oruro/productores-quinua-camelidos-salinizacion-pozos-agua",
                            "content": (
                                "Comunarios de municipios cercanos al lago Poopó denunciaron que el déficit hídrico redujo "
                                "drásticamente los bofedales para el ganado camélido."
                            ),
                        },
                    ],
                },
            ],
        },
    ]

    total_articles_seeded = 0
    total_events_seeded = 0

    for th_data in threads_blueprint:
        th_vec = compute_embedding(
            f"{th_data['title']} {th_data['current_summary']} {' '.join(th_data['key_entities'])} {th_data['primary_department']}"
        )
        thread = StoryThread(
            title=th_data["title"],
            slug=th_data["slug"],
            current_summary=th_data["current_summary"],
            status=th_data["status"],
            category=th_data["category"],
            primary_department=th_data["primary_department"],
            departments_affected=th_data["departments_affected"],
            key_entities=th_data["key_entities"],
            thread_embedding=th_vec,
        )
        db.add(thread)
        db.flush()

        for ev_data in th_data["events"]:
            ev_dt = now - timedelta(days=ev_data["days_ago"])
            ev_vec = compute_embedding(f"{ev_data['title']} {ev_data['summary']} {ev_data['department']}")
            event = StoryEvent(
                thread_id=thread.id,
                title=ev_data["title"],
                summary=ev_data["summary"],
                event_date=ev_dt,
                primary_department=ev_data["department"],
                category=th_data["category"],
                entities=th_data["key_entities"][:5],
                centroid_embedding=ev_vec,
            )
            db.add(event)
            db.flush()
            total_events_seeded += 1

            for idx, art_data in enumerate(ev_data["articles"]):
                src = existing_sources.get(art_data["source_slug"])
                if not src:
                    continue
                art_dt = ev_dt + timedelta(hours=idx * 2)
                art_summary = generate_summary(art_data["title"], art_data["content"])
                art_vec = compute_embedding(f"{art_data['title']} {art_summary} {ev_data['department']}")
                article = Article(
                    source_id=src.id,
                    event_id=event.id,
                    url=art_data["url"],
                    title=art_data["title"],
                    content=art_data["content"],
                    summary=art_summary,
                    published_at=art_dt,
                    scraped_at=art_dt + timedelta(minutes=25),
                    department=ev_data["department"],
                    category=th_data["category"],
                    entities=th_data["key_entities"][:4],
                    embedding=art_vec,
                )
                db.add(article)
                src.total_articles_collected = (src.total_articles_collected or 0) + 1
                src.last_scraped_at = now - timedelta(hours=2)
                total_articles_seeded += 1

            db.flush()
            recompute_event_metrics(db, event)

        db.flush()
        recompute_thread_metrics(db, thread)

    initial_run = ScrapeRun(
        started_at=now - timedelta(hours=2, minutes=4),
        finished_at=now - timedelta(hours=2),
        trigger="scheduled",
        status="completed",
        sources_scanned=len(existing_sources),
        new_articles=total_articles_seeded,
        new_events=total_events_seeded,
        updated_threads=len(threads_blueprint),
        details={"note": "Escaneo inicial matutino de fuentes nacionales, regionales, comunitarias y alternativas."},
    )
    db.add(initial_run)
    db.commit()
