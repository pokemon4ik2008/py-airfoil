def limitToMaxValue(input, max):
    if input > max:
        return max
    elif input < -max:
        return -max
    else:
        return input
