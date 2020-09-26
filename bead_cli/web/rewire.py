from collections import defaultdict
from typing import Dict, List, Set
from bead.meta import BeadName, InputName

ContentId = str
BoxName = str
BeadRewireOptions = dict


def get_options(beads) -> Dict[BoxName, List[BeadRewireOptions]]:
    beads = [bead for bead in beads if bead.is_not_phantom]

    box_clusters: Dict[BoxName, List[BeadRewireOptions]] = defaultdict(list)
    content_id_to_names: Dict[ContentId, Set[BeadName]] = defaultdict(set)

    for bead in beads:
        content_id_to_names[bead.content_id].add(bead.name)

    for bead in beads:
        input_map: Dict[InputName, List[BeadName]] = {}
        for input in bead.inputs:
            current_input_name = bead.get_input_bead_name(input.name)
            candidates = content_id_to_names[input.content_id]
            if current_input_name in candidates:
                # keep existing map, if a matching bead with that name exists
                candidate_list = [current_input_name]
            else:
                candidate_list = list(candidates)
            input_map[input.name] = candidate_list

        # leave out identity mappings
        input_map = {
            input_name: bead_names
            for input_name, bead_names in input_map.items()
            if bead_names != [input_name]
        }

        if input_map:
            box_clusters[bead.box_name].append(
                {
                    'name': bead.name,
                    'content_id': bead.content_id,
                    'timestamp': bead.timestamp_str,
                    'input_map': input_map
                }
            )

    return box_clusters
