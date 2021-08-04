from Stablo import *
from CPP14Visitor import CPP14Visitor
from CPP14Lexer import CPP14Lexer
import antlr4

if __name__ is not None and "." in __name__:
    from .CPP14Parser import CPP14Parser
else:
    from CPP14Parser import CPP14Parser


# funkcija za citanje koda
def GetCode(name):
    file = open(name, 'r')
    code = ""
    for line in file:
        code += line

    return code


# inicijalizacija potrebnih promenljivih
file_name = "Test.txt"
input_code = GetCode(file_name)
code = antlr4.InputStream(input_code)

lexer = CPP14Lexer(code)
tokens = antlr4.CommonTokenStream(lexer)
parser = CPP14Parser(tokens)
tree = parser.translationUnit()


# definicija klase, pomocu koje visitujemo stablo i pravimo ast
class Visitor(CPP14Visitor):
    allClasses = []
    allFunctions = []

    def __init__(self):
        self.current_class = None
        self.current_function = None
        self.current_field = None
        self.current_method = None
        self.declaration = None
        self.member_specification_flag = False
        self.typesDictionary = {            # svaki podrzan C++ tip je uparen sa svojim C# ekvivalentom
            "int": "int",
            "char": "char",
            "long long": "long",
            "string": "string",
            "double": "double",
            "float": "float"
        }
        self.classes_dictionary = {}    # ime klase je povezano sa AstClass objektom za tu klasu
        # NOTE: u ovaj recnik dodajem takodje svaku klasu kao poseban 'tip'

    def visitConstantExpression(self, ctx: CPP14Parser.ConstantExpressionContext):
        self.current_field.array_size = ctx.getText()
        return self.visitChildren(ctx)

    def visitNoPointerDeclarator(self, ctx: CPP14Parser.NoPointerDeclaratorContext):
        if ctx.constantExpression() == "None":
            if self.declaration is not None:
                self.declaration.array_definition = False
        else:
            if self.declaration is not None:
                self.declaration.variable = ctx.getText()
        #    print("PROMENLJIVA: " + self.variable)
        return self.visitChildren(ctx)

    def visitDeclSpecifier(self, ctx: CPP14Parser.DeclSpecifierSeqContext):
    #    if self.declaration is not None:
        #    if not(ctx.getText() in self.typesDictionary.values()):
             #   self.typesDictionary[ctx.getText()] = ctx.getText()

            #    print("Getting type of a declaration...")
            #    print(ctx.getText())
    #        self.declaration.type = self.typesDictionary[ctx.getText()]
        var_type = ctx.getText()

        if self.current_field is not None:
            if not self.current_field.abstract and var_type == "virtual":
                self.current_field.abstract = True
            else:
                self.current_field.type = var_type if self.current_field.type is None else self.current_field.type
        elif self.current_method is not None:
            # posto je sintaksa virtual int a ne int virutal, prvo proveravamo za virutal a posle za int
            if self.current_method.virtual is None and var_type == "virtual":
                self.current_method.virtual = var_type
            else:
                self.current_method.type = var_type if self.current_method.type is None else self.current_method.type
        elif self.current_function is not None:
            self.current_function.type = var_type if self.current_function.type is None else self.current_function.type

        return self.visitChildren(ctx)

    def visitInitializerClause(self, ctx: CPP14Parser.InitializerContext):
        value = ctx.getText()
        if value != "None":
            if self.current_field is not None:
                self.current_field.value = value

    def visitDeclaratorid(self, ctx: CPP14Parser.DeclaratorContext):
        variable = ctx.getText()
        if variable != "None":
            if self.current_field is not None:
                self.current_field.name = variable if self.current_field.name == "" else self.current_field.name
            elif self.current_method is not None:
                self.current_method.name = variable if self.current_method.name == "" else self.current_method.name
            elif self.current_function is not None:
                self.current_function.name = variable if self.current_function.name == "" else self.current_function.name
            #    print("ime funkcije: " + self.current_function.name)
        return self.visitChildren(ctx)

    def visitInitDeclarator(self, ctx: CPP14Parser.InitDeclaratorContext):
        return self.visitChildren(ctx)

    def visitSimpleDeclaration(self, ctx: CPP14Parser.SimpleDeclarationContext):
        # ovo mi zapravo mozda nece ni biti potrebno...
        if self.current_function is not None:
            self.declaration = AstDeclaration()       # pravimo objekat koji cemo popuniti

        self.visitChildren(ctx)
        self.declaration = None
        return

    def visitClassName(self, ctx: CPP14Parser.ClassNameContext):
        if self.current_class is not None:
            self.current_class.name = ctx.getText()       # dete ovog cvora je ime klase
            self.classes_dictionary[ctx.getText()] = self.current_class
        return self.visitChildren(ctx)

    def visitBaseTypeSpecifier(self, ctx:CPP14Parser.BaseTypeSpecifierContext):
        if self.current_class is not None:
            # oznaci koja klasa je bazna trenutnoj
            self.current_class.parent_classes.append(self.classes_dictionary[ctx.getText()])
            # oznaci baznoj klasi da trenutna klasa nasledjuje od nje
            self.classes_dictionary[ctx.getText()].child_classes.append(self.current_class)

    def visitBaseSpecifier(self, ctx: CPP14Parser.BaseClauseContext):
        # posto u C# ne mozemo reci da li je nasledjivanje public, protected ili private - access specifier nas ne
        # zanima, zanima nas samo ime klase od koje nasledjujemo]
        self.visitChildren(ctx)
        return

    def visitFunctionDefinition(self, ctx: CPP14Parser.FunctionBodyContext):
        if self.current_method is None:
            # ako ne obradjujemo metodu neke klase, onda se radi o definiciji obicne funkcije
            # ta funkcija je u C# metoda klase Program, tako da ovde koristimo objekat klase AstMethodDeclaration
            # samo sto je necemo dodavati u self.current_class.allDeclarations (jer current class ne postoji)
            self.current_function = AstMethodDeclaration()

        self.visitChildren(ctx)

        if self.current_function is not None:
            self.allFunctions.append(self.current_function)

        self.current_function = None
        return

    def visitAccessSpecifier(self, ctx: CPP14Parser.AccessSpecifierContext):
        if self.member_specification_flag:
            self.current_class.allDeclarations.append(ctx.getChild(0))    # jedino dete ovog cvora je access specifier
        return

    def visitMemberdeclaration(self, ctx: CPP14Parser.MemberdeclarationContext):
        # oke, ovo ce biti nesto kao simpleDeclaration

        if ctx.functionDefinition() is None:
            # u pitanju je deklaracija polja
            self.current_field = AstFieldDeclaration()
            self.visitChildren(ctx)
            if self.current_field.abstract:
                self.current_class.abstract = True
            self.current_class.allDeclarations.append(self.current_field)
            self.current_field = None
        else:
            # u pitanju je deklaracija metode
            self.current_method = AstMethodDeclaration()
            self.visitChildren(ctx)

            self.current_class.allDeclarations.append(self.current_method)
            self.current_method = None

        return

    def visitMemberSpecification(self, ctx: CPP14Parser.MemberSpecificationContext):
        self.member_specification_flag = True
        self.visitChildren(ctx)
        self.member_specification_flag = False
        return

    def visitClassSpecifier(self, ctx: CPP14Parser.ClassSpecifierContext):
        self.current_class = AstClass()

        self.visitChildren(ctx)

        self.allClasses.append(self.current_class)

        if len(self.current_class.parent_classes) > 0:
            self.current_class.parent_classes[0].directInheritance.append(self.current_class)

        self.current_class = None
        return


visitor = Visitor()
visitor.visitTranslationUnit(tree)

main_func = AstMethodDeclaration()
main_func.type = "static int"
main_func.name = "Main"

program_class = AstClass()
program_class.name = "Program"
# u klasu program je potrebno dodati ze sve funkcije iz liste visitor.allFunctions[]

for func in visitor.allFunctions:
    if isinstance(func, AstMethodDeclaration):
        if func.name == "main":
            continue
            # main funkciju handlujem posebno
    program_class.allDeclarations.append(func)

program_class.allDeclarations.append(main_func)

visitor.allClasses.append(program_class)


for klasa in visitor.allClasses:
    if isinstance(klasa, AstClass):
        print(klasa.generate_code())
        pass
