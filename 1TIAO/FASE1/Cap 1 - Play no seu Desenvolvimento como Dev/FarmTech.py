import os


lavouras = []


while True:
    os.system('cls')
   

    print("===== FarmTech Solutions =====")
    
    print("1 - Inserir Dados")
    print("2 - Visualizar Dados")
    print("3 - Atualizar Dados")
    print("4 - Deletar Dados")
    print("5 - Sair")

    print("===============================")

    user = int(input("\nDigite a opção desejada:\t"))

    if(user == 1):
        os.system('cls')

        cultura = input("Digite o nome da cultura:\t")
        comprimento = float(input("Qual o comprimento da lavoura? \t"))
        largura = float(input("Qual a largura da lavoura? \t"))
        ruas = int(input("Qual o numero de ruas existentes na lavoura?\t"))

        area = comprimento * largura

        area_total = area - (ruas * 0.5)    # De acordo com google, ruas de lavouras tem aproximadamente 0,5 metro

        insumo = input("Qual o insumo que pretende utilizar?\t")
        qnt_insumo = int(input("Qual a quantidade, em mL por metro, a ser pulverizada?\t"))

        qnt_litros = (qnt_insumo * area) / 1000

        # Arredondar valores
        print(f"\n\nSerá pulverizado ao todo {round(qnt_litros, 3)} litros de {insumo}, em todo os {area} m²")

        lavouras.append({
            "cultura":cultura,
            "area":area,
            "ruas":ruas,
            "insumo":insumo,
            "qnt_insumo":qnt_insumo,
            "qnt_litros":qnt_litros
        })

        input("\n\nPressione Enter para continuar")

    elif(user == 2):
        os.system('cls')

        if not lavouras:
            print("Nao há lavouras cadastradas")

            input("\n\nPressione Enter para continuar")
        # da p estilizar
        else:
            for i,lavoura in enumerate(lavouras):
                print(i,lavoura)

            input("\n\nPressione Enter para continuar")


    elif(user == 3):
        os.system('cls')

        # Pode ser visualizado os dados antes de esoclher. Ajuda a lembrar
        id_lavoura = int(input("Digite o indice da lavoura: \t"))
        campo = input("Digite o campo a editar: \t")
        novo_valor = input("Digite o novo valor: \t")

        # Formatar prints
        if 0 <= id_lavoura < len(lavouras):
            lavouras[id_lavoura][f"{campo}"] = novo_valor
            print(f"Lavoura ID {id_lavoura} atualizado para {novo_valor}")
            input("\n\nPressione Enter para continuar")
        else:
            print("ID de lavoura inválido.")
            input("\n\nPressione Enter para continuar")
            
        
    elif(user == 4):
        os.system('cls')

        id_lavoura = int(input("Digite o indice da lavoura: \t"))
        if 0 <= id_lavoura < len(lavouras):
            lavoura_removida = lavouras.pop(id_lavoura)
            print(f"Lavoura {lavoura_removida["cultura"]} removido com sucesso.")

            input("\n\nPressione Enter para continuar")
        else:
            print("ID de lavoura inválido.")

            input("\n\nPressione Enter para continuar")

    elif(user == 5):
        break

    else:
        os.system('cls')

        print("Digite uma opção valida!")

        input("\n\nPressione Enter para continuar")
    