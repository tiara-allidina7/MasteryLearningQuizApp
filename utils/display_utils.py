import decimal


def topic_marks_to_percent_display(topic_marks):
    for component, records in topic_marks.items():
        for record in records:
            record["grade"] = mark_to_display(record["grade"])


def mark_to_display(mark, show_dnw=False):
    if mark is None:
        return "DNW" if show_dnw else ""
    if mark == -1:
        return "N/A"
    return str(trim_trailing_zeroes(round(mark * 100, 2))) + "%"


def trim_trailing_zeroes(num):
    if num is None:
        return num
    try:
        num = num.quantize(decimal.Decimal(1)) if num == num.to_integral() else round(num.normalize(), 2)
    except AttributeError:
        num = decimal.Decimal(num)
        num = num.quantize(decimal.Decimal(1)) if num == num.to_integral() else round(num.normalize(), 2)

    return num
