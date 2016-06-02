a = {'1':True, '2':False}

def logged_in(dictionary, key):
    if dictionary.get(key, False) and dictionary[key]:
        return True
    else:
        return False

if __name__ == '__main__':
    print(logged_in(a, '1'))
    print(logged_in(a, '2'))
    print(logged_in(a, '3'))
    print(bool('True') == True)
    print(bool('False'))
    print(bool('0'))