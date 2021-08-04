
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
        self.override = False
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
        self.abstract = False       # da li je trenutna klasa apstraktna
        self.interface = False      # da li je potrebno izgenerisati interfejs za ovu klasu
        self.parent_classes = []        # za svaku baznu klasu generisemo objekat, metode i na kraju implicit operator
        self.allDeclarations = []       # u ovu listu cemo staviti i polja i metode, redom kojim se pojavljuju
        self.return_dictionary = {
            "int": "0",
            "char": 'a',
            "long": "0",
            "string": "str",
            "dobule": "3.14159",
            "float": "3.14159",
            "bool": "true"
        }
        return

    def check_if_overriden(self, method_name):     # helper funkcija za proveravanje da li je metoda overrajduvana
        for method in self.allDeclarations:
            if isinstance(method, AstMethodDeclaration):
                if method.name == method_name:
                    return True
        return False

    def check_virutal(self, method):
        if len(self.parent_classes) == 0:
            return
            # proveravamo sve metode klase koja je direktno nasledjena da proverimo da li je tr metoda deklarisana kao virtuelna
        parent = self.parent_classes[0]
        for parent_method in parent.allDeclarations:
            if isinstance(parent_method, AstMethodDeclaration):
                if parent_method.name == method.name and parent_method.virtual is not None:
                    method.override = True
            elif isinstance(parent_method, AstFieldDeclaration):
                # parser pure virtual metode vidi kao deklaraciju polja pa zato moramo proveriti i AstField objekte
                if parent_method.name == method.name and parent_method.abstract:
                    method.override = True

    def generate_inheritance(self):
        # za svaki parent izgenerisi objekat i posle izgenerisi potrebne metode
        for parent in self.parent_classes:
            if isinstance(parent, AstClass):
                if parent == self.parent_classes[0]:
                    continue
                if parent.abstract:
                    # apstraktne klase ne mogu definisati svoje objekte - tako da ne mozemo pozivati njene metode
                    # preko ugnjezdenog objekta (pretpostavka je da su sve metode vec overrajdovane)
                    continue

                necessary = False
                add_code = ""
                object_name = parent.name + "Part"
                add_code += "    public " + parent.name + " " + object_name + " = new " + parent.name + "();\n"

                for method in parent.allDeclarations:
                    if isinstance(method, AstMethodDeclaration):
                        if method.type is None:
                            continue
                        if self.check_if_overriden(method.name) and method.virtual:
                            # ako je ova metoda vec overrajdovana, preskoci je
                            continue
                        necessary = True
                        add_code += "   " + " public void " + method.name + "()\n"
                        add_code += "    {\n"
                        add_code += "       " + object_name + "." + method.name + "();\n"
                        add_code += "    }\n"
                if necessary:
                    self.kod += add_code
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
        if self.abstract:
            self.kod += "abstract "
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
                if self.interface:
                    specifier = "public"    # ako je tr klasa bazna nekoj drugoj klasi,sve metode moraju biti public

                self.check_virutal(decl)
                self.kod += decl.generate_code() + "\n"
                self.kod += "    {\n"
                self.kod += "       // method's body can be filled as you wish\n"
                self.kod += "       Console.WriteLine(" + '"' + decl.name + '"' + ");\n"
                if decl.name != "Main" and decl.type != "void":
                    self.kod += "       return " + self.return_dictionary[decl.type] + ";\n"
                self.kod += "    }\n"
            else:
                # ako nije ni AstFieldDeclaration ni AstMethodDeclaration, onda je u pitanju promena access specifiera
                specifier = str(decl)

        self.generate_inheritance()

        self.kod += "}\n"        # zatvaramo zagradu za definiciju klase
        return self.kod
