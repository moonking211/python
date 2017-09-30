def human_format(num):
    if not num:
        return 'Not Available'
    num = long(num)
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    if magnitude == 0:
        return num
    return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])