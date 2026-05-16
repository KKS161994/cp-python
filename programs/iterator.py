def sample_iterator():
    my_list = [1, 2, 3, 4]
    iterator = iter(my_list)
    while (element := next(iterator, None)) is not None:
        print(element)


def for_over_list():
    my_list = [1, 2, 3, 4]
    for element in my_list:
        print(element)


def for_over_iterator():
    my_list = [1, 2, 3, 4]
    iterator = iter(my_list)
    for element in iterator:
        print(element)


def while_with_stopiteration():
    my_list = [1, 2, 3, 4]
    iterator = iter(my_list)
    while True:
        try:
            element = next(iterator)
        except StopIteration:
            break
        print(element)


def while_with_sentinel():
    my_list = [1, 2, 3, 4]
    iterator = iter(my_list)
    while True:
        element = next(iterator, None)
        if element is None:
            break
        print(element)


def iter_with_sentinel():
    my_list = [1, 2, 3, 4]
    iterator = iter(my_list)
    for element in iter(lambda: next(iterator, None), None):
        print(element)


if __name__ == "__main__":
    for fn in (
        sample_iterator,
        for_over_list,
        for_over_iterator,
        while_with_stopiteration,
        while_with_sentinel,
        iter_with_sentinel,
    ):
        print(f"--- {fn.__name__} ---")
        fn()
