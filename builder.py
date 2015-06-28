#!/usr/bin/env python

"""
Not empty
"""

import os
import pmag
import validate_upload

class ErMagicBuilder(object):
    """
    more object oriented builder
    """

    def __init__(self, WD):
        self.WD = WD
        self.specimens = []
        self.samples = []
        self.sites = []
        self.locations = []
        self.data_model = validate_upload.get_data_model()


    def find_by_name(self, items_list, item_name):
        """
        Return item from items_list with name item_name.
        """
        #print '--'
        names = [item.name for item in items_list]
        #print 'items list', items_list
        #print 'items name', names
        if item_name in names:
            ind = names.index(item_name)
            #print 'ind', ind
            #print '--'
            return items_list[ind]
        else:
            print item_name, 'not in ', names
        return False

    def change_specimen(self, specimen, new_spec_name, new_sample=None, new_specimen_data={}):
        pass
        
    #def find_all_children(self, parent_item):
    #    """
    #
    #    ancestry = ['specimen', 'sample', 'site', 'location']
    #    child_types = {'sample': self.specimens, 'site': self.samples, 'location': self.sites}
    #    dtype = parent_item.dtype
    #    ind = ancestry.index(dtype)
    #    children = child_types[dtype]
    #
    #    if dtype in (1, 2, 3):
    #        pass


    def get_data(self):
        """
        attempt to read measurements file in working directory.
        """
        try:
            meas_data, file_type = pmag.magic_read(os.path.join(self.WD, "magic_measurements.txt"))
        except IOError:
            print "-E- ERROR: Can't find magic_measurements.txt file. Check path."
            return {}
        if file_type == 'bad_file':
            print "-E- ERROR: Can't read magic_measurements.txt file. File is corrupted."

        for rec in meas_data:
            #print 'rec', rec
            specimen_name = rec["er_specimen_name"]
            if specimen_name == "" or specimen_name == " ":
                continue
            sample_name = rec["er_sample_name"]
            site_name = rec["er_site_name"]
            location_name = rec["er_location_name"]

            # add items and parents
            location = self.find_by_name(self.locations, location_name)
            if not location:
                location = Location(location_name, 'location', self.data_model)
                self.locations.append(location)
            site = self.find_by_name(self.sites, site_name)
            if not site:
                site = Site(site_name, 'site', self.data_model)
                self.sites.append(site)
                site.location = location
            sample = self.find_by_name(self.samples, sample_name)
            if not sample:
                sample = Sample(sample_name, 'sample', self.data_model)
                sample.site = site
                self.samples.append(sample)
            specimen = self.find_by_name(self.specimens, specimen_name)
            if not specimen:
                specimen = Specimen(specimen_name, 'specimen', self.data_model)
                specimen.sample = sample
                self.specimens.append(specimen)

            # add child_items
            if not self.find_by_name(sample.specimens, specimen_name):
                sample.specimens.append(specimen)
            if not self.find_by_name(site.samples, sample_name):
                site.samples.append(sample)
            if not self.find_by_name(location.sites, site_name):
                location.sites.append(site)


class Pmag_object(object):
    """
    Base class for Specimens, Samples, Sites, etc.
    """

    def __init__(self, name, dtype, data_model=None):
        if not data_model:
            self.data_model = validate_upload.get_data_model()
        else:
            self.data_model = data_model
        self.name = name
        self.dtype = dtype

        er_name = 'er_' + dtype + 's'
        pmag_name = 'pmag_' + dtype + 's'
        self.pmag_reqd_headers, self.pmag_optional_headers = self.get_headers(pmag_name)
        self.er_reqd_headers, self.er_optional_headers = self.get_headers(er_name)

    def __repr__(self):
        return self.dtype + ": " + self.name

    def get_headers(self, data_type):
        """
        If data model not present, get data model from Earthref site or PmagPy directory.
        Return a list of required headers and optional headers for given data type.
        """
        try:
            data_dict = self.data_model[data_type]
        except KeyError:
            return [], []
        reqd_headers = sorted([header for header in data_dict.keys() if data_dict[header]['data_status'] == 'Required'])
        optional_headers = sorted([header for header in data_dict.keys() if data_dict[header]['data_status'] != 'Required'])
        return reqd_headers, optional_headers

    def combine_dicts(self, new_dict, old_dict):
        """
        returns a dictionary with all key, value pairs from new_dict.
        also returns key, value pairs from old_dict, if that key does not exist in new_dict.
        if a key is present in both new_dict and old_dict, the new_dict value will take precedence.
        """
        old_data_keys = old_dict.keys()
        new_data_keys = new_dict.keys()
        all_keys = set(old_data_keys).union(new_data_keys)
        combined_data_dict = {}
        for k in all_keys:
            try:
                combined_data_dict[k] = new_dict[k]
            except KeyError:
                combined_data_dict[k] = old_dict[k]
        return combined_data_dict





class Specimen(Pmag_object):

    """
    Specimen level object
    """

    def __init__(self, name, dtype, data_model=None):
        super(Specimen, self).__init__(name, dtype, data_model)
        self.sample = ""
        #self.site = ""
        #self.location = ""
        self.data = {}

    def change_specimen(self, new_name, new_sample=None, data_dict=None):
        self.name = new_name
        if new_sample:
            self.sample = new_sample
        if data_dict:
            self.combine_dicts(data_dict, self.data)

class Sample(Pmag_object):

    """
    Sample level object
    """

    def __init__(self, name, dtype, data_model=None):
        super(Sample, self).__init__(name, dtype, data_model)
        self.specimens = []
        self.site = ""
        #self.location = ""
        self.data = {}

    def change_sample(self, new_name, new_site=None, data_dict=None):

        # maybe make this a Pmag_object method
        self.name = new_name
        if new_site:
            self.site = new_site
        if data_dict:
            self.combine_dicts(data_dict, self.data)




class Site(Pmag_object):

    """
    Site level object
    """

    def __init__(self, name, dtype, data_model=None):
        super(Site, self).__init__(name, dtype, data_model)
        self.samples = []
        self.location = ""
        self.data = {}

    def change_site(self, new_name, new_location=None, data_dict=None):

        # maybe make this a Pmag_object method
        self.name = new_name
        if new_location:
            self.location = new_location
        if data_dict:
            self.combine_dicts(data_dict, self.data)



class Location(Pmag_object):

    """
    Location level object
    """

    def __init__(self, name, dtype, data_model=None):
        super(Location, self).__init__(name, dtype, data_model)
        self.sites = []
        self.data = {}

    def change_location(self, new_name, data_dict=None):
        self.name = new_name
        if data_dict:
            self.combine_dicts(data_dict, self.data)





if __name__ == '__main__':
    wd = pmag.get_named_arg_from_sys('-WD', default_val=os.getcwd())
    builder = ErMagicBuilder(wd)
    builder.get_data()
    #specimen = Specimen('spec1', 'specimen')
    #for spec in builder.specimens:
        #print str(spec) + ' belongs to ' + str(spec.sample) + ' belongs to ' + str(spec.sample.site) + ' belongs to ' + str(spec.sample.site.location)
    for site in builder.sites:
        print site, site.samples
        print '--'



