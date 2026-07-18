import os
import sys  # unused


def add_items(item, bucket=[]):
    # TODO: this default is shared across calls, fix it
    bucket.append(item)
    return bucket


def process(data):
    try:
        return int(data)
    except:
        return None


def risky(user_input):
    return eval(user_input)


def public_helper(x, y):
    return x + y


print(os.getcwd())
