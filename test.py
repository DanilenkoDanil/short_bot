def create_nine(number_nine: int):
    final_str = '0.'
    for i in range(number_nine):
        final_str += '9'
    return float(final_str)


print(create_nine(10))