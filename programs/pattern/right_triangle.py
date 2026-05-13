def right_triangle(N)->None:
    for i in range(N):
        for j in range(i+1):
            print("*", end="")
        print()
        
right_triangle(5)