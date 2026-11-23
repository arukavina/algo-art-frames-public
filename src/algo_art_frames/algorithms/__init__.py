"""Algorithm registry.

To add a new algorithm, the process is simple: create algorithms/<name>.py
exposing a `PLUGIN` (see base.AlgorithmPlugin), then import it here and add
it to REGISTRY below.
"""

from algo_art_frames.algorithms import (
    a_star_search,
    backpropagation,
    binary_search,
    dbscan,
    deflate_compression,
    fast_fourier_transform,
    genetic_algorithms,
    hyperloglog,
    k_means_clustering,
    knuth_morris_pratt,
    linear_congruential_generator,
    minimax,
    monte_carlo,
    pagerank,
    quicksort,
    ray_tracing,
    rsa_encryption,
    singular_value_decomposition,
)
from algo_art_frames.algorithms.base import AlgorithmPlugin

_MODULES = (
    binary_search,
    quicksort,
    a_star_search,
    rsa_encryption,
    fast_fourier_transform,
    k_means_clustering,
    knuth_morris_pratt,
    minimax,
    monte_carlo,
    genetic_algorithms,
    ray_tracing,
    singular_value_decomposition,
    deflate_compression,
    hyperloglog,
    pagerank,
    backpropagation,
    linear_congruential_generator,
    dbscan,
)


def _build_registry(modules=_MODULES) -> dict[str, AlgorithmPlugin]:
    registry: dict[str, AlgorithmPlugin] = {}
    for module in modules:
        slug = module.PLUGIN.slug
        if slug in registry:
            raise ValueError(
                f"Duplicate algorithm slug '{slug}': choose a distinct slug for "
                "alternative versions of an existing algorithm."
            )
        registry[slug] = module.PLUGIN
    return registry


REGISTRY: dict[str, AlgorithmPlugin] = _build_registry()
