"""
Based on the pylearn2's corruptor class.
Corruptor classes: classes that encapsulate the noise process for the DAE
training criterion.
"""

# Third-party imports
import numpy as np

class Corruptor(object):
    def __init__(self, corruption_level, rng=2001):
        """
        Allocate a corruptor object.

        Parameters
        ----------
        corruption_level : float
            Some measure of the amount of corruption to do. What this
            means will be implementation specific.
        rng : RandomState object or seed
            NumPy random number generator object (or seed for creating one)
            used to initialize a RandomStreams.
        """
        # The default rng should be build in a deterministic way
        rng = np.random.RandomState(rng)
        seed = int(rng.randint(2 ** 30))
        self.s_rng = np.random.RandomState(seed)
        self.corruption_level = corruption_level

    def __call__(self, inputs):
        """
        (Symbolically) corrupt the inputs with a noise process.

        Parameters
        ----------
        inputs : numpy nd array. Texture to be corrupted.

        Returns
        -------
        corrupted : Return the corrupted texture.

        Notes
        -----
        In the base class, this is just a stub.
        """
        raise NotImplementedError()

    def corruption_free_energy(self, corrupted_X, X):
        raise NotImplementedError()


class DummyCorruptor(Corruptor):
    def __call__(self, inputs):
        return inputs


class BinomialCorruptor(Corruptor):
    """
    A binomial corruptor sets inputs to 0 with probability
    0 < `corruption_level` < 1.
    """
    def _corrupt(self, x):
        return self.s_rng.binomial(
            size=x.shape,
            n=1,
            p=1 - self.corruption_level
        ) * x

    def __call__(self, inputs):
        """
        (Symbolically) corrupt the inputs with a binomial (masking) noise.

        Parameters
        ----------
        inputs : numpy nd array. Contains the 

        Returns
        -------
        corrupted : numpy nd array. Corrupted texture.
            where individual inputs have been masked with independent
            probability equal to `self.corruption_level`.
        """

        #if isinstance(inputs, tensor.Variable):
        return self._corrupt(inputs)
        #else:
        #    return [self._corrupt(inp) for inp in inputs]


class GaussianCorruptor(Corruptor):
    """
    A Gaussian corruptor transforms inputs by adding zero
    mean isotropic Gaussian noise.
    """

    def __init__(self, stdev, rng=2001):
        super(GaussianCorruptor, self).__init__(corruption_level=stdev, rng=rng)

    def _corrupt(self, x):
        noise = self.s_rng.normal(
            size=x.shape,
            loc=0.,
            scale=self.corruption_level
        )

        rval = abs(noise + x) % 255
        return rval

    def __call__(self, inputs):
        """
        (Symbolically) corrupt the inputs with Gaussian noise.

        Parameters
        ----------
        inputs : tensor_like, or list of tensor_likes
            Theano symbolic(s) representing a (list of) (mini)batch of inputs
            to be corrupted, with the first dimension indexing training
            examples and the second indexing data dimensions.

        Returns
        -------
        corrupted : tensor_like, or list of tensor_likes
            Theano symbolic(s) representing the corresponding corrupted inputs,
            where individual inputs have been corrupted by zero mean Gaussian
            noise with standard deviation equal to `self.corruption_level`.
        """
        #if isinstance(inputs, tensor.Variable):
        return self._corrupt(inputs)
        #return [self._corrupt(inp) for inp in inputs]

##################################################
def get(str):
    """ Evaluate str into a corruptor object, if it exists """
    obj = globals()[str]
    if issubclass(obj, Corruptor):
        return obj
    else:
        raise NameError(str)

