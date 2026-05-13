def daily_temp(temps: list[int]) -> list[int]:
    result = [0] * len(temps)
    stack = []

    # for i, temp in enumerate(temps):
    #     while stack and temps[stack[-1]] < temp:
    #         prev_index = stack.pop()
    #         result[prev_index] = i - prev_index
    #     stack.append(i)

    for i in range(len(temps)):
        while stack and stack[-1] < temps[i]:
            prev_index = stack.pop()
            result[prev_index] = i - prev_index
            
        stack.append(i)


    return result
        


    