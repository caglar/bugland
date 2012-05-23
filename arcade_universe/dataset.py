import numpy
import sys

from perlin import PerlinNoiseGenerator

class SpritePlacer(object):
	"""
	Defines a dataset composed of a sequence of images of the
	specified dimensions (``gen.w`` by ``gen.h`` pixels). Each image
	contains a certain number of binary sprites or "sprites" scattered
	about. The ``gen`` parameter must be an iterator or an iterable
	such that:

	   iter(gen) -> iterator of
		   ((((x1, y1), sprite1), ((x2, y2), sprite2), ...), target)

	Where ``spriten`` is a :class:`Sprite` object, ``0 <= xn < w``, ``0 <=
	yn < h``. ``SpritePlacer`` will generate a scene where the top left
	pixel of the nth sprite is positioned at ``(xn, yn)``
	coordinates. ``target`` is a tuple, list or vector of numbers
	representing the class(es) or target(s) associated to the
	scene. Additionally, ``gen`` must have the following attributes:

	- ``gen.w`` must be the width of the scene in pixels.

	- ``gen.h`` must be the height of the scene in pixels.

	- ``gen.nout`` must be the length of the target

	- ``gen.nclasses`` must be either ``None`` or a tuple, list or
	  vectors of integers or ``None``, an integer at the nth position
	  meaning that the nth target is a class identifier from 0 included
	  to ``nclasses[n]`` excluded, ``None`` meaning that the nth target

	- ``gen.out_format`` must be 'array'

	- ``gen.out_dtype`` must be the dtype of the targets generated by
	  iterating over ``iter(gen)`` (typically 'uint8', if the
	  target(s) is(are) classes).

	The ``spriteland.gen`` module contains generators corresponding to
	this interface.

	If ``collision_check`` is set to ``True``, no sprites' masks will
	overlap. This is done by rejection sampling: gen will be iterated
	over until it produces sprites at positions that do not lead to
	overlaps. For small images with large sprites or a lot of sprites, the
	rejection rate might be high. SpritePlacer provides a method,
	``self.rejection_rate()`` to have an estimate of the rejection
	rate for the samples generated up to the point the method is
	called. A warning will be issued during the generation of the very
	first sample if it takes more than 1000 tries, to help identify
	problems with placement.

	Another issue to be aware of with ``collision_check`` and
	rejection sampling is that the distribution of scenes might be
	biased as a result. For instance, if some sprites are larger than
	some others, scenes with them might be rejected at a greater
	frequency. Assymetrical sprites might be found more often at one side
	or corner than at the others, and so on. These biases might make
	learning easier. For the time being SpritePlacer does not give
	feedback to the generator that might help it doing a counter-bias
	to guarantee certain important statistics. It is recommended to at
	least verify the distribution of classes.

	The dataset can be iterated over and yields (input, target) where
	input and target are vectors.
	"""

	def __init__(self, gen, collision_check = False, enable_perlin = False):
		self.gen = gen
		self.collision_check = collision_check

		self.enable_perlin = enable_perlin

		self.w = gen.w
		self.h = gen.h
		self.nin = gen.w * gen.h
		assert gen.out_format == 'array'
		self.out_format = gen.out_format
		self.out_dtype = gen.out_dtype
		self.nout = gen.nout
		self.nclasses = gen.nclasses

		self.n_successes = 0
		self.n_rejections = 0

		if enable_perlin:
			self.perlin_gen = PerlinNoiseGenerator(self.w, self.h, 32)

	def rejection_rate(self):
		"""
		If collision_check is True, returns the rejection rate of the
		generator, which is the number of scenes that were rejected
		because of overlaps divided by the total number of scenes
		considered.
		"""
		total = self.n_successes + self.n_rejections
		if total == 0:
			return None
		else:
			return float(self.n_rejections) / total

	def __iter__(self):

		gen = iter(self.gen)

		if self.collision_check:
			collider = numpy.zeros((self.h, self.w))

		while True:
			if self.enable_perlin:
				data = self.perlin_gen.get_background_noise()
			else:
				data = numpy.zeros((self.h, self.w))

			targets = numpy.zeros((self.nout,), dtype = self.out_dtype)
			if not self.collision_check:
				description, target = gen.next()
				for (x, y), sprite in description:
					data[y:y + sprite.h, x:x + sprite.w] = sprite.patch
				targets[:] = target
				self.n_successes += 1

			else:
				ntrials = 0
				while True:
					if self.n_successes == 0 and ntrials and ntrials % 1000 == 0:
						print >> sys.stderr, "WARNING: Rejected %i candidates, could not yet fit a single scene together. You might want to generate larger images." % ntrials
					ntrials += 1
					description, target = gen.next()
					collider.fill(0)

					for (x, y), sprite in description:
						a, b = y - sprite.marginh, y + sprite.h + sprite.marginh
						c, d = x - sprite.marginw, x + sprite.w + sprite.marginw

						if a < 0 or b >= self.h or c < 0 or d >= self.w:
							ba, bb = (a < 0)*-a, sprite.mh - (b >= self.h) * (b - self.h + 1)
							bc, bd = (c < 0)*-c, sprite.mw - (d >= self.w) * (d - self.w + 1)

							a, b = max(0, a), min(b, self.h - 1)
							c, d = max(0, c), min(d, self.w - 1)

							collider[a:b, c:d] += sprite.mask[ba:bb, bc:bd]
						else:
							collider[a:b, c:d] += sprite.mask

					if numpy.any(collider > 255) or numpy.any(collider == 2) or numpy.any(collider == 3):
						self.n_rejections += 1
						continue
					else:
						for (x, y), sprite in description:
							data[y: y + sprite.h, x: x + sprite.w] = sprite.patch
						targets[:] = target
						self.n_successes += 1
						break
			yield data.reshape(self.nin), targets
