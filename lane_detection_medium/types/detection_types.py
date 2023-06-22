from typing import Optional, Union

from dataclasses import dataclass

import numpy as np

from .box_types import Bbox, BboxList, BoxFormat


@dataclass
class Detection:
    """Single Detection Result Class Implementation."""

    label_id: int
    conf: float
    bbox: np.ndarray[float, np.dtype[np.float32]]
    label_name: Optional[str] = None

    def __post_init__(self):
        # TODO: choose dformat, maybe make it as a method?
        self.bbox = Bbox(self.bbox, dformat=BoxFormat.xyxy)


@dataclass
class ImageDetections:
    """Single Image Detections Class Implementation."""

    results: np.ndarray[float, np.dtype[np.float32]]

    @property
    def confs(self) -> np.ndarray[float, np.dtype[np.float32]]:
        return self.results[:, 4]

    @property
    def class_ids(self) -> np.ndarray[float, np.dtype[np.float32]]:
        return self.results[:, 5]

    @property
    def class_labels(self) -> np.ndarray:
        return self.results[:, 6]

    @property
    def bboxes(self) -> BboxList:
        return BboxList(self.results[:, :4], dformat=BoxFormat.xyxy)

    def sort(self, ascending: bool = False):
        """Sort detections by confidence values."""

        conf_data = self._raw_result[:, 4]
        if not ascending:
            conf_data = -(self._raw_result[:, 4])

        self.results = self.results[conf_data.argsort()]

    def get_index(self, cls_name: Union[str, int]) -> Optional[np.ndarray]:
        if isinstance(cls_name, str):
            index_pos = -1
        elif isinstance(cls_name, int):
            index_pos = -2
        else:
            raise ValueError(f"cls_name contains wrong value '{cls_name}'")

        bbox_indexes = np.where(self._raw_result[:, index_pos] == cls_name)[0]
        if not len(bbox_indexes):
            bbox_indexes = None
        return bbox_indexes

    def delete(self, index: Union[int, np.ndarray]):
        updated_result = np.delete(self.results, index, axis=0)
        return ImageDetections(updated_result)

    def __len__(self):
        return len(self.results)

    @classmethod
    def from_yolo_labels(cls, data: np.ndarray, height: float, width: float):
        # shift label_id to the last column
        result = np.roll(data, -1, axis=1)

        bbox_np = result[:, :4].copy()
        bbox_np[:, [1, 3]] *= height  # reverse normalize y
        bbox_np[:, [0, 2]] *= width  # reverse normalize x
        bbox_np[:, :2] -= bbox_np[:, 2:] / 2  # xy top-left corner to center

        # fill columns of label names with -1
        result = np.c_[bbox_np, result[:, -1], np.ones(result.shape[0]) * -1]
        return cls(result)

    def filter_by_confidence(self, conf_threshold: float) -> np.ndarray:
        idx = np.where(self._raw_result[:, 4] >= conf_threshold)[0]
        return self._raw_result[idx]

    def __getitem__(self, idx: int) -> Detection:
        res = self.results[idx]

        return Detection(label_name=res[-1], label_id=res[-2], conf=res[4], bbox=res[:4])
