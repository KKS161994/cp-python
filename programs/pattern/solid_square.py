def printPattern(N) -> None:
    for i in range(N):
        for j in range(N):
            print("*",end="")
        print("")

printPattern(5)