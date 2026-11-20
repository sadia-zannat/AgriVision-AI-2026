---
license: cc-by-4.0
---
# Tomato Disease Detector (YOLOv8n)

A fine-tuned YOLOv8n object detection model that identifies 9 common tomato leaf conditions from images.

## Classes Detected

1. Tomato Early blight leaf
2. Tomato Septoria leaf spot
3. Tomato leaf (healthy)
4. Tomato leaf bacterial spot
5. Tomato leaf late blight
6. Tomato leaf mosaic virus
7. Tomato leaf yellow virus
8. Tomato mold leaf
9. Tomato two spotted spider mites leaf

## Performance

Trained for 100 epochs on a Tesla T4 GPU (Google Colab).

| Class | Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|---|
| **Overall (all)** | 0.680 | 0.675 | **0.686** | 0.465 |
| Tomato two spotted spider mites leaf | 0.982 | 1.000 | 0.995 | 0.886 |
| Tomato Septoria leaf spot | 0.817 | 0.794 | 0.849 | 0.561 |
| Tomato mold leaf | 0.685 | 0.813 | 0.798 | 0.539 |
| Tomato Early blight leaf | 0.674 | 0.626 | 0.685 | 0.408 |
| Tomato leaf yellow virus | 0.591 | 0.682 | 0.654 | 0.464 |
| Tomato leaf | 0.614 | 0.594 | 0.590 | 0.329 |
| Tomato leaf late blight | 0.570 | 0.611 | 0.562 | 0.364 |
| Tomato leaf mosaic virus | 0.611 | 0.544 | 0.567 | 0.359 |
| Tomato leaf bacterial spot | 0.578 | 0.413 | 0.478 | 0.272 |

**Note:** Bacterial spot and mosaic virus have the lowest recall — the model may miss some real-world instances of these two conditions. 
Spider mite detection is the strongest class, following additional data added during training (see Dataset section).

## Dataset

This model was trained on a combined dataset:

- **Base dataset:** [Crop Disease Computer Vision Model](https://universe.roboflow.com/aryan-rajvanshi-xvuyg/crop-disease-axhjj) by Aryan Rajvanshi, Roboflow Universe, licensed CC BY 4.0.
- **Supplementary data:** 145 additional spider mite images from [tomato spider mite Computer Vision Model](https://universe.roboflow.com/tomato-leaf-disease-brnbi/tomato-spider-mite-febhx)
- by "tomato leaf disease," Roboflow Universe, licensed CC BY 4.0 — added to correct a severe class imbalance (the base dataset had only 1 labeled spider mite image).

Final dataset: 2,977 images (2,226 train / 449 validation / 302 test).

## Usage

```python
from ultralytics import YOLO

model = YOLO("best.pt")
results = model("your_image.jpg")
results[0].show()
```

## Limitations

- First release (v1) — accuracy varies notably by class; see table above.
- Trained specifically on tomato leaves; not validated on other crops.
- Performance on bacterial spot and mosaic virus in particular may benefit from additional training data in a future version.

## License

CC BY 4.0, consistent with the source datasets.

## Author

Fine-tuned by Nariman Osman (Nar), as a learning project in computer vision / object detection.