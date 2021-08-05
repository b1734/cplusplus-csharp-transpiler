
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
        self.virtual = None         # da li je virtuelna funkcija u pitanju
        self.override = False        # da li je ova funkcija override neke virutelne
        self.specifier = None
        self.type = None        # ako type ostane none, u pitanju je konstruktor
        self.name = ""

    def generate_code(self):
        kod = ""
        if self.virtual is not None:
            kod += self.virtual + " "

        if self.override:
            kod += "override "

        if self.type is not None:
            kod += self.type + " "
        kod += self.name + "()"
        return kod


class AstFieldDeclaration:
    def __init__(self):
        self.abstract = False
        self.type = None
        self.name = ""
        self.value = None
        self.array_size = "-1"


    def generate_code(self):
        kod = ""
        if self.array_size != "-1":
            kod += self.type + "[] " + self.name + " = new " + self.type + "[" + self.array_size + "]"
            return kod

        # ako je u pitanju definicija pure virtual metode, parser je zapravo vidi kao polje - zato imamo ovo self.abstract
        # koje nam kaze da izgenerisemo apstraktnu metodu u c#
        if self.abstract:
            kod += "abstract " + self.type + " " + self.name + "()"
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
        self.abstract = False
        self.parent_classes = []        # za svaku baznu klasu generisemo objekat, metode i na kraju implicit operator
        self.child_classes = []      # ovde stavljamo sve klase koje nasledjuju ovu trenutnu klasu
        self.allDeclarations = []       # u ovu listu cemo staviti i polja i metode, redom kojim se pojavljuju
        self.directInheritance = []     # klase koje direktno nasledjuju trenutnu klasu
        self.return_dictionary = {
            "int": "0",
            "char": "'a'",
            "long": "0",
            "string": "str",
            "double": "3.14159",
            "float": "3.14159",
            "bool": "true"
        }
        return

    def check_if_overriden(self, method_name):
        # helper funkcija za proveravanje da li je metoda overrajduvana, prilikom prosledjivanja poziva
        for method in self.allDeclarations:
            if isinstance(method, AstMethodDeclaration):
                if method.name == method_name:
                    return True

        return False

    def check_virutal(self, method, direct):
        if len(self.parent_classes) == 0:
            return
        # proveravamo sve metode klase koja je direktno nasledjena da proverimo da li je tr metoda deklarisana kao virtuelna
        # kako bi znali da li da joj dopisemo override
        parent = direct
        for parent_method in parent.allDeclarations:
            if isinstance(parent_method, AstMethodDeclaration):
                if parent_method.name == method.name and parent_method.virtual is not None:
                    method.override = True
            elif isinstance(parent_method, AstFieldDeclaration):
                # parser pure virtual metode vidi kao deklaraciju polja pa zato moramo proveriti i AstField objekte
                if parent_method.name == method.name and parent_method.abstract:
                    method.override = True

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

    def generate_inheritance(self, direct_name):
        # posle deklaracija, treba da ugnjezdimo klase tako sto cemo za svaku klasu od koje trenutna klasa nasledjuje
        # (osim one koja se direktno nasledjuje) generisemo jedan objekat klase koja se nasledjuje, onda treba proci
        # kroz sve metode te klase i generisati ih i na kraju treba generisati static implicit operator

        for parent in self.parent_classes:

            mode = self.parent_classes[0]
            if isinstance(parent, AstClass):
                if parent.name == direct_name:     # preskacemo klasu koju smo direknto nasledili
                    continue
                if len(self.child_classes) > 0:
                    mode = "public"    # ukoliko je trenunta klasa baza nekoj klasi, sve njene metode moraju biti public
                necessary = False
                add_code = ""
                object_name = parent.name + "Part"       # generisemo objekat koji sigurno dodajemo
                self.kod += "    " + mode + " " + parent.name + " " + object_name + " = new " + parent.name + "();\n"

                for method in parent.allDeclarations:    # za svaku metodu, treba generisati kod koji ce pozvati tu metodu
                    # iz potrebne klase
                    if isinstance(method, AstMethodDeclaration):
                        if method.type is None:
                            continue            # preskoci constructor
                        if (self.check_if_overriden(method.name) and method.virtual) or method.specifier == "private":
                            # ako je ova metoda vec overrajdovana, preskoci je
                            continue
                        if mode == "public" and method.specifier == "protected":
                            mode = "protected"
                        necessary = True
                        add_code += "    " + mode + " void " + method.name + "()\n"
                        add_code += "    {\n"
                        add_code += "    " + "    " + object_name + "." + method.name + "();\n"
                        add_code += "    }\n"
                if necessary:
                    self.kod += add_code
                # na kraju, generisemo implicit operator
                self.kod += "    " + "static public implicit operator " + parent.name + "(" + self.name + " obj)\n"
                self.kod += "    {\n"
                self.kod += "    " + "    " + "return obj." + object_name + ";\n"
                self.kod += "    }\n"
            elif isinstance(parent, str):
                mode = parent
        return

    def generate_constructor(self, direct, specifier="public"):
        # oke, koliko kapiram private constructor se koristi samo ako je cela klasa static, cime se ja sad ne bavim
        # a protected constructor sluzi za nesto drugo
        # uglavnom, mislim da je poprilicno sigurno da stavim svaki konstruktor kao public

        self.kod += "    " + specifier + " " + self.name + "()\n"
        self.kod += "    {\n"
        # sada namestamo objekte
        for parent in self.parent_classes:
            if parent == direct: # prvu klasu nasledjujemo direktno
                continue
            if isinstance(parent, AstClass):
                self.kod += "    " + "    " + parent.name + "Part." + self.name + "Part = this;\n"

        self.kod += "    }\n"

    def generate_code(self):
        if self.abstract:
            self.kod += "abstract "
        self.kod += "class " + self.name

        direct = None
        if len(self.parent_classes) > 0:
            # klasa direktno nasledjuje jednu klasu, ostale ugnjezdujemo
            if isinstance(self.parent_classes[0], AstClass):
                direct = self.parent_classes[0]
            else:
                direct = self.parent_classes[1]
            for parent in self.parent_classes:
                if isinstance(parent, AstClass):
                    if parent.abstract:
                        direct = parent
            self.kod += " : " + direct.name + "\n"
        else:
            # ako nema nasledjivanja, samo prelazimo u novi red
            self.kod += "\n"

        self.kod += "{\n"        # otvaramo zagradu za definiciju klase

        specifier = "private"  # dok ne naidjemo na izricitu deklaraciju access specifiera, onda je ta prom. priv.
        if self.name == "Program":
            specifier = None

        # konstruktor generisemo posebno, jer ako imamo neki parent class moramo podesiti nejgove objekte
        generated_constructor = False
        # ako imamo samo jedan parent class, ne moramo da podesavamo constructor
        # vece od 2 iz razloga zato sto imamo jedan access specifier i jednu klasu
        if len(self.parent_classes) > 2:
            self.generate_constructor(direct)
            generated_constructor = True

        for decl in self.allDeclarations:
            if isinstance(decl, AstFieldDeclaration):
                self.kod += "    " + specifier + " " + decl.generate_code() + ";\n"
            elif isinstance(decl, AstMethodDeclaration):
                if decl.name == self.name and generated_constructor:
                    # preskacemo konstruktor, jer smo ga vec hendlovali
                    continue

                self.kod += "    "  # tabovanje
                if specifier is not None:
                    if len(self.child_classes) > 0:
                        specifier = "public"    # ako je tr klasa bazna nekoj drugoj klasi,sve metode moraju biti public
                    self.kod += specifier + " "      # ako nije u pitanju klasa Program, imamo neki access specifier
                    decl.specifier = specifier

                self.check_virutal(decl, direct)    # proveravamo, da li je trenutna metoda override
                self.kod += decl.generate_code() + "\n"
                self.kod += "    {\n"
                #    self.kod += "       // method's body can be filled as you wish\n"
                self.kod += "       Console.WriteLine(" + '"class ' + self.name + " - method " + decl.name + '"' + ");\n"
                if decl.name != "Main" and decl.type != "void" and decl.type is not None:
                    self.kod += "       return " + self.return_dictionary[decl.type] + ";\n"
                self.kod += "    }\n"
            else:
                # ako nije ni AstFieldDeclaration ni AstMethodDeclaration, onda je u pitanju promena access specifiera
                specifier = str(decl)

        self.generate_inheritance(direct.name if direct is not None else None)
        if not self.abstract:
            self.generate_children()

        self.kod += "}\n"        # zatvaramo zagradu za definiciju klase
        return self.kod
