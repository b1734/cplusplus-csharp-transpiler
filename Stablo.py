
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
        kod += self.name + "()"
        return kod


class AstFieldDeclaration:
    def __init__(self):
        self.type = None
        self.name = ""
        self.value = None
        self.array_size = "-1"


    def generate_code(self):
        kod = ""
        if self.array_size != "-1":
            kod += self.type + "[] " + self.name + " = new " + self.type + "[" + self.array_size + "]"
            return kod

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
        self.interface = False      # da li je potrebno izgenerisati interfejs za ovu klasu
        self.parent_classes = []        # za svaku baznu klasu generisemo objekat, metode i na kraju implicit operator
        self.allDeclarations = []       # u ovu listu cemo staviti i polja i metode, redom kojim se pojavljuju
        return

    def generate_inheritance(self):
        # za svaki parent izgenerisi objekat i posle izgenerisi potrebne metode
        for parent in self.parent_classes:
            if isinstance(parent, AstClass):
                if parent == self.parent_classes[0]:
                    continue

                object_name = parent.name + "Part"
                self.kod += "    public " + parent.name + " " + object_name + " = new " + parent.name + "();\n"

                for method in parent.allDeclarations:
                    if isinstance(method, AstMethodDeclaration):
                        if method.type is None:
                            continue
                        self.kod += "   " + " public void " + method.name + "()\n"
                        self.kod += "    {\n"
                        self.kod += "       " + object_name + "." + method.name + "();\n"
                        self.kod += "    }\n"
        return

    def generate_interface(self):
        interface_name = "I" + self.name        # IClassName
        self.kod += "interface " + interface_name + "\n"
        self.kod += "{\n"

        for method in self.allDeclarations:
            if isinstance(method, AstMethodDeclaration):
                if method.type is None:
                    # u pitanju je konstruktor koji preskacemo
                    continue

                self.kod += "    " + method.type + " " + method.name + "();\n"
                # svaki member interfejsa mora da bude public

        self.kod += "}\n"

    def generate_code(self):
        if self.interface:
            self.generate_interface()

        self.kod += "class " + self.name

        inherited_flag = False
        if self.interface:  # ukoliko je izgenerisan interfejs za ovu klasu, nasledi ga
            self.kod += " : I" + self.name
            inherited_flag = True

        if len(self.parent_classes) > 0:
            if inherited_flag:
                self.kod += ", "
            else:
                self.kod += " : "
            self.kod += self.parent_classes[0].name

            for parent in self.parent_classes:
                if isinstance(parent, AstClass):
                    if parent == self.parent_classes[0]:    # prvu klasu u listi nasledjujemo direktno
                        continue
                    parent_interface_name = "I" + parent.name
                    self.kod += ", " + parent_interface_name
            self.kod += "\n"

        else:
            # ako nema nasledjivanja, samo prelazimo u novi red
            self.kod += "\n"

        self.kod += "{\n"        # otvaramo zagradu za definiciju klase

        specifier = "private"  # dok ne naidjemo na izricitu deklaraciju access specifiera, onda je ta prom. priv.
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
                self.kod += "       Console.WriteLine(" + '"' + decl.name + '"' + ");\n"
                self.kod += "    }\n"
            else:
                # ako nije ni AstFieldDeclaration ni AstMethodDeclaration, onda je u pitanju promena access specifiera
                specifier = str(decl)

        self.generate_inheritance()

        self.kod += "}\n"        # zatvaramo zagradu za definiciju klase
        return self.kod
