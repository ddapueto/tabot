"""Seed script — Simula una empresa real con semanas de operación.
Crea datos realistas: leads, conversaciones, scoring, follow-ups, KB completo.

Uso: cd backend && uv run python scripts/seed_demo.py
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

# ─────────────────────────────────────────
# DATA
# ─────────────────────────────────────────

COMPANY_ID = uuid.UUID("a0000000-0000-0000-0000-000000000001")

COMPANY = {
    "id": COMPANY_ID,
    "name": "Casas del Bosque",
    "slug": "casas-del-bosque",
    "business_type": "Construccion de casas y cabanas de madera",
    "description": (
        "Empresa uruguaya con 15 anios de experiencia construyendo casas y cabanas de madera a medida. "
        "Mas de 200 casas entregadas en todo el pais. Trabajamos con pino tratado CCA, eucalipto y cedro importado. "
        "Ofrecemos diseno personalizado, construccion llave en mano, financiacion propia, y servicio post-venta. "
        "Showroom en Ruta 5 km 28, Canelones, con 3 modelos para visitar."
    ),
    "ai_personality": "Amigable, tuteo rioplatense natural (vos, tenes). Entusiasta sobre la madera. Menciona experiencia y showroom cuando sea relevante.",
    "ai_language": "es-UY",
    "ai_sales_goal": "Guiar al cliente hacia una visita al showroom o reunion virtual para cotizar. No presionar.",
    "ai_model": "llama-3.3-70b-versatile",
    "currency": "USD",
    "phone_number_id": "test-phone-id",
    "whatsapp_phone": "+59899000001",
    "timezone": "America/Montevideo",
    "business_hours": {"lun": "09:00-18:00", "mar": "09:00-18:00", "mie": "09:00-18:00", "jue": "09:00-18:00", "vie": "09:00-18:00", "sab": "09:00-13:00"},
    "is_active": True,
}

PRODUCTS = [
    {"name": "Tiny House Natura", "slug": "tiny-house", "category": "tiny_house", "price": 18500, "short_desc": "Tiny house 25m2 - Airbnb o estudio", "description": "Tiny house compacta de 25m2 ideal para alquiler turistico o estudio independiente. Pino tratado CCA, techo a dos aguas.", "specs": {"area_m2": 25, "dormitorios": 1, "banos": 1, "material": "Pino CCA", "dias": 30, "garantia": 5}, "features": ["Aislacion termica EPS", "Doble vidrio", "Cocina integrada", "Bano completo", "Deck 2x3m", "Instalacion electrica"], "price_notes": "No incluye cimientos ni conexiones. Transporte incluido hasta 100km."},
    {"name": "Cabana Weekend", "slug": "cabana-weekend", "category": "cabana", "price": 32000, "short_desc": "Cabana 40m2 con altillo - Escapada", "description": "Cabana de 40m2 con altillo dormitorio, perfecta para fin de semana. Rustica moderna con gran ventanal.", "specs": {"area_m2": 40, "dormitorios": 1, "banos": 1, "altillo": True, "material": "Pino+Eucalipto", "dias": 45, "garantia": 5}, "features": ["Aislacion termica", "Estufa a lena", "Altillo dormitorio", "Deck 4x3m", "Ventanal panoramico", "Doble vidrio"], "price_notes": "Incluye cimientos pilotes."},
    {"name": "Casa Familiar Roble", "slug": "casa-roble", "category": "casa", "price": 65000, "short_desc": "Casa 80m2 - 3 dorm, familia", "description": "Casa familiar 80m2, 3 dormitorios, living-comedor amplio. Eucalipto con terminaciones en pino cepillado.", "specs": {"area_m2": 80, "dormitorios": 3, "banos": 2, "material": "Eucalipto+Pino", "dias": 90, "garantia": 5}, "features": ["Calefaccion losa radiante", "Cocina americana", "Living 25m2", "Lavadero", "Doble vidrio", "Aislacion reforzada"], "price_notes": "Incluye electrica, sanitaria y cimientos."},
    {"name": "Casa Premium Cedro", "slug": "casa-cedro", "category": "casa", "price": 120000, "short_desc": "Casa 120m2 - 4 dorm, premium", "description": "Casa premium 120m2, 4 dormitorios, 2 pisos. Cedro importado con terminaciones de lujo. Diseno personalizable.", "specs": {"area_m2": 120, "dormitorios": 4, "banos": 3, "pisos": 2, "material": "Cedro importado", "dias": 150, "garantia": 10}, "features": ["Smart home", "Garage doble", "Piso radiante", "Triple vidrio", "Vestidor suite", "Terraza panoramica", "Bodega"], "price_notes": "Precio llave en mano con diseno arquitectonico."},
    {"name": "Modulo Home Office", "slug": "modulo-office", "category": "modulo", "price": 12000, "short_desc": "Modulo 15m2 - Tu oficina en el jardin", "description": "Modulo prefabricado 15m2 para home office. Listo en 15 dias. Aislacion acustica profesional.", "specs": {"area_m2": 15, "material": "Pino+OSB", "dias": 15, "garantia": 3}, "features": ["Aislacion acustica", "Aire acondicionado split", "Iluminacion LED", "Enchufes USB", "Fibra optica ready", "Ventana panoramica"], "price_notes": "Transporte e instalacion incluidos en Montevideo y Canelones."},
    {"name": "Pergola Deck Premium", "slug": "pergola-deck", "category": "complemento", "price": 4500, "short_desc": "Pergola + deck 4x4m", "description": "Pergola con deck de madera tratada, complemento ideal para cualquier casa. Medidas personalizables.", "specs": {"area_m2": 16, "material": "Pino CCA", "dias": 5, "garantia": 3}, "features": ["Policarbonato o tela", "Iluminacion opcional", "Medidas a pedido"], "price_notes": "Precio base 4x4m. Custom a presupuesto."},
]

KB_PERMANENT = [
    ("faq", "Garantia y mantenimiento", "Ofrecemos 5 anios de garantia en estructura y 2 en terminaciones. Casa Premium Cedro tiene 10 anios de garantia. La madera tratada CCA tiene garantia contra termitas, hongos e insectos. Recomendamos aplicar protector cada 2 anios en exteriores."),
    ("faq", "Financiacion", "Financiacion propia: 30% de entrega y hasta 24 cuotas en pesos sin interes. Creditos hipotecarios BHU y BROU. Tiny House y Modulo: hasta 12 cuotas con tarjeta Visa/Master."),
    ("faq", "Proceso de construccion", "1) Consulta y presupuesto gratis, 2) Diseno personalizado (1-2 semanas), 3) Firma + 30% anticipo, 4) Produccion en taller, 5) Transporte e instalacion, 6) Entrega con garantia. Tiempos: Tiny 30d, Cabana 45d, Familiar 90d, Premium 150d."),
    ("faq", "Terreno y cimientos", "No vendemos terrenos pero asesoramos. Cimientos: pilotes para pendiente, platea para plano. Incluidos en Casa Familiar y Premium. Tiny/Cabana: aparte (USD 2.000-4.000 segun terreno)."),
    ("faq", "Showroom y contacto", "Showroom y taller: Ruta 5 km 28, Canelones (30 min de Montevideo). Lun-Vie 9-18h, Sab 9-13h. 3 modelos construidos. Sin cita previa. Reuniones virtuales por Zoom/Meet. WhatsApp: +598 99 000 001."),
    ("faq", "Tipos de madera", "Pino CCA: economico, tratado contra insectos, ideal para tiny y modulos. Eucalipto: madera dura uruguaya, excelente relacion precio-calidad. Cedro importado: premium, naturalmente resistente, aroma. Todo de bosques FSC."),
    ("faq", "Envio y cobertura", "Construimos en todo Uruguay. Transporte incluido hasta 100km de Canelones. Mas de 100km: USD 5/km extra. Experiencia en Rocha, Maldonado, Colonia, Salto, Paysandu, Treinta y Tres."),
    ("faq", "Personalizacion", "Todos los modelos son personalizables: distribuccion interna, colores, terminaciones, extras. El diseno personalizado esta incluido en Casa Familiar y Premium. Para Tiny y Cabana tiene un costo adicional de USD 500."),
    ("faq", "Post-venta", "Servicio post-venta incluido: revision a los 6 meses y al anio. Mantenimiento preventivo opcional (USD 200/anio). Reparaciones cubiertas por garantia sin costo."),
    ("manual", "Ventajas madera vs tradicional", "La construccion en madera es 40-60% mas rapida, mas sustentable, mejor aislante termico natural, y permite disenos flexibles. La madera tratada moderna dura tanto como el hormigon con mantenimiento adecuado."),
]

KB_PROMOS = [
    ("Promo Verano: 15% OFF Tiny+Cabana", "15% de descuento en Tiny House Natura y Cabana Weekend. Valido hasta fin de marzo 2026. No acumulable con otras promos.", "2026-03-31T23:59:59Z", ["whatsapp", "instagram", "web"]),
    ("48 cuotas sin interes marzo", "48 cuotas sin interes en Casa Familiar Roble durante marzo 2026. Solo con tarjeta Visa o Mastercard.", "2026-03-31T23:59:59Z", ["whatsapp", "web"]),
    ("Modulo Office: envio gratis abril", "Envio gratis del Modulo Home Office a cualquier punto de Uruguay durante abril 2026.", "2026-04-30T23:59:59Z", ["whatsapp", "instagram"]),
    ("Pergola gratis con Casa Premium", "Compra una Casa Premium Cedro y te regalamos una Pergola Deck Premium (valor USD 4.500). Valido hasta mayo 2026.", "2026-05-31T23:59:59Z", ["whatsapp", "instagram", "web"]),
]

KB_INSTAGRAM = [
    ("https://instagram.com/p/CDB001", "IG: Entrega Casa Roble La Paloma", "Entregamos Casa Familiar Roble en La Paloma, Rocha. 80m2, 3 dorm, vista al mar. Cliente #203 feliz! 85 dias de obra. #casasdemadera #lapaloma"),
    ("https://instagram.com/p/CDB002", "IG: Proceso construccion timelapse", "Asi construimos: desde el diseno hasta la entrega. Video completo del proceso de una Cabana Weekend. 45 dias en 60 segundos. #construccion #madera"),
    ("https://instagram.com/p/CDB003", "IG: Tiny House terminada Piriapolis", "Tiny House Natura recien entregada en Piriapolis. Perfecta para alquiler Airbnb. Ya tiene 5 reservas para la temporada! #tinyhouse #airbnb"),
    ("https://instagram.com/p/CDB004", "IG: Showroom abierto sabados", "Te esperamos en nuestro showroom! Ruta 5 km 28, Canelones. Sabados de 9 a 13h. Veni a conocer los modelos en vivo. #showroom #canelones"),
]

USERS = [
    {"email": "martin@casasdelbosque.uy", "name": "Martin Gonzalez", "role": "admin", "phone": "+59899000002"},
    {"email": "lucia@casasdelbosque.uy", "name": "Lucia Perez", "role": "seller", "phone": "+59899000003"},
    {"email": "diego@casasdelbosque.uy", "name": "Diego Fernandez", "role": "seller", "phone": "+59899000004"},
]

# 25 leads realistas con diferentes perfiles y etapas
LEADS = [
    # ── URGENTES (score 76-100) ──
    {"name": "Ana Gutierrez", "phone": "59899100001", "city": "Punta del Este", "stage": "visiting", "score": 95, "priority": "urgent", "budget": "100k-150k", "timeline": "inmediato", "needs": "Casa premium 4 dorm con garage. Terreno 2000m2 en Punta del Este. Quiere agendar visita sabado.", "msgs": [
        ("in", "Hola! Buscamos casa definitiva, 4 dormitorios minimo, premium. Terreno en Punta del Este."),
        ("ai", "Hola Ana! La Casa Premium Cedro seria perfecta: 120m2, 4 dorm, garage doble, terminaciones de lujo. $120.000 USD llave en mano."),
        ("in", "Me encanta! Puedo ir al showroom este sabado?"),
        ("ai", "Claro! Estamos en Ruta 5 km 28, Canelones. Sabado de 9 a 13h. Te esperamos!"),
        ("in", "Perfecto, vamos con mi esposo a las 10h. Tienen financiacion?"),
        ("ai", "Si! 30% de entrega y hasta 24 cuotas sin interes. Ademas con la Casa Premium te regalamos una Pergola Deck. Los esperamos!"),
    ]},
    {"name": "Roberto Silva", "phone": "59899100002", "city": "Montevideo", "stage": "negotiating", "score": 88, "priority": "urgent", "budget": "60k-80k", "timeline": "inmediato", "needs": "Casa familiar 3 dorm. Ya tiene terreno en Canelones. Presupuesto definido. Quiere cerrar esta semana.", "msgs": [
        ("in", "Buen dia. Necesito casa de 3 dormitorios para mi familia. Tengo terreno en Las Piedras."),
        ("ai", "Hola Roberto! La Casa Familiar Roble tiene 80m2, 3 dormitorios, y $65.000 USD. Incluye todo excepto terreno."),
        ("in", "El precio me sirve. Cuanto de anticipo y cuando arrancan?"),
        ("ai", "30% de anticipo ($19.500) y arrancamos en 1-2 semanas. 90 dias de obra. Financiamos el 70% restante."),
        ("in", "Quiero avanzar. Puedo pasar manana a firmar?"),
    ]},

    # ── ALTOS (score 51-75) ──
    {"name": "Diego Alvarez", "phone": "59899100003", "city": "Montevideo", "stage": "qualified", "score": 70, "priority": "high", "budget": "10k-15k", "timeline": "1_mes", "needs": "Modulo home office urgente. Trabaja remoto. Jardin en Pocitos.", "msgs": [
        ("in", "Necesito modulo oficina para mi jardin ya! Trabajo remoto."),
        ("ai", "El Modulo Home Office sale $12.000 USD y esta listo en 15 dias. Transporte incluido en Montevideo."),
        ("in", "Genial! Me sirve. Que necesito del terreno?"),
        ("ai", "Solo que este nivelado. Nuestro equipo instala todo. Jardin de 10x15m alcanza perfecto."),
    ]},
    {"name": "Carolina Mendez", "phone": "59899100004", "city": "Maldonado", "stage": "interested", "score": 62, "priority": "high", "budget": "25k-35k", "timeline": "3_meses", "needs": "Cabana para alquiler turistico en Jose Ignacio. Interesa promo verano.", "msgs": [
        ("in", "Vi la promo del 15% en Instagram. Me interesa la cabana para alquilar."),
        ("ai", "Hola Carolina! La Cabana Weekend sale $32.000 pero con la promo queda en $27.200. 40m2 con altillo, perfecta para Airbnb."),
        ("in", "Cuanto salen los cimientos para terreno con pendiente en Jose Ignacio?"),
        ("ai", "Para terreno con pendiente usamos pilotes, costo aprox USD 3.500. Te hacemos presupuesto exacto si nos mandas ubicacion."),
    ]},
    {"name": "Fernando Lopez", "phone": "59899100005", "city": "Canelones", "stage": "interested", "score": 55, "priority": "high", "budget": "15k-20k", "timeline": "1_mes", "needs": "Tiny house para hijo universitario. Terreno familiar.", "msgs": [
        ("in", "Quiero una tiny house para mi hijo que va a empezar la facultad. Tenemos terreno en la casa."),
        ("ai", "La Tiny House Natura es ideal: 25m2 con cocina y bano. $18.500 USD, lista en 30 dias."),
        ("in", "Puede tener escritorio para estudiar? Y cuanto sale con la promo?"),
    ]},

    # ── MEDIOS (score 26-50) ──
    {"name": "Carlos Rodriguez", "phone": "59899100006", "city": "Rocha", "stage": "interested", "score": 45, "priority": "medium", "budget": "15k-20k", "timeline": "3_meses", "needs": "Tiny house Airbnb en La Paloma. Pregunto por promo y envio.", "msgs": [
        ("in", "Quiero poner tiny house en La Paloma para Airbnb. Cuanto sale y envio?"),
        ("ai", "La Tiny House Natura: $18.500 (con promo 15%: $15.725). Envio La Paloma: +$600 (120km extra). Lista en 30 dias."),
        ("in", "Los cimientos estan incluidos?"),
    ]},
    {"name": "Patricia Suarez", "phone": "59899100007", "city": "Colonia", "stage": "new", "score": 35, "priority": "medium", "budget": None, "timeline": "6_meses", "needs": "Interesada en casa familiar pero sin apuro. Quiere ver opciones.", "msgs": [
        ("in", "Hola, estamos pensando en construir una casa de madera en Colonia. Que opciones tienen?"),
        ("ai", "Hola Patricia! Tenemos desde Tiny House ($18.500) hasta Casa Premium ($120.000). Para familia, la Casa Roble de 80m2 a $65.000 es la mas popular."),
    ]},
    {"name": "Marcelo Diaz", "phone": "59899100008", "city": "Montevideo", "stage": "new", "score": 30, "priority": "medium", "budget": "30k-40k", "timeline": "3_meses", "needs": "Quiere cabana para fin de semana. Comparando con otras empresas.", "msgs": [
        ("in", "Estoy viendo opciones de cabanas. Cuanto salen las de ustedes?"),
        ("ai", "Nuestra Cabana Weekend: $32.000, 40m2, altillo, estufa a lena, deck. Con la promo: $27.200 hasta fin de marzo."),
    ]},
    {"name": "Sofia Fernandez", "phone": "59899100009", "city": "Canelones", "stage": "interested", "score": 40, "priority": "medium", "budget": "60k-80k", "timeline": "explorando", "needs": "Familia de 4, terreno en Canelones 800m2. Pidio precios.", "msgs": [
        ("in", "Busco casa para 4 personas. Terreno en Canelones."),
        ("ai", "La Casa Roble (80m2, 3 dorm, $65.000) o la Premium Cedro (120m2, 4 dorm, $120.000). Ambas con cimientos incluidos."),
        ("in", "La Roble me gusta. Cuanto es el anticipo?"),
    ]},
    {"name": "Gustavo Morales", "phone": "59899100010", "city": "Salto", "stage": "new", "score": 25, "priority": "medium", "budget": None, "timeline": None, "needs": "Consulta desde Salto. Pregunto si llegan tan lejos.", "msgs": [
        ("in", "Hola, estoy en Salto. Construyen alla?"),
        ("ai", "Si! Construimos en todo Uruguay. Salto tiene costo extra de envio: aprox USD 2.000 (400km). Hemos construido en Salto, Paysandu y Treinta y Tres."),
    ]},

    # ── BAJOS (score 0-25) ──
    {"name": "Laura Martinez", "phone": "59899100011", "city": None, "stage": "new", "score": 0, "priority": "low", "budget": None, "timeline": None, "needs": "Solo curiosidad desde Instagram.", "msgs": [
        ("in", "Hola, vi fotos en Instagram. Que lindas casas! Que tipos hacen?"),
        ("ai", "Gracias Laura! Hacemos desde Tiny House (25m2) hasta casas premium (120m2). Tambien cabanas y modulos oficina."),
    ]},
    {"name": "Alejandra Ruiz", "phone": "59899100012", "city": "Montevideo", "stage": "new", "score": 10, "priority": "low", "budget": None, "timeline": "explorando", "needs": "Pregunto por pergola para su casa actual.", "msgs": [
        ("in", "Tienen pergolas? Cuanto salen?"),
        ("ai", "Si! Pergola Deck Premium desde $4.500 USD (4x4m). Medidas personalizables. Madera tratada CCA con garantia."),
    ]},
    {"name": "Ricardo Pereira", "phone": "59899100013", "city": "Paysandu", "stage": "new", "score": 15, "priority": "low", "budget": "15k-25k", "timeline": "6_meses", "needs": "Quiere tiny para terreno de campo.", "msgs": [
        ("in", "Buenas, necesito una casita para mi campo en Paysandu. Algo chico y resistente."),
        ("ai", "La Tiny House Natura (25m2, $18.500) o la Cabana Weekend (40m2, $32.000) son ideales para campo. Madera tratada anti-insectos."),
    ]},
    {"name": "Valentina Gomez", "phone": "59899100014", "city": None, "stage": "new", "score": 5, "priority": "low", "budget": None, "timeline": None, "needs": "Pregunto horario del showroom.", "msgs": [
        ("in", "Cual es el horario del showroom?"),
        ("ai", "Ruta 5 km 28, Canelones. Lun-Vie 9-18h, Sabados 9-13h. Sin cita previa. Te esperamos!"),
    ]},
    {"name": "Jorge Acosta", "phone": "59899100015", "city": "Montevideo", "stage": "new", "score": 20, "priority": "low", "budget": "8k-15k", "timeline": "3_meses", "needs": "Quiere modulo oficina pero comparando precios.", "msgs": [
        ("in", "Cuanto sale un modulo oficina? Estoy comparando opciones."),
        ("ai", "Nuestro Modulo Home Office: $12.000 USD, 15m2, listo en 15 dias. Incluye aire, aislacion acustica, LED. Envio gratis en Montevideo."),
    ]},

    # ── GANADOS ──
    {"name": "Andres Barrios", "phone": "59899100016", "city": "Canelones", "stage": "won", "score": 100, "priority": "urgent", "budget": "65k", "timeline": "inmediato", "needs": "Compro Casa Familiar Roble. Obra en curso.", "msgs": [
        ("in", "Hola, soy Andres. Firme contrato la semana pasada. Cuando arrancan la obra?"),
        ("ai", "Hola Andres! Tu Casa Familiar Roble esta en produccion. Inicio de instalacion estimado: 15 de abril. Te mantenemos informado!"),
    ]},
    {"name": "Mariela Castro", "phone": "59899100017", "city": "Maldonado", "stage": "won", "score": 98, "priority": "urgent", "budget": "18.5k", "timeline": "inmediato", "needs": "Compro Tiny House para Airbnb. Entrega en abril.", "msgs": [
        ("in", "Mariela aca. Confirmo que la tiny quedo preciosa en las fotos! Cuando la entregan?"),
        ("ai", "Hola Mariela! Tu Tiny House Natura esta casi lista. Entrega programada: 5 de abril en tu terreno en Maldonado."),
    ]},

    # ── PERDIDOS ──
    {"name": "Eduardo Vega", "phone": "59899100018", "city": "Montevideo", "stage": "lost", "score": 30, "priority": "low", "budget": "40k-50k", "timeline": None, "needs": "Pidio presupuesto pero eligio otra empresa.", "msgs": [
        ("in", "Al final fuimos con otra empresa. Gracias igual."),
        ("ai", "Entendemos Eduardo. Quedamos a las ordenes para cualquier consulta futura. Exitos con tu proyecto!"),
    ]},
    {"name": "Camila Torres", "phone": "59899100019", "city": "Canelones", "stage": "lost", "score": 15, "priority": "low", "budget": None, "timeline": None, "needs": "Presupuesto fuera de rango.", "msgs": [
        ("in", "Es muy caro para nosotros. No tenemos tanto presupuesto."),
        ("ai", "Entiendo Camila. Si en el futuro queres evaluar opciones, estamos a las ordenes. La Tiny House desde $18.500 es nuestra opcion mas accesible."),
    ]},

    # ── MAS LEADS EN DISTINTAS ETAPAS ──
    {"name": "Martin Oregui", "phone": "59899100020", "city": "Durazno", "stage": "interested", "score": 48, "priority": "medium", "budget": "30k-40k", "timeline": "3_meses", "needs": "Cabana para turismo rural en Durazno.", "msgs": [
        ("in", "Tengo un campo turistico en Durazno y quiero agregar una cabana."),
        ("ai", "La Cabana Weekend es ideal para turismo rural: $32.000, 40m2, estufa a lena. Con la promo: $27.200."),
        ("in", "Me interesa. Ustedes instalan en Durazno?"),
    ]},
    {"name": "Luciana Bentancor", "phone": "59899100021", "city": "Montevideo", "stage": "qualified", "score": 58, "priority": "high", "budget": "10k-15k", "timeline": "inmediato", "needs": "Modulo oficina + pergola para jardin grande.", "msgs": [
        ("in", "Quiero modulo oficina y tambien una pergola. Cuanto sale todo junto?"),
        ("ai", "Modulo Home Office $12.000 + Pergola Deck $4.500 = $16.500 total. Envio gratis en Montevideo. 15 dias el modulo, 5 la pergola."),
        ("in", "Me encanta. Puedo ir al showroom manana?"),
    ]},
    {"name": "Gonzalo Arocena", "phone": "59899100022", "city": "Punta del Este", "stage": "negotiating", "score": 72, "priority": "high", "budget": "100k-120k", "timeline": "3_meses", "needs": "Casa premium pero quiere negociar precio y personalizar diseno.", "msgs": [
        ("in", "Me interesa la Casa Premium pero $120k es mucho. Tienen algun descuento? Y puedo cambiar la distribucion?"),
        ("ai", "El diseno es 100% personalizable. Sobre el precio, con la promo actual te regalamos la Pergola Deck ($4.500 de regalo). Financiamos: 30% anticipo + 24 cuotas."),
        ("in", "Si agrego garage cerrado cuanto mas sale?"),
    ]},
    {"name": "Natalia Ribeiro", "phone": "59899100023", "city": None, "stage": "new", "score": 8, "priority": "low", "budget": None, "timeline": None, "needs": "Pregunto por Instagram, solo vio fotos.", "msgs": [
        ("in", "Que hermosas casas! Son de Uruguay? 😍"),
        ("ai", "Si! Somos de Canelones, Uruguay. Construimos casas de madera a medida. Te gustaria saber mas?"),
    ]},
    {"name": "Pablo Sanchez", "phone": "59899100024", "city": "Flores", "stage": "interested", "score": 38, "priority": "medium", "budget": "15k-20k", "timeline": "6_meses", "needs": "Quiere tiny house pero necesita mas informacion sobre el proceso.", "msgs": [
        ("in", "Me interesa la tiny house pero nunca construi nada. Como es el proceso?"),
        ("ai", "Es muy simple: 1) Elegis modelo, 2) Hacemos diseno, 3) Firmas + 30% anticipo, 4) Construimos en taller, 5) Instalamos en tu terreno. 30 dias total para la Tiny House."),
        ("in", "Y la madera aguanta el clima de aca? Lluvia, humedad?"),
    ]},
    {"name": "Elena Ferreira", "phone": "59899100025", "city": "Colonia", "stage": "closing", "score": 85, "priority": "urgent", "budget": "32k", "timeline": "inmediato", "needs": "Cabana Weekend casi cerrada. Falta firmar contrato esta semana.", "msgs": [
        ("in", "Confirmo que quiero la Cabana Weekend. Cuando puedo ir a firmar?"),
        ("ai", "Excelente Elena! Podes venir esta semana, Lun-Vie 9-18h. Traje: documento, comprobante de domicilio, y el 30% de anticipo ($9.600)."),
        ("in", "Perfecto, voy el miercoles a las 10h."),
        ("ai", "Te esperamos el miercoles a las 10! Cualquier duda antes, escribinos."),
    ]},
]


# ─────────────────────────────────────────
# SEED LOGIC
# ─────────────────────────────────────────

async def main():
    from sqlalchemy import text
    from app.database import async_session, engine
    from app.models import Company, Lead, Conversation, Message, Product, KnowledgeItem, User

    print("🗑️  Limpiando base de datos...")
    async with engine.begin() as conn:
        for table in ["messages", "conversations", "lead_stage_history", "leads",
                       "knowledge_items", "product_options", "products", "users", "companies"]:
            await conn.execute(text(f"DELETE FROM {table}"))

    async with async_session() as db:
        # 1. Company
        print("🏢 Creando empresa...")
        company = Company(**COMPANY)
        db.add(company)
        await db.flush()

        # 2. Products
        print(f"📦 Creando {len(PRODUCTS)} productos...")
        product_ids = {}
        for p in PRODUCTS:
            prod = Product(
                company_id=COMPANY_ID,
                name=p["name"], slug=p["slug"], category=p["category"],
                price=p["price"], price_currency="USD", price_notes=p.get("price_notes"),
                description=p.get("description"), short_desc=p["short_desc"],
                specs=p.get("specs"), features=p.get("features"),
                is_active=True, in_stock=True, display_order=PRODUCTS.index(p) + 1,
            )
            db.add(prod)
            await db.flush()
            product_ids[p["name"]] = prod.id

        # 3. Users
        print(f"👥 Creando {len(USERS)} usuarios...")
        from app.api.auth import _hash_password
        for u in USERS:
            user = User(
                company_id=COMPANY_ID,
                email=u["email"], name=u["name"], role=u["role"],
                password_hash=_hash_password("demo1234"),
                whatsapp_phone=u.get("phone"),
                is_active=True,
            )
            db.add(user)
        await db.flush()

        # 4. KB — Sync products + permanent + promos + instagram
        print("📚 Creando Knowledge Base...")
        from app.services.kb_manager import sync_all_products_to_kb
        await sync_all_products_to_kb(db, COMPANY_ID)

        for source, title, content in KB_PERMANENT:
            item = KnowledgeItem(
                company_id=COMPANY_ID, source=source, title=title, content=content,
                item_type="permanent", priority=3,
                channels=["whatsapp", "instagram", "web"],
                is_active=True, auto_generated=False, needs_review=False,
                times_used=random.randint(2, 30),
            )
            db.add(item)

        for title, content, expires, channels in KB_PROMOS:
            item = KnowledgeItem(
                company_id=COMPANY_ID, source="promo", title=title, content=content,
                item_type="temporal", priority=1,
                expires_at=datetime.fromisoformat(expires),
                channels=channels,
                is_active=True, auto_generated=False, needs_review=False,
                times_used=random.randint(0, 20),
            )
            db.add(item)

        for url, title, content in KB_INSTAGRAM:
            item = KnowledgeItem(
                company_id=COMPANY_ID, source="instagram", source_url=url,
                title=title, content=content,
                item_type="permanent", priority=6,
                channels=["instagram", "whatsapp"],
                is_active=True, auto_generated=True, needs_review=False,
                times_used=random.randint(0, 5),
            )
            db.add(item)

        await db.flush()

        # 5. Leads + Conversations + Messages
        print(f"👤 Creando {len(LEADS)} leads con conversaciones...")
        now = datetime.now(timezone.utc)

        for i, lead_data in enumerate(LEADS):
            # Randomize creation time (last 30 days)
            created_days_ago = random.randint(0, 30)
            created_at = now - timedelta(days=created_days_ago, hours=random.randint(0, 12))

            lead = Lead(
                company_id=COMPANY_ID,
                whatsapp_id=lead_data["phone"],
                whatsapp_phone=lead_data["phone"],
                name=lead_data["name"],
                city=lead_data.get("city"),
                score=lead_data["score"],
                stage=lead_data["stage"],
                priority=lead_data["priority"],
                budget_range=lead_data.get("budget"),
                timeline=lead_data.get("timeline"),
                needs_summary=lead_data.get("needs"),
                source_channel="whatsapp",
                tags=[],
                is_active=True,
                last_message_at=created_at + timedelta(hours=len(lead_data["msgs"])),
                last_response_at=created_at + timedelta(hours=len(lead_data["msgs"]) + 0.01),
            )
            db.add(lead)
            await db.flush()

            # Create conversation
            conv = Conversation(
                lead_id=lead.id, company_id=COMPANY_ID,
                channel="whatsapp", status="active" if lead_data["stage"] not in ("won", "lost") else "closed",
                ai_enabled=lead_data["stage"] not in ("won", "lost", "visiting", "negotiating"),
            )
            db.add(conv)
            await db.flush()

            # Create messages
            for j, (direction, content) in enumerate(lead_data["msgs"]):
                msg_time = created_at + timedelta(hours=j * 0.5)
                msg = Message(
                    conversation_id=conv.id,
                    direction="inbound" if direction == "in" else "outbound",
                    sender_type="lead" if direction == "in" else "ai",
                    msg_type="text",
                    content=content,
                    ai_model="llama-3.3-70b-versatile" if direction == "ai" else None,
                    ai_tokens_in=random.randint(1800, 2500) if direction == "ai" else None,
                    ai_tokens_out=random.randint(100, 200) if direction == "ai" else None,
                )
                db.add(msg)

            await db.flush()

        await db.commit()

    # Summary
    async with async_session() as db:
        from sqlalchemy import func, select
        products_count = (await db.execute(select(func.count(Product.id)))).scalar()
        leads_count = (await db.execute(select(func.count(Lead.id)))).scalar()
        convs_count = (await db.execute(select(func.count(Conversation.id)))).scalar()
        msgs_count = (await db.execute(select(func.count(Message.id)))).scalar()
        kb_count = (await db.execute(select(func.count(KnowledgeItem.id)))).scalar()
        users_count = (await db.execute(select(func.count(User.id)))).scalar()

    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║          🤖 DEMO SEED COMPLETADO                ║")
    print("╠══════════════════════════════════════════════════╣")
    print(f"║  🏢 Empresa:       Casas del Bosque              ║")
    print(f"║  📦 Productos:     {products_count:<3d}                            ║")
    print(f"║  📚 KB Items:      {kb_count:<3d}                            ║")
    print(f"║  👥 Usuarios:      {users_count:<3d}                            ║")
    print(f"║  👤 Leads:         {leads_count:<3d}                            ║")
    print(f"║  💬 Conversaciones:{convs_count:<3d}                            ║")
    print(f"║  📨 Mensajes:      {msgs_count:<3d}                            ║")
    print("╠══════════════════════════════════════════════════╣")
    print("║  Login:                                         ║")
    print("║    martin@casasdelbosque.uy / demo1234 (admin)  ║")
    print("║    lucia@casasdelbosque.uy / demo1234 (seller)  ║")
    print("║    diego@casasdelbosque.uy / demo1234 (seller)  ║")
    print("╚══════════════════════════════════════════════════╝")


if __name__ == "__main__":
    asyncio.run(main())
