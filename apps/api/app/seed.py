from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.intelligence.clustering import recompute_event_metrics, recompute_thread_metrics
from app.intelligence.nlp import compute_embedding, generate_summary
from app.models import Article, ScrapeRun, Source, StoryEvent, StoryThread
from app.scraper.catalog import BOLIVIAN_SOURCES_CATALOG
from app.scraper.engine import run_daily_scan


def seed_database(db: Session, run_live_after_seed: bool = True) -> None:
    # 1. Sincronizar las 42 fuentes del catálogo nacional, digital, comunitario y regional
    existing_sources = {s.slug: s for s in db.query(Source).all()}
    for src_data in BOLIVIAN_SOURCES_CATALOG:
        if src_data["slug"] not in existing_sources:
            src = Source(**src_data)
            db.add(src)
            db.flush()
            existing_sources[src.slug] = src
        else:
            src = existing_sources[src_data["slug"]]
            src.name = src_data["name"]
            src.url = src_data["url"]
            src.rss_url = src_data["rss_url"]
            src.tier = src_data["tier"]
            src.department = src_data["department"]
            src.scrape_strategy = src_data["scrape_strategy"]
            src.description = src_data["description"]
    db.commit()

    if db.query(StoryThread).count() > 0:
        return

    now = datetime.now(timezone.utc)

    threads_blueprint = [
        {
            "title": "Caso 'Maletas', aprehensión del expresidente del TDJ de Santa Cruz Aldo Quezada y reestructuración judicial",
            "slug": "caso-maletas-aprehension-aldo-quezada-tdj-santa-cruz",
            "status": "active",
            "category": "Justicia y Seguridad Ciudadana",
            "primary_department": "Santa Cruz",
            "departments_affected": ["Santa Cruz", "Chuquisaca", "La Paz"],
            "key_entities": ["Caso Maletas", "TDJ Santa Cruz", "FELCN", "Fiscalía", "TSJ"],
            "current_summary": (
                "La investigación fiscal y policial por el denominado caso 'Maletas' y presunto tráfico de sustancias controladas "
                "derivó en allanamientos en Santa Cruz, el hallazgo de cajas fuertes vacías y la aprehensión del expresidente del "
                "Tribunal Departamental de Justicia (TDJ), Aldo Quezada, en medio de cambios en la Sala Plena del TSJ."
            ),
            "events": [
                {
                    "days_ago": 14,
                    "title": "Abren investigación fiscal por presunta red de encubrimiento y cobros irregulares en el caso 'Maletas'",
                    "summary": (
                        "Medios cruceños y portales digitales revelaron indicios sobre movimientos patrimoniales y resoluciones "
                        "judiciales observadas en torno al caso 'Maletas' en Santa Cruz."
                    ),
                    "department": "Santa Cruz",
                    "articles": [
                        {
                            "source_slug": "asuntos-centrales",
                            "title": "Fiscalía amplía pesquisas sobre operadores judiciales vinculados al caso Maletas en Santa Cruz",
                            "url": "https://asuntoscentrales.com/fiscalia-amplia-pesquisas-caso-maletas-santa-cruz",
                            "content": (
                                "Comisiones de fiscales de materia y agentes especiales iniciaron el cruce de llamadas y "
                                "declaraciones juradas de exautoridades judiciales del distrito cruceño."
                            ),
                        },
                        {
                            "source_slug": "oxigeno-bo",
                            "title": "Cuestionan actuación de vocales departamentales y piden auditoría del Consejo de la Magistratura",
                            "url": "https://oxigeno.bo/justicia/cuestionan-actuacion-vocales-auditoria-magistratura",
                            "content": (
                                "Legisladores y colegios de abogados exigieron transparentar los sorteos de causas sensibles "
                                "vinculadas a narcotráfico y legitimación de ganancias ilícitas."
                            ),
                        },
                    ],
                },
                {
                    "days_ago": 3,
                    "title": "Movimientos en la Sala Plena del TSJ en Sucre y operativos de allanamiento a exautoridades del TDJ",
                    "summary": (
                        "Mientras en Sucre se recompone la Sala Plena del Tribunal Supremo de Justicia, la FELCN y la Fiscalía "
                        "ejecutaron allanamientos en inmuebles del expresidente del TDJ de Santa Cruz."
                    ),
                    "department": "Santa Cruz",
                    "articles": [
                        {
                            "source_slug": "el-deber",
                            "title": "Fiscalía y FELCN allanan domicilio de exautoridad judicial en Santa Cruz dentro del caso Maletas",
                            "url": "https://eldeber.com.bo/santa-cruz/fiscalia-felcn-allanan-domicilio-caso-maletas-antecedente",
                            "content": (
                                "Los efectivos secuestraron documentación, equipos informáticos y verificaron la existencia de "
                                "cajas fuertes vacías en la residencia intervenida."
                            ),
                        },
                        {
                            "source_slug": "radio-fides",
                            "title": "Sala Plena del TSJ sesiona en Sucre en medio de acefalías y procesos contra exvocales",
                            "url": "https://radiofides.com/politica/sala-plena-tsj-sesiona-sucre-procesos-exvocales",
                            "content": (
                                "Magistrados del Tribunal Supremo de Justicia analizaron la situación de los tribunales "
                                "departamentales y la continuidad administrativa del Órgano Judicial."
                            ),
                        },
                    ],
                },
            ],
        },
        {
            "title": "Conflicto del Magisterio y la COB por transferencia de institutos técnicos y pliego sectorial",
            "slug": "conflicto-magisterio-cob-transferencia-institutos-tecnicos",
            "status": "active",
            "category": "Conflictos Sociales",
            "primary_department": "Nacional",
            "departments_affected": ["La Paz", "Potosí", "Cochabamba", "Santa Cruz"],
            "key_entities": ["Magisterio Rural", "COB", "Asamblea Legislativa"],
            "current_summary": (
                "Tras protestas y amenazas de bloqueo de carreteras contra el anteproyecto para transferir los institutos técnicos "
                "y tecnológicos a las gobernaciones, el Gobierno y el Magisterio Rural firmaron un acuerdo para suspender la medida, "
                "mientras la COB convoca a un ampliado nacional."
            ),
            "events": [
                {
                    "days_ago": 10,
                    "title": "Magisterio y rectores de institutos técnicos se declaran en emergencia contra proyecto de descentralización",
                    "summary": (
                        "Sindicatos de maestros urbanos y rurales denunciaron que el traspaso de institutos técnicos a las "
                        "gobernaciones pondría en riesgo los ítems y el presupuesto educativo."
                    ),
                    "department": "La Paz",
                    "articles": [
                        {
                            "source_slug": "exito-noticias",
                            "title": "Magisterio advierte con movilizaciones nacionales si no se retira el proyecto sobre institutos técnicos",
                            "url": "https://exitonoticias.com.bo/magisterio-advierte-movilizaciones-institutos-tecnicos",
                            "content": (
                                "Dirigentes de las federaciones departamentales de maestros señalaron que las gobernaciones "
                                "carecen de recursos para sostener la educación superior técnica."
                            ),
                        },
                        {
                            "source_slug": "radio-kollasuyo",
                            "title": "Docentes y estudiantes de institutos tecnológicos en Potosí marchan rechazando transferencia",
                            "url": "https://radiokollasuyo.bo/docentes-estudiantes-institutos-potosi-rechazan-transferencia",
                            "content": (
                                "En la Villa Imperial, delegaciones estudiantiles y sindicales recorrieron el centro exigiendo "
                                "que el Ministerio de Educación garantice el financiamiento estatal."
                            ),
                        },
                    ],
                },
            ],
        },
        {
            "title": "Inflación de alimentos, precio del pan, tarifas de transporte y emergencia financiera en Alcaldías (AMB)",
            "slug": "inflacion-alimentos-precio-pan-emergencia-financiera-alcaldias",
            "status": "active",
            "category": "Economía y Abastecimiento",
            "primary_department": "Nacional",
            "departments_affected": ["La Paz", "Potosí", "Cochabamba", "Santa Cruz", "Tarija"],
            "key_entities": ["INE", "AMB", "Defensoría del Pueblo", "EMAPA"],
            "current_summary": (
                "El incremento de costos en productos de la canasta familiar (como el pan en regiones, verduras y carne), sumado a "
                "la caída de ingresos por IDH y el encarecimiento de insumos para obras públicas, llevó a la Asociación de Municipalidades "
                "de Bolivia (AMB) y juntas vecinales a exigir medidas económicas de urgencia."
            ),
            "events": [
                {
                    "days_ago": 12,
                    "title": "INE reporta inflación acumulada de 6,03% impulsada por alimentos, almuerzo popular y transporte",
                    "summary": (
                        "El índice de precios al consumidor reflejó presiones en papa, cebolla, tomate, carne de res y "
                        "transporte urbano en las principales ciudades del país."
                    ),
                    "department": "Nacional",
                    "articles": [
                        {
                            "source_slug": "economy-bolivia",
                            "title": "Inflación acumulada llega al 6,03%: alimentos y costos logísticos presionan el bolsillo familiar",
                            "url": "https://www.economy.com.bo/economia/inflacion-acumulada-alimentos-costos-logisticos",
                            "content": (
                                "Analistas económicos advierten que el costo de reposición de insumos importados y la logística "
                                "del transporte continúan trasladándose a los precios minoristas en mercados."
                            ),
                        },
                        {
                            "source_slug": "el-alteno",
                            "title": "Amas de casa y gremiales en ferias de El Alto reclaman controles contra el agio y especulación",
                            "url": "https://www.elalteno.com.bo/ferias-el-alto-reclaman-controles-agio-especulacion",
                            "content": (
                                "En las ferias de la 16 de Julio y Río Seco, comerciantes y vecinos reportaron variaciones "
                                "semanales en abarrotes, pan y verduras traídas desde los valles."
                            ),
                        },
                    ],
                },
                {
                    "days_ago": 2,
                    "title": "Alcaldes de capitales y El Alto (AMB) dan ultimátum por reajuste de costos de obras y liquidez municipal",
                    "summary": (
                        "La Asociación de Municipalidades de Bolivia advirtió riesgo de paralización de obras y servicios de "
                        "aseo urbano y salud si no se aprueba un decreto de reajuste de precios y alivio financiero."
                    ),
                    "department": "La Paz",
                    "articles": [
                        {
                            "source_slug": "red-uno",
                            "title": "Alcaldes de la AMB piden decreto de reajuste de precios ante rescisión de contratos de obras",
                            "url": "https://www.reduno.com.bo/noticias/alcaldes-amb-decreto-reajuste-precios-obras-municipales",
                            "content": (
                                "Los burgomaestres de las nueve capitales más El Alto señalaron que las empresas constructoras "
                                "frenaron proyectos por el alza de materiales e insumos."
                            ),
                        },
                        {
                            "source_slug": "el-periodico-tarija",
                            "title": "Municipios de Tarija alertan caída crítica de ingresos por IDH y piden reprogramación financiera",
                            "url": "https://elperiodico.com.bo/municipios-tarija-alerta-caida-idh-reprogramacion",
                            "content": (
                                "Gobiernos municipales tarijeños advirtieron dificultades para cubrir contrapartes de proyectos "
                                "concurrentes, desayuno escolar y mantenimiento vial."
                            ),
                        },
                    ],
                },
            ],
        },
        {
            "title": "Tensión en el Trópico de Cochabamba: operativos policiales, retenes de UMOPAR y protesta de federaciones cocaleras",
            "slug": "tension-tropico-cochabamba-operativos-policiales-umopar-cocaleros",
            "status": "active",
            "category": "Conflictos Sociales",
            "primary_department": "Cochabamba",
            "departments_affected": ["Cochabamba"],
            "key_entities": ["Seis Federaciones del Trópico", "UMOPAR", "FELCN"],
            "current_summary": (
                "La ejecución de operativos antidroga y el control de puestos policiales en Villa Tunari y Shinahota generaron "
                "enfrentamientos entre afiliados de las Seis Federaciones del Trópico y efectivos de UMOPAR y la Policía."
            ),
            "events": [
                {
                    "days_ago": 7,
                    "title": "Sindicatos del Trópico declaran estado de alerta ante despliegue de patrullas de UMOPAR",
                    "summary": (
                        "A través de Radio Kawsachun Coca, dirigentes de las Seis Federaciones denunciaron operativos sin "
                        "coordinación local, mientras el Ministerio de Gobierno ratificó la presencia estatal en el Chapare."
                    ),
                    "department": "Cochabamba",
                    "articles": [
                        {
                            "source_slug": "kawsachun-coca",
                            "title": "Seis Federaciones del Trópico se declaran en vigilia permanente ante incursiones policiales",
                            "url": "https://kawsachuncoca.com/seis-federaciones-tropico-vigilia-incursiones-policiales",
                            "content": (
                                "Un ampliado de emergencia realizado en Lauca Ñ rechazó lo que califican como hostigamiento "
                                "a los productores de hoja de coca de Villa Tunari, Shinahota y Entre Ríos."
                            ),
                        },
                        {
                            "source_slug": "opinion",
                            "title": "Ministerio de Gobierno afirma que la Policía garantizará el libre tránsito y control en el Chapare",
                            "url": "https://www.opinion.com.bo/articulo/policial/policia-garantizara-control-chapare",
                            "content": (
                                "Autoridades policiales informaron que las unidades operativas continuarán realizando tareas de "
                                "interdicción y seguridad vial en la carretera Cochabamba-Santa Cruz."
                            ),
                        },
                    ],
                },
            ],
        },
        {
            "title": "Salvoconductos, solicitudes de asilo en México y controversia por salida del país de investigados",
            "slug": "salvoconductos-asilo-mexico-salida-investigados-beller-garcia-linera",
            "status": "active",
            "category": "Política y Gestión Pública",
            "primary_department": "La Paz",
            "departments_affected": ["La Paz", "Santa Cruz"],
            "key_entities": ["Cancillería", "Asamblea Legislativa", "Caso Hotel Las Américas", "Fiscalía"],
            "current_summary": (
                "La salida del país de Nadia Beller con salvoconducto hacia México y los reportes migratorios sobre el exvicepresidente "
                "Álvaro García Linera dentro del caso Hotel Las Américas desataron cuestionamientos legislativos, pedidos de informe "
                "a Migración y desmentidos sobre gestiones diplomáticas."
            ),
            "events": [
                {
                    "days_ago": 5,
                    "title": "Debate político y judicial por solicitudes de asilo diplomático y controles migratorios",
                    "summary": (
                        "Parlamentarios pidieron a la Cancillería y a la Dirección de Migración transparentar la lista de "
                        "personas con procesos pendientes que tramitan salvoconductos o salieron por pasos fronterizos."
                    ),
                    "department": "La Paz",
                    "articles": [
                        {
                            "source_slug": "vision-360",
                            "title": "Oposición y oficialismo chocan por el manejo de salvoconductos y alertas migratorias en casos sensibles",
                            "url": "https://www.vision360.bo/noticias/debate-salvoconductos-alertas-migratorias-casos",
                            "content": (
                                "Analistas y legisladores cuestionaron la falta de coordinación oportuna entre juzgados, "
                                "Fiscalía y Migración para ejecutar arraigos en investigaciones de alto perfil."
                            ),
                        },
                        {
                            "source_slug": "urgente-bo",
                            "title": "Piden petición de informe oral a Cancillería y Ministerio de Gobierno sobre salidas hacia México",
                            "url": "https://www.urgente.bo/noticias/piden-informe-oral-cancilleria-migracion-salidas-mexico",
                            "content": (
                                "En la Asamblea Legislativa Plurinacional se formalizaron cuestionarios escritos y orales "
                                "para esclarecer las actuaciones diplomáticas y de control en aeropuertos."
                            ),
                        },
                    ],
                },
            ],
        },
        {
            "title": "Control de combustibles y operativos contra el desvío y contrabando en fronteras y surtidores",
            "slug": "control-combustibles-operativos-desvio-contrabando-anh-ypfb-aduana",
            "status": "active",
            "category": "Economía y Abastecimiento",
            "primary_department": "Tarija",
            "departments_affected": ["Tarija", "Chuquisaca", "Oruro", "Santa Cruz"],
            "key_entities": ["ANH", "YPFB", "Aduana Nacional"],
            "current_summary": (
                "La Agencia Nacional de Hidrocarburos (ANH), la Policía y la Aduana intensificaron operativos en Yacuiba, Sucre, "
                "Oruro y pasos fronterizos ante el desvío ilegal de gasolina y diésel subvencionado y el contrabando."
            ),
            "events": [
                {
                    "days_ago": 8,
                    "title": "Refuerzan controles en plantas de YPFB y carreteras del sur por desvío de carburantes",
                    "summary": (
                        "Medios regionales del Gran Chaco, Tarija y Oruro reportaron intercepciones de cisternas y camiones "
                        "que transportaban combustible sin hoja de ruta autorizada."
                    ),
                    "department": "Tarija",
                    "articles": [
                        {
                            "source_slug": "yacuiba-noticias",
                            "title": "Investigan presuntas irregularidades en el control de salida de combustibles en planta de Yacuiba",
                            "url": "https://yacuibanoticias.com/investigan-control-salida-combustibles-planta-yacuiba",
                            "content": (
                                "Vecinos y transportistas del Gran Chaco exigieron auditoría al despacho de carburantes "
                                "en la zona fronteriza con Argentina."
                            ),
                        },
                        {
                            "source_slug": "la-patria-oruro",
                            "title": "Operativos conjuntos en rutas de Oruro y Chuquisaca comisaron miles de litros de combustible",
                            "url": "https://lapatria.bo/nacional/operativos-rutas-oruro-chuquisaca-comisaron-combustible",
                            "content": (
                                "La ANH informó que los combustibles incautados eran acopiados en bidones y tanques adaptados "
                                "para su reventa ilegal."
                            ),
                        },
                    ],
                },
            ],
        },
        {
            "title": "Denuncias por presunta red de venta de ítems y cobros irregulares en DGAC y NAABOL (Caso Cerimedo)",
            "slug": "denuncias-venta-items-cobros-irregulares-dgac-naabol-cerimedo",
            "status": "active",
            "category": "Justicia y Seguridad Ciudadana",
            "primary_department": "La Paz",
            "departments_affected": ["La Paz", "Pando", "Santa Cruz"],
            "key_entities": ["DGAC", "NAABOL", "Asamblea Legislativa", "Fiscalía"],
            "current_summary": (
                "Investigaciones periodísticas difundidas por medios digitales revelaron denuncias sobre una presunta red de "
                "intermediación y venta de cargos en entidades del sector aeronáutico (DGAC y NAABOL), motivando pedidos de "
                "investigación en el Legislativo."
            ),
            "events": [
                {
                    "days_ago": 6,
                    "title": "Portales de investigación destapan denuncias sobre direccionamiento de cargos en DGAC y NAABOL",
                    "summary": (
                        "Reportes de prensa independiente señalaron a exfuncionarios y operadores políticos por presuntos "
                        "cobros para designaciones en aeropuertos y aeronáutica civil."
                    ),
                    "department": "La Paz",
                    "articles": [
                        {
                            "source_slug": "cabildeo-digital",
                            "title": "Denuncian red de tráfico de influencias y cobros por cargos técnicos en el sector aeronáutico",
                            "url": "https://www.cabildeodigital.com/denuncian-trafico-influencias-cargos-sector-aeronautico",
                            "content": (
                                "Testimonios y capturas presentadas ante fiscalizadores apuntan a intermediarios que operaban "
                                "en la asignación de puestos en NAABOL y la DGAC."
                            ),
                        },
                    ],
                },
            ],
        },
        {
            "title": "Bolivia en la COP31, financiamiento internacional para bosques y crisis ambiental en cuencas regionales",
            "slug": "bolivia-cop31-financiamiento-bosques-crisis-ambiental-cuencas",
            "status": "active",
            "category": "Medio Ambiente y Territorio",
            "primary_department": "Nacional",
            "departments_affected": ["Santa Cruz", "Tarija", "Cochabamba", "Beni"],
            "key_entities": ["COP31", "ABT", "SERNAP", "Fiscalía"],
            "current_summary": (
                "Mientras Bolivia gestiona en la COP31 un paquete de 250 millones de euros y acuerdos con Brasil tras reportar "
                "una reducción de hectáreas quemadas, en los departamentos persisten procesos por sequía, descargas de aguas "
                "servidas al río Guadalquivir en Tarija y demandas de restauración ambiental."
            ),
            "events": [
                {
                    "days_ago": 9,
                    "title": "Regiones reclaman presupuesto para plantas de tratamiento de agua y prevención de incendios y sequía",
                    "summary": (
                        "En Tarija, Cochabamba y la Chiquitanía, colectivos y municipios advirtieron sobre el colapso de "
                        "lagunas de oxidación y el déficit hídrico en provincias."
                    ),
                    "department": "Tarija",
                    "articles": [
                        {
                            "source_slug": "la-voz-de-tarija",
                            "title": "Vecinos y ambientalistas de Tarija exigen solución definitiva a la contaminación del río Guadalquivir",
                            "url": "https://lavozdetarija.com/vecinos-tarija-solucion-contaminacion-rio-guadalquivir",
                            "content": (
                                "El colapso de los sistemas de tratamiento en San Lorenzo y Cercado continúa provocando "
                                "descargas de aguas residuales sin tratar hacia la cuenca del Guadalquivir."
                            ),
                        },
                        {
                            "source_slug": "la-region",
                            "title": "Especialistas piden que los fondos climáticos internacionales lleguen directamente a municipios y guardaparques",
                            "url": "https://www.laregion.bo/fondos-climaticos-municipios-guardaparques-bolivia",
                            "content": (
                                "Investigadores ambientales remarcaron que la reducción de incendios requiere equipamiento "
                                "permanente en áreas protegidas y control sobre quemas ilegales."
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
            ev_vec = compute_embedding(
                f"{ev_data['title']} {ev_data['summary']} {' '.join(th_data['key_entities'])} {ev_data['department']}"
            )
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
                art_vec = compute_embedding(
                    f"{art_data['title']} {art_summary} {' '.join(th_data['key_entities'])} {ev_data['department']}"
                )
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
                src.last_scraped_at = now - timedelta(hours=3)
                total_articles_seeded += 1

            db.flush()
            recompute_event_metrics(db, event)

        db.flush()
        recompute_thread_metrics(db, thread)

    initial_run = ScrapeRun(
        started_at=now - timedelta(hours=3, minutes=2),
        finished_at=now - timedelta(hours=3),
        trigger="seed",
        status="completed",
        sources_scanned=len(existing_sources),
        new_articles=total_articles_seeded,
        new_events=total_events_seeded,
        updated_threads=len(threads_blueprint),
        details={"note": "Base histórica cargada."},
    )
    db.add(initial_run)
    db.commit()

    # 2. Ejecutar escaneo real en vivo de las 42 fuentes bolivianas para poblar con las noticias reales del día
    if run_live_after_seed:
        run_daily_scan(db, trigger="scheduled", try_live_network=True, max_per_source=4)
