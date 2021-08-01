
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
        self.type = ""
        self.name = ""
        self.value = None

    def generate_code(self):
        kod = ""
        kod += self.type + " " + self.name
        if self.value is not None:
            kod += " = " + self.value
        return kod


# klasa za definiciju klasa
class AstClass:
    def __init__(self):
        self.name = ""
        self.inheritance = None
        self.allDeclarations = []       # u ovu listu cemo staviti i polja i metode, redom kojim se pojavljuju
        return

    def generate_code(self):
        kod = "class " + self.name + "\n"
        kod += "{\n"        # otvaramo zagradu za definiciju klase

        specifier = "private"       # dok ne naidjemo na izricitu deklaraciju access specifiera, onda je ta prom. priv.
        for decl in self.allDeclarations:
            if isinstance(decl, AstFieldDeclaration):
                kod += "    " + specifier + " " + decl.generate_code() + ";\n"
            elif isinstance(decl, AstMethodDeclaration):
                kod += "    " + specifier + " " + decl.generate_code() + "\n"
                kod += "    {\n"
                kod += "\n"
                kod += "    }\n"
            else:
                # ako nije ni AstFieldDeclaration ni AstMethodDeclaration, onda je u pitanju promena access specifiera
                specifier = str(decl)

        kod += "}\n"        # zatvaramo zagradu za definiciju klase
        return kod
