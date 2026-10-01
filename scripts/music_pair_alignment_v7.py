"""Align only the four standard augmentation excerpts to their stored clean parent."""
STANDARD_VIEWS = {'codec_lowrate', 'telephone_g711', 'noise_reverb', 'resample_eq'}


def weak_start_for_pair(strong, clean, start, length):
    if strong['parent_sample_id'] != clean['parent_sample_id'] or strong['split'] != clean['split']:
        raise ValueError('Pair identity or split differs')
    if strong['view_id'] not in STANDARD_VIEWS:
        # Preserve the historical policy for clean and partial-presence inputs.
        # Partial-presence masks need a separate controlled experiment.
        return min(start, max(0, clean['output_frames']-length))
    offset = strong['view_parameters']['source_start_frame']
    if type(offset) is not int or offset < 0 or start < 0:
        raise ValueError('Invalid source offset')
    weak_start = offset + start
    if start+length > strong['output_frames'] or weak_start+length > clean['output_frames']:
        raise ValueError('Aligned excerpt exceeds stored waveform')
    return weak_start
