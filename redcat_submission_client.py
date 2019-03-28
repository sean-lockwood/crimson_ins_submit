#! /usr/bin/env python

import yaml
import urllib
import os
from functools import wraps
from textwrap import wrap

BASE_URLS = {
    'dev': {
        'hst':  'https://hst-crds-dev.stsci.edu/',
        'jwst': 'https://jwst-crds-dev.stsci.edu/', },
    #'test': {
    #    'hst':  'https://hst-crds-test.stsci.edu/',
    #    'jwst': 'https://jwst-crds-test.stsci.edu/', },
    #'production': {
    #    'hst':  'https://hst-crds.stsci.edu/',
    #    'jwst': 'https://jwst-crds.stsci.edu/', },
    }

URL_DESCRIPTION = 'submission_form/redcat_description.yml'

NULL_FIELDTYPES = {
    'BooleanField'     : bool,
    'CharField'        : str,
    'TypedChoiceField' : str, }

HST_INSTRUMENTS  = ['acs', 'cos', 'nicmos', 'stis', 'wfc3', 'wfpc2']
JWST_INSTRUMENTS = ['fgs', 'miri', 'nircam', 'niriss', 'nirspec']  # system?
UNLOCKED = '<no lock acquired>'
UNAUTHENTICATED = '<unauthenticated>'

# Preserve order of YAML dicts (from https://stackoverflow.com/a/52621703):
yaml.add_representer(dict, lambda self, data: yaml.representer.SafeRepresenter.represent_dict(self, data.items()))


class RedcatSubmission(object):
    ''' Client-side Redcat submission class.  Can be used to prepare, validate, and submit 
    CRDS submissions.
    
    Call `S.help()` to print details about the submission object form fields.
    
    Parameters:
        observatory (str, {hst, jwst}):  Used in determining which CRDS for submission
        string (str, {production, test, dev}):  Used in determining which CRDS for submission
    '''
    def __init__(self, observatory, string='dev', *args, **kwargs):
        observatory = observatory.lower()
        string = string.lower()
        assert observatory in ['hst', 'jwst']
        assert string in ['dev', 'test', 'production']
        
        self._username = UNAUTHENTICATED
        self._lock_status = UNLOCKED
        self._observatory = observatory
        self._string = string
        self._url = urllib.parse.urljoin(BASE_URLS[self.string][self.observatory], URL_DESCRIPTION)
        self._files = set()
        
        try:
            with urllib.request.urlopen(self.url) as req:
                self._form_description = yaml.safe_load(req)
        except (urllib.error.HTTPError, urllib.error.URLError, ) as e:
            print ('Check your network connection!')
            raise e
        # Convert list describing form to a dictionary (preserves order):
        self._form_description = {field['key']: field for field in self._form_description}
        for key in self._form_description:  self._form_description[key].pop('key')
        
        self._all_keys = set(self._form_description.keys())
        self._required_keys = {x for x in self._form_description if self._form_description[x]['required']}
        self._optional_keys = {x for x in self._form_description if not self._form_description[x]['required']}
        
        self.__fields__ = dict()  # Users should not modify this directly!
        
        for key in self._form_description:
            # Avoid field validation for initialization by accessing hidden dictionary directly:
            self.__fields__[key] = NULL_FIELDTYPES[self._form_description[key]['type']]()
            try:
                self[key] = self._form_description[key]['initial']
            except KeyError:
                pass
    
    def __repr__(self):
        return '<RedcatSubmission Object {}-{}>:\nFields:  {}\nFiles:  {}'.format(
            self.observatory, self.string, 
            self.__fields__.__repr__(), 
            self.files.__repr__())
    
    def __setitem__(self, key, value):
        ''' Intercept and enforce validation requirements on individual fields.
        Booleans values map to 'Yes' and 'No' str.
        '''
        assert key in self._all_keys, "Key not in submission form template:  '{}'".format(key)
        if key in self._required_keys:
            assert value != '', "Field '{}' cannot be empty.".format(key)  # allow Boolean False
        field_type = NULL_FIELDTYPES[self._form_description[key]['type']]
        
        # Interpret boolean values in choice fields as 'Yes' and 'No':
        if isinstance(value, bool) and ('choices' in self._form_description[key]):
            if value:
                value = 'Yes'
            else:
                value = 'No'
        assert isinstance(value, field_type), \
            "'{}' must be of type {}".format(key, field_type.__name__)
        
        # Check if choice fields have allowed values:
        if 'choices' in self._form_description[key]:
            matches = [x for x in self._form_description[key]['choices'] if x.lower() == value.lower()]
            assert len(matches) == 1, \
                "'{}' must be a valid choice: {{{}}}".format(key, 
                    ', '.join(self._form_description[key]['choices']))
            # Inherit case from matching choice:
            value = matches[0]
         
        self.__fields__[key] = value
    
    @wraps(dict.__getitem__)
    def __getitem__(self, key, *args, **kargs):
        return self.__fields__.__getitem__(key, *args, **kargs)
    
    @wraps(dict.__contains__)
    def __contains__(self, *args, **kargs):
        return self.__fields__.__contains__(*args, **kargs)
    
    @wraps(dict.get)
    def get(self, *args, **kargs):
        return self.__fields__.get(*args, **kargs)
    
    @wraps(dict.keys)
    def keys(self, *args, **kargs):
        return self.__fields__.keys(*args, **kargs)
    
    @wraps(dict.values)
    def values(self, *args, **kargs):
        return self.__fields__.values(*args, **kargs)
    
    @wraps(dict.items)
    def items(self, *args, **kargs):
        return self.__fields__.items(*args, **kargs)
    
    def help(self):
        ''' Print help text derived from CRDS instance specified.
        '''
        # Can't easily overwrite __doc__ dynamically.
        for key, field in self._form_description.items():
            print (key, ' (', NULL_FIELDTYPES[self._form_description[key]['type']].__name__, 
                ', optional)' if not field.get('required', False) else ')', '\n', '-'*len(key), sep='')
            print ('\n'.join(wrap(field['label'])))
            if 'help_text' in field:
                print ('\n'.join(wrap(field['help_text'])))
            if 'choices' in field:
                print ('Valid choices:')
                # print ('  - ' + '\n  - '.join(field['choices']))
                print ('  {', ', '.join(["'{}'".format(x) for x in field['choices']]), '}', sep='')
            print ()
    
    def validate(self):
        ''' Validate the object for submission to CRDS.
        '''
        assert (set(self.keys()) - self._optional_keys) == self._required_keys, 'Extra/missing keys...'
        
        # Check for all empty required keys at once to raise one exception:
        empty_keys = {key for key in self._required_keys if self[key] == ''}  # Don't flag False booleans
        if empty_keys:
            raise Exception('These keywords cannot be empty:\n    ' + '\n    '.join(empty_keys))
        
        # If instrument is locked and "instrument" field is defined, make sure they're the same:
        assert (self.lock_status == UNLOCKED) or ('instrument' not in self) or (self['instrument'] == self.lock_status), \
            'Locked instrument is not the one being updated!'
        
        # Make sure files were associated with the submission:
        assert len(self.files) > 0, 'No files have been added to submission.  Use the `S.add_file()` method.'
        
        # More validation...
        
        # Call crds.certify() again? ...
        
    def add_file(self, filename):
        ''' Add a file to the submission.  Calls crds.certify() on the file.
        '''
        if not os.access(filename, os.R_OK):
            raise FileNotFoundError("'{}' does not exist or is not readable.".format(filename))
        
        # Call crds.certify() on file...
        
        self._files.add(filename)
        
        raise NotImplementedError()
    
    @property
    def files(self):
        ''' Set of files associated with the submission.
        '''
        return frozenset(self._files)
    
    @wraps(set.remove)
    def remove_file(self, filename, *args, **kargs):
        self._files.remove(filename, *args, **kargs)
    
    #@wraps(set.pop)
    #def pop_file(self, *args, **kargs):
    #    return self._files.pop(*args, **kargs)
    
    @property
    def yaml(self):
        ''' YAML representation of this submission object.
        '''
        return yaml.dump(dict(self))
    
    def submit(self):
        ''' Verification, send to CRDS server
        '''
        self.validate()
        raise NotImplementedError()
    
    def authenticate(self, username, login):
        ''' Login to the CRDS server using an auth.mast token.
        See http://auth.mast.stsci.edu/
        
        Parameters:
            username (str):  
            login (str):  
        '''
        self._username = username
        raise NotImplementedError()
    
    def logout(self):
        ''' Logout user.
        '''
        self._username = UNAUTHENTICATED
        raise NotImplementedError()
    
    @property
    def observatory(self):
        ''' Instantiated for HST or JWST.
        '''
        return self._observatory
    
    @property
    def string(self):
        ''' Instantiated for production, test, or dev string.
        '''
        return self._string
    
    @property
    def username(self):
        ''' Currently logged-in user.
        '''
        return self._username
    
    @property
    def url(self):
        ''' URL to CRDS instance specified at instantiation.
        '''
        return self._url
    
    @property
    def lock_status(self):
        ''' Instrument currently locked.
        '''
        return self._lock_status
    
    def lock(self, instrument):
        ''' Acquire an instrument lock.
        
        Parameter:
            instrument (str):  Must correspond to an instrument from the observatory 
                               specified on instantiation of the class.
        '''
        if self.observatory == 'hst':
            assert instrument in HST_INSTRUMENTS
        elif self.observatory == 'jwst':
            assert instrument in JWST_INSTRUMENTS
        else:
            raise Exception('Instrument not supported for {}'.format(self.observatory))
        
        assert self.username != UNAUTHENTICATED, 'You must first authenticate with the CRDS server.'
        
        self._lock_status = instrument
        
        raise NotImplementedError()
    
    def unlock(self):
        ''' Drop the instrument lock.
        '''
        self._lock_status = UNLOCKED
        raise NotImplementedError()
