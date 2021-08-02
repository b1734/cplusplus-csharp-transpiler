
# klase za AST
class AstDeclaration:
    def __init__(self):
        self.type = ""
        self.variable = ""
        self.value = ""
        self.array = False
        self.array_size = ""

    # generise ekvivalentan C# kod
    def generate_code(self):
        s = self.type
        if self.array: # ukoliko je definicija niza u pitanju, dodaj [] (kao int[])
            s += "[]"

        s += " " + self.variable

        if self.array:                                      # ako je dekl niza up pitanju, moramo da dodamo
            s += " = new int[" + self.array_size + "]"     # new int[size];

        if self.value != "":                                # ako je value true, to znaci da se dodeljuje neka vrednost
            if self.array:                                  # ako je niz u pitanju, ide drugacija sintaksa
                # zbog C# sintakse, niz ne mozemo inicijalizovati
                # u istoj liniji u kojoj ga deklarisemo
                # zato dodajemo novu liniju
                s += ";\n" + self.variable + " = " + self.value
            else:                                           # u suprotnom, u pitanju je obicna promenljiva
                s += " = "
                s += self.value
        s += ";"
        return s


# klasa za definiciju funkcija
class AstFunction:
    def __init__(self):
        self.type = ""
        self.name = ""

    def generate_code(self):
        return


class AstMethodDeclaration:
    def __init__(self):
        self.virtual = None         # ovo je za kasnije
        self.type = None        # ako type ostane none, u pitanju je konstruktor
        self.name = ""

    def generate_code(self):
        kod = ""
        if self.virtual is not None:
            pass
        elif self.type is not None:
            kod += self.type + " "
        kod += self.name        # zagrade su vec "uracunate" u self.name
        return kod


class AstFieldDeclaration:
    def __init__(self):
        self.type = None
        self.name = ""
        self.value = None

    def generate_code(self):
        kod = ""
        if self.type is not None:
            kod += self.type + " "
        kod += self.name

        if self.value is not None:
            kod += " = " + self.value
        return kod


# klasa za definiciju klasa
class AstClass:
    def __init__(self):
        self.kod = ""               # konacan kod koji ce biti izgenerisan
        self.name = ""
        self.parent_classes = []        # za svaku baznu klasu generisemo objekat, metode i na kraju implicit operator
        self.child_classes = []      # ovde stavljamo sve klase koje nasledjuju ovu trenutnu klasu
        self.allDeclarations = []       # u ovu listu cemo staviti i polja i metode, redom kojim se pojavljuju
        self.directInheritance = []     # klase koje direktno nasledjuju trenutnu klasu
        return

    def generate_children(self):
        # klasa sadrzi objekat deteta, kako bi mogli da izgenerisemo implicit operator i omogucimo eksplicitno type
        # castovanje iz bazne klase u nasledjenu
        for child in self.child_classes:
            if isinstance(child, AstClass):
                if child in self.directInheritance:     # za klase koje direktno nasledjujemo, ne treba generisati nista
                    continue

                object_name = child.name + "Part"
                object_decl = "public " + child.name + " " + object_name + ";"
                self.kod += "    " + object_decl + "\n"

                self.kod += "    " + "static public implicit operator " + child.name + "(" + self.name + " obj)\n"
                self.kod += "    {\n"
                self.kod += "    " + "    " + "return obj." + object_name + ";\n"
                self.kod += "    }\n"
        return

    def generate_inheritance(self):
        # posle deklaracija, treba da ugnjezdimo klase tako sto cemo za svaku klasu od koje trenutna klasa nasledjuje
        # (osim one koja se direktno nasledjuje) generisemo jedan objekat klase koja se nasledjuje, onda treba proci
        # kroz sve metode te klase i generisati ih i na kraju treba generisati static implicit operator

        for parent in self.parent_classes:
            if parent == self.parent_classes[0]:     # preskacemo prvu klasu u listi, jer smo nju vec direktno nalsedili
                continue

            if isinstance(parent, AstClass):
                object_name = parent.name + "Part"       # generisemo objekat
                object_decl = "public " + parent.name + " " + object_name + " = new " + parent.name + "();"
                self.kod += "    " + object_decl + "\n"

                for method in parent.allDeclarations:    # za svaku metodu, treba generisati kod koji ce pozvati tu metodu
                                                        # iz potrebne klase
                    if isinstance(method, AstMethodDeclaration):
                        if method.type is None:
                            continue            # preskoci constructor

                        self.kod += "    " + "void " + method.name + "\n"
                        self.kod += "    {\n"
                        self.kod += "    " + "    " + object_name + "." + method.name + ";\n"
                        self.kod += "    }\n"

                # na kraju, generisemo implicit operator
                self.kod += "    " + "static public implicit operator " + parent.name + "(" + self.name + " obj)\n"
                self.kod += "    {\n"
                self.kod += "    " + "    " + "return obj." + object_name + ";\n"
                self.kod += "    }\n"
        return

    def generate_constructor(self, specifier = "public"):
        # oke, koliko kapiram private constructor se koristi samo ako je cela klasa static, cime se ja sad ne bavim
        # a protected constructor sluzi za nesto drugo
        # uglavnom, mislim da je poprilicno sigurno da stavim svaki konstruktor kao public
        # TODO: namestanje specifiera!!

        self.kod += "    " + specifier + " " + self.name + "()\n"
        self.kod += "    {\n"
        # sada namestamo objekte
        for parent in self.parent_classes:
            if parent == self.parent_classes[0]: # prvu klasu nasledjujemo direktno
                continue
            self.kod += "    " + "    " + parent.name + "Part." + self.name + "Part = this;\n"

        self.kod += "    }\n"

    def generate_code(self):
        self.kod = "class " + self.name

        if len(self.parent_classes) > 0:
            # klasa direktno nasledjuje jednu klasu, ostale ugnjezdujemo
            self.kod += " : " + self.parent_classes[0].name + "\n"
        else:
            # ako nema nasledjivanja, samo prelazimo u novi red
            self.kod += "\n"

        self.kod += "{\n"        # otvaramo zagradu za definiciju klase

        specifier = "private"  # dok ne naidjemo na izricitu deklaraciju access specifiera, onda je ta prom. priv.
        if self.name == "Program":
            specifier = None

         # konstruktor generisemo posebno, jer ako imamo neki parent class moramo podesiti nejgove objekte
        generated_constructor = False
        if len(self.parent_classes) > 0:
            self.generate_constructor()
            generated_constructor = True

        for decl in self.allDeclarations:
            if isinstance(decl, AstFieldDeclaration):
                self.kod += "    " + specifier + " " + decl.generate_code() + ";\n"
            elif isinstance(decl, AstMethodDeclaration):
                if decl.name == (self.name + "()") and generated_constructor:
                    # preskacemo konstruktor, jer smo ga vec hendlovali
                    continue

                self.kod += "    "  # tabovanje
                if specifier is not None:
                    self.kod += specifier + " "      # ako nije u pitanju klasa Program, imamo neki access specifier
                self.kod += decl.generate_code() + "\n"
                self.kod += "    {\n"
                self.kod += "\n"
                self.kod += "    }\n"
            else:
                # ako nije ni AstFieldDeclaration ni AstMethodDeclaration, onda je u pitanju promena access specifiera
                specifier = str(decl)

        self.generate_inheritance()
        self.generate_children()

        self.kod += "}\n"        # zatvaramo zagradu za definiciju klase
        return self.kod
