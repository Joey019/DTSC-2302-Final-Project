"""
subgenres.py - the sub-genre list used by genre_tags.py. Only used to EVALUATE clusters, never to build them.

87 sub-genres in 8 groups. Each sub-genre has a group and a pattern that is matched against Goodreads shelf
names (lowercase, words joined by "-", e.g. "historical-mystery", "cozy-culinary"). A pattern matches
whole words of the shelf name: "art" matches "art-theft" but not "start" or "smart".

Groups:
    place, era, sleuth, plot, cozy_theme   what a book is about: its setting and premise
    speculative, audience_form             e.g. sci-fi or paranormal; young adult, short stories
    tone                                   mood: dark, funny, fast-paced, ...
To add a sub-genre, add a line below; check which shelf names it matches before using it.
"""

import re

# word(s) -> pattern that only matches whole hyphen-separated words of a shelf name
def _words(alternatives: str) -> str:
    return r"(?:^|-)(?:" + alternatives + r")(?:-|$)"


SUBGENRES = {
    # ---- place ------------------------------------------------------------------------
    "british": ("place", _words(r"british|brit|britain|england|english-mystery|uk|united-kingdom|london|cornwall|yorkshire|oxford|cambridge|cotswolds|wales|welsh")),
    "scottish_irish": ("place", _words(r"scotland|scottish|edinburgh|glasgow|highlands|ireland|irish|dublin|celtic")),
    "nordic": ("place", _words(r"nordic|scandinavia|scandinavian|scandi|swedish|sweden|norway|norwegian|danish|denmark|iceland|icelandic|finnish|finland")),
    "french": ("place", _words(r"france|french|paris|provence")),
    "italian_mediterranean": ("place", _words(r"italy|italian|venice|rome|sicily|florence|spain|spanish|greece|greek-mystery|mediterranean|portugal")),
    "german_central_europe": ("place", _words(r"germany|german|berlin|austria|vienna|prague|czech|poland|polish|hungary|eastern-europe")),
    "russian": ("place", _words(r"russia|russian|soviet|ussr|moscow")),
    "asian": ("place", _words(r"asia|asian|japan|japanese|china|chinese|india|indian-mystery|korea|korean|thailand|vietnam|hong-kong|singapore")),
    "african_middle_east": ("place", _words(r"africa|african(?!-american)|botswana|egypt|nigeria|kenya|middle-east|israel|turkey|turkish|istanbul|iran|arab")),
    "latin_american": ("place", _words(r"latin-america|latin-american|(?<!new-)mexico|mexican|cuba|brazil|argentina|caribbean")),
    "australian_nz": ("place", _words(r"australia|australian|aussie|new-zealand|nz|outback")),
    "canadian": ("place", _words(r"canada|canadian|quebec|toronto|montreal")),
    "us_south": ("place", _words(r"southern|south|louisiana|new-orleans|texas|georgia|alabama|mississippi|tennessee|carolina|charleston|savannah|appalachia|appalachian|kentucky")),
    "us_west": ("place", _words(r"western|west|wild-west|cowboy|cowboys|montana|wyoming|colorado|arizona|new-mexico|nevada|navajo|native-american")),
    "california": ("place", _words(r"california|los-angeles|la|hollywood|san-francisco")),
    "new_york_northeast": ("place", _words(r"new-york|nyc|manhattan|boston|new-england|maine|vermont|massachusetts|new-jersey")),
    "florida": ("place", _words(r"florida|miami|key-west")),
    "small_town_rural": ("place", _words(r"small-town|small-towns|village|rural|countryside|farm|amish")),
    "island_sea": ("place", _words(r"nautical|sea|ocean|sailing|boats?|ships?|pirates?|navy|naval|island|islands|maritime|submarine")),
    "wilderness": ("place", _words(r"wilderness|national-parks?|outdoors|alaska|arctic|antarctica|survival|nature")),
    # ---- era --------------------------------------------------------------------------
    "ancient": ("era", _words(r"ancient|ancient-rome|roman(?!-noir|-policier|-polar|-noire)|rome-ancient|ancient-egypt|ancient-greece|egyptian|classical-world")),
    "medieval": ("era", _words(r"medieval|middle-ages|mediaeval|12th-century|13th-century|14th-century|15th-century|knights?|monks?")),
    "tudor_17th_century": ("era", _words(r"tudor|tudors|elizabethan|renaissance|16th-century|17th-century|1600s|restoration")),
    "georgian_regency": ("era", _words(r"regency|georgian|18th-century|1700s|colonial|revolutionary-war")),
    "victorian_edwardian": ("era", _words(r"victorian|edwardian|19th-century|1800s|gaslight|gaslamp|civil-war")),
    "interwar_golden_age": ("era", _words(r"1920s|1930s|20s|30s|roaring-twenties|jazz-age|interwar|golden-age|golden-age-mystery|flapper|prohibition")),
    "ww2": ("era", _words(r"ww2|wwii|world-war-ii|world-war-2|world-war-two|wwi|ww1|world-war-i|world-war|1940s|holocaust|nazis?|^war")),
    "cold_war_postwar": ("era", _words(r"cold-war|1950s|1960s|1970s|vietnam-war")),
    # ---- sleuth / profession ----------------------------------------------------------
    "police_procedural": ("sleuth", _words(r"police|procedural|police-procedural|police-procedurals|cops?|detective-inspector|homicide|policier|law-enforcement|police-detective")),
    "private_investigator": ("sleuth", _words(r"private-investigator|private-investigators|private-eye|private-detective|pi|p-i|gumshoe")),
    "amateur_sleuth": ("sleuth", _words(r"amateur-sleuth|amateur-sleuths|amateur-detective|female-sleuth|women-sleuths|woman-sleuth|sleuth|sleuths|female-detective")),
    "forensic": ("sleuth", _words(r"forensic|forensics|csi|medical-examiner|coroner|pathologist|forensic-anthropology|crime-scene")),
    "fbi_federal": ("sleuth", _words(r"fbi|federal-agents?|us-marshals?|profiler|profiling|behavioral-analysis")),
    "legal": ("sleuth", _words(r"legal|legal-thriller|legal-thrillers|lawyers?|attorneys?|courtroom|law(?!-enforcement)|legal-fiction")),
    "medical": ("sleuth", _words(r"medical|medical-thriller|medical-thrillers|doctors?|hospital|nurses?|medicine|pandemic|virus")),
    "journalist": ("sleuth", _words(r"journalists?|journalism|reporters?|newspaper")),
    "clergy_religious_sleuth": ("sleuth", _words(r"clergy|clerical|priests?|nuns?|vicar|rabbi|clerical-mystery")),
    "academic": ("sleuth", _words(r"academic|academia|campus|college|university|professors?|dark-academia|boarding-school")),
    # ---- plot / premise ---------------------------------------------------------------
    "serial_killer": ("plot", _words(r"serial-killers?|serial-killer-thriller|serial-murder")),
    "psychological": ("plot", _words(r"psychological|psychological-thrillers?|psychological-suspense|mind-games|unreliable-narrator|mental-illness|psychology")),
    "domestic": ("plot", _words(r"domestic|domestic-thrillers?|domestic-suspense|marriage|family-drama|family-secrets|motherhood")),
    "kidnapping_missing": ("plot", _words(r"kidnapping|kidnapped|abduction|missing-persons?|missing-children|mysteries-missing|disappearance")),
    "cold_case": ("plot", _words(r"cold-case|cold-cases|unsolved")),
    "heist_caper": ("plot", _words(r"heist|heists|caper|capers|con-artists?|thief|thieves|burglar|robbery|art-theft|jewel-thief")),
    "organized_crime": ("plot", _words(r"mafia|mob|mobsters?|gangsters?|gangs?|organized-crime|organised-crime|cartel|drugs?|yakuza")),
    "espionage": ("plot", _words(r"espionage|spy|spies|spy-thrillers?|spy-fiction|cia|mi5|mi6|secret-agents?|intelligence")),
    "military_action": ("plot", _words(r"military|military-thrillers?|military-fiction|navy-seals?|special-forces|soldiers?|army|marines|mercenar(?:y|ies)|action-thrillers?")),
    "political_conspiracy": ("plot", _words(r"political|political-thrillers?|politics|conspiracy|conspiracies|terrorism|terrorists?|government|president|washington-dc")),
    "techno_thriller": ("plot", _words(r"techno-thrillers?|technothrillers?|techno|cyber|cyberpunk|hackers?|hacking|computers?|technology")),
    "archaeology_treasure": ("plot", _words(r"archaeology|archeology|archaeological|treasure|treasure-hunt|artifacts?|relics?|ancient-mysteries|lost-cities")),
    "locked_room_puzzle": ("plot", _words(r"locked-room|locked-room-mystery|impossible-crime|puzzles?|whodunn?its?|clue|fair-play|country-house")),
    "noir_hardboiled": ("plot", _words(r"noir|hard-?boiled|hardboiled|pulp|crime-noir|neo-noir|tart-noir|pulp-fiction")),
    "true_crime": ("plot", _words(r"true-crime|true-story|true-crimes|based-on-true-story|real-crime")),
    "revenge_vigilante": ("plot", _words(r"revenge|vigilantes?|vigilante-justice|assassins?|hitm[ae]n|hit-man")),
    # ---- cozy theme -------------------------------------------------------------------
    "culinary": ("cozy_theme", _words(r"culinary|culinary-mystery|culinary-cozy|food|foodie|cooking|cook|recipes?|baking|bakery|bakers?|cupcakes?|cookies?|coffee|tea|tea-shop|cafe|chocolate|restaurant|chefs?|catering|wine|pie|donuts?")),
    "crafts_hobbies": ("cozy_theme", _words(r"crafts?|crafting|crafty|knitting|knit|quilting|quilts?|sewing|needlework|needlecraft|embroidery|scrapbooking|yarn|beads?|antiques?|vintage-shop|thrift")),
    "animals_pets": ("cozy_theme", _words(r"cats?|cat-mysteries|cat-mystery|kitty|kittens?|dogs?|dog-mysteries|pets?|animals?|horses?|equestrian|birds?|birding|vets?|veterinarian")),
    "books_bookshop": ("cozy_theme", _words(r"(?<!used-)bookstores?|bookshops?|library-mystery|librarians?|books-about-books|bibliomystery|bookish|authors-as-characters")),
    "garden_herbs": ("cozy_theme", _words(r"garden|gardening|gardens|herbs?|flowers?|florist|plants")),
    "holiday": ("cozy_theme", _words(r"christmas|holiday|holidays|halloween|thanksgiving|easter|valentine|xmas|winter-holiday")),
    "arts_theatre_music": ("cozy_theme", _words(r"(?<!sequential-)art|artists?|painting|museums?|theatre|theater|actors?|actresses|music|musicians?|bands?|singers?|dance|opera|movies|film")),
    "sports": ("cozy_theme", _words(r"sports?|baseball|football|golf|horse-racing|racing|boxing|hockey|soccer|fishing")),
    "wedding_fashion_beauty": ("cozy_theme", _words(r"weddings?|bridal|fashion|beauty|salon|jewelry")),
    # ---- speculative ------------------------------------------------------------------
    "ghosts_haunted": ("speculative", _words(r"ghosts?|ghost-stories|haunted|haunting|haunted-house|spirits|ghost-mystery")),
    "witches_magic": ("speculative", _words(r"witch|witches|witchcraft|magic|magical|wizards?|spells|wiccan?|sorcery|magical-realism")),
    "vampires_shifters": ("speculative", _words(r"vampires?|werewolf|werewolves|shifters?|shape-?shifters?|demons?|angels?|fae|faeries?|fairies")),
    "psychic": ("speculative", _words(r"psychics?|psychic-abilities|clairvoyant|telepathy|precognition|paranormal-abilities")),
    "horror": ("speculative", _words(r"horror|horror-thriller|scary|creepy|terror|monsters?|zombies?|occult|gothic-horror|stephen-king")),
    "gothic": ("speculative", _words(r"gothic|gothic-fiction|gothic-romance|gothic-mystery")),
    "science_fiction": ("speculative", _words(r"sci-fi|scifi|science-fiction|sf|space|aliens?|dystopian?|dystopia|post-apocalyptic|apocalyptic|futuristic|cloning")),
    "fantasy": ("speculative", _words(r"fantasy|urban-fantasy|high-fantasy|epic-fantasy|fantasy-mystery|dragons?|fairy-tales?|mythology|myths?")),
    "time_travel_alt_history": ("speculative", _words(r"time-travel|alternate-history|alternative-history|alt-history|steampunk|time-slip")),
    # ---- audience / form --------------------------------------------------------------
    "young_adult": ("audience_form", _words(r"young-adult|ya|ya-fiction|ya-mystery|ya-thriller|teen|teens|teen-fiction|young-adult-fiction|new-adult|na")),
    "children_middle_grade": ("audience_form", _words(r"middle-grade|mg|childrens?|children-s|children-s-books|childrens-books|kids|kids-books|juvenile|juvenile-fiction|chapter-books?|picture-books?")),
    "romantic_suspense": ("audience_form", _words(r"romantic-suspense|romance-suspense|suspense-romance|romance|romantic|love|love-story|contemporary-romance|paranormal-romance|historical-romance|erotica|erotic|steamy")),
    "lgbtq": ("audience_form", _words(r"lgbt|lgbtq|lgbtqia|glbt|gay|lesbian|queer|m-m|mm|m-m-romance|mm-romance|f-f|ff|bisexual|trans")),
    "christian_inspirational": ("audience_form", _words(r"christian|christian-fiction|christian-mystery|inspirational|clean-romance|faith|amish-fiction")),
    "classics": ("audience_form", _words(r"classics?|classic-mystery|classic-crime|classic-literature|vintage-mystery|vintage-crime|golden-age-detective")),
    "literary": ("audience_form", _words(r"literary|literary-fiction|literature|literary-thriller|literary-mystery")),
    "short_stories_anthology": ("audience_form", _words(r"short-stories|short-story|anthology|anthologies|collection|collections|novellas?|short-fiction|stories")),
    "graphic_novel": ("audience_form", _words(r"graphic-novels?|comics?|manga|comic-books?")),
    "translated": ("audience_form", _words(r"translated|translation|in-translation|translated-fiction|world-literature|international")),
    "sherlockian_pastiche": ("audience_form", _words(r"sherlock|sherlock-holmes|sherlockiana|sherlockian|holmes|pastiche|holmesian")),
    # ---- tone -------------------------------------------------------------------------
    "cozy": ("tone", _words(r"cozy|cozies|cosy|cosies|cozy-mystery|cozy-mysteries|cozy-mysery|cosy-mystery|cosy-mysteries|cozy-mystery-series|light-mystery")),
    "humor": ("tone", _words(r"humou?r|humorous|funny|comedy|comedic|humor-mystery|laugh-out-loud|chick-lit|satire")),
    "dark_violent": ("tone", _words(r"dark|disturbing|gritty|grim|violence|violent|gore|gory|brutal|abuse|torture")),
    "fast_paced_action": ("tone", _words(r"action|action-adventure|adventure|adventures|fast-paced|page-turners?|edge-of-your-seat|thrill-ride")),
}

GROUPS = sorted({group for group, _ in SUBGENRES.values()})
_COMPILED = {name: re.compile(pattern) for name, (group, pattern) in SUBGENRES.items()}


def match_shelf(shelf_name: str) -> list[str]:
    """All sub-genres whose pattern matches this shelf name."""
    name = shelf_name.lower()
    return [genre for genre, pattern in _COMPILED.items() if pattern.search(name)]
