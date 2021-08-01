
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
        self.parent_classes = []        # za svaku klasu generisemo objekat, metode i na kraju implicit operator
        self.allDeclarations = []       # u ovu listu cemo staviti i polja i metode, redom kojim se pojavljuju
        return

    def generate_inheritance(self):

        # posle deklaracija, treba da ugnjezdimo klase tako sto cemo za svaku klasu od koje trenutna klasa nasledjuje
        # (osim one koja se direktno nasledjuje) generisemo jedan objekat klase koja se nasledjuje, onda treba proci
        # kroz sve metode te klase i generisati ih i na kraju treba generisati static implicit operator

        for klasa in self.parent_classes:
            if klasa == self.parent_classes[0]:     # preskacemo prvu klasu u listi, jer smo nju vec direktno nalsedili
                continue

            if isinstance(klasa, AstClass):
                object_name = klasa.name + "Part"       # generisemo objekat
                object_decl = "public " + klasa.name + " " + object_name + " = new " + klasa.name + "();"
                self.kod += "    " + object_decl + "\n"

                for method in klasa.allDeclarations:    # za svaku metodu, treba generisati kod koji ce pozvati tu metodu
                                                        # iz potrebne klase
                    if isinstance(method, AstMethodDeclaration):
                        self.kod += "    " + "void " + method.name + "\n"
                        self.kod += "    {\n"
                        self.kod += "    " + "    " + object_name + "." + method.name + ";\n"
                        self.kod += "    }\n"

                # na kraju, generisemo implicit operator
                self.kod += "    " + "static implicit operator " + klasa.name + "(" + self.name + " obj)\n"
                self.kod += "    {\n"
                self.kod += "    " + "    " + "return obj." + object_name + ";\n"
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

        specifier = "private"       # dok ne naidjemo na izricitu deklaraciju access specifiera, onda je ta prom. priv.
        if self.name == "Program":
            specifier = None
        for decl in self.allDeclarations:
            if isinstance(decl, AstFieldDeclaration):
                self.kod += "    " + specifier + " " + decl.generate_code() + ";\n"
            elif isinstance(decl, AstMethodDeclaration):
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

        if len(self.parent_classes) > 0:
            self.generate_inheritance()

        self.kod += "}\n"        # zatvaramo zagradu za definiciju klase
        return self.kod
