import os

# --- Data Sources ---

RAPPERS_PL = [
    "Taco Hemingway", "Quebonafide", "Mata", "Bedoes", "Sokół", "Pezet", "O.S.T.R.", "Paluch", "Szpaku",
    "Kizo", "Żabson", "Young Igi", "Otsochodzi", "Białas", "Solar", "Guzior", "Sarius", "ReTo",
    "Kukon", "Sobel", "White 2115", "Jan-rapowanie", "Malik Montana", "Kaz Bałagane", "Tede", "Peja",
    "Liroy", "Kaliber 44", "Paktofonika", "Magik", "Fokus", "Rahim", "Grubson", "DonGURALesko",
    "KęKę", "Słoń", "Shellerini", "Włodi", "Pelson", "Vienio", "Łona", "Webber", "Ten Typ Mes",
    "Stasiak", "Pyskaty", "Ero", "Kosi", "Siwers", "Małpa", "Bisz", "B.R.O", "PlanBe", "Smolasty",
    "Szamz", "Młody G", "Belmondo", "Owi", "Major SPZ", "Bonus RPK", "Rogal DDL", "Kabe", "Oki",
    "Gedz", "Dwa Sławy", "Rado Radosny", "Astek", "Kartky", "Tymek", "Czesław", "VNM", "Zeus",
    "HuczuHucz", "Tau", "Medium", "Buka", "Rahim", "Fokus", "Joka", "Dab", "Abradab", "JWP", "BC",
    "Hemp Gru", "Wilku", "Bilon", "Molesta", "WWO", "ZIP Skład", "Mor W.A.", "Płomień 81", "Onar",
    "Pezet", "Noon", "Eis", "Dinal", "Smarki Smark", "Zkibwoy", "Flojd", "W.E.N.A.", "Rasmentalism",
    "Ras", "Ment", "Kuba Knap", "Emil Blef", "Afrojax", "Legendarny Afrojax", "Zdechły Osa", "Młody Dzban",
    "Zetha", "Chivas", "Fagata", "Young Leosia", "Bambi", "Modelki", "Oliwka Brazil", "Ruskiefajki"
]

RAPPERS_WORLD = [
    "Eminem", "Kanye West", "Ye", "Jay-Z", "Drake", "Kendrick Lamar", "J. Cole", "Travis Scott",
    "Future", "21 Savage", "Lil Wayne", "Nicki Minaj", "Cardi B", "Megan Thee Stallion", "Doja Cat",
    "Snoop Dogg", "Dr. Dre", "Tupac", "2Pac", "Notorious B.I.G.", "Biggie", "Nas", "50 Cent",
    "Ice Cube", "Rakim", "Wu-Tang Clan", "Method Man", "Redman", "Busta Rhymes", "DMX", "Ludacris",
    "T.I.", "Young Thug", "Gunna", "Lil Baby", "DaBaby", "Post Malone", "Mac Miller", "Tyler, the Creator",
    "ASAP Rocky", "Playboi Carti", "Lil Uzi Vert", "XXXTentacion", "Juice WRLD", "Pop Smoke",
    "Migos", "Quavo", "Offset", "Takeoff", "Rick Ross", "Meek Mill", "Wiz Khalifa", "Kid Cudi",
    "Chance the Rapper", "Childish Gambino", "Logic", "G-Eazy", "Machine Gun Kelly", "MGK",
    "Jack Harlow", "Central Cee", "Stormzy", "Skepta", "Dave", "Aitch", "ArrDee", "Headie One"
]

CELEBS_PL = [
    "Lewandowski", "Robert Lewandowski", "Anna Lewandowska", "Lewy", 
    "Adam Małysz", "Małysz", "Orzeł z Wisły", "Kamil Stoch", "Stoch", "Piotr Żyła", "Żyła",
    "Iga Świątek", "Świątek", "Hurkacz", "Radwańska", "Gołota", "Adamek", "Błachowicz", "Jędrzejczyk",
    "Pudzian", "Mariusz Pudzianowski", "Dominator",
    "Makłowicz", "Robert Makłowicz", "Gessler", "Magda Gessler", "Wojewódzki", "Kuba Wojewódzki",
    "Hołownia", "Tusk", "Morawiecki", "Kaczyński", "Duda", "Andrzej Duda", "Wałęsa", "Lech Wałęsa",
    "Papież", "Jan Paweł II", "Wojtyła", "Karol Wojtyła",
    "Doda", "Rabczewska", "Rodowicz", "Maryla Rodowicz", "Krawczyk", "Krzysztof Krawczyk",
    "Zenek", "Zenon Martyniuk", "Sławomir", "Akcent", "Bayer Full",
    "Linda", "Bogusław Linda", "Pazura", "Cezary Pazura", "Stuhr", "Jerzy Stuhr", "Maciej Stuhr",
    "Koterski", "Misiek Koterski", "Karolak", "Tomasz Karolak", "Szyc", "Borys Szyc",
    "Friz", "Wersow", "Ekipa", "Gimper", "Rezi", "Blowek", "Książulo", "Budda"
]

CELEBS_WORLD = [
    "Messi", "Leo Messi", "Ronaldo", "Cristiano Ronaldo", "CR7", "Neymar", "Mbappe", "Haaland",
    "Lewandowski", "Benzema", "Zlatan", "Ibrahimovic",
    "LeBron", "LeBron James", "Curry", "Steph Curry", "Jordan", "Michael Jordan", "Kobe", "Kobe Bryant",
    "Shaq", "Shaquille O'Neal", "Tyson", "Mike Tyson", "Ali", "Muhammad Ali", "McGregor", "Conor McGregor",
    "Elon Musk", "Musk", "Bezos", "Jeff Bezos", "Zuckerberg", "Mark Zuckerberg", "Gates", "Bill Gates",
    "Jobs", "Steve Jobs",
    "Trump", "Donald Trump", "Biden", "Joe Biden", "Obama", "Barack Obama", "Putin", "Zelensky",
    "Taylor Swift", "Swift", "Beyonce", "Rihanna", "Adele", "Shakira", "JLo", "Jennifer Lopez",
    "Madonna", "Britney", "Britney Spears", "Lady Gaga", "Miley Cyrus", "Ariana Grande", "Selena Gomez",
    "Justin Bieber", "Bieber", "Ed Sheeran", "Harry Styles", "The Weeknd", "Bruno Mars",
    "Brad Pitt", "Pitt", "DiCaprio", "Leo DiCaprio", "Tom Cruise", "Cruise", "Johnny Depp", "Depp",
    "The Rock", "Dwayne Johnson", "Will Smith", "Smith", "Keanu Reeves", "Reeves"
]

CITIES_PL = [
    "Warszawa", "WWA", "Stolica", "Kraków", "KRK", "Łódź", "Wrocław", "Wroclove", "Poznań", "Gdańsk",
    "Szczecin", "Bydgoszcz", "Lublin", "Białystok", "Katowice", "Gdynia", "Częstochowa", "Radom",
    "Sosnowiec", "Toruń", "Kielce", "Rzeszów", "Gliwice", "Zabrze", "Olsztyn", "Bielsko-Biała",
    "Bytom", "Zielona Góra", "Rybnik", "Ruda Śląska", "Opole", "Tychy", "Gorzów", "Elbląg",
    "Płock", "Wałbrzych", "Tarnów", "Chorzów", "Kalisz", "Koszalin", "Legnica", "Grudziądz",
    "Słupsk", "Jaworzno", "Jastrzębie-Zdrój", "Nowy Sącz", "Jelenia Góra", "Siedlce", "Konin",
    "Piotrków", "Lubin", "Inowrocław", "Mysłowice", "Piła", "Ostrowiec", "Ostrów", "Siemianowice",
    "Stargard", "Pabianice", "Gniezno", "Suwałki", "Głogów", "Chełm", "Przemyśl", "Zamość",
    "Tomaszów", "Stalowa Wola", "Ełk", "Łomża", "Mielec", "Leszno", "Żory", "Bełchatów",
    "Świdnica", "Będzin", "Biała Podlaska", "Tczew", "Piekary", "Racibórz", "Legionowo", "Ostrołęka",
    "Hel", "Sopot", "Zakopane", "Sandomierz", "Kazimierz", "Wieliczka", "Oświęcim", "Ciechocinek",
    "Ustka", "Międzyzdroje", "Kołobrzeg", "Władysławowo", "Chałupy", "Jurata", "Jastarnia"
]

CITIES_WORLD = [
    "Nowy Jork", "NYC", "New York", "Londyn", "London", "Paryż", "Paris", "Berlin", "Tokio", "Tokyo",
    "Moskwa", "Pekin", "Szanghaj", "Dubaj", "Dubai", "Los Angeles", "LA", "Chicago", "Miami",
    "Las Vegas", "Vegas", "San Francisco", "Waszyngton", "Toronto", "Meksyk", "Rio", "Rio de Janeiro",
    "Buenos Aires", "Madryt", "Barcelona", "Rzym", "Mediolan", "Wenecja", "Neapol", "Ateny",
    "Stambuł", "Kair", "Jerozolima", "Tel Awiw", "Bombaj", "Delhi", "Bangkok", "Singapur",
    "Sydney", "Melbourne", "Kijów", "Lwów", "Wilno", "Mińsk", "Praga", "Wiedeń", "Budapeszt",
    "Bukareszt", "Sofia", "Belgrad", "Zagrzeb", "Sztokholm", "Oslo", "Kopenhaga", "Helsinki",
    "Amsterdam", "Bruksela", "Zurich", "Genewa", "Lizbona", "Dublin", "Monako"
]

BRANDS = [
    "Nike", "Adidas", "Puma", "Reebok", "New Balance", "Vans", "Converse", "Jordan", "Yeezy",
    "Gucci", "Prada", "Louis Vuitton", "LV", "Versace", "Balenciaga", "Dior", "Chanel", "Burberry",
    "Fendi", "Armani", "Hugo Boss", "Tommy Hilfiger", "Ralph Lauren", "Calvin Klein", "CK",
    "Zara", "H&M", "Bershka", "Pull&Bear", "Reserved", "Cropp", "House", "Sinsay", "CCC", "Deichmann",
    "Apple", "iPhone", "MacBook", "iPad", "AirPods", "Samsung", "Galaxy", "Sony", "PlayStation", "PS5",
    "Xbox", "Nintendo", "Switch", "Tesla", "BMW", "Audi", "Mercedes", "Merc", "Porsche", "Ferrari",
    "Lambo", "Lamborghini", "Bugatti", "Bentley", "Rolls-Royce", "Rolls", "Toyota", "Honda", "Ford",
    "McDonald", "MCD", "KFC", "Burger King", "Pizza Hut", "Subway", "Starbucks", "Cola", "Coca-Cola",
    "Pepsi", "Red Bull", "Monster", "Żabka", "Biedronka", "Lidl", "Dino", "Orlen", "Lotos", "Shell"
]

# --- Simple Inflector ---

def inflect_polish_word(word):
    """
    Very basic heuristic inflector for Polish names/nouns.
    It won't be perfect, but it covers 80% of cases for generating rhyme-able variations.
    """
    forms = {word}
    base = word
    
    # Heuristics based on endings
    if word.endswith("a"):
        # Femine logic (Warszawa -> Warszawy, Warszawę...)
        root = word[:-1]
        forms.add(root + "y")   # Dopełniacz (nie ma Warszawy)
        forms.add(root + "ę")   # Biernik (widzę Warszawę)
        forms.add(root + "ą")   # Narzędnik (z Warszawą)
        forms.add(root + "ie")  # Miejscownik (o Warszawie) - soft mutation needed often
        forms.add(root + "o")   # Wołacz (o Warszawo!)
        
        # Soft mutations for Miejscownik (r->rz, l->l, k->c, g->dz)
        if root.endswith("r"): forms.add(root[:-1] + "rze") # Góra -> Górze
        if root.endswith("k"): forms.add(root[:-1] + "ce")  # Polska -> Polsce
        if root.endswith("g"): forms.add(root[:-1] + "dze") # Praga -> Pradze
        
    elif word.endswith("o"):
        # Neuter (Mleko -> Mleka...)
        root = word[:-1]
        forms.add(root + "a")   # Dopełniacz
        forms.add(root + "u")   # Celownik
        forms.add(root + "em")  # Narzędnik
        forms.add(root + "ie")  # Miejscownik
        
        if root.endswith("k"): forms.add(root + "u") # Oku -> Oku (exception, simpl)
        
    elif word.endswith("ek") and len(word) > 3:
        # Fleeting 'e' (Marek -> Marka)
        root = word[:-2] + "k"
        forms.add(root + "a")
        forms.add(root + "owi")
        forms.add(root + "iem")
        forms.add(root + "u")
        
    elif word[-1] in "bcdfghjklmnprstvwzżźśń":
        # Masculine consonant ending (Adam -> Adama)
        forms.add(word + "a")   # Dopełniacz
        forms.add(word + "owi") # Celownik
        forms.add(word + "em")  # Narzędnik
        forms.add(word + "ie")  # Miejscownik
        forms.add(word + "u")   # Wołacz/Miejscownik often
        
        # Soft mutations
        if word.endswith("r"): forms.add(word[:-1] + "rze") # Komputer -> Komputerze
        
    # Plural hints (simple)
    if word.endswith("a"):
        forms.add(word[:-1] + "y") # Dziewczyna -> Dziewczyny
    else:
        forms.add(word + "y")      # Stół -> Stoły (phonetic approx)
        forms.add(word + "i")      # Student -> Studenci (approx)
        forms.add(word + "owie")   # Pan -> Panowie

    return list(forms)

def generate():
    all_entities = []
    
    # Process all lists
    datasets = [
        (RAPPERS_PL, "rapper"),
        (RAPPERS_WORLD, "rapper"),
        (CELEBS_PL, "celeb"),
        (CELEBS_WORLD, "celeb"),
        (CITIES_PL, "city"),
        (CITIES_WORLD, "city"),
        (BRANDS, "brand")
    ]
    
    final_output = []
    
    for dataset, tag in datasets:
        for name in dataset:
            # Handle multi-word names: inflect usually just the last word if it looks inflectable, 
            # or treat as whole. For simplicity, we add the full name as is, 
            # and inflections of the last part if it's a Polish name.
            
            parts = name.split()
            variations = set()
            variations.add(name)
            
            # If multiple phrases, try to inflect last word (e.g. "Taco Hemingway" -> "Taco Hemingwaya")
            if len(parts) > 1:
                last = parts[-1]
                inflected_last = inflect_polish_word(last)
                for infl in inflected_last:
                    if infl != last:
                        new_name = " ".join(parts[:-1] + [infl])
                        variations.add(new_name)
            else:
                # Single word - full inflection
                inflections = inflect_polish_word(name)
                variations.update(inflections)
            
            # Clean up
            cleaned_vars = [v for v in variations if len(v) > 2]
            
            # Format: Name|Var1,Var2,Var3|tag
            line = f"{name}|{','.join(cleaned_vars)}|{tag}"
            final_output.append(line)

    with open(os.path.join("data", "entities.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(final_output))
        
    print(f"Generated {len(final_output)} unique entities with variations.")

if __name__ == "__main__":
    generate()
