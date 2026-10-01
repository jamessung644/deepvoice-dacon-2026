import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from music_pair_alignment_v7 import weak_start_for_pair


class PairAlignmentTests(unittest.TestCase):
    def test_original_excerpt_is_recovered_instead_of_unrelated_prefix(self):
        clean = {'parent_sample_id': 'x', 'split': 'train', 'output_frames': 20}
        source = list(range(20))
        for view in ('codec_lowrate', 'telephone_g711', 'noise_reverb', 'resample_eq'):
            strong = dict(clean, view_id=view, output_frames=4, view_parameters={'source_start_frame': 12})
            correct_excerpt = source[12:16]
            aligned = weak_start_for_pair(strong, clean, 0, 4)
            self.assertEqual(source[aligned:aligned+4], correct_excerpt)
            self.assertNotEqual(source[:4], correct_excerpt)

    def test_clean_and_partial_policy_is_not_changed_in_this_experiment(self):
        clean = {'parent_sample_id': 'x', 'split': 'train', 'output_frames': 20}
        for view in ('clean', 'partial_presence'):
            r = dict(clean, view_id=view, view_parameters={'source_start_frame': 12})
            self.assertEqual(weak_start_for_pair(r, clean, 2, 4), 2)

    def test_out_of_range_missing_metadata_and_cross_split_fail(self):
        clean = {'parent_sample_id': 'x', 'split': 'train', 'output_frames': 20}
        r = dict(clean, view_id='noise_reverb', output_frames=4, view_parameters={'source_start_frame': 18})
        with self.assertRaises(ValueError): weak_start_for_pair(r, clean, 0, 4)
        r['view_parameters'] = {}
        with self.assertRaises(KeyError): weak_start_for_pair(r, clean, 0, 4)
        r['split'] = 'dev'
        with self.assertRaises(ValueError): weak_start_for_pair(r, clean, 0, 4)


if __name__ == '__main__':
    unittest.main()
