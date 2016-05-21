import numpy as np
from collections import Counter, OrderedDict
import warnings
import os
import cPickle as pickle

class MLDataset(object):
    """Class defining a ML dataset that helps maintain integrity and ease of access."""

    def __init__(self, data=None, labels=None, classes=None, description=''):
        if data is None or labels is None:
            self.__data = OrderedDict()
            self.__labels = OrderedDict()
            self.__classes = OrderedDict()
            self.__num_features = 0
        else:
            assert isinstance(data, dict), 'data must be a dict! keys: subject ID or any unique identifier'
            assert isinstance(labels, dict), 'labels must be a dict! keys: subject ID or any unique identifier'
            if classes is not None:
                assert isinstance(classes, dict), 'labels must be a dict! keys: subject ID or any unique identifier'

            assert len(data) == len(labels) == len(classes), 'Lengths of data, labels and classes do not match!'
            assert set(data.keys()) == set(labels.keys()) == set(classes.keys()), 'data, classes and labels ' \
                                                                                  'dictionaries must have the same keys!'
            num_features_in_elements = np.unique([len(sample) for sample in data.values()])
            assert len(num_features_in_elements) == 1, 'different samples have different number of features - invalid!'

            self.__num_features = num_features_in_elements[0]
            # OrderedDict to ensure the order is maintained when data/labels are returned in a matrix/array form
            self.__data = OrderedDict(data)
            self.__labels = OrderedDict(labels)
            self.__classes = OrderedDict(classes)
            self.__dtype = type(data)

        self.__description = description

    def load(self, path):
        raise NotImplementedError
        # try:
        #     path = os.path.abspath(path)
        #     with open(path, 'rb') as df:
        #         dataset = pickle.load(df)
        #         self.__dict__.update(dataset)
        #         return self
        # except IOError as ioe:
        #     raise IOError('Unable to read the dataset from file: {}',format(ioe))
        # finally:
        #     raise

    def save(self, path):
        raise NotImplementedError
        # try:
        #     path = os.path.abspath(path)
        #     with open(path, 'wb') as df:
        #         save_state = dict(self.__dict__)
        #         pickle.dump(save_state, df)
        #         # pickle.dump((self.__data, self.__classes, self.__labels, self.__dtype, self.__description), df)
        #         return
        # except IOError as ioe:
        #     raise IOError('Unable to read the dataset from file: {}',format(ioe))
        # finally:
        #     raise


    @property
    def data(self):
        """data in its original dict form."""
        return self.__data

    @property
    def data_matrix(self):
        """dataset features in a matrix form."""
        mat = np.zeros([self.num_samples, self.num_features])
        for ix, (sub, features) in enumerate(self.__data.items()):
            mat[ix, :] = features
        return mat

    @data.setter
    def data(self, values):
        if isinstance(values, dict):
            if self.__labels is not None and len(self.__labels) != len(values):
                raise ValueError('number of samples do not match the previously assigned labels')
            elif len(values) < 1:
                raise ValueError('There must be at least 1 sample in the dataset!')
            else:
                self.__data = values
        else:
            raise ValueError('data input must be a dictionary!')

    @property
    def labels(self):
        return self.__labels.values()

    @labels.setter
    def labels(self, values):
        """Class labels (such as 1, 2, -1, 'A', 'B' etc.) for each sample in the dataset."""
        if isinstance(values, dict):
            if self.__data is not None and len(self.__data) != len(values):
                raise ValueError('number of samples do not match the previously assigned data')
            else:
                self.__labels = values
        else:
            raise ValueError('labels input must be a dictionary!')

    @property
    def class_sizes(self):
        return Counter(self.classes)

    @property
    def __label_set(self):
        return set(self.labels)

    def add_sample(self, subject_id, features, label, class_id=None):
        """Adds a new sample to the dataset with its features, label and class ID. This is the preferred way to
        construct the dataset."""
        if subject_id not in self.__data:
            if self.num_samples <= 0:
                self.__data[subject_id] = features
                self.__labels[subject_id] = label
                self.__classes[subject_id] = class_id
                self.__dtype = type(features)
                self.__num_features = len(features)
            else:
                assert self.__num_features == len(features), \
                    ValueError('dimensionality of this sample ({}) does not match existing samples ({})'.format(
                    len(features),self.__num_features))
                assert isinstance(features,self.__dtype), TypeError("Mismatched dtype. Provide {}".format(self.__dtype))

                self.__data[subject_id] = features
                self.__labels[subject_id] = label
                self.__classes[subject_id] = class_id
        else:
            raise ValueError('{} already exists in this dataset!'.format(subject_id))

    def get_class(self, class_id):
        if class_id in self.class_set:
            subset_in_class = [sub_id for sub_id in self.__classes if self.__classes[sub_id] == class_id]
            return self.get_subset(subset_in_class)
        else:
            raise ValueError('Requested class: {} does not exist in this dataset.'.format(class_id))

    def get_subset(self, subset_ids):

        num_existing_keys = sum([1 for key in subset_ids if key in self.__data])
        if subset_ids is not None and num_existing_keys > 0:
            # need to ensure data are added to data, labels etc in the same order of subject IDs
            data = self.__get_subset_from_dict(self.__data, subset_ids)
            labels = self.__get_subset_from_dict(self.__labels, subset_ids)
            if self.__classes is not None:
                classes = self.__get_subset_from_dict(self.__classes, subset_ids)
            else:
                classes = None
            subdataset = MLDataset(data, labels, classes)
            # Appending the history
            subdataset.description += '\n Subset derived from: ' + self.description
            return subdataset
        else:
            warnings.warn('subset of IDs requested do not exist in the dataset!')
            return MLDataset()

    def __get_subset_from_dict(self, dict, subset):
        # Using OrderedDict helps ensure data are added to data, labels etc in the same order of subject IDs
        return OrderedDict((sid, dict[sid]) for sid in dict if sid in subset)

    @property
    def keys(self):
        """Identifiers (subject IDs, or sample names etc) forming the basis of dict-type MLDataset."""
        return self.__data.keys()

    @property
    def subject_ids(self):
        return self.keys

    @property
    def classes(self):
        """Identifiers (subject IDs, or sample names etc) forming the basis of dict-type MLDataset."""
        return self.__classes.values()

    @property
    def description(self):
        """Text description (header) that can be set by user."""
        return self.__description

    @description.setter
    def description(self, str_val):
        """Text description that can be set by user."""
        if not str_val: raise ValueError('description can not be empty')
        self.__description = str_val

    @property
    def num_features(self):
        """number of features in each sample."""
        return self.__num_features

    @property
    def num_samples(self):
        """number of samples in the entire dataset."""
        if self.__data is not None:
            return len(self.__data)
        else:
            return 0

    @property
    def num_classes(self):
        return len(self.__label_set)

    @property
    def class_set(self):
        return set(self.__classes.values())

    def add_classes(self, classes):
        assert isinstance(classes,dict), TypeError('Input classes is not a dict!')
        assert len(classes) == self.num_samples, ValueError('Too few items - need {} keys'.format(self.num_samples))
        assert all([ key in self.keys for key in classes ]), ValueError('One or more unrecognized keys!')
        self.__classes = classes

    def __len__(self):
        return self.num_samples

    def __nonzero__(self):
        if self.num_samples < 1:
            return False
        else:
            return True

    def __str__(self):
        """Returns a concise and useful text summary of the dataset."""
        full_descr = list()
        full_descr.append(self.description)
        full_descr.append('{} samples and {} features.'.format(self.num_samples, self.num_features))
        class_ids = self.class_sizes.keys()
        max_width = max([len(cls) for cls in class_ids])
        for cls in class_ids:
            full_descr.append('Class {:>{}} : {} samples.'.format(cls, max_width, self.class_sizes.get(cls)))
        return '\n'.join(full_descr)

    def __format__(self, fmt_str):
        if isinstance(fmt_str, basestring):
            return '{} samples x {} features with {} classes'.format(
                self.num_samples, self.num_features, self.num_classes)
        else:
            raise NotImplementedError('Requsted type of format not implemented.')

    def __repr__(self):
        return self.__str__()

    def __dir__(self):
        """Returns the preferred list of attributes to be used with the dataset."""
        return ['add_sample',
                'class_set',
                'class_sizes',
                'classes',
                'data',
                'data_matrix',
                'description',
                'get_class',
                'get_subset',
                'keys',
                'labels',
                'num_classes',
                'num_features',
                'num_samples',
                'subject_ids',
                'add_classes' ]

