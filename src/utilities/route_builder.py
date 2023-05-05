from typing import List, Set
import re

from src import CustomHash, NUM_TRUCK_CAPACITY, DELIVERY_DISPATCH_TIME
from src.models.package import Package


class RouteBuilder:

    @staticmethod
    def get_optimized_route(packages: List[Package]):
        optimized_indices = list()
        end_index = len(packages)
        for i in range(0, end_index - 1):
            package = packages[i]
            next_package = packages[i + 1]
            greatest_sum_package = packages[end_index - 1]
            if package.location is next_package.location or package.location is greatest_sum_package.location:
                optimized_indices.append(i)
                continue
            distance_to_last_to_next = (package.location.distance_dict[greatest_sum_package.location] + greatest_sum_package.location.distance_dict[next_package.location])
            distance_to_next = package.location.distance_dict[packages[i + 1].location]
            if end_index is not i and distance_to_last_to_next < distance_to_next:
                optimized_indices.append(i)
                end_index -= 1
                optimized_indices.append(end_index)
            else:
                optimized_indices.append(i)
        return optimized_indices

    @staticmethod
    def get_most_spread_out_stops(packages: List[Package]):
        pass

    @staticmethod
    def get_bundled_packages(packages: List[Package]) -> List[Set[Package]]:
        custom_hash = RouteBuilder.load_packages(packages)
        bundle_map = _get_bundled_package_ids(packages)
        package_bundle_sets = []
        for package_id in bundle_map.keys():
            bundle_set = set()
            bundle_set.add(custom_hash.get_package(package_id))
            for bundled_package_id in bundle_map[package_id]:
                bundle_set.add(custom_hash.get_package(bundled_package_id))
            package_bundle_sets.append(bundle_set)
        _unionize_bundled_sets(package_bundle_sets)
        return package_bundle_sets

    @staticmethod
    def get_delayed_packages(packages: List[Package]) -> Set[Package]:
        delayed_packages = set()
        for package in packages:
            if package.hub_arrival_time > DELIVERY_DISPATCH_TIME:
                delayed_packages.add(package)
        return delayed_packages

    @staticmethod
    def load_packages(packages: List[Package]) -> CustomHash:
        custom_hash = CustomHash(NUM_TRUCK_CAPACITY)
        for package in packages:
            custom_hash.add_package(package)
        return custom_hash


def _get_bundled_package_ids(packages: List[Package]):
    bundle_map = {}
    for package in packages:
        if str(package.special_note).startswith('Must be delivered with '):
            special_note = package.special_note
            pattern = r'\d+'
            package_ids = [int(match) for match in re.findall(pattern, special_note)]
            bundle_map[package.package_id] = package_ids
    return bundle_map


def _unionize_bundled_sets(bundled_sets):
    i = 0
    while i < len(bundled_sets):
        current_set = bundled_sets[i]
        intersecting_sets = [bundle for bundle in bundled_sets[i + 1:] if current_set.intersection(bundle)]
        if intersecting_sets:
            for intersecting_set in intersecting_sets:
                current_set = current_set.union(intersecting_set)
                bundled_sets.remove(intersecting_set)
            bundled_sets[i] = current_set
        i += 1
