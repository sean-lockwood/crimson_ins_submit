#! /usr/bin/env python

import yaml
import urllib
import os
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

# Preserve order of YAML dicts (from https://stackoverflow.com/a/52621703):
yaml.add_representer(dict, lambda self, data: yaml.representer.SafeRepresenter.represent_dict(self, data.items()))


class RedcatSubmission(dict):
    ''' Client-side Redcat submission class.  Can be used to prepare, validate, and submit 
    CRDS submissions.
    
    Parameters:
        observatory (str, {hst, jwst}):  Used in determining which CRDS for submission
        string (str, {production, test, dev}):  Used in determining which CRDS for submission
    '''
    def __init__(self, observatory, string='dev', *args, **kwargs):
        observatory = observatory.lower()
        string = string.lower()
        assert observatory in ['hst', 'jwst']
        assert string in ['dev', 'test', 'production']
        
        self._username = '<unauthenticated>'
        self._lock_status = '<no lock acquired>'
        self.observatory = observatory
        self.string = string
        self.url = urllib.parse.urljoin(BASE_URLS[self.string][self.observatory], URL_DESCRIPTION)
        
        try:
            with urllib.request.urlopen(self.url) as req:
                self.form_description = yaml.safe_load(req)
        except (urllib.error.HTTPError, urllib.error.URLError, ) as e:
            print ('Check your internet connection!')
            raise e
        # Convert list describing form to a dictionary (preserves order):
        self.form_description = {field['key']: field for field in self.form_description}
        for key in self.form_description:  self.form_description[key].pop('key')
        
        self._all_keys = set(self.form_description.keys())
        self._required_keys = {x for x in self.form_description if self.form_description[x]['required']}
        self._optional_keys = {x for x in self.form_description if not self.form_description[x]['required']}
        
        super(RedcatSubmission, self).__init__(self, *args, **kwargs)
        
        for key in self.form_description:
            #self[key] = NULL_FIELDTYPES[self.form_description[key]['type']]()
            # Use parent class __setitem__() to avoid field validation upon initialization:
            super(RedcatSubmission, self).__setitem__(key, NULL_FIELDTYPES[self.form_description[key]['type']]())
            try:
                self[key] = self.form_description[key]['initial']
            except KeyError:
                pass
    
    def __repr__(self):
        return '<SUBMISSION {}-{}>:\n{}'.format(self.observatory, self.string, 
            super(RedcatSubmission, self).__repr__())
    
    def __setitem__(self, key, value):
        ''' Intercept and enforce validation requirements on individual fields.
        '''
        assert key in self._all_keys
        if key in self._required_keys:
            assert value, "Field '{}' cannot be empty.".format(key)
        field_type = NULL_FIELDTYPES[self.form_description[key]['type']]
        assert isinstance(value, field_type), \
            '{} must be of type {}'.format(key, field_type.__name__)
        if 'choices' in self.form_description[key]:                     # *** <-- WORKING HERE:  Make case-insensitive
            assert value in self.form_description[key]['choices'], \
                '{} must be a valid choice: {{{}}}'.format(key, 
                    ', '.join(self.form_description[key]['choices']))
         
        super(RedcatSubmission, self).__setitem__(key, value)
    
    def help(self):
        ''' Print help text derived from CRDS instance specified.
        '''
        # Can't easily overwrite __doc__ dynamically.
        for key, field in self.form_description.items():
            print (key, ' (', NULL_FIELDTYPES[self.form_description[key]['type']].__name__, 
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
        empty_keys = {key for key in self._required_keys if not self[key]}
        if empty_keys:
            raise Exception('These keywords cannot be empty:\n    ' + '\n    '.join(empty_keys))
        
        # More validation...
        
        # Call crds.certify()...
        
    def add_file(self, filename):
        ''' Add a file to the submission.  Calls crds.certify() on the file.
        '''
        if not os.access(filename, os.R_OK):
            raise FileNotFoundError("'{}' does not exist or is not readable.".format(filename))
        
        raise NotImplementedError()
    
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
    
    @property
    def username(self):
        ''' Currently logged-in user.
        '''
        return self._username
    
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
        
        self._lock_status = instrument
        
        raise NotImplementedError()
    
    def unlock(self):
        ''' Drop the instrument lock.
        '''
        self._lock_status = '<no lock acquired>'
        raise NotImplementedError()
