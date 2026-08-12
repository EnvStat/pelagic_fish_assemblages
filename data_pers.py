import logging
import os
import pickle

from datetime import datetime

import pandas


"""
version 6.0
persistent data module
Shubin Mikhail
"""

VERSION = '=-6-='

##########################
## basic stuff
##########################


def save(x, path):
    if not path.endswith('.pik'): path+='.pik'
    with open(path, 'wb') as f:
        pickle.dump(x, f)


def load(path):
    if not path.endswith('.pik'): path+='.pik'
    with open(path,'rb') as f:
        return pickle.load(f)


def savetxt(x, path):
    if not path.endswith('.txt'): path+='.txt'
    with open(path,'w') as f:
        if isinstance(x, dict):
            for k, v in x.items():
                f.write(f'{k} \t= {v}\r\n')
        elif isinstance(x, (list, tuple)):
            for v in x:
                f.write(f'{v}\r\n')
        else:
            f.write(str(x))


def History(*args, **kwargs):
    if 'memory' in kwargs:
        return ParallelDataWriterWithMemory(*args, **kwargs)
    else:
        return ParallelDataWriter(*args, **kwargs)


class PDWCollision(IOError):
    """ collision of attiributes """
    pass


class PDWFileErorr(IOError):
    """ collision of attiributes """
    pass


class PDWFileAlreadyExists(IOError):
    """ collision of attiributes """
    pass


class PDWFileNotFound(IOError):
    """ collision of attiributes """
    pass


class ParallelDataWriter():
    """
    parallel data writer
    saves a dictionary of lists as a list of dictionaries

    keys:
             no folder	different keys    same keys    reopening
    a=append exception	exception         append		append
    w=write  write      rewrite           append		append
    n=new    write      rewrite           append       append
    m=mad    exception	append            append       append
    s=safe   write      exception         exception    exception
    """
    def __init__(self, name='', key='w'):
        self._name = name
        self._is_active = False
        self._key = key
        self._keys = []
        assert key in 'awnms'

    def _header(self):
        return {
            'keys': self._keys,
            'name': self._name,
            'time': str(datetime.now()),
            'version': VERSION,
            }

    def path(self):
        return self._name + '/'

    def init(self, keys):
        path = self.path()
        attr = {k: v for k,v in self.__dict__.items() if not k.startswith('_')}
        self._keys = keys

        head = self._header()
        create_new_folder = (not os.path.exists(path+'head.pik')) or self._key == 'n'

        #if the folder already exists, check if the saved data is consistent with self.
        if os.path.exists(path+'head.pik'):
            if self._key == 's':
                raise PDWFileAlreadyExists
            try:
                try:
                    old_keys = load(path+'head.pik')['keys']
                    old_attr = load(path+'attr.pik')
                except (IOError, EOFError):
                    raise PDWFileErorr()

                if old_keys != self._keys:
                    logging.error('keys collision')
                    logging.error('in old, not in new %s', set(old_keys) - set(self._keys))
                    logging.error('in new, not in old %s', set(self._keys) - set(old_keys))
                    raise PDWCollision()

                if old_attr!=attr:
                    logging.error('attributes collision')
                    logging.error('in old, not in new %s', set(old_attr.keys()) - set(attr.keys()))
                    logging.error('in new, not in old %s', set(attr.keys()) - set(old_attr.keys()))
                    for k in set(attr.keys()) & set(old_attr.keys()):
                        if attr[k] != old_attr[k]:
                            logging.error('%s \t---\t %s', attr[k], old_attr[k])
                    raise PDWCollision()

            except PDWCollision:
                # new file mode, all is fine, rewrite anyway
                # mad mode, continie anyway
                # write mode, rewrite instead od appending
                if self._key == 'w': create_new_folder = True
                # apped mode: this is error
                if self._key == 'a': raise

            except PDWFileErorr:
                # new file mode, all is fine, rewrite anyway
                # mad mode, troubling error
                if self._key == 'm': raise
                # write mode, rewrite instead od appending
                if self._key == 'w': create_new_folder = True
                # apped mode: this is error
                if self._key == 'a': raise

        if create_new_folder:
            if self._key in 'am':
                raise PDWFileNotFound()
            logging.warning('creating new folder')

            # create folders if needed
            os.makedirs(path, exist_ok=True)

            # remove existing files from the folder, if needed
            n = 0
            while os.path.exists(f'{path}data_{n}.pik'):
                logging.warning(f'removing {path}data_{n}.pik')
                os.remove(f'{path}data_{n}.pik')
                n+=1

            save(head, path+'head.pik')
            save(attr, path+'attr.pik')
            savetxt(head, path+'description.txt')
        else:
            logging.warning('appending existing folder')

        self.new_file()
        self._is_active = True

    def new_file(self):
        #count the number of esisting files
        path = self.path()
        n = 0
        while os.path.exists(f'{path}data_{n}.pik'):
            n+=1
        self._path = f'{path}data_{n}.pik'
        logging.warning(f'file n {n}')

    def writerow(self, **variables):
        if not self._is_active:
            self.init(keys=list(variables.keys()))
        self.flush(values=list(variables.values()))
        assert list(variables.keys()) == self._keys, (f'inconsistent keys! '
                                                      f'unexpected keys: {set(variables.keys()) - set(self._keys)} '
                                                      f'missing keys: {set(self._keys) - set(variables.keys())}')

    def flush(self, values):
        f = open(self._path, 'ab')
        pickle.dump(values, f)
        pickle.dump('\n', f)
        f.close()

    def save_state(self, **variables):
        path = self._name + '/state'
        save(variables, path)
        savetxt(variables, path)

    def __repr__(self):
        if self._active: return self._greetings+' (inactive)'
        else: return self._greetings


#######################
## LOAD
#######################


def Load(name, files=(), state_only=False, __class__=pandas.DataFrame):
    path = name + '/'
    if not os.path.exists(path+'head.pik'):
        raise Exception('Data do not exists', path)

    # loading header, keys, attributes and all the additional information
    attr = load(path+'attr')
    head = load(path+'head')
    keys = head['keys']

    # make the list of files
    positive_files = [x for x in files if x >= 0]
    negative_files = [x for x in files if x < 0]
    if positive_files:
        files = positive_files
    else:
        n = 0
        while os.path.exists(f'{path}data_{n}.pik'):
            n += 1
        files = set(range(n)) - set(negative_files)
        files = sorted(files)

    # start reading
    N = []  # numbers of lines per file
    H = []  # data
    for i in files:
        with open(f'{path}data_{i}.pik','rb') as f:
            current_file = []
            n = 0
            try:
                while True:
                    current_file.append(pickle.load(f))
                    n += 1
                    if pickle.load(f) != '\n':
                        raise Exception('damaged data file', path)
            except EOFError:
                #this is normal
                pass
            except:
                logging.error(f'data reading problem, file {i} line {n}')
                raise

        H.extend(current_file)
        N += [n]

    if len(H) == 0:
        raise Exception('data empty ', path)

    #create a data object
    D = __class__(H, columns=keys)

    # create attributes
    attr['__header__'] = head
    attr['__files_used__'] = files
    attr['__rows_per_file__'] = N

    D.__attr__ = attr

    return D


if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG)

    # test savetxt
    savetxt({'a': 1, 'b': 2}, 'test/test_dict')
    savetxt([1, 2, 'a'], 'test/test_list')

    # test save and load
    save({'a': 1, 'b': 20}, 'test/test_dict2')
    D = load('test/test_dict')
    print(D)

    # test ParallelDataWriter

    H = ParallelDataWriter('h', key='n')
    H.a = 'hello'
    for i in range(30):
        H.next(x=i, y=i**2)
        if i==13:
            H.new_file()
    H.save_state(x=i, y=i**2)

    del(H)

    D, attr = Load('h')
    print( D )
    print( D['x'] )
    print( D['y'] )
    print( attr['a'] )
    print( attr['__header__'] )
    print( attr['__files_used__'] )
    print( attr['__rows_per_file__'] )

    D, attr = Load('h', files=[1])
    print( D )
    D, attr = Load('h', files=[0])
    print( D )